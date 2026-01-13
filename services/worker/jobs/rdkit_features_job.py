import asyncio
import structlog
from datetime import datetime
from supabase import Client

logger = structlog.get_logger()

async def rdkit_batch_job(ctx, batch_size: int = 50):
    """
    Batch job to calculate RDKit descriptors for components that are missing them.
    """
    db: Client = ctx["db"]
    logger.info("rdkit_batch_job_started")
    
    # 1. Fetch components needing calculation
    # Criteria: status='pending' OR (status='active' AND properties->rdkit IS NULL)
    # Note: Complex OR queries in Supabase/PostgREST can be tricky.
    # We'll fetch 'pending' first, then check for missing properties if needed.
    
    # Fetch pending
    res = await db.table("component_catalog").select("id, properties").eq("status", "pending").limit(batch_size).execute()
    candidates = res.data
    
    if not candidates:
        # If no pending, check for active but missing rdkit (optional maintenance)
        # This might be expensive to query without a specific index/column.
        # Skipping for now to focus on new items.
        logger.info("rdkit_batch_job_no_pending_items")
        return {"status": "completed", "processed": 0}

    processed_count = 0
    from chem.descriptors import calculate_descriptors # Assuming this exists or we mock it

    for item in candidates:
        try:
            props = item.get("properties", {})
            smiles = props.get("smiles")
            
            if not smiles:
                # Mark as active but skipped (or failed?)
                # If it's a payload without SMILES, maybe fail?
                # For now, just mark active to stop reprocessing.
                await db.table("component_catalog").update({
                    "status": "active",
                    "compute_error": "No SMILES",
                    "computed_at": datetime.utcnow().isoformat()
                }).eq("id", item["id"]).execute()
                continue
                
            # Calculate
            descriptors = calculate_descriptors(smiles)
            
            if descriptors:
                props["rdkit"] = {"descriptors": descriptors}
                await db.table("component_catalog").update({
                    "properties": props,
                    "status": "active",
                    "computed_at": datetime.utcnow().isoformat()
                }).eq("id", item["id"]).execute()
                processed_count += 1
            else:
                await db.table("component_catalog").update({
                    "status": "failed",
                    "compute_error": "Calculation failed",
                    "computed_at": datetime.utcnow().isoformat()
                }).eq("id", item["id"]).execute()
                
        except Exception as e:
            logger.error("rdkit_calc_error", id=item["id"], error=str(e))
            await db.table("component_catalog").update({
                "status": "failed",
                "compute_error": str(e),
                "computed_at": datetime.utcnow().isoformat()
            }).eq("id", item["id"]).execute()

    logger.info("rdkit_batch_job_completed", processed=processed_count)
    return {"status": "completed", "processed": processed_count}
