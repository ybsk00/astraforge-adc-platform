 target_profiles 통합 타겟 프로필 설계 정리 (Connector Enrichment Spec)

## 0) 목적
`target_profiles`는 **여러 커넥터(UniProt/OpenTargets/HPA 등)** 가 협업하여 하나의 타겟(Target)에 대한 정보를 **점진적으로 보강(Enrichment)** 하는 **통합 저장소**입니다.

- UniProt: 타겟 프로필의 “골격(skeleton)” 생성
- Open Targets: 질병 연관성(associations) 보강
- HPA: 조직/세포 발현(expression) 보강
- (선택) ChEMBL/DrugBank 등: 외부 참조(external_refs) 보강

핵심 원칙은 **필드 소유권(ownership)** 과 **식별자 정규화(id resolution)** 입니다.

---

## 1) 권장 데이터 모델(요약)

### 1.1 핵심 식별자 (Identity)
- `ensembl_id` (가능하면 canonical key)
- `uniprot_id`
- `gene_symbol` (fallback)

> 운영 안정성은 “gene_symbol만으로 매칭하는 비율”을 줄이는 데 달려 있습니다.  
> UniProt 단계에서 가능한 한 `ensembl_id`까지 채워 OT/HPA가 gene_symbol fallback을 거의 사용하지 않도록 만듭니다.

### 1.2 프로필 본문(Enrichment Fields)
- `protein_name` (UniProt)
- `function_summary` (UniProt)
- `external_refs` (UniProt + 추가 커넥터)
- `associations` (Open Targets)
- `expression` (HPA)

### 1.3 메타/출처(Provenance)
- `sources`(jsonb): 커넥터별 fetched_at, endpoint, checksum, version 등
- `*_updated_at`: 커넥터별 최신 갱신 시각 (권장)
- `updated_at`: 레코드 전체 갱신 시각

---

## 2) 커넥터별 역할 정의 (Field Ownership)

### 2.1 UniProt (uniprot_job.py)
**역할**: 프로필 “골격 생성 + 기본 기능정보”
- 생성/업데이트 키: `uniprot_id` (우선), 가능하면 `ensembl_id`도 포함
- 책임 컬럼(업데이트 가능):
  - `uniprot_id`, `gene_symbol`, `protein_name`, `function_summary`, `external_refs`
  - (가능하면) `ensembl_id`
  - `checksum`(raw payload 기준)
  - `sources->uniprot`, `uniprot_updated_at`, `updated_at`

**업데이트 금지 컬럼**:
- `associations` (Open Targets 소유)
- `expression` (HPA 소유)

---

### 2.2 Open Targets (opentargets_fetch_job)
**역할**: 질병-표적 연관성(associations) 보강
- 매칭 키 우선순위:
  1) `ensembl_id`
  2) `gene_symbol` (fallback)
- 책임 컬럼(업데이트 가능):
  - `associations`
  - `sources->opentargets`, `opentargets_updated_at`, `updated_at`

**주의**:
- 새 레코드 생성(INSERT)은 원칙적으로 지양  
  → “UniProt가 뼈대 생성 → OT는 기존 레코드 보강” 흐름을 유지

---

### 2.3 HPA (hpa_fetch_job)
**역할**: 조직/암/세포내 위치/혈액 등 발현정보(expression) 보강
- 매칭 키 우선순위:
  1) `ensembl_id`
  2) `gene_symbol` (fallback)
- 책임 컬럼(업데이트 가능):
  - `expression`
  - `sources->hpa`, `hpa_updated_at`, `updated_at`

**주의**:
- OT와 동일하게, 원칙적으로 “기존 프로필 보강” 전제

---

## 3) 식별자 매칭 규칙 (Id Resolution Rules)

### 3.1 매칭 우선순위(권장)
1. `ensembl_id` = exact match
2. `uniprot_id` = exact match
3. `gene_symbol` = exact match (fallback)

### 3.2 gene_symbol fallback 사용 시 방어 규칙
- 동일 gene_symbol이 다중 레코드에 존재하면:
  - 가장 최근 `uniprot_updated_at`가 있는 레코드 우선
  - 없으면 `uniprot_id`가 있는 레코드 우선
  - 그래도 복수면 **업데이트 스킵 + ingestion_logs에 warning 기록**

> gene_symbol은 변경/동음이의가 존재하므로, fallback에서 “조용히 잘못 업데이트”되는 것이 가장 위험합니다.

---

## 4) 업데이트 정책 (Partial Update + NULL Guard)

### 4.1 NULL 덮어쓰기 방지
커넥터가 가져온 값이 아래에 해당하면 업데이트하지 않습니다.
- `None / NULL`
- 빈 배열 `[]`
- 빈 객체 `{}`

예시:
- Open Targets에서 associations 결과가 비어있으면 기존 associations를 유지
- HPA에서 expression이 비어있으면 기존 expression을 유지

### 4.2 JSON 병합 전략(권장)
- `expression`은 섹션별 병합이 현실적
  - 예: `{tissue:..., cancer:...}` 중 일부만 업데이트될 수 있음
- `associations`도 스냅샷형이라면 “완전치환” 가능
  - 단, empty 방지 규칙을 반드시 유지

---

## 5) Provenance(출처/검증가능성) 설계

### 5.1 sources(jsonb) 권장 구조
```json
{
  "uniprot": {
    "fetched_at": "2026-01-12T10:00:00Z",
    "endpoint": "https://rest.uniprot.org/...",
    "checksum": "md5/sha...",
    "query": "accession:P04626"
  },
  "opentargets": {
    "fetched_at": "2026-01-12T10:05:00Z",
    "endpoint": "https://api.opentargets.org/...",
    "checksum": "..."
  },
  "hpa": {
    "fetched_at": "2026-01-12T10:08:00Z",
    "endpoint": "https://www.proteinatlas.org/...",
    "checksum": "..."
  }
}
5.2 커넥터별 updated_at 권장
uniprot_updated_at

opentargets_updated_at

hpa_updated_at

6) DB 제약/인덱스 권장안
6.1 Unique (권장)
UNIQUE (uniprot_id) — 존재한다면 필수

UNIQUE (ensembl_id) — 가능하면 추가 (canonical key로 사용)

6.2 Index (권장)
INDEX (gene_symbol) — fallback 매칭용

(선택) GIN on associations, expression — 쿼리 패턴이 명확할 때만

7) 실행 순서(오케스트레이션) 규칙
7.1 권장 실행 플로우
Seed 커넥터(seed_fetch_job) 로 component_catalog에 최소 타겟 풀 확보

UniProt: target_profiles skeleton 생성/업데이트

Open Targets: associations 보강

HPA: expression 보강

(선택) ChEMBL/PubChem 등 compound_registry 계열 보강은 별도 파이프라인

7.2 “없으면 생성” 정책
UniProt: 생성 가능(INSERT 허용)

OpenTargets/HPA: 원칙적으로 생성 금지(UPDATE only)
→ skeleton 없는 상태에서 생성하면 identity가 흔들립니다.

8) 테이블 연동 관계(커넥터별 DB Usage)
8.1 공통(상태/감사)
ingestion_logs: 실행 로그/성공/실패/건수/에러 메시지

ingestion_cursors: source + query_hash 기반 상태/재시작 포인트

raw_source_records: 원본 payload 저장(검증/재현성/감사)

8.2 타겟 프로필(통합)
target_profiles: 통합 타겟 프로필(중앙)

8.3 Seed 카탈로그(기초 풀)
component_catalog: target/linker/payload/antibody 기초 목록(Seed)

9) 구현 체크리스트(운영 안정화)
9.1 데이터 품질(Identity)
 UniProt 단계에서 ensembl_id를 가능한 한 채우는가?

 gene_symbol fallback에서 다중 매칭 시 “조용히 업데이트”하지 않는가?

9.2 업데이트 안정성
 NULL/empty 덮어쓰기 방지 로직이 있는가?

 커넥터별로 업데이트 컬럼 범위가 고정되어 있는가?

9.3 관측 가능성
 ingestion_logs에 fetched/new/updated/errors가 기록되는가?

 sources(jsonb)로 fetched_at/checksum/endpoint가 남는가?

10) (권장) 예시 Pseudo SQL / Update Policy
10.1 Open Targets 업데이트(UPDATE only)
sql
코드 복사
UPDATE target_profiles
SET
  associations = :associations,
  sources = jsonb_set(coalesce(sources,'{}'::jsonb), '{opentargets}', :ot_meta::jsonb, true),
  opentargets_updated_at = now(),
  updated_at = now()
WHERE ensembl_id = :ensembl_id;
10.2 HPA 업데이트(부분 병합 예시)
sql
코드 복사
UPDATE target_profiles
SET
  expression = coalesce(expression,'{}'::jsonb) || :expression_patch::jsonb,
  sources = jsonb_set(coalesce(sources,'{}'::jsonb), '{hpa}', :hpa_meta::jsonb, true),
  hpa_updated_at = now(),
  updated_at = now()
WHERE ensembl_id = :ensembl_id;
실제 구현에서는 expression_patch가 빈 객체면 UPDATE를 스킵해야 합니다.

11) 결론: 현재 구조의 “정답 형태”
UniProt이 프로필을 만든다(Insert/Update)

OpenTargets/HPA는 기존 프로필에 “자기 필드만” 붙인다(Update only)

식별자는 ensembl_id > uniprot_id > gene_symbol 순으로 정규화

JSON 필드는 NULL/empty 덮어쓰기 금지 + (필요시) 병합 전략

모든 단계는 ingestion_logs/cursors/raw_source_records로 재현 가능해야 함

