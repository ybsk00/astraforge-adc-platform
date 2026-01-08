"""
ClinicalTrials.gov Connector
ClinicalTrials.gov API v2 기반 임상시험 데이터 수집

API 문서: https://clinicaltrials.gov/data-api/api
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


class ClinicalTrialsConnector(BaseConnector):
    """
    ClinicalTrials.gov 임상시험 데이터 수집 커넥터
    
    사용법:
        connector = ClinicalTrialsConnector(db_client)
        result = await connector.run(
            seed={"conditions": ["HER2 positive breast cancer"]},
            max_pages=10
        )
    """
    
    source = "clinicaltrials"
    rate_limit_qps = 3.0  # ClinicalTrials.gov 권장
    max_retries = 3
    
    # ClinicalTrials.gov API v2 endpoint
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    def __init__(self, db_client=None):
        super().__init__(db_client)
    
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드에서 쿼리 생성
        
        seed 예시:
            {"conditions": ["breast cancer", "HER2"]}
            {"interventions": ["trastuzumab", "T-DM1"]}
            {"nct_ids": ["NCT01120184", "NCT02131064"]}
            {"query": "antibody drug conjugate ADC"}
        """
        queries = []
        
        conditions = seed.get("conditions", [])
        interventions = seed.get("interventions", [])
        nct_ids = seed.get("nct_ids", [])
        query = seed.get("query")
        
        # Condition 검색
        for cond in conditions:
            queries.append(QuerySpec(
                query=cond,
                params={"type": "condition"}
            ))
        
        # Intervention 검색
        for interv in interventions:
            queries.append(QuerySpec(
                query=interv,
                params={"type": "intervention"}
            ))
        
        # NCT ID 직접 조회
        if nct_ids:
            queries.append(QuerySpec(
                query=",".join(nct_ids),
                params={"type": "nct_ids"}
            ))
        
        # 자유 검색
        if query:
            queries.append(QuerySpec(
                query=query,
                params={"type": "search"}
            ))
        
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """ClinicalTrials.gov에서 데이터 조회"""
        
        query_type = query.params.get("type", "search")
        page_token = cursor.position.get("nextPageToken")
        page_size = 20
        
        # API v2 studies endpoint
        url = f"{self.BASE_URL}/studies"
        
        params = {
            "format": "json",
            "pageSize": page_size,
            "fields": "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,StudyType,"
                      "Condition,Intervention,PrimaryOutcome,EnrollmentInfo,"
                      "StartDate,CompletionDate,LeadSponsor,LocationCountry",
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        # 쿼리 타입에 따른 필터
        if query_type == "condition":
            params["query.cond"] = query.query
        elif query_type == "intervention":
            params["query.intr"] = query.query
        elif query_type == "nct_ids":
            params["filter.ids"] = query.query
        else:
            params["query.term"] = query.query
        
        self.logger.info("clinicaltrials_request", query=query.query[:50], type=query_type)
        
        try:
            response = await fetch_with_retry(
                url,
                rate_limiter=self.rate_limiter,
                params=params,
                max_retries=self.max_retries
            )
            
            data = response.json()
            studies = data.get("studies", [])
            next_page_token = data.get("nextPageToken")
            
            return FetchResult(
                records=studies,
                has_more=bool(next_page_token),
                next_cursor={"nextPageToken": next_page_token} if next_page_token else {}
            )
            
        except Exception as e:
            if "404" in str(e):
                return FetchResult(records=[], has_more=False)
            raise
    
    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """ClinicalTrials.gov 레코드 정규화"""
        
        protocol = record.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        
        nct_id = id_module.get("nctId")
        if not nct_id:
            return None
        
        status_module = protocol.get("statusModule", {})
        design_module = protocol.get("designModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        interventions_module = protocol.get("armsInterventionsModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        outcomes_module = protocol.get("outcomesModule", {})
        
        # Interventions 추출
        interventions = []
        for interv in interventions_module.get("interventions", []):
            interventions.append({
                "type": interv.get("type"),
                "name": interv.get("name"),
                "description": interv.get("description", "")[:500]
            })
        
        # Primary outcomes 추출
        primary_outcomes = []
        for outcome in outcomes_module.get("primaryOutcomes", [])[:5]:
            primary_outcomes.append({
                "measure": outcome.get("measure"),
                "timeFrame": outcome.get("timeFrame")
            })
        
        # Phases 추출
        phases = design_module.get("phases", [])
        phase_str = ", ".join(phases) if phases else "N/A"
        
        data = {
            "nct_id": nct_id,
            "brief_title": id_module.get("briefTitle"),
            "official_title": id_module.get("officialTitle"),
            "overall_status": status_module.get("overallStatus"),
            "phase": phase_str,
            "study_type": design_module.get("studyType"),
            "conditions": conditions_module.get("conditions", []),
            "interventions": interventions,
            "primary_outcomes": primary_outcomes,
            "enrollment": status_module.get("enrollmentInfo", {}).get("count"),
            "start_date": status_module.get("startDateStruct", {}).get("date"),
            "completion_date": status_module.get("completionDateStruct", {}).get("date"),
            "lead_sponsor": sponsor_module.get("leadSponsor", {}).get("name"),
        }
        
        checksum = NormalizedRecord.compute_checksum(data)
        
        return NormalizedRecord(
            external_id=nct_id,
            record_type="clinical_trial",
            data=data,
            checksum=checksum,
            source="clinicaltrials"
        )
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """ClinicalTrials 데이터 저장"""
        if not self.db:
            return UpsertResult()
        
        result = UpsertResult()
        
        for record in records:
            try:
                await self._save_raw(record)
                upsert_status = await self._update_target_clinical(record)
                
                if upsert_status == "inserted":
                    result.inserted += 1
                    result.ids.append(record.external_id)
                elif upsert_status == "updated":
                    result.updated += 1
                else:
                    result.unchanged += 1
                    
            except Exception as e:
                result.errors += 1
                self.logger.warning("upsert_failed", nct_id=record.external_id, error=str(e))
        
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
    
    async def _update_target_clinical(self, record: NormalizedRecord) -> str:
        """
        target_profiles.clinical 업데이트
        
        조건(conditions)이나 개입(interventions)에서 관련 타겟을 찾아 연결
        """
        data = record.data
        conditions = data.get("conditions", [])
        
        # 조건에서 타겟 관련 키워드 추출
        target_keywords = []
        for cond in conditions:
            cond_lower = cond.lower()
            # HER2, EGFR 등 일반적인 타겟 키워드
            if any(keyword in cond_lower for keyword in ["her2", "egfr", "pd-1", "pd-l1", "bcma", "cd19", "cd20"]):
                target_keywords.append(cond)
        
        if not target_keywords:
            # Raw만 저장, target 연결 없음
            return "unchanged"
        
        # 관련 target_profiles 찾기
        for keyword in target_keywords:
            # gene_symbol로 검색
            profiles = self.db.table("target_profiles").select("id, clinical").ilike(
                "gene_symbol", f"%{keyword}%"
            ).execute()
            
            if profiles.data:
                for profile in profiles.data:
                    current_clinical = profile.get("clinical", {})
                    trials = current_clinical.get("trials", [])
                    
                    # 중복 체크
                    existing_ncts = [t.get("nct_id") for t in trials]
                    if data["nct_id"] not in existing_ncts:
                        trials.append({
                            "nct_id": data["nct_id"],
                            "title": data["brief_title"],
                            "phase": data["phase"],
                            "status": data["overall_status"],
                            "updated_at": datetime.utcnow().isoformat()
                        })
                        
                        current_clinical["trials"] = trials[:20]  # 최대 20개
                        current_clinical["updated_at"] = datetime.utcnow().isoformat()
                        
                        self.db.table("target_profiles").update({
                            "clinical": current_clinical
                        }).eq("id", profile["id"]).execute()
                
                return "updated"
        
        return "inserted"
