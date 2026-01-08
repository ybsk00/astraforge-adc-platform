"""
Fingerprint API Endpoints
구조 유사도 검색 및 분자 descriptor API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.services.fingerprint import FingerprintService, SimilarityResult
from app.core.database import get_db

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class FingerprintRequest(BaseModel):
    """Fingerprint 계산 요청"""
    smiles: str
    fp_type: str = "morgan"  # morgan, maccs, topological


class FingerprintResponse(BaseModel):
    """Fingerprint 응답"""
    smiles: str
    fingerprint_type: str
    on_bit_count: int
    total_bits: int


class SimilarityRequest(BaseModel):
    """유사도 계산 요청"""
    smiles1: str
    smiles2: str
    fp_type: str = "morgan"
    metric: str = "tanimoto"  # tanimoto, dice, cosine


class SimilaritySearchRequest(BaseModel):
    """유사 화합물 검색 요청"""
    smiles: str
    top_k: int = 10
    threshold: float = 0.5
    fp_type: str = "morgan"
    component_type: Optional[str] = None  # payload, linker


class SimilarCompound(BaseModel):
    """유사 화합물 결과"""
    compound_id: str
    name: str
    smiles: str
    similarity: float


class DescriptorRequest(BaseModel):
    """Descriptor 계산 요청"""
    smiles: str


class DescriptorResponse(BaseModel):
    """Descriptor 응답"""
    smiles: str
    molecular_weight: float
    exact_mass: float
    logp: float
    tpsa: float
    hbd: int
    hba: int
    rotatable_bonds: int
    rings: int
    aromatic_rings: int
    heavy_atoms: int
    fraction_csp3: float


# ============================================================
# Endpoints
# ============================================================

@router.post("/fingerprint", response_model=FingerprintResponse)
async def compute_fingerprint(request: FingerprintRequest):
    """
    SMILES에서 fingerprint 계산
    
    지원 타입:
    - morgan: Morgan/ECFP fingerprints
    - maccs: MACCS keys (166 bits)
    - topological: Daylight-type fingerprints
    """
    service = FingerprintService()
    
    result = service.compute_fingerprint(
        smiles=request.smiles,
        fp_type=request.fp_type
    )
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to compute fingerprint. Check SMILES validity."
        )
    
    return FingerprintResponse(
        smiles=request.smiles,
        fingerprint_type=result["type"],
        on_bit_count=result["on_bit_count"],
        total_bits=result["total_bits"]
    )


@router.post("/similarity")
async def calculate_similarity(request: SimilarityRequest):
    """
    두 화합물 간 구조 유사도 계산
    
    메트릭:
    - tanimoto: Tanimoto coefficient (기본)
    - dice: Dice similarity
    - cosine: Cosine similarity
    """
    service = FingerprintService()
    
    similarity = service.calculate_similarity(
        smiles1=request.smiles1,
        smiles2=request.smiles2,
        fp_type=request.fp_type,
        metric=request.metric
    )
    
    if similarity is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to calculate similarity. Check SMILES validity."
        )
    
    return {
        "smiles1": request.smiles1,
        "smiles2": request.smiles2,
        "similarity": similarity,
        "metric": request.metric,
        "fingerprint_type": request.fp_type
    }


@router.post("/search", response_model=List[SimilarCompound])
async def search_similar_compounds(request: SimilaritySearchRequest):
    """
    카탈로그에서 유사 화합물 검색
    
    Parameters:
    - smiles: 검색할 화합물 SMILES
    - top_k: 반환할 최대 개수 (기본 10)
    - threshold: 최소 유사도 (기본 0.5)
    - component_type: 컴포넌트 타입 필터 (payload, linker 등)
    """
    db = get_db()
    service = FingerprintService(db)
    
    results = await service.search_similar(
        query_smiles=request.smiles,
        top_k=request.top_k,
        threshold=request.threshold,
        fp_type=request.fp_type,
        component_type=request.component_type
    )
    
    return [
        SimilarCompound(
            compound_id=r.compound_id,
            name=r.name,
            smiles=r.smiles,
            similarity=r.similarity
        )
        for r in results
    ]


@router.post("/descriptors", response_model=DescriptorResponse)
async def compute_descriptors(request: DescriptorRequest):
    """
    SMILES에서 분자 descriptor 계산
    
    반환 값:
    - molecular_weight: 분자량
    - logp: LogP (지용성)
    - tpsa: Topological Polar Surface Area
    - hbd/hba: 수소결합 주개/받개 수
    - rotatable_bonds: 회전가능 결합 수
    - rings: 총 고리 수
    - aromatic_rings: 방향족 고리 수
    """
    service = FingerprintService()
    
    result = service.compute_descriptors(request.smiles)
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to compute descriptors. Check SMILES validity."
        )
    
    return DescriptorResponse(
        smiles=request.smiles,
        **result
    )


@router.get("/validate")
async def validate_smiles(smiles: str = Query(..., description="SMILES 문자열")):
    """
    SMILES 유효성 검증
    """
    service = FingerprintService()
    
    # Fingerprint 계산 시도로 유효성 확인
    result = service.compute_fingerprint(smiles, "morgan")
    
    if result:
        descriptors = service.compute_descriptors(smiles)
        return {
            "valid": True,
            "smiles": smiles,
            "molecular_weight": descriptors.get("molecular_weight") if descriptors else None
        }
    else:
        return {
            "valid": False,
            "smiles": smiles,
            "error": "Invalid SMILES string"
        }
