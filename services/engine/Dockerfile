# ADC Platform - Engine Service Dockerfile
# Python 3.11 + RDKit + FastAPI

FROM python:3.11-slim

LABEL maintainer="ADC Platform Team"
LABEL description="ADC Design Engine Service with RDKit"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# 시스템 의존성 (RDKit용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RDKit 설치 (conda-forge 패키지)
RUN pip install --no-cache-dir rdkit

# 애플리케이션 코드
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
