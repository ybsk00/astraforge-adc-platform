"""
Phase C Worker Jobs
ClinicalTrials.gov, openFDA 동기화 Jobs
"""

from datetime import datetime
from typing import Dict, Any
import structlog
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv


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
        os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )


# ============================================================
# ClinicalTrials.gov Jobs
# ============================================================


async def clinicaltrials_fetch_job(ctx, seed: Dict[str, Any]):
    """
    ClinicalTrials.gov 임상시험 동기화 Job

    Args:
        ctx: Arq 컨텍스트
        seed: {"conditions": [...]} or {"interventions": [...]} or {"nct_ids": [...]}
    """
    logger.info("clinicaltrials_fetch_job_started", seed=seed)

    db = get_supabase()
    start_time = datetime.utcnow()

    # 로그 생성을 가장 먼저 수행
    log_id = (
        db.table("ingestion_logs")
        .insert(
            {
                "source": "clinicaltrials",
                "phase": "sync",
                "status": "started",
                "meta": {"seed": seed},
            }
        )
        .execute()
        .data[0]["id"]
    )

    from app.connectors.base import generate_query_hash

    # 기본 쿼리 설정
    if (
        not seed.get("nct_ids")
        and not seed.get("conditions")
        and not seed.get("interventions")
    ):
        logger.info("clinicaltrials_using_default_targets")
        # T-DM1 관련 임상시험 (NCT04064359: KATE-3)
        seed["nct_ids"] = ["NCT04064359"]

        db.table("ingestion_logs").update(
            {"meta": {"seed": seed, "note": "Using default ClinicalTrials target"}}
        ).eq("id", log_id).execute()

    query_hash = generate_query_hash("clinicaltrials", str(seed), seed)

    db.table("ingestion_cursors").upsert(
        {
            "source": "clinicaltrials",
            "query_hash": query_hash,
            "status": "running",
            "config": seed,
            "updated_at": datetime.utcnow().isoformat(),
        },
        on_conflict="source,query_hash",
    ).execute()

    try:
        from app.connectors.clinicaltrials import ClinicalTrialsConnector

        connector = ClinicalTrialsConnector(db)
        result = await connector.run(seed, max_pages=10)

        stats = result.get("stats", {})

        db.table("ingestion_cursors").update(
            {
                "status": "idle",
                "last_success_at": datetime.utcnow().isoformat(),
                "stats": stats,
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("source", "clinicaltrials").eq("query_hash", query_hash).execute()

        db.table("ingestion_logs").update(
            {
                "status": "completed",
                "duration_ms": result.get("duration_ms", 0),
                "records_fetched": stats.get("fetched", 0),
                "records_new": stats.get("new", 0),
                "records_updated": stats.get("updated", 0),
            }
        ).eq("id", log_id).execute()

        logger.info("clinicaltrials_fetch_job_completed", stats=stats)
        return result

    except Exception as e:
        logger.error("clinicaltrials_fetch_job_failed", error=str(e))

        db.table("ingestion_cursors").update(
            {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("source", "clinicaltrials").eq("query_hash", query_hash).execute()

        db.table("ingestion_logs").update(
            {
                "status": "failed",
                "error_message": str(e),
                "duration_ms": int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
            }
        ).eq("id", log_id).execute()

        raise


# ============================================================
# openFDA Jobs
# ============================================================


async def openfda_fetch_job(ctx, seed: Dict[str, Any]):
    """
    openFDA 안전 신호 동기화 Job

    Args:
        ctx: Arq 컨텍스트
        seed: {"drug_names": [...]} or {"generic_names": [...]} or {"brand_names": [...]}
    """
    logger.info("openfda_fetch_job_started", seed=seed)

    db = get_supabase()
    start_time = datetime.utcnow()

    # 로그 생성을 가장 먼저 수행
    log_id = (
        db.table("ingestion_logs")
        .insert(
            {
                "source": "openfda",
                "phase": "sync",
                "status": "started",
                "meta": {"seed": seed},
            }
        )
        .execute()
        .data[0]["id"]
    )

    from app.connectors.base import generate_query_hash

    # 기본 쿼리 설정
    if (
        not seed.get("drug_names")
        and not seed.get("generic_names")
        and not seed.get("brand_names")
    ):
        logger.info("openfda_using_default_targets")
        # T-DM1 (Trastuzumab emtansine)
        seed["generic_names"] = ["Trastuzumab emtansine"]

        db.table("ingestion_logs").update(
            {"meta": {"seed": seed, "note": "Using default openFDA target"}}
        ).eq("id", log_id).execute()

    query_hash = generate_query_hash("openfda", str(seed), seed)

    db.table("ingestion_cursors").upsert(
        {
            "source": "openfda",
            "query_hash": query_hash,
            "status": "running",
            "config": seed,
            "updated_at": datetime.utcnow().isoformat(),
        },
        on_conflict="source,query_hash",
    ).execute()

    try:
        from app.connectors.openfda import OpenFDAConnector

        connector = OpenFDAConnector(db)
        result = await connector.run(seed, max_pages=10)

        stats = result.get("stats", {})

        db.table("ingestion_cursors").update(
            {
                "status": "idle",
                "last_success_at": datetime.utcnow().isoformat(),
                "stats": stats,
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("source", "openfda").eq("query_hash", query_hash).execute()

        db.table("ingestion_logs").update(
            {
                "status": "completed",
                "duration_ms": result.get("duration_ms", 0),
                "records_fetched": stats.get("fetched", 0),
                "records_new": stats.get("new", 0),
                "records_updated": stats.get("updated", 0),
            }
        ).eq("id", log_id).execute()

        logger.info("openfda_fetch_job_completed", stats=stats)
        return result

    except Exception as e:
        logger.error("openfda_fetch_job_failed", error=str(e))

        db.table("ingestion_cursors").update(
            {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("source", "openfda").eq("query_hash", query_hash).execute()

        db.table("ingestion_logs").update(
            {
                "status": "failed",
                "error_message": str(e),
                "duration_ms": int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
            }
        ).eq("id", log_id).execute()

        raise
