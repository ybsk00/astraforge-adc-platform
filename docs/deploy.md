# 배포 가이드 (Deploy Guide)

ADC 플랫폼 배포 절차를 설명합니다.

---

## 1. 아키텍처 개요

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│    Engine   │────▶│   Supabase  │
│   (Web)     │     │    (VM)     │     │ (Postgres)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────▼─────┐
                    │   Worker  │────▶ Redis (Managed)
                    │   (VM)    │
                    └───────────┘
```

---

## 2. 사전 요구사항

### 2.1 인프라
- **Supabase**: Project 생성 + pgvector 활성화
- **Redis**: Managed Redis (Upstash/Redis Cloud 권장)
- **VM**: Docker 설치된 Linux VM (Ubuntu 22.04 권장)

### 2.2 API 키
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY` (Embedding)
- `GEMINI_API_KEY` (LLM)
- `REDIS_URL` (Arq Worker)

---

## 3. 배포 절차

### 3.1 Web (Vercel)

```bash
# 1. Vercel CLI 설치
npm i -g vercel

# 2. 프로젝트 연결
cd apps/web
vercel link

# 3. 환경 변수 설정
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add NEXT_PUBLIC_ENGINE_URL

# 4. 배포
vercel --prod
```

### 3.2 Engine (VM + Docker)

```bash
# 1. 저장소 클론
git clone <repo-url>
cd ADC플랫폼

# 2. 환경 변수 설정
cp .env.example .env
vim .env  # 실제 값 입력

# 3. Docker 빌드 및 실행
docker-compose up -d engine

# 4. 헬스체크
curl http://localhost:8000/health
```

### 3.3 Worker (VM + Docker)

```bash
# Engine과 동일 VM에서
docker-compose up -d worker

# 로그 확인
docker-compose logs -f worker
```

---

## 4. 환경 변수

| 변수명 | 위치 | 설명 |
|---|---|---|
| `SUPABASE_URL` | Engine, Worker | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Engine, Worker | Service Role Key |
| `REDIS_URL` | Worker | Redis 연결 URL |
| `OPENAI_API_KEY` | Engine | OpenAI API Key |
| `GEMINI_API_KEY` | Engine | Google Gemini API Key |

---

## 5. 롤백 절차

### 5.1 Web (Vercel)
```bash
# 이전 배포로 롤백
vercel rollback
```

### 5.2 Engine/Worker (Docker)
```bash
# 1. 이전 이미지 태그 확인
docker images

# 2. 이전 버전으로 롤백
docker-compose down
docker-compose up -d --force-recreate
```

---

## 6. 모니터링

### 6.1 로그 확인
```bash
# Engine 로그
docker-compose logs -f engine

# Worker 로그
docker-compose logs -f worker
```

### 6.2 Observability
- 브라우저에서 `/admin/observability` 접속
- 일별 처리량, 오류율 확인

### 6.3 알림
- `/admin/alerts` 페이지에서 시스템 알림 확인
- 오류 발생 시 자동 알림 생성

---

## 7. 문제 해결

### 7.1 Engine 연결 실패
```bash
# 1. 컨테이너 상태 확인
docker-compose ps

# 2. 로그 확인
docker-compose logs engine | tail -50

# 3. 재시작
docker-compose restart engine
```

### 7.2 Worker 큐 정체
```bash
# 1. Redis 연결 확인
redis-cli -u $REDIS_URL ping

# 2. 큐 상태 확인
redis-cli -u $REDIS_URL llen arq:queue:default

# 3. Worker 재시작
docker-compose restart worker
```

---

## 8. 체크리스트

### 배포 전
- [ ] 환경 변수 설정 완료
- [ ] Supabase pgvector 활성화
- [ ] Redis 연결 테스트
- [ ] API 키 유효성 확인

### 배포 후
- [ ] /health 엔드포인트 응답 확인
- [ ] /admin/connectors 페이지 로드 확인
- [ ] 테스트 런 생성 확인
- [ ] Worker 로그 오류 없음 확인
