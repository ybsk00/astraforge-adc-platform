from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import structlog
from app.core.database import get_db
from app.core.security import require_admin, mask_log_entry

router = APIRouter(dependencies=[Depends(require_admin)])
logger = structlog.get_logger()

# === Schemas ===


class QueueStats(BaseModel):
    name: str
    active: int
    queued: int
    failed: int


class AuditLog(BaseModel):
    id: str
    timestamp: str
    actor: Optional[str]
    action: str
    target: Optional[str]
    metadata: Dict[str, Any]


class SystemLog(BaseModel):
    id: str
    timestamp: str
    level: str
    service: str
    message: str
    meta: Dict[str, Any]


# === Endpoints ===


@router.get("/queues", response_model=List[QueueStats])
async def get_queue_stats():
    """
    작업 큐 상태 조회 (Admin Only)
    """
    # TODO: Redis/Arq 연동하여 실제 큐 상태 조회
    # 현재는 Mock 반환 (Redis 연결 설정 필요)
    return [
        {"name": "design_run_queue", "active": 0, "queued": 0, "failed": 0},
        {"name": "ingestion_queue", "active": 0, "queued": 0, "failed": 0},
        {"name": "email_queue", "active": 0, "queued": 0, "failed": 0},
    ]


@router.post("/queues/retry")
async def retry_job(job_id: str):
    """
    실패한 작업 재시도 (Admin Only)
    """
    # TODO: Arq job retry logic
    return {"status": "retried", "job_id": job_id}


@router.get("/audit", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = Query(50), action: Optional[str] = None, db=Depends(get_db)
):
    """
    감사 로그 조회 (Real DB, Admin Only)
    """
    try:
        query = db.table("audit_events").select("*").order("created_at", desc=True)

        if action:
            query = query.eq("event_type", action)

        result = query.limit(limit).execute()

        items = []
        for row in result.data or []:
            entry = {
                "id": row["id"],
                "timestamp": row["created_at"],
                "actor": row.get("user_id"),
                "action": row["event_type"],
                "target": str(row.get("entity_id") or ""),
                "metadata": row.get("details") or {},
            }
            # Mask sensitive data in metadata
            masked_entry = mask_log_entry(entry)
            items.append(masked_entry)

        return items

    except Exception as e:
        logger.error("get_audit_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=List[SystemLog])
async def get_system_logs(
    limit: int = Query(100), level: Optional[str] = None, db=Depends(get_db)
):
    """
    시스템 로그 조회 (Ingestion Logs, Admin Only)
    """
    try:
        # Use ingestion_logs as system logs for now
        query = db.table("ingestion_logs").select("*").order("created_at", desc=True)

        if level:
            # Map level to status if needed
            pass

        result = query.limit(limit).execute()

        items = []
        for row in result.data or []:
            entry = {
                "id": row["id"],
                "timestamp": row["created_at"],
                "level": "INFO" if row["status"] == "completed" else "ERROR",
                "service": f"Ingestion({row['source']})",
                "message": row.get("error_message")
                or f"Phase {row['phase']} {row['status']}",
                "meta": row.get("meta") or {},
            }
            # Mask sensitive data
            masked_entry = mask_log_entry(entry)
            items.append(masked_entry)

        return items

    except Exception as e:
        logger.error("get_logs_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
