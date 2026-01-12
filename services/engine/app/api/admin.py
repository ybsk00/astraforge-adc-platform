from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_admin
import structlog

router = APIRouter(dependencies=[Depends(require_admin)])
logger = structlog.get_logger()

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
