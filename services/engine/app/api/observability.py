"""
Observability API Endpoints
커넥터 및 시스템 모니터링 메트릭 제공
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


# ============================================================
# Endpoints
# ============================================================


@router.get("/metrics")
async def get_connector_metrics(
    source: Optional[str] = Query(None, description="Source filter"),
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
):
    """
    커넥터별 처리량 메트릭 조회

    Returns:
        - source별 fetched/new/updated/errors 통계
        - 일별 처리량 트렌드
    """
    db = get_db()

    try:
        # ingestion_logs에서 집계
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        query = db.table("ingestion_logs").select("source, status, meta, created_at")
        query = query.gte("created_at", since)

        if source:
            query = query.eq("source", source)

        result = query.order("created_at", desc=True).limit(1000).execute()

        # 집계
        by_source = {}
        by_day = {}

        for log in result.data:
            src = log.get("source", "unknown")
            status = log.get("status", "unknown")
            meta = log.get("meta", {})

            # Source별 집계
            if src not in by_source:
                by_source[src] = {
                    "total_runs": 0,
                    "completed": 0,
                    "failed": 0,
                    "fetched": 0,
                    "new": 0,
                    "updated": 0,
                    "errors": 0,
                }

            by_source[src]["total_runs"] += 1

            if status == "completed":
                by_source[src]["completed"] += 1
                stats = meta.get("stats", {})
                by_source[src]["fetched"] += stats.get("fetched", 0)
                by_source[src]["new"] += stats.get("new", 0)
                by_source[src]["updated"] += stats.get("updated", 0)
            elif status == "failed":
                by_source[src]["failed"] += 1
                by_source[src]["errors"] += 1

            # 일별 집계
            created = log.get("created_at", "")[:10]  # YYYY-MM-DD
            if created:
                if created not in by_day:
                    by_day[created] = {"runs": 0, "completed": 0, "failed": 0}
                by_day[created]["runs"] += 1
                if status == "completed":
                    by_day[created]["completed"] += 1
                elif status == "failed":
                    by_day[created]["failed"] += 1

        # 성공률 계산
        for src, stats in by_source.items():
            if stats["total_runs"] > 0:
                stats["success_rate"] = round(
                    stats["completed"] / stats["total_runs"] * 100, 1
                )
            else:
                stats["success_rate"] = 0.0

        # 일별 데이터 정렬
        daily_trend = [{"date": date, **data} for date, data in sorted(by_day.items())]

        return {
            "by_source": by_source,
            "daily_trend": daily_trend,
            "period_days": days,
            "total_logs": len(result.data),
        }

    except Exception as e:
        logger.error("metrics_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_recent_errors(
    source: Optional[str] = Query(None, description="Source filter"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    최근 오류 로그 조회
    """
    db = get_db()

    try:
        query = db.table("ingestion_logs").select("*")
        query = query.eq("status", "failed")

        if source:
            query = query.eq("source", source)

        result = query.order("created_at", desc=True).limit(limit).execute()

        errors = []
        for log in result.data:
            meta = log.get("meta", {})
            errors.append(
                {
                    "id": log["id"],
                    "source": log.get("source"),
                    "phase": log.get("phase"),
                    "created_at": log.get("created_at"),
                    "error": meta.get("error") or meta.get("reason") or "Unknown error",
                    "seed": meta.get("seed"),
                }
            )

        return {
            "errors": errors,
            "total": len(errors),
        }

    except Exception as e:
        logger.error("errors_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health():
    """
    시스템 상태 확인
    """
    db = get_db()

    health = {
        "status": "healthy",
        "components": {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Supabase 연결 확인
    try:
        db.table("ingestion_logs").select("id").limit(1).execute()
        health["components"]["database"] = {"status": "up"}
    except Exception as e:
        health["components"]["database"] = {"status": "down", "error": str(e)}
        health["status"] = "degraded"

    # 최근 1시간 내 실패율 확인
    try:
        since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        logs = (
            db.table("ingestion_logs")
            .select("status")
            .gte("created_at", since)
            .execute()
        )

        total = len(logs.data)
        failed = sum(1 for log_item in logs.data if log_item.get("status") == "failed")

        if total > 0:
            failure_rate = failed / total * 100
            health["components"]["connectors"] = {
                "status": "warning" if failure_rate > 30 else "up",
                "total_runs_1h": total,
                "failed_runs_1h": failed,
                "failure_rate": round(failure_rate, 1),
            }
        else:
            health["components"]["connectors"] = {
                "status": "idle",
                "note": "No runs in last hour",
            }
    except Exception as e:
        health["components"]["connectors"] = {"status": "unknown", "error": str(e)}

    return health


@router.get("/cursors")
async def get_cursor_status(
    source: Optional[str] = Query(None, description="Source filter"),
):
    """
    Ingestion 커서 상태 조회
    """
    db = get_db()

    try:
        query = db.table("ingestion_cursors").select("*")

        if source:
            query = query.eq("source", source)

        result = query.order("last_success_at", desc=True).execute()

        cursors = []
        for cursor in result.data:
            stats = cursor.get("stats", {})
            cursors.append(
                {
                    "id": cursor["id"],
                    "source": cursor.get("source"),
                    "status": cursor.get("status"),
                    "cursor": cursor.get("cursor"),
                    "last_success_at": cursor.get("last_success_at"),
                    "fetched": stats.get("fetched", 0),
                    "new": stats.get("new", 0),
                    "updated": stats.get("updated", 0),
                    "errors": stats.get("errors", 0),
                }
            )

        return {
            "cursors": cursors,
            "total": len(cursors),
        }

    except Exception as e:
        logger.error("cursors_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
