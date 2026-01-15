# Golden Set 확장 파이프라인 보완사항 (v1.1)
작성일: 2026-01-15  
목표: **항체/링커/페이로드(구성요소) + SMILES/Proxy + 근거(Evidence) + Review Queue 승인**까지 버튼 기반으로 자동화하되, **LLM은 “후보 선택 + 근거 요약” 보조 역할**로만 사용한다.

---

## 0. 핵심 정리 (중요)
### 0.1 항체는 “SMILES”가 아니다
- **SMILES는 소분자 표기**이며, 항체(mAb/bispecific)는 단백질/거대분자라 “항체 SMILES”는 표준적으로 존재하지 않는다.
- 따라서 자동화 목표를 아래처럼 변경한다.

**항체 자동화 목표**
- `antibody_name_canonical` (표준명)
- `format` (mAb / bispecific / scFv 등)
- `isotype` (IgG1 등, 가능 시)
- `uniprot_id` 또는 `drugbank_id` (가능 시)
- (가능하면) `fasta_heavy`, `fasta_light` / `pdb_ids`
- `conjugation_type` (cys/lys/site-specific, 가능 시)
- `evidence_refs[]` (근거 링크/PMID/라벨)

**링커/페이로드 자동화 목표**
- 링커/페이로드는 **SMILES 자동 채움**을 목표로 하되,
- 공개 구조가 없으면 **Proxy SMILES**를 사용하고, 반드시 **Proxy임을 명시 + 근거**를 남긴다.

---

## 1. 보완사항 전체 목록 (이번 버전에 반영 권장)

### 1) [필수] Admin 확정 데이터 보호 (Overwrite Protection)
자동 Job이 Admin 수정 데이터를 덮어쓰지 않도록 보호 로직을 추가한다.

**권장 방식 A: 레코드 단위 Lock**
- `is_manually_verified BOOLEAN DEFAULT FALSE`
- `verified_at TIMESTAMP`
- `verified_by UUID`

**권장 방식 B: 필드 단위 Lock (정밀)**
- `{field}_verified BOOLEAN` (예: `payload_smiles_verified`, `linker_smiles_verified`)

**규칙**
- `is_manually_verified = true` 이면 자동 Job은 **절대 overwrite 금지**
- 자동으로 바꿔야 할 변화가 있으면 **Review Queue에 Diff로만 적재**한다.

---

### 2) [필수] ID Resolver 동의어 사전(Synonym Dictionary) 강화
resolve_ids_job의 성공률은 동의어 사전 품질에 좌우된다.

**초기 구축**
- HGNC Dump 기반: `alias -> HGNC symbol` 매핑 테이블을 시딩
  - 예: `HER2, neu, CD340 -> ERBB2`
  - 예: `TROP2 -> TACSTD2`

**운영**
- Admin UI에서 “Unmapped”가 발생하면
  - `입력 텍스트`를 `정답 symbol`로 지정 → **동의어 사전에 자동 추가**

---

### 3) [필수] RDKit 전처리: Salt Remover
PubChem SMILES에는 염(HCl 등) 또는 용매가 포함되는 경우가 있어 MW/LogP가 왜곡될 수 있다.

**규칙**
- RDKit 계산 직전에 반드시:
  - Standardizer
  - SaltRemover
  - Main Fragment 선택
을 수행한다.

---

### 4) [필수] Proxy 구조 표기 강화 (payload + linker + antibody)
Proxy 기반 계산값이 “실제 구조”가 아님을 명시해야 한다.

**권장 컬럼**
- `is_proxy_payload BOOLEAN`
- `proxy_payload_reference TEXT`
- `proxy_payload_evidence_refs JSONB`
- `is_proxy_linker BOOLEAN`
- `proxy_linker_reference TEXT`
- `is_proxy_antibody BOOLEAN` (항체는 서열 미공개 케이스 대비)
- `proxy_antibody_reference TEXT`

**보고서/UI 원칙**
- Proxy 사용 시 결과 옆에 `Proxy` 배지 + “근거 링크” 표시

---

### 5) [필수] Review Queue Diff View(변경점 시각화)
Admin 검수 효율을 위해 JSON 덩어리 대신 **old vs new Diff**가 반드시 필요하다.

**요구사항**
- `old_value` vs `new_value` 컬럼 비교
- 변경된 필드만 하이라이트
  - old(빨강) / new(초록)
- Approve/Reject 시 코멘트 입력 가능

---

## 2. Step3 확장 설계 (항체/링커/페이로드 자동화)

### Step3-A) Payload SMILES 자동화 (PubChem/ChEMBL 우선)
**입력**
- `payload_exact_name`, `payload_family`, `aliases`, `drug_name_canonical`

**처리**
1) PubChem 검색(정확명/동의어) → CID 확보
2) IsomericSMILES → 표준화 → `payload_smiles_standardized`
3) 실패 시: 후보 3~5개 생성 → LLM이 “Proxy 후보 선택 + 근거 요약” → Review Queue 적재

**산출**
- `payload_smiles_standardized`
- `payload_cid`
- `is_proxy_payload`, `proxy_payload_reference`, `evidence_refs[]`

---

### Step3-B) Linker SMILES 자동화 (라이브러리 + PubChem + RAG)
링커는 구조가 공개된 표준 링커가 많으므로 **Linker Reference Library를 먼저 구축**한다.

#### (필수 테이블) linker_library
- `linker_name`
- `linker_family` (Cleavable/Non-cleavable 등)
- `trigger` (Cathepsin/pH/Disulfide 등)
- `smiles`
- `attachment_points` (maleimide/NHS 등 메타)
- `evidence_refs[]`

#### 자동화 규칙 (우선순위)
1) `drug_name/aliases` 기반 룰 매핑 (예: vedotin 계열 → vc-pabc 계열 우선 탐색)
2) `linker_family + trigger`로 linker_library 매칭
3) PubChem/문헌(RAG)에서 후보 3~5개 수집
4) LLM이 후보 중 선택 + 근거 요약 (선택 실패 시 Proxy 추천) → Review Queue 적재

---

### Step3-C) Antibody 자동화 (SMILES 대신 Identity/Sequence)
항체는 “SMILES 채움”이 아니라 아래를 채우는 자동화로 정의한다.

**입력**
- `antibody_name` 또는 `drug_name_canonical`(항체명 포함된 경우)

**처리**
1) DrugBank/ChEMBL에서 항체 표준명/ID 후보 3~5개 수집
2) UniProt 후보 수집(가능 시)
3) LLM이 후보 중 “가장 타당한 항체 ID” 선택 + 근거 요약
4) 가능한 경우 FASTA/메타를 추가로 채움

**산출**
- `antibody_name_canonical`
- `format` (mAb/bispecific)
- `uniprot_id` or `drugbank_id`
- `isotype`(가능 시)
- `evidence_refs[]`
- (가능 시) `fasta_heavy/light`, `pdb_ids`

---

## 3. LLM 사용 원칙 (필수: “후보 선택 + 근거”만)
LLM에게 “구조를 만들어라”를 시키지 않는다.  
항상 **후보 리스트를 먼저 제공**하고, LLM은 그 중 선택만 한다.

### 3.1 Proxy 선택 프롬프트 템플릿 (Payload/Linker 공통)
- 입력: 후보(이름/ID/SMILES) 3~5개 + 대상 약물 정보 + payload/linker family
- 출력(JSON 고정):
  - `selected_candidate_id`
  - `confidence` (0~1)
  - `is_proxy` (true/false)
  - `reason_short` (근거 3줄 이내)
  - `evidence_refs` (URL/PMID/특허번호)

### 3.2 “구체 후보 힌트”를 먼저 던지는 방식 권장
- Bad: “MK-2870이랑 비슷한 거 찾아줘”
- Good: “payload가 Belotecan derivative이다. Belotecan(CID: xxxx)을 Proxy로 쓰는 것이 타당한가? 근거는 무엇인가?”

---

## 4. Gate 정책 업데이트 (옵션 C 유지)
### 승격 필수(Option C)
- ✅ `resolved_target_symbol` 존재
- ✅ `payload_smiles_standardized` 존재 **또는** `is_proxy_payload = true`
- ✅ `evidence_refs >= 1`

### 승격 권장(점수 가산)
- `linker_smiles` 또는 `is_proxy_linker = true`
- `antibody_name_canonical` + (가능 시) `uniprot_id/drugbank_id`
- (선택) `clinical_nct_id_primary`

> 항체/링커는 “자동화가 완벽하지 않아도” 골든셋 확장을 막지 않도록 “권장 조건”으로 둔다.

---

## 5. DB 스키마 변경 제안 (요약)

### 5.1 golden_candidates / golden_seed_items 확장
- `resolved_target_symbol`
- `payload_smiles_standardized`
- `payload_cid`
- `linker_smiles`
- `linker_id_ref` (linker_library FK)
- `antibody_name_canonical`
- `antibody_format`
- `uniprot_id`, `drugbank_id`
- `evidence_refs JSONB` (array)
- `is_manually_verified BOOLEAN`
- `verified_by`, `verified_at`

### 5.2 Proxy 플래그
- `is_proxy_payload`, `proxy_payload_reference`, `proxy_payload_evidence_refs`
- `is_proxy_linker`, `proxy_linker_reference`
- `is_proxy_antibody`, `proxy_antibody_reference`

### 5.3 Review Queue 필수 컬럼
- `entity_type` (candidate/seed)
- `entity_id`
- `diff_json` (field별 old/new)
- `proposal_snapshot`
- `proposed_by` (job/llm/admin)
- `status` (pending/approved/rejected)
- `review_comment`

---

## 6. API / 버튼 설계 (현 구조에 그대로 추가)

### Step1 후보 수집
- `POST /api/admin/golden/run-candidates`
  - ClinicalTrials.gov 기반 후보 수집 → `golden_candidates` 적재

### Step2 구성요소 추출/표준화
- `POST /api/admin/golden/run-enrich-components`
  - resolve_ids_job + extract_components_job
  - 결과는 overwrite 금지, Review Queue로만 적재

### Step3 SMILES/Identity 채우기 (확장)
- `POST /api/admin/golden/run-enrich-chemistry`
  - (A) payload smiles
  - (B) linker smiles
  - (C) antibody identity
  - 성공/실패/Proxy 제안 모두 Review Queue 적재

### Review/승격
- `POST /api/admin/golden/review/approve`
- `POST /api/admin/golden/review/reject`
- `POST /api/admin/golden/promote` (Gate 통과 시 final로 스냅샷 승격)

---

## 7. Admin UI 보완 요구사항

### /admin/golden-sets (탭)
1) Auto: golden_candidates
- Step1/2/3 버튼
- 후보 리스트
- 상태 배지(components ready / chemistry ready / gate pass)

2) Manual: golden_seed_items
- 수동 편집
- Verified Lock 토글
- Gate checklist 표시

3) Review Queue: golden_review_queue
- Diff View (필수)
- Approve/Reject + 코멘트

4) Final: golden_final_items
- 스냅샷 보기
- CSV/JSON Export
- Proxy 배지 표시

---

## 8. 구현 우선순위 (현실적인 순서)
1) Overwrite Protection + Review Queue Diff (품질/운영의 핵심)
2) linker_library 최소 30종 구축 + 링커 자동화 Step3-B
3) payload SMILES 자동화 Step3-A 안정화 + Proxy 표기
4) antibody identity Step3-C (SMILES가 아니라 ID/포맷/근거 중심)

---

## 9. 결론
- “항체/링커까지 자동화”는 가능하되, **항체는 SMILES가 아니라 Identity/Sequence로** 정의해야 성공한다.
- LLM은 “후보 선택 + 근거 요약”만 수행하고, 결과는 **Review Queue 승인 후 반영**해야 데이터 품질과 신뢰성을 유지할 수 있다.
- Gate는 Option C(임상 NCT 비필수)로 유지하되, payload 중심 필수 + 항체/링커는 권장 조건으로 운영한다.

