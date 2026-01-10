# API Contract

Frontend (Next.js)와 Backend (FastAPI Engine) 간의 연동 규격입니다.
모든 백엔드 호출은 `/api/v1` 프리픽스를 사용해야 합니다.

## Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://<api-domain>/api/v1`

## 1. Authentication & Permissions
- **Header**: `Authorization: Bearer <supabase_jwt>`
- **Admin Access**:
    - Supabase JWT의 `role` claim이 `service_role`이거나,
    - `X-Admin-Key` 헤더에 관리자 키 포함 (Internal/Ops only).
- **Workspace Scope**:
    - RLS(Row Level Security)를 통해 자동 처리.
    - JWT에 포함된 `sub` (User ID)를 기준으로 DB 레벨에서 필터링.

## 2. Common Standards

### Pagination & Sorting
목록 조회 API는 다음 쿼리 파라미터를 지원해야 합니다.
- `limit`: 반환할 항목 수 (Default: 20, Max: 100)
- `offset`: 건너뛸 항목 수 (Default: 0)
- `sort`: 정렬 기준 (예: `created_at.desc`, `score.asc`)

### Error Handling
모든 에러 응답은 다음 형식을 따릅니다.
```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested run does not exist.",
  "trace_id": "a1b2c3d4..."
}
```

### Long-running Operations
오래 걸리는 작업(런 실행, 인덱싱 등)은 비동기로 처리하며, Job ID를 반환합니다.
**Request**: `POST /design/runs`
**Response**:
```json
{
  "job_id": "job-1234",
  "status": "queued",
  "eta": 60
}
```
**Status Check**: `GET /ops/jobs/{job_id}` (또는 리소스별 상태 조회)

### Idempotency
중복 요청 방지를 위해 `Idempotency-Key` 헤더 사용을 권장합니다.
- Header: `Idempotency-Key: <uuid>`

## 3. Endpoints

### Catalog (컴포넌트)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/components` | 컴포넌트 목록 조회 |
| GET | `/catalog/components/{id}` | 컴포넌트 상세 조회 |
| POST | `/catalog/components` | 컴포넌트 등록 |

### Design (설계 및 실행)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/design/runs` | 새 디자인 런 생성 (Async) |
| GET | `/design/runs` | 런 목록 조회 |
| GET | `/design/runs/{id}` | 런 상세 조회 |
| GET | `/design/runs/{id}/progress` | 런 진행률 조회 |
| GET | `/design/runs/{id}/candidates` | 후보 물질 목록 조회 |
| GET | `/design/runs/{id}/candidates/{cid}` | 후보 물질 상세 조회 |
| GET | `/design/runs/{id}/compare` | 후보 물질 비교 (Scores + Assay) |
| POST | `/design/runs/{id}/cancel` | 런 취소 |
| POST | `/design/runs/{id}/rerun` | 런 재실행 |

### Evidence (근거 및 문헌)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/evidence/search` | 문헌 검색 (Vector + Keyword) |
| GET | `/evidence/documents/{id}` | 문헌 상세 조회 |
| GET | `/evidence/quality/issues` | 품질 이슈 조회 |

### Uploads (데이터 업로드)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/uploads/presigned-url` | 업로드용 URL 요청 (Optional) |
| POST | `/uploads` | 파일 업로드 메타데이터 등록 |
| GET | `/uploads` | 업로드 내역 조회 |
| GET | `/uploads/{id}` | 업로드 상세 조회 |

### Reports (리포트)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reports/generate` | 리포트 생성 요청 (Async) |
| GET | `/reports` | 리포트 목록 |
| GET | `/reports/{id}` | 리포트 상세 및 다운로드 URL |

### Ops (운영 관리) - **Admin Only**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ops/queues` | 작업 큐 상태 |
| GET | `/ops/audit` | 감사 로그 |
| GET | `/ops/logs` | 시스템 로그 |

### Health (상태 확인)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | 기본 헬스체크 (DB) |
| GET | `/health/worker` | 워커 헬스체크 |
| GET | `/health/status` | 시스템 상세 상태 |

## 4. Internal APIs (Worker/System Use Only)
다음 API는 프론트엔드에서 직접 호출하지 않습니다.
- `/staging/*`: 데이터 수집 중간 단계 처리
- `/connectors/*`: 외부 데이터 소스 연동
- `/ingestion/*`: 데이터 파이프라인 제어
- `/fingerprint/*`: 분자 구조 처리
- `/feedback/*`: 전문가 피드백 처리 (추후 공개 가능)
- `/observability/*`: 상세 모니터링 지표
- `/alerts/*`: 시스템 알림 발송

## 5. Rate Limiting & Retry Policy
- **OpenAI/LLM**: 429 에러 발생 시 클라이언트는 재시도하지 않습니다. 워커가 Exponential Backoff로 재시도합니다.
- **API**: 일반적인 API 요청 제한은 분당 600회입니다. 초과 시 429 에러를 반환합니다.
