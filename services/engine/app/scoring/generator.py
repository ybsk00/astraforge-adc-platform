"""
Candidate Generator
조합 폭발 방지를 위한 Generator 패턴 + Hard Reject 구현

체크리스트 §4.1, §부록C 기반
"""

import hashlib
from typing import Generator, Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class RejectReason:
    """하드 리젝트 사유"""

    code: str
    text: str
    count: int = 0


@dataclass
class GeneratorStats:
    """생성 통계"""

    total_combinations: int = 0
    hard_rejected: int = 0
    accepted: int = 0
    reject_reasons: Dict[str, RejectReason] = field(default_factory=dict)

    def add_reject(self, code: str, text: str):
        if code not in self.reject_reasons:
            self.reject_reasons[code] = RejectReason(code=code, text=text, count=0)
        self.reject_reasons[code].count += 1
        self.hard_rejected += 1


class HardRejectFilter:
    """
    하드 리젝트 필터

    조합 생성 전에 빠르게 제외할 수 있는 규칙
    """

    def __init__(self, rules: List[Dict[str, Any]] = None):
        """
        Args:
            rules: ruleset_v0.1.yaml에서 로드된 하드리젝트 규칙
        """
        self.rules = rules or []
        self.logger = logger.bind(service="hard_reject_filter")

    def check(
        self,
        target: Dict[str, Any],
        antibody: Dict[str, Any],
        linker: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        하드 리젝트 체크

        Returns:
            (is_rejected, code, reason)
        """
        # 기본 하드 리젝트 규칙

        # 1. 필수 컴포넌트 누락
        if not target or not target.get("id"):
            return True, "MISSING_TARGET", "Target component is required"
        if not payload or not payload.get("id"):
            return True, "MISSING_PAYLOAD", "Payload component is required"

        # 2. 비활성 컴포넌트
        for name, comp in [
            ("target", target),
            ("antibody", antibody),
            ("linker", linker),
            ("payload", payload),
        ]:
            if comp and comp.get("status") not in ["active", None]:
                return True, f"INACTIVE_{name.upper()}", f"{name.title()} is not active"

        # 3. Linker-Payload 호환성
        linker_type = linker.get("linker_type") if linker else None
        payload_class = payload.get("payload_class") if payload else None

        if linker_type == "cleavable" and payload_class == "non_cleavable_only":
            return (
                True,
                "LINKER_PAYLOAD_INCOMPATIBLE",
                "Cleavable linker with non-cleavable payload",
            )

        # 4. Target 발현량 임계값
        tumor_expr = target.get("expression", {}).get("tumor", 0)
        if tumor_expr < 1.0:  # 최소 발현량
            return (
                True,
                "LOW_TARGET_EXPRESSION",
                f"Target expression too low: {tumor_expr}",
            )

        # 5. ADC 제외 목록
        if target.get("adc_excluded"):
            return (
                True,
                "ADC_EXCLUDED_TARGET",
                "Target is excluded from ADC development",
            )

        # 6. 커스텀 룰 체크
        for rule in self.rules:
            if rule.get("action") == "hard_reject":
                if self._evaluate_rule(rule, target, antibody, linker, payload):
                    return (
                        True,
                        rule.get("id", "CUSTOM_RULE"),
                        rule.get("reason", "Custom rule violation"),
                    )

        return False, None, None

    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        target: Dict[str, Any],
        antibody: Dict[str, Any],
        linker: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> bool:
        """커스텀 룰 평가 (간단한 조건 체크)"""
        condition = rule.get("condition", {})

        # 컴포넌트 선택
        comp_name = condition.get("component", "target")
        comp_map = {
            "target": target,
            "antibody": antibody,
            "linker": linker,
            "payload": payload,
        }
        comp = comp_map.get(comp_name, {})

        # 필드 조건 체크
        field = condition.get("field")
        operator = condition.get("op", "eq")
        value = condition.get("value")

        if not field or value is None:
            return False

        actual = comp.get(field)
        if actual is None:
            return False

        if operator == "eq":
            return actual == value
        elif operator == "ne":
            return actual != value
        elif operator == "lt":
            return actual < value
        elif operator == "gt":
            return actual > value
        elif operator == "in":
            return actual in value
        elif operator == "not_in":
            return actual not in value

        return False


class CandidateGenerator:
    """
    후보 생성기 (Generator 패턴)

    조합 폭발 방지:
    - 배치 단위 생성 (기본 500개)
    - Hard Reject 즉시 필터링
    - 메모리 효율적 Generator 패턴
    """

    DEFAULT_BATCH_SIZE = 500

    def __init__(
        self,
        targets: List[Dict[str, Any]],
        antibodies: List[Dict[str, Any]],
        linkers: List[Dict[str, Any]],
        payloads: List[Dict[str, Any]],
        conjugations: List[Dict[str, Any]] = None,
        hard_reject_rules: List[Dict[str, Any]] = None,
        batch_size: int = None,
    ):
        """
        Args:
            targets: 활성 타겟 목록
            antibodies: 활성 항체 목록
            linkers: 활성 링커 목록
            payloads: 활성 페이로드 목록
            conjugations: 컨쥬게이션 방법 목록 (optional)
            hard_reject_rules: 하드 리젝트 규칙
            batch_size: 배치 크기
        """
        self.targets = targets or []
        self.antibodies = antibodies or [{}]  # 빈 항체도 허용
        self.linkers = linkers or [{}]
        self.payloads = payloads or []
        self.conjugations = conjugations or [{}]

        self.hard_reject_filter = HardRejectFilter(hard_reject_rules)
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self.stats = GeneratorStats()

        self.logger = logger.bind(service="candidate_generator")

        # 전체 조합 수 계산
        self.stats.total_combinations = (
            len(self.targets)
            * max(1, len(self.antibodies))
            * max(1, len(self.linkers))
            * len(self.payloads)
            * max(1, len(self.conjugations))
        )

        self.logger.info(
            "generator_initialized",
            total_combinations=self.stats.total_combinations,
            targets=len(self.targets),
            antibodies=len(self.antibodies),
            linkers=len(self.linkers),
            payloads=len(self.payloads),
        )

    def generate(self) -> Generator[Dict[str, Any], None, None]:
        """
        후보 생성 제너레이터

        Yields:
            {"target": {...}, "antibody": {...}, "linker": {...}, "payload": {...}, "hash": "..."}
        """
        for target in self.targets:
            for antibody in self.antibodies:
                for linker in self.linkers:
                    for payload in self.payloads:
                        for conjugation in self.conjugations:
                            # Hard Reject 체크
                            is_rejected, code, reason = self.hard_reject_filter.check(
                                target, antibody, linker, payload
                            )

                            if is_rejected:
                                self.stats.add_reject(code, reason)
                                continue

                            # 후보 해시 생성
                            candidate_hash = self._compute_hash(
                                target, antibody, linker, payload, conjugation
                            )

                            self.stats.accepted += 1

                            yield {
                                "target": target,
                                "antibody": antibody,
                                "linker": linker,
                                "payload": payload,
                                "conjugation": conjugation,
                                "candidate_hash": candidate_hash,
                            }

    def generate_batches(self) -> Generator[List[Dict[str, Any]], None, None]:
        """
        배치 단위 생성

        Yields:
            [candidate1, candidate2, ...]  # batch_size 개씩
        """
        batch = []

        for candidate in self.generate():
            batch.append(candidate)

            if len(batch) >= self.batch_size:
                yield batch
                batch = []

        # 남은 후보
        if batch:
            yield batch

    def _compute_hash(
        self,
        target: Dict[str, Any],
        antibody: Dict[str, Any],
        linker: Dict[str, Any],
        payload: Dict[str, Any],
        conjugation: Dict[str, Any],
    ) -> str:
        """후보 고유 해시 생성"""
        components = [
            str(target.get("id", "")),
            str(antibody.get("id", "")),
            str(linker.get("id", "")),
            str(payload.get("id", "")),
            str(conjugation.get("id", "")),
        ]
        hash_input = "|".join(components)
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def get_reject_summary(self) -> List[Dict[str, Any]]:
        """
        하드 리젝트 요약 (candidate_reject_summaries용)
        """
        return [
            {"reason_code": r.code, "reason_text": r.text, "rejected_count": r.count}
            for r in self.stats.reject_reasons.values()
        ]


def create_generator_from_catalog(
    db_client,
    target_ids: List[str] = None,
    constraints: Dict[str, Any] = None,
    hard_reject_rules: List[Dict[str, Any]] = None,
) -> CandidateGenerator:
    """
    카탈로그에서 컴포넌트 로드 후 제너레이터 생성

    Args:
        db_client: Supabase 클라이언트
        target_ids: 선택된 타겟 ID (없으면 전체)
        constraints: 필터 조건
        hard_reject_rules: 하드 리젝트 규칙

    Returns:
        CandidateGenerator 인스턴스
    """
    constraints = constraints or {}

    # 활성 컴포넌트만 로드
    def load_components(comp_type: str, ids: List[str] = None) -> List[Dict[str, Any]]:
        query = (
            db_client.table("component_catalog")
            .select("*")
            .eq("type", comp_type)
            .eq("status", "active")
        )

        if ids:
            query = query.in_("id", ids)

        result = query.execute()
        return result.data if result.data else []

    # 컴포넌트 로드
    targets = load_components("target", target_ids)
    antibodies = load_components("antibody", constraints.get("antibody_ids"))
    linkers = load_components("linker", constraints.get("linker_ids"))
    payloads = load_components("payload", constraints.get("payload_ids"))

    # 품질 등급 필터
    quality_threshold = constraints.get("min_quality_grade", "bronze")
    quality_order = {"gold": 3, "silver": 2, "bronze": 1}
    threshold = quality_order.get(quality_threshold, 1)

    def quality_filter(comp: Dict[str, Any]) -> bool:
        grade = comp.get("quality_grade", "bronze")
        return quality_order.get(grade, 1) >= threshold

    targets = [t for t in targets if quality_filter(t)]
    payloads = [p for p in payloads if quality_filter(p)]

    return CandidateGenerator(
        targets=targets,
        antibodies=antibodies,
        linkers=linkers,
        payloads=payloads,
        hard_reject_rules=hard_reject_rules,
        batch_size=constraints.get("batch_size", 500),
    )
