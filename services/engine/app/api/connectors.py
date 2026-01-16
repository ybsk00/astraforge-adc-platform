"""
Connectors API Endpoints
커넥터 상태 조회, 실행, 재시도 관리
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.queue import get_redis_pool

router = APIRouter()
logger = structlog.get_logger()


# ============================================================
# Connector Registry
# ============================================================

CONNECTOR_REGISTRY = {
    "pubmed": {
        "name": "PubMed",
        "description": "NCBI PubMed 문헌 수집",
        "category": "literature",
        "rate_limit": "3-10 req/sec (API Key 유무)",
    },
    "uniprot": {
        "name": "UniProt",
        "description": "UniProt 단백질 정보",
        "category": "target",
        "rate_limit": "5 req/sec",
    },
    "opentargets": {
        "name": "Open Targets",
        "description": "Target-Disease 연관 스코어",
        "category": "target",
        "rate_limit": "Standard GraphQL",
    },
    "hpa": {
        "name": "Human Protein Atlas",
        "description": "조직/세포 발현 데이터",
        "category": "expression",
        "rate_limit": "5 req/sec",
    },
    "chembl": {
        "name": "ChEMBL",
        "description": "화합물/활성 데이터",
        "category": "compound",
        "rate_limit": "5 req/sec",
    },
    "pubchem": {
        "name": "PubChem",
        "description": "화합물 구조/식별자",
        "category": "compound",
        "rate_limit": "5 req/sec",
    },
    "clinicaltrials": {
        "name": "ClinicalTrials.gov",
        "description": "임상시험 정보",
        "category": "clinical",
        "rate_limit": "Standard",
    },
    "openfda": {
        "name": "openFDA",
        "description": "FDA 안전 신호",
        "category": "safety",
        "rate_limit": "240 req/min",
    },
    "seed": {
        "name": "Seed Data",
        "description": "Gold Standard 데이터 시딩",
        "category": "system",
        "rate_limit": "None",
    },
    "resolve": {
        "name": "Resolve IDs",
        "description": "외부 ID 식별 (UniProt/PubChem)",
        "category": "system",
        "rate_limit": "External APIs",
    },
}


# ============================================================
# Schemas
# ============================================================


class ConnectorRunRequest(BaseModel):
    """커넥터 실행 요청"""

    query: Optional[str] = None
    uniprot_ids: Optional[list] = None
    gene_symbols: Optional[list] = None
    ensembl_ids: Optional[list] = None
    chembl_ids: Optional[list] = None
    cids: Optional[list] = None
    inchi_keys: Optional[list] = None
    names: Optional[list] = None
    limit: int = 100
    batch_mode: bool = False
    config: dict = {}


class ConnectorConfigUpdate(BaseModel):
    """커넥터 설정 업데이트"""

    schedule: Optional[str] = None  # cron expression
    rate_limit: Optional[float] = None
    enabled: Optional[bool] = None


# ============================================================
# Endpoints
# ============================================================


@router.get("")
async def list_connectors():
    """
    전체 커넥터 목록 및 상태
    """
    try:
        db = get_db()

        connectors = []

        for source, info in CONNECTOR_REGISTRY.items():
            # 모든 커서 상태 조회 (통계 합산용)
            try:
                cursor_result = (
                    db.table("ingestion_cursors")
                    .select("status, last_success_at, stats, error_message, updated_at")
                    .eq("source", source)
                    .order("last_success_at", desc=True)
                    .execute()
                )
                cursors_data = cursor_result.data or []
            except Exception as e:
                logger.error("cursor_fetch_failed", source=source, error=str(e))
                cursors_data = []

            # 통계 합산 및 상태 결정
            total_fetched = 0
            total_new = 0
            total_updated = 0
            running_count = 0
            failed_count = 0
            last_success = None
            last_error = None

            for cursor in cursors_data:
                stats = cursor.get("stats", {}) or {}
                total_fetched += stats.get("fetched", 0) or 0
                total_new += stats.get("new", 0) or 0
                total_updated += stats.get("updated", 0) or 0

                if cursor.get("status") == "running":
                    running_count += 1
                if cursor.get("status") == "failed":
                    failed_count += 1
                    if not last_error:
                        last_error = cursor.get("error_message")

                if cursor.get("last_success_at") and not last_success:
                    last_success = cursor.get("last_success_at")

            # 전체 상태 결정: running > failed > idle
            if running_count > 0:
                overall_status = "running"
            elif failed_count > 0 and not last_success:
                overall_status = "failed"
            else:
                overall_status = "idle"

            connectors.append(
                {
                    "source": source,
                    **info,
                    "status": overall_status,
                    "last_success_at": last_success,
                    "stats": {
                        "fetched": total_fetched,
                        "new": total_new,
                        "updated": total_updated,
                    },
                    "error_message": last_error if overall_status == "failed" else None,
                }
            )

        return {"connectors": connectors}
    except Exception as e:
        logger.error("list_connectors_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-defaults")
async def setup_default_connectors():
    """
    CONNECTOR_REGISTRY에 정의된 기본 커넥터들을 ingestion_cursors에 등록
    """
    try:
        db = get_db()

        # 현재 등록된 커넥터 소스 목록 조회
        existing_res = db.table("ingestion_cursors").select("source").execute()
        existing_sources = {row["source"] for row in (existing_res.data or [])}

        new_cursors = []
        for source, info in CONNECTOR_REGISTRY.items():
            if source not in existing_sources:
                new_cursors.append(
                    {
                        "source": source,
                        "status": "idle",
                        "cursor": {},
                        "stats": {"fetched": 0, "new": 0, "updated": 0},
                    }
                )

        if new_cursors:
            db.table("ingestion_cursors").insert(new_cursors).execute()

        return {
            "status": "success",
            "message": f"Added {len(new_cursors)} new connectors",
            "added": [c["source"] for c in new_cursors],
        }
    except Exception as e:
        logger.error("setup_defaults_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}")
async def get_connector_detail(source: str):
    """
    커넥터 상세 정보
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    info = CONNECTOR_REGISTRY[source]

    # 모든 커서 조회
    cursors = (
        db.table("ingestion_cursors")
        .select("*")
        .eq("source", source)
        .order("updated_at", desc=True)
        .limit(10)
        .execute()
    )

    # 최근 로그 조회
    logs = (
        db.table("ingestion_logs")
        .select("*")
        .eq("source", source)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    return {"source": source, **info, "cursors": cursors.data, "recent_logs": logs.data}


@router.get("/{source}/status")
async def get_connector_status(source: str):
    """
    커넥터 실시간 상태
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    # 가장 최근 커서
    cursor = (
        db.table("ingestion_cursors")
        .select("*")
        .eq("source", source)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )

    if not cursor.data:
        return {"source": source, "status": "idle", "message": "No ingestion history"}

    return {"source": source, **cursor.data[0]}


@router.post("/{source}/run")
async def run_connector(
    source: str, request: ConnectorRunRequest, background_tasks: BackgroundTasks
):
    """
    커넥터 실행

    백그라운드에서 데이터 수집을 시작합니다.
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        # 이미 실행 중인지 확인
        running = (
            db.table("ingestion_cursors")
            .select("id")
            .eq("source", source)
            .eq("status", "running")
            .execute()
        )

        if running.data:
            raise HTTPException(status_code=409, detail="Connector is already running")

        # 시드 데이터 구성
        seed = request.config.copy()
        if request.query:
            seed["query"] = request.query
        if request.uniprot_ids:
            seed["uniprot_ids"] = request.uniprot_ids
        if request.gene_symbols:
            seed["gene_symbols"] = request.gene_symbols
        if request.ensembl_ids:
            seed["ensembl_ids"] = request.ensembl_ids
        if request.chembl_ids:
            seed["chembl_ids"] = request.chembl_ids
        if request.cids:
            seed["cids"] = request.cids
        if request.inchi_keys:
            seed["inchi_keys"] = request.inchi_keys
        if request.names:
            seed["names"] = request.names
        seed["retmax"] = request.limit
        seed["batch_mode"] = request.batch_mode

        # Job enqueue
        pool = await get_redis_pool()

        job_name = f"{source}_fetch_job"
        job = await pool.enqueue_job(job_name, seed)

        logger.info("connector_run_enqueued", source=source, job_id=job.job_id)

        return {
            "status": "enqueued",
            "source": source,
            "job_id": job.job_id,
            "seed": seed,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("connector_run_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source}/stop")
async def stop_connector(source: str):
    """
    실행 중인 커넥터 중지
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        # 상태를 idle로 변경 (실제 job 취소는 워커에서 처리)
        db.table("ingestion_cursors").update(
            {"status": "idle", "updated_at": datetime.utcnow().isoformat()}
        ).eq("source", source).eq("status", "running").execute()

        logger.info("connector_stop_requested", source=source)

        return {"status": "stop_requested", "source": source}

    except Exception as e:
        logger.error("connector_stop_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source}/retry")
async def retry_connector(source: str):
    """
    실패한 커넥터 재시도
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        # 실패한 커서 조회
        failed = (
            db.table("ingestion_cursors")
            .select("*")
            .eq("source", source)
            .eq("status", "failed")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        if not failed.data:
            raise HTTPException(status_code=404, detail="No failed cursor to retry")

        cursor = failed.data[0]

        # 상태를 idle로 변경
        db.table("ingestion_cursors").update(
            {
                "status": "idle",
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", cursor["id"]).execute()

        # Job enqueue (기존 설정으로)
        pool = await get_redis_pool()
        seed = cursor.get("config", {})

        job_name = f"{source}_fetch_job"
        job = await pool.enqueue_job(job_name, seed, cursor.get("cursor", {}))

        logger.info("connector_retry_enqueued", source=source, cursor_id=cursor["id"])

        return {
            "status": "retry_enqueued",
            "source": source,
            "cursor_id": cursor["id"],
            "job_id": job.job_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("connector_retry_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}/logs")
async def get_connector_logs(
    source: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    커넥터 실행 로그 조회
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        query = (
            db.table("ingestion_logs").select("*", count="exact").eq("source", source)
        )

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)

        result = query.execute()

        return {
            "logs": result.data,
            "total": result.count or 0,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error("connector_logs_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}/stats")
async def get_connector_stats(source: str):
    """
    커넥터 통계
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        # 전체 로그에서 통계 계산
        logs = (
            db.table("ingestion_logs")
            .select(
                "status, records_fetched, records_new, records_updated, duration_ms"
            )
            .eq("source", source)
            .execute()
        )

        stats = {
            "total_runs": len(logs.data),
            "successful_runs": 0,
            "failed_runs": 0,
            "total_fetched": 0,
            "total_new": 0,
            "total_updated": 0,
            "avg_duration_ms": 0,
        }

        durations = []

        for log in logs.data:
            if log["status"] == "completed":
                stats["successful_runs"] += 1
            elif log["status"] == "failed":
                stats["failed_runs"] += 1

            stats["total_fetched"] += log.get("records_fetched", 0) or 0
            stats["total_new"] += log.get("records_new", 0) or 0
            stats["total_updated"] += log.get("records_updated", 0) or 0

            if log.get("duration_ms"):
                durations.append(log["duration_ms"])

        if durations:
            stats["avg_duration_ms"] = sum(durations) / len(durations)

        return stats

    except Exception as e:
        logger.error("connector_stats_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{source}/config")
async def update_connector_config(source: str, config: ConnectorConfigUpdate):
    """
    커넥터 설정 업데이트
    """
    if source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {source}")

    db = get_db()

    try:
        # 기존 커서 또는 새로 생성
        existing = (
            db.table("ingestion_cursors")
            .select("id, config")
            .eq("source", source)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        if existing.data:
            current_config = existing.data[0].get("config", {})
        else:
            current_config = {}

        # 설정 병합
        new_config = {**current_config}
        if config.schedule is not None:
            new_config["schedule"] = config.schedule
        if config.rate_limit is not None:
            new_config["rate_limit"] = config.rate_limit
        if config.enabled is not None:
            new_config["enabled"] = config.enabled

        if existing.data:
            db.table("ingestion_cursors").update(
                {"config": new_config, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", existing.data[0]["id"]).execute()
        else:
            db.table("ingestion_cursors").insert(
                {
                    "source": source,
                    "query_hash": "default",
                    "config": new_config,
                    "status": "idle",
                }
            ).execute()

        logger.info("connector_config_updated", source=source, config=new_config)

        return {"status": "updated", "config": new_config}

    except Exception as e:
        logger.error("connector_config_failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
