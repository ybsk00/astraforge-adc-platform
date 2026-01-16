"""
Reports API Endpoints
설계 결과 리포트 생성 및 관리
"""

from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel
import structlog
from datetime import datetime
import uuid

router = APIRouter()
logger = structlog.get_logger()

# === Schemas ===


class ReportGenerateRequest(BaseModel):
    run_id: str
    scope: str = "top_10"  # top_10, top_20, selected
    format: str = "pdf"  # pdf, html
    sections: List[str] = ["evidence", "protocol", "score"]


class ReportResponse(BaseModel):
    id: str
    run_id: str
    filename: str
    format: str
    status: str
    created_at: str
    download_url: Optional[str] = None


# === Endpoints ===


@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: ReportGenerateRequest):
    """
    리포트 생성 요청
    """
    # TODO: 실제 리포트 생성 로직 (PDF/HTML) 구현 필요
    # 현재는 Mock 응답

    report_id = str(uuid.uuid4())
    filename = f"report_{request.run_id}_{request.scope}.{request.format}"

    return {
        "id": report_id,
        "run_id": request.run_id,
        "filename": filename,
        "format": request.format,
        "status": "generating",
        "created_at": datetime.utcnow().isoformat(),
        "download_url": None,
    }


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
):
    """
    리포트 목록 조회
    """
    # TODO: DB 연동
    return [
        {
            "id": "rep_001",
            "run_id": run_id or "run_123",
            "filename": "report_run_123_top_10.pdf",
            "format": "pdf",
            "status": "ready",
            "created_at": datetime.utcnow().isoformat(),
            "download_url": "/downloads/rep_001",
        }
    ]
