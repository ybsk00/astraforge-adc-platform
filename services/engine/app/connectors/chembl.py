"""
ChEMBL Connector
ChEMBL REST API 기반 화합물/활성 데이터 수집

API 문서: https://www.ebi.ac.uk/chembl/api/data/docs
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


class ChEMBLConnector(BaseConnector):
    """
    ChEMBL 화합물/활성 데이터 수집 커넥터
    
    사용법:
        connector = ChEMBLConnector(db_client)
        result = await connector.run(
            seed={"chembl_ids": ["CHEMBL1201583"]},  # T-DM1
            max_pages=5
        )
    """
    
    source = "chembl"
    rate_limit_qps = 5.0
    max_retries = 3
    
    # ChEMBL API endpoint
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    
    def __init__(self, db_client=None):
        super().__init__(db_client)
    
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성
        
        seed 예시:
            {"chembl_ids": ["CHEMBL1201583"]}
            {"smiles": "CC(=O)Nc1ccc(O)cc1"}
            {"search": "maytansine"}
        """
        queries = []
        
        chembl_ids = seed.get("chembl_ids", [])
        smiles = seed.get("smiles")
        search = seed.get("search")
        
        for cid in chembl_ids:
            queries.append(QuerySpec(
                query=cid,
                params={"type": "molecule"}
            ))
        
        if smiles:
            queries.append(QuerySpec(
                query=smiles,
                params={"type": "smiles"}
            ))
        
        if search:
            queries.append(QuerySpec(
                query=search,
                params={"type": "search"}
            ))
        
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """ChEMBL에서 데이터 조회"""
        
        query_type = query.params.get("type", "molecule")
        offset = cursor.position.get("offset", 0)
        limit = 20
        
        if query_type == "molecule":
            return await self._fetch_molecule(query.query)
        elif query_type == "smiles":
            return await self._fetch_by_smiles(query.query)
        else:
            return await self._search_molecules(query.query, offset, limit)
    
    async def _fetch_molecule(self, chembl_id: str) -> FetchResult:
        """ChEMBL ID로 분자 조회"""
        url = f"{self.BASE_URL}/molecule/{chembl_id}.json"
        
        self.logger.info("chembl_molecule_request", chembl_id=chembl_id)
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            
            # 활성 데이터도 함께 조회
            activities = await self._fetch_activities(chembl_id)
            data["activities_summary"] = activities
            
            return FetchResult(
                records=[data],
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                self.logger.warning("chembl_not_found", chembl_id=chembl_id)
                return FetchResult(records=[], has_more=False)
            raise
    
    async def _fetch_activities(self, chembl_id: str, limit: int = 50) -> Dict[str, Any]:
        """활성 데이터 조회"""
        url = f"{self.BASE_URL}/activity.json"
        params = {
            "molecule_chembl_id": chembl_id,
            "limit": limit
        }
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                params=params,
                max_retries=self.max_retries
            )
            
            data = response.json()
            activities = data.get("activities", [])
            
            # 활성 요약
            summary = {
                "total_activities": len(activities),
                "targets": {},
                "assay_types": {}
            }
            
            for act in activities:
                target = act.get("target_chembl_id", "unknown")
                assay_type = act.get("assay_type", "unknown")
                
                if target not in summary["targets"]:
                    summary["targets"][target] = {
                        "name": act.get("target_pref_name", ""),
                        "count": 0,
                        "activities": []
                    }
                
                summary["targets"][target]["count"] += 1
                
                if len(summary["targets"][target]["activities"]) < 5:
                    summary["targets"][target]["activities"].append({
                        "standard_type": act.get("standard_type"),
                        "standard_value": act.get("standard_value"),
                        "standard_units": act.get("standard_units"),
                        "pchembl_value": act.get("pchembl_value")
                    })
                
                summary["assay_types"][assay_type] = summary["assay_types"].get(assay_type, 0) + 1
            
            return summary
            
        except Exception:
            return {"total_activities": 0, "targets": {}, "assay_types": {}}
    
    async def _fetch_by_smiles(self, smiles: str) -> FetchResult:
        """SMILES로 분자 검색"""
        url = f"{self.BASE_URL}/molecule.json"
        params = {
            "molecule_structures__canonical_smiles__flexmatch": smiles,
            "limit": 5
        }
        
        self.logger.info("chembl_smiles_search", smiles=smiles[:30])
        
        response = await fetch_with_retry(
            url,
            rate_limiter=self.rate_limiter,
            params=params,
            max_retries=self.max_retries
        )
        
        data = response.json()
        molecules = data.get("molecules", [])
        
        return FetchResult(
            records=molecules,
            has_more=False
        )
    
    async def _search_molecules(self, query: str, offset: int, limit: int) -> FetchResult:
        """텍스트 검색"""
        url = f"{self.BASE_URL}/molecule/search.json"
        params = {
            "q": query,
            "limit": limit,
            "offset": offset
        }
        
        self.logger.info("chembl_search", query=query, offset=offset)
        
        response = await fetch_with_retry(
            url,
            rate_limiter=self.rate_limiter,
            params=params,
            max_retries=self.max_retries
        )
        
        data = response.json()
        molecules = data.get("molecules", [])
        total = data.get("page_meta", {}).get("total_count", 0)
        
        has_more = (offset + limit) < total
        
        return FetchResult(
            records=molecules,
            has_more=has_more,
            next_cursor={"offset": offset + limit}
        )
    
    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """ChEMBL 레코드 정규화"""
        
        chembl_id = record.get("molecule_chembl_id")
        if not chembl_id:
            return None
        
        structures = record.get("molecule_structures", {}) or {}
        properties = record.get("molecule_properties", {}) or {}
        
        data = {
            "chembl_id": chembl_id,
            "pref_name": record.get("pref_name"),
            "molecule_type": record.get("molecule_type"),
            "max_phase": record.get("max_phase"),
            "therapeutic_flag": record.get("therapeutic_flag"),
            "canonical_smiles": structures.get("canonical_smiles"),
            "standard_inchi": structures.get("standard_inchi"),
            "standard_inchi_key": structures.get("standard_inchi_key"),
            "properties": {
                "mw_freebase": properties.get("mw_freebase"),
                "alogp": properties.get("alogp"),
                "hba": properties.get("hba"),
                "hbd": properties.get("hbd"),
                "psa": properties.get("psa"),
                "rtb": properties.get("rtb"),
                "ro3_pass": properties.get("ro3_pass"),
                "num_ro5_violations": properties.get("num_ro5_violations"),
                "cx_logp": properties.get("cx_logp"),
                "aromatic_rings": properties.get("aromatic_rings"),
                "heavy_atoms": properties.get("heavy_atoms"),
            },
            "activities_summary": record.get("activities_summary", {}),
        }
        
        checksum = NormalizedRecord.compute_checksum(data)
        
        return NormalizedRecord(
            external_id=chembl_id,
            record_type="compound",
            data=data,
            checksum=checksum,
            source="chembl"
        )
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """ChEMBL 데이터를 compound_registry에 저장"""
        if not self.db:
            return UpsertResult()
        
        result = UpsertResult()
        
        for record in records:
            try:
                await self._save_raw(record)
                upsert_status = await self._upsert_compound(record)
                
                if upsert_status == "inserted":
                    result.inserted += 1
                    result.ids.append(record.external_id)
                elif upsert_status == "updated":
                    result.updated += 1
                else:
                    result.unchanged += 1
                    
            except Exception as e:
                result.errors += 1
                self.logger.warning("upsert_failed", chembl_id=record.external_id, error=str(e))
        
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
    
    async def _upsert_compound(self, record: NormalizedRecord) -> str:
        """compound_registry에 upsert"""
        data = record.data
        inchi_key = data.get("standard_inchi_key")
        chembl_id = data["chembl_id"]
        
        # 기존 항목 확인 (InChIKey 또는 ChEMBL ID)
        existing = None
        if inchi_key:
            existing = self.db.table("compound_registry").select("id, checksum").eq(
                "inchi_key", inchi_key
            ).execute()
        
        if not existing or not existing.data:
            existing = self.db.table("compound_registry").select("id, checksum").eq(
                "chembl_id", chembl_id
            ).execute()
        
        compound_data = {
            "chembl_id": chembl_id,
            "canonical_smiles": data.get("canonical_smiles"),
            "inchi_key": inchi_key,
            "synonyms": [data.get("pref_name")] if data.get("pref_name") else [],
            "activities": data.get("activities_summary", {}),
            "properties": data.get("properties", {}),
            "checksum": record.checksum,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if existing and existing.data:
            old_checksum = existing.data[0].get("checksum", "")
            if old_checksum == record.checksum:
                return "unchanged"
            
            self.db.table("compound_registry").update(compound_data).eq(
                "id", existing.data[0]["id"]
            ).execute()
            return "updated"
        else:
            compound_data["created_at"] = datetime.utcnow().isoformat()
            self.db.table("compound_registry").insert(compound_data).execute()
            return "inserted"
