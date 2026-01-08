"""
Catalog API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from uuid import UUID
import structlog

from app.core.database import get_db
from app.core.queue import enqueue_compute_descriptors
from app.schemas.catalog import (
    ComponentCreate,
    ComponentUpdate,
    ComponentResponse,
    ComponentListResponse,
    ComponentType,
    ComponentStatus,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/components", response_model=ComponentResponse, status_code=201)
async def create_component(data: ComponentCreate):
    """
    새 카탈로그 컴포넌트 등록
    
    - 등록 시 status='pending_compute'로 시작
    - RDKit 워커가 디스크립터 계산 후 'active'로 전환
    """
    db = get_db()
    
    try:
        result = db.table("component_catalog").insert({
            "type": data.type,
            "name": data.name,
            "properties": data.properties,
            "quality_grade": data.quality_grade,
            "status": "pending_compute"
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create component")
        
        component = result.data[0]
        logger.info("component_created", 
                   component_id=component["id"], 
                   type=data.type, 
                   name=data.name)
        
        # SMILES가 있으면 RDKit 워커 Job enqueue
        if data.properties.get("smiles"):
            try:
                await enqueue_compute_descriptors(component["id"])
            except Exception as e:
                logger.warning("enqueue_failed", component_id=component["id"], error=str(e))
        
        return ComponentResponse(**component)
        
    except Exception as e:
        logger.error("component_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components", response_model=ComponentListResponse)
async def list_components(
    type: Optional[ComponentType] = Query(None, description="컴포넌트 타입 필터"),
    status: Optional[ComponentStatus] = Query(None, description="상태 필터"),
    quality_grade: Optional[str] = Query(None, description="품질 등급 필터"),
    search: Optional[str] = Query(None, description="이름 검색"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    카탈로그 컴포넌트 목록 조회
    
    - 타입, 상태, 품질 등급으로 필터링 가능
    - 이름 검색 지원
    - 페이지네이션 지원
    """
    db = get_db()
    
    try:
        # 기본 쿼리
        query = db.table("component_catalog").select("*", count="exact")
        
        # 필터 적용
        if type:
            query = query.eq("type", type)
        if status:
            query = query.eq("status", status)
        if quality_grade:
            query = query.eq("quality_grade", quality_grade)
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # 정렬 및 페이지네이션
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return ComponentListResponse(
            items=[ComponentResponse(**item) for item in result.data],
            total=result.count or 0,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error("component_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{component_id}", response_model=ComponentResponse)
async def get_component(component_id: UUID):
    """컴포넌트 상세 조회"""
    db = get_db()
    
    try:
        result = db.table("component_catalog").select("*").eq("id", str(component_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Component not found")
        
        return ComponentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("component_get_failed", component_id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/components/{component_id}", response_model=ComponentResponse)
async def update_component(component_id: UUID, data: ComponentUpdate):
    """
    컴포넌트 수정
    
    - properties 수정 시 status가 'pending_compute'로 변경될 수 있음
    """
    db = get_db()
    
    try:
        # 기존 컴포넌트 확인
        existing = db.table("component_catalog").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Component not found")
        
        # 업데이트 데이터 구성
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # properties 변경 시 재계산 필요
        if "properties" in update_data and "smiles" in update_data.get("properties", {}):
            update_data["status"] = "pending_compute"
            update_data["computed_at"] = None
        
        result = db.table("component_catalog").update(update_data).eq("id", str(component_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update component")
        
        logger.info("component_updated", component_id=str(component_id))
        return ComponentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("component_update_failed", component_id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/components/{component_id}")
async def delete_component(component_id: UUID):
    """
    컴포넌트 삭제 (deprecated 처리)
    
    - 실제 삭제 대신 status='deprecated'로 변경
    """
    db = get_db()
    
    try:
        # 기존 컴포넌트 확인
        existing = db.table("component_catalog").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Component not found")
        
        # deprecated로 변경
        result = db.table("component_catalog").update({
            "status": "deprecated"
        }).eq("id", str(component_id)).execute()
        
        logger.info("component_deprecated", component_id=str(component_id))
        return {"status": "deprecated", "component_id": str(component_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("component_delete_failed", component_id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components/{component_id}/retry")
async def retry_compute(component_id: UUID):
    """
    실패한 컴포넌트 재계산 요청
    
    - status='failed'인 컴포넌트에 대해 RDKit 재계산 트리거
    """
    db = get_db()
    
    try:
        # 컴포넌트 확인
        existing = db.table("component_catalog").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Component not found")
        
        component = existing.data[0]
        if component["status"] != "failed":
            raise HTTPException(status_code=400, detail="Only failed components can be retried")
        
        # status를 pending_compute로 변경
        result = db.table("component_catalog").update({
            "status": "pending_compute",
            "compute_error": None
        }).eq("id", str(component_id)).execute()
        
        # RDKit 워커 Job enqueue
        try:
            await enqueue_compute_descriptors(str(component_id))
        except Exception as e:
            logger.warning("enqueue_failed", component_id=str(component_id), error=str(e))
        
        logger.info("component_retry_queued", component_id=str(component_id))
        return {"status": "pending_compute", "component_id": str(component_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("component_retry_failed", component_id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === 통계 엔드포인트 ===

@router.get("/components/stats/summary")
async def get_catalog_stats():
    """카탈로그 통계 요약"""
    db = get_db()
    
    try:
        # 타입별 카운트
        result = db.table("component_catalog").select("type, status", count="exact").execute()
        
        stats = {
            "total": len(result.data),
            "by_type": {},
            "by_status": {}
        }
        
        for item in result.data:
            # 타입별
            t = item["type"]
            stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
            
            # 상태별
            s = item["status"]
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error("stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
