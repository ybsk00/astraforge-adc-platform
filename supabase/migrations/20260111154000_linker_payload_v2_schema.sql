-- 링커-페이로드 고도화 (v2) 스키마 확장 마이그레이션
-- 1. entity_linkers 테이블 확장
ALTER TABLE public.entity_linkers 
ADD COLUMN IF NOT EXISTS synonyms TEXT[],
ADD COLUMN IF NOT EXISTS cleavage_trigger TEXT,
ADD COLUMN IF NOT EXISTS chem_handle TEXT,
ADD COLUMN IF NOT EXISTS inchi_key TEXT,
ADD COLUMN IF NOT EXISTS external_id TEXT,
ADD COLUMN IF NOT EXISTS structure_source TEXT DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS structure_status TEXT DEFAULT 'confirmed',
ADD COLUMN IF NOT EXISTS structure_confidence INT DEFAULT 100;

-- 2. entity_drugs 테이블 확장 (페이로드 특화 필드)
ALTER TABLE public.entity_drugs
ADD COLUMN IF NOT EXISTS synonyms TEXT[],
ADD COLUMN IF NOT EXISTS payload_class TEXT,
ADD COLUMN IF NOT EXISTS mechanism TEXT,
ADD COLUMN IF NOT EXISTS membrane_permeability_note TEXT,
ADD COLUMN IF NOT EXISTS bystander_potential TEXT,
ADD COLUMN IF NOT EXISTS toxicity_flags JSONB,
ADD COLUMN IF NOT EXISTS inchi_key TEXT,
ADD COLUMN IF NOT EXISTS external_id TEXT,
ADD COLUMN IF NOT EXISTS structure_source TEXT DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS structure_status TEXT DEFAULT 'confirmed',
ADD COLUMN IF NOT EXISTS structure_confidence INT DEFAULT 100;

-- 3. 근거 수집 테이블 (evidence_snippets)
CREATE TABLE IF NOT EXISTS public.evidence_snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,         -- pubmed, pmc, patent, web
    source_id TEXT NOT NULL,           -- PMID, PMCID, Patent No 등
    title TEXT,
    year INT,
    chunk_id TEXT,
    quote TEXT,                        -- 근거 문장
    context TEXT,                      -- 주변 문맥
    extracted_entities JSONB,          -- 추출된 엔티티 정보
    quality_score INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 엔티티-근거 매핑 테이블 (entity_evidence_map)
CREATE TABLE IF NOT EXISTS public.entity_evidence_map (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,         -- linker, payload
    entity_id UUID NOT NULL,
    evidence_id UUID REFERENCES public.evidence_snippets(id) ON DELETE CASCADE,
    relation TEXT,                     -- supports, warns, mechanism, toxicity 등
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 설정
ALTER TABLE public.evidence_snippets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_evidence_map ENABLE ROW LEVEL SECURITY;

-- Admin 권한 부여
CREATE POLICY "Admins have full access to evidence_snippets" ON public.evidence_snippets FOR ALL USING (
  EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);
CREATE POLICY "Admins have full access to entity_evidence_map" ON public.entity_evidence_map FOR ALL USING (
  EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_evidence_snippets_source ON public.evidence_snippets(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_entity_evidence_map_entity ON public.entity_evidence_map(entity_type, entity_id);
