import asyncio
import structlog
from datetime import datetime
from supabase import Client
from typing import Dict, Any

logger = structlog.get_logger()

async def report_job(ctx, target_set: str = "golden_candidates"):
    """
    Report Job
    Generates summary statistics for the target candidate set.
    """
    db: Client = ctx["db"]
    logger.info("report_job_started", target_set=target_set)
    
    # 1. Fetch Candidates
    res = await db.table(target_set).select("*").execute()
    candidates = res.data
    
    if not candidates:
        return {"status": "completed", "message": "No candidates found"}
    
    # 2. Calculate Statistics
    total_count = len(candidates)
    approved_count = sum(1 for c in candidates if c.get("approval_status") == "Approved")
    final_count = sum(1 for c in candidates if c.get("is_final"))
    
    # Score Distribution
    scores = [c.get("confidence_score", 0) for c in candidates if c.get("confidence_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    # Top Candidates
    top_candidates = sorted(candidates, key=lambda x: x.get("confidence_score", 0), reverse=True)[:5]
    top_summary = [{"name": c["drug_name"], "score": c.get("confidence_score")} for c in top_candidates]
    
    # Component Distribution
    targets = {}
    payloads = {}
    for c in candidates:
        t = c.get("target") or "Unknown"
        p = c.get("payload") or "Unknown"
        targets[t] = targets.get(t, 0) + 1
        payloads[p] = payloads.get(p, 0) + 1
        
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "target_set": target_set,
        "total_count": total_count,
        "approved_count": approved_count,
        "final_count": final_count,
        "average_score": round(avg_score, 2),
        "top_candidates": top_summary,
        "distribution": {
            "targets": dict(sorted(targets.items(), key=lambda x: x[1], reverse=True)[:5]),
            "payloads": dict(sorted(payloads.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    }
    
    logger.info("report_generated", report=report)
    
    # Optionally save to a reports table if it existed, or just return
    return {"status": "completed", "report": report}
