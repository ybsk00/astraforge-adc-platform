"""
Staging API Endpoints
스테이징 컴포넌트 승인 워크플로우
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


# ============================================================
# Schemas
# ============================================================

class StagingComponentCreate(BaseModel):
    """스테이징 컴포넌트 생성"""
    type: str = Field(..., description="컴포넌트 타입 (target/antibody/linker/payload/conjugation)")
    name: str = Field(..., description="컴포넌트 이름")
    properties: dict = Field(default_factory=dict)
    quality_grade: str = Field(default="silver")
    source: dict = Field(default_factory=dict, description="출처 정보")


class StagingComponentUpdate(BaseModel):
    """스테이징 컴포넌트 수정"""
    name: Optional[str] = None
    properties: Optional[dict] = None
    quality_grade: Optional[str] = None
    review_note: Optional[str] = None


class StagingApproval(BaseModel):
    """승인/거절 요청"""
    review_note: Optional[str] = None


class BulkApproval(BaseModel):
    """일괄 승인"""
    ids: List[str] = Field(..., description="승인할 컴포넌트 ID 목록")
    review_note: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

@router.post("/components", status_code=201)
async def create_staging_component(data: StagingComponentCreate):
    """
    스테이징 컴포넌트 등록
    
    자동 수집된 데이터나 수동 등록 데이터를 검수 대기 상태로 등록합니다.
    """
    db = get_db()
    
    try:
        result = db.table("staging_components").insert({
            "type": data.type,
            "name": data.name,
            "properties": data.properties,
            "quality_grade": data.quality_grade,
            "source": data.source,
            "status": "pending"
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create staging component")
        
        component = result.data[0]
        logger.info("staging_component_created", 
                   id=component["id"], 
                   type=data.type, 
                   name=data.name)
        
        return component
        
    except Exception as e:
        logger.error("staging_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def list_staging_components(
    type: Optional[str] = Query(None, description="컴포넌트 타입 필터"),
    status: Optional[str] = Query(None, description="상태 필터 (pending/approved/rejected)"),
    source: Optional[str] = Query(None, description="출처 필터"),
    search: Optional[str] = Query(None, description="이름 검색"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    스테이징 컴포넌트 목록 조회
    """
    db = get_db()
    
    try:
        query = db.table("staging_components").select("*", count="exact")
        
        if type:
            query = query.eq("type", type)
        if status:
            query = query.eq("status", status)
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Source 필터 (JSONB)
        if source:
            query = query.eq("source->>source", source)
        
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return {
            "items": result.data,
            "total": result.count or 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("staging_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{component_id}")
async def get_staging_component(component_id: UUID):
    """스테이징 컴포넌트 상세 조회"""
    db = get_db()
    
    try:
        result = db.table("staging_components").select("*").eq("id", str(component_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Staging component not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("staging_get_failed", id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/components/{component_id}")
async def update_staging_component(component_id: UUID, data: StagingComponentUpdate):
    """스테이징 컴포넌트 수정"""
    db = get_db()
    
    try:
        # 기존 확인
        existing = db.table("staging_components").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Staging component not found")
        
        if existing.data[0]["status"] != "pending":
            raise HTTPException(status_code=400, detail="Cannot modify non-pending component")
        
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = db.table("staging_components").update(update_data).eq("id", str(component_id)).execute()
        
        logger.info("staging_component_updated", id=str(component_id))
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("staging_update_failed", id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components/{component_id}/approve")
async def approve_staging_component(component_id: UUID, data: StagingApproval = None):
    """
    스테이징 컴포넌트 승인
    
    승인된 컴포넌트는 component_catalog로 복사됩니다.
    """
    db = get_db()
    
    try:
        # 기존 확인
        existing = db.table("staging_components").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Staging component not found")
        
        staging = existing.data[0]
        if staging["status"] != "pending":
            raise HTTPException(status_code=400, detail="Component is not pending")
        
        # component_catalog에 복사
        catalog_data = {
            "type": staging["type"],
            "name": staging["name"],
            "properties": staging.get("properties", {}),
            "quality_grade": staging.get("quality_grade", "silver"),
            "status": "pending_compute"  # RDKit 계산 필요
        }
        
        # Source 정보 추가
        catalog_data["properties"]["source"] = staging.get("source", {})
        
        catalog_result = db.table("component_catalog").insert(catalog_data).execute()
        
        if not catalog_result.data:
            raise HTTPException(status_code=500, detail="Failed to create catalog component")
        
        # 스테이징 상태 업데이트
        db.table("staging_components").update({
            "status": "approved",
            "review_note": data.review_note if data else None,
            "approved_at": datetime.utcnow().isoformat()
        }).eq("id", str(component_id)).execute()
        
        logger.info("staging_component_approved", 
                   staging_id=str(component_id), 
                   catalog_id=catalog_result.data[0]["id"])
        
        return {
            "status": "approved",
            "staging_id": str(component_id),
            "catalog_id": catalog_result.data[0]["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("staging_approve_failed", id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components/{component_id}/reject")
async def reject_staging_component(component_id: UUID, data: StagingApproval = None):
    """스테이징 컴포넌트 거절"""
    db = get_db()
    
    try:
        existing = db.table("staging_components").select("*").eq("id", str(component_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Staging component not found")
        
        if existing.data[0]["status"] != "pending":
            raise HTTPException(status_code=400, detail="Component is not pending")
        
        db.table("staging_components").update({
            "status": "rejected",
            "review_note": data.review_note if data else None,
        }).eq("id", str(component_id)).execute()
        
        logger.info("staging_component_rejected", id=str(component_id))
        
        return {"status": "rejected", "staging_id": str(component_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("staging_reject_failed", id=str(component_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components/bulk/approve")
async def bulk_approve_staging_components(data: BulkApproval):
    """
    스테이징 컴포넌트 일괄 승인
    """
    db = get_db()
    results = {"approved": 0, "failed": 0, "errors": []}
    
    for component_id in data.ids:
        try:
            await approve_staging_component(
                UUID(component_id), 
                StagingApproval(review_note=data.review_note)
            )
            results["approved"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"id": component_id, "error": str(e)})
    
    logger.info("bulk_approve_completed", 
               approved=results["approved"], 
               failed=results["failed"])
    
    return results


@router.get("/duplicates")
async def get_duplicate_groups(
    field: str = Query("smiles", description="중복 체크 필드 (smiles/inchi_key/name)"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    중복 후보 그룹 조회
    
    동일한 SMILES 또는 InChIKey를 가진 스테이징 컴포넌트를 그룹화합니다.
    """
    db = get_db()
    
    try:
        # pending 상태만 조회
        result = db.table("staging_components").select("*").eq("status", "pending").execute()
        
        groups = {}
        
        for item in result.data:
            props = item.get("properties", {})
            
            if field == "smiles":
                key = props.get("smiles") or props.get("canonical_smiles")
            elif field == "inchi_key":
                key = props.get("inchi_key")
            else:
                key = item.get("name")
            
            if key:
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)
        
        # 2개 이상인 그룹만 반환
        duplicate_groups = [
            {"key": k, "count": len(v), "items": v}
            for k, v in groups.items()
            if len(v) > 1
        ]
        
        # 정렬 (많은 순)
        duplicate_groups.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "groups": duplicate_groups[:limit],
            "total_groups": len(duplicate_groups)
        }
        
    except Exception as e:
        logger.error("duplicate_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_staging_stats():
    """스테이징 통계"""
    db = get_db()
    
    try:
        result = db.table("staging_components").select("type, status").execute()
        
        stats = {
            "total": len(result.data),
            "by_status": {},
            "by_type": {}
        }
        
        for item in result.data:
            status = item["status"]
            comp_type = item["type"]
            
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_type"][comp_type] = stats["by_type"].get(comp_type, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error("staging_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
