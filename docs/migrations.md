# Database Migrations

Supabase 데이터베이스 스키마를 설정하기 위한 마이그레이션 파일 실행 순서입니다.
`infra/supabase/migrations` 디렉토리에 있는 SQL 파일들을 순서대로 실행해야 합니다.

## Execution Order

| Order | File | Description | Required |
|-------|------|-------------|----------|
| 1 | `001_init.sql` | 초기 스키마 (User, Workspace 등 기본 테이블) | Yes |
| 2 | `002_domain_data_automation.sql` | 도메인 데이터 자동화 관련 테이블 | Yes |
| 3 | `003_fix_unique_constraints.sql` | 002번 테이블의 제약조건 수정 | Optional (Recommended) |
| 4 | `003_user_data_upload.sql` | 사용자 데이터 업로드 테이블 | Yes |
| 5 | `004_refine_catalog_schema.sql` | 컴포넌트 카탈로그 스키마 개선 | Yes |
| 6 | `005_enable_rls.sql` | **RLS (Row Level Security)** 보안 정책 적용 | **Critical** |
| 7 | `006_add_search_function.sql` | 벡터 검색용 RPC 함수 (`match_literature_chunks`) | **Critical** |

## How to Apply

### Option 1: Supabase Dashboard (SQL Editor)
1. Supabase 대시보드 접속 -> SQL Editor
2. 위 순서대로 파일 내용을 복사하여 붙여넣기 후 `Run` 클릭
3. 에러 발생 시 의존성 확인 후 재시도

### Option 2: Supabase CLI (Local Dev)
```bash
supabase db reset
# 마이그레이션 파일들이 supabase/migrations 폴더에 있다면 자동 적용됨
```
