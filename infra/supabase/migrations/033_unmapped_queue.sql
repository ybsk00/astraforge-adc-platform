-- ================================================
-- Migration 033: Unmapped Queue for Resolver Failures
-- Description: Resolver 실패 항목 Admin 처리 큐
-- ================================================

CREATE TABLE IF NOT EXISTS public.unmapped_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 엔티티 타입 (target/payload/linker/antibody)
    entity_type TEXT NOT NULL,
    
    -- 매핑 실패한 텍스트
    unmapped_text TEXT NOT NULL,
    
    -- 컨텍스트 (어떤 seed_item, 어떤 source에서 왔는지)
    context JSONB DEFAULT '{}'::jsonb,
    
    -- 상태
    status TEXT DEFAULT 'open', -- open | resolved | ignored
    
    -- 해결 정보
    resolved_canonical_key TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMPTZ,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint (동일 텍스트 중복 방지)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unmapped_unique 
    ON public.unmapped_queue(entity_type, LOWER(unmapped_text)) 
    WHERE status = 'open';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_unmapped_status ON public.unmapped_queue(status);
CREATE INDEX IF NOT EXISTS idx_unmapped_entity ON public.unmapped_queue(entity_type);

-- RLS 설정
ALTER TABLE public.unmapped_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read unmapped_queue" 
    ON public.unmapped_queue 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can modify unmapped_queue" 
    ON public.unmapped_queue 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_unmapped_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_unmapped_queue_updated_at
    BEFORE UPDATE ON public.unmapped_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.update_unmapped_queue_updated_at();

-- 코멘트
COMMENT ON TABLE public.unmapped_queue IS 'ID Resolver 실패 항목 - Admin이 수동 매핑 처리';
COMMENT ON COLUMN public.unmapped_queue.context IS '예: {"seed_item_id": "...", "source": "clinicaltrials", "field": "target"}';

NOTIFY pgrst, 'reload config';
