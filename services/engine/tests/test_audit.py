"""
Audit Service Tests
- 이벤트 기록 테스트
- 마스킹 테스트
"""

import pytest

from app.services.audit_service import (
    AuditService,
)


class TestAuditMasking:
    """민감정보 마스킹 테스트"""

    @pytest.fixture
    def service(self):
        return AuditService()

    def test_mask_email(self, service):
        """이메일 마스킹"""
        data = {"user_email": "user@example.com"}
        masked = service.mask_sensitive(data)

        assert masked["user_email"] != "user@example.com"
        assert "***" in masked["user_email"]

    def test_mask_api_key(self, service):
        """API 키 마스킹"""
        data = {"api_key": "sk-1234567890abcdef"}
        masked = service.mask_sensitive(data)

        assert "1234567890" not in masked["api_key"]
        assert "***" in masked["api_key"]

    def test_mask_password(self, service):
        """비밀번호 마스킹"""
        data = {"password": "mysecretpassword"}
        masked = service.mask_sensitive(data)

        assert masked["password"] == "my***rd"  # 처음 2자 + *** + 마지막 2자

    def test_mask_short_value(self, service):
        """짧은 값 마스킹"""
        data = {"token": "abc"}
        masked = service.mask_sensitive(data)

        assert masked["token"] == "***MASKED***"

    def test_mask_nested_dict(self, service):
        """중첩 딕셔너리 마스킹"""
        data = {"user": {"email": "user@example.com", "name": "John Doe"}}
        masked = service.mask_sensitive(data)

        assert "***" in masked["user"]["email"]
        assert masked["user"]["name"] == "John Doe"  # 민감하지 않은 필드

    def test_mask_nested_list(self, service):
        """중첩 리스트 마스킹"""
        data = {
            "users": [{"email": "user1@example.com"}, {"email": "user2@example.com"}]
        }
        masked = service.mask_sensitive(data)

        for user in masked["users"]:
            assert "***" in user["email"]

    def test_non_sensitive_fields_unchanged(self, service):
        """민감하지 않은 필드는 변경 없음"""
        data = {"name": "Test Run", "count": 100, "status": "completed"}
        masked = service.mask_sensitive(data)

        assert masked == data

    def test_mask_with_none_value(self, service):
        """None 값 처리"""
        data = {"token": None, "name": "test"}
        masked = service.mask_sensitive(data)

        assert masked["token"] is None
        assert masked["name"] == "test"

    def test_preserve_prefix_suffix(self, service):
        """긴 값은 prefix/suffix 보존"""
        data = {"api_key": "sk-longsecretkeyvalue123"}
        masked = service.mask_sensitive(data)

        # 처음 2자 + *** + 마지막 2자
        assert masked["api_key"].startswith("sk")
        assert masked["api_key"].endswith("23")
        assert "***" in masked["api_key"]


class TestAuditService:
    """Audit Service 테스트"""

    @pytest.fixture
    def service(self):
        return AuditService()

    def test_log_event_sync_no_db(self, service):
        """DB 없이 동기 이벤트 기록 (로그만)"""
        # Should not raise
        service.log_event_sync(
            event_type="run.completed",
            resource_type="design_run",
            resource_id="test-run-id",
            action="complete",
            metadata={"candidate_count": 100},
        )

    def test_log_event_with_sensitive_data(self, service):
        """민감정보 포함 이벤트 (마스킹됨)"""
        # Should not raise and should mask
        service.log_event_sync(
            event_type="member.invited",
            resource_type="user",
            resource_id="test-user-id",
            action="invite",
            metadata={
                "email": "newuser@example.com",
                "token": "invitation-token-secret",
            },
        )

    def test_critical_event_types(self):
        """Critical 이벤트 타입 확인"""
        from app.services.audit_service import CRITICAL_EVENTS

        assert "ruleset.updated" in CRITICAL_EVENTS
        assert "scoring_params.updated" in CRITICAL_EVENTS
        assert "run.completed" not in CRITICAL_EVENTS


class TestAuditServiceIntegration:
    """Audit Service 통합 테스트 (모킹 필요)"""

    def test_fail_fast_disabled_continues(self):
        """fail_fast 비활성화 시 업무 계속"""
        # DB 연결 실패해도 예외 발생하지 않음
        service = AuditService(db_client=None, fail_fast_enabled=False)

        # Should not raise
        service.log_event_sync(
            event_type="run.completed",
            resource_type="design_run",
            resource_id="test-id",
        )
