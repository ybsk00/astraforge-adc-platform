# ADC 플랫폼: 도메인 데이터 자동 수집(Connectors) 구축 설계서 v1.0  
*(Supabase + Next.js + FastAPI + Arq/Redis 기준)*

## 0. 목표와 원칙

### 목표
- **도메인 데이터(정형 + 문헌 + 화학/구조)를 자동으로 수집·정규화·저장**하여 카탈로그/스코어링/RAG의 기반으로 사용
- **업데이트(증분 수집)**가 가능하도록 커서(cursor)와 버전 관리를 내장
- 운영 관점에서 **장애/레이트리밋/품질 이슈에 견딜 수 있는 파이프라인** 구성

### 원칙(운영 우선순위)
1. **지금 당장 키가 필요한 것**: PubMed(NCBI) (완료), LLM(Gemini), Embedding(OpenAI)
2. **키 없이도 먼저 구축 가능한 커넥터**를 우선 구현해 “자동 파이프라인”을 완성  
   - UniProt / Open Targets / ChEMBL / PubChem / ClinicalTrials / openFDA
3. **상용 데이터(유료/계약 필요)**는 플랫폼 가치 검증(PoC) 이후 단계적으로 추가

---

## 1. 전체 아키텍처(데이터 자동 수집)

### 구성 요소
- **Next.js(Admin UI)**: 커넥터 실행/상태/재시도, 스테이징 승인, 품질 리포트
- **FastAPI(Engine)**: 커넥터 오케스트레이션 API, 정규화/업서트 로직, 검색 API
- **Arq Worker + Redis**: 주기/배치 작업 실행(수집, 청킹, 임베딩, RDKit)
- **Supabase(Postgres + pgvector)**: 원본(raw), 스테이징(staging), 정규화(curated), 파생(derived) 저장

### 핵심 흐름(표준)
1) **Connector Fetch** → 2) **Raw 저장** → 3) **Normalize/Upsert(Curated)** →  
4) **Derived Jobs**(청킹/임베딩/RDKit/Polarity) → 5) **검색/스코어링에 사용**

---

## 2. 데이터 레이어 설계: Raw / Staging / Curated / Derived

### 2.1 Raw(원본 보존)
외부 소스의 응답을 그대로 저장하여 **재처리/추적** 가능하게 함.

- `raw_source_records`
  - `id uuid pk`
  - `source text` (pubmed/uniprot/opentargets/chembl/…)
  - `external_id text` (PMID, UniProt ID, ChEMBL ID 등)
  - `payload jsonb` (원본 응답)
  - `fetched_at timestamptz`
  - `checksum text` (변경 감지용)
  - `workspace_id uuid null` (public이면 null, private면 workspace)

### 2.2 Staging(검수 게이트)
자동 수집된 항목을 바로 production 카탈로그에 넣지 않고, **검수/승인**을 거쳐 반영.

- `staging_components`
  - `id uuid pk`
  - `type text` (target/linker/payload/antibody/conjugation)
  - `name text`
  - `canonical_smiles text null`
  - `normalized jsonb` (표준화된 필드)
  - `source jsonb` (provenance: source, url, external_id, fetched_at)
  - `status text` (pending_review/approved/rejected)
  - `review_note text null`
  - `approved_at timestamptz null`

### 2.3 Curated(정규화 카탈로그/메타)
플랫폼이 실제로 쓰는 표준 데이터.

- `component_catalog` (기존 + 보강)
  - `status` (pending_compute/active/failed/deprecated)
  - `properties` 안에 `source`(출처), `external_ids`, `rdkit`(파생치) 포함
- `target_profiles`
  - 표적별 expression/association 등 정형 메타(유전자·단백질 키로 정규화)
- `compound_registry`
  - 화합물 ID 매핑(InChIKey 중심), ChEMBL/PubChem 교차 매핑

### 2.4 Derived(파생 인덱스/특성)
- `literature_documents`, `literature_chunks`, `evidence_signals`(polarity)
- `chunk_embeddings` 또는 `literature_chunks.embedding`(pgvector)
- `component_fingerprints`(RDKit fingerprint 저장, 유사도 검색용)
- `audit_events`(수집/승인/재시도/실패 등 기록)

---

## 3. 커넥터 표준 인터페이스(반드시 공통화)

### 3.1 Connector Contract
각 소스 커넥터는 다음 함수를 동일한 시그니처로 제공:

- `build_queries(seed: dict) -> list[QuerySpec]`
- `fetch_page(query: QuerySpec, cursor: CursorState) -> FetchResult`
- `normalize(record: RawRecord) -> NormalizedRecord`
- `upsert(normalized: list[NormalizedRecord]) -> UpsertResult`
- `emit_jobs(upsert_result: UpsertResult) -> list[JobSpec]`
- `update_cursor(cursor: CursorState, result: FetchResult, upsert: UpsertResult) -> CursorState`

### 3.2 공통 기능(라이브러리)
- **Rate limiter**: source별 QPS 설정
- **Retry 정책**: 429/5xx → max 3회 + exponential backoff(1/2/4초)
- **Circuit breaker(선택)**: 반복 실패 시 일정 시간 정지 후 재개
- **Idempotency**: upsert 기반(동일 외부 ID는 중복 저장 금지)

---

## 4. 증분 업데이트(자동 업데이트) 설계

### 4.1 Cursor 테이블(공통)
소스별 증분 수집 상태를 테이블에 저장해 자동 업데이트 가능하게 함.

- `ingestion_cursors`
  - `id uuid pk`
  - `source text`
  - `query_hash text`
  - `cursor jsonb` (mindate/maxdate/retstart/page_token 등)
  - `last_success_at timestamptz`
  - `stats jsonb` (`fetched`, `new`, `updated`, `errors`)
  - `status text` (idle/running/failed)
  - `unique(source, query_hash)`

> PubMed 전용으로 이미 `literature_ingestion_cursors`를 쓰고 있다면, **통합 테이블로 합치거나** 공통 구조를 맞춰도 됩니다.

### 4.2 스케줄링(권장 기본)
- **PubMed**: 매일 1회(야간), 또는 6시간마다 증분(초기엔 daily 권장)
- **UniProt/OpenTargets/HPA**: 주 1회(메타 변화가 상대적으로 완만)
- **ChEMBL/PubChem**: 주 1~2회(또는 seed 변경 시 on-demand)
- **ClinicalTrials/openFDA**: 주 1회(또는 특정 프로그램만)

> 스케줄은 Arq 워커의 주기 작업(또는 외부 Cron/Cloud Scheduler)로 트리거.

---

## 5. 소스별 수집 전략(“키 없이도 되는 것부터”)

## 5.1 PubMed(NCBI) — 문헌 근거(키 완료)
- **ESearch → EFetch** 파이프라인
- cursor: `last_mindate/last_maxdate`, overlap 1일
- 문헌 저장 후:
  - `chunk`(300~800 tokens) → `embed`(OpenAI) → `polarity`(Evidence Signals) 순으로 파생 job

## 5.2 UniProt — Target 정규화 키(표준 ID)
- seed: UniProt ID 또는 gene symbol
- normalize: `uniprot_id`, protein name, organism, function summary, cross refs
- upsert: `target_profiles` 갱신(변경 감지 checksum)

## 5.3 Open Targets — Target–Disease 연관 스코어
- GraphQL로 필요한 필드만 최소 조회(비용/속도 최적화)
- normalize: association score, evidence count, disease ontology id 등
- 저장: `target_profiles.associations`(jsonb)

## 5.4 HPA — 발현/오프튜머 위험(정형)
- gene/ensembl 기준
- normalize: 조직별/세포별 발현 힌트(정량/등급)
- 저장: `target_profiles.expression`(jsonb)

## 5.5 ChEMBL — 화합물/활성/표적 연결
- seed: payload/linker 후보 키워드 또는 known ids
- normalize: canonical_smiles, inchi_key, assays/activities 요약
- 저장: `compound_registry` + (필요 시) `component_catalog` 후보로 staging 투입

## 5.6 PubChem — 구조/식별자 매핑 보강
- ChEMBL과 중복 제거 및 CID/동의어/기초 물성 보강
- normalize: InChIKey 중심으로 머지(“동일 물질” 판정)

## 5.7 ClinicalTrials.gov — 임상 단계/상태
- seed: target/indication 키워드, 또는 drug name
- 저장: `clinical_programs`(선택) 또는 `target_profiles.clinical`(jsonb)

## 5.8 openFDA — 안전 신호(선택)
- FAERS/라벨에서 독성/경고 신호를 요약
- 저장: `safety_signals`(선택) → Safety-Fit 보정치로 사용

---

## 6. 승인(Review) 기반 자동 반영: “자동 수집 + 사람 승인”의 결합

### 6.1 왜 승인 단계가 필요한가
- 외부 데이터는 표준화/명명/중복이 흔함
- 잘못된 SMILES/동일 화합물 중복은 RDKit/스코어링 품질을 무너뜨림

### 6.2 운영 정책(권장)
- 자동 수집된 신규 항목은 무조건 `staging_components.pending_review`
- 승인 시에만 `component_catalog`로 반영
- 승인 이벤트는 `audit_events`에 기록

### 6.3 승인 자동화(선택)
- 규칙 기반 자동 승인(예: Gold 등급 + SMILES 검증 통과 + 중복 없음)
- 나머지는 수동 승인

---

## 7. 파생 계산 파이프라인(자동 업데이트의 핵심)

### 7.1 RDKit(구조 특성/유사도)
- 대상: `component_catalog` 중 SMILES 보유(linker/payload)
- 상태 머신:
  - pending_compute → (RDKit descriptors + fingerprint) → active
  - 실패 시 failed + 원인 기록
- fingerprint를 저장해 **Tanimoto 유사도 검색** 기반의 구조 매칭 가능

### 7.2 임베딩(문헌 RAG 인덱스)
- 대상: `literature_chunks.embedding_status='pending'`
- OpenAI 임베딩 API를 배치로 호출(레이트리밋 대응)
- 장애 시 degraded mode: BM25-only 검색 가능하도록 구현

### 7.3 Polarity(negative data)
- Evidence Signals 생성:
  - chunk/문헌 요약에서 positive/negative/neutral 태그 부여
  - Risk-first retrieval에 사용(negative 가중치 부스팅)

---

## 8. 운영/관측(Observability)과 장애 대응

### 8.1 표준 로그 필드
- `source`, `query_hash`, `cursor_id`, `workspace_id`, `job_id`, `phase`, `duration_ms`, `result_counts`

### 8.2 알림 트리거(권장)
- 커넥터 실패율 급증(예: 1시간 내 실패 10회)
- Redis 큐 적체(대기 job 수 임계치 초과)
- 임베딩/LLM 429 연속 발생
- Supabase 연결 실패

### 8.3 장애 대응(표준)
- 429/5xx: max 3회 + backoff
- 연속 실패 시: `ingestion_cursors.status='failed'` + 운영자 알림
- 재시도 버튼: Admin UI에서 cursor 단위 재실행

---

## 9. Admin UI(Next.js) 최소 화면(권장)

1) **/admin/connectors**
   - 소스별 상태(최근 성공/실패, last_success_at, 처리량)
   - 실행/중지/재시도 버튼

2) **/admin/staging**
   - staging_components 목록(필터: type/status/source)
   - 승인/거절/메모
   - 중복 후보 묶음 보기(InChIKey 기준)

3) **/admin/ingestion/logs**
   - 최근 job 로그, 오류 코드/스택, 처리량 그래프

---

## 10. 보안/멀티테넌시 정책(요약)
- public 데이터: `workspace_id IS NULL`
- private 데이터: workspace_id 필수 + RLS 강제
- staging도 workspace별로 분리 가능(엔터프라이즈 대응)

---

## 11. 구현 로드맵(자동 수집 우선순위)

### Phase A (2주 내 MVP 자동 수집)
- PubMed 문헌 증분 수집 + 청킹 + 임베딩 + polarity
- UniProt target 보강(정규화 키 확정)
- staging 승인 UI(최소)

### Phase B (추가 2~3주)
- Open Targets + HPA 연결(표적 Bio/Safety 입력 강화)
- ChEMBL/PubChem 연결(구조/활성 데이터 자동 후보화)
- RDKit fingerprint + 유사도 검색

### Phase C (지속)
- ClinicalTrials/openFDA 보강
- 상용 데이터 커넥터(계약 후) 추가

---

## 12. 환경 변수(.env) 확정(자동 수집 포함)

### 필수
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `NCBI_API_KEY`, `NCBI_EMAIL`, `NCBI_TOOL`

### 선택(추후)
- `OPENTARGETS_ENDPOINT`(기본값 사용 가능)
- `CHEMBL_ENDPOINT`(기본값 사용 가능)
- `HPA_ENDPOINT`(기본값 사용 가능)
- `OPENFDA_ENDPOINT`(기본값 사용 가능)

---

## 13. 승인 기준(DoD) — “자동 수집 구축 완료” 정의

- [ ] 커넥터 프레임워크(공통 인터페이스 + 커서 + 재시도) 구현
- [ ] PubMed 증분 수집 E2E: 100편 수집→chunk→embed 성공
- [ ] UniProt 보강: seed 20개에 대해 target_profiles 생성/갱신
- [ ] staging 승인 플로우: pending→approved→component_catalog 반영
- [ ] 관측/로그: source별 처리량/실패율 확인 가능
- [ ] 운영 재시도: cursor 단위 재실행 버튼 제공

---

## 부록 A. “업데이트 때마다 자동 반영” 운영 정책(권장)

- **문헌(PubMed)**: 매일 증분 수집(새 논문/업데이트 반영)
- **정형 메타(UniProt/OpenTargets/HPA)**: 주 1회 갱신 + checksum 변경 시에만 업데이트
- **구조(ChEMBL/PubChem)**: 주 1회 + staging에서 승인된 후보만 카탈로그에 반영
- **승인된 카탈로그**는 RDKit 파생치 자동 갱신(상태 머신 유지)

---

## 부록 B. 위험 관리(핵심 3가지)
1) 외부 API 제한/장애 → **커서/백오프/재시도/중단 후 재개**
2) 데이터 오염(중복/잘못된 구조) → **staging 승인 게이트 + 중복 제거(InChIKey)**
3) 문헌 근거 환각 → **Forced citations + verifier + polarity/충돌 경고**
