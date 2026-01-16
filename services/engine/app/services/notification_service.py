"""
Notification Service
이메일(Resend) 및 Slack 알림 전송 서비스
"""

import os
import httpx
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()


class NotificationService:
    """알림 서비스"""

    def __init__(self):
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        self.logger = logger.bind(service="notification_service")

    async def send_slack_notification(
        self, message: str, blocks: Optional[list] = None
    ):
        """Slack 알림 전송"""
        if not self.slack_webhook_url:
            self.logger.warning("slack_webhook_url_not_configured")
            return

        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(self.slack_webhook_url, json=payload)
                res.raise_for_status()
                self.logger.info("slack_notification_sent")
        except Exception as e:
            self.logger.error("slack_notification_failed", error=str(e))

    async def send_email_notification(self, subject: str, html_content: str):
        """이메일 알림 전송 (Resend API 사용)"""
        if not self.resend_api_key:
            self.logger.warning("resend_api_key_not_configured")
            return

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": "ADC Platform <notifications@astraforge.ai>",
            "to": [self.admin_email],
            "subject": subject,
            "html": html_content,
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                self.logger.info("email_notification_sent")
        except Exception as e:
            self.logger.error("email_notification_failed", error=str(e))

    async def notify_validation_result(self, result: Dict[str, Any]):
        """검증 결과 알림 (실패 시 강조)"""
        is_pass = result.get("pass", False)
        version = result.get("scoring_version", "unknown")
        metrics = result.get("metrics", [])

        status_str = "✅ PASS" if is_pass else "❌ FAILED"
        subject = f"[ADC] Golden Set Validation {status_str} ({version})"

        # Slack Blocks 구성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Golden Set 검증 결과: {status_str}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Version:* {version}"},
                    {"type": "mrkdwn", "text": f"*Run ID:* {result.get('run_id')}"},
                ],
            },
        ]

        metric_text = "\n".join(
            [
                f"• {m['axis']} {m['metric']}: {m['value']:.4f} ({'OK' if m['pass'] else 'FAIL'})"
                for m in metrics
            ]
        )
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*주요 지표:*\n{metric_text}"},
            }
        )

        # Slack 전송
        await self.send_slack_notification(subject, blocks=blocks)

        # 실패 시에만 이메일 전송 (노이즈 방지)
        if not is_pass:
            html = f"<h2>Golden Set 검증 실패 알림</h2><p>버전: {version}</p><ul>"
            for m in metrics:
                color = "green" if m["pass"] else "red"
                html += f"<li style='color: {color}'>{m['axis']} {m['metric']}: {m['value']:.4f}</li>"
            html += "</ul><p><a href='#'>대시보드에서 확인하기</a></p>"
            await self.send_email_notification(subject, html)


def get_notification_service() -> NotificationService:
    return NotificationService()
