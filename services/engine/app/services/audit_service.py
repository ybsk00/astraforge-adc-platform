"""
Audit Service
감사 로그 기록 서비스

구현 계획 v2 기반:
- 비동기 이벤트 기록
- 민감정보 마스킹 (중첩 지원)
- 실패 정책: warn 로그 + 업무 계속, critical은 fail-fast 옵션
"""

import os
from typing import Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class AuditWriteError(Exception):
    """감사 로그 기록 실패"""

    pass


# 민감 필드 목록
MASKED_FIELDS = [
    "password",
    "api_key",
    "token",
    "secret",
    "email",
    "phone",
    "credential",
    "auth",
]

# Critical 이벤트 (fail-fast 대상)
CRITICAL_EVENTS = {
    "ruleset.updated",
    "scoring_params.updated",
    "member.removed",
    "workspace.deleted",
}

# 기록 대상 이벤트 타입
EVENT_TYPES = {
    # Run 관련
    "run.created",
    "run.executed",
    "run.completed",
    "run.failed",
    "run.cancelled",
    # 설정 변경
    "ruleset.updated",
    "scoring_params.updated",
    # 문헌
    "literature.indexed",
    "literature.excluded",
    # 리포트
    "report.exported",
    # 카탈로그
    "catalog.created",
    "catalog.deprecated",
    # 사용자
    "member.invited",
    "member.removed",
    # 피드백
    "feedback.submitted",
}


class AuditService:
    """
    감사 로그 서비스

    - 이벤트 기록
    - 민감정보 마스킹
    - 비동기 처리 (실패 시 warn)
    """

    def __init__(self, db_client=None, fail_fast_enabled: bool = False):
        """
        Args:
            db_client: Supabase 클라이언트
            fail_fast_enabled: Critical 이벤트 실패 시 예외 발생 여부
        """
        self.db = db_client
        self.fail_fast_enabled = (
            fail_fast_enabled or os.getenv("AUDIT_FAIL_FAST", "").lower() == "true"
        )
        self.logger = logger.bind(service="audit")

    async def log_event(
        self,
        event_type: str,
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        metadata: Dict[str, Any] = None,
        user_id: str = None,
        workspace_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """
        감사 이벤트 기록

        Args:
            event_type: 이벤트 유형 (예: "run.completed")
            resource_type: 리소스 타입 (예: "design_run")
            resource_id: 리소스 ID
            action: 액션 (예: "complete")
            metadata: 추가 메타데이터
            user_id: 사용자 ID
            workspace_id: 워크스페이스 ID
            ip_address: 클라이언트 IP
            user_agent: 클라이언트 User-Agent
        """
        # 메타데이터 마스킹
        masked_metadata = self.mask_sensitive(metadata or {})

        # 이벤트 레코드 생성
        event_record = {
            "event_type": event_type,
            "entity_type": resource_type,
            "entity_id": resource_id,
            "details": {"action": action, **masked_metadata},
            "created_at": datetime.utcnow().isoformat(),
        }

        if user_id:
            event_record["user_id"] = user_id
        if workspace_id:
            event_record["workspace_id"] = workspace_id

        # 로깅
        self.logger.info(
            "audit_event",
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        # DB 기록
        try:
            if self.db:
                await self._write_to_db(event_record)
            else:
                # DB 없으면 로그로만 기록
                self.logger.debug("audit_event_details", **event_record)

        except Exception as e:
            if event_type in CRITICAL_EVENTS and self.fail_fast_enabled:
                raise AuditWriteError(f"Critical audit event failed: {e}")
            else:
                self.logger.warning(
                    "audit_write_failed", event_type=event_type, error=str(e)
                )

    async def _write_to_db(self, event_record: Dict[str, Any]):
        """DB에 이벤트 기록"""
        if hasattr(self.db, "table"):
            # Supabase 클라이언트
            result = self.db.table("audit_events").insert(event_record).execute()
            return result
        # 다른 DB 클라이언트 지원 시 추가

    def log_event_sync(
        self,
        event_type: str,
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        metadata: Dict[str, Any] = None,
        user_id: str = None,
        workspace_id: str = None,
    ):
        """동기 이벤트 기록 (async 불가 시)"""
        masked_metadata = self.mask_sensitive(metadata or {})

        event_record = {
            "event_type": event_type,
            "entity_type": resource_type,
            "entity_id": resource_id,
            "details": {"action": action, **masked_metadata},
            "created_at": datetime.utcnow().isoformat(),
        }

        if user_id:
            event_record["user_id"] = user_id
        if workspace_id:
            event_record["workspace_id"] = workspace_id

        self.logger.info(
            "audit_event",
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        try:
            if self.db and hasattr(self.db, "table"):
                self.db.table("audit_events").insert(event_record).execute()
            else:
                self.logger.debug("audit_event_details", **event_record)

        except Exception as e:
            if event_type in CRITICAL_EVENTS and self.fail_fast_enabled:
                raise AuditWriteError(f"Critical audit event failed: {e}")
            else:
                self.logger.warning(
                    "audit_write_failed", event_type=event_type, error=str(e)
                )

    def mask_sensitive(
        self, data: Dict[str, Any], depth: int = 0, max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        민감정보 마스킹

        - 중첩 dict/list 지원
        - prefix/suffix 보존 (길이 > 8)
        """
        if depth > max_depth:
            return data

        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if self._is_sensitive_field(key):
                result[key] = self._mask_value(value)
            elif isinstance(value, dict):
                result[key] = self.mask_sensitive(value, depth + 1, max_depth)
            elif isinstance(value, list):
                result[key] = [
                    self.mask_sensitive(v, depth + 1, max_depth)
                    if isinstance(v, dict)
                    else v
                    for v in value
                ]
            else:
                result[key] = value

        return result

    def _is_sensitive_field(self, field_name: str) -> bool:
        """민감 필드 여부 확인"""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in MASKED_FIELDS)

    def _mask_value(self, value: Any) -> str:
        """값 마스킹"""
        if value is None:
            return None

        str_value = str(value)
        if len(str_value) > 8:
            # 처음 2자 + *** + 마지막 2자
            return f"{str_value[:2]}***{str_value[-2:]}"
        else:
            return "***MASKED***"


# 편의 함수
def get_audit_service(db_client=None, fail_fast: bool = False) -> AuditService:
    """AuditService 인스턴스 반환"""
    return AuditService(db_client=db_client, fail_fast_enabled=fail_fast)


# 이벤트 헬퍼 함수들
def audit_run_created(
    service: AuditService,
    run_id: str,
    workspace_id: str,
    user_id: str = None,
    indication: str = None,
    target_count: int = None,
):
    """런 생성 이벤트"""
    service.log_event_sync(
        event_type="run.created",
        resource_type="design_run",
        resource_id=run_id,
        action="create",
        metadata={
            "indication": indication,
            "target_count": target_count,
        },
        user_id=user_id,
        workspace_id=workspace_id,
    )


def audit_run_completed(
    service: AuditService,
    run_id: str,
    workspace_id: str,
    candidate_count: int = None,
    pareto_count: int = None,
    scoring_version: str = None,
    ruleset_version: str = None,
    duration_seconds: float = None,
):
    """런 완료 이벤트"""
    service.log_event_sync(
        event_type="run.completed",
        resource_type="design_run",
        resource_id=run_id,
        action="complete",
        metadata={
            "candidate_count": candidate_count,
            "pareto_count": pareto_count,
            "scoring_version": scoring_version,
            "ruleset_version": ruleset_version,
            "duration_seconds": duration_seconds,
        },
        workspace_id=workspace_id,
    )


def audit_run_failed(
    service: AuditService,
    run_id: str,
    workspace_id: str,
    error_message: str = None,
    error_code: str = None,
):
    """런 실패 이벤트"""
    service.log_event_sync(
        event_type="run.failed",
        resource_type="design_run",
        resource_id=run_id,
        action="fail",
        metadata={
            "error_message": error_message,
            "error_code": error_code,
        },
        workspace_id=workspace_id,
    )
