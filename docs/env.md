# ADC Platform 환경 변수

## 개요

이 문서는 ADC 플랫폼에서 사용하는 환경 변수를 설명합니다.

## 설정 방법

```bash
# 템플릿 복사
cp .env.example .env

# 실제 값 입력
nano .env  # 또는 원하는 에디터 사용
```

## 환경 변수 목록

### Supabase

| 변수 | 설명 | 필수 |
|------|------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL | ✅ |
| `SUPABASE_ANON_KEY` | Public anon key (브라우저용) | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (서버 전용) | ✅ |

> ⚠️ **보안**: Service Role Key는 **절대로** 클라이언트에 노출하지 마세요.

### Redis

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379` |

### LLM / Embedding

| 변수 | 설명 | 필수 |
|------|------|------|
| `GEMINI_API_KEY` | Gemini API Key (RAG/Protocol) | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key (Embedding) | ✅ |

### PubMed

| 변수 | 설명 | 권장 |
|------|------|------|
| `NCBI_API_KEY` | NCBI API Key (10 rps) | ✅ |
| `NCBI_EMAIL` | 연락처 이메일 | ✅ |
| `NCBI_TOOL` | 앱 식별자 | ✅ |

## 보안 원칙

| 컴포넌트 | 허용 키 |
|----------|---------|
| Next.js (브라우저) | `SUPABASE_ANON_KEY` only |
| FastAPI/Worker | 모든 키 사용 가능 |
