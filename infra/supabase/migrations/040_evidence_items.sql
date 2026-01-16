-- ================================================
-- Migration 040: Evidence Items Table
-- Description: 근거 다건 저장 테이블 (1:N)
-- ================================================

CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 연결된 Golden Seed Item
    golden_seed_item_id UUID REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
    
    -- 근거 타입
    type TEXT NOT NULL,
    -- Values: clinicaltrials / paper / patent / label / press / other
    
    -- 식별자
    id_or_url TEXT,
    -- Examples: NCT12345678, PMID:12345678, US10123456, URL
    
    -- 메타데이터
    title TEXT,
    published_date DATE,
    snippet TEXT,  -- 관련 문단 발췌
    
    -- 출처 신뢰도
    source_quality TEXT DEFAULT 'standard',
    -- Values: high (label, primary trial) / standard (paper, patent) / low (press, other)
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_evidence_items_seed 
    ON public.evidence_items(golden_seed_item_id);

CREATE INDEX IF NOT EXISTS idx_evidence_items_type 
    ON public.evidence_items(type);

-- RLS 설정
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read evidence_items" 
    ON public.evidence_items 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can manage evidence_items" 
    ON public.evidence_items 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_evidence_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_evidence_items_updated_at
    BEFORE UPDATE ON public.evidence_items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_evidence_items_updated_at();

-- 코멘트
COMMENT ON TABLE public.evidence_items IS '근거 다건 저장: 각 Golden Seed Item에 대해 여러 근거를 연결';
COMMENT ON COLUMN public.evidence_items.type IS 'clinicaltrials, paper, patent, label, press, other';
COMMENT ON COLUMN public.evidence_items.id_or_url IS 'NCT ID, PMID, Patent number, or URL';
COMMENT ON COLUMN public.evidence_items.snippet IS '관련 문단 발췌 (하이라이트용)';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration 040 completed: Evidence Items table created';
END $$;

NOTIFY pgrst, 'reload config';
