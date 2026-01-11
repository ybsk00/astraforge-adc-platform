import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    exit(1)

supabase: Client = create_client(url, key)

sql = """
-- 링커 엔티티 추가
CREATE TABLE IF NOT EXISTS public.entity_linkers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  smiles TEXT,                       -- 화학 구조 (SMILES)
  linker_type TEXT,                  -- ex) 'cleavable', 'non-cleavable'
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (name)
);

-- Seed Set - Linker 관계 테이블
CREATE TABLE IF NOT EXISTS public.seed_set_linkers (
  seed_set_id UUID REFERENCES public.seed_sets(id) ON DELETE CASCADE,
  linker_id   UUID REFERENCES public.entity_linkers(id) ON DELETE CASCADE,
  PRIMARY KEY (seed_set_id, linker_id)
);

-- 페이로드 연동을 위한 entity_drugs 확장
ALTER TABLE public.entity_drugs ADD COLUMN IF NOT EXISTS drug_role TEXT;
CREATE INDEX IF NOT EXISTS idx_entity_drugs_role ON public.entity_drugs (drug_role);

-- Seed Set - Payload 관계 테이블
CREATE TABLE IF NOT EXISTS public.seed_set_payloads (
  seed_set_id UUID REFERENCES public.seed_sets(id) ON DELETE CASCADE,
  drug_id     UUID REFERENCES public.entity_drugs(id) ON DELETE CASCADE,
  PRIMARY KEY (seed_set_id, drug_id)
);

-- RLS 설정
ALTER TABLE public.entity_linkers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.seed_set_linkers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.seed_set_payloads ENABLE ROW LEVEL SECURITY;

-- Admin 권한 부여
DO $$ 
BEGIN
    DROP POLICY IF EXISTS "Admins have full access to entity_linkers" ON public.entity_linkers;
    DROP POLICY IF EXISTS "Admins have full access to seed_set_linkers" ON public.seed_set_linkers;
    DROP POLICY IF EXISTS "Admins have full access to seed_set_payloads" ON public.seed_set_payloads;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

CREATE POLICY "Admins have full access to entity_linkers" ON public.entity_linkers FOR ALL USING (
  EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);
CREATE POLICY "Admins have full access to seed_set_linkers" ON public.seed_set_linkers FOR ALL USING (
  EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);
CREATE POLICY "Admins have full access to seed_set_payloads" ON public.seed_set_payloads FOR ALL USING (
  EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);
"""

try:
    # rpc를 사용하여 SQL 실행 (Supabase SQL Editor와 유사한 기능이 필요함)
    # 하지만 일반적인 supabase-py 클라이언트는 직접적인 SQL 실행을 지원하지 않음.
    # 대신 postgresql 직접 연결이 필요할 수 있으나, 여기서는 rpc가 정의되어 있지 않다면 실행 불가.
    # 프로젝트에 'exec_sql' 같은 rpc가 있는지 확인하거나 다른 방법을 찾아야 함.
    
    # 대안: npx supabase db query를 다시 시도하되, 패키지 설치 문제를 피하기 위해 
    # 이미 설치된 환경인지 확인하거나, 직접 psql 등을 사용.
    
    print("Executing SQL via Supabase RPC if available...")
    # 실제로는 supabase-py로 직접 SQL을 실행하는 것은 보안상 막혀있는 경우가 많음.
    # 따라서 CLI를 사용하는 것이 정석임.
    
    pass
except Exception as e:
    print(f"Error: {e}")
