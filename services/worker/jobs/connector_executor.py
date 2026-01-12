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
        
        # 3-1. 시드 기반 실행 (Seed Set ID가 있는 경우)
        if seed_set_id:
            # 시드 기반 자동 쿼리 생성 및 수집
            from .domain_resolver import resolve_entities, generate_queries
            
            # 엔티티 ID 해결 (EFO, Ensembl 등)
            await resolve_entities(ctx, seed_set_id)
            
            # 쿼리 생성
            queries = await generate_queries(ctx, seed_set_id, connector.get("name", "").lower())
            
            if connector_type == "api" and connector.get("name", "").lower() == "pubmed":
                from .pubmed_job import pubmed_fetch_job
                total_fetched = 0
                for q in queries[:10]: # MVP에서는 상위 10개 쿼리만 우선 실행
                    res = await pubmed_fetch_job(ctx, {"query": q["query"], "retmax": 50})
                    total_fetched += res.get("fetched", 0)
                result_summary = {"total_fetched": total_fetched, "queries_count": len(queries)}
            elif connector_type == "api" and connector.get("name", "").lower() == "opentargets":
                from .opentargets_job import opentargets_fetch_job
                total_fetched = 0
                for q in queries[:20]: # 상위 20개 조합 우선 실행
                    res = await opentargets_fetch_job(ctx, q)
                    if res.get("status") == "completed":
                        total_fetched += res.get("fetched", 0)
                result_summary = {"total_fetched": total_fetched, "queries_count": len(queries)}
            else:
                result_summary = {"message": f"Seed-based ingestion for {connector_type}/{connector.get('name')} not fully implemented"}
        
        # 3-2. 일반 실행 (직접 실행 또는 스케줄링)
        else:
            if connector_type == "api":
                connector_name = connector.get("name", "").lower()
                config = connector.get("config", {})
                
                if connector_name == "pubmed":
                    from .pubmed_job import pubmed_fetch_job
                    seed = {"query": config.get("query", "antibody drug conjugate"), "retmax": config.get("limit", 100)}
                    result_summary = await pubmed_fetch_job(ctx, seed)
                    
                elif connector_name == "uniprot":
                    from .uniprot_job import uniprot_fetch_job
                    result_summary = await uniprot_fetch_job(ctx, config)
                    
                elif connector_name == "opentargets":
                    from .meta_sync_job import opentargets_fetch_job
                    result_summary = await opentargets_fetch_job(ctx, config)
                    
                elif connector_name == "clinicaltrials":
                    from .clinical_job import clinicaltrials_fetch_job
                    result_summary = await clinicaltrials_fetch_job(ctx, config)
                    
                elif connector_name == "openfda":
                    from .clinical_job import openfda_fetch_job
                    result_summary = await openfda_fetch_job(ctx, config)
                    
                else:
                    result_summary = {"message": f"No job implementation for API connector: {connector_name}"}

            elif connector_type == "db":
                connector_name = connector.get("name", "").lower()
                config = connector.get("config", {})
                
                if connector_name == "hpa":
                    from .meta_sync_job import hpa_fetch_job
                    result_summary = await hpa_fetch_job(ctx, config)
                elif connector_name == "chembl":
                    from .meta_sync_job import chembl_fetch_job
                    result_summary = await chembl_fetch_job(ctx, config)
                elif connector_name == "pubchem":
                    from .meta_sync_job import pubchem_fetch_job
                    result_summary = await pubchem_fetch_job(ctx, config)
                else:
                    result_summary = {"message": f"No job implementation for DB connector: {connector_name}"}

            elif connector_type == "system":
                connector_name = connector.get("name", "").lower()
                
                if connector_name == "seed":
                    from .seed_job import seed_fetch_job
                    result_summary = await seed_fetch_job(ctx, connector.get("config", {}))
                elif connector_name == "resolve":
                    from .resolve_job import resolve_fetch_job
                    result_summary = await resolve_fetch_job(ctx, connector.get("config", {}))
                else:
                    result_summary = {"message": f"No job implementation for System connector: {connector_name}"}

            elif connector_type == "golden_seed":
                # Golden Seed 자동화 파이프라인 실행
                from .golden_seed_job import execute_golden_seed
                result_summary = await execute_golden_seed(ctx, run_id, connector.get("config", {}))
                
            elif connector_type == "RAG_SEED_FROM_PUBMED":
                # PubMed RAG 기반 Seed 생성
                from .rag_seed_job import rag_seed_query_job
                result_summary = await rag_seed_query_job(ctx, run_id, connector.get("config", {}))

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
