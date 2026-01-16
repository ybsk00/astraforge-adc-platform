"""
Rule Engine
YAML 룰셋 기반 후보 평가

구현 계획 v2 기반:
- 결정론적 룰 평가 (priority ASC, id ASC)
- 동시 적중 처리: hard_reject 즉시종료, penalty 누적, alert/protocol 누적
- candidate_rule_hits 기록용 결과 생성
"""

from typing import Dict, Any, List
import structlog

from .models import (
    Rule,
    RuleSet,
    RuleResult,
    EvaluationResult,
    CandidateFeatures,
    ActionType,
)
from .evaluator import SafeExpressionEvaluator

logger = structlog.get_logger()


class RuleEngine:
    """
    Rule Engine v1.0

    - YAML 룰셋 로드 및 평가
    - 결정론적 평가 순서 보장
    - 동시 적중 처리 정책 적용
    """

    def __init__(
        self,
        ruleset: RuleSet = None,
        evaluator: SafeExpressionEvaluator = None,
        stop_on_hard_reject: bool = True,
    ):
        """
        Args:
            ruleset: 적용할 룰셋
            evaluator: 표현식 평가기
            stop_on_hard_reject: hard_reject 시 후속 룰 평가 중단 여부
        """
        self.ruleset = ruleset
        self.evaluator = evaluator or SafeExpressionEvaluator()
        self.stop_on_hard_reject = stop_on_hard_reject
        self.logger = logger.bind(service="rule_engine")

    def set_ruleset(self, ruleset: RuleSet):
        """룰셋 설정"""
        self.ruleset = ruleset
        self.logger.info(
            "ruleset_loaded",
            version=ruleset.version,
            rule_count=len(ruleset.rules),
            enabled_count=len([r for r in ruleset.rules if r.enabled]),
        )

    def evaluate_candidate(
        self, features: CandidateFeatures, ruleset: RuleSet = None
    ) -> EvaluationResult:
        """
        단일 후보 평가

        Args:
            features: 평가 대상 피처
            ruleset: 사용할 룰셋 (미지정 시 self.ruleset 사용)

        Returns:
            EvaluationResult
        """
        ruleset = ruleset or self.ruleset
        if not ruleset:
            self.logger.warning("no_ruleset_configured")
            return EvaluationResult()

        # 평가 컨텍스트 생성
        context = features.to_dict()

        # 결과 초기화
        result = EvaluationResult()

        # 정렬된 룰 가져오기 (priority ASC, id ASC)
        sorted_rules = ruleset.get_sorted_rules()

        for rule in sorted_rules:
            rule_result = self._evaluate_rule(rule, context)

            if not rule_result.matched:
                continue

            # 적중 기록
            result.hits.append(rule_result)

            # 액션 처리
            if rule_result.action == ActionType.HARD_REJECT:
                result.hard_rejected = True
                result.reject_reason = rule_result.message
                result.reject_rule_id = rule_result.rule_id

                if self.stop_on_hard_reject:
                    self.logger.info(
                        "hard_reject_triggered",
                        rule_id=rule.id,
                        reason=rule_result.matched_reason,
                    )
                    break

            elif rule_result.action == ActionType.SOFT_REJECT:
                result.hard_rejected = True  # soft_reject도 reject 취급
                result.reject_reason = rule_result.message
                result.reject_rule_id = rule_result.rule_id
                # soft_reject는 계속 평가 (기록 목적)

            elif rule_result.action == ActionType.PENALTY:
                # 페널티 누적
                if ruleset.penalty_policy == "sum":
                    result.total_penalty += rule_result.delta
                else:  # "max"
                    result.total_penalty = max(result.total_penalty, rule_result.delta)
                result.penalty_breakdown[rule.id] = rule_result.delta

            elif rule_result.action == ActionType.ALERT:
                result.alerts.append(rule_result)

            elif rule_result.action == ActionType.REQUIRE_PROTOCOL:
                # 중복 제거하면서 추가
                for proto in rule_result.required_protocols:
                    if proto not in result.required_protocols:
                        result.required_protocols.append(proto)

        self.logger.debug(
            "evaluation_complete",
            hard_rejected=result.hard_rejected,
            total_penalty=result.total_penalty,
            alert_count=len(result.alerts),
            protocol_count=len(result.required_protocols),
            hit_count=len(result.hits),
        )

        return result

    def _evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleResult:
        """단일 룰 평가"""
        # 조건 딕셔너리 구성
        condition_dict = {
            "expression": rule.condition.expression,
            "all": rule.condition.all_conditions,
            "any": rule.condition.any_conditions,
        }

        # 평가
        matched, reason = self.evaluator.evaluate_condition(condition_dict, context)

        # 필요한 입력 변수 스냅샷
        inputs_snapshot = self._extract_inputs_snapshot(rule, context)

        # 결과 생성
        result = RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            matched=matched,
            action=rule.action.type,
            severity=rule.action.severity,
            message=rule.action.message if matched else "",
            matched_reason=reason,
            inputs_snapshot=inputs_snapshot,
        )

        # 액션별 추가 처리
        if matched:
            if rule.action.type == ActionType.PENALTY:
                result.delta = rule.action.value

            elif rule.action.type == ActionType.REQUIRE_PROTOCOL:
                if rule.action.template_id:
                    result.required_protocols = [rule.action.template_id]

        return result

    def _extract_inputs_snapshot(
        self, rule: Rule, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """룰 평가에 사용된 변수 스냅샷 추출"""
        snapshot = {}

        # 표현식에서 필드명 추출
        expression = rule.condition.expression
        if expression:
            # 간단한 필드명 추출 (첫 번째 단어)
            field_match = expression.split()[0] if expression.split() else None
            if field_match and field_match in context:
                snapshot[field_match] = context[field_match]

        # all/any 조건에서 필드명 추출
        for cond_list in [rule.condition.all_conditions, rule.condition.any_conditions]:
            for cond in cond_list:
                if isinstance(cond, dict) and "field" in cond:
                    field = cond["field"]
                    if field in context:
                        snapshot[field] = context[field]

        return snapshot

    def evaluate_batch(
        self, candidates: List[CandidateFeatures], ruleset: RuleSet = None
    ) -> List[EvaluationResult]:
        """
        배치 평가

        Args:
            candidates: 평가 대상 후보 리스트
            ruleset: 사용할 룰셋

        Returns:
            List[EvaluationResult]
        """
        return [self.evaluate_candidate(c, ruleset) for c in candidates]

    def get_required_protocols(
        self, features: CandidateFeatures, ruleset: RuleSet = None
    ) -> List[str]:
        """필수 프로토콜 목록 반환"""
        result = self.evaluate_candidate(features, ruleset)
        return result.required_protocols

    def check_hard_reject(
        self, features: CandidateFeatures, ruleset: RuleSet = None
    ) -> tuple[bool, str]:
        """
        하드리젝트 여부 확인

        Returns:
            (rejected, reason)
        """
        result = self.evaluate_candidate(features, ruleset)
        return result.hard_rejected, result.reject_reason


def get_rule_engine(
    ruleset: RuleSet = None, stop_on_hard_reject: bool = True
) -> RuleEngine:
    """Rule Engine 인스턴스 반환"""
    return RuleEngine(ruleset=ruleset, stop_on_hard_reject=stop_on_hard_reject)
