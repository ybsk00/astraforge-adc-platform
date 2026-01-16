"""
Automation API
자동 검증 트리거 및 데이터셋 동기화 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.core.supabase import get_supabase_client
from app.services.automation_service import get_automation_service
from app.services.dataset_sync_service import get_dataset_sync_service

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/trigger-validation")
async def trigger_validation(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db=Depends(get_supabase_client),
):
    """산식 변경에 따른 자동 검증 트리거 (Webhook용)"""
    service = get_automation_service(db)
    # 백그라운드에서 검증 실행 (응답 지연 방지)
    background_tasks.add_task(service.handle_scoring_param_change, payload)
    return {"status": "accepted", "message": "Validation triggered in background"}


@router.post("/sync-clinical-trials")
async def sync_clinical_trials(db=Depends(get_supabase_client)):
    """ClinicalTrials.gov 데이터 동기화 실행"""
    service = get_dataset_sync_service(db)
    try:
        updated_count = await service.sync_clinical_statuses()
        return {
            "status": "success",
            "updated_count": updated_count,
            "message": f"Successfully synced {updated_count} candidates",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
