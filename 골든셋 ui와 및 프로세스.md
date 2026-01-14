# ADC Platform — Admin 프로세스 & 최소 UI 구현 가이드 (MVP v1.0)
작성일: 2026-01-14  
목표: **관리자가 워커를 실행하고**, 수집된 RAW/Enrichment 결과를 검토한 뒤, **조건을 충족한 항목만 “승격(Final)”** 처리한다.  
핵심 원칙: 자동화는 “채우기(Enrichment)”, 최종 확정은 “사람(큐레이션)”.

---

## 0) 운영 컨셉 (왜 Admin 중심인가)
- 링커/페이로드는 공개 구조가 없거나 비정형 표기가 많아 **완전 자동화가 어렵다**.
- 따라서 **Admin이 “조건을 채워 넣고(수정)” → 조건 충족 시 “승격”**하는 방식이 가장 현실적이다.
- 워커는:
  1) 후보 근거(ClinicalTrials/NCT, PubChem/SMILES, ChEMBL/bioactivity)를 가져오고  
  2) 매핑/정규화/계산(RDKit)을 수행하며  
  3) 부족한 부분은 “Review Queue”로 올린다.

---

## 1) Admin 전체 프로세스 (End-to-End)

### Step A. Seed(골든셋) 기본 입력
- Admin이 Seed(20/50)를 DB에 입력한다.
- 최소 필드:
  - drug_name_canonical, aliases
  - target, antibody, linker_family, linker_trigger
  - payload_family, payload_exact_name
  - clinical_phase, program_status, outcome_label
  - primary_source_type, primary_source_id
- 입력 후 “필드 잠금(Verified)”을 걸 수 있다. (자동 overwrite 방지)

---

### Step B. 워커 실행 (Enrichment)
Admin이 “Run” 버튼으로 워커 실행:
1) resolve_ids_job (필수)  
2) clinical_enrich_job (ClinicalTrials 대표 NCT 선정 + secondary 후보 저장)  
3) pubchem_enrich_job (SMILES/물성, 실패 시 후보/유사체 제안)  
4) chembl_enrich_job (가능 시 target mapping, bioactivity)  
5) rdkit_features_job (Salt 제거 + 표준화 후 RDKit 지표 계산)  
6) data_quality_job (승격 조건 체크 → Review Queue 생성)

> 실행 결과는 Seed 테이블을 무조건 덮어쓰지 않고, 가능한 한 “제안(Suggestion)”으로 저장한 뒤 Admin이 채택한다.

---

### Step C. Review Queue 처리 (수정/보강)
Admin이 Review Queue에서 항목을 하나씩 해결:
- Missing SMILES / Proxy 필요
- Target unresolved (HER2→ERBB2 등)
- ClinicalTrials 대표 NCT 미확정/충돌
- Linker/Payload mapping 불확실
- RDKit 계산 실패(염/복합체/파싱 문제)

해결 방법:
- Admin이 Seed Detail 화면에서 직접 수정/입력
- 수정 후 해당 필드를 Verified로 잠금 (또는 레코드 전체 is_manually_verified)

---

### Step D. 품질 게이트 통과 → 승격(Promotion)
Seed가 “조건 충족” 상태가 되면:
- Admin이 “승격(Final)” 버튼 클릭
- 시스템은:
  - is_final=true
  - finalized_by, finalized_at
  - dataset_version 고정
  - final_snapshot(JSONB) 저장(권장)
- 이후 재실행되어도 덮어쓰기 금지(Overwrite Protection)

---

## 2) 승격 조건(Quality Gate) — Admin이 “채워서” 통과시키는 구조

### 2.1 기본 승격 조건 (MVP 최소)
아래 조건을 모두 만족하면 “승격 가능” 상태:

1) Target 정규화 완료  
- resolved_target_symbol 존재 (예: HER2→ERBB2, FRα→FOLR1)

2) 대표 임상(ClinicalTrials) 확정  
- clinical_nct_id_primary 존재  
- clinical_phase/program_status 최신화(가능하면)

3) Payload 구조 데이터 확보  
- payload_smiles_standardized 존재  
- 또는 proxy_smiles_flag=true AND is_proxy_derived=true

4) RDKit 계산 완료  
- mw/logp/tpsa/hbd/hba/qed 등 주요 지표 존재

5) Evidence 최소 1개  
- evidence_refs에 NCT 또는 PMID 또는 FDA label id 등

---

### 2.2 “조건을 Admin이 수정으로 채울 수 있어야 한다” 구현 방식
- Seed Detail 화면에서 각 조건의 “미충족 원인”을 표시하고
- 바로 입력/수정 가능한 UI를 제공한다.

예시:
- resolved_target_symbol 비어있음 → “Resolve Target” 버튼(Resolver 실행) + 수동 입력란
- clinical_nct_id_primary 없음 → “Search ClinicalTrials” 버튼 + 후보 리스트에서 선택
- payload_smiles_standardized 없음 → “PubChem Lookup” + 실패 시 “Proxy SMILES 입력”
- RDKit 실패 → “Standardize/Salt Remove 재시도” 버튼 + 오류 로그 표시

---

## 3) DB/상태 설계 (UI 구현을 위한 최소 필드 제안)

### 3.1 seed_golden_set (또는 golden_set_seed) 테이블에 권장 필드
- id (uuid)
- drug_name_canonical, aliases
- target, resolved_target_symbol
- antibody
- linker_family, linker_trigger
- payload_family, payload_exact_name
- payload_smiles_raw, payload_smiles_standardized
- proxy_smiles_flag (bool), proxy_reference (text), is_proxy_derived (bool)
- clinical_phase, program_status
- clinical_nct_id_primary, clinical_nct_ids_secondary (jsonb)
- outcome_label (Success/Fail/Uncertain/Caution)
- evidence_refs (jsonb array)
- rdkit_features_id (fk) 또는 rdkit_features_jsonb
- gate_status (enum: draft / needs_review / ready_to_promote / final)
- is_final (bool)
- overwrite_protection:
  - is_manually_verified (bool)
  - field_verified (jsonb)
- finalized_by, finalized_at
- updated_at

### 3.2 review_queue 테이블(또는 view) 권장
- id
- seed_id
- queue_type: missing_smiles | unresolved_target | nct_conflict | low_confidence | overwrite_suggestion | rdkit_failed ...
- severity: low/med/high
- suggested_value(jsonb) / reason(text) / source(jsonb)
- status: open / resolved / dismissed
- created_at, resolved_at, resolved_by

---

## 4) Admin UI — “간단하지만 운영 가능한” 최소 화면 5개

## (1) Golden Seed List (목록)
목적: 전체 Seed의 진행 상태를 한눈에 보고, 우선순위를 잡는다.

표 컬럼(권장):
- drug_name_canonical
- target / resolved_target_symbol
- payload_exact_name / smiles_status
- clinical_phase / program_status
- gate_status (draft/needs_review/ready/final)
- is_final
- actions: [상세] [워커실행] [승격]

필터:
- needs_review만 보기
- missing_smiles만 보기
- target별 보기(HER2/TROP2 등)
- final 제외 보기

---

## (2) Run Worker (실행 패널)
목적: Admin이 “한 항목” 또는 “전체 배치”로 워커를 실행.

기능:
- 실행 대상 선택:
  - (A) 선택한 seed_id 1개
  - (B) target 그룹(예: HER2 관련)
  - (C) 전체 Seed(단, verified/final은 skip)
- 실행 Job 체크박스:
  - resolve_ids_job (필수)
  - clinical_enrich_job
  - pubchem_enrich_job
  - chembl_enrich_job
  - rdkit_features_job
  - data_quality_job
- 실행 버튼
- run_log(진행 상태, 성공/실패, 오류)

---

## (3) Review Queue (검수 큐)
목적: “자동화가 못 채운 것”만 모아서 처리.

리스트:
- queue_type, severity, drug_name
- 이슈 요약(예: payload_smiles missing)
- actions: [해결하러가기] [무시] [재시도]

---

## (4) Seed Detail (핵심 화면)
목적: Admin이 조건을 직접 채우고 Verified 처리, 승격까지 수행.

구성(권장 섹션):
A) 기본 정보 (Editable)
- drug_name_canonical, aliases
- target, resolved_target_symbol(수동 입력 가능)
- antibody/linker/payload 정보

B) Evidence & ClinicalTrials
- primary NCT 선택 UI
- secondary NCT 리스트
- status/phase 최신값 표시
- evidence_refs 관리

C) Chemistry (PubChem + 수동)
- payload_smiles_raw / standardized
- “PubChem Lookup” 버튼
- “Proxy SMILES 입력” 영역 + is_proxy_derived 토글

D) RDKit Features
- 계산된 mw/logp/tpsa/qed/sa_score 등
- “표준화 후 재계산” 버튼
- 오류 로그(파싱 실패 시)

E) Gate Checklist (승격 조건 체크리스트)
- [ ] Target resolved
- [ ] Primary NCT selected
- [ ] SMILES ready (or Proxy)
- [ ] RDKit computed
- [ ] Evidence >= 1
→ 충족 시 “승격(Final)” 버튼 활성화

F) Verified / Lock
- is_manually_verified 토글
- 필드별 verified 토글(advanced)

---

## (5) Final Golden Set (최종본)
목적: is_final=true만 모아서 다운로드/검증/학습에 사용.

기능:
- 필터: 그룹(Approved/Late/Novelty/Fail), target
- Export CSV/JSON
- “버전 스냅샷 생성” (dataset_version 확정)

---

## 5) 승격 로직(운영 규칙)
- “승격 버튼”은 gate_status=ready_to_promote에서만 활성화
- 승격 시:
  - is_final=true
  - gate_status=final
  - is_manually_verified=true (자동)
  - finalized_at/by 기록
- 승격 이후 워커 재실행:
  - final/verified 레코드는 자동 업데이트 금지
  - 변경 제안은 review_queue로만 전달

---

## 6) 구현 난이도 최소화 팁 (MVP)
- 처음엔 “필드별 verified” 대신
  - is_manually_verified 하나로도 충분
- RDKit은 payload부터 시작(링커/전체 ADC는 Phase 2)
- ClinicalTrials 대표 NCT는 “Admin이 선택”을 기본으로 두고,
  - 워커는 후보를 뽑아 리스트로 제공하는 역할만 수행해도 됨

---

## 7) 오늘 해야 할 To-do (바로 적용 가능한 작업)
1) Seed Detail 화면에:
   - clinical_nct_id_primary 선택 UI
   - payload_smiles_standardized 입력 UI
   - is_proxy_derived 토글
   - “Gate Checklist” + 승격 버튼
2) Review Queue 화면에:
   - missing_smiles, unresolved_target, nct_conflict만 먼저 표시
3) Worker 실행:
   - seed_id 단일 실행부터(1개씩) 안정화

---

## 8) 결론
- 네, 운영은 “Admin이 워커 실행 + 리스트 검토 + 조건 채우기 + 승격”이 맞다.
- 핵심은 **조건을 UI에서 바로 수정/채울 수 있어야** 승격이 가능해지고,
  이 구조가 쌓이면 자동화 비중을 점진적으로 올릴 수 있다.
