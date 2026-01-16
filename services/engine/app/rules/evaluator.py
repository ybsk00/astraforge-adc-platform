"""
Safe Expression Evaluator
화이트리스트 기반 조건 평가기 - eval 절대 금지

구현 계획 v2 기반:
- 토큰화: (필드, 연산자, 상수)만 허용
- 허용 연산자: >, <, >=, <=, ==, !=, in, contains
- 복합 조건: all (AND), any (OR)
"""

import re
import operator
from typing import Dict, Any, List, Tuple
import structlog

logger = structlog.get_logger()


class EvaluatorError(Exception):
    """평가기 오류"""

    pass


class SafeExpressionEvaluator:
    """
    화이트리스트 기반 표현식 평가기

    보안: eval() 절대 사용 금지
    """

    # 허용된 연산자
    OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    # 특수 연산자 (별도 처리)
    SPECIAL_OPERATORS = {"in", "not_in", "contains", "is_null", "is_not_null"}

    # 표현식 파싱 정규식
    # 예: "DAR > 8", "LogP >= 4.0", "payload_class == 'withdrawn'"
    EXPRESSION_PATTERN = re.compile(
        r"^\s*(\w+)\s*(>|<|>=|<=|==|!=|in|not_in|contains|is_null|is_not_null)\s*(.*)$",
        re.IGNORECASE,
    )

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
        self.logger = logger.bind(component="SafeExpressionEvaluator")

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        표현식 평가

        Args:
            expression: 평가할 표현식 (예: "DAR > 8")
            context: 변수 컨텍스트

        Returns:
            (결과, 매칭 이유)
        """
        expression = expression.strip()

        if not expression:
            return False, "empty expression"

        try:
            match = self.EXPRESSION_PATTERN.match(expression)
            if not match:
                self.logger.warning("invalid_expression", expression=expression)
                return False, f"invalid expression format: {expression}"

            field_name = match.group(1)
            op_str = match.group(2).lower()
            value_str = match.group(3).strip()

            # 필드 값 조회
            if field_name not in context:
                self.logger.debug("field_not_found", field=field_name)
                return False, f"field '{field_name}' not found"

            field_value = context[field_name]

            # 특수 연산자 처리
            if op_str in self.SPECIAL_OPERATORS:
                return self._evaluate_special(
                    field_name, field_value, op_str, value_str
                )

            # 일반 비교 연산자
            if op_str not in self.OPERATORS:
                return False, f"unknown operator: {op_str}"

            # 값 파싱
            target_value = self._parse_value(value_str)

            # 타입 변환 후 비교
            result = self._compare(field_value, self.OPERATORS[op_str], target_value)

            if result:
                reason = f"{field_name} ({field_value}) {op_str} {target_value}"
            else:
                reason = ""

            return result, reason

        except Exception as e:
            self.logger.error("evaluation_error", expression=expression, error=str(e))
            return False, f"evaluation error: {str(e)}"

    def _evaluate_special(
        self, field_name: str, field_value: Any, op: str, value_str: str
    ) -> Tuple[bool, str]:
        """특수 연산자 평가"""

        if op == "is_null":
            result = field_value is None
            return result, f"{field_name} is null" if result else ""

        if op == "is_not_null":
            result = field_value is not None
            return result, f"{field_name} is not null" if result else ""

        if op == "in":
            # value_str는 리스트 형태: ['a', 'b', 'c'] 또는 [1, 2, 3]
            target_list = self._parse_list(value_str)
            result = field_value in target_list
            return (
                result,
                f"{field_name} ({field_value}) in {target_list}" if result else "",
            )

        if op == "not_in":
            target_list = self._parse_list(value_str)
            result = field_value not in target_list
            return (
                result,
                f"{field_name} ({field_value}) not in {target_list}" if result else "",
            )

        if op == "contains":
            target = self._parse_value(value_str)
            result = self._evaluate_contains(field_value, target)
            return result, f"{field_name} contains '{target}'" if result else ""

        return False, f"unknown special operator: {op}"

    def _evaluate_contains(self, field_value: Any, target: Any) -> bool:
        """
        contains 연산자 평가
        - 리스트/셋: membership
        - 문자열: substring
        """
        if field_value is None:
            return False

        if isinstance(field_value, (list, set, tuple)):
            return target in field_value

        if isinstance(field_value, str):
            target_str = str(target)
            if not self.case_sensitive:
                return target_str.lower() in field_value.lower()
            return target_str in field_value

        return False

    def _parse_value(self, value_str: str) -> Any:
        """문자열을 적절한 타입으로 파싱"""
        value_str = value_str.strip()

        # 빈 문자열
        if not value_str:
            return ""

        # 따옴표로 감싼 문자열
        if (value_str.startswith("'") and value_str.endswith("'")) or (
            value_str.startswith('"') and value_str.endswith('"')
        ):
            return value_str[1:-1]

        # 불리언
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # 숫자
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # 그 외 문자열
        return value_str

    def _parse_list(self, value_str: str) -> List[Any]:
        """리스트 파싱: ['a', 'b'] 또는 [1, 2, 3]"""
        value_str = value_str.strip()

        # [] 제거
        if value_str.startswith("[") and value_str.endswith("]"):
            value_str = value_str[1:-1]

        items = []
        for item in value_str.split(","):
            items.append(self._parse_value(item.strip()))

        return items

    def _compare(self, left: Any, op_func, right: Any) -> bool:
        """타입 안전 비교"""
        try:
            # 타입 통일
            if isinstance(left, bool) and isinstance(right, bool):
                return op_func(left, right)

            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return op_func(float(left), float(right))

            if isinstance(left, str) and isinstance(right, str):
                if not self.case_sensitive:
                    return op_func(left.lower(), right.lower())
                return op_func(left, right)

            # 타입이 다르면 문자열로 변환하여 비교
            return op_func(str(left), str(right))

        except Exception:
            return False

    def evaluate_condition(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        복합 조건 평가 (all/any)

        Args:
            condition: 조건 딕셔너리
                - expression: 단순 표현식
                - all: AND 조건 리스트
                - any: OR 조건 리스트
            context: 변수 컨텍스트
        """
        # 단순 표현식
        if "expression" in condition and condition["expression"]:
            return self.evaluate(condition["expression"], context)

        # AND 조건 (all)
        if "all" in condition and condition["all"]:
            reasons = []
            for cond in condition["all"]:
                if isinstance(cond, dict) and "field" in cond:
                    # 구조화된 조건: {field, operator, value}
                    expr = f"{cond['field']} {cond['operator']} {cond['value']}"
                    result, reason = self.evaluate(expr, context)
                else:
                    result, reason = self.evaluate_condition(cond, context)

                if not result:
                    return False, ""
                if reason:
                    reasons.append(reason)

            return True, " AND ".join(reasons)

        # OR 조건 (any)
        if "any" in condition and condition["any"]:
            for cond in condition["any"]:
                if isinstance(cond, dict) and "field" in cond:
                    expr = f"{cond['field']} {cond['operator']} {cond['value']}"
                    result, reason = self.evaluate(expr, context)
                else:
                    result, reason = self.evaluate_condition(cond, context)

                if result:
                    return True, reason

            return False, ""

        return False, "no valid condition found"


def get_evaluator(case_sensitive: bool = False) -> SafeExpressionEvaluator:
    """평가기 인스턴스 반환"""
    return SafeExpressionEvaluator(case_sensitive=case_sensitive)
