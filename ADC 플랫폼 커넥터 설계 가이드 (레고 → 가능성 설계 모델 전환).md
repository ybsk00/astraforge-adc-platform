# ADC 플랫폼 커넥터 설계 가이드 (레고 → 가능성 설계 모델 전환)

## 배경
기존에는 `ADC 관련 키워드` 중심으로 좁게 수집하여 “레고 조립”처럼 보이는 문제가 있었습니다.  
이제는 **표적(Target) 중심으로 후보물질 가능성 공간을 넓게 수집**하고, 근거(Evidence)와 정규화(Resolver), 계산(RDKit)로 수렴시키는 **설계 엔진(Design Engine)** 모델로 전환합니다.

현재 UI 기준으로 대부분 커넥터는 성공하나,
- `ClinicalTrials.gov`, `openFDA`는 `No module named 'app'`로 실패하여
먼저 **실행 환경/패키징 표준화**가 필요합니다.

---

## 0. 핵심 전략 요약 (Candidate-first, Target-driven, Evidence-attached)

### 목표 전환
- 과거: `ADC 키워드` 중심 → 데이터 부족/노이즈
- 현재: **표적(50개) 중심으로 후보물질을 넓게 수집** → 이후 엔진이 수렴

### 3단계 파이프라인
1) **Target Anchor(표적 고정)**  
   - 50개 표적(솔리드 25 + 헤마 25)을 Seed로 고정
2) **Candidate Pool 확장(넓게 수집)**  
   - 표적과 연결 가능한 payload/linker 후보군, 프로그램(임상), 근거(문헌), 구조/물성(화학DB) 확장
3) **Convergence(수렴/추천)**  
   - Evidence + RDKit 계산 + 규칙/스코어링으로 최종 후보 정렬/추천

> 커넥터는 “정답 생성기”가 아니라 “후보군 + 근거 + 메타데이터 축적기”로 설계한다.

---

## 1. 최우선: ClinicalTrials/openFDA 실패 원인 해결 (No module named 'app')

### 증상
- UI에서 ClinicalTrials.gov / openFDA만 실패
- 에러: `No module named 'app'`

### 원인(빈도 높은 케이스)
- 워커 실행 컨텍스트(Working dir / PYTHONPATH)가 커넥터마다 다름
- `from app...` 형태 import가 job 실행 시점에 루트 패키지를 못 찾음
- Docker 이미지/WORKDIR 변경으로 루트 경로가 깨짐

### 권장 해결 패턴(재발 방지)
- “각 job에서 sys.path 조작”을 늘리지 말고
- **워커 진입점 1곳에서**
  - 패키지를 `pip install -e .`로 설치하거나
  - PYTHONPATH를 프로젝트 루트로 강제
- 커넥터 확장 전 반드시 해결(운영 안정성/확장성 필수)

---

## 2. 커넥터 공통 설계 규격(필수 표준)

### (1) QueryProfile 도입
목적별로 수집 정의를 고정한다.
- 예: `target_enrichment`, `payload_discovery`, `linker_discovery`, `tox_risk`, `bystander_risk`

### (2) 입력 스키마 통일
- 최소: `target_id/gene_symbol/synonyms`
- 선택: `cancer_type`, `constraints`(solid only 등)

### (3) RAW 저장(필수)
- 외부 수집은 반드시 `*_raw` 테이블에 저장
- `source_hash` 기반 중복 방지

### (4) 정규화/매핑(Resolver) 분리
- 수집기: “텍스트/ID 후보”만 생성
- Resolver: canonical 매핑, confidence 산출, 캐시 저장

### (5) Evidence 첨부 강제
- 후보군/추론 결과는 반드시 `evidence_refs`(NCT/PMID/ChEMBL ID 등) 포함

### (6) 운영 제어(필수)
- rate limit, retry/backoff, circuit breaker
- per_target_limit, timebox(표적당 N초)

---

## 3. 커넥터별 역할 및 설계(무엇을 넓히고, 어떻게 수렴시키는가)

### A. Seed Data (System)
**역할**: 표준 사전 + 표적 앵커(50개)의 “단일 진실 소스”
- 확장(넓히기)보다 정확성/정규화에 집중
- `component_catalog`를 강하게 만들수록 이후 노이즈가 줄어듦

**출력**
- `component_catalog` (target/antibody/linker/payload)
- target: gene_symbol, canonical_name, synonyms, external_refs 필수
- payload/linker: 최소 “패밀리 수준”부터 시작(vedotin/DXd/DM1/SN-38 등)

---

### B. Resolve IDs (System)
**역할**: 노이즈 → 엔티티로 바꾸는 핵심 엔진
- synonyms/canonical 기반 매핑 1순위
- external_refs(PubChem/ChEMBL)도 키로 사용
- confidence 낮으면 `review_queue`로 분기

**출력**
- `mapping_table`(캐시), mapping_confidence
- (선택) golden_candidates/target_profiles에 canonical_id 연결

---

### C. ClinicalTrials.gov (Clinical)
**역할**: 표적별 임상 프로그램 풀 생성(ADC만이 아닌 “표적 관련 후보 풀”)
- ADC 키워드 의존 X
- -mab 의존 X (코드명 MK2870 등 존재)

**QueryProfile 예시**
- `target_enrichment`:
  - `(TARGET OR SYNONYMS) AND oncology_terms`
- `adc_signal_boost`(우선순위만 가중):
  - 위 쿼리에 `deruxtecan|vedotin|govitecan|ozogamicin|soravtansine|conjugate` 를 OR로 추가

**출력**
- RAW: `golden_seed_raw` (query_target, query_profile, raw_payload)
- Candidate: 프로그램명/코드명 텍스트 후보 + NCT evidence

**운영**
- 표적 1개씩 실행(per_target_limit)
- 중복: `(source, source_hash)` unique

---

### D. PubMed (Literature)
**역할**: 후보물질의 “근거(evidence)”를 생산
- 후보 자체보다 evidence 생성이 핵심
- 신규 payload(PROTAC, 면역활성 payload 등)도 “근거 기반 후보군”으로 흡수 가능

**QueryProfile 예시**
- `payload_discovery`:
  - `"TARGET" AND (payload OR warhead OR cytotoxic OR toxin OR PROTAC OR immune agonist) AND (conjugate OR ADC OR antibody)`
- `linker_discovery`:
  - `"TARGET" AND (cleavable linker OR non-cleavable OR valine-citrulline OR hydrazone OR disulfide)`
- `bystander_risk`:
  - `"payload_name" AND bystander AND ADC`
- `tox_risk`:
  - `"payload_name" AND (toxicity OR neutropenia OR ILD OR hepatotoxicity)`

**출력**
- `literature_raw`, `evidence_snippets`(PMID, excerpt, score)
- payload/linker 후보군(candidate list) + evidence_refs

---

### E. UniProt (Target)
**역할**: 표적의 기초 생물학(기능/도메인/세포외부/발현/내재화 힌트)
- ADC 적합성 “결정”이 아니라 feature로 저장

**출력**
- `target_profiles` 확장(기능 요약, 단백질 특징, external_refs)

---

### F. Open Targets (Target-Disease)
**역할**: 표적-질환 연관성/근거를 통해 “암종 우선순위” 제공
- 임상/문헌 쿼리에서 cancer_type 우선순위에 반영 가능

**출력**
- `target_profiles.associations` (질환, 점수, 근거 링크)

---

### G. Human Protein Atlas (Expression)
**역할**: 정상조직 발현 기반의 리스크 힌트 생성
- 성공 예측이 아니라 “리스크 레지스터 입력” 역할

**출력**
- `target_profiles.expression` + risk hints

---

### H. ChEMBL (Compound/Drug)
**역할**: payload 후보군의 약물성/기전/참조 보강
- ADC payload는 누락 가능 → payload family 사전과 결합 필요

**QueryProfile 예시**
- `payload_family_expand`:
  - MMAE/MMAF/DM1/DXd/SN-38/calicheamicin 등 패밀리 중심 확장
- `mechanism_expand`:
  - tubulin inhibitor / topoisomerase I inhibitor 등 기전 기반 확장

**출력**
- `component_catalog(payload)`의 external_refs, mechanism, references 보강
- (선택) `compound_profiles`(properties/assays)

---

### I. PubChem (Compound)
**역할**: SMILES/구조/물성 확보(RDKit 계산 전 필수)
- payload 후보가 확정 또는 준확정되면 lookup
- 실패 시 review_queue로 보내고 후보군 유지

**출력**
- `component_catalog.smiles`, `compound_properties`(MW, logP 등)

---

### J. openFDA (Safety)
**역할**: 실제 안전성 신호의 정량 힌트
- 신규 ADC/코드명은 매칭이 어려울 수 있음
- MVP에서는 승인/대표 payload 계열 중심으로 제한 권장

**QueryProfile 예시**
- `approved_payload_safety`:
  - DXd 관련 제품명/성분명 기반 AE 신호 수집(가능한 범위)

**출력**
- `safety_signals`(drug_name, top AEs, evidence)

---

## 4. 확장(Recall)과 정제(Precision)의 분리 운영

### 확장 담당(넓게 수집)
- ClinicalTrials, PubMed, ChEMBL
- 원칙: RAW + Evidence를 최대한 많이 쌓는다

### 정제 담당(노이즈 통제)
- Resolve IDs + Admin Review Queue
- 원칙: 자동 승격보다 “검수 우선순위”를 제공한다

### 수렴 담당(추천/정렬)
- RDKit Features + Recommendation Job
- 원칙: 계산/정책(스코어링)으로 정렬하고 설명 가능해야 한다

---

## 5. 운영 모델(표적 1개씩 DB 채우기)
1) Admin에서 표적 선택(HER2 등)
2) `target_enrichment` 런 실행
   - ClinicalTrials → RAW 축적
   - PubMed → payload/linker 후보 + 근거 축적
   - UniProt/OT/HPA → target profile 완성
   - PubChem/ChEMBL → SMILES/물성/기전 보강(가능한 범위)
3) Admin Review Queue에서 확정(승격)
   - Golden Set 50~100개를 “표적별”로 완성

---

## 6. 즉시 실행 가능한 다음 조치(권장 순서)
1) ClinicalTrials/openFDA의 `No module named app` 해결(패키징/PYTHONPATH 표준화)
2) 최소 QueryProfile 3종 정의 및 적용
   - `target_enrichment` (ClinicalTrials)
   - `payload_discovery`, `linker_discovery` (PubMed)
   - `payload_smiles_enrichment` (PubChem)
3) 모든 결과를 RAW + evidence로 저장
4) 표적 10개로 파일럿 → 기준 확정 후 50개로 확장

---

## 결론
커넥터를 “ADC만 찾는 좁은 검색기”에서
**표적 중심 후보군 + 근거 축적 시스템**으로 재설계하면,
플랫폼은 레고 조립이 아니라 **가능성 설계(Design Engine)**로 보이게 됩니다.
