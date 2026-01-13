import json
import time
import random
import re
from datetime import datetime
from supabase import Client
from .dictionaries import PAYLOAD_DICTIONARY, LINKER_DICTIONARY, TARGET_DICTIONARY
from .resolve_ids_job import resolve_text, QUERY_PROFILES
import httpx
import asyncio
import hashlib

PARSER_VERSION = "v2.0.0"

def make_program_key(c):
    """
    Generate a unique key for the drug program (combination of components)
    """
    s = "|".join([
        (c.get("drug_name") or "").lower().strip(),
        (c.get("target") or "").lower().strip(),
        (c.get("antibody") or "").lower().strip(),
        (c.get("linker") or "").lower().strip(),
        (c.get("payload") or "").lower().strip(),
    ])
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

async def execute_golden_seed(ctx, run_id: str, config: dict):
    """
    Golden Seed ADC 100 자동화 파이프라인 (Design Engine Version)
    1. QueryProfile 기반 수집 (Fetch)
    2. RAW 데이터 저장 (Lineage)
    3. ID Resolution (Normalize)
    4. 품질 게이트 및 승격 (Quality Gate & Promotion)
    5. DB 적재 (Upsert)
    """
    db: Client = ctx["db"]
    
    # Config Parsing
    target_count = config.get("target_count", 100)
    min_evidence = config.get("min_evidence", 1)
    # Profiles to run: default to all or specific list
    profiles_to_run = config.get("profiles", ["golden_adc_antibody_precision"])
    
    # Generate Dynamic Version
    base_version = config.get("seed_version", "v2")
    timestamp_suffix = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    seed_version = f"{base_version}-{timestamp_suffix}"
    
    summary = {
        "fetched": 0,
        "extracted": 0,
        "passed_gate": 0,
        "upserted": 0,
        "errors": []
    }

    # 1. Ensure Golden Set Version
    golden_set_id = _ensure_golden_set_version(db, "Golden Set A", seed_version, config)
    if not golden_set_id:
        return {"status": "failed", "error": "Failed to ensure Golden Set version"}

    # 2. Iterate Profiles
    total_fetched = 0
    total_upserted = 0
    
    for profile_name in profiles_to_run:
        if profile_name not in QUERY_PROFILES:
            print(f"[GoldenSeed] Warning: Unknown profile {profile_name}, skipping.")
            continue
            
        profile = QUERY_PROFILES[profile_name]
        print(f"[GoldenSeed] Running Profile: {profile_name} ({profile['description']})")
        
        # 2.1 Fetch Real Candidates with Profile
        raw_candidates = await _fetch_real_candidates(target_count, config, profile)
        print(f"[GoldenSeed]   Fetched {len(raw_candidates)} candidates for {profile_name}")
        total_fetched += len(raw_candidates)
        
        for raw in raw_candidates:
            try:
                # 2.2 Save RAW Data
                raw_data_id = await _save_raw_data(db, raw, profile_name, PARSER_VERSION, seed_version)
                
                # 2.3 Extract & Resolve
                item = await _extract_and_resolve(db, raw)
                
                # 2.4 Calculate Scores
                score, reasons = _calculate_confidence_score(item, min_evidence)
                item["confidence_score"] = score
                evidence_data = {"reasons": reasons}
                
                # 2.5 Promotion Logic (FINAL vs RAW)
                # Condition: Mapping Confidence >= Threshold AND Evidence Exists
                mapping_conf = item["mapping_confidence"]
                is_final = False
                if mapping_conf >= 0.8 and len(item["evidence_refs"]) >= min_evidence:
                    is_final = True
                
                # Generate Program Key
                program_key = make_program_key(item)
                
                # 2.6 Upsert Candidate
                data = {
                    "golden_set_id": golden_set_id,
                    "drug_name": item["drug_name"],
                    "target": item["target"],
                    "antibody": item["antibody"],
                    "linker": item["linker"],
                    "payload": item["payload"],
                    "program_key": program_key,
                    "approval_status": item["approval_status"],
                    "source_ref": item["evidence_refs"][0] if item["evidence_refs"] else None,
                    "confidence_score": item["confidence_score"],
                    "mapping_confidence": mapping_conf,
                    "is_final": is_final,
                    "raw_data_id": raw_data_id,
                    "dataset_version": seed_version,
                    "evidence_json": evidence_data,
                    "evidence_refs": [{"type": "clinical", "id": ref} for ref in item["evidence_refs"]], # JSONB format
                    "updated_at": datetime.utcnow().isoformat()
                }

                # Upsert
                res = db.table("golden_candidates").upsert(
                    data, 
                    on_conflict="golden_set_id,program_key"
                ).execute()
                
                if res.data:
                    candidate_id = res.data[0]['id']
                    # Insert Evidence Table (Optional, but good for search)
                    # ... (Skipping for brevity, relying on evidence_refs column for now)
                
                total_upserted += 1
                
            except Exception as e:
                msg = f"Error processing {raw.get('nct_id')}: {str(e)}"
                print(f"[GoldenSeed] {msg}")
                summary["errors"].append(msg)

    summary["fetched"] = total_fetched
    summary["upserted"] = total_upserted
    return summary

async def _save_raw_data(db, raw_item, profile_name, parser_version, dataset_version):
    """
    Save raw data to golden_seed_raw table
    """
    # Calculate hash for deduplication/lineage
    # Use nct_id + updated_at or similar if available, or just json dump
    content_hash = hashlib.sha256(json.dumps(raw_item, sort_keys=True).encode()).hexdigest()
    
    data = {
        "source": "clinicaltrials",
        "source_id": raw_item.get("nct_id"),
        "source_hash": content_hash,
        "raw_payload": raw_item,
        "parser_version": parser_version,
        "query_profile": profile_name,
        "dataset_version": dataset_version
    }
    
    # Check if exists (optional, or just insert)
    # For lineage, we might want to insert every time or only if hash changes.
    # Use Upsert to handle duplicates (Phase 2)
    res = db.table("golden_seed_raw").upsert(
        data, 
        on_conflict="source, source_hash"
    ).execute()
    
    # If upsert returns data, use it. If not (e.g. ignore), we might need to fetch.
    # But Supabase upsert returns data by default.
    if res.data:
        return res.data[0]["id"]
    
    # Fallback if no data returned (shouldn't happen with default return=representation)
    return None

async def _extract_and_resolve(db, raw):
    """
    Extract components and resolve IDs
    """
    text = raw["intervention"].lower()
    drug_name = raw["intervention"].replace("Drug: ", "").strip()
    
    # Simple Extraction (Regex/Dict) - similar to before but we will resolve them
    # 1. Payload
    payload_text = "Unknown"
    for k in PAYLOAD_DICTIONARY:
        if k in text:
            payload_text = k
            break
            
    # 2. Linker
    linker_text = "Unknown"
    if "vedotin" in text: linker_text = "vedotin"
    elif "deruxtecan" in text: linker_text = "deruxtecan"
    elif "govitecan" in text: linker_text = "govitecan"
    elif "soravtansine" in text: linker_text = "soravtansine"
    elif "ozogamicin" in text: linker_text = "ozogamicin"
    
    # 3. Target
    target_text = "Unknown"
    # ... (Reuse existing logic or improve)
    if "trastuzumab" in text: target_text = "HER2"
    elif "datopotamab" in text: target_text = "TROP2"
    # ... more rules
    
    # 4. Antibody
    antibody_text = text.split(" ")[1].capitalize() if " " in text else "Unknown"

    # Resolve IDs
    # We resolve the extracted text to canonical entities
    payload_res = await resolve_text(db, payload_text, "payload")
    linker_res = await resolve_text(db, linker_text, "linker")
    target_res = await resolve_text(db, target_text, "target")
    antibody_res = await resolve_text(db, antibody_text, "antibody")
    
    # Calculate Mapping Confidence (Average of components)
    confs = [payload_res["confidence"], linker_res["confidence"], target_res["confidence"], antibody_res["confidence"]]
    mapping_conf = sum(confs) / len(confs)
    
    return {
        "drug_name": drug_name,
        "target": target_text, # Keep text for display/search
        "antibody": antibody_text,
        "linker": linker_text,
        "payload": payload_text,
        "approval_status": "Approved" if raw["phase"] == "Phase 3" else "Clinical",
        "evidence_refs": raw["evidence_refs"],
        "mapping_confidence": mapping_conf,
        # We could store resolved IDs here too if we updated the table schema to have FKs
        # "payload_id": payload_res["id"], ...
    }

def _calculate_confidence_score(cand, min_evidence):
    score = 0
    reasons = []
    
    # Base Score for components (Text availability)
    if cand["target"] != "Unknown": score += 20
    if cand["payload"] != "Unknown": score += 20
    if cand["linker"] != "Unknown": score += 20
    if cand["antibody"] != "Unknown": score += 10
    
    # Evidence Score
    evidence_count = len(cand["evidence_refs"])
    if evidence_count >= min_evidence:
        score += 20
        reasons.append("Min evidence met")
    elif evidence_count >= 1:
        score += 10
        reasons.append("Has evidence")
        
    # Status Score
    if cand["approval_status"] == "Approved":
        score += 10
        reasons.append("Approved status")
        
    return min(score, 100), reasons

def _ensure_golden_set_version(db, name, version, config):
    try:
        res = db.table("golden_sets").upsert({
            "name": name,
            "version": version,
            "config": config
        }, on_conflict="name,version").execute()
        if res.data: return res.data[0]['id']
        return None
    except Exception as e:
        print(f"[GoldenSeed] Warning: Failed to ensure golden_set version: {e}")
        return None

import requests

# ... (imports)

ONCOLOGY_TERMS = [
    "cancer", "tumor", "carcinoma", "neoplasm", "metast",
    "lymphoma", "leukemia", "myeloma", "sarcoma", "malignan"
]

def is_oncology_condition(conditions: list) -> bool:
    if not conditions:
        return False
    blob = " ".join([c.lower() for c in conditions if c])
    return any(t in blob for t in ONCOLOGY_TERMS)

def is_antibody_like(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    # 항체/이중항체 키워드 + -mab 계열
    if re.search(r'(^|[^a-z0-9])[a-z0-9-]*mab([^a-z0-9]|$)', n):
        return True
    if "antibody" in n:
        return True
    if "monoclonal" in n:
        return True
    if "bispecific" in n:
        return True
    if "t-cell engager" in n or "t cell engager" in n:
        return True
    if "bite" in n:
        return True
    return False

def is_adc_like(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    # 약물명 리스트를 넣지 않더라도, ADC 형태 신호(문구 기반)를 우선 사용
    if "antibody-drug conjugate" in n or "antibody drug conjugate" in n:
        return True
    if "immunoconjugate" in n:
        return True
    if "antibody conjugate" in n:
        return True
    # ADC라는 단어는 노이즈가 있으나, 여기는 "intervention name"에서만 쓰므로 비교적 안전
    if re.search(r'(^|[^a-z0-9])adc([^a-z0-9]|$)', n):
        return True
    # (선택) 접미사 기반은 “약물명 리스트”가 아니라 패턴이므로 포함 가능
    if any(s in n for s in ["vedotin", "deruxtecan", "govitecan", "mertansine", "ozogamicin", "soravtansine"]):
        return True
    return False

async def _fetch_real_candidates(target_count, config, profile):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    results = []
    seen_ncts = set()

    # 1) Query.term: ADC/항체/이중항체 범주 + 온콜로지 AND
    adc_terms = [
        '"antibody-drug conjugate"',
        '"antibody drug conjugate"',
        '"immunoconjugate"',
        '"antibody conjugate"',
        'ADC',
    ]
    antibody_terms = [
        '"monoclonal antibody"', 'monoclonal', 'antibody', 'mAb',
        '"therapeutic antibody"', '"antibody therapy"',
        'bispecific', '"bispecific antibody"', 'BiTE', '"T-cell engager"'
    ]
    oncology_gate = '(cancer OR tumor OR carcinoma OR neoplasm OR metastatic OR lymphoma OR leukemia OR myeloma OR sarcoma OR malignan*)'

    # profile 키워드가 있으면 추가로 OR에 넣되, 전체는 oncology_gate로 제한
    profile_terms = profile.get("keywords", [])
    term_bucket = adc_terms + antibody_terms + profile_terms
    # 공백 포함 키워드는 따옴표
    def _q(t: str) -> str:
        t = t.strip()
        if " " in t and not (t.startswith('"') and t.endswith('"')):
            return f'"{t}"'
        return t

    concept_or = " OR ".join(_q(t) for t in term_bucket if t)
    query_term = f"({concept_or}) AND {oncology_gate}"

    params = {
        "pageSize": 50,
        "fields": ",".join([
            "protocolSection.identificationModule",
            "protocolSection.statusModule",
            "protocolSection.armsInterventionsModule",
            "protocolSection.conditionsModule",
            "protocolSection.referencesModule",
        ]),
        "query.term": query_term,
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED"
    }
    
    print(f"[GoldenSeed] Fetching with query: {query_term}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }

    next_page_token = None
    
    while len(results) < target_count:
        current_params = params.copy()
        if next_page_token:
            current_params["pageToken"] = next_page_token
            
        print(f"[GoldenSeed] Fetching page... (Current count: {len(results)})")
        
        def fetch_sync():
            return requests.get(base_url, params=current_params, headers=headers, timeout=30.0)

        try:
            resp = await asyncio.to_thread(fetch_sync)
            resp.raise_for_status()
            data = resp.json()
            studies = data.get("studies", [])
            
            if not studies:
                print("[GoldenSeed] No more studies found.")
                break
            
            for study in studies:
                proto = study.get("protocolSection", {}) or {}
                ident = proto.get("identificationModule", {}) or {}
                nct_id = ident.get("nctId")
                if not nct_id or nct_id in seen_ncts:
                    continue

                # 2) Conditions(암) 2차 게이트
                conditions = (proto.get("conditionsModule", {}) or {}).get("conditions", []) or []
                if not is_oncology_condition(conditions):
                    continue

                # 3) Interventions 전체 수집 후 ADC-like/Antibody-like 우선 선택
                interventions = (proto.get("armsInterventionsModule", {}) or {}).get("interventions", []) or []
                drug_names = []
                for intr in interventions:
                    if intr.get("type") == "DRUG" and intr.get("name"):
                        drug_names.append(intr["name"])

                # 후보 pick 우선순위: ADC-like > antibody-like > (없으면 스킵)
                adc_like = [n for n in drug_names if is_adc_like(n)]
                ab_like = [n for n in drug_names if is_antibody_like(n)]
                picked = None
                picked_kind = None

                if adc_like:
                    picked = adc_like[0]
                    picked_kind = "adc_like"
                elif ab_like:
                    picked = ab_like[0]
                    picked_kind = "antibody_like"
                else:
                    # 항체/ADC 신호 없는 DRUG만 있는 trial은 후보화 자체를 하지 않음
                    continue

                status = (proto.get("statusModule", {}) or {}).get("overallStatus", "Unknown")
                phases = (proto.get("statusModule", {}) or {}).get("phases", ["Unknown"]) or ["Unknown"]

                # evidence_refs: 최소 NCT는 포함, referencesModule에서 PMID 있으면 추가(가능 범위)
                refs = [nct_id]

                item = {
                    "nct_id": nct_id,
                    "intervention": f"Drug: {picked}",
                    "intervention_kind": picked_kind,   # 디버깅/품질 확인용
                    "all_drugs": drug_names,            # raw_payload에 남겨두면 추후 추출 개선에 도움
                    "conditions": conditions,           # raw_payload에 남기면 온콜로지 검증/보고서에 도움
                    "title": ident.get("officialTitle"),
                    "status": status,
                    "phase": "Phase " + "/".join(phases),
                    "evidence_refs": refs
                }

                seen_ncts.add(nct_id)
                results.append(item)
                if len(results) >= target_count:
                    break
            
            # Check for next page
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                print("[GoldenSeed] No next page token. Finished fetching.")
                break
                
        except Exception as e:
            print(f"[GoldenSeed] Error fetching: {e}")
            break
            
    return results
