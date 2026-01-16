"""
Pareto Front Calculator
다중 목적 최적화를 위한 파레토 프론트 계산

NSGA-II 기반 비지배 정렬 + 혼잡도 거리
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class ParetoMember:
    """파레토 프론트 멤버"""

    candidate_id: str
    rank: int
    crowding_distance: float
    objectives: Dict[str, float]


@dataclass
class ParetoFront:
    """파레토 프론트"""

    front_index: int
    objectives: List[str]
    members: List[ParetoMember] = field(default_factory=list)

    @property
    def member_count(self) -> int:
        return len(self.members)


class ParetoCalculator:
    """
    파레토 프론트 계산기

    4축 목적 함수:
    - eng_fit (최대화)
    - bio_fit (최대화)
    - safety_fit (최대화)
    - evidence_fit (최대화)
    """

    DEFAULT_OBJECTIVES = ["eng_fit", "bio_fit", "safety_fit", "evidence_fit"]

    def __init__(self, objectives: List[str] = None):
        """
        Args:
            objectives: 목적 함수 목록 (기본: 4축)
        """
        self.objectives = objectives or self.DEFAULT_OBJECTIVES
        self.logger = logger.bind(service="pareto_calculator")

    def calculate(
        self, candidates: List[Dict[str, Any]], max_fronts: int = 5
    ) -> List[ParetoFront]:
        """
        파레토 프론트 계산

        Args:
            candidates: [{"id": "...", "eng_fit": 80, "bio_fit": 70, ...}, ...]
            max_fronts: 최대 프론트 수

        Returns:
            List of ParetoFront
        """
        if not candidates:
            return []

        n = len(candidates)
        self.logger.info("pareto_calculating", candidates=n, objectives=self.objectives)

        # 1. 지배 관계 계산
        domination_count = [0] * n  # 각 후보가 지배당하는 횟수
        dominated_by = [[] for _ in range(n)]  # 각 후보를 지배하는 후보 목록

        for i in range(n):
            for j in range(n):
                if i != j:
                    if self._dominates(candidates[i], candidates[j]):
                        dominated_by[j].append(i)
                        domination_count[j] += 1

        # 2. 프론트 분리
        fronts: List[ParetoFront] = []
        remaining = set(range(n))
        front_idx = 0

        while remaining and front_idx < max_fronts:
            # 지배당하지 않는 후보들 = 현재 프론트
            current_front_indices = [i for i in remaining if domination_count[i] == 0]

            if not current_front_indices:
                break

            # 혼잡도 거리 계산
            crowding = self._calculate_crowding_distance(
                [candidates[i] for i in current_front_indices]
            )

            # 프론트 생성
            front = ParetoFront(
                front_index=front_idx,
                objectives=self.objectives,
                members=[
                    ParetoMember(
                        candidate_id=str(candidates[idx].get("id", idx)),
                        rank=front_idx,
                        crowding_distance=crowding[i],
                        objectives={
                            obj: candidates[idx].get(obj, 0) for obj in self.objectives
                        },
                    )
                    for i, idx in enumerate(current_front_indices)
                ],
            )
            fronts.append(front)

            # 현재 프론트 제거 후 나머지 지배 횟수 업데이트
            for i in current_front_indices:
                remaining.remove(i)
                for j in remaining:
                    if i in dominated_by[j]:
                        domination_count[j] -= 1

            front_idx += 1

        self.logger.info(
            "pareto_calculated",
            fronts=len(fronts),
            front_sizes=[f.member_count for f in fronts],
        )

        return fronts

    def _dominates(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        """
        a가 b를 지배하는지 확인

        a가 b를 지배하려면:
        - 모든 목적에서 a >= b
        - 적어도 하나의 목적에서 a > b
        """
        dominated = False
        for obj in self.objectives:
            a_val = a.get(obj, 0)
            b_val = b.get(obj, 0)

            if a_val < b_val:
                return False  # a가 b보다 열등한 목적이 있으면 지배하지 않음
            elif a_val > b_val:
                dominated = True  # a가 b보다 우월한 목적이 있음

        return dominated

    def _calculate_crowding_distance(
        self, candidates: List[Dict[str, Any]]
    ) -> List[float]:
        """
        혼잡도 거리 계산

        각 목적 함수별로 정렬 후 이웃과의 거리 합산
        """
        n = len(candidates)
        if n <= 2:
            return [float("inf")] * n

        distances = [0.0] * n

        for obj in self.objectives:
            # 목적 함수별 정렬
            sorted_indices = sorted(range(n), key=lambda i: candidates[i].get(obj, 0))

            # 경계값 (무한대할당)
            distances[sorted_indices[0]] = float("inf")
            distances[sorted_indices[-1]] = float("inf")

            # 중간값 거리 계산
            obj_min = candidates[sorted_indices[0]].get(obj, 0)
            obj_max = candidates[sorted_indices[-1]].get(obj, 0)
            obj_range = obj_max - obj_min if obj_max != obj_min else 1

            for i in range(1, n - 1):
                prev_val = candidates[sorted_indices[i - 1]].get(obj, 0)
                next_val = candidates[sorted_indices[i + 1]].get(obj, 0)
                distances[sorted_indices[i]] += (next_val - prev_val) / obj_range

        return distances

    def get_top_candidates(
        self, fronts: List[ParetoFront], top_n: int = 50
    ) -> List[str]:
        """
        상위 N개 후보 ID 추출

        랭크 우선, 같은 랭크면 혼잡도 거리 높은 순
        """
        all_members = []
        for front in fronts:
            all_members.extend(front.members)

        # 정렬: 랭크 오름차순, 혼잡도 내림차순
        all_members.sort(key=lambda m: (m.rank, -m.crowding_distance))

        return [m.candidate_id for m in all_members[:top_n]]

    def to_db_format(
        self, fronts: List[ParetoFront], run_id: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        DB 저장용 포맷 변환

        Returns:
            (run_pareto_fronts records, run_pareto_members records)
        """
        front_records = []
        member_records = []

        for front in fronts:
            front_id = f"{run_id}_{front.front_index}"

            front_records.append(
                {
                    "id": front_id,
                    "run_id": run_id,
                    "front_index": front.front_index,
                    "objectives": front.objectives,
                    "member_count": front.member_count,
                }
            )

            for member in front.members:
                member_records.append(
                    {
                        "front_id": front_id,
                        "candidate_id": member.candidate_id,
                        "rank": member.rank,
                        "crowding_distance": member.crowding_distance,
                    }
                )

        return front_records, member_records


# 편의 함수
def calculate_pareto_fronts(
    candidates: List[Dict[str, Any]], objectives: List[str] = None, max_fronts: int = 5
) -> List[ParetoFront]:
    """파레토 프론트 계산 편의 함수"""
    calculator = ParetoCalculator(objectives)
    return calculator.calculate(candidates, max_fronts)
