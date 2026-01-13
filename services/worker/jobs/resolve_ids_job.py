import asyncio
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime
from supabase import Client

logger = structlog.get_logger()

# Query Profiles
QUERY_PROFILES = {
    "payload_discovery": {
        "description": "Discover new payloads from literature/patents",
        "keywords": ["ADC payload", "cytotoxic", "tubulin inhibitor", "topoisomerase inhibitor"],
        "min_confidence": 0.6
    },
    "linker_discovery": {
        "description": "Discover new linkers",
        "keywords": ["ADC linker", "cleavable linker", "peptide linker"],
        "min_confidence": 0.6
    },
    "adc_validation": {
        "description": "Validate existing ADCs",
        "keywords": ["antibody-drug conjugate", "clinical trial"],
        "min_confidence": 0.8
    },
    "clinical_candidate_pool": {
        "description": "Broad collection of clinical candidates",
        "keywords": ["Phase 1", "Phase 2", "Phase 3", "solid tumor"],
        "min_confidence": 0.7
    }
}

async def resolve_text(db: Client, text: str, entity_type: str) -> Dict[str, Any]:
    """
    Resolve text to a canonical entity ID using caching.
    
    1. Check mapping_table cache.
    2. If miss, try to match with component_catalog (canonical_name, synonyms).
    3. Store result in mapping_table.
    """
    if not text:
        return {"id": None, "confidence": 0.0, "source": "empty"}

    normalized_key = text.strip().lower()
    
    # 1. Check Cache
    cache_res = await db.table("mapping_table").select("*").eq("normalized_key", normalized_key).eq("entity_type", entity_type).execute()
    if cache_res.data:
        entry = cache_res.data[0]
        return {
            "id": entry["canonical_id"],
            "confidence": entry["mapping_confidence"],
            "source": "cache",
            "resolver_version": entry["resolver_version"]
        }

    # 2. Resolve Logic
    # Fetch candidates from catalog
    # Note: In production, we might want to use full text search or similarity search.
    # For now, exact match on name/canonical_name/synonyms.
    
    # Try Exact Match on Name/Canonical Name
    catalog_res = await db.table("component_catalog").select("id, name, canonical_name, synonyms").eq("type", entity_type).execute()
    
    match_id = None
    confidence = 0.0
    match_method = "none"
    
    for item in catalog_res.data:
        # Check canonical name
        if item.get("canonical_name") and item["canonical_name"].lower() == normalized_key:
            match_id = item["id"]
            confidence = 1.0
            match_method = "canonical_exact"
            break
        
        # Check name
        if item["name"].lower() == normalized_key:
            match_id = item["id"]
            confidence = 0.95 # Name might be slightly less reliable than canonical
            match_method = "name_exact"
            break
            
        # Check synonyms
        if item.get("synonyms"):
            for syn in item["synonyms"]:
                if syn.lower() == normalized_key:
                    match_id = item["id"]
                    confidence = 0.9
                    match_method = "synonym_exact"
                    break
        if match_id: break
    
    # TODO: Add fuzzy matching or suffix matching (e.g. "vedotin" -> MMAE) here
    if not match_id and entity_type == "payload":
        if "vedotin" in normalized_key:
            # Find MMAE
            for item in catalog_res.data:
                if item["name"] == "MMAE":
                    match_id = item["id"]
                    confidence = 0.7 # Suffix heuristic
                    match_method = "suffix_heuristic"
                    break
        elif "deruxtecan" in normalized_key:
             for item in catalog_res.data:
                if item["name"] == "DXd":
                    match_id = item["id"]
                    confidence = 0.7
                    match_method = "suffix_heuristic"
                    break

    # 3. Store in Cache
    mapping_entry = {
        "source_text": text,
        "normalized_key": normalized_key,
        "canonical_id": match_id,
        "entity_type": entity_type,
        "mapping_confidence": confidence,
        "evidence_refs": [{"method": match_method}],
        "resolver_version": "v1.0",
        "updated_at": datetime.utcnow().isoformat()
    }
    
    try:
        await db.table("mapping_table").upsert(mapping_entry, on_conflict="normalized_key, entity_type").execute()
    except Exception as e:
        logger.error("mapping_cache_upsert_failed", error=str(e))

    return {
        "id": match_id,
        "confidence": confidence,
        "source": "computed",
        "resolver_version": "v1.0"
    }

async def resolve_batch_job(ctx, items: List[Dict[str, str]]):
    """
    Batch job to resolve a list of items.
    items: [{"text": "...", "type": "..."}]
    """
    # Implementation for batch processing if needed
    pass
