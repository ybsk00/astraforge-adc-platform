 Phase 0 (1단계) 완료 현황 점검
체크리스트의 섹션 10) Phase 0 항목을 기준으로 확인한 결과입니다:

순서	항목	상태	설명
1	Supabase dev/prod + pgvector 활성화	✅	
infra/supabase/schema.sql
에 DDL 정의, vector 확장 활성화
2	Docker 기반 Engine/Worker 기본 이미지	✅	
docker-compose.yml
, 
services/engine/Dockerfile
, 
services/worker/Dockerfile
 구현 완료
3	API 키 세팅 + 
.env.example
✅	
.env.example
 작성 완료 (Supabase/Redis/Gemini/OpenAI/NCBI 등)
4	Seed Catalog 템플릿	❌	아직 Gold 데이터 입력 없음 (CSV/시드 데이터 없음)
5	ruleset_v0.1.yaml + scoring_params v0.2	❌	YAML 파일 및 버전 없음
6	Golden set 준비	❌	산식 검증용 테스트 데이터 없음
📋 추가 구현 현황 (Phase 1 일부 선작업)
항목	상태	설명
Catalog CRUD API	✅	
services/engine/app/api/catalog.py
 - 생성/조회/수정/삭제/재시도/통계 엔드포인트 완료
Arq Worker 기본 구조	✅	
services/worker/jobs/worker.py
 - 워커 설정 및 Job 정의
RDKit Descriptor 모듈	✅	
services/worker/chem/descriptors.py
 - 디스크립터 계산 + 시뮬레이션 폴백
DB Schema (DDL)	✅	
infra/supabase/schema.sql
 - 전체 테이블 415줄 (pgvector, RLS 포함)
환경 변수 문서	✅	
docs/env.md
 작성 완료
📌 결론
✅ Phase 0 기술 인프라: 완료
Docker 환경, DB 스키마, API 기본 구조, Worker 기본 구조가 모두 구현됨
❌ Phase 0 도메인 데이터: 미완료
다음 3가지 항목이 아직 준비되지 않았습니다:

Seed Catalog 데이터 (Gold Standard Target 리스트, CSV 등)
ruleset_v0.1.yaml (필터/페널티/알림 규칙)
scoring_params v0.2 (가중치/임계값 파라미터)
Golden Set (산식 회귀 검증용 케이스 20~50)
🔜 다음 단계 권장
옵션 A: 도메인 데이터 없이 Phase 1 개발 진행

RDKit Worker 테스트용 샘플 데이터 생성
개발하면서 도메인 전문가와 병렬로 데이터 준비
옵션 B: 도메인 데이터 먼저 준비

Seed Catalog CSV 템플릿 생성
ruleset YAML 초안 작성
scoring_params JSON 초안 작성