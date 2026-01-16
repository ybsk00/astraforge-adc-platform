"""
Quality Gate Job - Gate 상태 자동 산출 (PASS/NEEDS_REVIEW/BLOCKED)
golden_seed_items 스캔하여 승격 가능 여부 판단

Usage:
    python -m services.worker.jobs.quality_gate_job
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def evaluate_gate_status(seed: dict) -> dict:
    """
    Option C 정책에 따른 Gate 상태 평가

    필수 조건 (3개):
    1. resolved_target_symbol 존재
    2. payload_smiles_standardized 존재 OR proxy_smiles_flag=true
    3. evidence_refs >= 1

    권장 (가점):
    - clinical_nct_id_primary 존재
    - rdkit_mw 존재 (RDKit 계산 완료)
    """
    # 필수 조건 체크
    gate1_target = bool(
        seed.get("resolved_target_symbol")
        and seed["resolved_target_symbol"].strip() != ""
    )
    gate2_smiles = bool(seed.get("payload_smiles_standardized")) or seed.get(
        "proxy_smiles_flag", False
    )

    evidence = seed.get("evidence_refs") or []
    if isinstance(evidence, str):
        import json

        try:
            evidence = json.loads(evidence)
        except Exception:
            evidence = []
    gate3_evidence = len(evidence) >= 1

    # 권장 조건 (가점)
    has_nct = bool(seed.get("clinical_nct_id_primary"))
    has_rdkit = seed.get("rdkit_mw") is not None

    # 상태 결정
    required_passed = [gate1_target, gate2_smiles, gate3_evidence]
    passed_count = sum(required_passed)
    total_required = len(required_passed)

    if all(required_passed):
        status = "PASS"
    elif passed_count >= 2:
        status = "NEEDS_REVIEW"
    else:
        status = "BLOCKED"

    # 점수 계산 (0-100)
    base_score = (passed_count / total_required) * 80
    bonus_score = (
        (5 if has_nct else 0)
        + (10 if has_rdkit else 0)
        + (5 if len(evidence) >= 2 else 0)
    )
    total_score = min(100, base_score + bonus_score)

    return {
        "status": status,
        "score": round(total_score, 1),
        "gates": {
            "target_resolved": gate1_target,
            "smiles_ready": gate2_smiles,
            "evidence_exists": gate3_evidence,
            "nct_available": has_nct,
            "rdkit_computed": has_rdkit,
        },
        "passed_count": passed_count,
        "total_required": total_required,
        "evidence_count": len(evidence),
    }


def execute_quality_gate_job(limit: int = 100) -> dict:
    """
    Main job: golden_seed_items 스캔하여 gate_status 업데이트
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Missing Supabase credentials"}

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 1. 모든 Manual Seed 조회 (is_final=false만)
    result = (
        supabase.table("golden_seed_items")
        .select("*")
        .eq("is_final", False)
        .limit(limit)
        .execute()
    )

    seeds = result.data or []

    print(f"[quality_gate_job] Evaluating {len(seeds)} seeds...")

    pass_count = 0
    review_count = 0
    blocked_count = 0

    for seed in seeds:
        seed_id = seed["id"]
        drug_name = seed.get("drug_name_canonical", "Unknown")

        # 2. Gate 평가
        evaluation = evaluate_gate_status(seed)
        status = evaluation["status"]
        score = evaluation["score"]

        print(f"\n[{drug_name}] {status} (Score: {score})")
        for gate_name, passed in evaluation["gates"].items():
            icon = "✓" if passed else "✗"
            print(f"  {icon} {gate_name}")

        # 3. gate_status 업데이트
        try:
            # gate_status를 lowercase로 저장 (DB 규칙)
            gate_status_db = status.lower().replace("_", "_")
            if status == "PASS":
                gate_status_db = "ready_to_promote"
            elif status == "NEEDS_REVIEW":
                gate_status_db = "needs_review"
            else:
                gate_status_db = "draft"

            supabase.table("golden_seed_items").update(
                {"gate_status": gate_status_db}
            ).eq("id", seed_id).execute()

            if status == "PASS":
                pass_count += 1
            elif status == "NEEDS_REVIEW":
                review_count += 1
            else:
                blocked_count += 1

        except Exception as e:
            print(f"  ✗ Update failed: {e}")

    return {
        "success": True,
        "processed": len(seeds),
        "pass": pass_count,
        "needs_review": review_count,
        "blocked": blocked_count,
    }


if __name__ == "__main__":
    result = execute_quality_gate_job()
    print("\n=== Job Complete ===")
    print(f"PASS (ready_to_promote): {result.get('pass', 0)}")
    print(f"NEEDS_REVIEW: {result.get('needs_review', 0)}")
    print(f"BLOCKED: {result.get('blocked', 0)}")
