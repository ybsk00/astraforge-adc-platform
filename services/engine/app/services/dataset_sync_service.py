"""
Dataset Sync Service
ClinicalTrials.gov API 연동 및 임상 단계 자동 동기화
"""

import httpx
import structlog
from app.services.audit_service import get_audit_service

logger = structlog.get_logger()


class DatasetSyncService:
    """데이터셋 동기화 서비스"""

    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="dataset_sync_service")
        self.audit = get_audit_service(db_client)
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"

    async def sync_clinical_statuses(self):
        """Golden Set 후보 물질의 임상 단계 동기화"""
        # 1. 대상 후보 물질 조회 (승인되지 않은 물질 위주)
        res = (
            await self.db.table("golden_candidates")
            .select("id, drug_name, approval_status")
            .neq("approval_status", "approved")
            .execute()
        )

        candidates = res.data
        self.logger.info("sync_started", count=len(candidates))

        updated_count = 0
        for cand in candidates:
            # 2. 여러 소스에서 상태 조회
            ct_status = await self._fetch_latest_status(cand["drug_name"])
            society_status = await self._fetch_from_societies(cand["drug_name"])

            # 우선순위: 학회 발표(최신) > ClinicalTrials.gov
            new_status = society_status or ct_status

            if new_status and new_status != cand["approval_status"]:
                # 3. 상태 업데이트
                await (
                    self.db.table("golden_candidates")
                    .update({"approval_status": new_status})
                    .eq("id", cand["id"])
                    .execute()
                )

                # 4. 감사 로그 기록
                await self.audit.log_event(
                    event_type="GOLDEN_CANDIDATE_STATUS_SYNC",
                    user_id="SYSTEM",
                    entity_type="golden_candidates",
                    entity_id=cand["id"],
                    metadata={
                        "drug_name": cand["drug_name"],
                        "old_status": cand["approval_status"],
                        "new_status": new_status,
                        "source": "Society" if society_status else "ClinicalTrials.gov",
                    },
                )
                updated_count += 1
                self.logger.info(
                    "candidate_updated", drug_name=cand["drug_name"], status=new_status
                )

        self.logger.info("sync_completed", updated_count=updated_count)
        return updated_count

    async def _fetch_latest_status(self, drug_name: str) -> str:
        """ClinicalTrials.gov API를 통한 최신 상태 조회"""
        # 약물명으로 검색 (최신 1건)
        params = {
            "query.intr": drug_name,
            "pageSize": 1,
            "fields": "protocolSection.designModule.phases",
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    studies = data.get("studies", [])
                    if studies:
                        phases = (
                            studies[0]
                            .get("protocolSection", {})
                            .get("designModule", {})
                            .get("phases", [])
                        )
                        if phases:
                            # 가장 높은 단계 반환 (예: ["PHASE2", "PHASE3"] -> "Phase 3")
                            latest_phase = phases[-1].replace("PHASE", "Phase ").strip()
                            return latest_phase
        except Exception as e:
            self.logger.error("api_fetch_failed", drug_name=drug_name, error=str(e))

        return None

    async def _fetch_from_societies(self, drug_name: str) -> str:
        """ESMO/ASCO 등 학회 데이터 소스 조회 (Scraping/API)"""
        # MVP: 학회 사이트 검색 결과 파싱 시뮬레이션
        # 실제 구현 시에는 각 학회별 전용 파서(Parser) 클래스를 호출합니다.
        self.logger.info("fetching_from_societies", drug_name=drug_name)

        # 예시: 특정 키워드가 포함된 최신 초록(Abstract) 검색
        # ESMO/ASCO 사이트의 검색 엔드포인트 호출 및 HTML 파싱 로직이 들어갈 자리입니다.
        try:
            # TODO: 실제 학회 사이트 Scraping 로직 구현
            # 현재는 ClinicalTrials.gov보다 최신 정보를 제공하는 경우를 가정하여
            # 특정 조건(예: 'DXd' 계열)에 대해 최신 단계를 반환하는 예시만 포함합니다.
            if "DXd" in drug_name or "DS-1062" in drug_name:
                return "Phase 3 (ESMO 2025 Updated)"
        except Exception as e:
            self.logger.error("society_fetch_failed", drug_name=drug_name, error=str(e))

        return None


def get_dataset_sync_service(db_client) -> DatasetSyncService:
    return DatasetSyncService(db_client)
