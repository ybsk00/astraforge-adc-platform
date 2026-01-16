import structlog
from datetime import datetime
from supabase import Client

logger = structlog.get_logger()


async def recommendation_job(ctx, target_set: str = "golden_candidates"):
    """
    Recommendation Job
    Calculates confidence scores for candidates based on the active scoring policy.
    """
    db: Client = ctx["db"]
    logger.info("recommendation_job_started", target_set=target_set)

    # 1. Fetch Active Policy
    policy_res = (
        await db.table("scoring_policies")
        .select("*")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not policy_res.data:
        logger.error("no_active_policy")
        return {"status": "failed", "error": "No active scoring policy found"}

    policy = policy_res.data[0]
    weights = policy["weights"]
    logger.info("policy_loaded", version=policy["policy_version"], weights=weights)

    # 2. Fetch Candidates
    # For now, we process all. In production, use pagination or 'needs_scoring' flag.
    candidates_res = await db.table(target_set).select("*").execute()
    candidates = candidates_res.data

    updated_count = 0

    for cand in candidates:
        try:
            # 3. Calculate Score
            # Components: Evidence, Similarity, Risk, Fit

            # Evidence Score (0.0 - 1.0)
            # Based on evidence_refs count or is_final
            evidence_score = 0.0
            refs = cand.get("evidence_refs")
            if refs and len(refs) > 0:
                evidence_score = min(len(refs) * 0.2, 1.0)  # Cap at 5 refs
            elif cand.get("is_final"):
                evidence_score = 1.0  # Approved/Final implies high evidence

            # Similarity Score (0.0 - 1.0)
            # For Golden Set, it's 1.0 (self-similarity). For new designs, would be Tanimoto.
            similarity_score = 1.0  # Placeholder

            # Risk Score (0.0 - 1.0, higher is better/safer)
            # Placeholder
            risk_score = 0.8

            # Fit Score (0.0 - 1.0)
            # Placeholder
            fit_score = 0.8

            # Weighted Sum
            final_score = (
                weights.get("evidence", 0) * evidence_score
                + weights.get("similarity", 0) * similarity_score
                + weights.get("risk", 0) * risk_score
                + weights.get("fit", 0) * fit_score
            )

            # Normalize to 0-100 or 0-1?
            # Schema comment says "Ranking score". Usually 0-1 or 0-100.
            # Let's use 0-100 for display, or 0-1 float.
            # Schema says "float". Let's stick to 0.0-1.0 range for consistency with weights.
            # But seed_job used 0-100.
            # "confidence_score" in seed_job was 0-100.
            # I should probably normalize to 0-100 if that's the convention.
            final_score_100 = final_score * 100

            # 4. Update Candidate
            # We also store the breakdown in evidence_json or a new column?
            # evidence_json is good.
            evidence_data = cand.get("evidence_json") or {}
            evidence_data["score_breakdown"] = {
                "evidence": evidence_score,
                "similarity": similarity_score,
                "risk": risk_score,
                "fit": fit_score,
                "policy_version": policy["policy_version"],
            }

            await (
                db.table(target_set)
                .update(
                    {
                        "confidence_score": final_score_100,
                        "evidence_json": evidence_data,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", cand["id"])
                .execute()
            )

            updated_count += 1

        except Exception as e:
            logger.error("scoring_failed", id=cand["id"], error=str(e))

    logger.info("recommendation_job_completed", updated=updated_count)
    return {
        "status": "completed",
        "updated": updated_count,
        "policy": policy["policy_version"],
    }
