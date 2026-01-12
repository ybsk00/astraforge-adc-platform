import json
import time
import random
from datetime import datetime
from supabase import Client
from .dictionaries import PAYLOAD_DICTIONARY, LINKER_DICTIONARY, TARGET_DICTIONARY

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
    min_evidence = config.get("min_evidence", 2)
    seed_version = config.get("seed_version", "v1")
    
    summary = {
        "fetched": 0,
        "extracted": 0,
        "passed_gate": 0,
        "upserted": 0,
        "errors": []
    }

    # 1. Fetch Candidates (Mock for v1)
    # 실제 구현 시에는 ClinicalTrials API 호출 로직으로 대체
    raw_candidates = _fetch_mock_candidates(config.get("candidate_fetch_size", 500))
    summary["fetched"] = len(raw_candidates)

    # 2. Extract & Normalize
    processed_candidates = []
    for raw in raw_candidates:
        extracted = _extract_components(raw)
        if extracted:
            processed_candidates.append(extracted)
    
    summary["extracted"] = len(processed_candidates)

    # 3. Quality Gate & Scoring
    valid_candidates = []
    for cand in processed_candidates:
        score, reasons = _calculate_confidence_score(cand, min_evidence)
        cand["confidence_score"] = score
        cand["score_reasons"] = reasons
        
        # Hard Gate: 4요소 필수 + 최소 점수
        if all([cand["target"], cand["antibody"], cand["linker"], cand["payload"]]) and score >= 50:
            valid_candidates.append(cand)
            
    summary["passed_gate"] = len(valid_candidates)

    # 4. Deterministic Sort (Score DESC, Name ASC)
    # 점수 높은 순, 동점이면 이름 알파벳 순 -> 항상 같은 결과 보장
    valid_candidates.sort(key=lambda x: (-x["confidence_score"], x["drug_name"]))
    
    # Top N Selection
    final_selection = valid_candidates[:target_count]

    # 5. DB Upsert
    upsert_count = 0
    
    # Ensure Golden Set Version Exists and Get ID
    golden_set_id = _ensure_golden_set_version(db, "ADC_GOLDEN_100", seed_version, config)
    
    if not golden_set_id:
        summary["errors"].append("Failed to get Golden Set ID. Aborting upsert.")
        return summary

    for item in final_selection:
        try:
            # Prepare Evidence JSON
            evidence_data = {
                "sources": item["evidence_refs"],
                "score_reasons": item["score_reasons"],
                "raw_data": item["raw_source"]
            }

            data = {
                "golden_set_id": golden_set_id,  # Link to Golden Set
                "drug_name": item["drug_name"],
                "target": item["target"],
                "antibody": item["antibody"],
                "linker": item["linker"],
                "payload": item["payload"],
                "approval_status": item["approval_status"],
                "source_ref": item["evidence_refs"][0] if item["evidence_refs"] else None,
                "confidence_score": item["confidence_score"],
                "dataset_version": seed_version,
                "evidence_json": evidence_data,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert based on Unique Key (golden_set_id, drug_name, target, antibody, linker, payload)
            res = db.table("golden_candidates").upsert(
                data, 
                on_conflict="golden_set_id,drug_name,target,antibody,linker,payload"
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
        except Exception as e:
            summary["errors"].append(f"Upsert failed for {item['drug_name']}: {str(e)}")

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
            return res.data[0]['id']
        return None
    except Exception as e:
        print(f"Warning: Failed to ensure golden_set version: {e}")
        return None
