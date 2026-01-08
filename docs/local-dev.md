# ADC 플랫폼 로컬 개발 환경 설정 가이드

## 📋 사전 요구사항

| 항목 | 버전 | 필수 |
|---|---|:---:|
| Node.js | 18+ | ✅ |
| Python | 3.11+ | ✅ |
| Docker | 24+ | ✅ |
| Redis | 7+ | ✅ |

---

## 🚀 빠른 시작

### 1. 레포지토리 클론

```bash
git clone <repository-url>
cd ADC플랫폼
```

### 2. 환경변수 설정

루트 디렉토리에 `.env` 파일 생성:

```bash
cp .env.example .env
```

필수 환경변수:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
NCBI_API_KEY=your-ncbi-key

# Redis
REDIS_URL=redis://localhost:6379

# Optional
LOG_LEVEL=INFO
```

### 3. Docker 컴포즈 실행

```bash
# 모든 서비스 시작 (Redis + Engine + Worker)
docker-compose up -d

# 로그 확인
docker-compose logs -f engine
docker-compose logs -f worker

# 서비스 중지
docker-compose down
```

---

## 🔧 개별 서비스 개발

### Engine (FastAPI)

```bash
cd services/engine

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### Worker (Arq)

```bash
cd services/worker

# 의존성 설치 (engine과 동일한 venv 사용 가능)
pip install -r requirements.txt

# 워커 실행
arq jobs.worker.WorkerSettings

# 또는 개발 모드
arq jobs.worker.WorkerSettings --watch
```

### Web (Next.js)

```bash
cd apps/web

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

웹 앱: http://localhost:3000

---

## 📊 데이터베이스 설정

### Supabase 스키마 적용

```bash
# Supabase 대시보드에서 SQL 에디터 열기
# infra/supabase/schema.sql 실행

# 또는 마이그레이션 개별 실행
infra/supabase/migrations/001_*.sql
infra/supabase/migrations/002_domain_data_automation.sql
infra/supabase/migrations/003_fix_unique_constraints.sql
```

### pgvector 활성화

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 🧪 테스트 실행

### Engine 유닛 테스트

```bash
cd services/engine
pytest tests/ -v
```

### E2E 검증 스크립트

```bash
cd services/engine

# PubMed E2E
python scripts/verify_pubmed_e2e.py

# UniProt E2E
python scripts/verify_uniprot_e2e.py

# Staging Flow E2E
python scripts/verify_staging_flow.py
```

---

## 📁 프로젝트 구조

```
ADC플랫폼/
├── apps/
│   └── web/                 # Next.js 프론트엔드
├── services/
│   ├── engine/              # FastAPI 백엔드
│   │   ├── app/
│   │   │   ├── api/         # API 라우터
│   │   │   ├── scoring/     # 스코어링 엔진
│   │   │   ├── services/    # 비즈니스 로직
│   │   │   └── connectors/  # 외부 데이터 커넥터
│   │   └── scripts/         # 검증 스크립트
│   └── worker/              # Arq 워커
│       └── jobs/            # 백그라운드 작업
├── infra/
│   └── supabase/            # DB 스키마
├── config/                  # 룰셋/파라미터
├── docs/                    # 문서
└── docker-compose.yml
```

---

## 🔍 주요 API 엔드포인트

| 경로 | 설명 |
|---|---|
| `GET /health` | 헬스 체크 |
| `POST /api/v1/design/runs` | 새 런 생성 |
| `GET /api/v1/design/runs/{id}/candidates` | 후보 목록 |
| `POST /api/v1/catalog/components` | 컴포넌트 등록 |
| `POST /api/v1/staging/approve/{id}` | 스테이징 승인 |
| `POST /api/v1/feedback/feedback` | 피드백 저장 |

---

## ❓ 트러블슈팅

### RDKit 설치 실패

```bash
# conda 사용 권장
conda install -c conda-forge rdkit
```

### Redis 연결 오류

```bash
# Redis 실행 확인
redis-cli ping

# Docker로 Redis 실행
docker run -d -p 6379:6379 redis:7-alpine
```

### Supabase 연결 오류

1. 환경변수 확인: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
2. Supabase 대시보드에서 API 키 재확인
3. 네트워크 방화벽 확인
