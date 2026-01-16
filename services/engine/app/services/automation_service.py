"""
Automation Service
산식 변경 감지 및 자동 검증 트리거

기능:
- scoring_params 변경 시 GoldenSetValidator 호출
- 검증 결과에 따른 감사 로그 기록
- 관리자 알림 연동 (MVP: 로그 기록)
"""

import structlog
from typing import Dict, Any
from app.services.golden_set_validator import get_golden_validator
from app.services.audit_service import get_audit_service
from app.services.notification_service import get_notification_service

logger = structlog.get_logger()


class AutomationService:
    """자동화 서비스"""

    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="automation_service")
        self.validator = get_golden_validator(db_client)
        self.audit = get_audit_service(db_client)
        self.notifier = get_notification_service()

    async def handle_scoring_param_change(self, payload: Dict[str, Any]):
        """산식 파라미터 변경 이벤트 핸들러 (Webhook 등에서 호출)"""
        param_id = payload.get("id")
        version = payload.get("version", "unknown")
        is_active = payload.get("is_active", False)

        self.logger.info(
            "scoring_param_change_detected",
            param_id=param_id,
            version=version,
            is_active=is_active,
        )

        # 활성화된 경우에만 자동 검증 실행
        if is_active:
            try:
                # 1. Golden Set 검증 실행
                result = await self.validator.run_validation(
                    scoring_version=version,
                    dataset_version="v1.1",  # 최신 데이터셋 버전
                )

                # 2. 결과 기록 (Audit Log)
                await self.audit.log_event(
                    event_type="GOLDEN_SET_AUTO_VALIDATION",
                    user_id="SYSTEM",  # 자동화 시스템
                    entity_type="scoring_params",
                    entity_id=param_id,
                    metadata={
                        "version": version,
                        "pass": result["pass"],
                        "run_id": result["run_id"],
                        "metrics": result["metrics"],
                    },
                )

                # 3. 알림 전송
                await self.notifier.notify_validation_result(
                    {
                        "pass": result["pass"],
                        "scoring_version": version,
                        "run_id": result["run_id"],
                        "metrics": result["metrics"],
                    }
                )

                self.logger.info(
                    "auto_validation_completed",
                    version=version,
                    pass_status=result["pass"],
                )

                return result

            except Exception as e:
                self.logger.error(
                    "auto_validation_failed", version=version, error=str(e)
                )
                # 실패 로그 기록
                await self.audit.log_event(
                    event_type="GOLDEN_SET_AUTO_VALIDATION_FAILED",
                    user_id="SYSTEM",
                    entity_type="scoring_params",
                    entity_id=param_id,
                    metadata={"version": version, "error": str(e)},
                )
                raise
        else:
            self.logger.info(
                "auto_validation_skipped", version=version, reason="not_active"
            )
            return None


def get_automation_service(db_client) -> AutomationService:
    return AutomationService(db_client)
