"""
Human Protein Atlas (HPA) Connector
HPA API 기반 조직/세포 발현 데이터 수집

API 문서: https://www.proteinatlas.org/about/download
"""
import os
from datetime import datetime
from typing import Any, Optional, Dict, List
import structlog

from app.connectors.base import (
    BaseConnector,
    QuerySpec,
    CursorState,
    FetchResult,
    NormalizedRecord,
    UpsertResult,
    fetch_with_retry,
)

logger = structlog.get_logger()


class HPAConnector(BaseConnector):
    """
    Human Protein Atlas 발현 데이터 수집 커넥터
    
    사용법:
        connector = HPAConnector(db_client)
        result = await connector.run(
            seed={"ensembl_ids": ["ENSG00000141736"]},  # ERBB2
            max_pages=1
        )
    """
    
    source = "hpa"
    rate_limit_qps = 5.0
    max_retries = 3
    
    # HPA API endpoint
    BASE_URL = "https://www.proteinatlas.org"
    
    def __init__(self, db_client=None):
        super().__init__(db_client)
    
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성
        
        seed 예시:
            {"ensembl_ids": ["ENSG00000141736"]}
            {"gene_symbols": ["ERBB2", "EGFR"]}
        """
        queries = []
        
        ensembl_ids = seed.get("ensembl_ids", [])
        gene_symbols = seed.get("gene_symbols", [])
        
        for eid in ensembl_ids:
            queries.append(QuerySpec(
                query=eid,
                params={"type": "ensembl"}
            ))
        
        for gene in gene_symbols:
            queries.append(QuerySpec(
                query=gene,
                params={"type": "gene"}
            ))
        
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """HPA에서 발현 데이터 조회"""
        
        identifier = query.query
        query_type = query.params.get("type", "gene")
        
        # HPA JSON endpoint
        url = f"{self.BASE_URL}/{identifier}.json"
        
        self.logger.info("hpa_request", identifier=identifier)
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            
            return FetchResult(
                records=[data] if data else [],
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                self.logger.warning("hpa_not_found", identifier=identifier)
                return FetchResult(records=[], has_more=False)
            raise
    
    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """HPA 레코드 정규화"""
        
        gene = record.get("Gene", "")
        ensembl = record.get("Ensembl", "")
        
        if not gene and not ensembl:
            return None
        
        # Tissue expression 추출
        tissue_expression = {}
        for tissue in record.get("Tissue expression", []):
            tissue_name = tissue.get("Tissue", "")
            if tissue_name:
                tissue_expression[tissue_name] = {
                    "level": tissue.get("Level", ""),
                    "reliability": tissue.get("Reliability", ""),
                }
        
        # RNA tissue specificity
        rna_specificity = record.get("RNA tissue specificity", "")
        
        # Subcellular location
        subcellular = []
        for loc in record.get("Subcellular location", []):
            if isinstance(loc, dict):
                subcellular.append(loc.get("Location", ""))
            else:
                subcellular.append(str(loc))
        
        # Blood expression
        blood_expression = {}
        for item in record.get("Blood expression", []):
            if isinstance(item, dict):
                cell_type = item.get("Cell type", "")
                if cell_type:
                    blood_expression[cell_type] = {
                        "level": item.get("Level", ""),
                        "tpm": item.get("TPM", 0)
                    }
        
        # Cancer expression (높은 발현 조직)
        cancer_expression = {}
        for cancer in record.get("Pathology", []):
            if isinstance(cancer, dict):
                cancer_name = cancer.get("Cancer", "")
                if cancer_name:
                    cancer_expression[cancer_name] = {
                        "high": cancer.get("High", 0),
                        "medium": cancer.get("Medium", 0),
                        "low": cancer.get("Low", 0),
                        "not_detected": cancer.get("Not detected", 0)
                    }
        
        data = {
            "gene_symbol": gene,
            "ensembl_id": ensembl,
            "protein_name": record.get("Protein name", ""),
            "tissue_expression": tissue_expression,
            "rna_specificity": rna_specificity,
            "subcellular_location": subcellular,
            "blood_expression": blood_expression,
            "cancer_expression": cancer_expression,
            "protein_class": record.get("Protein class", []),
        }
        
        checksum = NormalizedRecord.compute_checksum(data)
        
        return NormalizedRecord(
            external_id=ensembl or gene,
            record_type="expression",
            data=data,
            checksum=checksum,
            source="hpa"
        )
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """HPA 데이터를 target_profiles.expression에 저장"""
        if not self.db:
            return UpsertResult()
        
        result = UpsertResult()
        
        for record in records:
            try:
                await self._save_raw(record)
                upsert_status = await self._update_target_profile(record)
                
                if upsert_status == "inserted":
                    result.inserted += 1
                elif upsert_status == "updated":
                    result.updated += 1
                else:
                    result.unchanged += 1
                    
            except Exception as e:
                result.errors += 1
                self.logger.warning("upsert_failed", id=record.external_id, error=str(e))
        
        return result
    
    async def _save_raw(self, record: NormalizedRecord):
        """원본 데이터 저장"""
        try:
            self.db.table("raw_source_records").upsert({
                "source": record.source,
                "external_id": record.external_id,
                "payload": record.data,
                "checksum": record.checksum,
                "fetched_at": datetime.utcnow().isoformat(),
            }, on_conflict="source,external_id").execute()
        except Exception as e:
            self.logger.warning("raw_save_failed", error=str(e))
    
    async def _update_target_profile(self, record: NormalizedRecord) -> str:
        """target_profiles.expression 업데이트"""
        data = record.data
        ensembl_id = data.get("ensembl_id")
        gene_symbol = data.get("gene_symbol")
        
        # 기존 프로필 찾기 (ensembl 또는 gene_symbol로)
        existing = None
        if ensembl_id:
            existing = self.db.table("target_profiles").select(
                "id, expression"
            ).eq("ensembl_id", ensembl_id).execute()
        
        if not existing or not existing.data:
            if gene_symbol:
                existing = self.db.table("target_profiles").select(
                    "id, expression"
                ).eq("gene_symbol", gene_symbol).execute()
        
        expression_data = {
            "hpa": {
                "tissue_expression": data["tissue_expression"],
                "rna_specificity": data["rna_specificity"],
                "subcellular_location": data["subcellular_location"],
                "blood_expression": data["blood_expression"],
                "cancer_expression": data["cancer_expression"],
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
        if existing and existing.data:
            # 기존 expression과 병합
            current_expr = existing.data[0].get("expression", {})
            current_expr.update(expression_data)
            
            self.db.table("target_profiles").update({
                "expression": current_expr,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", existing.data[0]["id"]).execute()
            
            return "updated"
        else:
            # 새 프로필 생성
            if gene_symbol:
                self.db.table("target_profiles").insert({
                    "gene_symbol": gene_symbol,
                    "ensembl_id": ensembl_id,
                    "protein_name": data.get("protein_name"),
                    "expression": expression_data,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                return "inserted"
            
            return "unchanged"
