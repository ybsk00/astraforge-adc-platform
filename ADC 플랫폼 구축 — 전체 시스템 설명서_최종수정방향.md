# ADC 플랫폼 구축 — 전체 시스템 설명서 (System Overview)
버전: v0.9  
작성일: 2026-01-13  
목적: 현재까지의 작업(Seed/Golden Seed/Worker 안정화)을 기반으로, **근거 기반 추천 + RDKit 계산 + 자동 보고서 생성** 중심의 “설계 엔진”으로 시스템을 재정의하고, 이후 모듈별 구현/개선을 일관되게 진행하기 위한 공통 문서

---

## 1. 시스템 목표(Why)
### 1) 외부/투자자 관점 목표
- 단순 “조합(레고) UI”가 아니라,
- **문헌·전임상·임상 근거 + 계산(RDKit) 기반으로 링커/페이로드를 추천하고**
- **타당성 점수(100점) + 근거 번들로 보고서(PDF)까지 자동 산출**하는 “설계 엔진”임을 증명

### 2) 사용자(연구자) 관점 목표
- 사용자는 복잡한 조합·수집·계산을 직접 하지 않고,
- **암종/바이오마커 선택 → 항체 선택(검증된 항체 고정) → 목표 설정 → 보고서 신청**
- 결과는 **다운로드 가능한 보고서**로 받는다.

### 3) 운영(관리자) 관점 목표
- 관리자/시스템은 자동으로 다수 시뮬레이션을 수행하고,
- 추천 결과의 품질을 **Golden Set(레퍼런스 케이스) 기반으로 검증/보정**한다.
- 데이터 파이프라인은 재현 가능하며, 실패/충돌/불확실성을 기록한다.

---

## 2. 핵심 제품 플로우(End-to-End)
### A. 연구자(사용자) 플로우
1. 암종 선택 (예: Breast cancer)
2. 바이오마커/서브타입 선택 (예: HER2+, ER+)
3. 항체 선택 (예: trastuzumab 등 검증된 항체)
4. 설계 목표 선택 (예: bystander 필요, 독성 엄격, CMC 안정성 우선 등)
5. “보고서 신청(Submit)” 클릭
6. Run 상태(대기/진행/완료) 확인
7. 완료 후 보고서 다운로드

### B. 시스템/관리자(자동) 플로우
1. 입력(암종/항체/목표)을 기준으로 후보 탐색(링커/페이로드 pool 생성)
2. 근거 수집(임상/전임상/문헌/특허) 및 엔티티 매핑
3. RDKit 계산(피처/유사도/리스크 프록시)
4. 조합 생성(Top-K) 및 100점 스코어링
5. 결과 저장(근거+점수+경고+가정)
6. 보고서(PDF/HTML) 생성
7. 사용자 다운로드 제공
8. 관리자: 결과 검토/승인/정책 수정(룰/가중치/금지 조합)

---

## 3. 시스템 구성요소(Architecture)
### 3.1 Frontend (Next.js)
- 사용자 페이지
  - 암종/바이오마커/항체 선택
  - 목표(옵션) 선택
  - 보고서 신청 및 Run 상태/결과 조회
  - 보고서 다운로드
- Admin 페이지
  - Seed/Catalog 관리(타겟/항체/링커/페이로드 사전)
  - Golden Set(레퍼런스 케이스) 관리
  - Runs/Reports 관리(실행 로그/오류/재시도)
  - 룰/가중치/금지 조합 관리(Compatibility Matrix)

### 3.2 Backend API (FastAPI Engine)
- Frontend ↔ Backend 연동 표준 API 제공
- 주요 책임
  - 보고서 신청 생성(= Run 생성)
  - Run 상태/결과 조회
  - Admin 관리용 CRUD(카탈로그, 골든셋, 룰/가중치 등)
  - 워커(Job) 트리거(큐/DB 기반)

### 3.3 Worker (Python, arq 기반 가정)
- 실제 데이터 수집/처리/계산/보고서 생성의 실행 주체
- 주요 Job
  - seed_job: component_catalog 적재/병합
  - meta_sync_job: 외부 소스 enrichment (UniProt, HPA, OpenTargets, ChEMBL, PubChem 등)
  - golden_seed_job: ClinicalTrials 기반 후보군 생성(Top 100 등)
  - rdkit_features_job: SMILES 기반 피처/유사도 산출
  - preclinical_evidence_job: 전임상 정형 근거(assay/bioactivity) 수집·정규화
  - recommendation_job: Top-K 조합 및 100점 스코어링
  - report_job: 결과 기반 PDF/HTML 보고서 생성

### 3.4 Database (Supabase Postgres + pgvector)
- 운영 데이터 저장소
- 역할
  - component_catalog(표준 사전) + seed/merge 관리
  - 골든셋(레퍼런스 케이스) 저장
  - evidence_items(근거 원천) 저장
  - run/result/report 저장 및 상태 관리
  - (선택) 문헌 청킹+임베딩 벡터 저장(pgvector)

---

## 4. 핵심 데이터 개념(Concepts)
### 4.1 component_catalog (표준 사전 / Canonical Dictionary)
- 목적: 모든 데이터 수집/추천/보고서의 “기준 엔티티”
- 타입 예시: `target`, `antibody`, `linker`, `payload`
- 필수 방향:
  - **링커/페이로드는 RDKit 입력을 위해 구조(SMILES 등) 필드가 필요**
  - synonyms(동의어)로 매핑 정확도 확보
  - canonical_name + 외부참조(external_refs)로 정규화

### 4.2 Golden Set (레퍼런스 케이스북)
- 목적: “부품 목록”이 아니라 “정답/검증 기준”
- 포함 요소:
  - (암종/바이오마커/항체/링커/페이로드) 조합
  - outcome_label(성공/실패/독성/CMC 문제 등)
  - failure_modes(aggregation, instability, off-target tox 등)
  - evidence_refs(문헌/전임상/임상 링크)
- 역할:
  - 추천 결과의 유사도/정합성 평가 기준
  - 룰/가중치 튜닝 기준(회귀 테스트)

### 4.3 Evidence Items (근거 데이터)
- 유형:
  - 임상: ClinicalTrials 기반 trial/arms/interventions/phase/status/outcomes
  - 전임상 정형: bioactivity, assay, cell line, target 등(ChEMBL/PubChem 등)
  - 문헌 정성: RAG로 추출한 근거 문장/요약 + 출처
  - 특허: 클레임/설계 패턴 힌트 + 출처
- 원칙:
  - 모든 추천에는 근거 링크/요약이 함께 제공되어야 함
  - 불확실/충돌은 숨기지 않고 “경고/가정”으로 노출

---

## 5. 데이터 파이프라인(Seed → Enrichment → Golden → Recommend → Report)
### Step 1) Seed 적재 (seed_job)
- 입력: seeds JSON(예: targets_seed_200.json + 항체/링커/페이로드 seed 확장)
- 처리:
  - 기존 DB보다 JSON 데이터 우선 병합(필드 단위 Merge)
  - upsert 충돌은 select→insert/update로 안정화
- 산출:
  - component_catalog에 기준 엔티티 생성/정규화

### Step 2) Enrichment (meta_sync_job, batch_mode)
- 입력: component_catalog의 대상(타겟 등)
- 처리:
  - UniProt: 기본 타겟 정보/외부 참조
  - OpenTargets: 질환 연관/점수
  - HPA: 발현
  - ChEMBL/PubChem: 약물/활성/구조 연결(가능 범위)
- 산출:
  - target_profiles 등 확장 테이블(또는 component_catalog의 metadata 확장)

### Step 3) Golden 후보 생성 (golden_seed_job)
- 입력: ClinicalTrials 기반(강제), disease/target 중심
- 처리:
  - intervention 추출 강화(약물명 패턴)
  - suffix 기반 payload/linker 추론(초기 휴리스틱)
  - 1차 catalog 매칭 → 실패 시 휴리스틱
  - Raw vs Final 분리 전략(is_final 등)
- 산출:
  - “임상 기반 후보 pool” (Top 100 등) 생성

### Step 4) RDKit 피처 산출 (rdkit_features_job)
- 입력: payload/linker의 SMILES(또는 mol)
- 처리:
  - descriptors(MW, LogP, TPSA, HBD/HBA 등)
  - fingerprints(예: Morgan/ECFP)
  - Golden Set 대비 유사도(Tanimoto 등)
  - 리스크 프록시 feature(소수성 과다, MW 과다 등)
- 산출:
  - rdkit_features 테이블(또는 component_catalog metadata)에 저장

### Step 5) 전임상 근거 수집 (preclinical_evidence_job)
- 입력: 후보 payload(또는 관련 엔티티)
- 처리:
  - 정형 근거 우선(assay/bioactivity)
  - 문헌 정성은 RAG로 확장(추후)
- 산출:
  - evidence_items에 정형 근거 저장 및 엔티티 매핑

### Step 6) 추천 및 점수화 (recommendation_job)
- 입력: 암종/바이오마커/항체 + 목표
- 처리:
  - 후보 pool 구성(임상/골든/카탈로그 기반)
  - 조합 생성(payload×linker, 항체 고정)
  - Compatibility Matrix(룰 기반: 금지/경고/조건부) 적용
  - 100점 스코어 계산 및 Top-K 선정
- 산출:
  - recommendation_results 저장(점수 분해 + 근거 번들 + 경고/가정)

### Step 7) 보고서 생성 (report_job)
- 입력: recommendation_results
- 처리:
  - 보고서 템플릿에 근거/점수/경고/가정/그래프/표 삽입
- 산출:
  - PDF/HTML 리포트 파일
  - report 레코드(다운로드 링크/상태)

---

## 6. 100점 스코어링(Scoring) — MVP 표준
> 원칙: “정밀 독성 예측”을 과장하지 않고, **근거 기반 + 계산 기반(프록시)**를 분리 표기한다.

### 6.1 점수 구성(총 100)
1) Evidence Score (0–40)
- 임상 + 전임상 정형 + 문헌 정성의 “근거량/일치도/품질”
- 예: 관련 trial 수, 전임상 assay 근거 유무, 리뷰/원문 근거 포함 여부

2) Similarity-to-Golden (0–25)
- Golden Set 성공 케이스 대비 payload/linker 유사도
- RDKit fingerprint 기반 유사도 점수

3) Developability Risk (0–25)
- RDKit descriptor 기반 리스크 프록시
- 예: 지나친 소수성/분자량, 극단적 TPSA 등 → 페널티

4) Design-Fit Score (0–10)
- 목표 기반 가중치
- 예: bystander 필요 → membrane-permeable 계열(정성 근거 포함) 가점
- 독성 엄격 → 안전성 시그널 있는 클래스 페널티

### 6.2 결과 출력 원칙
- 총점과 함께 **점수 분해(breakdown)**를 반드시 제공
- 경고(warnings)와 가정(assumptions)을 구조적으로 저장/표시
- 금지 조합은 결과에 포함하지 않거나 별도 섹션에 “제외 사유”로 기록

---

## 7. Compatibility Matrix (룰 기반 호환성)
- 목적: “레고처럼 아무거나 붙인다”는 인상을 제거하는 핵심 장치
- 형태:
  - 금지(Forbidden): 조합 불가(예: 특정 트리거+특정 클래스 리스크가 과다)
  - 경고(Warning): 가능하나 위험(예: 응집 리스크 높음)
  - 조건부(Conditional): 특정 조건(DAR 범위, 안정성 조건)에서만 허용
- 운영:
  - 초기에는 룰 기반으로 시작
  - Golden Set의 실패 모드가 누적되면 룰 정교화

---

## 8. 운영 방식(“사용자는 신청만” 구조)
### 8.1 Run/Report 중심 운영
- 사용자는 설계 파라미터를 최소로 입력
- 시스템은 비동기 실행(Run)
- 완료 시 다운로드 제공

### 8.2 상태 관리
- Run 상태: queued → running → done/failed
- 실패 시:
  - 오류 로그 저장
  - 재시도 정책(관리자)
  - 데이터/근거 부족은 “불확실성 경고”로 보고서에 표기 가능

### 8.3 Admin의 역할
- Seed/Catalog 정합성 유지(동의어/SMILES/클래스)
- Golden Set 확장(성공/실패 케이스 축적)
- 룰/가중치 튜닝(Compatibility, Scoring weights)
- 결과 품질 모니터링(Top-K 분포, 근거 커버리지)

---

## 9. 현재까지 완료된 작업(요약)
- Worker Import 에러 해결(sys.path)
- connector_executor 분기 로직 완성(api/db/system 타입별 job 호출)
- meta_sync_job batch_mode 지원(카탈로그 기반 수집)
- seed_job upsert 이슈 해결(select→insert/update)
- DB 마이그레이션(커넥터 타입, batch_mode config)
- 타겟 200개 seed JSON 생성 및 seed_job 연동
- 변경 사항 main 브랜치 push 완료
- Worker 재시작 필요(운영 절차)

---

## 10. 다음 단계(수정 방향) — “엔진화” 우선순위
### Priority 1) component_catalog 확장(링커/페이로드 30~50 + SMILES + synonyms)
- RDKit 계산의 전제
- 임상/문헌 매핑 정확도 개선

### Priority 2) golden_seed_job 강화(임상 기반 후보 pool Top 100 안정화)
- Mock 제거, suffix/패턴 강화, raw/final 분리

### Priority 3) rdkit_features_job 신설 + 100점 스코어 MVP 구현
- 외부 설득력 급상승(“계산 기반” 증명)

### Priority 4) preclinical_evidence_job 신설(정형 전임상 우선)
- “방대한 전임상” 요구를 현실화하는 첫 단계

### Priority 5) report_job 신설(PDF/HTML)
- 사용자 가치의 최종 산출물
- 투자자 데모에서도 가장 강력한 결과물

---

## 11. 리스크 및 원칙
### 11.1 데이터 품질/매핑 리스크
- 동의어/약물명 변형/약물 접미사(vedotin, deruxtecan 등)로 인해 매핑 오류 가능
- 해결 원칙:
  - canonical 사전(component_catalog) 강화
  - 매핑 confidence score + human review 경로 유지

### 11.2 “독성 예측” 과장 리스크
- RDKit만으로 독성을 정밀 예측할 수 없음을 명시
- MVP는 “리스크 프록시”로 시작하고 근거 기반으로 보강

### 11.3 보고서의 과학적 정직성
- 근거/계산/추론을 구분 표기
- 불확실성/충돌/데이터 부족은 숨기지 않는다(신뢰 확보)

---

## 12. 용어 정리(간단)
- Seed: 기준 사전 적재 작업
- component_catalog: 엔티티 표준 사전(타겟/항체/링커/페이로드)
- Golden Set: 성공/실패 레퍼런스 케이스북(평가 기준)
- Evidence: 임상/전임상/문헌/특허 근거 묶음
- Run: 사용자 요청 기반의 비동기 실행 단위
- Report: Run 결과를 정리한 다운로드 산출물
- Compatibility Matrix: 조합 금지/경고/조건부 허용 룰

---

## 13. 부록: 권장 엔티티 최소 필드(초안)
### payload
- canonical_name, synonyms[]
- smiles (required)
- payload_class, mech_tags[]
- external_refs (pubchem_id, chembl_id 등)

### linker
- canonical_name, synonyms[]
- linker_type (cleavable/non-cleavable)
- trigger (cathepsin/acid/disulfide 등)
- stability_tags[]
- (optional) smiles/structure (링커 자체 구조가 필요하면)

### antibody
- canonical_name, target_gene_symbol, format
- validated_indications[]
- external_refs

### golden_set_case
- disease, biomarker
- antibody_id, linker_id, payload_id
- outcome_label, failure_modes[]
- evidence_refs[]

---

문서 끝.
