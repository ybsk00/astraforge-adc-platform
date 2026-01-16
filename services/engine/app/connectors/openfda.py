"""
openFDA Connector
openFDA FAERS API 기반 약물 부작용 안전 신호 수집

API 문서: https://open.fda.gov/apis/drug/event/
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


class OpenFDAConnector(BaseConnector):
    """
    openFDA 약물 부작용(FAERS) 데이터 수집 커넥터

    사용법:
        connector = OpenFDAConnector(db_client)
        result = await connector.run(
            seed={"drug_names": ["trastuzumab", "ado-trastuzumab emtansine"]},
            max_pages=10
        )
    """

    source = "openfda"
    rate_limit_qps = 4.0  # openFDA: 240 req/min = 4 req/sec
    max_retries = 3

    # openFDA endpoint
    BASE_URL = "https://api.fda.gov/drug/event.json"

    def __init__(self, db_client=None):
        super().__init__(db_client)
        self.api_key = os.getenv("OPENFDA_API_KEY", "")

    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성

        seed 예시:
            {"drug_names": ["trastuzumab", "pembrolizumab"]}
            {"generic_names": ["trastuzumab"]}
            {"brand_names": ["Herceptin", "Kadcyla"]}
        """
        queries = []

        drug_names = seed.get("drug_names", [])
        generic_names = seed.get("generic_names", [])
        brand_names = seed.get("brand_names", [])

        for name in drug_names:
            queries.append(QuerySpec(query=name, params={"type": "drug_name"}))

        for name in generic_names:
            queries.append(QuerySpec(query=name, params={"type": "generic_name"}))

        for name in brand_names:
            queries.append(QuerySpec(query=name, params={"type": "brand_name"}))

        return queries

    async def fetch_page(self, query: QuerySpec, cursor: CursorState) -> FetchResult:
        """openFDA에서 데이터 조회"""

        query_type = query.params.get("type", "drug_name")
        skip = cursor.position.get("skip", 0)
        limit = 100

        # 쿼리 필드 매핑
        if query_type == "drug_name":
            search_field = f'patient.drug.medicinalproduct:"{query.query}"'
        elif query_type == "generic_name":
            search_field = f'patient.drug.openfda.generic_name:"{query.query}"'
        else:  # brand_name
            search_field = f'patient.drug.openfda.brand_name:"{query.query}"'

        params = {
            "search": search_field,
            "limit": limit,
            "skip": skip,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        self.logger.info(
            "openfda_request", query=query.query, type=query_type, skip=skip
        )

        try:
            response = await fetch_with_retry(
                self.BASE_URL,
                rate_limiter=self.rate_limiter,
                params=params,
                max_retries=self.max_retries,
            )

            data = response.json()
            results = data.get("results", [])
            meta = data.get("meta", {}).get("results", {})
            total = meta.get("total", 0)

            has_more = (skip + limit) < min(total, 1000)  # openFDA는 최대 1000개

            # 결과에 drug_name 추가
            for r in results:
                r["_query_drug_name"] = query.query

            return FetchResult(
                records=results, has_more=has_more, next_cursor={"skip": skip + limit}
            )

        except Exception as e:
            if "404" in str(e) or "No matches found" in str(e):
                return FetchResult(records=[], has_more=False)
            raise

    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """openFDA 레코드 정규화"""

        safety_report_id = record.get("safetyreportid")
        if not safety_report_id:
            return None

        query_drug = record.get("_query_drug_name", "")

        # Patient reactions
        patient = record.get("patient", {})
        reactions = []
        for reaction in patient.get("reaction", [])[:10]:
            reactions.append(
                {
                    "term": reaction.get("reactionmeddrapt"),
                    "outcome": reaction.get("reactionoutcome"),
                }
            )

        # Drug info
        drugs = []
        for drug in patient.get("drug", [])[:5]:
            drug_info = {
                "name": drug.get("medicinalproduct"),
                "indication": drug.get("drugindication"),
                "characterization": drug.get(
                    "drugcharacterization"
                ),  # 1=suspect, 2=concomitant, 3=interacting
            }
            openfda = drug.get("openfda", {})
            if openfda:
                drug_info["brand_name"] = openfda.get("brand_name", [None])[0]
                drug_info["generic_name"] = openfda.get("generic_name", [None])[0]
                drug_info["manufacturer"] = openfda.get("manufacturer_name", [None])[0]
            drugs.append(drug_info)

        # Outcome mapping

        data = {
            "safety_report_id": safety_report_id,
            "query_drug": query_drug,
            "receive_date": record.get("receivedate"),
            "serious": record.get("serious"),
            "serious_death": record.get("seriousnessdeath"),
            "serious_hospitalization": record.get("seriousnesshospitalization"),
            "serious_disability": record.get("seriousnessdisabling"),
            "patient_sex": patient.get("patientsex"),
            "patient_age": patient.get("patientonsetage"),
            "patient_age_unit": patient.get("patientonsetageunit"),
            "reactions": reactions,
            "drugs": drugs,
            "report_country": record.get("occurcountry"),
        }

        checksum = NormalizedRecord.compute_checksum(data)

        return NormalizedRecord(
            external_id=safety_report_id,
            record_type="adverse_event",
            data=data,
            checksum=checksum,
            source="openfda",
        )

    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """openFDA 데이터 저장 및 집계"""
        if not self.db:
            return UpsertResult()

        result = UpsertResult()

        # 약물별로 그룹화하여 safety_signals 집계
        drug_signals = {}

        for record in records:
            try:
                await self._save_raw(record)
                result.inserted += 1

                # Safety signals 집계
                drug_name = record.data.get("query_drug")
                if drug_name:
                    if drug_name not in drug_signals:
                        drug_signals[drug_name] = {
                            "total_reports": 0,
                            "serious_reports": 0,
                            "fatal_reports": 0,
                            "reactions": {},
                        }

                    signals = drug_signals[drug_name]
                    signals["total_reports"] += 1

                    if record.data.get("serious") == "1":
                        signals["serious_reports"] += 1
                    if record.data.get("serious_death") == "1":
                        signals["fatal_reports"] += 1

                    for reaction in record.data.get("reactions", []):
                        term = reaction.get("term", "unknown")
                        signals["reactions"][term] = (
                            signals["reactions"].get(term, 0) + 1
                        )

            except Exception as e:
                result.errors += 1
                self.logger.warning(
                    "upsert_failed", id=record.external_id, error=str(e)
                )

        # target_profiles.safety_signals 업데이트
        for drug_name, signals in drug_signals.items():
            await self._update_safety_signals(drug_name, signals)

        return result

    async def _save_raw(self, record: NormalizedRecord):
        """원본 데이터 저장"""
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

    async def _update_safety_signals(self, drug_name: str, signals: Dict):
        """
        target_profiles.safety_signals 업데이트

        약물 이름으로 관련 타겟을 찾아 안전 신호 저장
        """
        # compound_registry에서 약물 검색
        compounds = self.db.table("compound_registry").select("id, synonyms").execute()

        related_compound_id = None
        for compound in compounds.data:
            synonyms = compound.get("synonyms", [])
            if drug_name.lower() in [s.lower() for s in synonyms if s]:
                related_compound_id = compound["id"]
                break

        # 관련 component 찾기
        if related_compound_id:
            components = (
                self.db.table("component_catalog")
                .select("id, properties")
                .eq("type", "payload")
                .execute()
            )

            for comp in components.data:
                comp.get("properties", {})
                # 연결된 compound_id가 있으면 업데이트
                # (실제로는 target과 연결해야 하지만, payload 기준으로 저장)

        # 직접 target_profiles 검색 (gene_symbol 기반은 아니지만 raw 데이터로 저장)
        # safety_signals는 drug 기반이므로 별도 테이블이 더 적합할 수 있음

        # 현재는 raw에만 저장하고 집계는 별도 쿼리로 처리
        self.logger.info(
            "safety_signals_aggregated",
            drug=drug_name,
            total=signals["total_reports"],
            serious=signals["serious_reports"],
        )


# ============================================================
# Safety Signal 집계 함수
# ============================================================


async def aggregate_safety_signals(db, drug_name: str) -> Dict:
    """
    특정 약물의 안전 신호 집계

    Args:
        db: Supabase 클라이언트
        drug_name: 약물 이름

    Returns:
        집계된 안전 신호 데이터
    """
    # raw_source_records에서 해당 약물 데이터 조회
    records = (
        db.table("raw_source_records")
        .select("payload")
        .eq("source", "openfda")
        .execute()
    )

    signals = {
        "drug_name": drug_name,
        "total_reports": 0,
        "serious_reports": 0,
        "fatal_reports": 0,
        "top_reactions": [],
        "reports_by_year": {},
    }

    reaction_counts = {}

    for record in records.data:
        payload = record.get("payload", {})
        if payload.get("query_drug", "").lower() != drug_name.lower():
            continue

        signals["total_reports"] += 1

        if payload.get("serious") == "1":
            signals["serious_reports"] += 1
        if payload.get("serious_death") == "1":
            signals["fatal_reports"] += 1

        # Reactions 집계
        for reaction in payload.get("reactions", []):
            term = reaction.get("term", "unknown")
            reaction_counts[term] = reaction_counts.get(term, 0) + 1

        # 연도별 집계
        receive_date = payload.get("receive_date", "")
        if len(receive_date) >= 4:
            year = receive_date[:4]
            signals["reports_by_year"][year] = (
                signals["reports_by_year"].get(year, 0) + 1
            )

    # Top reactions
    signals["top_reactions"] = sorted(
        [{"term": k, "count": v} for k, v in reaction_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:20]

    return signals
