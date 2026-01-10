"""
ADC Engine - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, design, catalog, staging, connectors, ingestion, fingerprint, feedback, observability, alerts, uploads

app = FastAPI(
    title="ADC Design Engine",
    description="ADC(Antibody-Drug Conjugate) 설계 및 의사결정 엔진",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, tags=["Health"])
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


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    pass
