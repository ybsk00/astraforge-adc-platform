"""
UniProt Connector
UniProt REST API 기반 Target 프로필 수집

API 문서: https://www.uniprot.org/help/api
"""

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


class UniProtConnector(BaseConnector):
    """
    UniProt Target 프로필 수집 커넥터

    사용법:
        connector = UniProtConnector(db_client)
        result = await connector.run(
            seed={"uniprot_ids": ["P04626", "P00533"]},  # HER2, EGFR
            max_pages=1
        )
    """

    source = "uniprot"
    rate_limit_qps = 5.0  # UniProt은 관대함
    max_retries = 3

    # UniProt REST API endpoints
    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    def __init__(self, db_client=None):
        super().__init__(db_client)

    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 UniProt 쿼리 생성

        seed 예시:
            {"uniprot_ids": ["P04626", "P00533"]}
            {"gene_symbols": ["ERBB2", "EGFR"], "organism": "human"}
        """
        queries = []

        # UniProt ID로 직접 조회
        uniprot_ids = seed.get("uniprot_ids", [])
        if uniprot_ids:
            for uid in uniprot_ids:
                queries.append(QuerySpec(query=uid, params={"type": "id"}))

        # Gene symbol로 검색
        gene_symbols = seed.get("gene_symbols", [])
        organism = seed.get("organism", "Homo sapiens")

        for gene in gene_symbols:
            query = f"gene:{gene} AND organism_name:{organism}"
            queries.append(QuerySpec(query=query, params={"type": "search"}))

        # 자유 검색 쿼리
        search_query = seed.get("query")
        if search_query:
            queries.append(QuerySpec(query=search_query, params={"type": "search"}))

        return queries

    async def fetch_page(self, query: QuerySpec, cursor: CursorState) -> FetchResult:
        """UniProt에서 데이터 조회"""

        query_type = query.params.get("type", "id")

        if query_type == "id":
            # 단일 ID 조회
            return await self._fetch_by_id(query.query)
        else:
            # 검색 쿼리
            return await self._fetch_by_search(query.query, cursor)

    async def _fetch_by_id(self, uniprot_id: str) -> FetchResult:
        """UniProt ID로 단일 엔트리 조회"""
        url = f"{self.BASE_URL}/{uniprot_id}"

        headers = {"Accept": "application/json"}

        self.logger.info("uniprot_fetch_id", uniprot_id=uniprot_id)

        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                headers=headers,
                max_retries=self.max_retries,
            )

            data = response.json()
            return FetchResult(records=[data], has_more=False)

        except Exception as e:
            if "404" in str(e):
                self.logger.warning("uniprot_not_found", uniprot_id=uniprot_id)
                return FetchResult(records=[], has_more=False)
            raise

    async def _fetch_by_search(self, query: str, cursor: CursorState) -> FetchResult:
        """UniProt 검색"""
        url = f"{self.BASE_URL}/search"

        params = {
            "query": query,
            "format": "json",
            "size": 25,  # 페이지 크기
        }

        # 커서가 있으면 사용
        next_link = cursor.position.get("next_link")
        if next_link:
            url = next_link
            params = {}

        headers = {"Accept": "application/json"}

        self.logger.info("uniprot_search", query=query)

        response = await fetch_with_retry(
            url,
            rate_limiter=self.rate_limiter,
            headers=headers,
            params=params if not next_link else None,
            max_retries=self.max_retries,
        )

        data = response.json()
        records = data.get("results", [])

        # 다음 페이지 링크 확인
        link_header = response.headers.get("Link", "")
        next_link = None
        if 'rel="next"' in link_header:
            # Link 헤더에서 next URL 추출
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    next_link = part.split(";")[0].strip().strip("<>")
                    break

        return FetchResult(
            records=records,
            has_more=bool(next_link),
            next_cursor={"next_link": next_link} if next_link else {},
        )

    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """UniProt 레코드 정규화"""
        # Primary accession
        accession = record.get("primaryAccession")
        if not accession:
            return None

        # Gene information
        genes = record.get("genes", [])
        gene_symbol = ""
        if genes:
            primary_gene = genes[0]
            gene_symbol = primary_gene.get("geneName", {}).get("value", "")

        # Protein name
        protein_desc = record.get("proteinDescription", {})
        recommended_name = protein_desc.get("recommendedName", {})
        protein_name = recommended_name.get("fullName", {}).get("value", "")

        if not protein_name:
            # Alternative: submittedName
            submitted = protein_desc.get("submittedName", [])
            if submitted:
                protein_name = submitted[0].get("fullName", {}).get("value", "")

        # Organism
        organism_obj = record.get("organism", {})
        organism = organism_obj.get("scientificName", "")

        # Function
        function_summary = ""
        comments = record.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    function_summary = texts[0].get("value", "")
                    break

        # Cross-references
        cross_refs = record.get("uniProtKBCrossReferences", [])
        external_refs = {}
        ensembl_id = ""

        for xref in cross_refs:
            db = xref.get("database", "")
            ref_id = xref.get("id", "")

            if db == "Ensembl":
                if not ensembl_id:
                    ensembl_id = ref_id
                external_refs.setdefault("ensembl", []).append(ref_id)
            elif db == "GeneID":
                external_refs["ncbi_gene"] = ref_id
            elif db == "HGNC":
                external_refs["hgnc"] = ref_id
            elif db == "PDB":
                external_refs.setdefault("pdb", []).append(ref_id)

        # Sequence
        sequence = record.get("sequence", {})
        seq_length = sequence.get("length", 0)
        seq_mass = sequence.get("molWeight", 0)

        data = {
            "uniprot_id": accession,
            "gene_symbol": gene_symbol,
            "ensembl_id": ensembl_id,
            "protein_name": protein_name,
            "organism": organism,
            "function_summary": function_summary,
            "external_refs": external_refs,
            "sequence_length": seq_length,
            "molecular_weight": seq_mass,
        }

        checksum = NormalizedRecord.compute_checksum(data)

        return NormalizedRecord(
            external_id=accession,
            record_type="target",
            data=data,
            checksum=checksum,
            source="uniprot",
        )

    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """UniProt 레코드를 DB에 저장"""
        if not self.db:
            self.logger.warning("no_db_client")
            return UpsertResult()

        result = UpsertResult()

        for record in records:
            try:
                # raw 저장
                await self._save_raw(record)

                # target_profiles 저장
                upsert_result = await self._upsert_target_profile(record)

                if upsert_result == "inserted":
                    result.inserted += 1
                    result.ids.append(record.external_id)
                elif upsert_result == "updated":
                    result.updated += 1
                else:
                    result.unchanged += 1

            except Exception as e:
                result.errors += 1
                self.logger.warning(
                    "upsert_failed", uniprot_id=record.external_id, error=str(e)
                )

        return result

    async def _save_raw(self, record: NormalizedRecord):
        """원본 데이터를 raw_source_records에 저장"""
        try:
            self.db.table("raw_source_records").upsert(
                {
                    "source": record.source,
                    "external_id": record.external_id,
                    "payload": record.data,
                    "checksum": record.checksum,
                    "fetched_at": datetime.utcnow().isoformat(),
                },
                on_conflict="source,external_id",
            ).execute()
        except Exception as e:
            self.logger.warning("raw_save_failed", error=str(e))

    async def _upsert_target_profile(self, record: NormalizedRecord) -> str:
        """target_profiles에 upsert"""
        data = record.data

        # 기존 프로필 확인
        existing = (
            self.db.table("target_profiles")
            .select("id, checksum")
            .eq("uniprot_id", data["uniprot_id"])
            .execute()
        )

        profile_data = {
            "uniprot_id": data["uniprot_id"],
            "gene_symbol": data.get("gene_symbol"),
            "ensembl_id": data.get("ensembl_id"),
            "protein_name": data.get("protein_name"),
            "organism": data.get("organism"),
            "function_summary": data.get("function_summary"),
            "external_refs": data.get("external_refs", {}),
            "checksum": record.checksum,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if existing.data:
            # 체크섬 비교
            old_checksum = existing.data[0].get("checksum", "")
            if old_checksum == record.checksum:
                return "unchanged"

            # 업데이트
            self.db.table("target_profiles").update(profile_data).eq(
                "uniprot_id", data["uniprot_id"]
            ).execute()
            return "updated"
        else:
            # 삽입
            profile_data["created_at"] = datetime.utcnow().isoformat()
            self.db.table("target_profiles").insert(profile_data).execute()
            return "inserted"


# ============================================================
# Target 카탈로그 연결 헬퍼
# ============================================================


async def link_target_to_catalog(db, uniprot_id: str, component_id: str):
    """
    target_profiles를 component_catalog와 연결

    Args:
        db: Supabase 클라이언트
        uniprot_id: UniProt ID
        component_id: component_catalog의 ID
    """
    db.table("target_profiles").update(
        {"component_id": component_id, "updated_at": datetime.utcnow().isoformat()}
    ).eq("uniprot_id", uniprot_id).execute()


async def enrich_targets_from_catalog(db, connector: UniProtConnector):
    """
    component_catalog의 target 타입 컴포넌트에서 UniProt 정보 보강

    target의 properties.uniprot_id가 있으면 UniProt에서 정보 가져와 프로필 생성
    """
    # Target 타입 컴포넌트 중 uniprot_id가 있는 것 조회
    result = (
        db.table("component_catalog")
        .select("id, name, properties")
        .eq("type", "target")
        .eq("status", "active")
        .execute()
    )

    uniprot_ids = []
    id_map = {}  # uniprot_id -> component_id

    for comp in result.data:
        props = comp.get("properties", {})
        uid = props.get("uniprot_id")
        if uid:
            uniprot_ids.append(uid)
            id_map[uid] = comp["id"]

    if not uniprot_ids:
        return {"status": "no_targets"}

    # UniProt에서 조회
    run_result = await connector.run(seed={"uniprot_ids": uniprot_ids}, max_pages=1)

    # 연결
    for uid in run_result.get("stats", {}).get("ids", []):
        if uid in id_map:
            await link_target_to_catalog(db, uid, id_map[uid])

    return run_result
