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
        "service": "adc-engine",
    }


@router.get("/status")
async def system_status():
    """시스템 상태 확인"""
    return {
        "status": "operational",
        "version": "0.1.0",
        "components": {
            "database": "connected",  # TODO: 실제 연결 확인
            "redis": "connected",  # TODO: 실제 연결 확인
            "worker": "available",  # TODO: 실제 상태 확인
        },
    }


@router.get("/health/worker")
async def worker_health():
    """워커 상태 확인 (Redis Connection)"""
    from app.core.queue import get_redis_pool

    try:
        pool = await get_redis_pool()
        # Check Redis connection
        await pool.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "adc-worker",
            "backend": "redis",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "adc-worker",
            "error": str(e),
        }
