# Target-centric Enrichment 기반 Golden Set 구축 (표적 1개씩 실행)

## 목적
현재 Golden Set 구축이 “레고 조립(텍스트 조합)”처럼 보이지 않도록, **표적(Target) 단위로 임상/문헌/화학 근거를 수집·정규화·보강**하여 DB를 채우는 운영 구조로 전환합니다.  
핵심은 “자동 승격(완전 자동)”이 아니라, **표적 1개 실행 → 후보군+근거 자동 생성 → 관리자 확정(승격)** 흐름입니다.

---

## 핵심 원칙
1. **표적 1개씩 실행(Target-centric Run)**  
   - HER2, HER3, TROP2 등 표적을 선택하면 그 표적에 대해서만 파이프라인을 실행합니다.
2. **ClinicalTrials 단독으로 링커/페이로드 ‘완전 자동’은 어렵다**  
   - 임상 데이터는 코드명(MK-2870 등) 또는 복합 요법 문자열이 많아 구성요소가 불완전합니다.
3. 따라서 “정확한 구조(화학식) 완전 자동”이 아니라  
   **후보군(candidate) + evidence(근거) 자동 생성** 후 **관리자 확정**으로 품질을 확보합니다.
4. 투자자/외부 설명 포인트:  
   - “수기 입력”이 아니라 **큐레이션(Review → Approve → Audit)** 이며,
   - 모든 결정은 **근거(evidence_refs) + lineage(dataset_version/run_id)** 로 추적 가능합니다.

---

## 전체 아키텍처 개요
### Target Enrichment Run (표적 단위 런)
- 입력: `target = "HER2"` (+ 선택: cancer_type, constraints)
- 처리:
  1) 임상 데이터 수집 (ClinicalTrials)
  2) 프로그램/코드명 정규화 (Resolver)
  3) 문헌 근거 수집 (PubMed RAG)
  4) 화학/약물 메타 보강 (ChEMBL/PubChem 등, 가능 범위)
  5) 품질 게이트 + 검수 큐 생성 (Admin Review Queue)
- 출력:
  - RAW: `golden_seed_raw`에 원문 전체 저장(재현성)
  - 후보군: payload/linker 후보 + 근거 저장
  - 관리자 확정 후: `golden_candidates.is_final=true` 로 Golden Set 승격

---

## 데이터 소스별 역할(표적 1개 실행 기준)
### 1) ClinicalTrials (임상 프로그램 “풀” 확보)
- 목표: 표적 관련 trial을 최대한 넓게 모으되 oncology로 제한
- 저장: NCT ID, title, conditions, interventions, phase/status 등
- 비고: 링커/페이로드는 직접 명시되지 않는 경우가 많음

### 2) PubMed RAG (근거 문장/PMID 확보)
- 목표: “이 프로그램의 payload/linker family가 무엇인지”를 뒷받침하는 문장/PMID 수집
- 저장: snippet/excerpt, PMID, confidence, query_profile, retrieved_at
- 비고: PROTAC/면역활성 payload 등 신규 payload 계열도 문헌 근거로 후보군화 가능

### 3) ChEMBL/PubChem 등 (가능한 범위의 구조/물성 확보)
- 목표: payload 후보가 확정되면 SMILES 및 기본 물성(분자량, logP 등)을 확보
- 비고: 모든 payload가 1:1로 매칭되는 것은 아니므로 “가능한 범위”에서 보강

---

## DB 스키마(권장 최소)
### A. `component_catalog` (표준 사전)
- 목적: 관리자 확정 시 표준 엔티티로 연결
- 권장 컬럼:
  - `type` (target/antibody/linker/payload)
  - `canonical_name`
  - `gene_symbol` (target)
  - `synonyms` (jsonb)
  - `smiles` (payload 후보의 경우)
  - `linker_type`, `trigger` (linker 계열 분류)
  - `external_refs` (pubchem/chembl/drugbank 등)

### B. `golden_seed_raw` (표적 단위 RAW 저장; 재현성/추적성 핵심)
- 권장 컬럼:
  - `source` = "clinicaltrials"
  - `source_id` = NCT ID
  - `source_hash` (중복 방지)
  - `raw_payload` (jsonb; title/conditions/interventions/all_drugs 포함)
  - `query_profile` = "target_enrichment"
  - `query_target` (예: HER2)
  - `parser_version`, `dataset_version`
  - `fetched_at`

### C. `golden_candidates` (확정/승격된 Golden Set)
- 운영 원칙:
  - 자동 승격은 최소화하고, **관리자 확정 후 is_final=true** 로 승격
- 권장 컬럼:
  - `target`, `antibody`, `payload`, `linker` (표시용)
  - (선택) 각각의 FK id (`target_id`, `payload_id` 등)
  - `program_key` (조합 유니크 키)
  - `source_ref` (NCT ID)
  - `evidence_refs` (jsonb; NCT/PMID 등)
  - `mapping_confidence`, `confidence_score`
  - `is_final`, `review_status`, `reviewed_by`, `reviewed_at`, `review_note`
  - `raw_data_id` (FK), `dataset_version`

### D. 후보군 저장(선택지 2개)
#### 옵션 1) `target_profiles`에 jsonb로 후보군 저장(빠른 MVP)
- 컬럼 예:
  - `payload_candidates` (jsonb list)
  - `linker_candidates` (jsonb list)
  - `evidence_bundle` (jsonb)
- 장점: 테이블 증가 최소화

#### 옵션 2) `candidate_components` 테이블 신설(운영/검색에 유리)
- 컬럼 예:
  - `target_id`, `component_type`(payload/linker)
  - `candidate_name`, `family`, `confidence`
  - `evidence_refs` (jsonb)
  - `smiles`(optional), `properties_json`(optional)
  - `dataset_version`, `created_at`

---

## 실행 워크플로우(표적 1개 기준)
### Step 0. Admin 입력
- 선택: Target = HER2
- 옵션: per_target_limit(예: 30), status filter, phase filter(예: Phase 1+)

### Step 1. 임상 수집(ClinicalTrials Fetch)
- 쿼리 정책: **표적 중심 + oncology AND** (mAb 기반 수집 금지)
- query.term 형태:
  - `(<TARGET OR SYNONYMS>) AND (cancer OR tumor OR carcinoma OR neoplasm OR metastatic OR lymphoma OR leukemia OR myeloma OR sarcoma OR malignan*)`
- 수집 결과는 전량 `golden_seed_raw`로 저장
- 저장 시 반드시 포함:
  - `query_target`, `all_drugs`, `conditions`, `title`, `phase/status`

### Step 2. 정규화(Resolver)
- 목표:
  - 코드명(MK-2870 등)과 알려진 프로그램명/동의어를 연결할 수 있도록 기반 마련
- 결과:
  - mapping_table(캐시)에 기록하거나 raw_payload에 정규화 힌트 저장

### Step 3. payload/linker 후보군 생성(자동, 근거 포함)
- 규칙 기반(초기; “완전 자동 확정”이 아닌 후보군 생성):
  - suffix/패턴 신호로 payload family 후보 생성
  - 문헌(RAG)로 근거 문장/PMID 확보
- 후보군 저장:
  - target_profiles 또는 candidate_components에
  - `{name/family/confidence/evidence_refs}` 형태로 기록

### Step 4. 품질 게이트 + Review Queue
- 자동 판단은 “승격”이 아니라 “검수 우선순위”에 사용
  - 예: evidence 없음 / 너무 애매함 / 프로그램명 불명 → review_queue에 표시

### Step 5. 관리자 수동 확정(승격)
- Admin이 RAW + evidence를 보고 다음을 수행:
  - “ADC 확실 / 항체치료제 / 제외” 라벨
  - payload/linker 후보 선택(또는 Unknown 유지)
  - 승격 버튼 → `golden_candidates.is_final=true`
  - reviewed_by/at/note 기록

---

## Admin UI(필수 최소 기능)
### 1) Target 선택 + 실행 버튼
- 표적 50개 리스트에서 1개 선택
- “수집 실행” → worker run 생성

### 2) RAW Review 화면
- 필터:
  - query_target, phase, status, cancer keyword
- 표시:
  - NCT ID, title, conditions, all_drugs, phase/status
- 액션:
  - “승격(Promote)” / “보류” / “제외”

### 3) Candidate Panel (payload/linker 후보 + 근거)
- payload 후보 목록(근거 PMID/NCT 스니펫 포함)
- linker 후보 목록(가능하면)
- 선택 시 golden_candidates에 반영

### 4) Audit/History
- 누가 무엇을 승격/수정했는지 로그(최소 reviewed_by/at/note)

---

## 품질/재현성(필수 기준)
1. `golden_seed_raw`에 **dataset_version + parser_version** 저장
2. raw_payload에 **query_target, query_terms, fetched_at** 포함
3. candidate/승격 결과에는 **raw_data_id** 연결
4. Golden Set은 “최종 확정본”이므로 `is_final=true`만 외부/사용자 노출

---

## 기대 효과
- **문서/보고서가 일방적이지 않음**: 표적별로 “근거 기반 후보군”이 쌓임
- “레고 조립”이 아니라 **표적별 설계 엔진의 근거 데이터베이스**로 보임
- 50개 표적을 한 번에 돌리는 대신, **표적 1개씩 고품질로 채우는 운영**이 가능
- PROTAC/면역활성 payload 등 **다양한 payload 확장**이 후보군+근거 방식으로 자연스럽게 가능

---

## 한계 및 운영 결론
- ClinicalTrials 단독으로 “링커 구조/SMILES까지 100% 자동”은 어려움
- 그러나 표적 1개 단위로
  - 임상 후보 풀(ClinicalTrials) + 근거(PubMed) + 구조 보강(PubChem/ChEMBL)
  - 그리고 관리자 확정(승격)
  을 결합하면, **MVP 수준에서 설득력 높은 Golden Set과 설계 근거 DB 구축이 가능**합니다.

---

## 다음 작업(권장 순서)
1) `target_enrichment` QueryProfile/Run 정의 및 worker에서 실행 가능하도록 연결
2) `golden_seed_raw`에 query_target 저장 + RAW 축적
3) Admin “RAW Review + Promote” 메뉴 구현
4) 표적 10개로 파일럿 → 품질 확인 후 50개 확장
