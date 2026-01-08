"""
Scoring Engine v0.2
Eng-Fit / Bio-Fit / Safety-Fit 벡터화 산식 구현

체크리스트 §0.3 확정 산식 기반
"""
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class ScoreComponents:
    """개별 스코어 컴포넌트 (설명 가능성 용)"""
    terms: Dict[str, float] = field(default_factory=dict)
    risk: float = 0.0
    fit: float = 100.0
    missing_features: List[str] = field(default_factory=list)


@dataclass
class CandidateScores:
    """후보 전체 스코어"""
    eng_fit: float = 0.0
    bio_fit: float = 0.0
    safety_fit: float = 0.0
    evidence_fit: float = 0.0  # RAG 후 산출
    
    eng_components: ScoreComponents = field(default_factory=ScoreComponents)
    bio_components: ScoreComponents = field(default_factory=ScoreComponents)
    safety_components: ScoreComponents = field(default_factory=ScoreComponents)
    
    def total_fit(self, weights: Dict[str, float] = None) -> float:
        """가중 합계 스코어"""
        weights = weights or {"eng": 0.25, "bio": 0.35, "safety": 0.30, "evidence": 0.10}
        return (
            self.eng_fit * weights.get("eng", 0.25) +
            self.bio_fit * weights.get("bio", 0.35) +
            self.safety_fit * weights.get("safety", 0.30) +
            self.evidence_fit * weights.get("evidence", 0.10)
        )


class ScoringEngine:
    """
    ADC 후보 스코어링 엔진 v0.2
    
    모든 산식은 100 - Risk 구조:
    - EngFit = 100 - CMC_Risk
    - BioFit = 100 - BioRisk
    - SafetyFit = 100 - SafetyRisk
    """
    
    # 기본 가중치 (scoring_params에서 오버라이드 가능)
    DEFAULT_WEIGHTS = {
        # Eng-Fit weights
        "w_agg": 0.35,
        "w_proc": 0.25,
        "w_anal": 0.20,
        "w_unc": 0.20,
        # Bio-Fit weights
        "w_dea": 0.25,
        "w_int": 0.25,
        "w_het": 0.15,
        "w_acc": 0.15,
        "w_bs": 0.20,
        # Safety-Fit weights
        "w_oot": 0.30,
        "w_haz": 0.25,
        "w_clv": 0.15,
        "w_sar": 0.15,
        "w_neg": 0.15,
    }
    
    # 기본 계수
    DEFAULT_COEFFICIENTS = {
        "omega_logP": 10.0,
        "omega_DAR": 15.0,
        "omega_patch": 5.0,
        "k_dea": 10.0,
        "k_oot": 8.0,
        "k_crit": 20.0,
    }
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Args:
            params: scoring_params 테이블에서 로드된 파라미터
        """
        self.params = params or {}
        self.weights = {**self.DEFAULT_WEIGHTS, **self.params.get("weights", {})}
        self.coefficients = {**self.DEFAULT_COEFFICIENTS, **self.params.get("coefficients", {})}
        self.logger = logger.bind(service="scoring_engine")
    
    def score_candidate(
        self,
        target: Dict[str, Any],
        antibody: Dict[str, Any],
        linker: Dict[str, Any],
        payload: Dict[str, Any],
        conjugation: Dict[str, Any] = None
    ) -> CandidateScores:
        """
        단일 후보 스코어 계산
        
        Args:
            target: Target 컴포넌트 properties
            antibody: Antibody 컴포넌트 properties
            linker: Linker 컴포넌트 properties
            payload: Payload 컴포넌트 properties
            conjugation: Conjugation 컴포넌트 properties (optional)
        
        Returns:
            CandidateScores with all fits and components
        """
        # Merge properties for easier access
        props = {
            "target": target,
            "antibody": antibody,
            "linker": linker,
            "payload": payload,
            "conjugation": conjugation or {}
        }
        
        # Calculate each fit
        eng = self._calculate_eng_fit(props)
        bio = self._calculate_bio_fit(props)
        safety = self._calculate_safety_fit(props)
        
        return CandidateScores(
            eng_fit=eng.fit,
            bio_fit=bio.fit,
            safety_fit=safety.fit,
            evidence_fit=0.0,  # RAG 단계에서 계산
            eng_components=eng,
            bio_components=bio,
            safety_components=safety
        )
    
    def _calculate_eng_fit(self, props: Dict[str, Any]) -> ScoreComponents:
        """
        Eng-Fit (CMC Risk) 계산
        
        EngFit = 100 - CMC_Risk
        CMC_Risk = clip(w_agg * AggRisk + w_proc * ProcRisk + w_anal * AnalRisk + w_unc * UncPenalty, 0, 100)
        """
        components = ScoreComponents()
        payload = props.get("payload", {})
        linker = props.get("linker", {})
        conjugation = props.get("conjugation", {})
        
        # 1. AggRisk (응집 위험)
        logP = payload.get("logP", payload.get("molecular_weight", 0) / 100)  # 대체값
        DAR = conjugation.get("DAR", 4.0)
        H_patch = payload.get("hydrophobic_patch", 0)
        
        agg_risk = self._clip(
            self.coefficients["omega_logP"] * max(0, logP - 2.0) +
            self.coefficients["omega_DAR"] * max(0, DAR - 4.0) +
            self.coefficients["omega_patch"] * H_patch,
            0, 100
        )
        components.terms["AggRisk"] = agg_risk
        
        # 2. ProcRisk (공정 복잡도)
        proc_risk = 0.0
        if conjugation.get("site_specific"):
            proc_risk += 30.0
        if linker.get("purification_difficulty", "normal") == "high":
            proc_risk += 25.0
        proc_risk = self._clip(proc_risk, 0, 100)
        components.terms["ProcRisk"] = proc_risk
        
        # 3. AnalRisk (분석 난이도)
        anal_risk = 0.0
        if DAR > 4:
            anal_risk += 20.0
        if payload.get("aggregation_prone"):
            anal_risk += 30.0
        anal_risk = self._clip(anal_risk, 0, 100)
        components.terms["AnalRisk"] = anal_risk
        
        # 4. UncPenalty (불확실성 페널티)
        unc_penalty = 0.0
        required_features = ["logP", "solubility", "stability"]
        for f in required_features:
            if f not in payload:
                unc_penalty += 10.0
                components.missing_features.append(f"payload.{f}")
        unc_penalty = self._clip(unc_penalty, 0, 100)
        components.terms["UncPenalty"] = unc_penalty
        
        # CMC_Risk 합산
        cmc_risk = self._clip(
            self.weights["w_agg"] * agg_risk +
            self.weights["w_proc"] * proc_risk +
            self.weights["w_anal"] * anal_risk +
            self.weights["w_unc"] * unc_penalty,
            0, 100
        )
        components.risk = cmc_risk
        components.fit = 100 - cmc_risk
        
        return components
    
    def _calculate_bio_fit(self, props: Dict[str, Any]) -> ScoreComponents:
        """
        Bio-Fit (생물학적 적합성) 계산
        
        BioFit = 100 - BioRisk
        """
        components = ScoreComponents()
        target = props.get("target", {})
        payload = props.get("payload", {})
        
        # 1. DEA (Differential Expression Advantage)
        # DEA = clip(50 + k_dea * (log2(T_expr_tumor+1) - log2(N_expr_max+1)), 0, 100)
        tumor_expr = target.get("expression", {}).get("tumor", 10.0)
        normal_expr = target.get("expression", {}).get("normal_max", 1.0)
        
        dea = self._clip(
            50 + self.coefficients["k_dea"] * (
                math.log2(tumor_expr + 1) - math.log2(normal_expr + 1)
            ),
            0, 100
        )
        components.terms["DEA"] = dea
        
        # 2. INT (Internalization)
        int_score = target.get("internalization", 0.7) * 100
        components.terms["INT"] = int_score
        
        # 3. HET (Heterogeneity penalty)
        het_pen = target.get("heterogeneity", 0.3) * 100
        components.terms["HET_pen"] = het_pen
        
        # 4. ACC (Accessibility penalty)
        acc_pen = (1 - target.get("accessibility", 0.8)) * 100
        components.terms["ACC_pen"] = acc_pen
        
        # 5. BS (Bystander match)
        bystander_need = target.get("bystander_need", 0.5)
        bystander_cap = payload.get("bystander_capability", 0.5)
        bs_match = (1 - abs(bystander_need - bystander_cap)) * 100
        components.terms["BS_match"] = bs_match
        
        # BioRisk 합산
        bio_risk = self._clip(
            self.weights["w_dea"] * (100 - dea) +
            self.weights["w_int"] * max(0, 70 - int_score) +  # threshold 70
            self.weights["w_het"] * het_pen +
            self.weights["w_acc"] * acc_pen +
            self.weights["w_bs"] * (100 - bs_match),
            0, 100
        )
        components.risk = bio_risk
        components.fit = 100 - bio_risk
        
        return components
    
    def _calculate_safety_fit(self, props: Dict[str, Any]) -> ScoreComponents:
        """
        Safety-Fit (안전성) 계산
        
        SafetyFit = 100 - SafetyRisk
        """
        components = ScoreComponents()
        target = props.get("target", {})
        payload = props.get("payload", {})
        linker = props.get("linker", {})
        
        # 1. OOT (Off-target toxicity)
        normal_expr = target.get("expression", {}).get("normal_max", 1.0)
        critical_tissue = 1 if target.get("critical_tissue_expression") else 0
        
        oot = self._clip(
            self.coefficients["k_oot"] * math.log2(normal_expr + 1) +
            self.coefficients["k_crit"] * critical_tissue,
            0, 100
        )
        components.terms["OOT"] = oot
        
        # 2. PH (Payload hazard)
        ph = payload.get("hazard_score", 0.5) * 100
        components.terms["PH"] = ph
        
        # 3. CLV (Cleavage risk)
        clv = linker.get("cleavage_risk", 0.3) * 100
        components.terms["CLV"] = clv
        
        # 4. SAR (Systemic exposure)
        sar = payload.get("systemic_exposure_proxy", 30)
        components.terms["SAR"] = sar
        
        # 5. NEG (Negative signals from literature)
        neg = target.get("negative_signal_score", 0) * 100
        components.terms["NEG"] = neg
        
        # SafetyRisk 합산
        safety_risk = self._clip(
            self.weights["w_oot"] * oot +
            self.weights["w_haz"] * ph +
            self.weights["w_clv"] * clv +
            self.weights["w_sar"] * sar +
            self.weights["w_neg"] * neg,
            0, 100
        )
        components.risk = safety_risk
        components.fit = 100 - safety_risk
        
        return components
    
    @staticmethod
    def _clip(value: float, min_val: float, max_val: float) -> float:
        """값을 범위 내로 제한"""
        return max(min_val, min(max_val, value))
    
    def score_to_dict(self, scores: CandidateScores) -> Dict[str, Any]:
        """CandidateScores를 저장용 딕셔너리로 변환"""
        return {
            "eng_fit": round(scores.eng_fit, 2),
            "bio_fit": round(scores.bio_fit, 2),
            "safety_fit": round(scores.safety_fit, 2),
            "evidence_fit": round(scores.evidence_fit, 2),
            "score_components": {
                "eng_fit": {
                    "terms": {k: round(v, 2) for k, v in scores.eng_components.terms.items()},
                    "risk": round(scores.eng_components.risk, 2),
                    "missing_features": scores.eng_components.missing_features
                },
                "bio_fit": {
                    "terms": {k: round(v, 2) for k, v in scores.bio_components.terms.items()},
                    "risk": round(scores.bio_components.risk, 2),
                    "missing_features": scores.bio_components.missing_features
                },
                "safety_fit": {
                    "terms": {k: round(v, 2) for k, v in scores.safety_components.terms.items()},
                    "risk": round(scores.safety_components.risk, 2),
                    "missing_features": scores.safety_components.missing_features
                }
            }
        }


class BatchScoringEngine(ScoringEngine):
    """
    배치 스코어링 (벡터화)
    
    여러 후보를 한 번에 처리하여 성능 최적화
    """
    
    def score_batch(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[CandidateScores]:
        """
        배치 스코어링
        
        Args:
            candidates: [{"target": {...}, "antibody": {...}, ...}, ...]
        
        Returns:
            List of CandidateScores
        """
        results = []
        
        for candidate in candidates:
            try:
                score = self.score_candidate(
                    target=candidate.get("target", {}),
                    antibody=candidate.get("antibody", {}),
                    linker=candidate.get("linker", {}),
                    payload=candidate.get("payload", {}),
                    conjugation=candidate.get("conjugation", {})
                )
                results.append(score)
            except Exception as e:
                self.logger.warning("score_failed", error=str(e))
                # 오류 시 기본 점수
                results.append(CandidateScores())
        
        return results


# 편의 함수
def get_scoring_engine(params: Dict[str, Any] = None) -> ScoringEngine:
    """스코어링 엔진 인스턴스 반환"""
    return ScoringEngine(params)


def get_batch_scoring_engine(params: Dict[str, Any] = None) -> BatchScoringEngine:
    """배치 스코어링 엔진 인스턴스 반환"""
    return BatchScoringEngine(params)
