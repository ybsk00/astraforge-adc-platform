"""
Design Run Execution Job
Run 생성 → 후보 생성 → 스코어링 → 파레토 계산 전체 파이프라인

체크리스트 §부록C (Worker 실행 순서) 기반
"""

import os
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
import structlog

from app.scoring import (
    BatchScoringEngine,
    ParetoCalculator,
    create_generator_from_catalog,
)

logger = structlog.get_logger()


async def design_run_execute(ctx: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """
    Design Run 실행 Worker Job

    실행 순서 (§부록C):
    1. 입력 정규화 + scoring_version 고정
    2. 카탈로그 로드 (active only)
    3. 후보 생성 (generator) + 하드리젝트 → reject_summaries
    4. 배치 벡터화 스코어 계산
    5. 룰 적용 (TODO)
    6. 파레토 프론트 계산
    7. Evidence Engine (TODO - RAG)
    8. Protocol 생성 (TODO)
    9. 상태 업데이트 + run_progress 완료

    Args:
        ctx: Arq context
        run_id: design_runs.id

    Returns:
        {"status": "completed", "stats": {...}}
    """
    from supabase import create_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        return {"status": "error", "message": "Supabase not configured"}

    db = create_client(supabase_url, supabase_key)
    log = logger.bind(run_id=run_id)

    start_time = datetime.utcnow()
    stats = {
        "total_combinations": 0,
        "hard_rejected": 0,
        "accepted": 0,
        "scored": 0,
        "pareto_fronts": 0,
        "top_candidates": 0,
    }

    try:
        # ================================================
        # 1. Run 정보 로드 (이미 poll_db_jobs에서 running으로 변경됨)
        log.info("run_starting")

        run_result = db.table("design_runs").select("*").eq("id", run_id).execute()
        if not run_result.data:
            return {"status": "error", "message": "Run not found"}

        run = run_result.data[0]

        # attempt 증가 및 시작 시간 기록
        db.table("design_runs").update(
            {
                "attempt": run.get("attempt", 0) + 1,
                "started_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", run_id).execute()

        # run_progress 초기화
        db.table("run_progress").upsert(
            {
                "run_id": run_id,
                "phase": "loading",
                "processed_candidates": 0,
                "accepted_candidates": 0,
                "rejected_candidates": 0,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).execute()

        # ================================================
        # 2. 카탈로그 로드 (active only)
        # ================================================
        log.info("loading_catalog")

        target_ids = run.get("target_ids", [])
        constraints = run.get("constraints", {})

        # 룰셋 로드 (TODO: ruleset_v0.1.yaml 지원)
        hard_reject_rules = []

        generator = create_generator_from_catalog(
            db,
            target_ids=target_ids,
            constraints=constraints,
            hard_reject_rules=hard_reject_rules,
        )

        stats["total_combinations"] = generator.stats.total_combinations
        log.info("catalog_loaded", total_combinations=stats["total_combinations"])

        # ================================================
        # 3. 후보 생성 + 스코어링 (배치)
        # ================================================
        log.info("generating_candidates")

        db.table("run_progress").update(
            {"phase": "generating", "updated_at": datetime.utcnow().isoformat()}
        ).eq("run_id", run_id).execute()

        # 스코어링 파라미터 로드
        scoring_params = {}
        params_result = (
            db.table("scoring_params").select("*").eq("is_active", True).execute()
        )
        if params_result.data:
            scoring_params = params_result.data[0].get("params", {})

        scoring_engine = BatchScoringEngine(scoring_params)

        all_candidates = []
        batch_num = 0

        for batch in generator.generate_batches():
            batch_num += 1
            log.info("processing_batch", batch=batch_num, size=len(batch))

            # 스코어 계산
            scores = scoring_engine.score_batch(batch)

            # 후보 + 스코어 합치기
            for candidate, score in zip(batch, scores):
                candidate_data = {
                    "id": str(uuid4()),
                    "run_id": run_id,
                    "target_id": candidate["target"].get("id"),
                    "antibody_id": candidate["antibody"].get("id"),
                    "linker_id": candidate["linker"].get("id"),
                    "payload_id": candidate["payload"].get("id"),
                    "conjugation_id": candidate["conjugation"].get("id"),
                    "candidate_hash": candidate["candidate_hash"],
                    "snapshot": {
                        "target": candidate["target"],
                        "antibody": candidate["antibody"],
                        "linker": candidate["linker"],
                        "payload": candidate["payload"],
                    },
                    "eng_fit": score.eng_fit,
                    "bio_fit": score.bio_fit,
                    "safety_fit": score.safety_fit,
                    "evidence_fit": score.evidence_fit,
                    "score_components": scoring_engine.score_to_dict(score).get(
                        "score_components", {}
                    ),
                }
                all_candidates.append(candidate_data)

            stats["scored"] += len(batch)

            # 진행률 업데이트
            db.table("run_progress").update(
                {
                    "processed_candidates": stats["scored"],
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("run_id", run_id).execute()

        stats["hard_rejected"] = generator.stats.hard_rejected
        stats["accepted"] = generator.stats.accepted

        log.info(
            "candidates_generated",
            accepted=stats["accepted"],
            rejected=stats["hard_rejected"],
            scored=stats["scored"],
        )

        # ================================================
        # 4. 하드 리젝트 요약 저장
        # ================================================
        reject_summaries = generator.get_reject_summary()
        for summary in reject_summaries:
            db.table("candidate_reject_summaries").upsert(
                {
                    "run_id": run_id,
                    "reason_code": summary["reason_code"],
                    "reason_text": summary["reason_text"],
                    "rejected_count": summary["rejected_count"],
                    "updated_at": datetime.utcnow().isoformat(),
                },
                on_conflict="run_id,reason_code",
            ).execute()

        # ================================================
        # 5. 후보 DB 저장
        # ================================================
        log.info("saving_candidates")

        db.table("run_progress").update(
            {"phase": "saving", "updated_at": datetime.utcnow().isoformat()}
        ).eq("run_id", run_id).execute()

        # 배치 인서트 (500개씩)
        for i in range(0, len(all_candidates), 500):
            batch = all_candidates[i : i + 500]

            # candidates 테이블
            candidate_records = [
                {
                    "id": c["id"],
                    "run_id": c["run_id"],
                    "target_id": c["target_id"],
                    "antibody_id": c["antibody_id"],
                    "linker_id": c["linker_id"],
                    "payload_id": c["payload_id"],
                    "conjugation_id": c["conjugation_id"],
                    "candidate_hash": c["candidate_hash"],
                    "snapshot": c["snapshot"],
                }
                for c in batch
            ]
            db.table("candidates").insert(candidate_records).execute()

            # candidate_scores 테이블
            score_records = [
                {
                    "candidate_id": c["id"],
                    "eng_fit": c["eng_fit"],
                    "bio_fit": c["bio_fit"],
                    "safety_fit": c["safety_fit"],
                    "evidence_fit": c["evidence_fit"],
                    "score_components": c["score_components"],
                }
                for c in batch
            ]
            db.table("candidate_scores").insert(score_records).execute()

        # ================================================
        # 6. 파레토 프론트 계산
        # ================================================
        log.info("calculating_pareto")

        db.table("run_progress").update(
            {"phase": "pareto", "updated_at": datetime.utcnow().isoformat()}
        ).eq("run_id", run_id).execute()

        pareto_calculator = ParetoCalculator()
        fronts = pareto_calculator.calculate(all_candidates, max_fronts=5)

        stats["pareto_fronts"] = len(fronts)

        # 파레토 프론트 저장
        front_records, member_records = pareto_calculator.to_db_format(fronts, run_id)

        if front_records:
            db.table("run_pareto_fronts").insert(front_records).execute()
        if member_records:
            db.table("run_pareto_members").insert(member_records).execute()

        # Top-N 후보 (RAG/Protocol 우선 처리용)
        top_candidates = pareto_calculator.get_top_candidates(fronts, top_n=50)
        stats["top_candidates"] = len(top_candidates)

        log.info(
            "pareto_calculated",
            fronts=stats["pareto_fronts"],
            top_candidates=stats["top_candidates"],
        )

        # ================================================
        # 7. 보고서 오케스트레이션 (Orchestrator)
        # ================================================
        log.info("starting_orchestrator")
        from jobs.orchestrator import ReportOrchestrator

        orchestrator = ReportOrchestrator(db, run_id)
        report_data = await orchestrator.execute()

        # TODO: PDF 렌더링 및 Artifact 저장 로직 추가

        # ================================================
        # 9. 완료 상태 업데이트
        # ================================================
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        db.table("design_runs").update(
            {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "result_summary": {
                    "total_combinations": stats["total_combinations"],
                    "accepted_candidates": stats["accepted"],
                    "rejected_candidates": stats["hard_rejected"],
                    "pareto_fronts": stats["pareto_fronts"],
                    "top_candidates": stats["top_candidates"],
                    "duration_ms": duration_ms,
                },
                "locked_by": None,
                "locked_at": None,
            }
        ).eq("id", run_id).execute()

        db.table("run_progress").update(
            {
                "phase": "completed",
                "accepted_candidates": stats["accepted"],
                "rejected_candidates": stats["hard_rejected"],
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("run_id", run_id).execute()

        log.info("run_completed", duration_ms=duration_ms, stats=stats)

        return {
            "status": "completed",
            "run_id": run_id,
            "stats": stats,
            "duration_ms": duration_ms,
        }

    except Exception as e:
        log.error("run_failed", error=str(e))

        # 재시도 시간 계산
        attempt = run.get("attempt", 0) + 1 if "run" in locals() else 1
        delays = [60, 300, 900]
        delay = delays[min(attempt - 1, len(delays) - 1)]
        from datetime import timedelta

        next_retry = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()

        # 실패 상태 업데이트 및 Lock 해제
        db.table("design_runs").update(
            {
                "status": "failed",
                "result_summary": {"error": str(e)},
                "next_retry_at": next_retry,
                "locked_by": None,
                "locked_at": None,
            }
        ).eq("id", run_id).execute()

        db.table("run_progress").update(
            {"phase": "failed", "updated_at": datetime.utcnow().isoformat()}
        ).eq("run_id", run_id).execute()

        # 알림 생성
        try:
            db.table("alerts").insert(
                {
                    "type": "error",
                    "source": "worker:design_run",
                    "message": f"Design run failed: {str(e)}",
                    "details": {"run_id": run_id, "attempt": attempt},
                }
            ).execute()
        except Exception as alert_err:
            log.error("failed_to_create_alert", error=str(alert_err))

        return {"status": "error", "run_id": run_id, "error": str(e)}
