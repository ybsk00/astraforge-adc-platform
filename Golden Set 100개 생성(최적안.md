# Golden Set 100개 생성(최적안) — DB 초기화 + 재구축 + 후보 100개 보장 설계 (MD)

목표
- 기존 DB 데이터를 삭제(초기화)하고 다시 테스트하되,
- “실제로” 매 실행마다 **Golden Set 후보 100개**가 생성되도록
- 후보 단위를 명확히 정의하고(중복 방지 기준 포함),
- Evidence(근거) 조회까지 정상 동작하도록 시스템을 재정렬한다.

핵심 결론(최적안)
- 현재 후보가 8개로 수렴하는 이유는 “약물(조합) 단위 후보”가 실제로 고유 개수가 적기 때문이다.
- **100개를 보장하려면 후보 단위를 ‘Trial(NCT) 단위’로 잡는 것이 가장 현실적이고 재현성도 높다.**
- 즉, Golden Candidate 1개 = ClinicalTrials.gov의 NCT 1건 (또는 NCT + drug_name 조합)

---

## 0) 작업 범위/원칙
- DB는 테스트를 위해 Golden 관련 테이블만 삭제/초기화한다.
- 기존 Seed, Connector Runs 등은 유지할 수도 있으나, 혼선을 막기 위해 “Golden 관련”은 전부 리셋을 권장한다.
- Golden Set은 “버전/묶음”을 갖는다.
- 후보는 “NCT 단위”로 100개를 충족한다.
- Evidence는 Candidate FK를 가진다(고아 evidence 금지).
- Upsert 중복 기준은 **golden_set_id + source_ref(NCT)** 로 고정한다.

---

## 1) 데이터 모델(최적안) — Candidate=Trial(NCT) 단위
### 1.1 테이블: golden_sets (묶음/버전)
- id (uuid, pk)
- dataset_version (text) 기본 'v1'
- status (text) default 'draft'  -- draft/reviewed/promoted/archived
- source (text) default 'clinicaltrials'
- config_json (jsonb)  -- 실행 설정(검색어, 필터 등)
- result_summary_json (jsonb) -- fetched/extracted/passed_gate/upserted
- created_at (timestamptz)

### 1.2 테이블: golden_candidates (후보 100개)
Candidate 1개 = ClinicalTrials Trial 1건(NCT 1건)

- id (uuid, pk)
- golden_set_id (uuid, fk -> golden_sets.id)
- dataset_version (text)
- source (text) = 'clinicaltrials'
- source_ref (text) = NCT ID (예: NCT01234567)
- title (text)  -- trial title
- drug_name (text)  -- 추출된 약물/프로그램명(가능하면)
- target (text)  -- 추출(가능하면)
- antibody (text)  -- 추출(가능하면)
- linker (text)  -- 추출(가능하면)
- payload (text)  -- 추출(가능하면)
- phase (text)  -- Phase 1/2/3/4
- conditions (text[]) -- 질환(가능하면 배열)
- review_status (text) default 'pending'
- created_at (timestamptz)

### 1.3 테이블: golden_candidate_evidence (근거)
- id (uuid, pk)
- candidate_id (uuid, fk -> golden_candidates.id on delete cascade)
- source (text) = 'clinicaltrials'
- ref_id (text) = NCT ID
- url (text)
- snippet (text)
- created_at (timestamptz)

---

## 2) DB 초기화(삭제) + 스키마 재생성 (SQL)
### 2.1 삭제/초기화 (Golden 관련 테이블만)
> 주의: 아래는 “Golden 관련만” 삭제한다. 운영 테이블은 건드리지 않는다.

```sql
-- FK 때문에 evidence 먼저 삭제
drop table if exists public.golden_candidate_evidence cascade;
drop table if exists public.golden_candidates cascade;
drop table if exists public.golden_sets cascade;
2.2 테이블 생성
sql
코드 복사
create table public.golden_sets (
  id uuid primary key default gen_random_uuid(),
  dataset_version text not null default 'v1',
  status text not null default 'draft',
  source text not null default 'clinicaltrials',
  config_json jsonb not null default '{}'::jsonb,
  result_summary_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.golden_candidates (
  id uuid primary key default gen_random_uuid(),
  golden_set_id uuid not null references public.golden_sets(id) on delete cascade,
  dataset_version text not null default 'v1',
  source text not null default 'clinicaltrials',
  source_ref text not null, -- NCT ID
  title text,
  drug_name text,
  target text,
  antibody text,
  linker text,
  payload text,
  phase text,
  conditions text[],
  review_status text not null default 'pending',
  created_at timestamptz not null default now()
);

create table public.golden_candidate_evidence (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null references public.golden_candidates(id) on delete cascade,
  source text not null default 'clinicaltrials',
  ref_id text not null, -- NCT ID
  url text,
  snippet text,
  created_at timestamptz not null default now()
);
2.3 유니크 인덱스(핵심)
후보 중복 방지는 “골든셋 단위”로, “NCT 단위”로 고정한다.

sql
코드 복사
-- 같은 골든셋 안에서 동일 NCT는 1번만 존재
create unique index golden_candidates_unique_trial
on public.golden_candidates (golden_set_id, source, source_ref);

-- evidence는 candidate_id + ref_id 기준으로 중복 방지(선택)
create unique index golden_candidate_evidence_unique
on public.golden_candidate_evidence (candidate_id, source, ref_id);
3) Worker 로직(최적안) — “100개 보장” 전략
3.1 실행 개요
golden_sets 생성 (새 golden_set_id 발급)

ClinicalTrials API에서 Trial 목록 fetched (예: 500~2000건)

Trial 단위로 candidate 생성 후보 풀 구성

Quality Gate 적용(필수는 NCT/URL/Title, 옵션으로 ADC 키워드/phase)

상위 100개 선택

golden_candidates 업서트(유니크: golden_set_id + source_ref)

업서트된 candidate_id 목록 확보

candidate_id에 증거(evidence) insert (FK 기반) — 고아 데이터 금지

golden_sets.result_summary_json 업데이트

3.2 Quality Gate(현실적/100개 확보용)
필수 통과 조건(최소):

source_ref(NCT) 존재

url 존재

title 존재

가점/랭킹:

title/brief_summary에 “antibody-drug conjugate” OR “ADC” OR payload 키워드 포함

Phase 2/3/4 우선

조건(암) 포함 우선

중요: 지금 단계에서는 target/linker/payload 추출이 불완전해도 후보 100개를 먼저 확보한다.
추출은 이후 고도화 가능. (UI에서 “근거 기반 검토”가 먼저)

3.3 업서트 규칙(반드시 고정)
on_conflict: (golden_set_id, source, source_ref)

업데이트: title, phase, conditions, drug_name 등은 최신값으로 update

4) “100개 보장”을 위한 ClinicalTrials 검색 조건(권장)
4.1 검색 쿼리(추천)
질환: cancer OR solid tumor OR lymphoma 등

키워드: “antibody drug conjugate” OR “ADC” OR “vedotin” OR “emtansine” OR “deruxtecan”

최신/활성: Recruiting/Active/Completed (너무 제한하지 말 것)

fetched 목표: 최소 500건 이상

4.2 후보가 부족할 때 자동 확장 로직
1차 쿼리로 100개 미만이면:

필터 완화(phase 조건 제거)

상태 조건 완화

키워드 확장(“conjugate”, “monoclonal antibody”, payload 계열 키워드)

최종적으로 fetched를 1000까지 늘려서 100개 충족

5) Backend/API (UI 조회용)
5.1 목록
GET /api/admin/golden-sets

golden_sets 목록(생성일, status, 후보수(집계), result_summary)

5.2 상세
GET /api/admin/golden-sets/{id}

golden_set 메타 + candidates 100개

5.3 Evidence 모달
GET /api/admin/golden-candidates/{candidateId}/evidence

golden_candidate_evidence 반환

6) 프론트(UI) 동작 정의
6.1 Golden Sets 목록 (/admin/golden-sets)
각 행: created_at / status / candidate_count / fetched / upserted

클릭 시 상세

6.2 상세 (/admin/golden-sets/[id])
candidates 테이블 100개 표시

각 row “근거 보기” 버튼 → Evidence 모달 오픈

review_status(pending/approved/rejected) 변경 가능(선택)

6.3 Seed 승격은 후순위
지금 목표는 “100개 생성 + 근거 확인 + 리뷰 워크플로우”까지로 제한

7) 검증(Verification) 체크리스트
7.1 DB 검증
sql
코드 복사
-- 최신 골든셋 1개 확인
select id, created_at, result_summary_json
from golden_sets
order by created_at desc
limit 1;

-- 해당 셋 candidate count = 100 확인
select golden_set_id, count(*)
from golden_candidates
group by golden_set_id
order by count(*) desc;

-- evidence가 고아 없이 붙는지 확인
select count(*) as orphan_evidence
from golden_candidate_evidence e
left join golden_candidates c on c.id = e.candidate_id
where c.id is null;
기대값:

candidate count = 100

orphan_evidence = 0

7.2 UI 검증
목록에서 최신 셋이 보인다

상세에서 100개가 보인다

“근거 보기” 모달에서 NCT 링크가 열린다

8) 왜 이 방식이 “최적”인가(요약)
ADC 약물(조합) 단위로는 고유 후보 수가 적어 100개를 안정적으로 만들기 어렵다.

Trial(NCT) 단위는 데이터가 충분히 많고, “근거 확인”에도 최적이다.

이후 고도화 단계에서 NCT 기반 후보를 약물/표적/링커/페이로드 단위로 정규화하여
진짜 ADC 조합 후보로 승격시키는 것이 자연스러운 로드맵이다.

9) 다음 단계(추후)
NCT 텍스트에서 drug/target/linker/payload 추출 정확도 향상

동일 drug_name + 구성요소를 묶어 “조합 후보(ADC program)” 엔티티 생성

골든_measurements(측정값) 수집/추가 후 정량 검증(MAE/Spearman)로 확장