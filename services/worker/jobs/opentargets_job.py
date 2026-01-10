import asyncio
import structlog
from datetime import datetime
from typing import Dict, Any, List
from supabase import Client
import os
import httpx

logger = structlog.get_logger()

async def opentargets_fetch_job(ctx: Dict[str, Any], seed: Dict[str, Any]):
    """
    Open Targets API를 통해 타겟-질병 연관성 데이터를 수집합니다.
    """
    db: Client = ctx["db"]
    log = logger.bind(seed=seed)
    log.info("opentargets_fetch_started")
    
    target_id = seed.get("target_id") # Ensembl ID
    disease_id = seed.get("disease_id") # EFO ID
    
    if not target_id or not disease_id:
        log.error("missing_ids", target_id=target_id, disease_id=disease_id)
        return {"status": "failed", "error": "Missing target_id or disease_id"}

    # GraphQL Query
    query = """
    query association($targetId: String!, $diseaseId: String!) {
      association(targetId: $targetId, diseaseId: $diseaseId) {
        score
        datatypeScores {
          id
          score
        }
      }
    }
    """
    variables = {"targetId": target_id, "diseaseId": disease_id}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.platform.opentargets.org/api/v4/graphql",
                json={"query": query, "variables": variables}
            )
            resp.raise_for_status()
            data = resp.json()
            
            association = data.get("data", {}).get("association")
            if not association:
                log.info("no_association_found")
                return {"status": "completed", "fetched": 0}
            
            # Raw Data 저장
            import json
            import hashlib
            payload = association
            checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            
            db.table("raw_source_records").upsert({
                "source": "opentargets",
                "external_id": f"{target_id}_{disease_id}",
                "payload": payload,
                "checksum": checksum,
                "fetched_at": datetime.utcnow().isoformat()
            }, on_conflict="source,external_id").execute()
            
            # Target Profile 업데이트 (jsonb 필드에 연관성 정보 추가)
            # 실제로는 target_profiles 테이블의 구조에 맞춰 업데이트 로직 필요
            # 여기서는 간단히 로그만 남김
            log.info("association_fetched", score=association.get("score"))
            
            return {"status": "completed", "fetched": 1, "score": association.get("score")}
            
    except Exception as e:
        log.error("opentargets_fetch_failed", error=str(e))
        return {"status": "failed", "error": str(e)}
