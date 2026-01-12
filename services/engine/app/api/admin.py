from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import random

router = APIRouter()

class ValidationSummary(BaseModel):
    MAE: float
    Spearman: float
    TopKOverlap: float

class ValidationRun(BaseModel):
    id: str
    created_at: str
    pass_status: bool  # 'pass' is a reserved keyword in Python, using pass_status
    scoring_version: str
    summary: ValidationSummary

class TrendResponse(BaseModel):
    items: List[Dict[str, Any]]

@router.get("/golden/trend")
async def get_golden_trend():
    """
    Golden Set 검증 트렌드 데이터 조회
    현재는 시각화를 위한 Mock 데이터를 반환합니다.
    """
    # 실제 구현 시에는 DB의 validation_runs 테이블 등에서 조회
    items = []
    base_date = datetime.utcnow() - timedelta(days=10)
    
    for i in range(10):
        date = (base_date + timedelta(days=i)).isoformat()
        items.append({
            "id": f"run-{i}",
            "created_at": date,
            "pass": True if random.random() > 0.2 else False,
            "scoring_version": "v1.2.0",
            "summary": {
                "MAE": 0.5 - (i * 0.02) + (random.random() * 0.05),
                "Spearman": 0.7 + (i * 0.01) + (random.random() * 0.05),
                "TopKOverlap": 0.6 + (i * 0.015)
            }
        })
    
    return {"items": items}
