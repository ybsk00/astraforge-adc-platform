"""
Ingestion API
로그 조회, 통계 집계 API
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


# ============================================================
# Ingestion Logs API
# ============================================================


class LogEntry(BaseModel):
    id: str
    source: str
    phase: str
    status: str
    duration_ms: Optional[int]
    records_fetched: int
    records_new: int
    records_updated: int
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: str


class LogsResponse(BaseModel):
    logs: list[LogEntry]
    total: int
    limit: int
    offset: int


@router.get("/logs", response_model=LogsResponse)
async def get_ingestion_logs(
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Ingestion 로그 조회"""
    from app.db.supabase import get_client

    db = get_client()

    query = db.table("ingestion_logs").select("*", count="exact")

    if source:
        query = query.eq("source", source)
    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    logs = []
    for row in result.data:
        logs.append(
            LogEntry(
                id=str(row["id"]),
                source=row["source"],
                phase=row.get("phase", ""),
                status=row["status"],
                duration_ms=row.get("duration_ms"),
                records_fetched=row.get("records_fetched", 0),
                records_new=row.get("records_new", 0),
                records_updated=row.get("records_updated", 0),
                error_code=row.get("error_code"),
                error_message=row.get("error_message"),
                created_at=row["created_at"],
            )
        )

    return LogsResponse(
        logs=logs,
        total=result.count or len(logs),
        limit=limit,
        offset=offset,
    )


# ============================================================
# Ingestion Stats API
# ============================================================


class OverallStats(BaseModel):
    total_logs: int
    total_fetched: int
    total_new: int
    successful_runs: int
    failed_runs: int
    sources_active: int
    last_24h_runs: int
    last_24h_fetched: int


@router.get("/stats", response_model=OverallStats)
async def get_overall_stats():
    """전체 Ingestion 통계"""
    from app.db.supabase import get_client

    db = get_client()

    # 전체 로그 조회
    all_logs = (
        db.table("ingestion_logs")
        .select("id, source, status, records_fetched, records_new, created_at")
        .execute()
    )

    total_logs = len(all_logs.data)
    total_fetched = sum(log.get("records_fetched", 0) for log in all_logs.data)
    total_new = sum(log.get("records_new", 0) for log in all_logs.data)
    successful_runs = len(
        [log for log in all_logs.data if log.get("status") == "completed"]
    )
    failed_runs = len([log for log in all_logs.data if log.get("status") == "failed"])

    # Active sources
    sources = set(log.get("source") for log in all_logs.data if log.get("source"))

    # Last 24 hours
    now = datetime.utcnow()
    cutoff = (now - timedelta(hours=24)).isoformat()

    recent_logs = [log for log in all_logs.data if log.get("created_at", "") >= cutoff]
    last_24h_runs = len(recent_logs)
    last_24h_fetched = sum(log.get("records_fetched", 0) for log in recent_logs)

    return OverallStats(
        total_logs=total_logs,
        total_fetched=total_fetched,
        total_new=total_new,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        sources_active=len(sources),
        last_24h_runs=last_24h_runs,
        last_24h_fetched=last_24h_fetched,
    )


class SourceStats(BaseModel):
    source: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    total_fetched: int
    total_new: int
    total_updated: int
    avg_duration_ms: float


@router.get("/stats/{source}", response_model=SourceStats)
async def get_source_stats(source: str):
    """특정 소스 통계"""
    from app.db.supabase import get_client

    db = get_client()

    logs = db.table("ingestion_logs").select("*").eq("source", source).execute()

    if not logs.data:
        return SourceStats(
            source=source,
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            total_fetched=0,
            total_new=0,
            total_updated=0,
            avg_duration_ms=0,
        )

    total_runs = len(logs.data)
    successful_runs = len(
        [log for log in logs.data if log.get("status") == "completed"]
    )
    failed_runs = len([log for log in logs.data if log.get("status") == "failed"])
    total_fetched = sum(log.get("records_fetched", 0) for log in logs.data)
    total_new = sum(log.get("records_new", 0) for log in logs.data)
    total_updated = sum(log.get("records_updated", 0) for log in logs.data)

    durations = [
        log.get("duration_ms", 0) for log in logs.data if log.get("duration_ms")
    ]
    avg_duration_ms = sum(durations) / len(durations) if durations else 0

    return SourceStats(
        source=source,
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        total_fetched=total_fetched,
        total_new=total_new,
        total_updated=total_updated,
        avg_duration_ms=avg_duration_ms,
    )


# ============================================================
# Ingestion History API
# ============================================================


class DailyStats(BaseModel):
    date: str
    runs: int
    fetched: int
    new: int
    errors: int


@router.get("/history")
async def get_ingestion_history(
    days: int = Query(7, ge=1, le=30),
    source: Optional[str] = None,
):
    """일별 Ingestion 히스토리"""
    from app.db.supabase import get_client

    db = get_client()

    now = datetime.utcnow()
    cutoff = (now - timedelta(days=days)).isoformat()

    query = (
        db.table("ingestion_logs")
        .select("source, status, records_fetched, records_new, created_at")
        .gte("created_at", cutoff)
    )

    if source:
        query = query.eq("source", source)

    result = query.execute()

    # 일별 집계
    daily = {}
    for log in result.data:
        date = log.get("created_at", "")[:10]
        if date not in daily:
            daily[date] = {"runs": 0, "fetched": 0, "new": 0, "errors": 0}

        daily[date]["runs"] += 1
        daily[date]["fetched"] += log.get("records_fetched", 0)
        daily[date]["new"] += log.get("records_new", 0)
        if log.get("status") == "failed":
            daily[date]["errors"] += 1

    # 날짜 정렬
    history = [DailyStats(date=date, **stats) for date, stats in sorted(daily.items())]

    return {"history": history}
