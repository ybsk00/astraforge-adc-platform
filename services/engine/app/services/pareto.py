"""
Pareto Service
다차원 점수 기반 파레토 최적화 (Pareto Front)

체크리스트 §6.3 기반:
- Non-dominated Sorting
- Multi-objective Selection (Bio, Safety, Eng, Clin)
"""

from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class ParetoService:
    """파레토 최적화 서비스"""

    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="pareto")

    def calculate_pareto_fronts(
        self, candidates: List[Dict[str, Any]], dimensions: List[str]
    ) -> List[List[str]]:
        """비지배 정렬을 통한 파레토 프론트 산출"""
        if not candidates:
            return []

        # dimensions: ["bio_fit", "safety_fit", "eng_fit", "clin_fit"]

        # 1. 각 후보가 지배하는 후보들과 지배당하는 횟수 초기화
        S = [[] for _ in range(len(candidates))]
        n = [0 for _ in range(len(candidates))]
        fronts = [[]]

        for p in range(len(candidates)):
            for q in range(len(candidates)):
                if self._dominates(candidates[p], candidates[q], dimensions):
                    S[p].append(q)
                elif self._dominates(candidates[q], candidates[p], dimensions):
                    n[p] += 1

            if n[p] == 0:
                fronts[0].append(p)

        # 2. 후속 프론트 산출
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in S[p]:
                    n[q] -= 1
                    if n[q] == 0:
                        next_front.append(q)
            i += 1
            fronts.append(next_front)

        if not fronts[-1]:
            fronts.pop()

        # 인덱스를 candidate_id로 변환
        result = []
        for front in fronts:
            result.append([candidates[idx]["id"] for idx in front])

        return result

    def _dominates(
        self, p: Dict[str, Any], q: Dict[str, Any], dimensions: List[str]
    ) -> bool:
        """p가 q를 지배하는지 확인 (모든 차원에서 p >= q 이고 최소 하나에서 p > q)"""
        and_condition = True
        or_condition = False

        for dim in dimensions:
            p_val = p.get(dim, 0.0)
            q_val = q.get(dim, 0.0)

            if p_val < q_val:
                and_condition = False
                break
            if p_val > q_val:
                or_condition = True

        return and_condition and or_condition

    async def save_pareto_results(
        self, run_id: str, fronts: List[List[str]], dimensions: List[str]
    ):
        """파레토 결과를 DB에 저장"""
        for i, member_ids in enumerate(fronts):
            # 1. Front 정보 저장
            front_res = (
                await self.db.table("run_pareto_fronts")
                .insert(
                    {
                        "run_id": run_id,
                        "front_index": i,
                        "member_count": len(member_ids),
                        "dimensions": dimensions,
                    }
                )
                .execute()
            )

            front_id = front_res.data[0]["id"]

            # 2. Member 정보 저장
            members = [
                {"pareto_front_id": front_id, "candidate_id": mid} for mid in member_ids
            ]
            if members:
                await self.db.table("run_pareto_members").insert(members).execute()


def get_pareto_service(db_client) -> ParetoService:
    return ParetoService(db_client)
