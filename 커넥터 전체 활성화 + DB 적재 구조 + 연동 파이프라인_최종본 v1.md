커넥터 전체 활성화 + DB 적재 구조 + 연동 파이프라인 (최종본 v1)

본 문서는 사용자가 제공한 connector executor 분기 코드와, 실제 job 파일 분석 결과(각 커넥터가 쓰는 테이블)를 기준으로 **“각 커넥터의 역할/DB 사용/연동 순서/운영 규칙”**을 최종 확정합니다.
목표는 커넥터들을 모두 활성화하고, DB에 쌓이는 데이터가 어디에 쓰이는지 혼선 없이 운영 가능한 형태로 정리하는 것입니다.

0) 현재 커넥터 실행 구조 (코드 기준)
0.1 Connector Type 분기

connector_type == "api"

PubMed, UniProt, OpenTargets, ClinicalTrials, openFDA

connector_type == "db"

HPA, ChEMBL, PubChem

connector_type == "system"

Seed, Resolve

(별도) Golden Seed(ADC100)

golden_seed_job.py 등으로 별도 커넥터 타입/이름으로 연결되어 있다고 가정 (현재 분석 결과 포함)

1) 공통 운영 테이블 (모든 커넥터에 공통)

“실행/상태/재실행/중복방지”는 커넥터 종류와 무관하게 아래 테이블로 관리됩니다.

1.1 ingestion_logs

역할: 실행 이력 로그 (started/completed/failed, duration, fetched/new/updated 등)

UI 표기: “마지막 실행”, “성공/실패”, “처리량”, “에러”

1.2 ingestion_cursors

역할: 동일 쿼리/동일 시드에 대한 상태/커서(중복 방지/이어받기)

핵심 필드(관찰):

source, query_hash, status(running/idle/failed), stats, error_message, last_success_at

1.3 raw_source_records (대부분의 “외부 API/DB 커넥터”)

역할: 외부에서 가져온 원본 payload 저장(감사/재현/디버깅용)

장점: 파싱/정규화 실패해도 원본이 남아서 복구 가능

2) 커넥터별 역할과 “실제 쓰는 테이블” (최종 확정)

아래는 사용자가 제공한 분석 결과를 그대로 기준으로 확정한 표입니다.

2.1 API 커넥터
(A) PubMed

역할: 문헌 수집 → (청킹) → RAG 데이터 축적

테이블

literature_documents : PMID/제목/초록 등 문헌 메타

literature_chunks : 문헌을 쪼갠 청크

주의

현재 job 설명에 “임베딩” 단계가 언급되지만, DB 사용 분석에는 embedding 테이블이 명시되지 않음

즉, 현재는 “문헌+청크”까지가 확실히 적재되는 구조로 보이며, 임베딩은 별도 파일/테이블이 있거나 아직 미연결일 수 있음

(B) UniProt

역할: 타깃(단백질) 프로필 동기화/보강

테이블

raw_source_records

target_profiles

ingestion_cursors

ingestion_logs

(C) Open Targets

역할: 타깃 관련 정보(질환 연관성 등) 보강 (현재 구조상 target_profiles 업데이트로 귀결)

테이블

raw_source_records

target_profiles

ingestion_cursors

ingestion_logs

중요

일반적으로는 target_disease_associations 같은 별도 테이블이 자연스럽지만,

현재 구현은 target_profiles에 통합 업데이트하는 형태로 보이므로, v1은 이 구조를 기준으로 운영합니다.

(D) ClinicalTrials.gov

역할: 임상시험 데이터 동기화

테이블(확정)

ingestion_cursors

ingestion_logs

추가(코드 주석 기준)

“Connector class”를 통해 clinical_trials에도 적재(또는 업데이트)하는 흐름이 존재

즉, 실질적 도메인 테이블은 clinical_trials가 맞고, 실행 관리는 cursors/logs가 담당

(E) openFDA

역할: 안전/부작용 이벤트(신호) 동기화

테이블(확정)

ingestion_cursors

ingestion_logs

추가(코드 주석 기준)

“Connector class”를 통해 openfda_events(또는 유사)에 적재하는 흐름 존재

2.2 DB 커넥터
(F) HPA (Human Protein Atlas)

역할: 발현/조직 특이성 등 타깃 보강 (현재 구조는 target_profiles 업데이트)

테이블

raw_source_records

target_profiles

ingestion_cursors

ingestion_logs

(G) ChEMBL

역할: 화합물/약물 레지스트리(메타) 동기화

테이블

raw_source_records

compound_registry

ingestion_cursors

ingestion_logs

(H) PubChem

역할: 화합물 속성/ID 동기화

테이블

raw_source_records

compound_registry

ingestion_cursors

ingestion_logs

2.3 SYSTEM 커넥터
(I) Seed Data

역할: 내부 기준/기초 카탈로그 시딩 (Targets/Linkers/Payloads/Antibodies 등)

테이블

component_catalog

(J) Resolve IDs

역할: 카탈로그의 외부 ID 정합성 보강(동일성/매핑)

테이블

component_catalog

2.4 Golden Seed 커넥터 (ADC100)
(K) Golden Seed (ADC100)

역할: “검증용 ADC 후보 100개” 생성 및 저장

테이블

golden_sets : 생성 버전/구성(config)/메타

golden_candidates : 후보(Drug/Target/Antibody/Linker/Payload + score/evidence)

주의(현재 가장 중요한 결론)

현재 Golden Seed 생성은 RAG(PubMed)를 ‘생성 엔진’으로 쓰는 구조가 아니다.

PubMed는 “근거 텍스트 저장용(RAG)”이고,

Golden Seed는 “후보 생성/정규화/게이트/적재” 파이프라인이다.

다만, Golden 후보에 “왜 들어왔는지”를 설명하기 위해 PubMed 기반 evidence를 **후처리(enrichment)**로 붙이는 것은 v1에서도 강력 권장됩니다.

3) “RAG로 Seed를 만들 수 있나?”에 대한 최종 답
3.1 현재 구현 기준 결론

현재 PubMed 파이프라인은 문헌 텍스트를 DB에 쌓는 역할이며,

Golden Seed(ADC100)는 golden_sets / golden_candidates를 채우는 별도 파이프라인입니다.

즉, 현 상태에서는 “RAG가 곧 Seed 생성”이 아닙니다.

3.2 다만, 가능한 확장(권장 아키텍처)

PubMed에 축적된 문헌(chunks/documents)을 사용해:

Golden 후보의 evidence_json을 보강하거나,

golden_candidate_evidence 같은 별도 테이블로 “근거 리스트”를 만들고,

UI에서 Evidence 모달로 보여주는 방식이 가장 현실적인 v1 확장입니다.

4) 커넥터 데이터는 “어디에 쓰이는가” (사용처 매핑)
4.1 component_catalog (Seed/Resolve)

목적: “시스템이 참조할 기준/정규화된 컴포넌트 목록”

사용처:

이후 UniProt batch 모드(카탈로그 기반 동기화)

Golden Seed 구성 요소 표준화(사전/매핑 기준)

설계 단계(나중)에 후보 조합 UI

4.2 target_profiles (UniProt/OpenTargets/HPA)

목적: 타깃의 “기초 프로필+연관성+발현”을 한곳에 축적(현재 v1 구조)

사용처:

타깃 상세 페이지(관리자/사용자)

후보 평가(설계 단계에서 scoring feature로 활용)

4.3 compound_registry (PubChem/ChEMBL)

목적: payload/약물/화합물 메타와 ID(특히 InChIKey/CID 등)

사용처:

payload 표준화

(향후) RDKit 기반 물성/독성/응집성 계산의 입력

4.4 clinical_trials / openfda_events (ClinicalTrials/openFDA)

목적: 임상 단계/안전 신호 보강

사용처:

후보 우선순위(승인/임상 단계 가중치)

리포트/검토 근거

4.5 literature_documents / literature_chunks (PubMed RAG)

목적: 근거 문헌 저장

사용처:

“Evidence 모달”

Golden 후보의 근거 보강(후처리 job)

4.6 golden_sets / golden_candidates (Golden Seed)

목적: “검증용 후보(정답 후보군)” 관리

사용처:

검증 트렌드(모델 평가 기준 데이터셋)

관리자 검토/승인 워크플로우(선택)

5) 전체 활성화 후 “정석 실행 순서” (바로 실행 가능한 운영 플로우)

아래 순서로 실행하면 데이터가 가장 안정적으로 쌓입니다.

Seed(Data) 실행

component_catalog 기본값 확보

Resolve 실행

component_catalog ID 정합성/동일성 보강

UniProt 실행 (batch_mode 권장)

target_profiles 생성/업데이트

OpenTargets 실행

target_profiles 연관성/근거 보강

HPA 실행

target_profiles 발현 보강

PubChem 실행

compound_registry 화합물 ID/속성 보강

ChEMBL 실행

compound_registry 약물/활성 메타 보강

ClinicalTrials 실행

clinical_trials 임상 정보 축적

openFDA 실행

openfda_events 안전 신호 축적

Golden Seed(ADC100) 실행

golden_sets, golden_candidates 생성

PubMed 실행

literature_documents, literature_chunks 축적

(권장 추가) Golden Evidence Enrichment 실행(신규)

golden_candidates 각각에 대해 PubMed 문헌 근거 연결 → Evidence 모달 완성

6) “Golden Seed 생성에 PubMed RAG를 활용하는가?” 최종 정책
v1(권장, 지금 당장)

Golden Seed 생성은 RAG를 직접 사용하지 않는다.

이유:

RAG 텍스트 추출로 구성요소(표적/항체/링커/페이로드)를 “생성”하면 중복/누락/환각이 쉽게 발생

지금 단계의 목표는 안정적으로 100개를 만들고 DB 파이프라인을 고정하는 것

v1에서 RAG의 역할

PubMed는 “근거” 제공용으로 사용:

Golden 후보의 source_ref/evidence_json을 후처리로 보강

UI Evidence 모달에서 “왜 포함됐는지”를 확인

7) 커넥터 활성화(운영 체크리스트)
7.1 활성화 전 확인

각 커넥터의 config에 최소 기본값 존재:

PubMed: query, limit

UniProt: batch_mode 또는 query

OpenTargets/HPA/ChEMBL/PubChem/ClinicalTrials/openFDA: 최소 query/seed 기준

7.2 활성화 후 확인(필수 쿼리)

ingestion_logs에서 source별 최근 실행 성공 여부 확인

ingestion_cursors에서 status가 idle로 복귀했는지 확인

핵심 도메인 테이블 증가 확인:

component_catalog

target_profiles

compound_registry

clinical_trials

openfda_events

golden_candidates

literature_documents, literature_chunks

8) 다음 액션 (지금 바로 해야 하는 순서)

connectors 테이블에서 전체 커넥터 is_active=true 적용

Seed → Resolve 실행 (component_catalog 고정)

UniProt(batch) → OpenTargets → HPA 실행 (target_profiles 채우기)

PubChem → ChEMBL 실행 (compound_registry 채우기)

ClinicalTrials → openFDA 실행

Golden Seed(ADC100) 실행 (golden_candidates 생성)

PubMed 실행 (문헌/청크 축적)

(바로 추가 구현 권장) Golden 후보별 PubMed 근거 매핑 “Evidence Enrichment Job” 추가

그래야 “왜 골든에 들어갔지?”가 UI에서 설명 가능해지고, 시스템이 설득력을 갖습니다.

9) (중요) 현재 문서 기준에서의 정리된 결론

지금 하고 있는 작업은:

Seed(카탈로그) 생성 + 외부 소스 동기화(타깃/화합물/임상/안전) + Golden 후보(ADC100) 생성

어드민이 “골든 시드만 생성하면 되나?”에 대한 답:

운영을 위해서는 최소 component_catalog(Seed/Resolve)와 golden_candidates(Golden Seed)가 함께 필요

외부 커넥터(UniProt/OpenTargets/PubChem/ChEMBL/ClinicalTrials/openFDA)는 “설계/검증 고도화”의 재료를 쌓는 단계