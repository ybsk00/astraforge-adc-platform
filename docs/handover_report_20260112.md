# 📋 개발 인수인계 보고서 (2026-01-12)

## 1. 개요
본 문서는 2026년 1월 12일 진행된 **Admin UI 개선 및 Golden Set 데이터 정합성 확보** 작업에 대한 상세 내역과, 후속 작업을 위한 가이드를 포함합니다.

---

## 2. 주요 작업 내역

### 2.1. Admin UI 및 번역 수정
*   **레이아웃 버그 수정**:
    *   `AdminSidebar.tsx`: `z-index`를 50으로 상향하여 헤더 위로 올라오지 않도록 수정.
    *   `DashboardHeader.tsx`: `position: fixed` 및 `left-64` 적용으로 사이드바와 겹치지 않게 고정.
    *   `AdminLayout.tsx`: `pt-20` 추가로 헤더 높이만큼 콘텐츠 여백 확보.
*   **번역 파일 복구**:
    *   `ko.json`: 손상된 파일 복구 및 누락된 키(`seeds`, `observability` 등) 추가.

### 2.2. Golden Set 기능 고도화
*   **페이지네이션 구현**:
    *   `/admin/golden-sets`: 한 페이지당 20개씩 표시되도록 서버 사이드 페이지네이션 적용.
*   **데이터 정합성 버그 수정 (Critical)**:
    1.  **데이터 누락 (Orphaned Data)**:
        *   **증상**: 커넥터 실행 성공 메시지는 뜨지만 리스트에 아무것도 안 나옴.
        *   **원인**: `golden_candidates` 저장 시 `golden_set_id`를 누락하여 연결 고리 끊김.
        *   **해결**: `golden_seed_job.py`에서 Set ID를 받아와 FK로 저장하도록 수정.
    2.  **데이터 중복/소실 (Truncated Names)**:
        *   **증상**: 100개를 생성해도 7~8개만 남음. 약물 이름이 "vedotin" 등으로 잘림.
        *   **원인**: Worker의 구버전 로직(이름 파싱 오류)이 메모리에 상주 & DB의 엄격한 Unique Key.
        *   **해결**:
            *   DB Unique Key 변경: `(drug_name, ...)` → `(golden_set_id, source_ref)`
            *   Worker 로직 수정: 동적 버전(`v1-{timestamp}`) 생성 및 올바른 이름 파싱 적용.

---

## 3. 데이터베이스 변경 사항 (Migrations)

최근 적용된 마이그레이션 파일들은 `infra/supabase/migrations/` 경로에 있습니다.

| 파일명 | 설명 | 비고 |
| :--- | :--- | :--- |
| `018_operational_golden_schema.sql` | Evidence 테이블, Review 상태 컬럼 추가 | 초기 스키마 |
| `019_promote_rpc.sql` | `promote_golden_set` RPC 함수 추가 | 원자적 승격 처리 |
| `020_fix_golden_unique_constraint.sql` | Unique Key에 `golden_set_id` 포함 | **적용됨** |
| `021_change_golden_unique_key.sql` | Unique Key를 `(golden_set_id, source_ref)`로 변경 | **최종 적용됨** |

> **Note**: `021`번 마이그레이션이 최종적으로 적용되어야 100개의 데이터가 정상적으로 생성됩니다.

---

## 4. 백엔드 Worker 로직 (`golden_seed_job.py`)

*   **위치**: `services/worker/jobs/golden_seed_job.py`
*   **주요 로직**:
    1.  **Dynamic Versioning**: 실행 시마다 `v1-{YYYYMMDD-HHMMSS}` 형식으로 버전을 생성하여, 매번 새로운 Golden Set을 만듭니다.
    2.  **Unique Key Handling**: `upsert` 시 `(golden_set_id, source_ref)`를 기준으로 충돌을 감지합니다.
    3.  **Evidence Linking**: Candidate 생성 후 반환된 ID를 이용해 `golden_candidate_evidence` 테이블에 근거 자료를 저장합니다.

---

## 5. 실행 및 테스트 가이드

### 5.1. Worker 재시작 (필수)
코드가 수정되었으므로, 반드시 Worker 프로세스(또는 Docker 컨테이너)를 재시작해야 변경된 로직이 반영됩니다.

```bash
# Docker 사용 시
docker-compose restart worker

# 로컬 실행 시
# 실행 중인 터미널에서 Ctrl+C 후 다시 실행
python -m services.worker.main
```

### 5.2. 커넥터 실행
1.  Admin 페이지 > **커넥터 관리** (`/admin/connectors`) 접속.
2.  **Golden Seed Connector** 실행 버튼 클릭.
3.  약 10~20초 후 완료 메시지 확인.

### 5.3. 결과 확인
1.  **Golden Set 목록** (`/admin/golden-sets`) 접속.
2.  방금 생성된 세트(예: `ADC_GOLDEN_100 (v1-20260112-...)`) 확인.
3.  **상세 보기** 클릭 시 100개의 후보 물질이 정상적으로 보이는지 확인.

---

## 6. 향후 계획 (Next Steps)

*   [ ] **시드 관리 페이지 고도화**: `/admin/seeds` 페이지에서 Source 배지 표시 및 상태 필터링 기능 추가 필요.
*   [ ] **실제 데이터 연동**: 현재 Mock 데이터를 사용 중이므로, 추후 ClinicalTrials.gov API 연동 로직(`_fetch_real_candidates`) 구현 필요.
