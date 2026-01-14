-- ================================================
-- Migration 030: Synonym Dictionary for ID Resolver
-- Description: 동의어 사전 (target/payload/linker 매핑)
-- ================================================

CREATE TABLE IF NOT EXISTS public.synonym_dictionary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 엔티티 타입 (target/payload/linker/antibody)
    entity_type TEXT NOT NULL,
    
    -- 별칭 (검색어)
    alias_text TEXT NOT NULL,
    
    -- 표준화된 키 (결과값)
    canonical_key TEXT NOT NULL,
    
    -- 출처 (신뢰도 순: admin > hgnc > import)
    source TEXT NOT NULL DEFAULT 'import',
    
    -- 신뢰도 (admin override = 1.0)
    confidence FLOAT DEFAULT 0.8,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint (엔티티 타입 + 별칭 조합)
CREATE UNIQUE INDEX IF NOT EXISTS idx_synonym_unique 
    ON public.synonym_dictionary(entity_type, LOWER(alias_text));

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_synonym_canonical 
    ON public.synonym_dictionary(entity_type, canonical_key);

-- RLS 설정
ALTER TABLE public.synonym_dictionary ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read synonym_dictionary" 
    ON public.synonym_dictionary 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can modify synonym_dictionary" 
    ON public.synonym_dictionary 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_synonym_dictionary_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_synonym_dictionary_updated_at
    BEFORE UPDATE ON public.synonym_dictionary
    FOR EACH ROW
    EXECUTE FUNCTION public.update_synonym_dictionary_updated_at();

-- ================================================
-- 초기 데이터: Target 동의어 (HGNC 기반)
-- ================================================
INSERT INTO public.synonym_dictionary (entity_type, alias_text, canonical_key, source, confidence) VALUES
-- HER2 Family
('target', 'HER2', 'ERBB2', 'hgnc', 0.95),
('target', 'Her2', 'ERBB2', 'hgnc', 0.95),
('target', 'neu', 'ERBB2', 'hgnc', 0.90),
('target', 'CD340', 'ERBB2', 'hgnc', 0.90),
('target', 'HER-2', 'ERBB2', 'hgnc', 0.95),
('target', 'HER3', 'ERBB3', 'hgnc', 0.95),
('target', 'Her3', 'ERBB3', 'hgnc', 0.95),
('target', 'EGFR', 'EGFR', 'hgnc', 1.0),

-- TROP2
('target', 'TROP2', 'TACSTD2', 'hgnc', 0.95),
('target', 'Trop-2', 'TACSTD2', 'hgnc', 0.95),
('target', 'TROP-2', 'TACSTD2', 'hgnc', 0.95),
('target', 'EGP-1', 'TACSTD2', 'hgnc', 0.85),

-- CD Family
('target', 'CD30', 'TNFRSF8', 'hgnc', 0.95),
('target', 'CD79b', 'CD79B', 'hgnc', 1.0),
('target', 'CD19', 'CD19', 'hgnc', 1.0),
('target', 'CD33', 'CD33', 'hgnc', 1.0),
('target', 'CD22', 'CD22', 'hgnc', 1.0),

-- Folate Receptor
('target', 'FR alpha', 'FOLR1', 'hgnc', 0.95),
('target', 'FRα', 'FOLR1', 'hgnc', 0.95),
('target', 'Folate receptor alpha', 'FOLR1', 'hgnc', 0.90),
('target', 'FOLR1', 'FOLR1', 'hgnc', 1.0),

-- Nectin-4
('target', 'Nectin-4', 'NECTIN4', 'hgnc', 0.95),
('target', 'Nectin4', 'NECTIN4', 'hgnc', 0.95),
('target', 'PVRL4', 'NECTIN4', 'hgnc', 0.90),

-- c-Met
('target', 'c-Met', 'MET', 'hgnc', 0.95),
('target', 'cMet', 'MET', 'hgnc', 0.95),
('target', 'c-MET', 'MET', 'hgnc', 0.95),
('target', 'HGFR', 'MET', 'hgnc', 0.90),
('target', 'MET', 'MET', 'hgnc', 1.0),

-- Tissue Factor
('target', 'Tissue Factor', 'F3', 'hgnc', 0.95),
('target', 'TF', 'F3', 'hgnc', 0.85),
('target', 'CD142', 'F3', 'hgnc', 0.90),

-- DLL3
('target', 'DLL3', 'DLL3', 'hgnc', 1.0),
('target', 'Delta-like 3', 'DLL3', 'hgnc', 0.90)

ON CONFLICT (entity_type, LOWER(alias_text)) DO NOTHING;

-- 코멘트
COMMENT ON TABLE public.synonym_dictionary IS 'ID Resolver 동의어 사전 - target/payload/linker 매핑';
COMMENT ON COLUMN public.synonym_dictionary.source IS 'admin: 수동 등록 (최우선), hgnc: HGNC 데이터, import: 자동 추출';

NOTIFY pgrst, 'reload config';
