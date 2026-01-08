# ADC 플랫폼 구축 — 수정/보완/추가 사항 통합 체크리스트 (Implementation Readiness) v1.3
본 문서는 현재까지의 설계(v1.1 블루프린트/운영가이드)를 기준으로, **구현 착수 전 “반드시 확정/준비/검증”해야 할 항목**을 한 장으로 정리한 실행 문서입니다.  
(목표: Phase 0 준비 완료 → Phase 1 개발 착수)

---

## 0) 결정 사항(확정안)
아래 항목은 “미지정” 상태를 해소하기 위해 **권장안을 ‘확정안’으로 정리**합니다. (변경 가능하나, 변경 시 영향 범위를 명시해야 합니다)

### 0.1 Embedding 모델 선택(확정)
- **Public Literature Index:** `OpenAI text-embedding-3-small`  
- **Private Workspace Index(사내 미발표/민감 데이터):** 로컬 임베딩(BGE 계열, 예: `bge-m3`) **옵션/2단계**
- 운영 규칙:
  - `embedding_model_id`로 **모델별 인덱스 분리**
  - 차원(dims) 변경도 “다른 모델 버전”으로 취급

### 0.2 LLM 선택(확정)
- **RAG/Protocol/Verifier:** **Gemini API**를 기본 채택
- 운영 규칙:
  - JSON Schema 기반 **Structured Output 강제**
  - Provider 추상화(LLMClient 인터페이스)로 GPT/Claude 대체 가능하도록 설계

### 0.3 Bio-Fit / Safety-Fit 산식(확정: v0.2)
- **Eng-Fit(v0.2)와 동일하게** `Score = 100 - Risk` 구조로 **벡터화 산식**을 적용한다.
- 산식은 “term(항)” 단위로 분해해 저장하고(`score_components`, `feature_importance`), `scoring_params(version)`로 런 단위 고정한다.


### Eng-Fit (v0.2, 확정)
- `EngFit = 100 - CMC_Risk`
- `CMC_Risk = clip(`
  - `w_agg * AggRisk`
  - `+ w_proc * ProcRisk`
  - `+ w_anal * AnalRisk`
  - `+ w_unc * UncPenalty`
  - `, 0, 100)`
- 정의(0~100 스케일):
  - `AggRisk = clip( ω_logP * max(0, LogP - 2.0) + ω_DAR * max(0, DAR - 4.0) + ω_patch * H_patch , 0, 100)`
    - `H_patch`: RDKit 기반 소수성 패치 점수(예: hydrophobic patch)
  - `ProcRisk`: 공정 복잡도 점수(예: site-specific 여부, 정제 난이도) — 초기에는 룰/태그 기반
  - `AnalRisk`: 분석 난이도(예: DAR 분포/응집 분석 요구) — 초기에는 룰/태그 기반
  - `UncPenalty`: 불확실성 페널티(필수 피처 결측 시)

저장 규칙:
- `candidate_scores.score_components.eng_fit`에 `AggRisk/ProcRisk/AnalRisk/UncPenalty/CMC_Risk` 저장
- `feature_importance`에 term 단위(최소) 영향도 저장

**Bio-Fit (v0.2, 예시 템플릿)**  
- `BioFit = 100 - BioRisk`
- `BioRisk = clip(`
  - `w_dea * (100 - DEA)`  
  - `+ w_int * max(0, Int_threshold - INT)`  
  - `+ w_het * HET_pen`  
  - `+ w_acc * ACC_pen`  
  - `+ w_bs  * (100 - BS_match)`
  - `, 0, 100)`
- 정의(0~100 스케일):
  - `DEA = clip(50 + k_dea * (log2(T_expr_tumor+1) - log2(N_expr_max+1)), 0, 100)`
  - `INT = 100 * internalization(0~1)`
  - `HET_pen = 100 * heterogeneity(0~1)`
  - `ACC_pen = 100 * (1 - accessibility)(0~1)`
  - `BS_match = 100 * (1 - abs(bystander_need - bystander_capability))`

**Safety-Fit (v0.2, 예시 템플릿)**  
- `SafetyFit = 100 - SafetyRisk`
- `SafetyRisk = clip(`
  - `w_oot * OOT`  
  - `+ w_haz * PH`  
  - `+ w_clv * CLV`  
  - `+ w_sar * SAR`  
  - `+ w_neg * NEG`
  - `, 0, 100)`
- 정의(0~100 스케일):
  - `OOT = clip(k_oot * log2(N_expr_max+1) + k_crit*critical_tissue_flag, 0, 100)`
  - `PH = 100 * payload_hazard(0~1)`
  - `CLV = 100 * cleavage_risk(0~1)`
  - `SAR = systemic_exposure_proxy(0~100)` *(Eng-Fit의 노출/응집 proxy 재사용 권장)*
  - `NEG = 100 * negative_signal(0~1)` *(부정 근거/독성/중단 시그널)*

저장 규칙:
- `candidate_scores.score_components.{bio_fit,safety_fit}`에 term별 값 및 Risk 합산값 저장
- `feature_importance`에 term 단위(최소) 영향도 저장(예: SHAP 또는 단순 기여도)


### 0.4 초기 카탈로그 데이터(확정: Seed + Growth)
- **Seed Catalog(검수된 소량) → 운영 중 확장(Growth)** 전략
- MVP 권장 수량:
  - Targets: 50~150
  - Payloads: 15~30
  - Linkers: 10~25
  - Antibody Templates: 10~40(서열이 아닌 “속성 템플릿” 중심)
- 품질 등급:
  - Gold / Silver / Bronze(조합 입력 허용 범위 차등)

### 0.5 워커 기술 선택(확정)
- **Arq(Redis 기반)** 확정  
- 큐 분리(권장 최소):
  - `design_run_queue`(조합/스코어)
  - `cheminf_queue`(RDKit 프리컴퓨트)
  - `literature_queue`(인덱싱/임베딩)
  - `rag_queue`(RAG/Verifier/Protocol)

### 0.6 FastAPI 배포 방식(확정)
- **MVP~초기 운영: VM 배포 확정**
- 스케일 단계: VM → ECS 또는 Cloud Run로 이관(필요 시)

---

## 1) ✅ 결정 완료 항목(요약표)
| 항목 | 확정 내용 |
|---|---|
| Embedding 모델 | Public=OpenAI `text-embedding-3-small`, Private=로컬 BGE 옵션 |
| LLM 선택 | Gemini API (Structured Output + Provider 추상화) |
| Eng/Bio/Safety-Fit 산식 | v0.2 벡터화 산식 확정 |
| 초기 카탈로그 데이터 | Seed + Growth 전략, Gold/Silver/Bronze 등급 |
| 워커 기술 | Arq 확정 (큐 분리, 재시도/백오프, idempotency) |
| FastAPI 배포 | VM 확정 (확장 시 ECS/Cloud Run) |



## 2) 🟡 보완 권장 사항(문서화/운영)
> 아래는 **운영 리스크를 크게 낮추는 항목**이며, MVP 전까지 최소 1회 문서/정책으로 고정합니다.

### 2.1 환경 구성 문서화(완료)
- `.env` 변수 목록: Supabase/Redis/RDKit/Embedding/LLM/Literature connector
- 로컬 개발환경 설정 가이드
- 에러 핸들링/폴백/레이트리밋 대응
- 성능 벤치마크 목표(10k 후보, 문헌 검색 SLA)
- 테스트 전략(Unit/Integration/E2E)
- 산식 검증(Golden Set + Regression)

> 참고: `adc_environment_ops_guide.md`에 정리됨(레포 docs/로 이동 권장)

---

## 3) 🔑 구현 시작 전 사전 체크(필수)
### 3.1 Critical(🔴) 체크리스트
- [ ] **Redis 연결 정보 확보**
  - Managed Redis(Upstash/Redis Cloud) 또는 VM Redis
  - Arq 워커 연결용 URL/Password
- [ ] **Supabase pgvector 활성화**  
  - Dashboard → Database → Extensions → `vector` Enable  
  - 또는 SQL: `create extension if not exists vector;`
- [ ] **RDKit 설치 환경 확정**  
  - 권장: Docker(또는 conda)로 엔진/워커에 RDKit 포함
- [ ] **API 키 확보**  
  - Gemini API Key(LLM)
  - OpenAI API Key(embedding, Public index)
  - PubMed(E-utilities) 관련 키/식별(선택이지만 권장)
- [ ] **Secrets 관리 방식 확정**  
  - Vercel env / VM secret store / CI secret 등 (키 노출 금지)

### 3.2 High(🟡) 체크리스트
- [ ] Supabase 플랜 확인: DB/Storage 용량, RLS 사용, 성능/동시성
- [ ] 도메인 전문가 참여 확정: 룰셋/카탈로그 검수/파라미터 검증
- [ ] 저작권/라이선스 확인: PubMed 데이터 사용 조건, 인용 정책(Forced citations 정책 포함)

### 3.3 Medium(🟠) 체크리스트
- [ ] 비용 추정: Vercel/Supabase/API(Embedding/LLM) 월간 사용량 기반

---

## 4) ⚠️ 기술적 위험 요소 및 대응(요약)
### 4.1 조합 폭발(Cartesian explosion)
- 위험: 5개 요소 조합 시 수백만 후보 가능
- 대응:
  - Generator 패턴 + 배치 처리(예: 500 단위)
  - Hard cut / hard reject + 요약 테이블만 저장
  - Vectorized scoring(루프 금지)

### 4.2 LLM Hallucination/잘못된 인용
- 위험: RAG가 근거를 왜곡하거나 임의 인용 생성
- 대응:
  - Forced Evidence 규격(인용 없으면 “Assumption” 라벨)
  - Verifier 단계(인용 스팬/정합성 검사)
  - (고도화) NLI 기반 검증

### 4.3 RDKit 의존성/설치 복잡(특히 Windows)
- 대응: Docker 이미지로 엔진/워커 표준화(권장)


### 4.4 Negative Data 처리(운영 리스크)
- 위험: 실패/독성/중단 사례를 무시하면 동일 실수를 반복할 가능성이 높음
- 대응:
  - 문헌 chunk에 `polarity` 태그 부여 (`positive`/`negative`/`neutral`)
  - 특정 리스크 플래그 존재 시 **negative polarity chunk 가중치 부스팅**(Risk-first retrieval)
  - UI에 “Risk discovered” 배지/배너 표시(근거 링크 포함)


### 4.5 운영 장애 대응 정책(필수)
- **Embedding API 장애**
  - 기본: 큐 재시도(max 3회, exponential backoff + jitter)
  - 폴백: (선택) 로컬 BGE 임베딩 서비스로 전환 또는 “BM25-only 검색”으로 강등 운영
- **LLM API Rate Limit/장애**
  - 429 발생 시: 60초 대기 후 재시도(지수 백오프 적용 가능)
  - 우선순위: Top-N(예: 50) 후보에 대해 RAG/Protocol 우선 처리, 나머지는 지연/배치 처리
  - Verifier 실패 시: “Needs Review” 라벨 + 재검증 큐로 이관
- **RDKit 계산 타임아웃/실패**
  - 단일 컴포넌트 계산 제한(권장 60초)
  - 초과/실패 시: `component_catalog.status='failed'` + 원인 로그 저장 + 수동 재시도 UI
- **Supabase 연결 장애**
  - Engine/Worker health check 엔드포인트 제공
  - 장애 감지 시 알림(Slack/Email 등) + 큐 작업 pause(옵션)
  - 장기 장애 시: run 실행은 중단하고 UI에 상태를 “Paused/Degraded”로 표시

---

## 5) 📋 즉시 준비해야 할 사항(Phase 0: 구현 착수 전)
| 항목 | 설명 | 담당 |
|---|---|---|
| Supabase 프로젝트 생성 | Dev/Prod 분리, pgvector 활성화 | 개발 |
| API 키 발급 | Supabase, Gemini, OpenAI, PubMed | 개발 |
| 개발 환경 Docker 구성 | Python 3.11 + RDKit + FastAPI + Redis | 개발 |
| 초기 카탈로그 데이터 | Gold Standard Target 리스트(최소 100~200) + 속성/근거 | 도메인 |
| 룰셋 초안 | `ruleset_v0.1.yaml` 초안(필터/페널티/알림 규칙) | 도메인 |
| 스코어링 파라미터 | Bio/Safety/Eng 가중치/임계값 v0.2 | 도메인 |
| Golden Set | 산식 회귀 검증용 케이스 20~50 | 도메인+개발 |

> 아래 5.5~5.10은 DDL/정책 등 기술적 준비 상세 항목입니다.

---


### 5.5 DDL 체크(Phase 0)
- [ ] 추가 테이블 DDL 반영:
  - `candidate_reject_summaries` (하드리젝트 요약)
  - `run_progress` (진행률 추적)
  - `evidence_signals` (문헌 polarity: positive/negative/neutral)
  - `scoring_params` (버전화된 스코어링 파라미터)
  - `candidate_rule_hits` (룰 적중 로그)
  - `rule_performance` (룰 신뢰도/성공률 집계)
  - `run_pareto_fronts` (파레토 프론트 메타)
  - `run_pareto_members` (파레토 프론트 멤버 후보)

### 5.6 카탈로그 상태 관리(Phase 0)
- [ ] `component_catalog.status` 컬럼 추가 (pending_compute/active/failed/deprecated)
- [ ] **active-only** 조합 입력 정책 확정
- [ ] pending 컴포넌트 존재 시 런 실행 정책 확정(차단 vs 경고 후 제한 실행)
- [ ] RDKit 실패(`failed`) 재시도/복구 정책(최대 재시도, 원인 로그, 수동 수정 흐름)

### 5.7 피드백 시스템(Human-in-the-loop, Phase 1)
- [ ] `human_feedback` 테이블 DDL 반영
- [ ] 후보/근거/프로토콜에 대한 동의/비동의/코멘트 UI
- [ ] outlier 제외 플래그 정책 확정:
  - `assay_results.is_outlier` 또는
  - `human_feedback.exclude_from_training`



### 5.8 문헌 Connector 인터페이스(Phase 1)
- [ ] PubMed Connector 표준 인터페이스 구현:
  - `fetch_since(cursor)` : 증분 수집(커서 기반)
  - `normalize(record)` : 메타 정규화(PMID/DOI/저자/연도 등)
  - `emit_chunks(doc)` : 청킹(권장 300~800 tokens)
  - `extract_entities(doc)` : 엔티티 태깅(옵션; Target/Linker/Payload 등)
- [ ] 증분 커서 관리 방식 확정:
  - `literature_ingestion_cursors` 테이블(권장) 또는
  - `connector_state` JSONB(대안)
- [ ] 재처리 정책:
  - 동일 PMID/DOI upsert
  - chunk 재생성은 문서 버전 변경 시에만

### 5.9 프로토콜 템플릿 준비(Phase 1~2)
- [ ] 초기 템플릿 목록 정의(권장 최소 세트):
  - SEC (Aggregation check)
  - HIC (Hydrophobicity profile)
  - Plasma stability + free drug LC-MS
  - Internalization kinetics
  - Cytotoxicity panel (target-high/low cell lines)
- [ ] 템플릿 저장 방식 확정:
  - (A) 코드/YAML(초기 권장, 변경 이력은 git)
  - (B) `protocol_templates` 테이블(운영 UI 필요 시)
- [ ] 템플릿 ↔ 룰 연결 정책:
  - 특정 리스크/룰 적중 시 템플릿 자동 추가(예: AggRisk 높으면 SEC 필수)

### 5.10 RLS 정책(Phase 0~1)
- [ ] workspace_id 기반 RLS 적용 범위 확정:
  - `design_runs`, `candidates`, `candidate_scores`
  - `candidate_evidence`, `candidate_protocols`
  - `candidate_rule_hits`, `human_feedback`, `assay_results`
  - `component_catalog` (workspace custom 컴포넌트)
  - `literature_documents`, `literature_chunks` (private 문헌)
- [ ] public 문헌(workspace_id IS NULL) 읽기 허용 정책 확정
- [ ] 인증/식별 방식 확정:
  - JWT에 `workspace_id` 포함 또는
  - 사용자-워크스페이스 매핑 테이블로 서버에서 강제
- [ ] 보안 테스트(섹션 9.6)로 workspace 격리 검증 필수



### 5.11 감사 로그(Audit Events, Phase 0~1)
- [ ] `audit_events` 테이블 DDL 반영(블루프린트 §9.2)
- [ ] 필수 기록 대상:
  - Run 생성/실행/완료
  - 룰셋/모델셋 변경(scoring_params, ruleset 버전)
  - 문헌 인덱싱 실행/재실행
  - 후보 export/리포트 생성
  - 카탈로그 컴포넌트 추가/수정/삭제(deprecated 포함)
- [ ] 로그 보존 정책 확정(예: 1년 보관) + 개인정보/민감정보 마스킹 규칙


## 6) 🛠️ 기술 스택 준비(확정 구성)
- Frontend: Next.js 14+(App Router) + Supabase Auth
- Backend: FastAPI(Engine) + Arq(Worker)
- DB: Supabase(Postgres + RLS + pgvector)
- Cheminformatics: RDKit(Engine/Worker)
- Embedding: OpenAI `text-embedding-3-small`(Public) + 로컬(BGE 옵션, Private)
- LLM: Gemini(API)
- Deployment:
  - Web: Vercel
  - Engine/Worker: VM(Docker) + Redis(Managed 권장)

---

## 7) 📚 문서화 산출물(레포에 반드시 포함)
### 7.1 필수 문서
- [ ] `docs/env.md` : 환경 변수(.env.example) + 운영 시크릿 정책
- [ ] `docs/local-dev.md` : 로컬 개발환경 설정
- [ ] `docs/api.md` : FastAPI OpenAPI/Swagger 링크 및 주요 엔드포인트 요약
- [ ] `docs/db.md` : DB 스키마(DDL) + ERD(이미지 또는 링크)
- [ ] `docs/deploy.md` : Vercel/VM 배포 절차 + 롤백 정책
- [ ] `docs/benchmarks.md` : 성능 목표/측정 방법/결과 기록
- [ ] `docs/cheminformatics.md` : RDKit 디스크립터 목록 + 계산 파이프라인
- [ ] `docs/evidence.md` : Evidence Engine 규격(하이브리드 검색, Forced Evidence, Conflict Alert)
- [ ] `docs/protocol-templates.md` : 프로토콜 템플릿 목록 + 룰 연결 정책

### 7.2 추천 문서
- [ ] `docs/rules.md` : 룰 엔진 YAML 규격 + 샘플
- [ ] `docs/scoring.md` : Eng/Bio/Safety 산식 + scoring_params versioning 정책
- [ ] `docs/security.md` : RLS 정책/테넌시 격리/로그 보안

---

## 8) 성능/품질 기준(초기 합격선)
### 8.1 성능 벤치마크
- 후보 10,000개:
  - 조합 생성 + 하드리젝트 요약 + 벡터화 스코어 + 파레토 계산 **≤ 60초**
  - Evidence/RAG/Protocol은 비동기(Top-N=50 우선) **≤ 90초**
- 문헌 검색 SLA:
  - evidence lookup p95 **≤ 1.0초**
  - 일반 검색 p95 **≤ 2.0초**

### 8.2 품질/신뢰 기준
- **Forced Evidence:**
  - 인용 없는 주장 → "Assumption"으로 라벨링되어야 통과
- **설명 가능성:**
  - 모든 후보에 대해 `score_components`(term) 최소 3개 이상 제공
- **Conflict Alert 트리거:**
  - 동일 주제에 찬성/반대 근거가 동시 존재
  - 인용 수 < 2 + 불확실성(결측/추정) 높음
  - 실험 조건이 다른 상반된 결론(조건 불일치)



---

## 9) 테스트 범위(최소 합격선)
### 9.1 Unit
- scoring 산식(Eng/Bio/Safety) term별 수치 테스트
- 룰 엔진 YAML 파싱/평가
- RDKit 계산(정상/실패 케이스)
- chunking 로직

### 9.2 Integration
- run 생성→worker 실행→완료→결과 조회(E2E의 전 단계)
- embedding/LLM은 mock 기본, 별도 스모크 테스트로 실 API 확인

### 9.3 E2E(Playwright)
- Run 생성/완료
- 후보 상세(근거/프로토콜 표시)
- 비교 + 피드백 저장

### 9.4 산식 검증(Golden Set)
- golden_set(20~50) 기반 회귀 테스트
- scoring_params 변경 시 편차/순위 변동을 승인 절차로 관리


### 9.5 Evidence/RAG 테스트
- Forced Evidence 규격 검증(인용 누락 시 "Assumption" 라벨)
- Conflict Alert 트리거 조건 테스트
- Negative polarity retrieval 부스팅 테스트

### 9.6 보안/RLS 테스트
- workspace 격리 검증(다른 테넌트 데이터 접근 불가)
- private 문헌 접근 제어 테스트

---

## 10) 실행 권장 순서(Phase 0 → Phase 1)
### Phase 0 (준비, 3~7일)
1) Supabase dev/prod + pgvector 활성화
2) Docker 기반 Engine/Worker 기본 이미지 구축(RDKit 포함)
3) API 키 세팅 + `.env.example` 커밋
4) Seed Catalog 템플릿(CSV) + Gold 1차 입력
5) ruleset_v0.1.yaml + scoring_params v0.2 확정
6) Golden set 준비

### Phase 1 (개발 착수, 2~4주)
1) catalog 등록 + async-precompute(pending→active)
2) run 생성/배치 후보 생성/벡터화 스코어/파레토
3) 문헌 ingestion + chunk + embedding + 검색
4) Forced Evidence RAG + Protocol 생성 + Verifier
5) UI 구현:
   - 런 리스트/상세
   - 후보 리스트/상세(근거/프로토콜 표시)
   - 피드백 입력
6) 후보 비교 화면(`/design/runs/[runId]/compare?ids=a,b`):
   - 4축 점수 병렬 비교
   - term 기여도 비교
   - 근거(positive/negative) 분리 표시
   - 프로토콜 차이점(diff) 표시

### Phase 2~4 (개략, 별도 상세 계획)
- **Phase 2 (2~3주):** Rule Engine + Protocol Generator 심화(템플릿/룰 커버리지 확대, rule_performance 활용)
- **Phase 3 (3~4주):** Evidence Engine MVP 고도화 + 문헌 인덱싱 파이프라인 안정화(negative polarity 강화)
- **Phase 4 (지속):** 운영 안정화 + 학습 루프(assay → rule 튜닝, scoring_params 고도화)

> 상세 일정/리소스는 별도 프로젝트 계획 문서에서 관리한다.



---

## 부록 A) 즉시 생성할 파일 목록(.env.example)
- `apps/web/.env.example`
- `services/engine/.env.example`
- `services/worker/.env.example`

---

## 부록 B) 담당자별 산출물 체크(최소)
### 개발자
- Supabase 프로젝트/DDL/RLS/pgvector
- Docker/배포(VM)
- Engine/Worker 실행/로그/재시도
- Bench/Tests 자동화

### 도메인 전문가
- Target Gold 목록(근거 포함)
- Payload/Linker 위험도 태그 정의
- ruleset_v0.1.yaml
- scoring_params v0.2(가중치/임계값)
- golden_set


---

---

## 부록 C) Worker 실행 순서(design_run_execute)
`design_run_execute(run_id)` 워커 job의 표준 실행 순서:

1. **입력 정규화** + `scoring_version` 고정 (재현성 확보)
2. **카탈로그 로드** (`status='active'`만 조회)
3. **후보 생성** (generator 패턴) + 하드리젝트 → `candidate_reject_summaries`
4. **배치 벡터화 스코어 계산** (Eng/Bio/Safety 4축)
5. **룰 적용** (배치/후처리) + `candidate_rule_hits` 기록
6. **파레토 프론트 계산** → `run_pareto_fronts`, `run_pareto_members`
7. **Evidence Engine** (Risk-first + negative polarity) + Forced citations → `candidate_evidence`
8. **Protocol 생성** (템플릿 기반) → `candidate_protocols`
9. **상태 업데이트** + `run_progress` 완료 기록

> 각 단계는 `run_progress.phase`에 기록되어 진행률 추적 가능



## 📝 통합 요약(v1.3 최종본)
| 구분 | 항목 수 | 상세 |
|---|---:|---|
| ✅ v1.1→v1.2 반영 완료 | 7 | Eng-Fit 산식, Connector 인터페이스, 프로토콜 템플릿, RLS 정책, 섹션 형식 정리 등 |
| 🔴 v1.3 추가 반영 | 4 | Worker 실행 순서(부록 C), 감사 로그(5.11), Pareto 테이블(5.5), 장애 대응(4.5) |
| 🟡 v1.3 수정/개선 | 3 | 섹션 1 상태 업데이트(결정 완료), Phase 2~4 로드맵 추가, 통합 요약 갱신 |

최종 정리:
- 🔴 추가 필수(4): Worker 실행 순서, 감사 로그, Pareto 테이블, 장애 대응 정책
- 🟡 수정/보완(3): 섹션 1 상태 업데이트, Phase 2~4 로드맵, 통합 요약 갱신

