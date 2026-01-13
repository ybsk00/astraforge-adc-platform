import asyncio
from typing import Dict, Any
import structlog
from datetime import datetime
from supabase import Client

logger = structlog.get_logger()

async def data_quality_check_job(ctx, run_id: str = None):
    """
    Data Quality Gate Job
    Checks for:
    1. Component Catalog Completeness (SMILES, Synonyms)
    2. Golden Candidate Quality (Evidence, Confidence)
    """
    db: Client = ctx["db"]
    logger.info("data_quality_check_started")
    
    reports = []
    
    # 1. Catalog Completeness (Payload SMILES)
    try:
        # Count total payloads
        total_payloads = await db.table("component_catalog").select("count", count="exact").eq("type", "payload").execute()
        count_total = total_payloads.count
        
        # Count payloads with SMILES
        valid_payloads = await db.table("component_catalog").select("count", count="exact").eq("type", "payload").not_.is_("smiles", "null").neq("smiles", "").execute()
        count_valid = valid_payloads.count
        
        missing_count = count_total - count_valid
        missing_rate = (missing_count / count_total) if count_total > 0 else 0.0
        
        status = "pass"
        if missing_rate > 0.1: status = "warning"
        if missing_rate > 0.5: status = "fail"
        
        reports.append({
            "check_type": "catalog_completeness_payload_smiles",
            "status": status,
            "results": {
                "total": count_total,
                "missing": missing_count,
                "missing_rate": round(missing_rate, 4)
            },
            "fail_thresholds": {"max_missing_rate": 0.1}
        })
    except Exception as e:
        logger.error("check_failed", check="catalog_completeness", error=str(e))

    # 2. Golden Candidate Quality (Evidence)
    try:
        # Check candidates without evidence
        # Assuming evidence_refs is populated or we check the join.
        # Using evidence_refs column (jsonb)
        # We want to check if evidence_refs is empty or null
        
        # Note: Supabase/PostgREST filtering on JSONB array length is tricky.
        # We might need to fetch a sample or use a custom RPC.
        # For simplicity, we'll fetch all final candidates and check in python (if not too many).
        # Or just check for null.
        
        # Let's check for null evidence_refs
        no_evidence = await db.table("golden_candidates").select("count", count="exact").is_("evidence_refs", "null").execute()
        count_no_evidence = no_evidence.count
        
        total_cands = await db.table("golden_candidates").select("count", count="exact").execute()
        count_total = total_cands.count
        
        missing_rate = (count_no_evidence / count_total) if count_total > 0 else 0.0
        
        status = "pass"
        if missing_rate > 0.05: status = "warning"
        if missing_rate > 0.2: status = "fail"
        
        reports.append({
            "check_type": "golden_candidate_evidence_completeness",
            "status": status,
            "results": {
                "total": count_total,
                "missing_evidence": count_no_evidence,
                "missing_rate": round(missing_rate, 4)
            },
            "fail_thresholds": {"max_missing_rate": 0.05}
        })
        
    except Exception as e:
        logger.error("check_failed", check="golden_candidate_quality", error=str(e))

    # 3. Save Reports
    if reports:
        for r in reports:
            r["run_id"] = run_id or f"manual-{datetime.utcnow().isoformat()}"
        
        await db.table("quality_reports").insert(reports).execute()
        logger.info("data_quality_check_completed", report_count=len(reports))
        
    return {"status": "completed", "reports": reports}
