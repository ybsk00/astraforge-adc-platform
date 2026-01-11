-- 링커 엔티티 추가
CREATE TABLE IF NOT EXISTS public.entity_linkers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  smiles TEXT,                       -- 화학 구조 (SMILES)
  linker_type TEXT,                  -- ex) "cleavable", "non-cleavable"
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
CREATE POLICY "Admins have full access to entity_linkers" ON public.entity_linkers FOR ALL USING (is_admin());
CREATE POLICY "Admins have full access to seed_set_linkers" ON public.seed_set_linkers FOR ALL USING (is_admin());
CREATE POLICY "Admins have full access to seed_set_payloads" ON public.seed_set_payloads FOR ALL USING (is_admin());
