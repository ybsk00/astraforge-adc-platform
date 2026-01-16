-- ================================================
-- Migration 041: Field Provenance Table
-- Description: 필드 ↔ 근거 연결 (추적성 핵심)
-- ================================================

CREATE TABLE IF NOT EXISTS public.field_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 연결된 Golden Seed Item
    golden_seed_item_id UUID REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
    
    -- 필드 정보
    field_name TEXT NOT NULL,
    -- Examples: target, payload_family, linker_type, dar_range
    
    field_value TEXT,
    -- 해당 필드의 값
    
    -- 근거 연결
    evidence_item_id UUID REFERENCES public.evidence_items(id) ON DELETE SET NULL,
    
    -- 신뢰도
    confidence FLOAT DEFAULT 0.7,
    -- 0.0 ~ 1.0
    
    -- 인용 정보 (하이라이트용)
    quote_span TEXT,
    -- 근거 문서에서 발췌한 정확한 문장
    
    -- Vector DB 연결 (One-Click Review용)
    source_chunk_id UUID,
    -- evidence_chunks.id 참조
    
    char_start INT,
    char_end INT,
    -- quote_span의 시작/끝 오프셋
    
    -- 메모
    note TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_field_provenance_seed 
    ON public.field_provenance(golden_seed_item_id);

CREATE INDEX IF NOT EXISTS idx_field_provenance_field 
    ON public.field_provenance(field_name);

CREATE INDEX IF NOT EXISTS idx_field_provenance_confidence 
    ON public.field_provenance(confidence);

-- RLS 설정
ALTER TABLE public.field_provenance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read field_provenance" 
    ON public.field_provenance 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can manage field_provenance" 
    ON public.field_provenance 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- 코멘트
COMMENT ON TABLE public.field_provenance IS '필드 추적성: 각 필드 값이 어느 근거에서 왔는지 연결';
COMMENT ON COLUMN public.field_provenance.field_name IS '필드 이름: target, payload_family, linker_type 등';
COMMENT ON COLUMN public.field_provenance.confidence IS '신뢰도 0.0~1.0 (Gate: >= 0.7 권장)';
COMMENT ON COLUMN public.field_provenance.quote_span IS '근거 문서 발췌 문장';
COMMENT ON COLUMN public.field_provenance.source_chunk_id IS 'Vector DB evidence_chunks.id 참조';
COMMENT ON COLUMN public.field_provenance.char_start IS 'quote_span 시작 오프셋 (하이라이트용)';
COMMENT ON COLUMN public.field_provenance.char_end IS 'quote_span 끝 오프셋 (하이라이트용)';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration 041 completed: Field Provenance table created';
END $$;

NOTIFY pgrst, 'reload config';
