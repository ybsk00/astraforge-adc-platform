"""
ADC Engine - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import health, design, catalog, staging, connectors, ingestion, fingerprint, feedback, observability, alerts, uploads, evidence, reports, ops, automation, pipeline, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    # Startup
    from app.core.database import get_db
    import structlog
    
    logger = structlog.get_logger()
    try:
        db = get_db()
        # Lightweight connection check (select 1 equivalent)
        db.table("workspaces").select("id").limit(1).execute()
        logger.info("database_connected", url=settings.SUPABASE_URL)
    except Exception as e:
        # Log but don't crash, as per recommendation
        logger.error("database_connection_failed", error=str(e))
    
    # 2. 스케줄러 시작 (Phase 15)
    from app.services.scheduler_service import get_scheduler_service
    scheduler = get_scheduler_service()
    scheduler.start()
    
    yield
    
    # Shutdown
    # 3. 스케줄러 중지
    scheduler.stop()
    logger.info("application_shutdown")

app = FastAPI(
    title="ADC Design Engine",
    description="ADC(Antibody-Drug Conjugate) 설계 및 의사결정 엔진",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
from fastapi import HTTPException
from app.core.errors import global_exception_handler

app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(design.router, prefix="/api/v1/design", tags=["Design"])
app.include_router(staging.router, prefix="/api/v1/staging", tags=["Staging"])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connectors"])
app.include_router(ingestion.router, prefix="/api/v1/ingestion", tags=["Ingestion"])
app.include_router(fingerprint.router, prefix="/api/v1/fingerprint", tags=["Fingerprint"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["Observability"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["Uploads"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(ops.router, prefix="/api/v1/ops", tags=["Ops"])
app.include_router(automation.router, prefix="/api/v1", tags=["Automation"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
