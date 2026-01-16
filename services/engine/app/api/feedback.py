"""
Feedback API Endpoints
Human-in-the-loop 피드백 시스템

체크리스트 §5.7 기반:
- 후보/근거/프로토콜에 대한 동의/비동의/코멘트
- outlier 제외 플래그
"""

import os
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid
import structlog

router = APIRouter()
logger = structlog.get_logger()


def get_db():
    """Supabase 클라이언트"""
    from supabase import create_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Database not configured")

    return create_client(supabase_url, supabase_key)


# === Schemas ===


class FeedbackCreate(BaseModel):
    """피드백 생성 요청"""

    entity_type: Literal["candidate", "evidence", "protocol", "score"] = Field(
        ..., description="피드백 대상 유형"
    )
    entity_id: str = Field(..., description="피드백 대상 ID")
    feedback_type: Literal["agree", "disagree", "comment", "flag_outlier"] = Field(
        ..., description="피드백 유형"
    )
    comment: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 평점")
    exclude_from_training: bool = Field(False, description="학습 데이터 제외 여부")


class FeedbackResponse(BaseModel):
    """피드백 응답"""

    id: str
    entity_type: str
    entity_id: str
    feedback_type: str
    comment: Optional[str]
    rating: Optional[int]
    user_id: Optional[str]
    created_at: str


class AssayResultCreate(BaseModel):
    """분석 결과 등록"""

    candidate_id: str
    assay_type: str = Field(..., description="분석 유형 (e.g., IC50, binding_affinity)")
    result_value: float
    unit: str
    conditions: Optional[dict] = None
    is_outlier: bool = False
    notes: Optional[str] = None


class AssayResultResponse(BaseModel):
    """분석 결과 응답"""

    id: str
    candidate_id: str
    assay_type: str
    result_value: float
    unit: str
    is_outlier: bool
    created_at: str


# === Endpoints ===


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    workspace_id: str = Query(..., description="워크스페이스 ID"),
    user_id: Optional[str] = None,
    db=Depends(get_db),
):
    """
    피드백 생성

    후보, 근거, 프로토콜, 스코어에 대한 피드백 저장
    """
    feedback_id = str(uuid.uuid4())

    try:
        record = {
            "id": feedback_id,
            "workspace_id": workspace_id,
            "entity_type": feedback.entity_type,
            "entity_id": feedback.entity_id,
            "feedback_type": feedback.feedback_type,
            "comment": feedback.comment,
            "rating": feedback.rating,
            "user_id": user_id,
            "exclude_from_training": feedback.exclude_from_training,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = db.table("human_feedback").insert(record).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create feedback")

        logger.info(
            "feedback_created",
            feedback_id=feedback_id,
            entity_type=feedback.entity_type,
            feedback_type=feedback.feedback_type,
        )

        return FeedbackResponse(
            id=feedback_id,
            entity_type=feedback.entity_type,
            entity_id=feedback.entity_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            rating=feedback.rating,
            user_id=user_id,
            created_at=record["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("feedback_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback")
async def list_feedback(
    workspace_id: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    feedback_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """피드백 목록 조회"""
    try:
        query = (
            db.table("human_feedback")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at", desc=True)
        )

        if entity_type:
            query = query.eq("entity_type", entity_type)
        if entity_id:
            query = query.eq("entity_id", entity_id)
        if feedback_type:
            query = query.eq("feedback_type", feedback_type)

        result = query.range(offset, offset + limit - 1).execute()

        return {"items": result.data or [], "limit": limit, "offset": offset}

    except Exception as e:
        logger.error("feedback_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats/{entity_id}")
async def get_feedback_stats(entity_id: str, db=Depends(get_db)):
    """엔티티별 피드백 통계"""
    try:
        result = (
            db.table("human_feedback")
            .select("feedback_type")
            .eq("entity_id", entity_id)
            .execute()
        )

        stats = {
            "agree": 0,
            "disagree": 0,
            "comment": 0,
            "flag_outlier": 0,
            "total": len(result.data) if result.data else 0,
        }

        for item in result.data or []:
            ft = item.get("feedback_type")
            if ft in stats:
                stats[ft] += 1

        return stats

    except Exception as e:
        logger.error("feedback_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Assay Results ===


@router.post("/assay-results", response_model=AssayResultResponse)
async def create_assay_result(
    assay: AssayResultCreate, workspace_id: str = Query(...), db=Depends(get_db)
):
    """
    분석 결과 등록

    실험 데이터를 후보에 연결
    """
    assay_id = str(uuid.uuid4())

    try:
        record = {
            "id": assay_id,
            "workspace_id": workspace_id,
            "candidate_id": assay.candidate_id,
            "assay_type": assay.assay_type,
            "result_value": assay.result_value,
            "unit": assay.unit,
            "conditions": assay.conditions or {},
            "is_outlier": assay.is_outlier,
            "notes": assay.notes,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = db.table("assay_results").insert(record).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create assay result")

        logger.info(
            "assay_result_created",
            assay_id=assay_id,
            candidate_id=assay.candidate_id,
            assay_type=assay.assay_type,
        )

        return AssayResultResponse(
            id=assay_id,
            candidate_id=assay.candidate_id,
            assay_type=assay.assay_type,
            result_value=assay.result_value,
            unit=assay.unit,
            is_outlier=assay.is_outlier,
            created_at=record["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("assay_result_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assay-results")
async def list_assay_results(
    workspace_id: str,
    candidate_id: Optional[str] = None,
    assay_type: Optional[str] = None,
    exclude_outliers: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """분석 결과 목록 조회"""
    try:
        query = (
            db.table("assay_results")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at", desc=True)
        )

        if candidate_id:
            query = query.eq("candidate_id", candidate_id)
        if assay_type:
            query = query.eq("assay_type", assay_type)
        if exclude_outliers:
            query = query.eq("is_outlier", False)

        result = query.range(offset, offset + limit - 1).execute()

        return {"items": result.data or [], "limit": limit, "offset": offset}

    except Exception as e:
        logger.error("assay_results_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/assay-results/{assay_id}/outlier")
async def mark_as_outlier(assay_id: str, is_outlier: bool, db=Depends(get_db)):
    """분석 결과 outlier 플래그 설정"""
    try:
        result = (
            db.table("assay_results")
            .update({"is_outlier": is_outlier})
            .eq("id", assay_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Assay result not found")

        return {"id": assay_id, "is_outlier": is_outlier}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("mark_outlier_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
