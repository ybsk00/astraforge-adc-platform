"""
Calc Engine Service
RDKit 기반 물성 계산 및 적절성 평가 (응집성, 독성, 바이스텐딩, bsAb)

체크리스트 §5.1, §5.2, §5.3, §6.3 기반:
- Aggregation Risk Score
- Toxicity Alerts (SMARTS)
- Bystander Proxy Score
- bsAb Applicability Score
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import structlog
from rdkit import Chem
from rdkit.Chem import Descriptors, FilterCatalog

logger = structlog.get_logger()


@dataclass
class PayloadCalcResult:
    """페이로드 계산 결과"""

    payload_id: str
    smiles: str
    mw: float = 0.0
    clogp: float = 0.0
    tpsa: float = 0.0
    hbd: int = 0
    hba: int = 0
    rotb: int = 0
    rings: int = 0
    arom_rings: int = 0
    fsp3: float = 0.0
    aggregation_score: float = 0.0
    bystander_proxy_score: float = 0.0
    toxicity_alerts: List[Dict[str, Any]] = field(default_factory=list)
    pains_alerts: List[Dict[str, Any]] = field(default_factory=list)
    rationale: Dict[str, List[str]] = field(
        default_factory=lambda: {"aggregation": [], "bystander": []}
    )


@dataclass
class TargetCalcResult:
    """타겟 계산 결과"""

    target_a_id: str
    target_b_id: Optional[str] = None
    expression_selectivity_score: float = 0.0
    coexpression_risk_score: float = 0.0
    internalization_score: float = 0.0
    safety_overlap_score: float = 0.0
    bsab_applicability_score: float = 0.0
    rationale: Dict[str, Any] = field(default_factory=dict)


class CalcEngine:
    """적절성 평가 및 계산 엔진"""

    def __init__(self):
        self.logger = logger.bind(service="calc_engine")
        # PAINS 및 FilterCatalog 초기화
        params = FilterCatalog.FilterCatalogParams()
        params.AddCatalogs(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
        params.AddCatalogs(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
        self.filter_catalog = FilterCatalog.FilterCatalog(params)

        # Reactive/Electrophilic SMARTS 패턴 (예시)
        self.reactive_patterns = {
            "michael_acceptor": "[C;H1,H2]=C-C=[O,S]",
            "epoxide": "C1OC1",
            "acyl_halide": "C(=O)[Cl,Br,I]",
            "aldehyde": "[CX3H1]=O",
            "aniline": "c[NH2]",
        }

    def calculate_payload(
        self, payload_id: str, smiles: str
    ) -> Optional[PayloadCalcResult]:
        """페이로드 물성 및 점수 계산"""
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            self.logger.error("invalid_smiles", payload_id=payload_id, smiles=smiles)
            return None

        res = PayloadCalcResult(payload_id=payload_id, smiles=smiles)

        # 1. 기본 Descriptor
        res.mw = Descriptors.MolWt(mol)
        res.clogp = Descriptors.MolLogP(mol)
        res.tpsa = Descriptors.TPSA(mol)
        res.hbd = Descriptors.NumHDonors(mol)
        res.hba = Descriptors.NumHAcceptors(mol)
        res.rotb = Descriptors.NumRotatableBonds(mol)
        res.rings = Descriptors.RingCount(mol)
        res.arom_rings = Descriptors.NumAromaticRings(mol)
        res.fsp3 = Descriptors.FractionCSP3(mol)

        # 2. Aggregation Risk Score (0~100)
        res.aggregation_score, res.rationale["aggregation"] = (
            self._calc_aggregation_score(res)
        )

        # 3. Bystander Proxy Score (0~100)
        res.bystander_proxy_score, res.rationale["bystander"] = (
            self._calc_bystander_score(res)
        )

        # 4. Toxicity & PAINS Alerts
        res.toxicity_alerts = self._check_toxicity_alerts(mol)
        res.pains_alerts = self._check_pains_alerts(mol)

        return res

    def _calc_aggregation_score(
        self, res: PayloadCalcResult
    ) -> tuple[float, List[str]]:
        """응집성 점수 산출 (설계서 규칙 반영)"""
        score = 0.0
        rationale = []

        if res.clogp > 3.5:
            score += 20
            rationale.append(f"High cLogP ({res.clogp:.2f}) > 3.5: +20")
        if res.tpsa < 40:
            score += 15
            rationale.append(f"Low TPSA ({res.tpsa:.2f}) < 40: +15")
        if res.arom_rings >= 3:
            score += 10
            rationale.append(f"High Aromatic Rings ({res.arom_rings}) >= 3: +10")
        if res.rings >= 4:
            score += 10
            rationale.append(f"High Ring Count ({res.rings}) >= 4: +10")
        if res.rotb > 8:
            score += 10
            rationale.append(f"High Rotatable Bonds ({res.rotb}) > 8: +10")
        if res.mw > 700:
            score += 10
            rationale.append(f"High MW ({res.mw:.2f}) > 700: +10")
        if res.fsp3 > 0.35:
            score -= 10
            rationale.append(
                f"High Fsp3 ({res.fsp3:.2f}) > 0.35: -10 (Risk Mitigation)"
            )

        return max(0.0, min(100.0, score)), rationale

    def _calc_bystander_score(self, res: PayloadCalcResult) -> tuple[float, List[str]]:
        """바이스텐딩 점수 산출 (설계서 규칙 반영)"""
        score = 50.0  # 기본 점수
        rationale = ["Base score: 50"]

        if 2.0 <= res.clogp <= 4.5:
            score += 15
            rationale.append(f"Optimal cLogP ({res.clogp:.2f}) for permeability: +15")
        if res.tpsa < 70:
            score += 10
            rationale.append(f"Low TPSA ({res.tpsa:.2f}) < 70: +10")
        elif res.tpsa > 120:
            score -= 15
            rationale.append(f"High TPSA ({res.tpsa:.2f}) > 120: -15")

        if res.hbd >= 3:
            score -= 10
            rationale.append(f"High HBD ({res.hbd}) >= 3: -10")
        if res.mw > 900:
            score -= 10
            rationale.append(f"High MW ({res.mw:.2f}) > 900: -10")

        return max(0.0, min(100.0, score)), rationale

    def _check_toxicity_alerts(self, mol: Chem.Mol) -> List[Dict[str, Any]]:
        """반응성 모티프 알럿 체크"""
        alerts = []
        for name, smarts in self.reactive_patterns.items():
            patt = Chem.MolFromSmarts(smarts)
            if mol.HasSubstructMatch(patt):
                alerts.append(
                    {
                        "rule_id": f"TOX_{name.upper()}",
                        "name": name,
                        "severity": "high",
                        "matched_smarts": smarts,
                    }
                )
        return alerts

    def _check_pains_alerts(self, mol: Chem.Mol) -> List[Dict[str, Any]]:
        """PAINS/Brenk 알럿 체크"""
        alerts = []
        matches = self.filter_catalog.GetMatches(mol)
        for match in matches:
            alerts.append(
                {"rule_id": match.GetDescription(), "name": match.GetDescription()}
            )
        return alerts

    def calculate_bsab_applicability(
        self, target_a: Dict[str, Any], target_b: Dict[str, Any]
    ) -> TargetCalcResult:
        """다중항체(bsAb) 적용 가능성 평가"""
        res = TargetCalcResult(target_a_id=target_a["id"], target_b_id=target_b["id"])

        # 1. Expression Selectivity (0~25)
        # HPA 데이터 기반 (MVP: 카테고리 점수화)
        sel_score = self._score_selectivity(target_a, target_b)
        res.expression_selectivity_score = sel_score

        # 2. Co-expression Risk (0~25, 역점수)
        co_risk = self._score_coexpression_risk(target_a, target_b)
        res.coexpression_risk_score = co_risk

        # 3. Internalization Score (0~25)
        int_score = self._score_internalization(target_a, target_b)
        res.internalization_score = int_score

        # 4. Safety Overlap Score (0~25, 역점수)
        saf_score = self._score_safety_overlap(target_a, target_b)
        res.safety_overlap_score = saf_score

        # 최종 점수
        res.bsab_applicability_score = max(
            0.0, min(100.0, sel_score + int_score - co_risk - saf_score)
        )

        return res

    def _score_selectivity(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        # MVP: 단순 가점 (추후 HPA 연동)
        return 20.0

    def _score_coexpression_risk(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        # MVP: 단순 감점
        return 5.0

    def _score_internalization(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        # UniProt subcellular location 기반
        score = 0.0
        for t in [a, b]:
            loc = t.get("subcellular_location", "").lower()
            if "membrane" in loc or "surface" in loc:
                score += 10.0
        return min(25.0, score)

    def _score_safety_overlap(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        # MVP: 단순 감점
        return 5.0


def get_calc_engine() -> CalcEngine:
    return CalcEngine()
