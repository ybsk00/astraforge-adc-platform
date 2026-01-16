"""
Scheduler Service
APScheduler를 이용한 주기적 작업 관리
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog
from app.services.dataset_sync_service import get_dataset_sync_service
from app.core.supabase import get_supabase_client

logger = structlog.get_logger()


class SchedulerService:
    """스케줄러 서비스"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.logger = logger.bind(service="scheduler_service")
        self._is_running = False

    def start(self):
        """스케줄러 시작 및 작업 등록"""
        if self._is_running:
            return

        # 1. 주간 임상 데이터 동기화 작업 등록 (매주 월요일 03:00)
        self.scheduler.add_job(
            self._run_sync_job,
            CronTrigger(day_of_week="mon", hour=3, minute=0),
            id="weekly_clinical_sync",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        self.logger.info("scheduler_started", jobs=["weekly_clinical_sync"])

    def stop(self):
        """스케줄러 중지"""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            self.logger.info("scheduler_stopped")

    async def _run_sync_job(self):
        """동기화 작업 실행 래퍼"""
        self.logger.info("sync_job_triggered")
        try:
            # 의존성 주입을 위한 클라이언트 생성
            db = get_supabase_client()
            sync_service = get_dataset_sync_service(db)
            updated_count = await sync_service.sync_clinical_statuses()
            self.logger.info("sync_job_completed", updated_count=updated_count)
        except Exception as e:
            self.logger.error("sync_job_failed", error=str(e))

    def get_jobs(self):
        """등록된 작업 목록 조회"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": str(job.next_run_time),
                    "trigger": str(job.trigger),
                }
            )
        return jobs


# 싱글톤 인스턴스
_scheduler_instance = None


def get_scheduler_service() -> SchedulerService:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
