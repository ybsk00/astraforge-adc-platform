"""
ClinicalTrials Auto Collect Job - 새 ADC 후보 자동 수집
ClinicalTrials.gov에서 ADC 관련 임상시험을 검색하여 golden_candidates에 저장

Usage:
    python -m services.worker.jobs.clinicaltrials_auto_collect_job
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


def search_adc_trials(
    query_terms: str = "antibody drug conjugate", max_results: int = 50
) -> list:
    """
    ClinicalTrials.gov에서 ADC 관련 임상시험 검색
    """
    try:
        url = f"{CT_API_BASE}/studies"
        params = {
            "query.term": query_terms,
            "query.cond": "cancer OR tumor OR neoplasm OR carcinoma",
            "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION,COMPLETED",
            "pageSize": min(max_results, 100),
            "fields": "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,Condition,InterventionName,InterventionType,StartDate,CompletionDate,LeadSponsorName",
            "format": "json",
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  ! API Error: {response.status_code}")
            return []

        data = response.json()
        studies = data.get("studies", [])

        return studies

    except Exception as e:
        print(f"  ! Search failed: {e}")
        return []


def extract_drug_info(study: dict) -> dict | None:
    """
    임상시험 데이터에서 약물 정보 추출
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
        title = id_module.get("briefTitle", "") or id_module.get("officialTitle", "")

        # 개입(약물) 정보 추출
        interventions = arms_module.get("interventions", [])
        drug_names = []
        for intervention in interventions:
            if intervention.get("type") in [
                "DRUG",
                "BIOLOGICAL",
                "COMBINATION_PRODUCT",
            ]:
                name = intervention.get("name", "")
                if name and (
                    "adc" in name.lower()
                    or "conjugate" in name.lower()
                    or "mab" in name.lower()
                    or "zumab" in name.lower()
                    or "ximab" in name.lower()
                    or "tumab" in name.lower()
                ):
                    drug_names.append(name)

        if not drug_names:
            # 제목에서 약물명 추출 시도
            adc_keywords = [
                "adc",
                "conjugate",
                "vedotin",
                "deruxtecan",
                "emtansine",
                "govitecan",
                "tesirine",
                "ozogamicin",
                "maytansine",
            ]
            for keyword in adc_keywords:
                if keyword in title.lower():
                    drug_names = [title.split(" for ")[0].split(" in ")[0][:100]]
                    break

        if not drug_names:
            return None

        # 질환/타겟 정보
        conditions = conditions_module.get("conditions", [])

        # Phase 정보
        phases = design_module.get("phases", [])
        phase = phases[0] if phases else "Unknown"

        # 스폰서 정보
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor_name = lead_sponsor.get("name", "Unknown")

        return {
            "nct_id": nct_id,
            "drug_name": drug_names[0] if drug_names else "",
            "title": title[:500],
            "phase": phase,
            "status": status_module.get("overallStatus", ""),
            "conditions": conditions[:5],
            "sponsor": sponsor_name,
            "start_date": status_module.get("startDateStruct", {}).get("date", ""),
        }

    except Exception:
        return None


def save_to_candidates(supabase, candidates: list) -> dict:
    """
    golden_candidates 테이블에 저장
    """
    inserted = 0
    duplicates = 0

    for candidate in candidates:
        try:
            # 중복 체크 (NCT ID 또는 drug_name 기준)
            existing = (
                supabase.table("golden_candidates")
                .select("id")
                .or_(
                    f"source_ref.eq.{candidate['nct_id']},drug_name.ilike.{candidate['drug_name']}"
                )
                .limit(1)
                .execute()
            )

            if existing.data:
                duplicates += 1
                continue

            # 새 후보 저장
            record = {
                "drug_name": candidate["drug_name"],
                "target": "",  # resolve_ids_job에서 채움
                "source_ref": candidate["nct_id"],
                "review_status": "pending",
                "metadata": {
                    "title": candidate["title"],
                    "phase": candidate["phase"],
                    "status": candidate["status"],
                    "conditions": candidate["conditions"],
                    "sponsor": candidate["sponsor"],
                    "collected_at": datetime.utcnow().isoformat(),
                },
            }

            supabase.table("golden_candidates").insert(record).execute()
            inserted += 1
            print(f"  ✓ Added: {candidate['drug_name']} ({candidate['nct_id']})")

        except Exception as e:
            print(f"  ! Save failed: {e}")

    return {"inserted": inserted, "duplicates": duplicates}


def execute_clinicaltrials_auto_collect(max_results: int = 50) -> dict:
    """
    Main job: ClinicalTrials.gov에서 ADC 후보 자동 수집
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Missing Supabase credentials"}

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("[clinicaltrials_auto_collect] Searching ClinicalTrials.gov...")

    # 1. ADC 관련 검색 쿼리들
    search_queries = [
        "antibody drug conjugate",
        "ADC immunoconjugate",
        "vedotin OR deruxtecan OR emtansine",
        "trastuzumab conjugate OR sacituzumab",
    ]

    all_candidates = []

    for query in search_queries:
        print(f"\n  Searching: {query}")
        studies = search_adc_trials(
            query, max_results=max_results // len(search_queries)
        )

        for study in studies:
            drug_info = extract_drug_info(study)
            if drug_info and drug_info["drug_name"]:
                # 중복 제거
                existing = [
                    c for c in all_candidates if c["nct_id"] == drug_info["nct_id"]
                ]
                if not existing:
                    all_candidates.append(drug_info)
                    print(
                        f"    Found: {drug_info['drug_name']} ({drug_info['nct_id']})"
                    )

    print(f"\n  Total unique candidates: {len(all_candidates)}")

    # 2. golden_candidates에 저장
    if all_candidates:
        result = save_to_candidates(supabase, all_candidates)
    else:
        result = {"inserted": 0, "duplicates": 0}

    return {
        "success": True,
        "searched": len(search_queries),
        "found": len(all_candidates),
        "inserted": result["inserted"],
        "duplicates": result["duplicates"],
    }


if __name__ == "__main__":
    result = execute_clinicaltrials_auto_collect(max_results=100)
    print("\n=== Job Complete ===")
    print(f"Found: {result.get('found', 0)}")
    print(f"Inserted: {result.get('inserted', 0)}")
    print(f"Duplicates: {result.get('duplicates', 0)}")
