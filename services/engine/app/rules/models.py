"""
Rule Engine Models
데이터클래스 및 타입 정의

구현 계획 v2 기반:
- Rule, RuleCondition, RuleAction
- RuleResult, EvaluationResult
- CandidateFeatures (표준화된 입력)
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ActionType(str, Enum):
    """룰 액션 타입"""
    HARD_REJECT = "hard_reject"
    SOFT_REJECT = "soft_reject"
    PENALTY = "penalty"
    ALERT = "alert"
    REQUIRE_PROTOCOL = "require_protocol"


class Severity(str, Enum):
    """심각도 레벨"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RuleCondition:
    """룰 조건"""
    expression: str = ""
    all_conditions: List[Dict[str, Any]] = field(default_factory=list)  # AND
    any_conditions: List[Dict[str, Any]] = field(default_factory=list)  # OR
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleCondition":
        if isinstance(data, str):
            return cls(expression=data)
        return cls(
            expression=data.get("expression", ""),
            all_conditions=data.get("all", []),
            any_conditions=data.get("any", [])
        )


@dataclass
class RuleAction:
    """룰 액션"""
    type: ActionType
    message: str = ""
    value: float = 0.0  # penalty 값
    target: str = "EngFit"  # penalty 적용 대상
    template_id: str = ""  # require_protocol 시 템플릿 ID
    severity: Severity = Severity.INFO
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleAction":
        action_type = ActionType(data.get("type", "alert"))
        severity_str = data.get("severity", "info")
        severity = Severity(severity_str) if severity_str in [s.value for s in Severity] else Severity.INFO
        
        return cls(
            type=action_type,
            message=data.get("message", ""),
            value=float(data.get("value", 0.0)),
            target=data.get("target", "EngFit"),
            template_id=data.get("template_id", ""),
            severity=severity
        )


@dataclass
class Rule:
    """룰 정의"""
    id: str
    name: str
    priority: int = 10
    enabled: bool = True
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    rationale: str = ""
    condition: RuleCondition = field(default_factory=RuleCondition)
    action: RuleAction = field(default_factory=lambda: RuleAction(type=ActionType.ALERT))
    references: List[Dict[str, str]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            priority=int(data.get("priority", 10)),
            enabled=data.get("enabled", True),
            version=data.get("version", "1.0"),
            tags=data.get("tags", []),
            rationale=data.get("rationale", ""),
            condition=RuleCondition.from_dict(data.get("condition", {})),
            action=RuleAction.from_dict(data.get("action", {})),
            references=data.get("references", [])
        )


@dataclass
class RuleResult:
    """단일 룰 평가 결과"""
    rule_id: str
    rule_name: str
    matched: bool
    action: ActionType
    delta: float = 0.0  # penalty 시 감점량
    severity: Severity = Severity.INFO
    matched_reason: str = ""  # 어떤 조건이 참이었는지
    message: str = ""
    inputs_snapshot: Dict[str, Any] = field(default_factory=dict)  # 평가에 사용된 변수
    required_protocols: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "matched": self.matched,
            "action": self.action.value,
            "delta": self.delta,
            "severity": self.severity.value,
            "matched_reason": self.matched_reason,
            "message": self.message,
            "inputs_snapshot": self.inputs_snapshot,
            "required_protocols": self.required_protocols
        }


@dataclass
class EvaluationResult:
    """전체 평가 결과 (여러 룰 적용 후)"""
    hard_rejected: bool = False
    reject_reason: str = ""
    reject_rule_id: str = ""
    total_penalty: float = 0.0
    penalty_breakdown: Dict[str, float] = field(default_factory=dict)  # rule_id -> delta
    alerts: List[RuleResult] = field(default_factory=list)
    required_protocols: List[str] = field(default_factory=list)  # 중복 제거됨
    hits: List[RuleResult] = field(default_factory=list)  # 적중한 모든 룰
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hard_rejected": self.hard_rejected,
            "reject_reason": self.reject_reason,
            "reject_rule_id": self.reject_rule_id,
            "total_penalty": self.total_penalty,
            "penalty_breakdown": self.penalty_breakdown,
            "alerts": [a.to_dict() for a in self.alerts],
            "required_protocols": self.required_protocols,
            "hits": [h.to_dict() for h in self.hits]
        }


@dataclass
class CandidateFeatures:
    """
    룰 평가에 필요한 필드 표준화
    룰은 이 클래스의 필드만 참조 가능
    """
    # 기본 속성
    DAR: float = 0.0
    LogP: float = 0.0
    H_patch: float = 0.0
    molecular_weight: float = 0.0
    
    # 스코어링 결과 (Scoring Engine에서 계산)
    AggRisk: float = 0.0
    ProcRisk: float = 0.0
    AnalRisk: float = 0.0
    BioRisk: float = 0.0
    SafetyRisk: float = 0.0
    OOT: float = 0.0  # Off-Target risk
    CLV: float = 0.0  # Cleavage risk
    INT: float = 0.0  # Internalization score
    
    # 메타데이터
    payload_class: str = ""
    linker_type: str = ""
    conjugation_site: str = ""
    critical_tissue_expression: bool = False
    clinical_failure_count: int = 0
    
    # 스코어
    eng_fit: float = 0.0
    bio_fit: float = 0.0
    safety_fit: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """평가 컨텍스트용 딕셔너리 변환"""
        return {
            "DAR": self.DAR,
            "LogP": self.LogP,
            "H_patch": self.H_patch,
            "molecular_weight": self.molecular_weight,
            "AggRisk": self.AggRisk,
            "ProcRisk": self.ProcRisk,
            "AnalRisk": self.AnalRisk,
            "BioRisk": self.BioRisk,
            "SafetyRisk": self.SafetyRisk,
            "OOT": self.OOT,
            "CLV": self.CLV,
            "INT": self.INT,
            "payload_class": self.payload_class,
            "linker_type": self.linker_type,
            "conjugation_site": self.conjugation_site,
            "critical_tissue_expression": self.critical_tissue_expression,
            "clinical_failure_count": self.clinical_failure_count,
            "eng_fit": self.eng_fit,
            "bio_fit": self.bio_fit,
            "safety_fit": self.safety_fit,
        }
    
    @classmethod
    def from_candidate(cls, candidate: Dict[str, Any], scores: Dict[str, Any] = None) -> "CandidateFeatures":
        """Dict에서 표준 피처 추출"""
        props = candidate.get("properties", candidate.get("snapshot", candidate))
        score_components = scores or {}
        
        # 스코어 컴포넌트에서 리스크 값 추출
        eng_components = score_components.get("eng_fit", {}).get("terms", {})
        bio_components = score_components.get("bio_fit", {}).get("terms", {})
        safety_components = score_components.get("safety_fit", {}).get("terms", {})
        
        return cls(
            DAR=float(props.get("DAR", props.get("dar", 0.0))),
            LogP=float(props.get("LogP", props.get("logp", 0.0))),
            H_patch=float(props.get("H_patch", props.get("hydrophobic_patch", 0.0))),
            molecular_weight=float(props.get("molecular_weight", props.get("mw", 0.0))),
            AggRisk=float(eng_components.get("AggRisk", 0.0)),
            ProcRisk=float(eng_components.get("ProcRisk", 0.0)),
            AnalRisk=float(eng_components.get("AnalRisk", 0.0)),
            BioRisk=float(bio_components.get("BioRisk", 0.0)),
            SafetyRisk=float(safety_components.get("SafetyRisk", 0.0)),
            OOT=float(safety_components.get("OOT", 0.0)),
            CLV=float(safety_components.get("CLV", 0.0)),
            INT=float(bio_components.get("INT", 0.0)),
            payload_class=str(props.get("payload_class", "")),
            linker_type=str(props.get("linker_type", "")),
            conjugation_site=str(props.get("conjugation_site", "")),
            critical_tissue_expression=bool(props.get("critical_tissue_expression", False)),
            clinical_failure_count=int(props.get("clinical_failure_count", 0)),
            eng_fit=float(score_components.get("eng_fit", {}).get("final", 0.0)),
            bio_fit=float(score_components.get("bio_fit", {}).get("final", 0.0)),
            safety_fit=float(score_components.get("safety_fit", {}).get("final", 0.0)),
        )


@dataclass
class RuleSet:
    """룰셋 (버전화된 룰 집합)"""
    version: str
    description: str = ""
    created_at: str = ""
    author: str = ""
    inputs_contract: List[str] = field(default_factory=list)
    penalty_policy: str = "sum"  # "sum" or "max"
    rules: List[Rule] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleSet":
        rules = [Rule.from_dict(r) for r in data.get("rules", [])]
        return cls(
            version=data.get("version", "0.0"),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            author=data.get("author", ""),
            inputs_contract=data.get("inputs_contract", []),
            penalty_policy=data.get("penalty_policy", "sum"),
            rules=rules
        )
    
    def get_sorted_rules(self) -> List[Rule]:
        """결정론적 순서로 룰 정렬: (priority ASC, id ASC)"""
        return sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: (r.priority, r.id)
        )
