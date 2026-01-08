"""
Open Targets Connector
Open Targets Platform GraphQL API 기반 Target-Disease 연관 수집

API 문서: https://platform-docs.opentargets.org/data-access/graphql-api
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
    RateLimiter,
)

logger = structlog.get_logger()


class OpenTargetsConnector(BaseConnector):
    """
    Open Targets Target-Disease 연관 수집 커넥터
    
    사용법:
        connector = OpenTargetsConnector(db_client)
        result = await connector.run(
            seed={"ensembl_ids": ["ENSG00000141736"]},  # ERBB2
            max_pages=10
        )
    """
    
    source = "opentargets"
    rate_limit_qps = 5.0  # Open Targets는 관대함
    max_retries = 3
    
    # Open Targets GraphQL endpoint
    API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
    
    def __init__(self, db_client=None):
        super().__init__(db_client)
    
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성
        
        seed 예시:
            {"ensembl_ids": ["ENSG00000141736", "ENSG00000146648"]}
            {"target_id": "ENSG00000141736"}
        """
        queries = []
        
        ensembl_ids = seed.get("ensembl_ids", [])
        target_id = seed.get("target_id")
        
        if target_id:
            ensembl_ids = [target_id]
        
        for eid in ensembl_ids:
            queries.append(QuerySpec(
                query=eid,
                params={"type": "associations"}
            ))
        
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """Open Targets에서 Target associations 조회"""
        
        ensembl_id = query.query
        page = cursor.position.get("page", 0)
        size = 25
        
        # GraphQL 쿼리
        graphql_query = """
        query TargetAssociations($ensemblId: String!, $page: Pagination) {
          target(ensemblId: $ensemblId) {
            id
            approvedSymbol
            approvedName
            biotype
            associatedDiseases(page: $page) {
              count
              rows {
                disease {
                  id
                  name
                  therapeuticAreas {
                    id
                    name
                  }
                }
                score
                datatypeScores {
                  id
                  score
                }
              }
            }
          }
        }
        """
        
        variables = {
            "ensemblId": ensembl_id,
            "page": {"index": page, "size": size}
        }
        
        self.logger.info("opentargets_request", ensembl_id=ensembl_id, page=page)
        
        import httpx
        
        await self.rate_limiter.acquire()
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_URL,
                json={"query": graphql_query, "variables": variables},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        
        data = response.json()
        
        # 에러 체크
        if "errors" in data:
            self.logger.warning("graphql_errors", errors=data["errors"])
            return FetchResult(records=[], has_more=False)
        
        target = data.get("data", {}).get("target")
        if not target:
            return FetchResult(records=[], has_more=False)
        
        associations = target.get("associatedDiseases", {})
        rows = associations.get("rows", [])
        total_count = associations.get("count", 0)
        
        # 결과에 target 정보 포함
        records = [{
            "target_id": target["id"],
            "target_symbol": target.get("approvedSymbol"),
            "target_name": target.get("approvedName"),
            "biotype": target.get("biotype"),
            "associations": rows
        }]
        
        # 다음 페이지 확인
        has_more = (page + 1) * size < total_count
        
        return FetchResult(
            records=records,
            has_more=has_more,
            next_cursor={"page": page + 1}
        )
    
    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """Open Targets 레코드 정규화"""
        
        target_id = record.get("target_id")
        if not target_id:
            return None
        
        associations = record.get("associations", [])
        
        # Top associations 추출 (score 기준)
        top_associations = []
        for assoc in sorted(associations, key=lambda x: x.get("score", 0), reverse=True)[:20]:
            disease = assoc.get("disease", {})
            top_associations.append({
                "disease_id": disease.get("id"),
                "disease_name": disease.get("name"),
                "score": assoc.get("score"),
                "therapeutic_areas": [
                    ta.get("name") for ta in disease.get("therapeuticAreas", [])
                ],
                "datatype_scores": {
                    ds.get("id"): ds.get("score") 
                    for ds in assoc.get("datatypeScores", [])
                }
            })
        
        data = {
            "ensembl_id": target_id,
            "target_symbol": record.get("target_symbol"),
            "target_name": record.get("target_name"),
            "biotype": record.get("biotype"),
            "associations": top_associations,
            "total_associations": len(associations)
        }
        
        checksum = NormalizedRecord.compute_checksum(data)
        
        return NormalizedRecord(
            external_id=target_id,
            record_type="target_association",
            data=data,
            checksum=checksum,
            source="opentargets"
        )
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """Open Targets 데이터를 target_profiles에 저장"""
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
                self.logger.warning("upsert_failed", ensembl_id=record.external_id, error=str(e))
        
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
        """target_profiles.associations 업데이트"""
        data = record.data
        ensembl_id = data["ensembl_id"]
        
        # 기존 프로필 확인
        existing = self.db.table("target_profiles").select(
            "id, associations"
        ).eq("ensembl_id", ensembl_id).execute()
        
        associations_data = {
            "opentargets": {
                "associations": data["associations"],
                "total_count": data["total_associations"],
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
        if existing.data:
            # 기존 associations와 병합
            current_assoc = existing.data[0].get("associations", {})
            current_assoc.update(associations_data)
            
            self.db.table("target_profiles").update({
                "associations": current_assoc,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("ensembl_id", ensembl_id).execute()
            
            return "updated"
        else:
            # 새 프로필 생성 (gene_symbol이 있으면)
            if data.get("target_symbol"):
                self.db.table("target_profiles").insert({
                    "ensembl_id": ensembl_id,
                    "gene_symbol": data["target_symbol"],
                    "protein_name": data.get("target_name"),
                    "associations": associations_data,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                return "inserted"
            
            return "unchanged"
