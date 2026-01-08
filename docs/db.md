# ADC Platform - Database Schema Reference

## Overview

ADC Platform은 Supabase (PostgreSQL + pgvector)를 사용합니다.

**Extensions:**
- `uuid-ossp` - UUID 생성
    candidates ||--o{ candidate_scores : has
    candidates ||--o{ candidate_evidence : has
    component_catalog ||--o{ staging_components : from
```

---

## 1. Core Tables

### `workspaces`
멀티테넌트 워크스페이스

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| name | TEXT | 워크스페이스 이름 |
| settings | JSONB | 설정 |
| created_at | TIMESTAMPTZ | 생성일 |

### `app_users`
사용자 정보

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK → workspaces |
| email | TEXT | 이메일 |
| role | TEXT | admin / member / viewer |
| created_at | TIMESTAMPTZ | 생성일 |

---

## 2. Catalog Tables

### `component_catalog`
컴포넌트 카탈로그 (Target, Payload, Linker, Antibody)

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK → workspaces (NULL = public) |
| type | TEXT | target / payload / linker / antibody |
| name | TEXT | 이름 |
| canonical_smiles | TEXT | 정규화된 SMILES (화합물) |
| properties | JSONB | 속성 (RDKit 디스크립터 포함) |
| quality_grade | TEXT | gold / silver / bronze |
| status | TEXT | active / pending_compute / failed |
| gene_symbol | TEXT | 유전자 심볼 (Target) |
| uniprot_accession | TEXT | UniProt ID (Target) |
| inchikey | TEXT | InChIKey (화합물) |
| pubchem_cid | INTEGER | PubChem CID (화합물) |
| chembl_id | TEXT | ChEMBL ID (화합물) |
| is_gold | BOOLEAN | Gold Standard 여부 |
| created_at | TIMESTAMPTZ | 생성일 |

### `staging_components`
스테이징 (검수 대기)

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| type | TEXT | 컴포넌트 타입 |
| name | TEXT | 이름 |
| normalized | JSONB | 정규화된 데이터 |
| source | JSONB | 출처 정보 |
| status | TEXT | pending_review / approved / rejected |
| review_note | TEXT | 검수 메모 |
| approved_at | TIMESTAMPTZ | 승인일 |

---

## 3. Design Run Tables

### `design_runs`
설계 실행

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK → workspaces |
| target_ids | UUID[] | 선택된 타겟 ID 배열 |
| indication | TEXT | 적응증 |
| strategy | TEXT | balanced / aggressive / conservative |
| constraints | JSONB | 제약 조건 |
| status | TEXT | pending / running / completed / failed |
| scoring_version | TEXT | 스코어링 파라미터 버전 |
| ruleset_version | TEXT | 룰셋 버전 |
| result_summary | JSONB | 결과 요약 |
| created_at | TIMESTAMPTZ | 생성일 |
| completed_at | TIMESTAMPTZ | 완료일 |

### `run_progress`
런 진행률

| Column | Type | Description |
|---|---|---|
| run_id | UUID | PK, FK → design_runs |
| phase | TEXT | 현재 단계 |
| processed_candidates | INT | 처리된 후보 수 |
| accepted_candidates | INT | 통과된 후보 수 |
| rejected_candidates | INT | 거절된 후보 수 |

### `candidates`
생성된 후보

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| run_id | UUID | FK → design_runs |
| target_id | UUID | 타겟 ID |
| antibody_id | UUID | 항체 ID |
| linker_id | UUID | 링커 ID |
| payload_id | UUID | 페이로드 ID |
| candidate_hash | TEXT | 조합 해시 (중복 방지) |
| status | TEXT | pending / scored / rejected |

### `candidate_scores`
후보 점수

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| candidate_id | UUID | FK → candidates |
| eng_fit | NUMERIC | 엔지니어링 적합도 (0-100) |
| bio_fit | NUMERIC | 생물학적 적합도 (0-100) |
| safety_fit | NUMERIC | 안전성 적합도 (0-100) |
| total_fit | NUMERIC | 종합 점수 (0-100) |
| score_components | JSONB | 세부 점수 항목 |
| feature_importance | JSONB | 피처 기여도 |

---

## 4. Evidence & Protocol Tables

### `candidate_evidence`
후보 근거

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| candidate_id | UUID | FK → candidates |
| evidence_type | TEXT | literature / clinical / preclinical |
| content | JSONB | 근거 내용 |
| citations | JSONB[] | 인용 목록 |
| polarity | TEXT | positive / negative / neutral |
| confidence | NUMERIC | 신뢰도 |

### `candidate_protocols`
권장 프로토콜

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| candidate_id | UUID | FK → candidates |
| template_id | TEXT | 프로토콜 템플릿 ID |
| protocol | JSONB | 프로토콜 내용 |
| rationale | TEXT | 추천 이유 |

---

## 5. Literature Tables

### `literature_documents`
문헌 메타데이터

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| pmid | TEXT | PubMed ID |
| doi | TEXT | DOI |
| title | TEXT | 제목 |
| abstract | TEXT | 초록 |
| authors | JSONB | 저자 목록 |
| published_at | DATE | 발행일 |

### `literature_chunks`
문헌 청크 (RAG용)

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK → literature_documents |
| content | TEXT | 청크 내용 |
| embedding | VECTOR(1536) | 임베딩 벡터 |
| embedding_model | TEXT | 모델 ID |
| token_count | INT | 토큰 수 |

---

## 6. Ingestion Tables

### `ingestion_cursors`
증분 수집 커서

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| source | TEXT | pubmed / uniprot / chembl 등 |
| query_hash | TEXT | 쿼리 해시 |
| cursor | JSONB | 커서 상태 |
| last_success_at | TIMESTAMPTZ | 마지막 성공 |
| stats | JSONB | 통계 (fetched, new, updated) |
| status | TEXT | idle / running / failed |

### `ingestion_logs`
수집 로그

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| source | TEXT | 소스 |
| phase | TEXT | 단계 |
| status | TEXT | started / completed / failed |
| meta | JSONB | 메타데이터 |
| created_at | TIMESTAMPTZ | 생성일 |

### `raw_source_records`
원본 데이터 보존

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| source | TEXT | 소스 |
| external_id | TEXT | 외부 ID |
| payload | JSONB | 원본 응답 |
| checksum | TEXT | 변경 감지용 해시 |
| fetched_at | TIMESTAMPTZ | 수집일 |

---

## 7. Derived Tables

### `target_profiles`
타겟 프로필 (보강 데이터)

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| target_id | UUID | FK → component_catalog |
| uniprot_data | JSONB | UniProt 데이터 |
| opentargets_data | JSONB | Open Targets 연관 |
| hpa_data | JSONB | HPA 발현 데이터 |
| clinical_data | JSONB | 임상 데이터 |

### `compound_registry`
화합물 레지스트리

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| inchi_key | TEXT | InChIKey (중복 제거 키) |
| chembl_id | TEXT | ChEMBL ID |
| pubchem_cid | INTEGER | PubChem CID |
| structures | JSONB | 구조 정보 |
| properties | JSONB | 물성 정보 |

---

## 8. Version Management

### `rulesets`
룰셋 버전 관리

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| version | TEXT | 버전 (v0.1 등) |
| yaml_text | TEXT | YAML 내용 |
| sha256 | TEXT | 해시 |
| is_active | BOOLEAN | 활성화 여부 |

### `scoring_params`
스코어링 파라미터 버전 관리

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| version | TEXT | 버전 (v0.2 등) |
| params | JSONB | 파라미터 |
| is_active | BOOLEAN | 활성화 여부 |

---

## Indexes

주요 인덱스:
- `idx_component_catalog_type` - 타입별 조회
- `idx_component_catalog_status` - 상태별 조회
- `idx_design_runs_workspace` - 워크스페이스별 런
- `idx_candidates_run` - 런별 후보
- `idx_literature_chunks_embedding` - 벡터 검색 (ivfflat)

---

## RLS Policies

Row Level Security가 다음 테이블에 적용됩니다:
- `design_runs` - workspace_id 기반
- `candidates` - run의 workspace_id 기반
- `component_catalog` - public (NULL) 또는 workspace_id
- `literature_documents` - public 또는 private

---

## Migrations

마이그레이션 파일 위치: `infra/supabase/migrations/`

| File | Description |
|---|---|
| `001_initial.sql` | 초기 스키마 |
| `002_domain_data_automation.sql` | 자동 수집 테이블 |
| `003_pareto_tables.sql` | 파레토 프론트 |
| `004_refine_catalog_schema.sql` | 카탈로그 스키마 보완 |
