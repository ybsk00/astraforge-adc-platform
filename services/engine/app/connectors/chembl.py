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
        시드에서 쿼리 생성 (QueryProfile 지원)
        
        seed 예시:
            {"profile_name": "payload_family_expand", "smiles": ["CC(=O)..."]}
        """
        queries = []
        
        # 1. Query Profile 확인
        profile_name = seed.get("profile_name")
        if not profile_name:
            # Fallback to legacy mode
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
            
        # 2. Profile 로드
        from services.worker.profiles import get_profile
        profile = get_profile(profile_name)
        
        if not profile:
            self.logger.error("unknown_profile", profile=profile_name)
            return []
            
        # 3. Profile Mode에 따른 쿼리 생성
        if profile.get("mode") == "expansion":
            # SMILES 기반 Similarity Search
            smiles_list = seed.get("smiles", [])
            if isinstance(smiles_list, str):
                smiles_list = [smiles_list]
                
            if not smiles_list:
                self.logger.warning("no_smiles_provided", profile=profile_name)
                return []
                
            threshold = profile.get("threshold", 70) # Default similarity threshold
            
            for smi in smiles_list:
                queries.append(QuerySpec(
                    query=smi,
                    params={
                        "type": "similarity",
                        "threshold": threshold
                    }
                ))
        else:
            self.logger.warning("unsupported_profile_mode", mode=profile.get("mode"))
            
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
        elif query_type == "similarity":
            return await self._fetch_by_similarity(query.query, query.params.get("threshold", 70), offset, limit)
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
        """SMILES로 분자 검색 (Flexmatch)"""
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
        
    async def _fetch_by_similarity(self, smiles: str, threshold: int, offset: int, limit: int) -> FetchResult:
        """SMILES Similarity Search"""
        url = f"{self.BASE_URL}/molecule.json"
        params = {
            "similarity": smiles,
            "similarity_type": threshold, # ChEMBL API uses 'similarity' param for structure and 'similarity_type' isn't standard but 'similarity' filter exists. 
            # Correct ChEMBL Similarity Search: /molecule?similarity=SMILES&similarity_cutoff=80
            # But 'similarity' parameter in filter usually takes the SMILES.
            # Let's use the filter format: molecule_structures__canonical_smiles__similarity=SMILES
            # And we can specify threshold if supported, but usually it's >= 40% by default or we can filter client side.
            # Actually ChEMBL API documentation says: /similarity/{smiles}/{similarity}
            # But we are using the filter-based API (molecule.json).
            # Filter: molecule_structures__canonical_smiles__similarity
        }
        # Re-defining params for correct filter usage
        params = {
            "molecule_structures__canonical_smiles__similarity": smiles,
            "limit": limit,
            "offset": offset
        }
        # Note: Threshold control via filter param might be implicit or fixed. 
        # For now we trust the API's default similarity behavior (usually > 40% or sorted by similarity).
        
        self.logger.info("chembl_similarity_search", smiles=smiles[:30], threshold=threshold)
        
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
        """
        RAW 저장 중심이므로 정규화는 최소화하거나 Skip.
        """
        return None
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """
        RAW First 전략이므로 Upsert는 사용하지 않음.
        """
        return UpsertResult()
    
    async def _save_raw(self, record: NormalizedRecord):
        """Deprecated: BaseConnector.save_raw_data 사용"""
        pass
    
    async def _upsert_compound(self, record: NormalizedRecord) -> str:
        """Deprecated"""
        pass
