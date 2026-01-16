"""
Orchestrator Service
ADC 설계 9단계 표준 실행 워크플로우 (부록 C 준수)

1. Input Normalization
2. Candidate Generation
3. Appropriateness Evaluation (RDKit, bsAb)
4. Vectorized Scoring
5. Pareto Optimization
6. Evidence RAG
7. Protocol Generation
8. Status Update & Audit Log
9. Report Generation (Trigger)
"""

from typing import List, Dict, Any
from uuid import UUID
import structlog
from datetime import datetime

from app.services.resolver import ResolverService
from app.services.calc_engine import get_calc_engine
from app.services.scoring import get_scoring_service
from app.services.pareto import get_pareto_service
from app.services.evidence import get_evidence_service
from app.services.protocol import get_protocol_service
from app.services.report_service import get_report_service
from app.services.audit_service import get_audit_service

logger = structlog.get_logger()


class Orchestrator:
    """ADC 설계 오케스트레이터"""

    def __init__(self, db_client):
        self.db = db_client
        self.resolver = ResolverService(db_client)
        self.calc_engine = get_calc_engine()
        self.scoring_service = get_scoring_service(db_client)
        self.pareto_service = get_pareto_service(db_client)
        self.evidence_service = get_evidence_service(db_client)
        self.protocol_service = get_protocol_service()
        self.report_service = get_report_service(db_client)
        self.audit_service = get_audit_service(db_client)
        self.logger = logger.bind(service="orchestrator")

    async def run_design_pipeline(self, run_id: UUID):
        """전체 9단계 파이프라인 실행"""
        self.logger.info("design_pipeline_started", run_id=str(run_id))

        try:
            # 1. Input Normalization
            await self._update_progress(run_id, 1, "Normalization", "running")
            # TODO: Resolver 연동
            await self._update_progress(run_id, 1, "Normalization", "completed")

            # 2. Candidate Generation
            await self._update_progress(run_id, 2, "Generation", "running")
            candidates = await self._generate_candidates(run_id)
            await self._update_progress(
                run_id,
                2,
                "Generation",
                "completed",
                f"Generated {len(candidates)} candidates",
            )

            # 3. Appropriateness Evaluation (CalcEngine)
            await self._update_progress(run_id, 3, "Appropriateness", "running")
            await self._evaluate_appropriateness(run_id, candidates)
            await self._update_progress(run_id, 3, "Appropriateness", "completed")

            # 4. Vectorized Scoring
            await self._update_progress(run_id, 4, "Scoring", "running")
            score_results = await self.scoring_service.calculate_scores(
                str(run_id), candidates
            )
            # 점수 저장 (디테일 생략, MVP 수준)
            await self._update_progress(
                run_id,
                4,
                "Scoring",
                "completed",
                f"Scored {len(score_results)} candidates",
            )

            # 5. Pareto Optimization
            await self._update_progress(run_id, 5, "Pareto", "running")
            dimensions = ["bio_fit", "safety_fit", "eng_fit", "clin_fit"]
            # ScoreResult 객체를 dict로 변환하여 전달
            score_dicts = [vars(r) for r in score_results if not r.is_rejected]
            fronts = self.pareto_service.calculate_pareto_fronts(
                score_dicts, dimensions
            )
            await self.pareto_service.save_pareto_results(
                str(run_id), fronts, dimensions
            )
            await self._update_progress(
                run_id, 5, "Pareto", "completed", f"Found {len(fronts)} fronts"
            )

            # 6. Evidence RAG
            await self._update_progress(run_id, 6, "Evidence", "running")
            # Top N 후보에 대해 근거 생성 (예: Front 0 멤버들)
            top_candidate_ids = fronts[0] if fronts else []
            for cand_id in top_candidate_ids[:5]:  # MVP: 상위 5개만
                cand_data = next(c for c in candidates if c["id"] == cand_id)
                score_comp = next(
                    s for s in score_results if s.candidate_id == cand_id
                ).components
                evidence = await self.evidence_service.generate_evidence(
                    cand_data, score_comp
                )
                # DB 저장
                await (
                    self.db.table("evidence_signals")
                    .insert(self.evidence_service.to_db_format(cand_id, evidence))
                    .execute()
                )
            await self._update_progress(run_id, 6, "Evidence", "completed")

            # 7. Protocol Generation
            await self._update_progress(run_id, 7, "Protocol", "running")
            for cand_id in top_candidate_ids[:5]:
                score_comp = next(
                    s for s in score_results if s.candidate_id == cand_id
                ).components
                protocols = self.protocol_service.generate_protocols(
                    cand_id, score_comp
                )
                for p in protocols:
                    await (
                        self.db.table("design_protocols")
                        .insert(self.protocol_service.to_db_format(p))
                        .execute()
                    )
            await self._update_progress(run_id, 7, "Protocol", "completed")

            # 8. Status Update & Audit Log
            await self._update_progress(run_id, 8, "Finalizing", "running")
            await self.audit_service.log_event("RUN_COMPLETED", resource_id=str(run_id))
            await self._update_progress(run_id, 8, "Finalizing", "completed")

            # 9. Report Generation (Trigger)
            await self._update_progress(run_id, 9, "Reporting", "running")
            report_path = await self.report_service.generate_report(run_id)
            await self._update_progress(
                run_id,
                9,
                "Reporting",
                "completed",
                f"Report generated at {report_path}",
            )

            self.logger.info("design_pipeline_completed", run_id=str(run_id))

        except Exception as e:
            self.logger.error(
                "design_pipeline_failed", run_id=str(run_id), error=str(e)
            )
            # 장애 상태 관리 (Degraded)
            await self._update_progress(
                run_id, 0, "Error", "failed", f"System Degraded: {str(e)}"
            )
            await self.audit_service.log_event(
                "RUN_FAILED", resource_id=str(run_id), metadata={"error": str(e)}
            )
            raise

    async def _update_progress(
        self, run_id: UUID, step: int, phase: str, status: str, message: str = None
    ):
        """런 진행률 업데이트"""
        data = {
            "run_id": str(run_id),
            "step_number": step,
            "phase": phase,
            "status": status,
            "message": message,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if status == "running":
            data["started_at"] = datetime.utcnow().isoformat()
        elif status == "completed":
            data["completed_at"] = datetime.utcnow().isoformat()

        await self.db.table("run_progress").upsert(data).execute()

    async def _generate_candidates(self, run_id: UUID) -> List[Dict[str, Any]]:
        """후보 조합 생성 (MVP: DB에 등록된 Target/Payload/Linker 조합)"""
        # 실제 구현에서는 필터링 및 조합 로직 필요
        res = (
            await self.db.table("design_candidates")
            .select("*")
            .eq("run_id", str(run_id))
            .execute()
        )
        return res.data

    async def _evaluate_appropriateness(
        self, run_id: UUID, candidates: List[Dict[str, Any]]
    ):
        """적절성 평가 실행 (CalcEngine)"""
        for cand in candidates:
            # 1. Payload RDKit Calculation
            payload_smiles = cand.get("payload_smiles")
            if payload_smiles:
                res = self.calc_engine.calculate_payload(
                    cand["payload_id"], payload_smiles
                )
                if res:
                    await (
                        self.db.table("computations_payload_rdkit")
                        .insert(
                            {
                                "run_id": str(run_id),
                                "payload_id": cand["payload_id"],
                                "mw": res.mw,
                                "clogp": res.clogp,
                                "tpsa": res.tpsa,
                                "hbd": res.hbd,
                                "hba": res.hba,
                                "rotb": res.rotb,
                                "rings": res.rings,
                                "arom_rings": res.arom_rings,
                                "fsp3": res.fsp3,
                                "aggregation_score": res.aggregation_score,
                                "bystander_proxy_score": res.bystander_proxy_score,
                                "toxicity_alerts": res.toxicity_alerts,
                                "pains_alerts": res.pains_alerts,
                            }
                        )
                        .execute()
                    )

            # 2. bsAb Applicability (Target A & B 존재 시)
            # TODO: 다중항체 후보인 경우 로직 추가
            pass


def get_orchestrator(db_client) -> Orchestrator:
    return Orchestrator(db_client)
