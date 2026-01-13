# Golden Set 작업 가이드 — 관련 파일 역할 정리 및 수정 방향
버전: v1.0  
작성일: 2026-01-13  
목적: 현재 존재하는 Golden Set 관련 Python 파일들의 **역할(Responsibility)·데이터 흐름·수정 포인트**를 명확히 정의하고, “레고형 Seed”가 아니라 **정답(레퍼런스) 기반 검증/추천 엔진**으로 확장하기 위한 개발 기준을 제공한다.

---

## 1) Golden Set의 재정의(핵심 방향)
### 1.1 기존 인상(문제)
- Seed/Golden Seed가 “부품 카탈로그 + 조합 생성”처럼 보이면 외부에서는 **짜집기(레고)**로 인식됨.
- “정답 데이터”가 단순 정적 리스트(Approved/Clinical)로만 남아 있으면, 시스템은 **엔진(예측/추천/검증)**이 아니라 **DB 채우기**로 보임.

### 1.2 목표(수정 방향)
Golden Set은 “부품 목록”이 아니라 다음을 포함하는 **레퍼런스 케이스북(정답지)** 이다.
- (암종/바이오마커/항체/링커/페이로드) 조합 레퍼런스
- 성과/리스크 레이블(성공/실패/독성/CMC/응집 등)
- 측정값(예: IC50, DAR 범위, release 조건 등 가능한 범위)
- 근거 링크(임상/전임상/문헌)
- 시스템 추천/예측과의 일치도 평가(Validator)

즉, Seed는 “생성”이고 Validator는 “정답지로서 유효성/정확도 검증”이다.

---

## 2) 파일별 역할(현재)과 권장 책임 경계(To-Be)
아래는 사용자가 정리한 파일들을 기준으로, **현재 역할(As-Is)**과 **수정 후 역할(To-Be)**를 정리한 표이다.

### 2.1 데이터 시딩(생성 및 적재)
#### A) `services/engine/seed_golden_data.py`
- As-Is
  - 초기 버전(모태). 골든 데이터의 기본 구조/적재 방식이 들어있을 가능성이 높음.
- To-Be
  - **레거시(참조용)**로 격하하거나, v2/v3 공통 로직만 분리해 **공용 라이브러리**로 전환
  - 권장: `seed_lib.py` 같은 모듈로 “DB insert/upsert/merge” 공통 함수만 남기고, 실사용 엔트리포인트는 v2/v3 또는 unified CLI로 이동

#### B) `services/engine/seed_golden_data_v2.py` (Approved 정적 데이터)
- As-Is
  - 승인(Approved) 기반 정적 데이터 시딩
- To-Be
  - Approved는 “정답 레퍼런스”로 유용하나, **링커/페이로드/항체/타겟 매핑이 canonical하게 저장**되어야 함
  - 필수 개선:
    - canonical entity 매핑(antibody/linker/payload) 실패 시 “휴리스틱 문자열 저장” 금지
    - component_catalog와 **강제 연결(외부 ID or canonical_name)** 하도록 변경
    - evidence_refs(근거 링크/출처) 필드 포함

#### C) `services/engine/seed_golden_data_v3.py` (Clinical 정적 데이터)
- As-Is
  - 임상 단계(Clinical) 기반 정적 데이터 시딩
- To-Be
  - Clinical은 변동성이 있으므로 “정적 데이터” 형태로 유지하되,
  - “정적 시드”는 최소한의 레퍼런스만 제공하고,
  - **변동 데이터는 golden_seed_job(동적 수집)에서 raw로 수집 → 검증 후 final로 승격**하는 구조로 이동

#### D) `services/worker/jobs/golden_seed_job.py` (동적 수집 워커)
- As-Is
  - 외부에서 데이터를 긁어오는 동적 수집(예: ClinicalTrials 기반 후보 추출로 보임)
- To-Be
  - 책임을 명확히 분리:
    1) **RAW 수집(전량 저장)**: 수집한 원천 데이터를 가공 최소화로 저장
    2) **정규화/매핑**: component_catalog와 매핑(동의어/접미사/패턴)
    3) **FINAL 후보 생성**: 스코어/규칙 기반으로 Top N 승격(예: is_final)
  - 중요한 원칙:
    - “Mock 데이터” 경로 완전 차단
    - FINAL은 반드시 매핑 confidence(신뢰도)와 evidence_refs를 포함해야 함

---

## 3) 데이터 검증(Validation) — 핵심 로직
### 3.1 `services/engine/app/services/golden_set_validator.py`
#### As-Is (사용자 요약)
- Golden Set 측정값(IC50 등)과 시스템 예측 점수를 비교하여 정확도 산출
- 단위 변환(nM, pM 등)
- MAE, Spearman 상관계수
- 검증 결과 DB 저장

#### To-Be (권장 강화 방향)
Validator는 “있으면 좋은 기능”이 아니라 **골든셋의 존재 이유**가 된다.
따라서 다음을 강화해야 한다.

##### A) 검증 입력 범위 확대
- 기존: IC50(또는 유사 potency)
- 확장(단계적으로):
  1) potency 계열(IC50/EC50/Kd 등)
  2) 리스크/개발성(응집 위험 proxy, 소수성 등) — RDKit 피처 기반
  3) 임상 성공/실패 레이블과의 정합성(분류 지표: ROC-AUC 등은 후속)

##### B) “예측값”의 정의 명확화
- 현재 시스템의 예측은 곧 “100점 추천 스코어”로 갈 가능성이 높음
- Validator는 다음을 구분해서 저장해야 한다:
  - `pred_total_score` (0–100)
  - `pred_breakdown` (evidence/similarity/risk/fit)
  - `measured_values` (golden에 있는 값들)
  - `agreement_metrics` (MAE, Spearman 등)

##### C) 단위/지표 표준화(필수)
- 단위 변환은 Validator의 가장 중요한 방어선
- 최소 표준:
  - 농도 단위: pM/nM/uM/mM 변환
  - 로그 스케일(IC50가 로그 분포) 고려 여부를 명시(예: log10 transform 사용)
  - 결측/범위값(“>10uM”, “<1nM”) 처리 정책 정의

##### D) 검증 결과는 “개발 게이트”로 활용
- 기준 미달이면:
  - 추천 결과를 사용자에게 그대로 노출하지 않거나
  - “불확실/근거 부족” 경고를 강제 표시하거나
  - FINAL 승격을 막는 정책 적용 가능
- 즉, Validator 결과가 운영 정책과 연결되어야 한다.

---

## 4) 테스트 및 유틸리티
### 4.1 `services/engine/test_pubmed_seed_set.py`
- As-Is
  - PubMed 데이터 기반 시딩 테스트(골든셋과 연관 가능)
- To-Be
  - PubMed는 비정형 텍스트이므로 “정답 데이터 생성”이 아니라:
    - evidence_items 생성 및
    - 엔티티 매핑 정확도(precision/recall)에 대한 테스트로 전환하는 것이 바람직
  - 권장 테스트 항목:
    - 특정 키워드/표적에서 동의어 매핑 성공률
    - 페이로드/링커 추론(접미사 기반)의 오류율
    - evidence_refs가 누락되지 않는지

### 4.2 `check_seed_tables_v2.py`
- As-Is
  - DB에 시딩된 테이블 행(row) 개수 확인
- To-Be
  - “개수 확인” 외에 운영에 필요한 기본 품질 체크를 추가 권장:
    - component_catalog에서 payload/linker 중 smiles 누락 비율
    - golden_set에서 evidence_refs 누락 비율
    - final 후보의 매핑 confidence 분포(저신뢰 비율)

---

## 5) 권장 데이터 모델(골든셋 관련) — 최소 형태
> 정확한 테이블명은 현재 DB에 맞춰 조정하되, 논리 구조는 아래를 권장한다.

### 5.1 Golden Set 케이스(정답지)
- `golden_set_cases`
  - disease, biomarker
  - antibody_id, linker_id, payload_id (component_catalog FK 또는 canonical key)
  - outcome_label (success/fail/tox/cmc/agg 등)
  - failure_modes[] (jsonb)
  - measured_values (jsonb: IC50 등)
  - evidence_refs (jsonb: 임상/전임상/문헌 링크)
  - created_at, updated_at

### 5.2 동적 수집 RAW / FINAL 분리
- `golden_seed_raw`
  - source (clinicaltrials 등), raw_payload(jsonb), fetched_at
- `golden_seed_candidates`
  - 매핑 결과(antibody/linker/payload), confidence, evidence_refs, is_final

### 5.3 Validator 결과
- `golden_validation_runs`
  - run_id, dataset_version, started_at, finished_at
- `golden_validation_results`
  - case_id, pred_total_score, pred_breakdown
  - metrics(jsonb: MAE, Spearman 등)
  - notes/warnings

---

## 6) 수정해야 할 코딩 포인트(실행 가능한 수준)
### 6.1 Seed 스크립트(v2/v3) 공통 개선
1) **component_catalog 강제 매핑**
   - 문자열 기반 임시 저장(예: “vedotin payload 추정”) 금지
   - 매핑 실패 시: `unmapped_entities`로 별도 기록하고 FINAL로 승격 금지
2) **evidence_refs 필수화**
   - approved/clinical이든 최소 출처 링크는 남겨야 보고서가 성립
3) **링커/페이로드 구조 필드**
   - payload는 smiles 필수(없으면 rdkit job 불가)

### 6.2 golden_seed_job 개선(동적 수집 워커)
1) RAW/FINAL 분리 저장
2) intervention 추출 로직 강화(패턴/사전)
3) suffix 기반 추론은 “보조”로만 사용
4) 매핑 confidence 점수 부여
5) FINAL 승격 조건:
   - (a) canonical 매핑 성공
   - (b) evidence_refs 존재
   - (c) confidence 임계 이상

### 6.3 golden_set_validator 강화
1) 단위 변환/범위값 정책을 코드 레벨로 고정
2) 예측 점수(100점) breakdown 저장
3) 검증 지표는 최소 MAE + Spearman 유지
4) (선택) 케이스별 “오차 원인 분해” 로그:
   - 근거 부족(evidence low)
   - 유사도 낮음(similarity low)
   - 리스크 페널티 과다(risk penalty high)

---

## 7) 운영 권장 규칙(골든셋이 엔진으로 보이게 만드는 장치)
- Golden Set은 “정답”이므로 변경은 버전 관리:
  - dataset_version, 변경 내역 로그(누가/언제/무엇)
- FINAL 후보는 “검증”을 통과해야 사용자 보고서에 반영:
  - validator 결과 미달 시 “Draft”로만 유지
- 보고서에는 항상:
  - 근거(링크/요약) + 점수 분해 + 경고/가정
  - “정밀 독성 예측”이 아니라 “근거+계산 기반 프록시”임을 구분 표기

---

## 8) 다음 액션(권장 작업 순서)
1) Seed v2/v3의 출력 스키마를 “골든 케이스북” 형태로 정리(필드 확정)
2) component_catalog에 linker/payload 구조 필드(smiles) 확장
3) golden_seed_job의 RAW/FINAL 분리 + confidence 도입
4) golden_set_validator의 입력/출력 스키마를 “100점 breakdown”에 맞춰 확장
5) Admin UI에서 Golden Set 케이스 + Validator 결과 확인 흐름 연결

---

## 9) 파일-책임 매트릭스(요약)
- seed_golden_data(_v2/_v3): “정적 레퍼런스 케이스 생성/적재”
- golden_seed_job: “동적 수집(임상 등) RAW 저장 → 매핑/정규화 → FINAL 후보 생성”
- golden_set_validator: “정답지 대비 예측/추천 점수의 정확도 산출 및 품질 게이트”
- test_pubmed_seed_set: “문헌 근거(evidence) 생성/매핑 정확도 테스트”
- check_seed_tables_v2: “시드/골든 데이터 품질 지표 점검(개수+결측+누락률)”

---

문서 끝.
