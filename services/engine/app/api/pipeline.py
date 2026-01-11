"""
Pipeline API Endpoints
Seed Set 기반 데이터 수집 파이프라인 실행
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import structlog
from app.core.database import get_db
from app.services.pipeline import PipelineService

router = APIRouter()
logger = structlog.get_logger()

class PipelineRunRequest(BaseModel):
    seed_set_id: str
    connector_names: Optional[List[str]] = None
    max_pages: int = 10

@router.post("/run-seed-set")
async def run_seed_set_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Seed Set 기반 수집 파이프라인 실행 (백그라운드)
    """
    try:
        service = PipelineService(db)
        # 백그라운드에서 실행하여 즉시 응답 반환
        background_tasks.add_task(
            service.run_seed_set,
            seed_set_id=request.seed_set_id,
            connector_names=request.connector_names,
            max_pages=request.max_pages
        )
        
        return {
            "status": "accepted",
            "message": "Pipeline execution started in background",
            "seed_set_id": request.seed_set_id
        }
    except Exception as e:
        logger.error("pipeline_trigger_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
