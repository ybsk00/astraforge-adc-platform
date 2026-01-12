import json
import time
import random
from datetime import datetime
from supabase import Client
from .dictionaries import PAYLOAD_DICTIONARY, LINKER_DICTIONARY, TARGET_DICTIONARY
import httpx
import asyncio
import hashlib

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

# Mock Data for v1 (ClinicalTrials.gov simulation)
MOCK_TRIALS = [
    {
        "nct_id": "NCT04460456",
        "title": "Study of Trastuzumab Deruxtecan (T-DXd) in Participants With HER2-positive Metastatic Breast Cancer",
        "intervention": "Drug: Trastuzumab deruxtecan",
        "status": "Recruiting",
        "phase": "Phase 3"
    },
    {
        "nct_id": "NCT04556773",
        "title": "A Study of Datopotamab Deruxtecan (Dato-DXd) in Participants With Advanced or Metastatic Non-Small Cell Lung Cancer",
        "intervention": "Drug: Datopotamab deruxtecan",
        "status": "Recruiting",
        "phase": "Phase 3"
    },
    {
        "nct_id": "NCT03262935",
        "title": "Study of Sacituzumab Govitecan-hziy in Metastatic Urothelial Cancer",
        "intervention": "Drug: Sacituzumab govitecan",
        "status": "Active, not recruiting",
        "phase": "Phase 2"
    },
    {
        "nct_id": "NCT04256343",
        "title": "Study of Enfortumab Vedotin in Subjects With Locally Advanced or Metastatic Urothelial Cancer",
        "intervention": "Drug: Enfortumab vedotin",
        "status": "Recruiting",
        "phase": "Phase 3"
    },
    {
        "nct_id": "NCT02301985",
        "title": "A Study of Mirvetuximab Soravtansine in Platinum-Resistant Ovarian Cancer",
        "intervention": "Drug: Mirvetuximab soravtansine",
        "status": "Completed",
        "phase": "Phase 3"
    }
]

async def execute_golden_seed(ctx, run_id: str, config: dict):
    """
    Golden Seed ADC 100 자동화 파이프라인
    1. 후보 수집 (Fetch)
    2. 추출 및 표준화 (Extract & Normalize)
    3. 품질 게이트 (Quality Gate)
    4. 결정적 정렬 (Deterministic Sort)
    5. DB 적재 (Upsert)
    """
    db: Client = ctx["db"]
    
    # Config Parsing
    target_count = config.get("target_count", 100)
    min_evidence = config.get("min_evidence", 1)
    
    # Generate Dynamic Version for every run (e.g., v1-20240112-123045)
    base_version = config.get("seed_version", "v1")
    timestamp_suffix = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    seed_version = f"{base_version}-{timestamp_suffix}"
    
    summary = {
        "fetched": 0,
        "extracted": 0,
        "passed_gate": 0,
        "upserted": 0,
        "errors": []
    }



# ... (inside execute_golden_seed)

    # 1. Fetch Candidates
    data_source = config.get("data_source", "mock")
    print(f"[GoldenSeed] Starting job with data_source={data_source}, target={target_count}")

    if data_source == "clinicaltrials":
        # Real Data Fetching
        raw_candidates = await _fetch_real_candidates(target_count, config)
    else:
        # Mock Data
        raw_candidates = _fetch_mock_candidates(config.get("candidate_fetch_size", 500))
    
    print(f"[GoldenSeed] Fetched {len(raw_candidates)} candidates (deduped)")
    
    # 1.1 Raw Level Dedup (NCT ID 기준) - Already done in real fetch, but safe to keep
    seen_ncts = set()
    deduped_raw = []
    for r in raw_candidates:
        nct = r.get("nct_id")
        if not nct or nct in seen_ncts:
            continue
        seen_ncts.add(nct)
        deduped_raw.append(r)
    
    raw_candidates = deduped_raw
    summary["fetched"] = len(raw_candidates)

    # 2. Process & Upsert
    upsert_count = 0
    golden_set_id = _ensure_golden_set_version(db, "Golden Set A", seed_version, config)
    
    if not golden_set_id:
        print("[GoldenSeed] Critical Error: Failed to ensure Golden Set version. Aborting.")
        summary["errors"].append("Failed to ensure Golden Set version")
        return summary

    for raw in raw_candidates:
        try:
            item = _extract_components(raw)
            score, reasons = _calculate_confidence_score(item, min_evidence)
            item["confidence_score"] = score
            evidence_data = {"reasons": reasons}

            # Generate Program Key
            program_key = make_program_key(item)

            data = {
                "golden_set_id": golden_set_id,  # Link to Golden Set
                "drug_name": item["drug_name"],
                "target": item["target"],
                "antibody": item["antibody"],
                "linker": item["linker"],
                "payload": item["payload"],
                "program_key": program_key,      # New Grouping Key
                "approval_status": item["approval_status"],
                "source_ref": item["evidence_refs"][0] if item["evidence_refs"] else None,
                "confidence_score": item["confidence_score"],
                "dataset_version": seed_version,
                "evidence_json": evidence_data,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert based on Unique Key (golden_set_id, source_ref)
            res = db.table("golden_candidates").upsert(
                data, 
                on_conflict="golden_set_id,source_ref"
            ).execute()
            
            # Get the inserted candidate ID
            if res.data and len(res.data) > 0:
                candidate_id = res.data[0]['id']
                
                # Insert Evidence into separate table
                if item["evidence_refs"]:
                    evidence_records = []
                    for ref in item["evidence_refs"]:
                        evidence_records.append({
                            "candidate_id": candidate_id,
                            "source": "ClinicalTrials.gov" if "NCT" in ref else "PubMed",
                            "ref_id": ref,
                            "url": f"https://clinicaltrials.gov/study/{ref}" if "NCT" in ref else None,
                            "snippet": f"Evidence for {item['drug_name']} from {ref}"
                        })
                    
                    if evidence_records:
                        db.table("golden_candidate_evidence").insert(evidence_records).execute()

            upsert_count += 1
            if upsert_count % 10 == 0:
                print(f"[GoldenSeed] Upserted {upsert_count} candidates...")
                
        except Exception as e:
            msg = f"Upsert failed for {item.get('drug_name', 'Unknown')}: {str(e)}"
            print(f"[GoldenSeed] Error: {msg}")
            summary["errors"].append(msg)

    summary["upserted"] = upsert_count
    return summary

def _fetch_mock_candidates(limit):
    """
    Mock Data Generator
    실제 API 대신 시뮬레이션 데이터 생성
    """
    results = []
    # Base templates
    templates = [
        ("Trastuzumab deruxtecan", "HER2", "Trastuzumab", "DXd", "GGFG"),
        ("Datopotamab deruxtecan", "TROP2", "Datopotamab", "DXd", "GGFG"),
        ("Sacituzumab govitecan", "TROP2", "Sacituzumab", "SN-38", "Hydrazone"),
        ("Enfortumab vedotin", "Nectin-4", "Enfortumab", "MMAE", "VC"),
        ("Mirvetuximab soravtansine", "FOLR1", "Mirvetuximab", "DM4", "Disulfide"),
        ("Brentuximab vedotin", "CD30", "Brentuximab", "MMAE", "VC"),
        ("Polatuzumab vedotin", "CD79b", "Polatuzumab", "MMAE", "VC"),
        ("Gemtuzumab ozogamicin", "CD33", "Gemtuzumab", "Calicheamicin", "Hydrazone"),
        ("Inotuzumab ozogamicin", "CD22", "Inotuzumab", "Calicheamicin", "Hydrazone"),
        ("Tisotumab vedotin", "TF", "Tisotumab", "MMAE", "VC"),
    ]
    
    for i in range(limit):
        # Randomly pick a template and add some noise/variation
        base = random.choice(templates)
        drug_name, target, ab, payload, linker = base
        
        # Simulate some incomplete/noisy data
        if random.random() < 0.1: continue # Skip some
        
        item = {
            "intervention": f"Drug: {drug_name}",
            "nct_id": f"NCT{random.randint(10000000, 99999999)}",
            "phase": random.choice(["Phase 1", "Phase 2", "Phase 3"]),
            "status": random.choice(["Recruiting", "Completed", "Active"]),
            "title": f"Study of {drug_name} in Cancer"
        }
        results.append(item)
        
    return results

def _extract_components(raw):
    """
    Extract components from raw text using Dictionaries
    """
    text = raw["intervention"].lower()
    
    # 1. Payload Extraction
    payload = None
    payload_std = None
    for k, v in PAYLOAD_DICTIONARY.items():
        if k in text:
            payload = k
            payload_std = v
            break
            
    # 2. Linker Extraction (Infer from drug name suffix or known combinations)
    # Mock logic: In reality, we need deeper text analysis
    linker = "Unknown"
    linker_std = "Unknown"
    if "vedotin" in text: 
        linker_std = "VC"
    elif "deruxtecan" in text:
        linker_std = "GGFG"
    elif "govitecan" in text:
        linker_std = "Hydrazone"
    elif "soravtansine" in text:
        linker_std = "Disulfide"
    elif "ozogamicin" in text:
        linker_std = "Hydrazone"
        
    # 3. Target Extraction (Infer from known drugs or title)
    # Mock logic
    target_std = "Unknown"
    if "trastuzumab" in text: target_std = "HER2"
    elif "datopotamab" in text: target_std = "TROP2"
    elif "sacituzumab" in text: target_std = "TROP2"
    elif "enfortumab" in text: target_std = "Nectin-4"
    elif "mirvetuximab" in text: target_std = "FOLR1"
    elif "brentuximab" in text: target_std = "CD30"
    elif "polatuzumab" in text: target_std = "CD79b"
    elif "gemtuzumab" in text: target_std = "CD33"
    elif "inotuzumab" in text: target_std = "CD22"
    elif "tisotumab" in text: target_std = "TF"

    # 4. Antibody Extraction
    antibody = text.split(" ")[1].capitalize() if " " in text else "Unknown" # Simple heuristic
    
    # Drug Name
    drug_name = raw["intervention"].replace("Drug: ", "").strip()

    return {
        "drug_name": drug_name,
        "target": target_std,
        "antibody": antibody,
        "linker": linker_std,
        "payload": payload_std,
        "approval_status": "Approved" if raw["phase"] == "Phase 3" else "Clinical",
        "evidence_refs": [raw["nct_id"]],
        "raw_source": raw
    }

def _calculate_confidence_score(cand, min_evidence):
    score = 0
    reasons = []
    
    # Base Score for components
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
    """
    Ensure the Golden Set version record exists and return its ID
    """
    try:
        res = db.table("golden_sets").upsert({
            "name": name,
            "version": version,
            "config": config
        }, on_conflict="name,version").execute()
        
        if res.data and len(res.data) > 0:
            print(f"[GoldenSeed] Golden Set Version ensured: {res.data[0]['id']}")
            return res.data[0]['id']
        return None
    except Exception as e:
        print(f"[GoldenSeed] Warning: Failed to ensure golden_set version: {e}")
        return None

async def _fetch_real_candidates(target_count, config):
    """
    Fetch real candidates from ClinicalTrials.gov API v2
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    results = []
    seen_ncts = set()
    next_page_token = None
    
    # Configurable parameters
    ct_config = config.get("clinicaltrials", {})
    queries = ct_config.get("queries", [
        {"query.term": '"antibody-drug conjugate" OR "antibody drug conjugate" OR ADC'},
        {"query.intr": "vedotin OR deruxtecan OR govitecan OR soravtansine OR ozogamicin"},
        {"query.term": "MMAE OR DM1 OR DM4 OR DXd OR SN-38 OR calicheamicin"}
    ])
    filters = ct_config.get("filters", {
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED"
    })
    page_size = ct_config.get("page_size", 50) # Max 1000, but smaller is safer
    sleep_sec = ct_config.get("sleep_sec", 1.0)
    
    print("[GoldenSeed] Starting ClinicalTrials.gov fetch...")
    
    async with httpx.AsyncClient() as client:
        for q_idx, query_params in enumerate(queries):
            if len(results) >= target_count:
                break
                
            print(f"[GoldenSeed] Processing Query {q_idx+1}/{len(queries)}: {query_params}")
            next_page_token = None
            
            # Max pages per query to prevent infinite loops
            for page in range(ct_config.get("max_pages_per_query", 10)):
                if len(results) >= target_count:
                    break
                
                params = {
                    "pageSize": page_size,
                    "fields": "protocolSection.identificationModule,protocolSection.statusModule,protocolSection.armsInterventionsModule,protocolSection.conditionsModule,protocolSection.referencesModule",
                    **query_params,
                    **filters
                }
                
                if next_page_token:
                    params["pageToken"] = next_page_token
                
                try:
                    resp = await client.get(base_url, params=params, timeout=30.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    studies = data.get("studies", [])
                    print(f"[GoldenSeed]   Page {page+1}: Found {len(studies)} studies")
                    
                    for study in studies:
                        proto = study.get("protocolSection", {})
                        ident = proto.get("identificationModule", {})
                        nct_id = ident.get("nctId")
                        
                        if not nct_id or nct_id in seen_ncts:
                            continue
                            
                        # Extract Intervention (Drug Name)
                        interventions = proto.get("armsInterventionsModule", {}).get("interventions", [])
                        drug_name = "Unknown"
                        found_adc = False
                        
                        for intr in interventions:
                            if intr.get("type") == "DRUG":
                                name = intr.get("name", "")
                                # Simple heuristic to find the ADC drug
                                if "mab" in name.lower() or "conjugate" in name.lower() or "adc" in name.lower():
                                    drug_name = name
                                    found_adc = True
                                    break
                        
                        if not found_adc and interventions:
                            # Fallback to first drug
                            for intr in interventions:
                                if intr.get("type") == "DRUG":
                                    drug_name = intr.get("name")
                                    break
                        
                        # Normalize Status
                        status = proto.get("statusModule", {}).get("overallStatus", "Unknown")
                        
                        # Extract References
                        refs = []
                        ref_module = proto.get("referencesModule", {})
                        for r in ref_module.get("references", []):
                            if r.get("pmid"):
                                refs.append(r.get("pmid"))
                        
                        # Add NCT ID as first ref
                        refs.insert(0, nct_id)
                        
                        item = {
                            "nct_id": nct_id,
                            "intervention": f"Drug: {drug_name}",
                            "title": ident.get("officialTitle") or ident.get("briefTitle", "No Title"),
                            "status": status,
                            "phase": "Phase " + "/".join(proto.get("statusModule", {}).get("phases", ["Unknown"])),
                            "evidence_refs": refs, # Store refs here for extraction
                            "raw_source": study # Store full object if needed
                        }
                        
                        seen_ncts.add(nct_id)
                        results.append(item)
                        
                        if len(results) >= target_count:
                            break
                    
                    next_page_token = data.get("nextPageToken")
                    if not next_page_token:
                        break
                        
                    await asyncio.sleep(sleep_sec)
                    
                except Exception as e:
                    print(f"[GoldenSeed] Error fetching page: {e}")
                    await asyncio.sleep(sleep_sec * 2) # Backoff
                    continue
                    
    print(f"[GoldenSeed] Finished fetching. Total unique candidates: {len(results)}")
    return results
