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
        시드에서 쿼리 생성 (QueryProfile 지원)
        
        seed 예시:
            {"profile_name": "target_enrichment", "targets": ["HER2", "EGFR"]}
            {"profile_name": "adc_signal_boost", "targets": ["HER2"]}
        """
        queries = []
        
        # 1. Query Profile 확인
        profile_name = seed.get("profile_name")
        if not profile_name:
            # Fallback to legacy mode (if needed) or raise error
            self.logger.warning("no_profile_name_provided", seed=seed)
            return []
            
        # 2. Profile 로드 (Local import to avoid circular dependency if any)
        from services.worker.profiles import get_profile
        profile = get_profile(profile_name)
        
        if not profile:
            self.logger.error("unknown_profile", profile=profile_name)
            return []
            
        # 3. Target 기반 쿼리 생성
        targets = seed.get("targets", [])
        if not targets:
            # 타겟이 없으면 실행 불가 (Target-Centric)
            self.logger.warning("no_targets_provided", profile=profile_name)
            return []
            
        from services.worker.jobs.dictionaries import TARGET_SYNONYMS
        
        for target in targets:
            # Synonyms 가져오기
            synonyms_list = TARGET_SYNONYMS.get(target, [])
            # 검색어 구성을 위해 따옴표 처리
            synonyms_str = " OR ".join([f'"{s}"' if " " in s else s for s in synonyms_list])
            target_str = f'"{target}"' if " " in target else target
            
            # Query Template 채우기
            query_str = profile["query_template"].format(
                target=target_str,
                synonyms=synonyms_str or target_str # fallback if no synonyms
            )
            
            # Boost Keywords (Optional)
            if "boost_keywords" in profile:
                boost_str = " OR ".join([f'"{k}"' for k in profile["boost_keywords"]])
                # Boost는 AND 조건이 아니라 OR로 확장하거나, 랭킹에 영향을 주도록 구성
                # ClinicalTrials API는 복잡한 부스팅을 지원하지 않으므로, 
                # 여기서는 "Target AND (Oncology OR ADC_Keywords)" 형태로 확장
                query_str = f"{query_str} OR ({target_str} AND ({boost_str}))"

            queries.append(QuerySpec(
                query=query_str,
                params={
                    "type": "search", # 항상 search 모드 사용
                    "target": target # 메타데이터용
                }
            ))
            
        return queries
    
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """ClinicalTrials.gov에서 데이터 조회"""
        
        page_token = cursor.position.get("nextPageToken")
        page_size = 20
        
        # API v2 studies endpoint
        url = f"{self.BASE_URL}/studies"
        
        params = {
            "format": "json",
            "pageSize": page_size,
            "fields": "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,StudyType,"
                      "Condition,Intervention,PrimaryOutcome,EnrollmentInfo,"
                      "StartDate,CompletionDate,LeadSponsor,LocationCountry,"
                      "ArmsInterventionsModule,ConditionsModule,StatusModule,IdentificationModule", # Full modules for RAW
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        # Search Query
        params["query.term"] = query.query
        
        # Filter by Status (from Profile if available, hardcoded for now as per guide)
        params["filter.overallStatus"] = "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED"
        
        self.logger.info("clinicaltrials_request", query=query.query[:50])
        
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
        """
        RAW 저장 중심이므로 정규화는 최소화하거나 Skip.
        BaseConnector.run에서 normalize 실패 시 에러 카운트만 하고 진행함.
        여기서는 None을 반환하여 Upsert 단계를 건너뛰게 함 (Phase 2 전략: RAW First)
        """
        return None
    
    async def upsert(self, records: List[NormalizedRecord]) -> UpsertResult:
        """
        RAW First 전략이므로 Upsert는 사용하지 않음.
        BaseConnector.run에서 normalize가 None을 반환하면 호출되지 않음.
        """
        return UpsertResult()
    
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
