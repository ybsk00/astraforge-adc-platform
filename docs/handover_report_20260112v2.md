# 2026-01-12 작업 인수인계서

## 1. 작업 개요
오늘 작업은 **ADC 플랫폼의 데이터 파이프라인 안정화 및 초기 데이터 시딩(Seeding)**에 집중했습니다.
모든 커넥터(API, DB, System)가 정상적으로 작동하도록 코드를 수정하고, 데이터베이스 설정을 마이그레이션했습니다.

## 2. 주요 작업 내역

### A. 커넥터 및 워커 수정
1.  **Worker Import 에러 수정**: `services/worker/jobs/worker.py`에 `sys.path`를 추가하여 `No module named 'app'` 에러를 해결했습니다.
2.  **커넥터 실행 로직 수정 (`connector_executor.py`)**: API, DB, System 타입별로 올바른 Job을 호출하도록 분기 로직을 완성했습니다.
3.  **Batch Mode 지원 (`meta_sync_job.py`)**: `UniProt`, `HPA`, `OpenTargets`, `ChEMBL`, `PubChem` 커넥터가 `component_catalog`에 있는 타겟을 기준으로 데이터를 수집하도록 `batch_mode` 로직을 추가했습니다.
4.  **Seed Job Upsert 수정 (`seed_job.py`)**: `component_catalog`의 Partial Unique Index로 인한 `upsert` 에러를 해결하기 위해, 명시적인 `select` -> `insert/update` 로직으로 변경했습니다.

### B. 데이터베이스 마이그레이션
1.  **커넥터 타입 수정**:
    *   `ClinicalTrials.gov`, `openFDA` -> `api`
    *   `Seed Data`, `Resolve IDs` -> `system`
2.  **Batch Mode 설정**: 메타데이터 커넥터들의 `config`에 `{"batch_mode": true}`를 적용했습니다.

### C. 데이터 시딩 준비
1.  **200개 타겟 리스트 생성**: `services/worker/seeds/targets_seed_200.json` 파일을 생성했습니다. (Gold + Silver 타겟 포함)
2.  **Seed Job 연동**: `seed_job.py`가 위 JSON 파일을 로드하여 `component_catalog`에 적재하도록 수정했습니다.

## 3. 현재 상태
*   모든 코드 변경 사항은 `origin main`에 푸시되었습니다.
*   데이터베이스 마이그레이션은 완료되었습니다.
*   **Worker 프로세스는 재시작이 필요합니다.**

## 4. 내일(1/13) 작업 계획 (보강됨)

내일 작업은 **`골든셋강화_0113.md`**와 **`시드커넥트강화_0113.md`** 문서를 기반으로 진행합니다.

### A. Seed 커넥터 강화 (`시드커넥트강화_0113.md`)
**목표**: `component_catalog`를 Golden Seed 생성을 위한 "표준 사전"으로 격상
1.  **Merge 로직 개선**: `seed_job.py`에서 기존 데이터보다 **JSON 파일 데이터 우선**으로 병합하도록 수정 (필드별 Merge).
2.  **Unique Index 추가**: `component_catalog`에 `(type, gene_symbol)` 유니크 인덱스 추가 (중복 방지).
3.  **데이터 확장**: 항체/링커/페이로드를 최소 30~50개로 확장하고 `synonyms` 필드 추가.
4.  **검증**: HER2/HER3 등 핵심 타겟이 정상적으로 매핑되는지 확인.

### B. Golden Seed 강화 (`골든셋강화_0113.md`)
**목표**: ClinicalTrials 기반으로 **유의미한 Top 100 후보** 생성 (현재 <10개 수렴 문제 해결)
1.  **Mock 제거**: `golden_seed_job.py`에서 Mock 데이터 경로 완전 차단 (ClinicalTrials 강제).
2.  **추출 로직 강화**:
    *   **Intervention 추출**: `mab`, `conjugate` 외에 구체적인 약물명 패턴 추가.
    *   **Suffix 추론**: `vedotin`, `deruxtecan` 등 Suffix 기반으로 Payload/Linker 추론 로직 추가.
    *   **Catalog 연동**: 1차로 `component_catalog`와 매칭하고, 실패 시 휴리스틱 사용.
3.  **DB 구조 개선**: Raw(수집 전체)와 Final(Top 100) 구분 전략 적용 (`is_final` 플래그 등).

### C. 실행 순서 가이드
1.  **Worker 재시작**: `python -m services.worker.main`
2.  **Seed 커넥터 코드 수정 및 실행**: `시드커넥트강화_0113.md` 적용 -> 데이터 적재
3.  **Golden Seed 코드 수정 및 실행**: `골든셋강화_0113.md` 적용 -> 후보 생성
4.  **결과 검증**: Admin UI에서 Final 100개 후보 확인

## 5. 참고 파일
*   **`골든셋강화_0113.md`**: Golden Seed 로직 개선 상세 가이드
*   **`시드커넥트강화_0113.md`**: Seed 커넥터 및 Catalog 개선 상세 가이드
*   `services/worker/jobs/seed_job.py`: 시딩 로직
*   `services/worker/jobs/golden_seed_job.py`: 골든셋 생성 로직
*   `services/worker/jobs/worker.py`: 워커 설정
