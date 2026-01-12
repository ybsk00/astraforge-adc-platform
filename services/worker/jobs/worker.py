"""
Arq Worker Settings and Job Definitions
"""
import asyncio
from datetime import datetime
from arq.connections import RedisSettings
from arq.cron import cron
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
    from .run_execute_job import design_run_execute
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

    # Stale Timeout 계산 (ISO 포맷)
    stale_threshold = (datetime.utcnow().timestamp() - stale_timeout)
    stale_threshold_iso = datetime.fromtimestamp(stale_threshold).isoformat()

    # 1. Connector Runs 폴링 (RPC 기반 Atomic Pickup)
    try:
        # RPC 호출로 안전하게 작업 가져오기 (SKIP LOCKED)
        rpc_res = db.rpc("pick_connector_run", {"worker_id": worker_id}).execute()
        
        if rpc_res.data:
            run = rpc_res.data
            logger.info("connector_run_picked", run_id=run["id"], worker_id=worker_id)
            
            # 커넥터 실행 로직 호출
            # 커넥터 실행 로직 호출
            from .connector_executor import execute_connector_run
            await execute_connector_run(ctx, run["id"])
            
    except Exception as e:
        logger.error("connector_polling_error", error=str(e))

    # 2. Design Runs 폴링 및 잠금
    design_query = db.table("design_runs").select("id, status, attempt").or_(
        "status.eq.queued,"
        f"and(status.eq.failed,next_retry_at.lte.{now},attempt.lt.3),"
        f"and(status.eq.running,locked_at.lte.{stale_threshold_iso})"
    ).limit(5).execute()

    if design_result := design_query.data:
        from .run_execute_job import design_run_execute
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
    # Phase A Jobs
    from .pubmed_job import pubmed_fetch_job, pubmed_chunk_job, pubmed_embed_job
    from .uniprot_job import uniprot_fetch_job, uniprot_enrich_from_catalog_job, uniprot_batch_sync_job
    
    # Real Data Integration Jobs
    from .parse_candidate_csv_job import parse_candidate_csv_job
    from .index_literature_job import index_literature_job
    
    # Phase B Jobs
    from .meta_sync_job import opentargets_fetch_job, hpa_fetch_job, chembl_fetch_job, pubchem_fetch_job, enrich_targets_batch_job
    
    # Phase C Jobs
    from .clinical_job import clinicaltrials_fetch_job, openfda_fetch_job
    
    # Phase F Jobs
    from .seed_job import seed_fetch_job
    from .resolve_job import resolve_fetch_job
    from .golden_seed_job import execute_golden_seed
    from .rag_seed_job import rag_seed_query_job
    
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
        rag_seed_query_job,
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

    # Cron Jobs (주기적 실행)
    cron_jobs = [
        cron(poll_db_jobs, second={0, 10, 20, 30, 40, 50}) # 10초마다 실행
    ]

