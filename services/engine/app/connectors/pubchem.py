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
        시드에서 쿼리 생성
        
        seed 예시:
            {"cids": [2244, 2519]}  # Aspirin, Caffeine
            {"inchi_keys": ["DTHNMHAUYICORS-KTKZVXAJSA-N"]}
            {"smiles": "CC(=O)Nc1ccc(O)cc1"}  # Paracetamol
            {"names": ["aspirin", "maytansine"]}
        """
        queries = []
        
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
        """PubChem 레코드 정규화"""
        
        cid = record.get("CID")
        if not cid:
            return None
        
        data = {
            "pubchem_cid": str(cid),
            "molecular_formula": record.get("MolecularFormula"),
            "molecular_weight": record.get("MolecularWeight"),
            "canonical_smiles": record.get("CanonicalSMILES"),
            "isomeric_smiles": record.get("IsomericSMILES"),
            "inchi": record.get("InChI"),
            "inchi_key": record.get("InChIKey"),
            "iupac_name": record.get("IUPACName"),
            "synonyms": record.get("Synonyms", []),
            "properties": {
                "xlogp": record.get("XLogP"),
                "tpsa": record.get("TPSA"),
                "complexity": record.get("Complexity"),
                "hbd": record.get("HBondDonorCount"),
                "hba": record.get("HBondAcceptorCount"),
                "rotatable_bonds": record.get("RotatableBondCount"),
                "heavy_atoms": record.get("HeavyAtomCount"),
            }
        }
        
        checksum = NormalizedRecord.compute_checksum(data)
        
        return NormalizedRecord(
            external_id=str(cid),
            record_type="compound",
            data=data,
            checksum=checksum,
            source="pubchem"
        )
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """PubChem 데이터를 compound_registry에 저장"""
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
                self.logger.warning("upsert_failed", cid=record.external_id, error=str(e))
        
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
        inchi_key = data.get("inchi_key")
        pubchem_cid = data["pubchem_cid"]
        
        # 기존 항목 확인 (InChIKey 우선)
        existing = None
        if inchi_key:
            existing = self.db.table("compound_registry").select("id, checksum, pubchem_cid").eq(
                "inchi_key", inchi_key
            ).execute()
        
        if not existing or not existing.data:
            existing = self.db.table("compound_registry").select("id, checksum, pubchem_cid").eq(
                "pubchem_cid", pubchem_cid
            ).execute()
        
        compound_data = {
            "pubchem_cid": pubchem_cid,
            "canonical_smiles": data.get("canonical_smiles"),
            "inchi_key": inchi_key,
            "synonyms": data.get("synonyms", []),
            "properties": data.get("properties", {}),
            "checksum": record.checksum,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if existing and existing.data:
            old_checksum = existing.data[0].get("checksum", "")
            if old_checksum == record.checksum:
                return "unchanged"
            
            # PubChem CID 병합
            existing_data = existing.data[0]
            if not existing_data.get("pubchem_cid"):
                compound_data["pubchem_cid"] = pubchem_cid
            
            self.db.table("compound_registry").update(compound_data).eq(
                "id", existing.data[0]["id"]
            ).execute()
            return "updated"
        else:
            compound_data["created_at"] = datetime.utcnow().isoformat()
            self.db.table("compound_registry").insert(compound_data).execute()
            return "inserted"
