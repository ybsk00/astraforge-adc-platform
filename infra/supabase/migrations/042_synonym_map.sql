-- ================================================
-- Migration 042: Synonym Map Table
-- Description: 약물명 동의어 매핑 (중복 생성 방지)
-- ================================================

CREATE TABLE IF NOT EXISTS public.synonym_map (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 표준(Canonical) 약물 연결
    canonical_drug_id UUID REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
    
    -- 동의어 원본 텍스트
    synonym_text TEXT NOT NULL,
    -- Examples: DS-8201, T-DXd, Enhertu
    
    -- 정규화된 동의어 (UNIQUE 제약용)
    synonym_text_normalized TEXT NOT NULL,
    -- lower() + 공백제거 + 하이픈 통일
    -- Examples: ds8201, tdxd, enhertu
    
    -- 출처 정보
    source_type TEXT,
    -- Values: clinicaltrials / paper / patent / fda_label / manual
    
    source_url TEXT,
    
    -- 신뢰도
    confidence FLOAT DEFAULT 0.8,
    -- 0.0 ~ 1.0
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint on normalized synonym
-- 정규화된 동의어로 중복 방지
CREATE UNIQUE INDEX IF NOT EXISTS idx_synonym_map_normalized_unique 
    ON public.synonym_map(synonym_text_normalized);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_synonym_map_canonical 
    ON public.synonym_map(canonical_drug_id);

CREATE INDEX IF NOT EXISTS idx_synonym_map_source 
    ON public.synonym_map(source_type);

-- RLS 설정
ALTER TABLE public.synonym_map ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read synonym_map" 
    ON public.synonym_map 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can manage synonym_map" 
    ON public.synonym_map 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_synonym_map_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_synonym_map_updated_at
    BEFORE UPDATE ON public.synonym_map
    FOR EACH ROW
    EXECUTE FUNCTION public.update_synonym_map_updated_at();

-- 정규화 함수 (사용 시)
CREATE OR REPLACE FUNCTION public.normalize_synonym(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    -- 소문자 변환, 공백/하이픈/언더스코어 제거
    RETURN LOWER(REGEXP_REPLACE(input_text, '[\s\-\_]+', '', 'g'));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 코멘트
COMMENT ON TABLE public.synonym_map IS '약물명 동의어 매핑: 중복 레코드 생성 방지';
COMMENT ON COLUMN public.synonym_map.canonical_drug_id IS '표준 약물 ID (golden_seed_items.id)';
COMMENT ON COLUMN public.synonym_map.synonym_text IS '동의어 원본 (표기 그대로)';
COMMENT ON COLUMN public.synonym_map.synonym_text_normalized IS '정규화된 동의어 (중복 체크용)';
COMMENT ON FUNCTION public.normalize_synonym IS '동의어 정규화 함수: 소문자 + 공백/하이픈 제거';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration 042 completed: Synonym Map table created with normalization';
END $$;

NOTIFY pgrst, 'reload config';
