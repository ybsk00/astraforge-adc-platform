"""
PubMed Connector
NCBI E-utilities 기반 문헌 수집

API 문서: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""

import os
from datetime import datetime
from typing import Any, Optional, Dict, List
import xmltodict
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


class PubMedConnector(BaseConnector):
    """
    PubMed 문헌 수집 커넥터

    사용법:
        connector = PubMedConnector(db_client)
        result = await connector.run(
            seed={"query": "ADC antibody drug conjugate"},
            max_pages=10
        )
    """

    source = "pubmed"
    rate_limit_qps = 3.0  # NCBI API Key 없이 3 req/sec, 있으면 10 req/sec
    max_retries = 3

    # NCBI E-utilities endpoints
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, db_client=None):
        super().__init__(db_client)

        # 환경 변수에서 NCBI 설정 로드
        self.api_key = os.getenv("NCBI_API_KEY", "")
        self.email = os.getenv("NCBI_EMAIL", "adc_platform@example.com")
        self.tool = os.getenv("NCBI_TOOL", "adc_platform")

        # API Key 있으면 rate limit 증가
        if self.api_key:
            self.rate_limit_qps = 10.0
            self.rate_limiter.interval = 1.0 / 10.0

    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 PubMed 쿼리 생성 (QueryProfile 지원)

        seed 예시:
            {"profile_name": "payload_discovery", "targets": ["HER2"]}
            {"profile_name": "tox_risk", "payloads": ["MMAE"]}
        """
        queries = []

        # 1. Query Profile 확인
        profile_name = seed.get("profile_name")
        if not profile_name:
            # Fallback to legacy mode
            query = seed.get("query", "")
            if query:
                return [
                    QuerySpec(query=query, params={"retmax": seed.get("retmax", 100)})
                ]
            return []

        # 2. Profile 로드
        from services.worker.profiles import get_profile

        profile = get_profile(profile_name)

        if not profile:
            self.logger.error("unknown_profile", profile=profile_name)
            return []

        # 3. Parameter 기반 쿼리 생성
        # Profile Mode에 따라 필요한 파라미터가 다름

        if profile.get("mode") == "discovery":
            # Target 기반 Discovery (Payload, Linker)
            targets = seed.get("targets", [])
            if not targets:
                self.logger.warning("no_targets_provided", profile=profile_name)
                return []

            for target in targets:
                query_str = profile["query_template"].format(target=target)
                queries.append(
                    QuerySpec(
                        query=query_str,
                        params={"retmax": seed.get("retmax", 100), "target": target},
                    )
                )

        elif profile.get("mode") == "risk":
            # Payload 기반 Risk Check
            payloads = seed.get("payloads", [])
            if not payloads:
                self.logger.warning("no_payloads_provided", profile=profile_name)
                return []

            for payload in payloads:
                query_str = profile["query_template"].format(payload=payload)
                queries.append(
                    QuerySpec(
                        query=query_str,
                        params={"retmax": seed.get("retmax", 100), "payload": payload},
                    )
                )

        else:
            self.logger.warning("unsupported_profile_mode", mode=profile.get("mode"))

        return queries

    async def fetch_page(self, query: QuerySpec, cursor: CursorState) -> FetchResult:
        """
        PubMed에서 한 페이지 조회
        """
        retstart = cursor.position.get("retstart", 0)
        retmax = query.params.get("retmax", 100)

        # 1. ESearch - PMID 목록 조회
        esearch_params = {
            "db": "pubmed",
            "term": query.query,
            "retmode": "json",
            "retstart": retstart,
            "retmax": retmax,
            "usehistory": "y",
            "email": self.email,
            "tool": self.tool,
        }

        if self.api_key:
            esearch_params["api_key"] = self.api_key

        if query.params.get("mindate"):
            esearch_params["mindate"] = query.params["mindate"]
        if query.params.get("maxdate"):
            esearch_params["maxdate"] = query.params["maxdate"]
        esearch_params["datetype"] = "pdat"  # publication date

        self.logger.info("esearch_request", query=query.query, retstart=retstart)

        response = await fetch_with_retry(
            self.ESEARCH_URL,
            rate_limiter=self.rate_limiter,
            params=esearch_params,
            max_retries=self.max_retries,
        )

        search_result = response.json()
        esearch = search_result.get("esearchresult", {})

        pmids = esearch.get("idlist", [])
        total_count = int(esearch.get("count", 0))
        webenv = esearch.get("webenv", "")
        query_key = esearch.get("querykey", "")

        self.logger.info(
            "esearch_result", pmids_count=len(pmids), total_count=total_count
        )

        if not pmids:
            return FetchResult(records=[], has_more=False, next_cursor={})

        # 2. EFetch - 상세 정보 조회
        efetch_params = {
            "db": "pubmed",
            "retmode": "xml",
            "rettype": "abstract",
            "email": self.email,
            "tool": self.tool,
        }

        if self.api_key:
            efetch_params["api_key"] = self.api_key

        # WebEnv 사용 가능하면 사용 (더 효율적)
        if webenv and query_key:
            efetch_params["WebEnv"] = webenv
            efetch_params["query_key"] = query_key
            efetch_params["retstart"] = 0
            efetch_params["retmax"] = len(pmids)
        else:
            efetch_params["id"] = ",".join(pmids)

        response = await fetch_with_retry(
            self.EFETCH_URL,
            rate_limiter=self.rate_limiter,
            params=efetch_params,
            max_retries=self.max_retries,
        )

        # XML 파싱
        articles = self._parse_pubmed_xml(response.text)

        # 다음 페이지 여부 확인
        has_more = (retstart + len(pmids)) < total_count

        return FetchResult(
            records=articles,
            has_more=has_more,
            next_cursor={
                "retstart": retstart + retmax,
                "webenv": webenv,
                "query_key": query_key,
                "total_count": total_count,
            },
        )

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """PubMed XML 파싱"""
        try:
            data = xmltodict.parse(xml_text)
        except Exception as e:
            self.logger.error("xml_parse_failed", error=str(e))
            return []

        articles = []
        pubmed_set = data.get("PubmedArticleSet", {})
        pubmed_articles = pubmed_set.get("PubmedArticle", [])

        # 단일 결과인 경우 리스트로 변환
        if isinstance(pubmed_articles, dict):
            pubmed_articles = [pubmed_articles]

        for article in pubmed_articles:
            try:
                parsed = self._parse_article(article)
                if parsed:
                    articles.append(parsed)
            except Exception as e:
                self.logger.warning("article_parse_failed", error=str(e))

        return articles

    def _parse_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """단일 PubMed article 파싱"""
        medline = article.get("MedlineCitation", {})
        article_data = medline.get("Article", {})

        # PMID
        pmid_obj = medline.get("PMID", {})
        pmid = pmid_obj if isinstance(pmid_obj, str) else pmid_obj.get("#text", "")

        if not pmid:
            return None

        # Title
        title = article_data.get("ArticleTitle", "")
        if isinstance(title, dict):
            title = title.get("#text", "")

        # Abstract
        abstract_obj = article_data.get("Abstract", {})
        abstract_texts = abstract_obj.get("AbstractText", [])

        if isinstance(abstract_texts, str):
            abstract = abstract_texts
        elif isinstance(abstract_texts, dict):
            abstract = abstract_texts.get("#text", "")
        elif isinstance(abstract_texts, list):
            # Structured abstract인 경우
            parts = []
            for part in abstract_texts:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    label = part.get("@Label", "")
                    text = part.get("#text", "")
                    if label:
                        parts.append(f"{label}: {text}")
                    else:
                        parts.append(text)
            abstract = " ".join(parts)
        else:
            abstract = ""

        # Authors
        author_list = article_data.get("AuthorList", {}).get("Author", [])
        if isinstance(author_list, dict):
            author_list = [author_list]

        authors = []
        for author in author_list:
            if isinstance(author, dict):
                lastname = author.get("LastName", "")
                forename = author.get("ForeName", "")
                if lastname:
                    authors.append({"lastname": lastname, "forename": forename})

        # Journal
        journal_obj = article_data.get("Journal", {})
        journal = journal_obj.get("Title", "")
        if not journal:
            journal = journal_obj.get("ISOAbbreviation", "")

        # Publication date
        pub_date_obj = journal_obj.get("JournalIssue", {}).get("PubDate", {})
        year = pub_date_obj.get("Year", "")
        month = pub_date_obj.get("Month", "01")
        day = pub_date_obj.get("Day", "01")

        # Month 이름을 숫자로 변환
        month_map = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        if month in month_map:
            month = month_map[month]

        publication_date = None
        if year:
            try:
                publication_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except Exception:
                publication_date = f"{year}-01-01"

        # DOI
        doi = ""
        article_ids = (
            article.get("PubmedData", {}).get("ArticleIdList", {}).get("ArticleId", [])
        )

        if isinstance(article_ids, dict):
            article_ids = [article_ids]
        for aid in article_ids:
            if isinstance(aid, dict) and aid.get("@IdType") == "doi":
                doi = aid.get("#text", "")
                break

        return {
            "pmid": pmid,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "publication_date": publication_date,
        }

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

    async def _upsert_document(self, record: NormalizedRecord) -> str:
        """Deprecated"""
        pass


# ============================================================
# 증분 수집용 헬퍼 함수
# ============================================================


async def get_pubmed_cursor(db, query_hash: str) -> Optional[Dict[str, Any]]:
    """저장된 커서 조회"""
    result = (
        db.table("ingestion_cursors")
        .select("*")
        .eq("source", "pubmed")
        .eq("query_hash", query_hash)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


async def save_pubmed_cursor(
    db,
    query_hash: str,
    cursor: Dict[str, Any],
    stats: Dict[str, int],
    status: str = "idle",
):
    """커서 저장/업데이트"""
    db.table("ingestion_cursors").upsert(
        {
            "source": "pubmed",
            "query_hash": query_hash,
            "cursor": cursor,
            "stats": stats,
            "status": status,
            "last_success_at": datetime.utcnow().isoformat()
            if status == "idle"
            else None,
            "updated_at": datetime.utcnow().isoformat(),
        },
        on_conflict="source,query_hash",
    ).execute()
