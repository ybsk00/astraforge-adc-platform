"""
Evidence API Endpoints
문헌 검색 및 근거 품질 관리
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import structlog
from datetime import datetime

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()

# === Schemas ===


class EvidenceSearchResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    journal: str
    year: int
    abstract: str
    pmid: Optional[str] = None
    doi: Optional[str] = None
    relevance_score: float


class QualityIssueResponse(BaseModel):
    id: str
    type: str  # 'conflict', 'outdated', 'retracted'
    description: str
    severity: str  # 'high', 'medium', 'low'
    status: str  # 'open', 'resolved', 'ignored'
    evidence_id: str
    created_at: str


# === Endpoints ===


@router.get("/search", response_model=dict)
async def search_evidence(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(
        None, description="Filter by source (e.g., pubmed, patent)"
    ),
    db=Depends(get_db),
):
    """
    문헌 검색 API (Vector Search)
    """
    from app.core.ai import get_embedding

    # 1. Query Embedding
    embedding = await get_embedding(q)

    if not embedding:
        # Fallback to simple text search if embedding fails
        # or return empty if strict
        logger.warning("embedding_failed_fallback_text", query=q)
        # TODO: Implement text search fallback
        return {"results": [], "total": 0, "limit": limit, "offset": offset}

    # 2. Vector Search via RPC
    try:
        params = {
            "query_embedding": embedding,
            "match_threshold": 0.5,  # Adjust threshold
            "match_count": limit,
        }
        result = db.rpc("match_literature_chunks", params).execute()

        items = []
        for row in result.data or []:
            items.append(
                {
                    "id": row.get("document_id"),  # Use doc ID as main ID
                    "chunk_id": row.get("id"),
                    "title": row.get("document_title"),
                    "authors": row.get("document_authors") or [],
                    "journal": "Unknown",  # RPC didn't return journal, maybe add later
                    "year": int(row.get("document_year")[:4])
                    if row.get("document_year")
                    else None,
                    "abstract": row.get(
                        "content"
                    ),  # Showing chunk content as abstract/snippet
                    "relevance_score": row.get("similarity"),
                }
            )

        return {
            "results": items,
            "total": len(items),  # Approximation
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error("vector_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/issues", response_model=List[QualityIssueResponse])
async def get_quality_issues(
    status: Optional[str] = Query(None, description="Filter by status"),
    db=Depends(get_db),
):
    """
    근거 품질 이슈 목록 조회
    """
    try:
        query = db.table("quality_issues").select("*").order("created_at", desc=True)

        if status:
            query = query.eq("status", status)

        result = query.execute()

        return [
            QualityIssueResponse(
                id=item["id"],
                type=item["type"],
                description=item["description"],
                severity=item["severity"],
                status=item["status"],
                evidence_id=item.get("evidence_id") or "",
                created_at=item["created_at"],
            )
            for item in result.data or []
        ]
    except Exception as e:
        logger.error("get_quality_issues_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/resolve")
async def resolve_issue(
    issue_id: str,
    resolution: str,
    user_id: str = "system",  # In real app, get from auth context
    db=Depends(get_db),
):
    """
    품질 이슈 해결 처리
    """
    try:
        # 1. Check if issue exists
        result = db.table("quality_issues").select("*").eq("id", issue_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Issue not found")

        # 2. Update status
        update_data = {
            "status": "resolved",
            "updated_at": datetime.utcnow().isoformat(),
        }

        db.table("quality_issues").update(update_data).eq("id", issue_id).execute()

        return {"status": "resolved", "issue_id": issue_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_issue_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
