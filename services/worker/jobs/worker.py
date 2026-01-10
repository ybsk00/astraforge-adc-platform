"""
Arq Worker Settings and Job Definitions
"""
import asyncio
from datetime import datetime
from arq.connections import RedisSettings
import os
from dotenv import load_dotenv
import structlog
from supabase import create_client, Client
from pathlib import Path

# .env 파일 로드
def find_env():
    current = Path(__file__).resolve()
    for _ in range(5):
        current = current.parent
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
    return ".env"

load_dotenv(find_env())

logger = structlog.get_logger()


def get_supabase() -> Client:
    """Supabase 클라이언트"""
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )


# === Job Functions ===

async def compute_component_descriptors(ctx, component_id: str):
    """
    RDKit 디스크립터 계산 Job
    
    1. 컴포넌트 조회
    2. SMILES 추출
    3. RDKit 디스크립터 계산
    4. properties.rdkit.descriptors 업데이트
    5. status = 'active' 또는 'failed'
    """
    logger.info("compute_descriptors_started", component_id=component_id)
    
    db = get_supabase()
    
    try:
        # 1. 컴포넌트 조회
        result = db.table("component_catalog").select("*").eq("id", component_id).execute()
        if not result.data:
            logger.error("component_not_found", component_id=component_id)
            return {"status": "failed", "error": "Component not found"}
        
        component = result.data[0]
        properties = component.get("properties", {})
        smiles = properties.get("smiles")
        
        if not smiles:
            # SMILES 없으면 바로 active로 전환 (디스크립터 계산 불필요)
            db.table("component_catalog").update({
                "status": "active",
                "computed_at": datetime.utcnow().isoformat()
            }).eq("id", component_id).execute()
            
            logger.info("no_smiles_skipped", component_id=component_id)
            return {"status": "active", "message": "No SMILES - skipped"}
        
        # 2. 디스크립터 계산
        from chem.descriptors import calculate_descriptors
        descriptors = calculate_descriptors(smiles)
        
        if descriptors is None:
            # 계산 실패
            db.table("component_catalog").update({
                "status": "failed",
                "compute_error": "Invalid SMILES or calculation failed",
                "computed_at": datetime.utcnow().isoformat()
            }).eq("id", component_id).execute()
            
            logger.error("computation_failed", component_id=component_id)
            return {"status": "failed", "error": "Computation failed"}
        
        # 3. 결과 저장
        properties["rdkit"] = {"descriptors": descriptors}
        
        db.table("component_catalog").update({
            "properties": properties,
            "status": "active",
            "compute_error": None,
            "computed_at": datetime.utcnow().isoformat()
        }).eq("id", component_id).execute()
        
        logger.info("compute_descriptors_completed", 
                   component_id=component_id,
                   mw=descriptors.get("mw"))
        
        return {"status": "active", "descriptors": descriptors}
        
    except Exception as e:
        logger.error("compute_descriptors_failed", component_id=component_id, error=str(e))
        
        # 에러 기록
        try:
            db.table("component_catalog").update({
                "status": "failed",
                "compute_error": str(e),
                "computed_at": datetime.utcnow().isoformat()
            }).eq("id", component_id).execute()
        except Exception:
            pass
        
        return {"status": "failed", "error": str(e)}


# Import full design_run_execute implementation (optional - requires scoring module)
try:
    from jobs.run_execute_job import design_run_execute
except ImportError as e:
    logger.warning("design_run_execute not available", error=str(e))
    # Fallback stub if scoring module not available
    async def design_run_execute(ctx, run_id: str):
        logger.error("design_run_execute called but scoring module not available")
        return {"status": "error", "message": "Scoring module not available in this worker"}


async def pubmed_ingest_job(ctx, workspace_id: str, query: str, cursor: dict = None):
    """
    PubMed 문헌 수집 Job (Phase 3에서 구현)
    """
    logger.info("pubmed_ingest_started", workspace_id=workspace_id, query=query)
    
    # TODO: Phase 3에서 구현
    stats = {
        "fetched_docs": 0,
        "new_docs": 0,
        "new_chunks": 0,
        "embedded_chunks": 0
    }
    
    logger.info("pubmed_ingest_completed", workspace_id=workspace_id, stats=stats)
    return {"status": "completed", "stats": stats}


async def embed_chunks_job(ctx, chunk_ids: list):
    """
    청크 임베딩 생성 Job (Phase 3에서 구현)
    """
    logger.info("embed_chunks_started", count=len(chunk_ids))
    
    # TODO: Phase 3에서 구현
    logger.info("embed_chunks_completed", count=len(chunk_ids))
    return {"status": "completed", "embedded": len(chunk_ids)}


async def poll_db_jobs(ctx):
    """
    Supabase DB를 폴링하여 대기 중인 작업을 찾아 실행합니다.
    Locking 및 Retry 로직을 포함합니다.
    """
    db: Client = ctx["db"]
    worker_id = os.getenv("HOSTNAME", "worker-default")
    now = datetime.utcnow().isoformat()
    stale_timeout = 600 # 10분
    
    logger.info("polling_db_jobs_started")

    # 1. Connector Runs 폴링 및 잠금
    # 대상: queued 상태 OR (failed 상태 AND 재시도 가능) OR (running 상태 AND stale lock)
    connector_query = db.table("connector_runs").select("id, status, attempt").or_(
        "status.eq.queued,"
        f"and(status.eq.failed,next_retry_at.lte.{now},attempt.lt.3),"
        f"and(status.eq.running,locked_at.lte.{(datetime.utcnow().timestamp() - stale_timeout)})"
    ).limit(5).execute()

    if connector_result := connector_query.data:
        from jobs.connector_executor import execute_connector_run
        for run in connector_result:
            # 원자적 잠금 시도
            lock_res = db.table("connector_runs").update({
                "status": "running",
                "locked_by": worker_id,
                "locked_at": now,
                "started_at": now
            }).eq("id", run["id"]).or_(
                "status.eq.queued,"
                "status.eq.failed,"
                f"and(status.eq.running,locked_at.lte.{(datetime.utcnow().timestamp() - stale_timeout)})"
            ).execute()
            
            if lock_res.data:
                logger.info("connector_run_locked", run_id=run["id"])
                await execute_connector_run(ctx, run["id"])

    # 2. Design Runs 폴링 및 잠금
    design_query = db.table("design_runs").select("id, status, attempt").or_(
        "status.eq.queued,"
        f"and(status.eq.failed,next_retry_at.lte.{now},attempt.lt.3),"
        f"and(status.eq.running,locked_at.lte.{(datetime.utcnow().timestamp() - stale_timeout)})"
    ).limit(5).execute()

    if design_result := design_query.data:
        from jobs.run_execute_job import design_run_execute
        for run in design_result:
            lock_res = db.table("design_runs").update({
                "status": "running",
                "locked_by": worker_id,
                "locked_at": now
            }).eq("id", run["id"]).or_(
                "status.eq.queued,"
                "status.eq.failed,"
                f"and(status.eq.running,locked_at.lte.{(datetime.utcnow().timestamp() - stale_timeout)})"
            ).execute()

            if lock_res.data:
                logger.info("design_run_locked", run_id=run["id"])
                await design_run_execute(ctx, run["id"])

    logger.info("polling_db_jobs_completed")
    return {"status": "polled"}


# === Startup/Shutdown ===

async def startup(ctx):
    """워커 시작 시 초기화"""
    logger.info("worker_started")
    ctx["db"] = get_supabase()


async def shutdown(ctx):
    """워커 종료 시 정리"""
    logger.info("worker_stopped")


# === Worker Settings ===

class WorkerSettings:
    """Arq Worker 설정"""
    
    # Phase A Jobs
    from jobs.pubmed_job import pubmed_fetch_job, pubmed_chunk_job, pubmed_embed_job
    from jobs.uniprot_job import uniprot_fetch_job, uniprot_enrich_from_catalog_job, uniprot_batch_sync_job
    
    # Real Data Integration Jobs
    from jobs.parse_candidate_csv_job import parse_candidate_csv_job
    from jobs.index_literature_job import index_literature_job
    
    # Phase B Jobs
    from jobs.meta_sync_job import opentargets_fetch_job, hpa_fetch_job, chembl_fetch_job, pubchem_fetch_job, enrich_targets_batch_job
    
    # Phase C Jobs
    from jobs.clinical_job import clinicaltrials_fetch_job, openfda_fetch_job
    
    # Phase F Jobs
    from jobs.seed_job import seed_fetch_job
    from jobs.resolve_job import resolve_fetch_job
    
    functions = [
        compute_component_descriptors,
        design_run_execute,
        pubmed_ingest_job,
        embed_chunks_job,
        poll_db_jobs,
        # Real Data Jobs
        parse_candidate_csv_job,
        index_literature_job,
        # Phase A connector jobs
        pubmed_fetch_job,
        pubmed_chunk_job,
        pubmed_embed_job,
        uniprot_fetch_job,
        uniprot_enrich_from_catalog_job,
        uniprot_batch_sync_job,
        # Phase B connector jobs
        opentargets_fetch_job,
        hpa_fetch_job,
        chembl_fetch_job,
        pubchem_fetch_job,
        enrich_targets_batch_job,
        # Phase C connector jobs
        clinicaltrials_fetch_job,
        openfda_fetch_job,
        # Phase F jobs
        seed_fetch_job,
        resolve_fetch_job,
    ]
    
    on_startup = startup
    on_shutdown = shutdown
    
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    
    # 큐 설정
    queue_name = "adc_worker"
    max_jobs = 10
    job_timeout = 3600  # 1시간
    
    # 재시도 설정
    max_tries = 3
    retry_delay = 60

