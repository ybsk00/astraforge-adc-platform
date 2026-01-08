# ADC Platform - API Reference

## Overview

ADC Platform Engine API는 FastAPI로 구현되었으며,
ADC 설계 및 의사결정을 위한 백엔드 서비스를 제공합니다.

**Base URL:** `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Endpoints Summary

| Category | Prefix | Description |
|---|---|---|
| Health | `/` | 서버 상태 확인 |
| Catalog | `/api/v1/catalog` | 컴포넌트 카탈로그 CRUD |
| Design | `/api/v1/design` | 설계 런 관리 |
| Staging | `/api/v1/staging` | 스테이징 승인 워크플로우 |
| Connectors | `/api/v1/connectors` | 외부 데이터 커넥터 |
| Ingestion | `/api/v1/ingestion` | 수집 로그 및 상태 |
| Fingerprint | `/api/v1/fingerprint` | 화학 구조 유사도 검색 |
| Feedback | `/api/v1/feedback` | Human-in-the-loop 피드백 |
| Observability | `/api/v1/observability` | 시스템 모니터링 |

---

## Health

### `GET /health`
서버 상태 확인

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Catalog API

### `GET /api/v1/catalog`
컴포넌트 목록 조회

**Query Parameters:**
- `type` (optional): target | payload | linker | antibody
- `status` (optional): active | pending_compute | failed
- `search` (optional): 이름 검색
- `limit` (default: 20, max: 100)
- `offset` (default: 0)

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### `POST /api/v1/catalog`
컴포넌트 등록

### `GET /api/v1/catalog/{id}`
컴포넌트 상세 조회

### `PATCH /api/v1/catalog/{id}`
컴포넌트 수정

### `POST /api/v1/catalog/{id}/retry`
RDKit 계산 재시도

### `GET /api/v1/catalog/stats`
카탈로그 통계

---

## Design API

### `GET /api/v1/design/runs`
설계 런 목록

### `POST /api/v1/design/runs`
새 런 생성

**Request Body:**
```json
{
  "indication": "HER2+ Breast Cancer",
  "target_ids": ["uuid1", "uuid2"],
  "strategy": "balanced",
  "constraints": {}
}
```

### `GET /api/v1/design/runs/{id}`
런 상세 조회

### `GET /api/v1/design/runs/{id}/candidates`
런의 후보 목록

### `GET /api/v1/design/runs/{id}/pareto`
파레토 프론트 조회

---

## Staging API

### `GET /api/v1/staging/components`
스테이징 컴포넌트 목록

**Query Parameters:**
- `type`: 컴포넌트 타입
- `status`: pending | approved | rejected
- `source`: 출처 필터

### `POST /api/v1/staging/components/{id}/approve`
컴포넌트 승인 → catalog로 이동

### `POST /api/v1/staging/components/{id}/reject`
컴포넌트 거절

### `POST /api/v1/staging/components/bulk/approve`
일괄 승인

### `GET /api/v1/staging/stats`
스테이징 통계

### `GET /api/v1/staging/duplicates`
중복 후보 그룹 조회

---

## Connectors API

### `GET /api/v1/connectors`
커넥터 목록 및 상태

### `POST /api/v1/connectors/{source}/run`
커넥터 실행

**Request Body:**
```json
{
  "batch_mode": true,
  "limit": 100
}
```

**Available Sources:**
- `pubmed` - 문헌 검색
- `uniprot` - 단백질 정보
- `opentargets` - 표적-질병 연관
- `chembl` - 화합물 활성
- `pubchem` - 화합물 구조
- `clinicaltrials` - 임상 시험
- `openfda` - 안전 신호
- `hpa` - 발현 데이터
- `seed` - Gold 데이터 시딩
- `resolve` - 외부 ID 해상

### `GET /api/v1/connectors/{source}/status`
커넥터 상태 조회

### `POST /api/v1/connectors/{source}/retry`
실패한 커넥터 재시도

---

## Observability API

### `GET /api/v1/observability/metrics`
커넥터 처리량 메트릭

**Query Parameters:**
- `source`: 소스 필터
- `days`: 조회 기간 (default: 7, max: 30)

### `GET /api/v1/observability/errors`
최근 오류 로그

### `GET /api/v1/observability/health`
시스템 상태

### `GET /api/v1/observability/cursors`
Ingestion 커서 상태

---

## Fingerprint API

### `POST /api/v1/fingerprint/similarity`
화학 구조 유사도 검색

**Request Body:**
```json
{
  "smiles": "CCO",
  "top_k": 10,
  "threshold": 0.7
}
```

---

## Feedback API

### `POST /api/v1/feedback`
피드백 등록

### `GET /api/v1/feedback`
피드백 목록

### `POST /api/v1/feedback/assay-results`
Assay 결과 등록

---

## Alerts API

### `GET /api/v1/alerts`
알림 목록 조회

**Query Parameters:**
- `type`: error | warning | info
- `source`: 소스 필터
- `is_read`: true | false
- `limit`: (default: 50)

### `POST /api/v1/alerts`
새 알림 생성

### `POST /api/v1/alerts/{id}/read`
알림 읽음 처리

### `POST /api/v1/alerts/read-all`
전체 알림 읽음 처리

### `DELETE /api/v1/alerts/{id}`
알림 삭제

### `GET /api/v1/alerts/stats`
알림 통계

---

## Error Responses

모든 API는 다음 형식의 오류 응답을 반환합니다:

```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes:**
- `200` - 성공
- `201` - 생성됨
- `400` - 잘못된 요청
- `404` - 리소스 없음
- `500` - 서버 오류

---

## Authentication

현재 MVP 단계에서는 인증이 비활성화되어 있습니다.
운영 환경에서는 Supabase Auth + JWT를 사용합니다.

---

## Rate Limiting

외부 API 연동 시 레이트 리밋이 적용됩니다:
- PubMed: 10 req/sec (API 키 있을 때)
- UniProt: 무제한
- ChEMBL: 10 req/sec
- PubChem: 5 req/sec
