# 보안 (Security)

> 본 문서는 ADC 플랫폼의 데이터 보안, 접근 제어, 감사 로그 정책을 정의합니다.

---

## 1. 개요

ADC 플랫폼은 멀티테넌시 환경에서 운영되며, 다음 보안 원칙을 따릅니다:

- **데이터 격리**: 워크스페이스 간 완전한 데이터 분리
- **최소 권한**: 필요한 최소한의 접근 권한만 부여
- **감사 추적**: 주요 활동에 대한 완전한 로그 기록
- **암호화**: 전송 및 저장 시 암호화

---

## 2. Row Level Security (RLS)

### 2.1 개요

Supabase의 RLS를 사용하여 `workspace_id` 기반으로 데이터를 격리합니다.

### 2.2 적용 대상 테이블

| 테이블 | RLS 적용 | 비고 |
|--------|----------|------|
| `design_runs` | ✅ | 워크스페이스별 런 격리 |
| `candidates` | ✅ | 런에 종속 |
| `candidate_scores` | ✅ | 후보에 종속 |
| `candidate_evidence` | ✅ | 후보에 종속 |
| `candidate_protocols` | ✅ | 후보에 종속 |
| `candidate_rule_hits` | ✅ | 후보에 종속 |
| `human_feedback` | ✅ | 워크스페이스별 피드백 |
| `assay_results` | ✅ | 워크스페이스별 실험 결과 |
| `component_catalog` | ⚠️ | 공용 + 워크스페이스 커스텀 |
| `literature_documents` | ⚠️ | 공용 + 프라이빗 문헌 |
| `literature_chunks` | ⚠️ | 문서에 종속 |

### 2.3 RLS 정책 예시

```sql
-- design_runs 테이블 RLS
ALTER TABLE design_runs ENABLE ROW LEVEL SECURITY;

-- SELECT 정책
CREATE POLICY "Users can view own workspace runs"
ON design_runs FOR SELECT
USING (
  workspace_id = (
    SELECT workspace_id FROM user_workspaces 
    WHERE user_id = auth.uid() 
    LIMIT 1
  )
);

-- INSERT 정책
CREATE POLICY "Users can create runs in own workspace"
ON design_runs FOR INSERT
WITH CHECK (
  workspace_id = (
    SELECT workspace_id FROM user_workspaces 
    WHERE user_id = auth.uid() 
    LIMIT 1
  )
);

-- component_catalog (공용 + 커스텀)
CREATE POLICY "Users can view public or own components"
ON component_catalog FOR SELECT
USING (
  workspace_id IS NULL  -- 공용 카탈로그
  OR workspace_id = (
    SELECT workspace_id FROM user_workspaces 
    WHERE user_id = auth.uid() 
    LIMIT 1
  )
);
```

### 2.4 Public 문헌 정책

```sql
-- 공용 문헌 (workspace_id IS NULL) 읽기 허용
CREATE POLICY "Users can view public literature"
ON literature_documents FOR SELECT
USING (
  workspace_id IS NULL
  OR workspace_id = (
    SELECT workspace_id FROM user_workspaces 
    WHERE user_id = auth.uid() 
    LIMIT 1
  )
);
```

---

## 3. 인증 및 식별

### 3.1 인증 방식

| 방식 | 설명 | 사용 환경 |
|------|------|----------|
| Supabase Auth | JWT 기반 인증 | 웹 프론트엔드 |
| API Key | 서비스 간 인증 | 백엔드/워커 |
| SSO (선택) | 엔터프라이즈 SSO | 대기업 고객 |

### 3.2 JWT 구조

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "researcher",
  "workspace_id": "workspace-uuid",
  "permissions": ["run:create", "run:read", "candidate:read"],
  "exp": 1704844800
}
```

### 3.3 사용자-워크스페이스 매핑

```sql
CREATE TABLE user_workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  workspace_id UUID REFERENCES workspaces(id) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, workspace_id)
);

-- 역할 정의
-- admin: 워크스페이스 관리, 멤버 초대
-- researcher: 런 생성/실행, 피드백 입력
-- viewer: 읽기 전용
```

---

## 4. 권한 관리 (RBAC)

### 4.1 역할 정의

| 역할 | 권한 |
|------|------|
| **admin** | 워크스페이스 설정, 멤버 관리, 전체 접근 |
| **researcher** | 런 생성/실행, 피드백, 리포트 |
| **viewer** | 읽기 전용 |

### 4.2 권한 매트릭스

| 리소스 | admin | researcher | viewer |
|--------|-------|------------|--------|
| 런 생성 | ✅ | ✅ | ❌ |
| 런 조회 | ✅ | ✅ | ✅ |
| 피드백 입력 | ✅ | ✅ | ❌ |
| 리포트 내보내기 | ✅ | ✅ | ✅ |
| 카탈로그 추가 | ✅ | ❌ | ❌ |
| 멤버 관리 | ✅ | ❌ | ❌ |

---

## 5. 감사 로그 (Audit Events)

### 5.1 audit_events 테이블

```sql
CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID REFERENCES workspaces(id),
  user_id UUID REFERENCES auth.users(id),
  event_type VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id UUID,
  action VARCHAR(50) NOT NULL,
  metadata JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_workspace ON audit_events(workspace_id, created_at);
CREATE INDEX idx_audit_user ON audit_events(user_id, created_at);
CREATE INDEX idx_audit_resource ON audit_events(resource_type, resource_id);
```

### 5.2 필수 기록 대상

| 이벤트 유형 | 리소스 | 액션 |
|-------------|--------|------|
| `run.created` | design_run | create |
| `run.executed` | design_run | execute |
| `run.completed` | design_run | complete |
| `run.failed` | design_run | fail |
| `ruleset.updated` | ruleset | update |
| `scoring_params.updated` | scoring_params | update |
| `literature.indexed` | literature | index |
| `report.exported` | report | export |
| `catalog.created` | component | create |
| `catalog.deprecated` | component | deprecate |
| `member.invited` | user | invite |
| `member.removed` | user | remove |

### 5.3 메타데이터 예시

```json
{
  "event_type": "run.completed",
  "resource_type": "design_run",
  "resource_id": "run-uuid",
  "action": "complete",
  "metadata": {
    "candidate_count": 1250,
    "pareto_count": 45,
    "scoring_version": "v0.2",
    "ruleset_version": "v0.1",
    "duration_seconds": 58
  }
}
```

### 5.4 보존 정책

| 환경 | 보존 기간 | 아카이브 |
|------|----------|---------|
| 개발 | 30일 | 없음 |
| 스테이징 | 90일 | 없음 |
| 프로덕션 | 1년 | S3 장기 보관 |

### 5.5 민감정보 마스킹

```python
MASKED_FIELDS = [
    "password",
    "api_key",
    "secret",
    "token",
    "email"  # 필요시
]

def mask_sensitive(data: dict) -> dict:
    for key in data:
        if any(field in key.lower() for field in MASKED_FIELDS):
            data[key] = "***MASKED***"
    return data
```

---

## 6. 보안 테스트

### 6.1 워크스페이스 격리 검증

```python
def test_workspace_isolation():
    """다른 워크스페이스 데이터 접근 불가 검증"""
    # 워크스페이스 A 사용자로 로그인
    user_a = login_as("user_a@workspace_a.com")
    
    # 워크스페이스 B의 런 ID로 조회 시도
    response = client.get(
        f"/api/runs/{workspace_b_run_id}",
        headers=user_a.headers
    )
    
    assert response.status_code == 404  # 또는 403
```

### 6.2 프라이빗 문헌 접근 검증

```python
def test_private_literature_access():
    """프라이빗 문헌 접근 제어 검증"""
    # 워크스페이스 A 사용자
    user_a = login_as("user_a@workspace_a.com")
    
    # 워크스페이스 B의 프라이빗 문헌 조회 시도
    response = client.get(
        f"/api/literature/{workspace_b_private_doc_id}",
        headers=user_a.headers
    )
    
    assert response.status_code == 404
    
    # 공용 문헌은 접근 가능
    response = client.get(
        f"/api/literature/{public_doc_id}",
        headers=user_a.headers
    )
    
    assert response.status_code == 200
```

---

## 7. 보안 체크리스트

### 7.1 배포 전 필수 확인

- [ ] 모든 RLS 정책 활성화 확인
- [ ] API 키 환경변수 설정 (하드코딩 금지)
- [ ] HTTPS 강제 적용
- [ ] CORS 설정 검토
- [ ] Rate limiting 설정

### 7.2 정기 점검

- [ ] 감사 로그 이상 징후 모니터링
- [ ] 미사용 사용자 계정 비활성화
- [ ] API 키 정기 교체 (90일)
- [ ] 의존성 보안 취약점 스캔

---

## 관련 문서

- [db.md](./db.md) - 데이터베이스 스키마
- [deploy.md](./deploy.md) - 배포 절차
- [env.md](./env.md) - 환경 변수 설정
