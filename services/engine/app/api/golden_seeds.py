"""
Golden Seed Items API Endpoints
True Golden Set 관리 (근거/추적성/게이트 체크)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
import structlog
from datetime import datetime
from enum import Enum

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


# === Enums ===
class PlatformAxis(str, Enum):
    VEDOTIN_MMAE = "VEDOTIN_MMAE"
    DXD = "DXD"
    OPTIDC_KELUN = "OPTIDC_KELUN"
    INDEPENDENT = "INDEPENDENT"


class EvidenceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class CurationLevel(str, Enum):
    DRAFT = "Draft"
    MANUAL = "Manual"
    REVIEW = "Review"
    FINAL = "Final"


class EvidenceType(str, Enum):
    CLINICALTRIALS = "clinicaltrials"
    PAPER = "paper"
    PATENT = "patent"
    LABEL = "label"
    PRESS = "press"
    OTHER = "other"


# === Schemas ===
class EvidenceItemCreate(BaseModel):
    type: EvidenceType
    id_or_url: Optional[str] = None
    title: Optional[str] = None
    published_date: Optional[str] = None
    snippet: Optional[str] = None
    source_quality: Optional[str] = "standard"


class EvidenceItemResponse(BaseModel):
    id: str
    type: str
    id_or_url: Optional[str]
    title: Optional[str]
    published_date: Optional[str]
    snippet: Optional[str]
    source_quality: Optional[str]
    created_at: str


class FieldProvenanceCreate(BaseModel):
    field_name: str
    field_value: Optional[str] = None
    evidence_item_id: Optional[str] = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    quote_span: Optional[str] = None
    source_chunk_id: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    note: Optional[str] = None


class FieldProvenanceResponse(BaseModel):
    id: str
    field_name: str
    field_value: Optional[str]
    evidence_item_id: Optional[str]
    confidence: float
    quote_span: Optional[str]
    created_at: str


class GateCheckResult(BaseModel):
    passed: bool
    score: int
    max_score: int
    checks: dict


# === Evidence Grade Mapping ===
EVIDENCE_GRADE_SCORES = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "F": 1,
}


# === Gate Checker ===
def check_gate_conditions(seed: dict) -> GateCheckResult:
    """
    Gate Checklist 검사
    1. Axis Assigned
    2. Target Resolved
    3. Construct Ready (payload_family, linker_type, conjugation_method)
    4. Evidence >= 2 (별도 조회 필요)
    5. Evidence Grade >= B
    6. Outcome Consistent
    """
    checks = {}
    score = 0
    max_score = 6

    # 1. Axis Assigned
    checks["axis_assigned"] = bool(seed.get("platform_axis"))
    if checks["axis_assigned"]:
        score += 1

    # 2. Target Resolved
    checks["target_resolved"] = bool(
        seed.get("resolved_target_symbol") or seed.get("target")
    )
    if checks["target_resolved"]:
        score += 1

    # 3. Construct Ready
    payload_ok = bool(seed.get("payload_family"))
    linker_ok = bool(seed.get("linker_type"))
    conj_ok = bool(seed.get("conjugation_method"))
    checks["construct_ready"] = payload_ok and linker_ok and conj_ok
    checks["construct_details"] = {
        "payload_family": payload_ok,
        "linker_type": linker_ok,
        "conjugation_method": conj_ok,
    }
    if checks["construct_ready"]:
        score += 1

    # 4. Evidence >= 2 (count from evidence_refs or evidence_items)
    evidence_refs = seed.get("evidence_refs") or []
    evidence_count = len(evidence_refs) if isinstance(evidence_refs, list) else 0
    checks["evidence_count"] = evidence_count
    checks["evidence_sufficient"] = evidence_count >= 2
    if checks["evidence_sufficient"]:
        score += 1

    # 5. Evidence Grade >= B
    grade = seed.get("evidence_grade") or "F"
    grade_score = EVIDENCE_GRADE_SCORES.get(grade, 1)
    checks["evidence_grade"] = grade
    checks["evidence_grade_ok"] = grade_score >= 4  # B 이상
    if checks["evidence_grade_ok"]:
        score += 1

    # 6. Outcome Consistent
    outcome = seed.get("outcome")
    program_status = seed.get("program_status")
    # Success 이면서 Discontinued면 불일치
    # Fail 이면서 failure_mode가 없으면 불일치
    outcome_ok = True
    if outcome == "Success" and program_status == "Discontinued":
        outcome_ok = False
    if outcome == "Fail" and not seed.get("failure_mode"):
        outcome_ok = False
    checks["outcome_consistent"] = outcome_ok
    if outcome_ok:
        score += 1

    return GateCheckResult(
        passed=score >= 5,  # 최소 5/6 통과 필요
        score=score,
        max_score=max_score,
        checks=checks,
    )


# === Endpoints ===


@router.get("/{seed_id}")
async def get_golden_seed(
    seed_id: str,
    db=Depends(get_db),
):
    """
    Golden Seed Item 조회
    """
    try:
        result = (
            db.table("golden_seed_items").select("*").eq("id", seed_id).execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Seed not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_golden_seed_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed_id}/gate-check")
async def check_gate(
    seed_id: str,
    db=Depends(get_db),
):
    """
    Gate Checklist 검사
    """
    try:
        # 1. Fetch seed
        result = (
            db.table("golden_seed_items").select("*").eq("id", seed_id).execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Seed not found")

        seed = result.data[0]

        # 2. Fetch evidence count
        ev_result = (
            db.table("evidence_items")
            .select("id")
            .eq("golden_seed_item_id", seed_id)
            .execute()
        )
        evidence_count = len(ev_result.data) if ev_result.data else 0

        # Update seed with evidence count for gate check
        seed["_evidence_count"] = evidence_count

        # 3. Run gate check
        gate_result = check_gate_conditions(seed)

        # Update evidence count in result
        gate_result.checks["evidence_count"] = evidence_count
        gate_result.checks["evidence_sufficient"] = evidence_count >= 2

        return gate_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("gate_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Evidence Endpoints ===


@router.post("/{seed_id}/evidence")
async def add_evidence(
    seed_id: str,
    evidence: EvidenceItemCreate,
    db=Depends(get_db),
):
    """
    근거 추가
    """
    try:
        # Check if seed exists
        seed_result = (
            db.table("golden_seed_items").select("id").eq("id", seed_id).execute()
        )
        if not seed_result.data:
            raise HTTPException(status_code=404, detail="Seed not found")

        # Insert evidence
        data = {
            "golden_seed_item_id": seed_id,
            "type": evidence.type.value,
            "id_or_url": evidence.id_or_url,
            "title": evidence.title,
            "published_date": evidence.published_date,
            "snippet": evidence.snippet,
            "source_quality": evidence.source_quality,
        }
        result = db.table("evidence_items").insert(data).execute()

        return {"status": "created", "id": result.data[0]["id"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_evidence_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed_id}/evidence")
async def get_evidence_list(
    seed_id: str,
    db=Depends(get_db),
):
    """
    근거 목록 조회
    """
    try:
        result = (
            db.table("evidence_items")
            .select("*")
            .eq("golden_seed_item_id", seed_id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"items": result.data or [], "total": len(result.data or [])}

    except Exception as e:
        logger.error("get_evidence_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Provenance Endpoints ===


@router.post("/{seed_id}/provenance")
async def add_provenance(
    seed_id: str,
    provenance: FieldProvenanceCreate,
    db=Depends(get_db),
):
    """
    필드 추적성 추가
    """
    try:
        data = {
            "golden_seed_item_id": seed_id,
            "field_name": provenance.field_name,
            "field_value": provenance.field_value,
            "evidence_item_id": provenance.evidence_item_id,
            "confidence": provenance.confidence,
            "quote_span": provenance.quote_span,
            "source_chunk_id": provenance.source_chunk_id,
            "char_start": provenance.char_start,
            "char_end": provenance.char_end,
            "note": provenance.note,
        }
        result = db.table("field_provenance").insert(data).execute()

        return {"status": "created", "id": result.data[0]["id"]}

    except Exception as e:
        logger.error("add_provenance_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed_id}/provenance")
async def get_provenance_list(
    seed_id: str,
    field_name: Optional[str] = Query(None),
    db=Depends(get_db),
):
    """
    필드 추적성 조회
    """
    try:
        query = (
            db.table("field_provenance")
            .select("*")
            .eq("golden_seed_item_id", seed_id)
        )

        if field_name:
            query = query.eq("field_name", field_name)

        result = query.order("created_at", desc=True).execute()
        return {"items": result.data or [], "total": len(result.data or [])}

    except Exception as e:
        logger.error("get_provenance_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === Approve High Confidence ===


@router.post("/{seed_id}/approve-high-confidence")
async def approve_high_confidence(
    seed_id: str,
    threshold: float = Query(0.9, ge=0.5, le=1.0),
    db=Depends(get_db),
):
    """
    고신뢰도 필드 일괄 승인
    confidence >= threshold 인 provenance의 값을 seed에 반영
    """
    try:
        # 1. Get high confidence provenance
        prov_result = (
            db.table("field_provenance")
            .select("*")
            .eq("golden_seed_item_id", seed_id)
            .gte("confidence", threshold)
            .execute()
        )

        if not prov_result.data:
            return {"status": "no_changes", "approved_count": 0}

        # 2. Build update data
        update_data = {}
        approved_fields = []
        for prov in prov_result.data:
            field_name = prov["field_name"]
            field_value = prov["field_value"]
            if field_name and field_value:
                update_data[field_name] = field_value
                approved_fields.append(field_name)

        if not update_data:
            return {"status": "no_changes", "approved_count": 0}

        # 3. Update seed
        update_data["updated_at"] = datetime.utcnow().isoformat()
        db.table("golden_seed_items").update(update_data).eq(
            "id", seed_id
        ).execute()

        return {
            "status": "approved",
            "approved_count": len(approved_fields),
            "approved_fields": approved_fields,
        }

    except Exception as e:
        logger.error("approve_high_confidence_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
