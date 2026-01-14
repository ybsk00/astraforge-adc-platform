"""
ClinicalTrials Enrich Job - 표적 기반 임상정보 보강
50개 표적 + ADC 문맥으로 ClinicalTrials.gov에서 임상정보 검색

Usage:
    python -m services.worker.jobs.clinicaltrials_enrich_job
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# ClinicalTrials.gov API v2
CT_API_BASE = "https://clinicaltrials.gov/api/v2"

# 표적 목록 (dictionaries.py에서 가져옴)
from services.worker.jobs.dictionaries import (
    TARGET_LIST_SOLID, 
    TARGET_LIST_HEME, 
    TARGET_SYNONYMS
)


def search_trials_by_target(target: str, synonyms: list = None, max_results: int = 20) -> list:
    """
    표적 + ADC 문맥으로 ClinicalTrials.gov 검색
    
    Query: (target OR synonyms) AND ("antibody-drug conjugate" OR "ADC" OR "immunoconjugate")
    """
    if not target:
        return []
    
    # 동의어 포함 검색어 구성
    target_terms = [target]
    if synonyms:
        target_terms.extend(synonyms)
    
    target_query = " OR ".join([f'"{t}"' for t in target_terms])
    adc_context = '("antibody-drug conjugate" OR "antibody drug conjugate" OR "ADC" OR "immunoconjugate")'
    
    query = f"({target_query}) AND {adc_context}"
    
    try:
        url = f"{CT_API_BASE}/studies"
        params = {
            "query.term": query,
            "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION,COMPLETED,TERMINATED",
            "pageSize": min(max_results, 50),
            "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,LeadSponsorName,StartDate",
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get("studies", [])
        
    except Exception as e:
        print(f"  ! Search failed for {target}: {e}")
        return []


def extract_trial_info(study: dict) -> dict | None:
    """
    임상시험 데이터에서 핵심 정보 추출
    """
    try:
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        design_module = protocol.get("designModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        
        nct_id = id_module.get("nctId", "")
        title = id_module.get("briefTitle", "")
        
        # Phase 정보
        phases = design_module.get("phases", [])
        phase = phases[0] if phases else "Unknown"
        
        # Status 정보
        overall_status = status_module.get("overallStatus", "")
        
        # 약물명 추출
        drug_names = []
        interventions = arms_module.get("interventions", [])
        for intervention in interventions:
            if intervention.get("type") in ["DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT"]:
                name = intervention.get("name", "")
                if name:
                    drug_names.append(name)
        
        # 질환 정보
        conditions = conditions_module.get("conditions", [])
        
        return {
            "nct_id": nct_id,
            "title": title[:500] if title else "",
            "phase": phase,
            "status": overall_status,
            "conditions": conditions[:5],
            "drug_names": drug_names[:5],
            "sponsor": sponsor_module.get("leadSponsor", {}).get("name", "")
        }
        
    except Exception:
        return None


def rank_trials(trials: list) -> list:
    """
    대표 Trial 선정을 위한 순위 매기기
    Phase 3 > Phase 2 > Phase 1
    Status: Recruiting > Active > Completed > Terminated
    """
    def get_score(trial_info: dict) -> int:
        score = 0
        
        # Phase 점수
        phase = trial_info.get("phase", "").upper()
        if "PHASE3" in phase or "PHASE 3" in phase:
            score += 300
        elif "PHASE2" in phase or "PHASE 2" in phase:
            score += 200
        elif "PHASE1" in phase or "PHASE 1" in phase:
            score += 100
        
        # Status 점수
        status = trial_info.get("status", "").upper()
        if "RECRUITING" in status:
            score += 40
        elif "ACTIVE" in status:
            score += 30
        elif "COMPLETED" in status:
            score += 20
        elif "TERMINATED" in status:
            score += 10
        
        return score
    
    return sorted(trials, key=get_score, reverse=True)


def add_to_review_queue(supabase, seed_item_id: str, queue_type: str, proposed_patch: dict, 
                        confidence: float = 0.5, evidence: list = None):
    """Review Queue에 제안 추가"""
    try:
        supabase.table("golden_review_queue").insert({
            "seed_item_id": seed_item_id,
            "queue_type": queue_type,
            "proposed_patch": proposed_patch,
            "evidence_refs": evidence or [],
            "confidence": confidence,
            "status": "pending"
        }).execute()
    except Exception as e:
        print(f"  ! Failed to add to review_queue: {e}")


def is_field_verified(field_verified: dict, field: str) -> bool:
    """필드가 verified 상태인지 확인"""
    if not field_verified or not isinstance(field_verified, dict):
        return False
    return field_verified.get(field, False)


def execute_clinicaltrials_enrich_job(limit: int = 100, force_update: bool = False) -> dict:
    """
    Main job: golden_seed_items의 표적으로 ClinicalTrials.gov에서 임상정보 검색 및 보강
    
    규칙:
    - verified 필드는 자동 업데이트 금지 (Review Queue로 제안)
    - clinical_phase/program_status가 비어있는 항목 대상
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Missing Supabase credentials"}
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. 임상정보가 부족한 항목 조회
    query = supabase.table("golden_seed_items") \
        .select("id, drug_name_canonical, target, resolved_target_symbol, clinical_phase, program_status, clinical_nct_id_primary, evidence_refs, field_verified") \
        .or_("clinical_phase.is.null,clinical_phase.eq.,program_status.is.null,program_status.eq.") \
        .limit(limit)
    
    result = query.execute()
    seeds = result.data or []
    
    print(f"[clinicaltrials_enrich_job] Processing {len(seeds)} seeds without clinical info...")
    
    enriched_count = 0
    queued_count = 0
    failed_count = 0
    
    for seed in seeds:
        seed_id = seed["id"]
        drug_name = seed.get("drug_name_canonical", "Unknown")
        target = seed.get("resolved_target_symbol") or seed.get("target", "")
        field_verified = seed.get("field_verified") or {}
        current_evidence = seed.get("evidence_refs") or []
        
        print(f"\n[{drug_name}] Target: {target}")
        
        if not target:
            print("  ! No target, skipping")
            failed_count += 1
            continue
        
        # 2. 표적으로 ClinicalTrials 검색
        synonyms = TARGET_SYNONYMS.get(target, [])
        studies = search_trials_by_target(target, synonyms, max_results=10)
        
        if not studies:
            print(f"  → No trials found for {target}")
            failed_count += 1
            continue
        
        # 3. Trial 정보 추출 및 순위 매기기
        trial_infos = []
        for study in studies:
            info = extract_trial_info(study)
            if info and info.get("nct_id"):
                trial_infos.append(info)
        
        if not trial_infos:
            print(f"  → No valid trial info extracted")
            failed_count += 1
            continue
        
        # 대표 Trial 선정
        ranked = rank_trials(trial_infos)
        best_trial = ranked[0]
        
        nct_id = best_trial["nct_id"]
        phase = best_trial["phase"]
        status = best_trial["status"]
        
        print(f"  → Best: {nct_id} | {phase} | {status}")
        
        # 4. 업데이트 데이터 준비
        update_data = {}
        proposed_patch = {}
        
        # clinical_phase
        if not seed.get("clinical_phase"):
            if is_field_verified(field_verified, "clinical_phase") and not force_update:
                proposed_patch["clinical_phase"] = {
                    "old": seed.get("clinical_phase", ""),
                    "new": phase,
                    "source": "clinicaltrials",
                    "evidence": [{"type": "NCT", "id": nct_id}]
                }
            else:
                update_data["clinical_phase"] = phase
        
        # program_status
        if not seed.get("program_status"):
            if is_field_verified(field_verified, "program_status") and not force_update:
                proposed_patch["program_status"] = {
                    "old": seed.get("program_status", ""),
                    "new": status,
                    "source": "clinicaltrials",
                    "evidence": [{"type": "NCT", "id": nct_id}]
                }
            else:
                update_data["program_status"] = status
        
        # clinical_nct_id_primary
        if not seed.get("clinical_nct_id_primary"):
            update_data["clinical_nct_id_primary"] = nct_id
        
        # evidence_refs에 NCT 추가
        if isinstance(current_evidence, str):
            import json
            try:
                current_evidence = json.loads(current_evidence)
            except:
                current_evidence = []
        
        nct_evidence = {"type": "NCT", "id": nct_id, "url": f"https://clinicaltrials.gov/study/{nct_id}"}
        existing_ncts = [e.get("id") for e in current_evidence if e.get("type") == "NCT"]
        
        if nct_id not in existing_ncts:
            updated_evidence = current_evidence + [nct_evidence]
            update_data["evidence_refs"] = updated_evidence
        
        # 5. 업데이트 실행
        if update_data:
            try:
                supabase.table("golden_seed_items").update(update_data).eq("id", seed_id).execute()
                print(f"  ✓ Updated: phase={update_data.get('clinical_phase', '-')}, status={update_data.get('program_status', '-')}")
                enriched_count += 1
            except Exception as e:
                print(f"  ✗ Update failed: {e}")
                failed_count += 1
        
        # 6. Review Queue에 제안 추가 (Verified 필드용)
        if proposed_patch:
            add_to_review_queue(
                supabase, seed_id, "enrichment_update",
                proposed_patch,
                confidence=0.8,
                evidence=[{"type": "NCT", "id": nct_id}]
            )
            queued_count += 1
            print(f"  → Queued verified field updates")
    
    return {
        "success": True,
        "processed": len(seeds),
        "enriched": enriched_count,
        "queued": queued_count,
        "failed": failed_count
    }


if __name__ == "__main__":
    result = execute_clinicaltrials_enrich_job()
    print(f"\n=== Job Complete ===")
    print(f"Processed: {result.get('processed', 0)}")
    print(f"Enriched: {result.get('enriched', 0)}")
    print(f"Queued: {result.get('queued', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
