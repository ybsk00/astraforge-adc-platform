"""
Discovery API Endpoints - Phase 3: 2단 검색 시스템
새로운 Golden Seed 후보 발굴을 위한 API
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db
from app.services.discovery import (
    DiscoveryService,
    DiscoveryRequest,
    DiscoveryResult,
    PlatformAxis,
    SynonymResolver,
    COMMON_NOT_TERMS,
    RECALL_QUERIES,
    PRECISION_KEYWORDS
)

router = APIRouter()
logger = structlog.get_logger()


# === Schemas ===
class SynonymCreate(BaseModel):
    canonical_drug_id: str
    synonym_text: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class SynonymResponse(BaseModel):
    id: str
    canonical_drug_id: str
    synonym_text: str
    synonym_text_normalized: str
    confidence: float
    created_at: str


class QueryPreviewResponse(BaseModel):
    axis: str
    recall_query: str
    precision_keywords: List[str]
    not_terms: List[str]


# === Discovery Endpoints ===

@router.get("/query-preview")
async def get_query_preview(
    axis: PlatformAxis = Query(..., description="Platform axis"),
    additional_query: Optional[str] = Query(None, description="Additional search terms"),
    db=Depends(get_db),
) -> QueryPreviewResponse:
    """
    검색 쿼리 미리보기 (실제 검색 없이 쿼리 확인)
    """
    service = DiscoveryService(db)
    
    recall_query = service.build_recall_query(axis, additional_query)
    precision_keywords = PRECISION_KEYWORDS.get(axis, [])
    
    return QueryPreviewResponse(
        axis=axis.value,
        recall_query=recall_query,
        precision_keywords=precision_keywords,
        not_terms=COMMON_NOT_TERMS
    )


@router.get("/axes")
async def list_axes():
    """
    사용 가능한 검색 축 목록
    """
    return {
        "axes": [
            {
                "value": axis.value,
                "recall_terms": RECALL_QUERIES.get(axis, []),
                "precision_keywords": PRECISION_KEYWORDS.get(axis, [])
            }
            for axis in PlatformAxis
        ],
        "common_not_terms": COMMON_NOT_TERMS
    }


@router.post("/search")
async def search_candidates(
    request: DiscoveryRequest = Body(...),
    db=Depends(get_db),
) -> DiscoveryResult:
    """
    2단 검색 실행
    
    1. Recall 단계: 넓은 범위 기본 검색
    2. Precision 단계: 정밀 키워드 필터링
    3. Synonym Resolution: 기존 데이터 중복 제거
    """
    try:
        service = DiscoveryService(db)
        result = await service.search(request)
        return result
    except Exception as e:
        logger.error("discovery_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-duplicate")
async def check_duplicate(
    drug_name: str = Query(..., description="Drug name to check"),
    db=Depends(get_db),
):
    """
    기존 Golden Seed에 해당 약물이 있는지 확인 (동의어 포함)
    """
    try:
        service = DiscoveryService(db)
        existing_id = await service.check_existing(drug_name)
        
        if existing_id:
            # 기존 데이터 조회
            result = db.table("golden_seed_items").select(
                "id, drug_name_canonical, platform_axis, clinical_stage"
            ).eq("id", existing_id).execute()
            
            return {
                "exists": True,
                "seed_id": existing_id,
                "seed_info": result.data[0] if result.data else None
            }
        
        return {"exists": False, "seed_id": None, "seed_info": None}
    
    except Exception as e:
        logger.error("check_duplicate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Synonym Endpoints ===

@router.get("/synonyms/{drug_id}")
async def get_drug_synonyms(
    drug_id: str,
    db=Depends(get_db),
):
    """
    특정 약물의 모든 동의어 조회
    """
    try:
        resolver = SynonymResolver(db)
        synonyms = await resolver.get_all_synonyms(drug_id)
        
        # 상세 정보도 조회
        result = db.table("synonym_map").select("*").eq(
            "canonical_drug_id", drug_id
        ).execute()
        
        return {
            "canonical_drug_id": drug_id,
            "synonyms": synonyms,
            "details": result.data or []
        }
    except Exception as e:
        logger.error("get_synonyms_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms")
async def add_synonym(
    request: SynonymCreate,
    db=Depends(get_db),
):
    """
    새 동의어 추가
    """
    try:
        resolver = SynonymResolver(db)
        success = await resolver.add_synonym(
            canonical_drug_id=request.canonical_drug_id,
            synonym_text=request.synonym_text,
            source_type=request.source_type,
            source_url=request.source_url,
            confidence=request.confidence
        )
        
        if success:
            return {"status": "created", "synonym": request.synonym_text}
        else:
            raise HTTPException(status_code=500, detail="Failed to add synonym")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_synonym_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/synonyms/resolve")
async def resolve_synonym(
    drug_name: str = Query(..., description="Drug name or synonym to resolve"),
    db=Depends(get_db),
):
    """
    동의어를 canonical drug ID로 해결
    """
    try:
        resolver = SynonymResolver(db)
        canonical_id = await resolver.resolve(drug_name)
        
        if canonical_id:
            # canonical drug 정보도 조회
            result = db.table("golden_seed_items").select(
                "id, drug_name_canonical, platform_axis"
            ).eq("id", canonical_id).execute()
            
            return {
                "resolved": True,
                "canonical_drug_id": canonical_id,
                "drug_info": result.data[0] if result.data else None
            }
        
        return {"resolved": False, "canonical_drug_id": None, "drug_info": None}
    
    except Exception as e:
        logger.error("resolve_synonym_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/synonyms/{synonym_id}")
async def delete_synonym(
    synonym_id: str,
    db=Depends(get_db),
):
    """
    동의어 삭제
    """
    try:
        db.table("synonym_map").delete().eq("id", synonym_id).execute()
        return {"status": "deleted", "id": synonym_id}
    except Exception as e:
        logger.error("delete_synonym_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Batch Operations ===

@router.post("/synonyms/batch")
async def add_synonyms_batch(
    synonyms: List[SynonymCreate] = Body(...),
    db=Depends(get_db),
):
    """
    동의어 일괄 추가
    """
    try:
        resolver = SynonymResolver(db)
        results = []
        
        for syn in synonyms:
            success = await resolver.add_synonym(
                canonical_drug_id=syn.canonical_drug_id,
                synonym_text=syn.synonym_text,
                source_type=syn.source_type,
                source_url=syn.source_url,
                confidence=syn.confidence
            )
            results.append({
                "synonym": syn.synonym_text,
                "success": success
            })
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "total": len(synonyms),
            "success_count": success_count,
            "results": results
        }
    
    except Exception as e:
        logger.error("add_synonyms_batch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
