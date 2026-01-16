"""
Discovery Service - Phase 3: 2단 검색 시스템
True Golden Set의 새 후보 발굴을 위한 검색 로직

특징:
1. 공통 NOT 조건으로 마켓 리포트 등 제외
2. 축별 2단 쿼리 (Recall → Precision)
3. Synonym Resolution 단계
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum
import structlog
import re

logger = structlog.get_logger()


# === 공통 NOT 조건 ===
COMMON_NOT_TERMS = [
    "global market size",
    "cagr",
    "market forecast",
    "investment analysis",
    "market report",
    "industry report",
    "market share",
    "valuation",
    "pipeline market",
    "market research",
    "market analysis",
    "market overview",
    "market trends",
    "competitive landscape report"
]


# === 축별 검색 쿼리 정의 ===
class PlatformAxis(str, Enum):
    VEDOTIN_MMAE = "VEDOTIN_MMAE"
    DXD = "DXD"
    OPTIDC_KELUN = "OPTIDC_KELUN"
    INDEPENDENT = "INDEPENDENT"


# 1차 Recall 쿼리 (넓은 범위)
RECALL_QUERIES: Dict[PlatformAxis, List[str]] = {
    PlatformAxis.VEDOTIN_MMAE: [
        "vedotin",
        "MMAE",
        "monomethyl auristatin E",
        "auristatin",
        "vcMMAE"
    ],
    PlatformAxis.DXD: [
        "DXd",
        "deruxtecan",
        "Enhertu",
        "DS-8201",
        "T-DXd",
        "DXd-8201"
    ],
    PlatformAxis.OPTIDC_KELUN: [
        "OptiDC",
        "Kelun",
        "Kelun-Biotech",
        "SKB264",
        "site-specific ADC"
    ],
    PlatformAxis.INDEPENDENT: [
        "Trodelvy",
        "SN-38",
        "govitecan",
        "sacituzumab",
        "Padcev",
        "enfortumab",
        "Adcetris",
        "brentuximab"
    ]
}

# 2차 Precision 쿼리 (정밀 필터링)
PRECISION_KEYWORDS: Dict[PlatformAxis, List[str]] = {
    PlatformAxis.VEDOTIN_MMAE: [
        "linker",
        "valine-citrulline",
        "vc-PAB",
        "cathepsin",
        "cleavable linker",
        "DAR"
    ],
    PlatformAxis.DXD: [
        "bystander effect",
        "ILD",
        "interstitial lung disease",
        "topoisomerase",
        "HER2 low",
        "membrane permeable"
    ],
    PlatformAxis.OPTIDC_KELUN: [
        "site-specific",
        "stability",
        "DAR control",
        "homogeneous",
        "conjugation site"
    ],
    PlatformAxis.INDEPENDENT: [
        "payload",
        "hydrolysable",
        "cleavable",
        "internalization",
        "tumor penetration"
    ]
}


# === Schemas ===
class DiscoveryRequest(BaseModel):
    axis: Optional[PlatformAxis] = None  # None이면 모든 축
    query: Optional[str] = None  # 추가 사용자 쿼리
    limit: int = Field(default=50, ge=1, le=200)
    include_precision_filter: bool = True
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DiscoveryCandidate(BaseModel):
    title: str
    source_type: str  # pubmed, clinicaltrials, patent, etc.
    source_id: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    axis: PlatformAxis
    recall_score: float
    precision_score: float
    total_score: float
    matched_recall_terms: List[str] = []
    matched_precision_terms: List[str] = []


class DiscoveryResult(BaseModel):
    axis: Optional[PlatformAxis]
    total_candidates: int
    candidates: List[DiscoveryCandidate]
    query_used: str
    not_terms_applied: List[str]


# === Synonym Resolution ===
class SynonymResolver:
    """동의어 해결 서비스 - synonym_map 테이블 활용"""
    
    def __init__(self, db):
        self.db = db
        self._cache: Dict[str, str] = {}
    
    def normalize_text(self, text: str) -> str:
        """텍스트 정규화: 소문자, 공백/하이픈 통일"""
        if not text:
            return ""
        normalized = text.lower().strip()
        normalized = re.sub(r'[\s\-_]+', '-', normalized)
        return normalized
    
    async def resolve(self, drug_name: str) -> Optional[str]:
        """동의어를 canonical drug_id로 해결"""
        normalized = self.normalize_text(drug_name)
        
        # 캐시 확인
        if normalized in self._cache:
            return self._cache[normalized]
        
        try:
            result = self.db.table("synonym_map").select(
                "canonical_drug_id"
            ).eq("synonym_text_normalized", normalized).execute()
            
            if result.data:
                canonical_id = result.data[0]["canonical_drug_id"]
                self._cache[normalized] = canonical_id
                return canonical_id
        except Exception as e:
            logger.error("synonym_resolve_failed", drug_name=drug_name, error=str(e))
        
        return None
    
    async def get_all_synonyms(self, canonical_drug_id: str) -> List[str]:
        """특정 약물의 모든 동의어 조회"""
        try:
            result = self.db.table("synonym_map").select(
                "synonym_text"
            ).eq("canonical_drug_id", canonical_drug_id).execute()
            
            return [r["synonym_text"] for r in result.data] if result.data else []
        except Exception as e:
            logger.error("get_synonyms_failed", error=str(e))
            return []
    
    async def add_synonym(
        self,
        canonical_drug_id: str,
        synonym_text: str,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        confidence: float = 0.8
    ) -> bool:
        """새 동의어 추가"""
        normalized = self.normalize_text(synonym_text)
        
        try:
            self.db.table("synonym_map").upsert({
                "canonical_drug_id": canonical_drug_id,
                "synonym_text": synonym_text,
                "synonym_text_normalized": normalized,
                "source_type": source_type,
                "source_url": source_url,
                "confidence": confidence
            }, on_conflict="synonym_text_normalized").execute()
            
            # 캐시 업데이트
            self._cache[normalized] = canonical_drug_id
            return True
        except Exception as e:
            logger.error("add_synonym_failed", error=str(e))
            return False


# === Discovery Service ===
class DiscoveryService:
    """2단 검색 서비스"""
    
    def __init__(self, db):
        self.db = db
        self.synonym_resolver = SynonymResolver(db)
    
    def build_not_clause(self) -> str:
        """공통 NOT 조건 생성"""
        not_terms = [f'"{term}"' for term in COMMON_NOT_TERMS]
        return f"NOT ({' OR '.join(not_terms)})"
    
    def build_recall_query(self, axis: PlatformAxis, additional_query: Optional[str] = None) -> str:
        """1차 Recall 쿼리 생성"""
        terms = RECALL_QUERIES.get(axis, [])
        term_clause = " OR ".join([f'"{t}"' for t in terms])
        
        base_query = f"({term_clause}) AND ADC"
        
        if additional_query:
            base_query = f"({base_query}) AND ({additional_query})"
        
        # 공통 NOT 조건 추가
        not_clause = self.build_not_clause()
        
        return f"{base_query} {not_clause}"
    
    def calculate_precision_score(self, text: str, axis: PlatformAxis) -> tuple[float, List[str]]:
        """2차 Precision 점수 계산"""
        precision_keywords = PRECISION_KEYWORDS.get(axis, [])
        matched = []
        
        text_lower = text.lower() if text else ""
        
        for keyword in precision_keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        score = len(matched) / len(precision_keywords) if precision_keywords else 0.0
        return score, matched
    
    def calculate_recall_score(self, text: str, axis: PlatformAxis) -> tuple[float, List[str]]:
        """Recall 매칭 점수 계산"""
        recall_terms = RECALL_QUERIES.get(axis, [])
        matched = []
        
        text_lower = text.lower() if text else ""
        
        for term in recall_terms:
            if term.lower() in text_lower:
                matched.append(term)
        
        score = len(matched) / len(recall_terms) if recall_terms else 0.0
        return score, matched
    
    async def search(self, request: DiscoveryRequest) -> DiscoveryResult:
        """
        2단 검색 실행
        
        1. Recall 단계: 넓은 범위 검색
        2. Precision 단계: 정밀 필터링 (선택적)
        3. Synonym Resolution: 기존 데이터와 매칭
        """
        axes_to_search = [request.axis] if request.axis else list(PlatformAxis)
        all_candidates: List[DiscoveryCandidate] = []
        
        for axis in axes_to_search:
            # 1. Recall 쿼리 생성
            query = self.build_recall_query(axis, request.query)
            
            # TODO: 실제 검색 엔진 호출 (PubMed, ClinicalTrials 등)
            # 여기서는 예시 구조만 제공
            
            logger.info("discovery_search", axis=axis.value, query=query[:100])
        
        return DiscoveryResult(
            axis=request.axis,
            total_candidates=len(all_candidates),
            candidates=all_candidates[:request.limit],
            query_used=self.build_recall_query(request.axis or PlatformAxis.VEDOTIN_MMAE, request.query),
            not_terms_applied=COMMON_NOT_TERMS
        )
    
    async def check_existing(self, drug_name: str) -> Optional[str]:
        """기존 Golden Seed에 있는지 확인 (동의어 포함)"""
        # 1. 직접 매칭
        try:
            result = self.db.table("golden_seed_items").select(
                "id"
            ).ilike("drug_name_canonical", f"%{drug_name}%").execute()
            
            if result.data:
                return result.data[0]["id"]
        except Exception as e:
            logger.error("check_existing_direct_failed", error=str(e))
        
        # 2. 동의어 매칭
        canonical_id = await self.synonym_resolver.resolve(drug_name)
        return canonical_id
    
    async def filter_duplicates(
        self,
        candidates: List[DiscoveryCandidate]
    ) -> List[DiscoveryCandidate]:
        """기존 데이터와 중복 제거"""
        unique = []
        
        for candidate in candidates:
            # 제목에서 약물명 추출 (간단한 휴리스틱)
            existing_id = await self.check_existing(candidate.title)
            if not existing_id:
                unique.append(candidate)
        
        return unique


# === API Endpoint 등록을 위한 함수 ===
def get_discovery_service(db) -> DiscoveryService:
    return DiscoveryService(db)
