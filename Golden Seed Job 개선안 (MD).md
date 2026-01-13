# Golden Seed Job 개선안 (MD)  
작성일: 2026-01-13  
대상: `golden_seed_job.py` (Design Engine Version) / ClinicalTrials 기반 Golden 후보 생성 파이프라인  
목표: **링커/페이로드 Unknown 문제 해소 + 엉뚱한 항체 매핑 제거 + ADC 후보 생성 품질 정상화**  
전제: 현재 시스템 구조(Profiles → RAW 저장 → Resolver → 승격/Upsert)는 최대한 유지한다.

---

## 1. 현상 정리 (현재 결과가 이상한 이유)

### 1.1 링커/페이로드가 대부분 Unknown
- ClinicalTrials 원천에는 **linker/payload 구조화 필드가 없다**.
- 현 상태에서는 텍스트 기반 추출만 하며, 사전/규칙이 부족해 대부분 매칭 실패.
- 특히 `vedotin/deruxtecan/govitecan/...`을 **linker로 저장**하고 있는데, 이는 구조적으로 잘못이다.

### 1.2 유명 항암제/비관련 약물이 섞여 들어옴
- QueryProfile 검색이 충분히 좁지 않아 `placebo tablet`, `insulin`, `radiotracer(Tc99m...)` 같은 비-ADC 후보가 섞임.
- Oncology 필터/ADC 신호 필터가 부족하거나 “승격 게이트”가 약해서 후보 테이블까지 들어간다.

### 1.3 antibody 컬럼 매핑이 깨짐(중요)
- `antibody_text = text.split(" ")[1].capitalize()` 로직은 ClinicalTrials intervention 포맷에서 거의 랜덤.
- 그 결과 “Cisplatin이 antibody로 들어가는” 같은 데이터 왜곡이 발생.

---

## 2. 핵심 설계 원칙 (레고처럼 보이지 않게 하는 기준)

### 2.1 Suffix는 Linker가 아니다
- `vedotin`, `deruxtecan`, `govitecan`, `mertansine`, `ozogamicin` 등은
  - **링커가 아니라 ADC 약물명 접미사(페이로드/계열 신호)**에 가깝다.
- 따라서:
  - `linker`에 저장하지 않는다.
  - 별도 `suffix_signal` 또는 `payload_family`로 분리하여 저장/추론에 사용한다.

### 2.2 Antibody는 “확실할 때만” 채운다
- 항체 추출은 **-mab 패턴 / catalog 기반 매칭**으로만 수행.
- 확신이 없으면 Unknown 유지(억지로 채우면 데이터가 무너짐).

### 2.3 승격(FINAL) 조건은 “근거 + 매핑 신뢰”를 동시에 만족해야 한다
- 후보가 FINAL로 승격되려면:
  - `mapping_confidence >= threshold`
  - `evidence` 최소 기준 충족(단순 NCT 1개가 아니라 evidence 타입/커버리지 기준 권장)
- 그렇지 않으면 RAW로만 저장하고 Admin Review Queue로 보낸다.

---

## 3. 구조적 문제점 및 수정 우선순위

## 3.1 (P0) Extract 단계 오류 수정: linker/payload/antibody 추출 재설계
### 문제
- linker에 suffix를 넣음 → 데이터 왜곡
- antibody token split → 랜덤값 저장

### 수정안
- `suffix_signal` 별도 분리
- payload는 suffix 기반 1차 추론 + payload dictionary 기반 2차 추출
- antibody는 -mab 패턴 또는 component_catalog 매칭 기반

---

## 3.2 (P0) Upsert 충돌키 설계 오류 수정
### 문제
- 현재 `on_conflict="golden_set_id,source_ref"`이며 `source_ref = nct_id` 수준
- 동일 NCT 내 여러 intervention/arm 후보가 **덮어쓰기** 되는 구조

### 수정안 (권장 순서)
1) `on_conflict="golden_set_id,program_key"`
2) 혹은 `golden_set_id,raw_data_id`

> program_key는 이미 존재하므로 최소 변경으로 해결 가능.

---

## 3.3 (P0) RAW 테이블 중복 폭발 방지 (lineage 안정화)
### 문제
- `_save_raw_data()`가 무조건 insert → 동일 NCT 반복 실행 시 RAW 무한 적재

### 수정안
- `golden_seed_raw`에 Unique Index 추가:
  - `(source, source_hash)` 또는 `(source, source_id, source_hash)`
- insert 대신 upsert 사용 → 같은 raw는 재사용
- `raw_data_id`를 안정적으로 참조 가능

---

## 3.4 (P1) Evidence 설계 개선 (min_evidence 의미 있게)
### 문제
- 지금 evidence_refs가 사실상 `[nct_id]` 뿐이라 min_evidence=1이면 다 통과

### 수정안
- ClinicalTrials에서 `referencesModule`을 파싱해 PMID/논문 링크를 evidence에 추가
- `min_evidence`를 단순 개수가 아니라 evidence 타입 기준으로 설계 권장:
  - 최소 clinical 1개(NCT)
  - publication이 있으면 가산점/승격 우대

---

## 4. 권장 데이터 모델 변화 (최소 변경 버전)

### 4.1 golden_seed_raw (이미 계획 반영)
필수 컬럼(요약):
- `source`, `source_id(nct_id)`, `source_hash`
- `raw_payload(jsonb)`
- `query_profile`, `parser_version`, `dataset_version`
- (권장) `fetched_at`, `conditions`, `interventions(list)` 추출본

### 4.2 golden_candidates (현재 컬럼 유지 + 최소 보강)
- `program_key` (이미 사용)
- `raw_data_id` (이미 사용)
- `mapping_confidence`, `confidence_score`, `is_final` (이미 사용)
- (권장) `suffix_signal` 또는 `payload_family` 컬럼 추가(추론 근거로 남김)

---

## 5. 구현 패치 가이드 (코드 레벨)

## 5.1 `_extract_and_resolve()` 재구성 (권장 로직)
### 입력
- raw.intervention (현재: "Drug: {drug_name}")

### 출력 (텍스트 + resolved)
- `antibody_text`, `target_text`, `payload_text`, `linker_text`, `suffix_signal`
- `mapping_confidence` (Unknown은 confidence=0 처리 권장)
- (선택) `payload_id/linker_id/antibody_id/target_id`

### Payload 추론(권장)
1) suffix 기반:
- vedotin → payload = MMAE (또는 “MMAE-family”)
- deruxtecan → payload = DXd-family
- govitecan → payload = SN-38
- mertansine → payload = DM1
- ozogamicin → payload = calicheamicin

2) payload dictionary 기반:
- `PAYLOAD_DICTIONARY`에서 키워드 탐색

### Linker 처리(권장)
- ClinicalTrials에서 linker는 거의 안 나오므로:
  - 기본 Unknown
  - linker dictionary에서 명시적 패턴이 있을 때만 채움

### Antibody 추출(권장)
- `\b[a-z0-9-]+mab\b` 정규식 기반 추출
- 또는 catalog(type=antibody) synonyms 매칭
- 없으면 Unknown(억지 추정 금지)

### Target 추출(권장)
- antibody가 확정되면 **antibody→target 매핑 룰/테이블**로 결정
- (예시 룰)
  - trastuzumab → HER2
  - datopotamab → TROP2
- unknown이면 target Unknown 유지

---

## 5.2 `_save_raw_data()`를 Upsert로 변경 (중복 방지)
- source_hash: raw_item JSON dump 기반 sha256 유지 가능
- DB에 Unique Index 추가 후:
  - insert 대신 upsert + ID 반환 방식으로 변경

---

## 5.3 Upsert 충돌키 변경
현재:
- `on_conflict="golden_set_id,source_ref"` (source_ref=nct_id)

권장:
- `on_conflict="golden_set_id,program_key"`

이렇게 하면 같은 NCT 내 후보들이 덮어쓰지 않고 정상 축적됨.

---

## 5.4 승격(FINAL) 조건 재정의(권장)
현재:
- mapping_conf >= 0.8 AND len(evidence_refs) >= min_evidence

개선:
- `mapping_confidence`는 Unknown 포함 평균이 아니라, **확정된 컴포넌트만 평균**하거나 Unknown은 0으로 처리
- evidence는 “clinical(NCT)”만 있는 경우 FINAL 승격을 더 보수적으로:
  - 예: publication evidence가 없으면 FINAL=False 또는 confidence_score 제한

---

## 6. 운영 전략: Admin Review Queue 연동(수기관리 포함)

### 6.1 왜 필요한가
- ClinicalTrials만으로 linker/payload 완전 자동화는 어렵다.
- 따라서 Raw/Low-confidence 후보를 Admin이 검수하여 Golden 후보를 확정하는 흐름이 필요.

### 6.2 권장 흐름
1) 워커가 Raw 수집 + 기본 추론/매핑 수행
2) 승격 조건 미달 후보는 `review_queue`에 적재
3) Admin이:
   - 항체/표적 확정
   - payload family 확정
   - evidence_refs 보강
   - 최종 승인(is_final=true) 처리

---

## 7. 즉시 적용 체크리스트 (오늘 수정하면 바로 개선되는 것)

- [ ] `vedotin/deruxtecan/govitecan/...`을 linker에 넣는 로직 제거
- [ ] antibody 추출: token split 제거, -mab/cat 매칭 기반으로 변경
- [ ] golden_candidates upsert conflict key를 `program_key` 중심으로 변경
- [ ] golden_seed_raw 중복 방지 unique index + upsert 적용
- [ ] Oncology/ADC 필터 강화(승격 게이트 또는 fetch 단계)

---

## 8. 기대 효과 (수정 후)
- `placebo/insulin` 같은 비관련 후보가 golden_candidates에 들어가는 비율 급감
- antibody 컬럼이 “약물명”으로 오염되는 현상 제거
- payload는 suffix 기반으로 최소한의 유의미한 추론이 가능해져 Unknown 감소
- NCT 단위 덮어쓰기 문제 해소 → 후보군이 정상적으로 축적
- 이후 Report/Recommendation 엔진에서 “근거 연결(evidence)” 기반으로 풍부한 보고서 생성 가능

---
