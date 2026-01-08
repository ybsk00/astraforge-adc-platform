"""
Design Run API Endpoints
Run 생성/조회/관리 + 후보 조회

Phase 1 핵심 API
"""
import os
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
import uuid
import structlog

router = APIRouter()
logger = structlog.get_logger()


def get_db():
    """Supabase 클라이언트 의존성"""
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    return create_client(supabase_url, supabase_key)


# === Schemas ===

class RunConstraints(BaseModel):
    """런 제약조건"""
    dar_min: float = 2.0
    dar_max: float = 8.0
    conjugation_mode: Literal["random", "site_specific", "both"] = "both"
    min_quality_grade: Literal["gold", "silver", "bronze"] = "bronze"
    forbidden_payloads: List[str] = []
    forbidden_linkers: List[str] = []
    antibody_ids: Optional[List[str]] = None
    linker_ids: Optional[List[str]] = None
    payload_ids: Optional[List[str]] = None
    batch_size: int = 500


class RunCreate(BaseModel):
    """런 생성 요청"""
    target_ids: List[str] = Field(..., min_length=1, description="선택된 타겟 ID 목록")
    indication: str = Field(..., description="적응증")
    strategy: Literal["balanced", "penetration", "stability", "cmc"] = "balanced"
    workspace_id: Optional[str] = None
    constraints: Optional[RunConstraints] = None


class RunResponse(BaseModel):
    """런 응답"""
    id: str
    status: str
    created_at: str
    target_ids: List[str]
    indication: str
    strategy: str
    result_summary: Optional[Dict[str, Any]] = None


class CandidateListItem(BaseModel):
    """후보 목록 아이템"""
    id: str
    candidate_hash: str
    target_name: Optional[str]
    payload_name: Optional[str]
    eng_fit: float
    bio_fit: float
    safety_fit: float
    evidence_fit: float
    pareto_rank: Optional[int] = None


class RunProgress(BaseModel):
    """런 진행률"""
    phase: str
    processed_candidates: int
    accepted_candidates: int
    rejected_candidates: int


# === Endpoints ===

@router.post("/runs", response_model=RunResponse)
async def create_run(run_data: RunCreate, db=Depends(get_db)):
    """
    새 Design Run 생성
    
    Run을 DB에 저장하고 Worker Job을 enqueue합니다.
    """
    run_id = str(uuid.uuid4())
    log = logger.bind(run_id=run_id)
    
    try:
        # 1. Run 저장
        run_record = {
            "id": run_id,
            "workspace_id": run_data.workspace_id,
            "target_ids": run_data.target_ids,
            "indication": run_data.indication,
            "strategy": run_data.strategy,
            "constraints": run_data.constraints.model_dump() if run_data.constraints else {},
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.table("design_runs").insert(run_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create run")
        
        log.info("run_created", target_count=len(run_data.target_ids))
        
        # 2. Worker Job Enqueue (Redis)
        try:
            import redis
            from arq import create_pool
            from arq.connections import RedisSettings
            
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            # Parse redis URL
            settings = RedisSettings.from_dsn(redis_url)
            
            # Enqueue job (sync for now, can be async)
            r = redis.from_url(redis_url)
            # Simple job enqueue via Redis list
            import json
            job_data = json.dumps({
                "job": "design_run_execute",
                "run_id": run_id,
                "enqueue_time": datetime.utcnow().isoformat()
            })
            r.lpush("arq:queue:design_run_queue", job_data)
            
            log.info("job_enqueued", queue="design_run_queue")
            
        except Exception as e:
            log.warning("job_enqueue_failed", error=str(e))
            # Job enqueue 실패해도 run은 생성됨 (수동 실행 가능)
        
        return RunResponse(
            id=run_id,
            status="pending",
            created_at=run_record["created_at"],
            target_ids=run_data.target_ids,
            indication=run_data.indication,
            strategy=run_data.strategy
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("run_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
async def list_runs(
    status: Optional[str] = None,
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db)
):
    """런 목록 조회"""
    try:
        query = db.table("design_runs").select("*").order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        
        # Count query
        count_result = db.table("design_runs").select("id", count="exact").execute()
        total = count_result.count if count_result.count else 0
        
        # Paginated query
        result = query.range(offset, offset + limit - 1).execute()
        
        return {
            "items": result.data or [],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("list_runs_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db=Depends(get_db)):
    """런 상세 조회"""
    try:
        result = db.table("design_runs").select("*").eq("id", run_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        run = result.data[0]
        
        return RunResponse(
            id=run["id"],
            status=run["status"],
            created_at=run["created_at"],
            target_ids=run.get("target_ids", []),
            indication=run.get("indication", ""),
            strategy=run.get("strategy", "balanced"),
            result_summary=run.get("result_summary")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/progress", response_model=RunProgress)
async def get_run_progress(run_id: str, db=Depends(get_db)):
    """런 진행률 조회"""
    try:
        result = db.table("run_progress").select("*").eq("run_id", run_id).execute()
        
        if not result.data:
            return RunProgress(
                phase="unknown",
                processed_candidates=0,
                accepted_candidates=0,
                rejected_candidates=0
            )
        
        progress = result.data[0]
        
        return RunProgress(
            phase=progress.get("phase", "unknown"),
            processed_candidates=progress.get("processed_candidates", 0),
            accepted_candidates=progress.get("accepted_candidates", 0),
            rejected_candidates=progress.get("rejected_candidates", 0)
        )
        
    except Exception as e:
        logger.error("get_progress_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/candidates")
async def list_candidates(
    run_id: str,
    sort_by: str = Query("eng_fit", regex="^(eng_fit|bio_fit|safety_fit|evidence_fit)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    pareto_rank: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(get_db)
):
    """
    런의 후보 목록 조회
    
    파레토 랭크, 스코어 기준 정렬/필터링
    """
    try:
        # Join candidates with scores
        query = db.table("candidates").select(
            """
            id, candidate_hash, snapshot,
            candidate_scores(eng_fit, bio_fit, safety_fit, evidence_fit),
            run_pareto_members(rank)
            """
        ).eq("run_id", run_id)
        
        if pareto_rank is not None:
            query = query.eq("run_pareto_members.rank", pareto_rank)
        
        result = query.range(offset, offset + limit - 1).execute()
        
        # Transform results
        items = []
        for c in (result.data or []):
            scores = c.get("candidate_scores", [{}])[0] if c.get("candidate_scores") else {}
            pareto = c.get("run_pareto_members", [{}])[0] if c.get("run_pareto_members") else {}
            snapshot = c.get("snapshot", {})
            
            items.append({
                "id": c["id"],
                "candidate_hash": c.get("candidate_hash", ""),
                "target_name": snapshot.get("target", {}).get("name"),
                "payload_name": snapshot.get("payload", {}).get("name"),
                "eng_fit": scores.get("eng_fit", 0),
                "bio_fit": scores.get("bio_fit", 0),
                "safety_fit": scores.get("safety_fit", 0),
                "evidence_fit": scores.get("evidence_fit", 0),
                "pareto_rank": pareto.get("rank")
            })
        
        # Sort
        reverse = sort_order == "desc"
        items.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        return {
            "items": items,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("list_candidates_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/candidates/{candidate_id}")
async def get_candidate(run_id: str, candidate_id: str, db=Depends(get_db)):
    """후보 상세 조회 (스코어 컴포넌트 포함)"""
    try:
        result = db.table("candidates").select(
            """
            *,
            candidate_scores(*),
            candidate_evidence(id, evidence_text, citations, conflict_alert),
            candidate_protocols(id, protocol_type, status)
            """
        ).eq("id", candidate_id).eq("run_id", run_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_candidate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, db=Depends(get_db)):
    """런 취소"""
    try:
        # 상태 확인
        result = db.table("design_runs").select("status").eq("id", run_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        current_status = result.data[0]["status"]
        
        if current_status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel run with status: {current_status}")
        
        # 취소
        db.table("design_runs").update({
            "status": "cancelled",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", run_id).execute()
        
        return {"status": "cancelled", "run_id": run_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("cancel_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{run_id}/rerun")
async def rerun(run_id: str, db=Depends(get_db)):
    """런 재실행 (동일 설정으로 새 런 생성)"""
    try:
        # 기존 런 조회
        result = db.table("design_runs").select("*").eq("id", run_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        original = result.data[0]
        
        # 새 런 생성
        new_run_id = str(uuid.uuid4())
        new_run = {
            "id": new_run_id,
            "workspace_id": original.get("workspace_id"),
            "target_ids": original.get("target_ids", []),
            "indication": original.get("indication", ""),
            "strategy": original.get("strategy", "balanced"),
            "constraints": original.get("constraints", {}),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.table("design_runs").insert(new_run).execute()
        
        # Job enqueue
        try:
            import redis
            import json
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url)
            job_data = json.dumps({
                "job": "design_run_execute",
                "run_id": new_run_id,
                "enqueue_time": datetime.utcnow().isoformat()
            })
            r.lpush("arq:queue:design_run_queue", job_data)
        except:
            pass
        
        return {
            "status": "pending",
            "run_id": new_run_id,
            "original_run_id": run_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("rerun_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/pareto")
async def get_pareto_fronts(run_id: str, db=Depends(get_db)):
    """런의 파레토 프론트 조회"""
    try:
        result = db.table("run_pareto_fronts").select(
            """
            *,
            run_pareto_members(candidate_id, rank, crowding_distance)
            """
        ).eq("run_id", run_id).order("front_index").execute()
        
        return {
            "run_id": run_id,
            "fronts": result.data or []
        }
        
    except Exception as e:
        logger.error("get_pareto_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
