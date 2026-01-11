"""
Scoring Service
후보 물질의 4축 점수 산출 (Bio, Safety, Engineering, Clinical)

체크리스트 §6.1, §6.2 기반:
- 가중치 기반 점수 합산
- Hard Reject 처리
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class ScoreResult:
    candidate_id: str
    bio_fit: float = 0.0
    safety_fit: float = 0.0
    eng_fit: float = 0.0
    clin_fit: float = 0.0
    total_score: float = 0.0
    is_rejected: bool = False
    reject_reason: Optional[str] = None
    components: Dict[str, Any] = None

class ScoringService:
    """벡터화된 스코어링 서비스"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="scoring")

    async def calculate_scores(self, run_id: str, candidates: List[Dict[str, Any]]) -> List[ScoreResult]:
        """모든 후보에 대해 점수 산출"""
        # 1. 스코어링 파라미터 로드
        params = await self._get_active_params()
        weights = params.get("weights", {"bio": 0.25, "safety": 0.25, "eng": 0.25, "clin": 0.25})
        thresholds = params.get("thresholds", {"hard_reject": 20.0})
        
        results = []
        for cand in candidates:
            res = await self._score_candidate(cand, weights, thresholds)
            results.append(res)
            
        return results

    async def _get_active_params(self) -> Dict[str, Any]:
        """활성화된 스코어링 파라미터 조회"""
        res = await self.db.table("scoring_params").select("*").eq("is_active", True).limit(1).execute()
        if res.data:
            return res.data[0]
        return {}

    async def _score_candidate(self, cand: Dict[str, Any], weights: Dict[str, float], thresholds: Dict[str, float]) -> ScoreResult:
        """단일 후보 점수 산출"""
        # MVP: 단순화된 산식 (추후 복합 산식으로 확장)
        bio = cand.get("bio_score", 50.0)
        safety = cand.get("safety_score", 50.0)
        eng = cand.get("eng_score", 50.0)
        clin = cand.get("clin_score", 50.0)
        
        # Hard Reject 체크
        if bio < thresholds.get("hard_reject", 0):
            return ScoreResult(cand["id"], is_rejected=True, reject_reason="Bio-fit below threshold")
            
        total = (bio * weights["bio"] + 
                 safety * weights["safety"] + 
                 eng * weights["eng"] + 
                 clin * weights["clin"])
                 
        return ScoreResult(
            candidate_id=cand["id"],
            bio_fit=bio,
            safety_fit=safety,
            eng_fit=eng,
            clin_fit=clin,
            total_score=total,
            components={
                "bio": {"score": bio, "weight": weights["bio"]},
                "safety": {"score": safety, "weight": weights["safety"]},
                "eng": {"score": eng, "weight": weights["eng"]},
                "clin": {"score": clin, "weight": weights["clin"]}
            }
        )

def get_scoring_service(db_client) -> ScoringService:
    return ScoringService(db_client)
