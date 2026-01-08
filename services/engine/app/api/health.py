"""
Health Check Endpoints
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "adc-engine"
    }


@router.get("/api/v1/status")
async def system_status():
    """시스템 상태 확인"""
    return {
        "status": "operational",
        "version": "0.1.0",
        "components": {
            "database": "connected",  # TODO: 실제 연결 확인
            "redis": "connected",     # TODO: 실제 연결 확인
            "worker": "available"     # TODO: 실제 상태 확인
        }
    }
