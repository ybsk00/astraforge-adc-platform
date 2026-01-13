"""
PubChem Connector
PubChem PUG REST API 기반 화합물 구조/식별자 수집

API 문서: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
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


class PubChemConnector(BaseConnector):
    """
    PubChem 화합물 구조/식별자 수집 커넥터
    
    사용법:
        connector = PubChemConnector(db_client)
        result = await connector.run(
            seed={"inchi_keys": ["DTHNMHAUYICORS-KTKZVXAJSA-N"]},
            max_pages=1
        )
    """
    
    source = "pubchem"
    rate_limit_qps = 5.0  # PubChem: 5 req/sec
    max_retries = 3
    
    # PubChem PUG REST endpoints
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    def __init__(self, db_client=None):
        super().__init__(db_client)
    
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성 (QueryProfile 지원)
        
        seed 예시:
            {"profile_name": "payload_smiles_enrichment", "payloads": ["MMAE", "DXd"]}
        """
        queries = []
        
        # 1. Query Profile 확인
        profile_name = seed.get("profile_name")
        if not profile_name:
            # Fallback to legacy mode
            cids = seed.get("cids", [])
            inchi_keys = seed.get("inchi_keys", [])
            smiles_list = seed.get("smiles", [])
            names = seed.get("names", [])
            
            # Batch CIDs (최대 100개씩)
            for i in range(0, len(cids), 100):
                batch = cids[i:i+100]
                queries.append(QuerySpec(
                    query=",".join(map(str, batch)),
                    params={"type": "cid"}
                ))
            
            # InChIKey (개별)
            for key in inchi_keys:
                queries.append(QuerySpec(
                    query=key,
                    params={"type": "inchikey"}
                ))
            
            # SMILES
            if isinstance(smiles_list, str):
                smiles_list = [smiles_list]
            for smi in smiles_list:
                queries.append(QuerySpec(
                    query=smi,
                    params={"type": "smiles"}
                ))
            
            # Names
            for name in names:
                queries.append(QuerySpec(
                    query=name,
                    params={"type": "name"}
                ))
                
            return queries
            
        # 2. Profile 로드
        from services.worker.profiles import get_profile
        profile = get_profile(profile_name)
        
        if not profile:
            self.logger.error("unknown_profile", profile=profile_name)
            return []
            
        # 3. Profile Mode에 따른 쿼리 생성
        if profile.get("mode") == "enrichment":
            # Payload 이름으로 SMILES/물성 조회
            payloads = seed.get("payloads", [])
            if not payloads:
                self.logger.warning("no_payloads_provided", profile=profile_name)
                return []
                
            for payload in payloads:
                queries.append(QuerySpec(
                    query=payload,
                    params={"type": "name"}
                ))
        else:
            self.logger.warning("unsupported_profile_mode", mode=profile.get("mode"))
            
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """PubChem에서 데이터 조회"""
        
        query_type = query.params.get("type", "cid")
        
        if query_type == "cid":
            return await self._fetch_by_cid(query.query)
        elif query_type == "inchikey":
            return await self._fetch_by_inchikey(query.query)
        elif query_type == "smiles":
            return await self._fetch_by_smiles(query.query)
        else:
            return await self._fetch_by_name(query.query)
    
    async def _fetch_by_cid(self, cids: str) -> FetchResult:
        """CID로 조회"""
        url = f"{self.BASE_URL}/compound/cid/{cids}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
        
        self.logger.info("pubchem_cid_request", cids=cids[:50])
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [])
            
            return FetchResult(
                records=properties,
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                return FetchResult(records=[], has_more=False)
            raise
    
    async def _fetch_by_inchikey(self, inchikey: str) -> FetchResult:
        """InChIKey로 조회"""
        url = f"{self.BASE_URL}/compound/inchikey/{inchikey}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
        
        self.logger.info("pubchem_inchikey_request", inchikey=inchikey)
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [])
            
            return FetchResult(
                records=properties,
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                return FetchResult(records=[], has_more=False)
            raise
    
    async def _fetch_by_smiles(self, smiles: str) -> FetchResult:
        """SMILES로 조회"""
        import urllib.parse
        encoded_smiles = urllib.parse.quote(smiles, safe="")
        url = f"{self.BASE_URL}/compound/smiles/{encoded_smiles}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
        
        self.logger.info("pubchem_smiles_request", smiles=smiles[:30])
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [])
            
            return FetchResult(
                records=properties,
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                return FetchResult(records=[], has_more=False)
            raise
    
    async def _fetch_by_name(self, name: str) -> FetchResult:
        """이름으로 조회"""
        import urllib.parse
        encoded_name = urllib.parse.quote(name, safe="")
        url = f"{self.BASE_URL}/compound/name/{encoded_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
        
        self.logger.info("pubchem_name_request", name=name)
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=self.max_retries
            )
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [])
            
            # Synonyms도 가져오기
            if properties:
                cid = properties[0].get("CID")
                if cid:
                    synonyms = await self._fetch_synonyms(cid)
                    properties[0]["Synonyms"] = synonyms
            
            return FetchResult(
                records=properties,
                has_more=False
            )
            
        except Exception as e:
            if "404" in str(e):
                return FetchResult(records=[], has_more=False)
            raise
    
    async def _fetch_synonyms(self, cid: int, limit: int = 10) -> List[str]:
        """Synonyms 조회"""
        url = f"{self.BASE_URL}/compound/cid/{cid}/synonyms/JSON"
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                max_retries=2
            )
            
            data = response.json()
            info = data.get("InformationList", {}).get("Information", [])
            
            if info:
                return info[0].get("Synonym", [])[:limit]
            return []
            
        except Exception:
            return []
    
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
