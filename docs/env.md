# Environment Variables

ADC Platform의 각 서비스 실행을 위해 필요한 환경 변수 설정입니다.

## Common Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase 프로젝트 URL | Yes | - |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (Admin 권한) | Yes | - |
| `REDIS_URL` | Redis 연결 URL (Worker Queue용) | Yes | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API Key (Vector Search/Embedding용) | Yes | - |
| `LOG_LEVEL` | 로깅 레벨 (DEBUG, INFO, WARNING, ERROR) | No | `INFO` |
| `ENVIRONMENT` | 실행 환경 (development, production) | No | `development` |

## Service Specifics

### Engine (`services/engine`)
- API 서버 실행 시 필요합니다.
- `.env.example`을 복사하여 `.env` 파일을 생성하세요.

### Worker (`services/worker`)
- 백그라운드 작업(CSV 파싱, 임베딩 등) 실행 시 필요합니다.
- `.env.example`을 복사하여 `.env` 파일을 생성하세요.

## Setup
```bash
# Engine
cd services/engine
cp .env.example .env
# .env 파일 편집

# Worker
cd services/worker
cp .env.example .env
# .env 파일 편집
```
