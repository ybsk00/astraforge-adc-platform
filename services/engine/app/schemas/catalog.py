"""
Catalog Schemas (Pydantic Models)
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime
from uuid import UUID


# === Component Types ===
ComponentType = Literal["target", "antibody", "linker", "payload", "conjugation"]
QualityGrade = Literal["gold", "silver", "bronze"]
ComponentStatus = Literal["pending_compute", "active", "failed", "deprecated"]


# === Request Schemas ===


class ComponentCreate(BaseModel):
    """컴포넌트 생성 요청"""

    type: ComponentType
    name: str = Field(..., min_length=1, max_length=255)
    properties: dict[str, Any] = Field(default_factory=dict)
    quality_grade: QualityGrade = "silver"

    class Config:
        json_schema_extra = {
            "example": {
                "type": "payload",
                "name": "MMAE",
                "properties": {
                    "smiles": "CC(C)C[C@H]1NC(=O)[C@H](CC(C)C)N(C)C(=O)...",
                    "mechanism": "tubulin_inhibitor",
                    "mw": 717.9,
                },
                "quality_grade": "gold",
            }
        }


class ComponentUpdate(BaseModel):
    """컴포넌트 수정 요청"""

    name: Optional[str] = None
    properties: Optional[dict[str, Any]] = None
    quality_grade: Optional[QualityGrade] = None
    status: Optional[ComponentStatus] = None


# === Response Schemas ===


class ComponentResponse(BaseModel):
    """컴포넌트 응답"""

    id: UUID
    workspace_id: Optional[UUID] = None
    type: ComponentType
    name: str
    properties: dict[str, Any]
    quality_grade: QualityGrade
    status: ComponentStatus
    compute_error: Optional[str] = None
    computed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ComponentListResponse(BaseModel):
    """컴포넌트 목록 응답"""

    items: list[ComponentResponse]
    total: int
    limit: int
    offset: int


# === RDKit 관련 스키마 ===


class RDKitDescriptors(BaseModel):
    """RDKit 계산 디스크립터"""

    mw: Optional[float] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    rot_bonds: Optional[int] = None
    rings: Optional[int] = None
    aromatic_rings: Optional[int] = None
