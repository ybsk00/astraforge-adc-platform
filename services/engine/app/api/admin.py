from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_admin
import structlog

from app.core.queue import enqueue_golden_seed_run
import uuid

router = APIRouter(dependencies=[Depends(require_admin)])
logger = structlog.get_logger()

@router.post("/golden/seed")
async def trigger_golden_seed(
    payload: Dict[str, Any],
    db=Depends(get_db)
):
    """
    Golden Seed 수집 트리거 (Target-Centric)
    
    Payload:
        targets: List[str] (예: ["HER2", "TROP2"])
        limit: int (Target 당 수집 개수, 기본 30)
    """
    try:
        run_id = str(uuid.uuid4())
        targets = payload.get("targets", [])
        limit = payload.get("limit", 30)
        
        config = {
            "targets": targets,
            "per_target_limit": limit,
            "mode": "target_only" # 강제 설정
        }
        
        job_id = await enqueue_golden_seed_run(run_id, config)
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to enqueue job")
            
        return {
            "status": "accepted",
            "run_id": run_id,
            "job_id": job_id,
            "message": f"Started collection for {len(targets)} targets"
        }
        
    except Exception as e:
        logger.error("trigger_golden_seed_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/golden/trend")
async def get_golden_trend(db=Depends(get_db)):
    """
    Golden Set 검증 트렌드 데이터 조회 (Real DB)
    """
    try:
        # 1. 최근 검증 실행 내역 조회
        runs_res = db.table("golden_validation_runs")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        if not runs_res.data:
            return {"items": []}
            
        run_ids = [r["id"] for r in runs_res.data]
        
        # 2. 상세 지표 조회
        metrics_res = db.table("golden_validation_metrics")\
            .select("*")\
            .in_("run_id", run_ids)\
            .execute()
            
        # 3. 데이터 가공 (run_id별로 metrics 그룹화)
        metrics_map = {}
        for m in metrics_res.data:
            rid = m["run_id"]
            axis = m["axis"] or "overall"
            if rid not in metrics_map:
                metrics_map[rid] = {}
            if axis not in metrics_map[rid]:
                metrics_map[rid][axis] = {}
            
            # MAE, Spearman 등 주요 지표 추출
            metrics_map[rid][axis][m["metric"]] = m["value"]

        # 4. 최종 결과 조립
        items = []
        for r in runs_res.data:
            rid = r["id"]
            run_metrics = metrics_map.get(rid, {})
            # 하위 호환성을 위한 summary (overall 기준)
            summary = run_metrics.get("overall", {})
            
            items.append({
                "id": rid,
                "created_at": r["created_at"],
                "pass": r["pass"],
                "scoring_version": r["scoring_version"],
                "dataset_version": r.get("dataset_version", "v1.0"),
                "metrics": run_metrics,
                "summary": summary
            })
            
        return {"items": items}
        
    except Exception as e:
        logger.error("get_golden_trend_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch golden trend data")
