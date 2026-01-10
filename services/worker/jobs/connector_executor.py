import asyncio
import structlog
from datetime import datetime
from typing import Dict, Any
from supabase import Client

logger = structlog.get_logger()

async def execute_connector_run(ctx: Dict[str, Any], run_id: str):
    """
    특정 커넥터 실행 작업을 처리합니다.
    
    1. connector_runs 테이블에서 작업 정보 조회
    2. 상태를 'running'으로 변경
    3. 커넥터 타입에 따른 실제 수집 로직 실행
    4. 결과에 따라 'succeeded' 또는 'failed'로 업데이트
    """
    db: Client = ctx["db"]
    
    logger.info("connector_run_execution_started", run_id=run_id)
    
    try:
        # 1. 작업 정보 및 커넥터 정보 조회
        result = db.table("connector_runs").select("*, connectors(*)").eq("id", run_id).execute()
        if not result.data:
            logger.error("connector_run_not_found", run_id=run_id)
            return
        
        run_data = result.data[0]
        connector = run_data.get("connectors")
        
        if not connector:
            logger.error("connector_info_missing", run_id=run_id)
            return

        # 2. 상태 확인 (이미 poll_db_jobs에서 running으로 변경됨)
        # attempt는 여기서 증가시킴
        db.table("connector_runs").update({
            "attempt": run_data.get("attempt", 0) + 1
        }).eq("id", run_id).execute()

        # 3. 커넥터 타입 및 시드 정보 확인
        connector_type = connector.get("type")
        seed_set_id = run_data.get("seed_set_id")
        
        result_summary = {}
        
        if seed_set_id:
            # 시드 기반 자동 쿼리 생성 및 수집
            from jobs.domain_resolver import resolve_entities, generate_queries
            
            # 엔티티 ID 해결 (EFO, Ensembl 등)
            await resolve_entities(ctx, seed_set_id)
            
            # 쿼리 생성
            queries = await generate_queries(ctx, seed_set_id, connector.get("name", "").lower())
            
            if connector_type == "api" and connector.get("name", "").lower() == "pubmed":
                from jobs.pubmed_job import pubmed_fetch_job
                total_fetched = 0
                for q in queries[:10]: # MVP에서는 상위 10개 쿼리만 우선 실행
                    res = await pubmed_fetch_job(ctx, {"query": q["query"], "retmax": 50})
                    total_fetched += res.get("fetched", 0)
                result_summary = {"total_fetched": total_fetched, "queries_count": len(queries)}
            elif connector_type == "api" and connector.get("name", "").lower() == "opentargets":
                from jobs.opentargets_job import opentargets_fetch_job
                total_fetched = 0
                for q in queries[:20]: # 상위 20개 조합 우선 실행
                    res = await opentargets_fetch_job(ctx, q)
                    if res.get("status") == "completed":
                        total_fetched += res.get("fetched", 0)
                result_summary = {"total_fetched": total_fetched, "queries_count": len(queries)}
            else:
                result_summary = {"message": f"Seed-based ingestion for {connector_type}/{connector.get('name')} not fully implemented"}
        
        elif connector_type == "api":
            # API 타입 커넥터 로직 (예시로 PubMed 호출)
            from jobs.pubmed_job import pubmed_fetch_job
            # 커넥터 설정(config)에서 쿼리 등을 가져옴
            config = connector.get("config", {})
            seed = {
                "query": config.get("query", "antibody drug conjugate"),
                "retmax": config.get("limit", 100)
            }
            res = await pubmed_fetch_job(ctx, seed)
            result_summary = res
        elif connector_type == "crawler":
            # 크롤러 타입 로직 (추후 확장)
            result_summary = {"message": "Crawler logic not implemented yet"}
        else:
            raise ValueError(f"Unsupported connector type: {connector_type}")

        # 4. 성공 업데이트
        db.table("connector_runs").update({
            "status": "succeeded",
            "ended_at": datetime.utcnow().isoformat(),
            "result_summary": result_summary,
            "locked_by": None,
            "locked_at": None
        }).eq("id", run_id).execute()
        
        logger.info("connector_run_execution_succeeded", run_id=run_id)

    except Exception as e:
        logger.error("connector_run_execution_failed", run_id=run_id, error=str(e))
        
        # 재시도 시간 계산 (지수 백오프: 1분, 5분, 15분)
        attempt = run_data.get("attempt", 0) + 1
        delays = [60, 300, 900]
        delay = delays[min(attempt - 1, len(delays) - 1)]
        from datetime import timedelta
        next_retry = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()

        # 실패 업데이트 및 Lock 해제
        db.table("connector_runs").update({
            "status": "failed",
            "ended_at": datetime.utcnow().isoformat(),
            "error_json": {"error": str(e)},
            "next_retry_at": next_retry,
            "locked_by": None,
            "locked_at": None
        }).eq("id", run_id).execute()

        # 알림 생성
        try:
            db.table("alerts").insert({
                "type": "error",
                "source": f"connector:{connector.get('name', 'unknown')}",
                "message": f"Connector run failed: {str(e)}",
                "details": {"run_id": run_id, "attempt": attempt}
            }).execute()
        except Exception as alert_err:
            logger.error("failed_to_create_alert", error=str(alert_err))
