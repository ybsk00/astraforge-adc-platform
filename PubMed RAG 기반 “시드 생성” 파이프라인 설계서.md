# PubMed RAG 기반 “시드 생성” 파이프라인 설계서 (Seed-from-RAG Pipeline)

## 0) 목적 요약
현재 `services/worker/jobs/pubmed_job.py`는 다음을 수행합니다.

- PubMed에서 문헌 수집 → `literature_documents`
- 제목/초록 청킹 → `literature_chunks`
- OpenAI 임베딩 → `literature_chunks.embedding`(또는 별도 테이블)

이 파이프라인은 **RAG용 벡터 인덱스(문헌 지식베이스)**를 구축하는 단계이며,
여기에서 한 단계만 더 추가하면 “ADC 설계/검증에 쓰는 Seed Set(표적/항체/링커/페이로드 목록)”을 **문헌 근거 기반으로 자동 생성**할 수 있습니다.

핵심 아이디어:

> (1) 문헌을 벡터DB에 쌓는다(RAG 인덱스)  
> (2) 특정 쿼리/주제(예: HER2 ADC, TROP2 DXd linker 등)로 벡터 검색한다  
> (3) 검색 결과 텍스트에서 엔티티를 추출/정규화한다  
> (4) 엔티티 테이블/Seed Set으로 적재하고, 근거(evidence)를 연결한다

이 문서는 (2)~(4)를 위한 **Seed-from-RAG Job** 추가 설계입니다.

---

## 1) 전체 파이프라인 아키텍처

### 1.1 Existing (이미 구현됨)
1) `pubmed_fetch_job`
- PubMed ESearch/EFetch로 PMID/제목/초록 수집
- `literature_documents` 저장
- 신규 문서 발생 시 `pubmed_chunk_job` 예약

2) `pubmed_chunk_job`
- 제목+초록을 토큰 기준 300~400으로 분할
- `literature_chunks` 저장
- `pubmed_embed_job` 예약

3) `pubmed_embed_job`
- OpenAI Embeddings로 chunk를 벡터화
- `literature_chunks.embedding` 또는 `literature_embeddings` 저장

### 1.2 New (이번에 추가할 단계)
4) `rag_seed_query_job` (신규)
- “Seed Query Set”을 입력으로 받아 벡터DB에서 top-k 검색
- 검색 결과 chunk를 모아 후보 엔티티(표적/항체/링커/페이로드/약물명)를 추출
- 엔티티 테이블에 upsert + 근거(evidence) 연결
- “Seed Set” 레코드로 묶어 저장(버전/상태 포함)

---

## 2) 데이터 모델(ERD) 확장안

### 2.1 Existing 테이블(가정)
- `literature_documents`
  - id, pmid, title, abstract, journal, year, fetched_at, raw_json …
- `literature_chunks`
  - id, document_id(FK), chunk_index, text, token_count, embedding(vector), created_at …

> embedding 저장 위치가 별도 테이블이라면, seed job에서 “chunk text + embedding”을 조인할 수 있도록 키만 맞추면 됩니다.

### 2.2 New 테이블(Seed 생성 및 근거 연결)

#### A) Seed Query Set (RAG 검색 입력 묶음)
```sql
create table if not exists seed_query_sets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  status text not null default 'active', -- active/archived
  created_at timestamptz not null default now()
);

create table if not exists seed_queries (
  id uuid primary key default gen_random_uuid(),
  seed_query_set_id uuid not null references seed_query_sets(id) on delete cascade,
  query_text text not null,     -- 예: "HER2 antibody-drug conjugate linker payload"
  top_k int not null default 50,
  min_score numeric not null default 0.0,
  created_at timestamptz not null default now()
);
B) 엔티티 테이블(최소 버전; 이미 있으면 재사용)
프로젝트에 entity_targets, entity_drugs, entity_linkers, entity_payloads가 이미 존재한다면 그대로 사용하세요. 없다면 아래 최소안으로 시작합니다.

sql
코드 복사
create table if not exists entity_targets (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_antibodies (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_linkers (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  linker_type text,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_payloads (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  payload_class text,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_drugs (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);
C) “Seed Set” (운영에 쓰는 묶음) + 구성요소 연결
sql
코드 복사
create table if not exists seed_sets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  version text not null,
  status text not null default 'draft', -- draft/active/archived
  source text not null default 'rag',   -- rag/manual/golden_promoted 등
  seed_query_set_id uuid references seed_query_sets(id),
  created_at timestamptz not null default now(),
  unique(name, version)
);

-- Seed Set 구성요소(간단화: JSON으로 시작 → 이후 관계형 확장 가능)
create table if not exists seed_set_items (
  id uuid primary key default gen_random_uuid(),
  seed_set_id uuid not null references seed_sets(id) on delete cascade,
  target_id uuid references entity_targets(id),
  antibody_id uuid references entity_antibodies(id),
  linker_id uuid references entity_linkers(id),
  payload_id uuid references entity_payloads(id),
  drug_id uuid references entity_drugs(id),
  confidence_score int not null default 0,
  evidence_count int not null default 0,
  created_at timestamptz not null default now()
);

-- 중복 방지(동일 seed_set 내 동일 조합)
create unique index if not exists seed_set_items_unique_key
on seed_set_items (seed_set_id, target_id, antibody_id, linker_id, payload_id, drug_id);
D) Evidence (근거 연결)
sql
코드 복사
create table if not exists entity_evidence (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null,     -- target/antibody/linker/payload/drug/seed_item
  entity_id uuid not null,
  source text not null,          -- PubMed
  ref_id text not null,          -- PMID
  chunk_id uuid references literature_chunks(id),
  snippet text,
  created_at timestamptz not null default now()
);

-- 중복 방지
create unique index if not exists entity_evidence_unique_key
on entity_evidence (entity_type, entity_id, source, ref_id, chunk_id);
3) Seed-from-RAG Job 설계
3.1 Job 이름/파일
[NEW] services/worker/jobs/rag_seed_job.py

역할: “벡터DB 검색 → 엔티티 추출/정규화 → seed_sets/seed_set_items 생성 → evidence 연결”

3.2 입력(Config)
json
코드 복사
{
  "seed_query_set_id": "<uuid>",
  "seed_set_name": "ADC_RAG_SEEDS",
  "seed_set_version": "v1-<timestamp>",
  "target_count": 100,

  "retrieval": {
    "top_k_default": 50,
    "max_chunks_total": 3000,
    "min_similarity": 0.25,
    "dedup_by_pmid": true
  },

  "extraction": {
    "mode": "rules",              // rules | hybrid_llm
    "rules": {
      "target_dictionary": true,
      "payload_dictionary": true,
      "linker_dictionary": true,
      "antibody_patterns": true
    },
    "llm": {
      "enabled": false,
      "model": "gpt-4.1-mini",
      "only_when_ambiguous": true
    }
  },

  "scoring": {
    "base": 20,
    "has_target": 20,
    "has_payload": 20,
    "has_linker": 20,
    "has_antibody": 10,
    "evidence_per_chunk": 5,
    "max_score": 100
  }
}
“챗봇이 없다”면 extraction.mode=rules로 시작하는 것이 가장 안전합니다.
LLM은 ‘애매한 케이스만 보강’ 옵션으로 두는 것을 권장합니다.

4) Retrieval(벡터 검색) 구현 가이드
4.1 검색 쿼리 실행 방식
seed_queries를 읽어 각 query_text로 embedding을 만든 뒤,

pgvector에서 cosine/inner-product로 top-k chunk를 검색합니다.

4.2 Supabase pgvector 예시(개념)
literature_chunks.embedding이 vector일 때:

sql
코드 복사
select
  c.id as chunk_id,
  d.pmid,
  c.text,
  1 - (c.embedding <=> :query_embedding) as similarity
from literature_chunks c
join literature_documents d on d.id = c.document_id
where c.embedding is not null
order by c.embedding <=> :query_embedding
limit :top_k;
4.3 Dedup 정책(권장)
dedup_by_pmid=true이면, 같은 PMID에서 너무 많은 chunk가 나오지 않게 cap 적용

예: PMID당 최대 3개 chunk만 사용

5) Extraction(엔티티 추출/정규화) 구현 가이드
5.1 Rules 기반 추출(권장 v1)
Target: TARGET_DICTIONARY + 정규식(HER2/HER3/TROP2/EGFR/BCMA/CD19/CD22/CD30/CD33/Nectin-4 등)

Payload: PAYLOAD_DICTIONARY(MMAE/DM1/DM4/DXd/SN-38/Calicheamicin 등)

Linker: LINKER_DICTIONARY(VC/SMCC/GGFG/Hydrazone/Disulfide 등)

Antibody: 약물명 패턴(“trastuzumab”, “patritumab” 등) + 사전

핵심: 문헌 chunk에서 엔티티를 찾으면 “표준명(정규화된 name)”로 변환한 뒤 저장합니다.

5.2 Hybrid LLM 보강(옵션)
규칙이 Unknown인 경우에만, chunk 텍스트를 LLM에 보내

{target, antibody, linker, payload, drug_name} 구조화 JSON으로 추출

단, 비용/일관성 문제가 있으니 v1은 rules-only 권장

6) Scoring + Seed Set 100개 선정 로직(중요)
6.1 점수 계산
엔티티가 채워질수록 점수 상승

evidence(근거 chunk 수, PMID 수) 많을수록 점수 상승

최종 score 0~100

6.2 “100개”를 안정적으로 만드는 기준(권장)
후보 단위는 seed_set_items(조합)입니다.

동일 조합 중복은 유니크 인덱스로 방지됩니다.

top-score 순으로 채우되, 다양성 캡을 적용합니다.

target별 최대 10개

payload별 최대 20개

linker별 최대 30개

이렇게 해야 특정 payload(예: MMAE)만 과도하게 몰리는 현상을 방지합니다.

7) Evidence 연결 방식(필수)
7.1 무엇을 Evidence로 남기나
최소: entity_evidence에

entity_type(예: payload)

entity_id(예: MMAE)

ref_id(= PMID)

chunk_id

snippet(해당 chunk에서 엔티티가 나온 문장 일부)

7.2 UI에서 “왜 들어왔지?”를 바로 설명 가능
Seed Item 상세에서:

연결된 Evidence 리스트(PMID, chunk snippet) 표시

클릭 시 원문(제목/초록) 표시

8) Worker/Queue 연결(Connector Runs 방식)
8.1 connectors 테이블에 새로운 커넥터 등록(권장)
RAG_SEED_FROM_PUBMED 커넥터 추가

Run 버튼 → connector_runs에 queued 생성

워커가 status=queued를 가져가 rag_seed_query_job 실행

8.2 result_summary 표준(필수)
실행이 “정상인지”는 아래 통계가 있어야 판단됩니다.

json
코드 복사
{
  "retrieval": { "queries": 20, "chunks_total": 800, "unique_pmids": 240 },
  "extraction": { "targets": 35, "payloads": 12, "linkers": 9, "antibodies": 18 },
  "seed_set": { "items_created": 100, "items_updated": 0 },
  "evidence": { "rows_inserted": 560 }
}
9) 구현 파일 변경 목록(요약)
[NEW]
services/worker/jobs/rag_seed_job.py

migrations/012_add_seed_query_sets.sql (seed_query_sets, seed_queries, seed_sets, seed_set_items, entity_evidence 등)

[MODIFY]
services/worker/worker.py

잡 레지스트리에 rag_seed_query_job 등록

services/worker/connector_executor.py

connector type이 RAG_SEED_FROM_PUBMED일 때 rag_seed_job 호출

(선택) Admin UI

/admin/seeds에 “RAG Seed Sets” 탭 추가

seed_query_sets 관리 UI(쿼리 추가/활성화)

10) 검증(Verification) SQL
10.1 Seed Set 100개 생성 확인
sql
코드 복사
select s.name, s.version, count(i.*) as items
from seed_sets s
join seed_set_items i on i.seed_set_id = s.id
where s.source = 'rag'
group by s.name, s.version
order by s.created_at desc
limit 5;
10.2 Evidence 연결 확인
sql
코드 복사
select entity_type, count(*) as rows
from entity_evidence
group by entity_type
order by rows desc;
10.3 다양성 확인
sql
코드 복사
-- target 다양성
select count(distinct t.name)
from seed_set_items i
join entity_targets t on t.id = i.target_id
where i.seed_set_id = '<seed_set_id>';

-- payload 분포 상위 10
select p.name, count(*) 
from seed_set_items i
join entity_payloads p on p.id = i.payload_id
where i.seed_set_id = '<seed_set_id>'
group by p.name
order by count(*) desc
limit 10;
11) 운영 권장 순서(가장 효율적)
PubMed RAG 인덱스 구축(pubmed_fetch/chunk/embed)을 “넓게” 확보

쿼리: ADC, antibody-drug conjugate, linker, payload, DAR 등

seed_query_sets를 “표적/기술축 중심”으로 20~50개 구성

rag_seed_query_job 실행 → Seed Set 100 생성

UI에서 evidence 모달로 검토/승격(필요 시)

결론
현재 파이프라인은 “문헌 RAG 인덱스(문헌 시드셋)”을 만드는 단계입니다.

여기에 rag_seed_query_job을 추가하면,

벡터 검색 결과를 근거로

표적/항체/링커/페이로드 엔티티를 자동 생성하고

Seed Set 100을 근거 연결까지 포함해 자동 적재할 수 있습니다.

원하시면 다음 단계로, 귀 프로젝트의 실제 테이블명/컬럼명(literature_chunks에 embedding 컬럼이 있는지 등)을 기준으로

rag_seed_job.py의 “실제 실행 가능한 코드 골격”

지금 기본 쿼리 하나로는 항상 비슷한 문헌만 반복적으로 상위에 걸리고, 결과적으로 “새 문헌/새 엔티티”가 잘 늘지 않습니다. 특히 ADC는 표현이 다양해서 “ADC therapy” 같은 범용 쿼리는 노이즈도 많고 다양성도 떨어집니다.
따라서 기본 쿼리는 (1) 쿼리 로테이션, (2) 구조적 쿼리(표적/페이로드/링커 축), (3) 날짜/정렬/필터, (4) 중복 방지용 query_hash 설계까지 같이 보강하는 것이 정석입니다.

아래는 바로 적용 가능한 개선안입니다.

1) 문제점 진단

현재:

query = seed.get("query", "") or "antibody drug conjugate OR ADC therapy OR targeted drug delivery"
query_hash = md5(f"pubmed:{query}:{str(seed)}")[:16]

문제 1: 쿼리 다양성이 없음

같은 기본 쿼리 → PubMed는 항상 비슷한 “ADC general review” 상위 논문 위주로 반환

new=0이 반복되기 쉬움(이미 저장된 PMID 반복)

문제 2: 용어가 너무 broad/모호

“targeted drug delivery”는 ADC뿐 아니라 나노입자/리포좀 등 광범위 분야가 포함됨 → 노이즈 증가

문제 3: seed dict 전체를 hash에 넣는 구조는 재현성이 떨어질 수 있음

str(seed)는 키 순서/포맷에 따라 달라질 수 있고, 불필요한 값이 들어가서 쿼리 캐싱/중복 제어가 불안정해질 수 있음

2) 추천안: “기본 쿼리 1개”가 아니라 “쿼리 세트 + 로테이션”
2.1 최소 쿼리 세트(권장 12~20개)

아래는 **ADC 엔티티(seed 생성)**에 직접 도움이 되는 축으로 구성한 예시입니다.

A. ADC 핵심 용어(정밀)

"antibody-drug conjugate"[Title/Abstract] OR "antibody drug conjugate"[Title/Abstract] OR ADC[Title/Abstract]

B. Payload 축(다양성 확보)

(MMAE OR "monomethyl auristatin E" OR MMAF OR DM1 OR DM4 OR DXd OR "deruxtecan" OR "SN-38" OR calicheamicin)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

C. Linker 축

(valine-citrulline OR VC OR SMCC OR maleimide OR hydrazone OR disulfide OR GGFG)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

D. Target 축(대표 표적을 로테이션)

(HER2 OR ERBB2)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(HER3 OR ERBB3)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(TROP2 OR TACSTD2)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(EGFR)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(BCMA OR TNFRSF17)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(CD19 OR CD22 OR CD79b OR CD30)[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(Nectin-4 OR "NECTIN4")[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

E. 임상/안전/제조 축(설계/검증에 도움)

(DAR OR "drug-to-antibody ratio")[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(aggregation OR stability OR "CMC")[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

(toxic* OR safety OR "bystander effect")[Title/Abstract] AND ("antibody-drug conjugate" OR ADC)[Title/Abstract]

포인트: 단순 “ADC therapy”가 아니라, payload/linker/target 키워드가 포함된 쿼리가 seed 다양성을 크게 올립니다.

3) 추천 구현(코드 패턴)
3.1 seed에 query가 없으면 “로테이션 세트”에서 선택

run_id 또는 timestamp 기반으로 항상 달라지게 선택

또는 매 실행 시 여러 쿼리를 묶어서 실행(권장)

DEFAULT_QUERIES = [
  '"antibody-drug conjugate"[Title/Abstract] OR "antibody drug conjugate"[Title/Abstract] OR ADC[Title/Abstract]',
  '(MMAE OR MMAF OR DM1 OR DM4 OR DXd OR deruxtecan OR "SN-38" OR calicheamicin)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(valine-citrulline OR VC OR SMCC OR hydrazone OR disulfide OR GGFG)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(HER2 OR ERBB2)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(HER3 OR ERBB3)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(TROP2 OR TACSTD2)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(Nectin-4 OR NECTIN4)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(BCMA OR TNFRSF17)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(DAR OR "drug-to-antibody ratio")[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
  '(aggregation OR stability OR CMC)[Title/Abstract] AND ("antibody-drug conjugate"[Title/Abstract] OR ADC[Title/Abstract])',
]

def pick_queries(seed: dict, run_id: str, max_q: int = 3):
    if seed.get("query"):
        return [seed["query"]]
    # run_id 기반 로테이션(항상 변동)
    idx = int(hashlib.md5(run_id.encode()).hexdigest(), 16)
    qs = []
    for i in range(max_q):
        qs.append(DEFAULT_QUERIES[(idx + i) % len(DEFAULT_QUERIES)])
    return qs

3.2 query_hash는 “정렬된 최소 정보”로 만들기

str(seed) 대신 필요한 필드만 canonical JSON으로:

def make_query_hash(queries: list[str], extra: dict):
    payload = {
        "queries": queries,
        "filters": extra.get("filters", {}),
        "date_from": extra.get("date_from"),
        "date_to": extra.get("date_to"),
        "retmax": extra.get("retmax"),
        "sort": extra.get("sort"),
    }
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(f"pubmed:{s}".encode()).hexdigest()[:16]


이렇게 하면 “같은 조건이면 같은 해시”가 보장되어 중복 제어가 쉬워집니다.

4) 날짜 필터/정렬도 같이 넣어야 “새 문헌”이 들어옵니다

기본적으로 PubMed는 관련성/최신순 등으로 결과가 편향됩니다. “새 문헌”을 꾸준히 가져오려면:

최근 1년(또는 6개월) 제한을 두거나

매 실행 시 date window를 이동하는 방식이 필요합니다.

권장:

초기 대량 수집: 2015~현재(넓게)

운영 업데이트: 최근 30~90일만(새 것만)

5) 결론(가장 실용적 권장안)

기본 쿼리 1개는 반드시 보강해야 합니다.

최소한:

payload/linker/target 축 쿼리 세트 10~20개

run_id 기반 로테이션(매 실행 다른 쿼리)

query_hash를 canonical JSON 기반으로

최근 기간 필터(운영 모드)

이 4가지만 적용해도 “항상 같은 PMID만” 가져오는 현상이 크게 줄어듭니다.
