# ADC 플랫폼 보고서(PDF) 생성 고도화 구현계획 (Orchestrator 적용)

> 목적: “근거 기반 + 정형 데이터 + 자동 PDF 출력”을 표준 기능으로 구축하여, 사용자가 반복적으로 **제출 가능한 수준의 상세 보고서**를 생성할 수 있도록 한다.  
> 핵심 원칙: 문서 수(2,000만 등) 경쟁이 아니라 **근거 추적성(Evidence Traceability)과 재현성(Reproducibility)**로 승부한다.

---

## 1. 목표 및 성공 기준(Success Metrics)

### 1.1 목표
- ADC 후보 설계/비교/리스크/실험계획을 **단일 실행(Run)으로 보고서(PDF) 생성**
- 모든 핵심 주장(Claim)에 **근거(Evidence) ID**를 연결
- 표/부록 중심으로 **세부 자료 출력이 풍부한 제출형 레이아웃** 제공

### 1.2 성공 기준(정량)
- **Claim → Evidence 연결률 ≥ 90%** (핵심 주장 기준)
- **근거 출처/위치 표기율 ≥ 95%** (논문/표/그림/문장 위치)
- 보고서 생성 시간: MVP 기준 **5~15분 내** (코퍼스/검색 규모에 따라 조정)
- 사용자 만족 지표(내부): “보고서 그대로 공유 가능” 응답 **≥ 70%**

---

## 2. 보고서 제품 범위(Scope)

### 2.1 MVP 보고서 유형 (우선순위)
1) **ADC 후보 설계 보고서** (1순위)
2) **표적(Target) 선정 보고서**
3) **리스크 검토(Risk Register) 보고서**
4) **실험 계획(Experiment Plan) 보고서**

### 2.2 보고서 산출물 구성(표준)
- Executive Summary (1~2p)
- Landscape (Target/Competition/Indication)
- Design Candidates (조합 후보별 상세 카드 + 비교표)
- Evidence Pack (근거 목록 + 인용 위치)
- Risk Register (리스크/근거/완화 전략/우선순위)
- Experiment Plan (in vitro → in vivo 단계별 체크리스트)
- Appendix (쿼리 로그, 용어사전, 가정 목록, 계산/룰)

---

## 3. 시스템 아키텍처(요약)

### 3.1 구성 요소
- **Frontend (Next.js)**: Run 생성, 진행률, 결과(HTML/PDF) 조회, 다운로드
- **Backend (FastAPI Engine)**: Orchestrator 실행, RAG/정규화, Report JSON 생성, PDF 렌더
- **Vector DB (Supabase pgvector)**: 청킹/임베딩 저장, 하이브리드 검색
- **Object Storage**: 결과 PDF 저장(예: S3/Supabase Storage)
- **LLM**: 검색/추론/작성/QA 역할로 분리 호출

### 3.2 핵심 데이터 흐름
1) 사용자 입력(목표/표적/적응증/제약조건) → Run 생성  
2) Evidence 수집(RAG/검색) → Evidence ID 발급  
3) 정규화/스키마 매핑 → 후보 생성/평가  
4) Report JSON 생성(정형)  
5) PDF 템플릿 렌더링 → 저장/다운로드 제공

---

## 4. 오케스트레이터(멀티 에이전트) 설계

### 4.1 에이전트 역할 정의
- **A1. Evidence Retriever**
  - 역할: 문헌/데이터에서 “원문 근거 단위” 수집 및 Evidence ID 발급
  - 산출물: `evidence[]` 초안, 커버리지 체크리스트

- **A2. Structurer (Normalizer)**
  - 역할: 근거를 ADC 스키마로 정규화(타깃/항체/링커/페이로드/DAR/독성/PK 등)
  - 산출물: `target_landscape`, `design_candidates[]` 구조화

- **A3. Analyst/Scorer**
  - 역할: 후보 우선순위 산정(룰+점수), 리스크 도출, 비교표 생성
  - 산출물: `risk_register[]`, candidate scoring, 비교표 데이터

- **A4. Report Writer**
  - 역할: 보고서 섹션별 문장화(제출형 톤), 표/부록 배치 지시
  - 제약: 모든 핵심 주장에 Evidence ID 연결 강제

- **A5. QA/Red Team (필수)**
  - 역할: 과장/환각/불일치/근거 누락 검출 및 수정 지시
  - 산출물: QA 이슈 리스트 + 수정 반영된 최종 Report JSON

> MVP는 A1~A5를 권장하나, 리소스 제약 시 A3와 A4를 통합 가능(단 QA는 유지).

### 4.2 라운드(권장 3라운드)
**Round 1: Evidence Harvest**
- 입력: 사용자 질의 + Seed(표적/적응증/제약조건) + 검색 템플릿
- 출력: `evidence[]` (원문 발췌/표/그림 캡션 포함), Evidence Index

**Round 2: Structuring & Scoring**
- 입력: evidence
- 출력: 구조화된 `design_candidates[]`, `target_landscape`, 점수/리스크

**Round 3: Composition & QA**
- 입력: 구조화 데이터 + 템플릿 규칙
- 출력: 최종 `report.json` + “PDF 렌더 ready”
- QA가 “근거 없는 주장/수치 충돌/용어 혼동”을 제거하고 재작성 지시

---

## 5. Report JSON 스키마(정형 데이터 표준)

### 5.1 최상위 구조(예시)
- `meta`
  - run_id, created_at, version, user_inputs
- `executive_summary`
- `target_landscape`
  - target_list[], expression_summary, internalization_evidence
- `design_candidates[]`
  - target, antibody, linker, payload, DAR(가능 시), rationale, pros/cons
  - `claims[]` (각 claim에 evidence_ids 필수)
- `scoring`
  - weights, candidate_scores[], explanation
- `risk_register[]`
  - risk_item, severity, likelihood, evidence_ids, mitigation
- `experiment_plan`
  - 단계별 목표/조건/endpoint/판정기준
- `evidence[]`
  - evidence_id, source_type, citation, url/doi, excerpt, location, confidence
- `assumptions[]`
- `query_log[]`
  - query, filters, timestamp, result_count
- `appendix`

### 5.2 Claim–Evidence 연결 규칙(강제)
- 모든 `claims[]`는 `evidence_ids`를 1개 이상 보유
- Evidence는 최소 필드:
  - 출처(doi/url), 발췌(excerpt), 위치(location), 신뢰도(confidence)

---

## 6. PDF 출력(렌더링) 설계

### 6.1 템플릿 전략
- **Report JSON → PDF Template 렌더링** (권장)
- 섹션별 템플릿 고정 + 표/부록 자동 확장
- “짧은 본문 + 풍부한 부록” 구조로 제출용 적합

### 6.2 PDF 핵심 기능(필수 6종)
1) **Evidence Index 페이지**: Evidence ID ↔ 출처/링크/위치
2) **표준 비교표(Table Pack)**: 후보 조합 비교표, 표적 비교표
3) **Risk Register 표**: 리스크/근거/완화/우선순위
4) **Query Log 부록**: 검색 과정 투명성
5) **Assumption Ledger**: 근거 부족은 “가정”으로 분리 표기
6) **Reproducibility Appendix**: 실험 조건/판정기준 체크리스트

### 6.3 구현 방식(옵션)
- Python 기반 PDF 생성 (예: ReportLab / WeasyPrint 등)
- 대용량 부록 대비: 페이지 자동 분할, 표 헤더 반복, 목차/북마크

---

## 7. API 연동 규격(요약)

### 7.1 Backend 엔드포인트(예시)
- `POST /api/v1/design/runs` : 보고서 Run 생성
- `GET  /api/v1/design/runs/{id}/progress` : 진행률
- `GET  /api/v1/design/runs/{id}` : Run 결과(Report JSON)
- `GET  /api/v1/design/runs/{id}/pdf` : PDF 다운로드(혹은 presigned url)

### 7.2 Run 상태 모델
- `queued` → `retrieving` → `structuring` → `writing` → `qa` → `rendering` → `done` / `failed`

---

## 8. UI/UX 구성(최소 요구)

### 8.1 Run 생성 화면
- 보고서 유형 선택
- 표적/적응증/제약조건 입력(간단 폼)
- 출력 옵션: “요약 중심 / 제출형(부록 포함)”

### 8.2 결과 화면
- 섹션별 미리보기(HTML)
- Evidence Index 탐색
- PDF 다운로드
- “근거 부족/가정 목록” 표시(투명성)

---

## 9. 품질 보증(QA) 및 평가 체계

### 9.1 자동 QA 체크리스트(필수)
- Claim에 Evidence가 없는 문장 검출
- 수치/용어 불일치(예: 동일 후보의 payload 표기가 다름)
- 과장 표현(“확실히/완벽히/치료” 등) 제거
- 출처 없는 비교/순위 주장 금지

### 9.2 리그레션 테스트(권장)
- 동일 입력에 대해 Report JSON 스키마 유효성 검사
- PDF 렌더 실패율 측정 및 복구 로직

---

## 10. 단계별 구현 계획(권장 로드맵)

### Phase 0 (1~2주): 기반 정리
- Report JSON 스키마 확정
- PDF 템플릿 초안(목차/표준 표/부록 틀)
- Run 상태/저장소/파일 저장 규칙 확정

### Phase 1 (2~4주): Orchestrator MVP
- A1~A5 라운드 3단계 구현
- Evidence ID 발급 + Claim–Evidence 강제 연결
- Report JSON 생성 후 HTML preview까지

### Phase 2 (2~4주): PDF 고도화
- Table Pack, Risk Register, Evidence Index 완성
- Query Log/Assumption Ledger/Experiment Appendix 추가
- 대용량 부록 최적화(페이지/목차/북마크)

### Phase 3 (지속): 데이터 확장/정확도 강화
- ADC 특화 용어사전/정규화 룰 강화
- 신규 소스 커넥터 추가(특허/임상/기업 파이프라인 등)
- 평가셋 구축(정답/근거 세트)

---

## 11. 리스크 및 대응

- **데이터 규모 열세**: “ADC 특화 코퍼스 + 구조화 품질”로 포지셔닝
- **환각/과장**: QA/Red Team 강제 + Claim–Evidence 규칙
- **PDF 복잡도 증가**: JSON 기반 템플릿 렌더로 구조 안정화
- **근거 저작권 이슈**: 본문 인용은 최소 발췌, 부록은 링크/서지 중심(원문 대량 복제 금지)

---

## 12. 의사결정 포인트(고정해야 할 것)
- MVP 보고서 1순위: **ADC 후보 설계 보고서**
- PDF 스타일: “제출형(부록 확장)”을 기본값으로
- Claim–Evidence 규칙: 예외 없이 강제(품질의 핵심)

---

## 부록 A. “ADC 후보 설계 보고서” 권장 목차(예시)
1. Executive Summary  
2. Problem Definition & Constraints  
3. Target Landscape  
4. Design Candidates Overview (비교표)  
5. Candidate 1..N Deep Dive (Claim–Evidence 포함)  
6. Risk Register  
7. Experiment Plan (in vitro/in vivo)  
8. Evidence Index  
9. Query Log / Assumptions  
10. Appendix (용어사전, 룰/점수 가중치)

---

## 부록 B. 산출물 파일 구조(권장)
- `/runs/{run_id}/report.json`
- `/runs/{run_id}/report.pdf`
- `/runs/{run_id}/artifacts/figures/*` (차트/표 이미지)
- `/runs/{run_id}/logs/query_log.json`

---
