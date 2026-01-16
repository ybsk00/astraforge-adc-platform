"""
Worker Queue Client
Arq 워커에 Job을 enqueue하기 위한 클라이언트
"""

from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
import structlog

logger = structlog.get_logger()


async def get_redis_pool():
    """Redis 연결 풀 생성 - Worker 큐 이름과 일치해야 함"""
    return await create_pool(
        RedisSettings.from_dsn(settings.REDIS_URL),
        default_queue_name="adc_worker",  # Worker의 queue_name과 일치
    )


async def enqueue_compute_descriptors(component_id: str):
    """
    RDKit 디스크립터 계산 Job enqueue

    Args:
        component_id: 컴포넌트 UUID
    """
    try:
        pool = await get_redis_pool()
        job = await pool.enqueue_job("compute_component_descriptors", component_id)
        logger.info(
            "job_enqueued",
            job_id=job.job_id,
            function="compute_component_descriptors",
            component_id=component_id,
        )
        return job.job_id
    except Exception as e:
        logger.warning(
            "job_enqueue_failed",
            function="compute_component_descriptors",
            component_id=component_id,
            error=str(e),
        )
        return None


async def enqueue_design_run(run_id: str):
    """
    Design Run 실행 Job enqueue

    Args:
        run_id: Run UUID
    """
    try:
        pool = await get_redis_pool()
        job = await pool.enqueue_job("design_run_execute", run_id)
        logger.info(
            "job_enqueued",
            job_id=job.job_id,
            function="design_run_execute",
            run_id=run_id,
        )
        return job.job_id
    except Exception as e:
        logger.warning(
            "job_enqueue_failed",
            function="design_run_execute",
            run_id=run_id,
            error=str(e),
        )
        return None


async def enqueue_pubmed_ingest(workspace_id: str, query: str, cursor: dict = None):
    """
    PubMed 문헌 수집 Job enqueue
    """
    try:
        pool = await get_redis_pool()
        job = await pool.enqueue_job("pubmed_ingest_job", workspace_id, query, cursor)
        logger.info(
            "job_enqueued",
            job_id=job.job_id,
            function="pubmed_ingest_job",
            workspace_id=workspace_id,
        )
        return job.job_id
    except Exception as e:
        logger.warning("job_enqueue_failed", function="pubmed_ingest_job", error=str(e))
        return None
        return None


async def enqueue_golden_seed_run(run_id: str, config: dict):
    """
    Golden Seed 수집 Job enqueue

    Args:
        run_id: Run UUID
        config: 실행 설정 (targets, limit 등)
    """
    try:
        pool = await get_redis_pool()
        job = await pool.enqueue_job("execute_golden_seed", run_id, config)
        logger.info(
            "job_enqueued",
            job_id=job.job_id,
            function="execute_golden_seed",
            run_id=run_id,
            config_targets=config.get("targets"),
        )
        return job.job_id
    except Exception as e:
        logger.warning(
            "job_enqueue_failed",
            function="execute_golden_seed",
            run_id=run_id,
            error=str(e),
        )
        return None
