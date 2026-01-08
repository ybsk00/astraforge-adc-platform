# ADC Platform

ADC(Antibody-Drug Conjugate) 설계 및 의사결정 엔진 플랫폼

## 🏗️ 프로젝트 구조

```
├── apps/
│   └── web/                  # Next.js 프론트엔드
├── services/
│   ├── engine/               # FastAPI 엔진 서비스
│   └── worker/               # Arq 워커 (RDKit 포함)
├── infra/
│   └── supabase/
│       ├── schema.sql        # 전체 DDL
│       └── migrations/       # 마이그레이션 파일
├── scripts/                  # 벤치마크/유틸리티
├── docs/                     # 문서
└── docker-compose.yml        # 로컬 개발 환경
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 복사
cp .env.example .env

# .env 파일에 실제 값 입력
```

### 2. Docker 실행

```bash
# 전체 서비스 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

### 3. 서비스 확인

- **Engine API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 📋 개발 가이드

### Engine (FastAPI)

```bash
cd services/engine
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Worker (Arq)

```bash
cd services/worker
pip install -r requirements.txt
# RDKit은 conda로 설치: conda install -c conda-forge rdkit
arq jobs.worker.WorkerSettings
```

### Web (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

## 🗄️ 데이터베이스

Supabase Dashboard에서 `infra/supabase/schema.sql` 실행

### 필수 Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
```

## 🔐 보안 원칙

| 컴포넌트 | 사용 키 | 원칙 |
|----------|---------|------|
| 브라우저 | `anon_key` only | Service Role 노출 금지 |
| 서버 | `service_role_key` | 서버에서만 사용 |

## 📚 문서

- [구현 계획](docs/implementation_plan.md)
- [API 명세](http://localhost:8000/docs)
- [환경 변수](docs/env.md)

## 📦 기술 스택

- **Frontend**: Next.js 14+ (App Router)
- **Backend**: FastAPI + Arq
- **Database**: Supabase (PostgreSQL + pgvector)
- **Cheminformatics**: RDKit
- **LLM**: Gemini API
- **Embedding**: OpenAI text-embedding-3-small
