"""
Alerts API Endpoints
시스템 알림 및 알람 관리
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from uuid import UUID
import structlog

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


# ============================================================
# Models
# ============================================================

class AlertCreate(BaseModel):
    type: str  # error | warning | info
    source: str  # connector source or system
    message: str
    meta: dict = {}


class AlertResponse(BaseModel):
    id: str
    type: str
    source: str
    message: str
    meta: dict
    is_read: bool
    created_at: str


# ============================================================
# Endpoints
# ============================================================

@router.get("")
async def list_alerts(
    type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """
    알림 목록 조회
    """
    db = get_db()
    
    try:
        query = db.table("system_alerts").select("*")
        
        if type:
            query = query.eq("type", type)
        if source:
            query = query.eq("source", source)
        if is_read is not None:
            query = query.eq("is_read", is_read)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "alerts": result.data,
            "total": len(result.data),
            "unread": sum(1 for a in result.data if not a.get("is_read", False)),
        }
        
    except Exception as e:
        logger.warning("alerts_table_not_found", error=str(e))
        # 테이블이 없으면 빈 목록 반환
        return {"alerts": [], "total": 0, "unread": 0}


@router.post("")
async def create_alert(alert: AlertCreate):
    """
    새 알림 생성
    """
    db = get_db()
    
    try:
        data = {
            "type": alert.type,
            "source": alert.source,
            "message": alert.message,
            "meta": alert.meta,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = db.table("system_alerts").insert(data).execute()
        
        return {"id": result.data[0]["id"], "status": "created"}
        
    except Exception as e:
        logger.error("alert_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """
    알림 읽음 처리
    """
    db = get_db()
    
    try:
        result = db.table("system_alerts").update({
            "is_read": True
        }).eq("id", alert_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "marked_read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("alert_read_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-all")
async def mark_all_read():
    """
    모든 알림 읽음 처리
    """
    db = get_db()
    
    try:
        db.table("system_alerts").update({
            "is_read": True
        }).eq("is_read", False).execute()
        
        return {"status": "all_marked_read"}
        
    except Exception as e:
        logger.error("alert_read_all_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """
    알림 삭제
    """
    db = get_db()
    
    try:
        result = db.table("system_alerts").delete().eq("id", alert_id).execute()
        
        return {"status": "deleted"}
        
    except Exception as e:
        logger.error("alert_delete_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_alert_stats():
    """
    알림 통계
    """
    db = get_db()
    
    try:
        result = db.table("system_alerts").select("type, is_read").execute()
        
        stats = {
            "total": len(result.data),
            "unread": sum(1 for a in result.data if not a.get("is_read", False)),
            "by_type": {},
        }
        
        for alert in result.data:
            t = alert.get("type", "unknown")
            if t not in stats["by_type"]:
                stats["by_type"][t] = 0
            stats["by_type"][t] += 1
        
        return stats
        
    except Exception as e:
        logger.warning("alerts_stats_failed", error=str(e))
        return {"total": 0, "unread": 0, "by_type": {}}
