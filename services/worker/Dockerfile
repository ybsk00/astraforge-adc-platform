# ADC Platform - Worker Service Dockerfile
# RDKit (conda-forge) + Arq Worker

FROM continuumio/miniconda3:latest

LABEL maintainer="ADC Platform Team"
LABEL description="ADC Worker Service with RDKit for background jobs"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# RDKit 설치 (conda)
RUN conda install -c conda-forge rdkit -y && \
    conda clean -afy

# Python 의존성
# Python 의존성
COPY services/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared App Package (Engine)
COPY services/engine/app /app/app

# Worker Code
COPY services/worker /app

# 헬스체크 (Redis 연결 확인)
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import redis; r=redis.from_url('${REDIS_URL:-redis://localhost:6379}'); r.ping()" || exit 1

# 실행
CMD ["arq", "jobs.worker.WorkerSettings"]
