-- ================================================
-- Migration 033: Unmapped Queue for Resolver Failures
-- Description: Resolver 실패 항목 Admin 처리 큐
-- ================================================

-- 기존 테이블 삭제 (필요시)
DROP TABLE IF EXISTS public.unmapped_queue CASCADE;

-- 테이블 생성
CREATE TABLE public.unmapped_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 엔티티 타입 (target/payload/linker/antibody)
    entity_type TEXT NOT NULL,
    
    -- 매핑 실패한 텍스트
    unmapped_text TEXT NOT NULL,
    
    -- 컨텍스트 (어떤 seed_item, 어떤 source에서 왔는지)
    context JSONB DEFAULT '{}'::jsonb,
    
    -- 상태
    status TEXT DEFAULT 'open',
    
    -- 해결 정보
    resolved_canonical_key TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMPTZ,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_unmapped_status ON public.unmapped_queue(status);
CREATE INDEX idx_unmapped_entity ON public.unmapped_queue(entity_type);

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

DROP TRIGGER IF EXISTS trigger_update_unmapped_queue_updated_at ON public.unmapped_queue;
CREATE TRIGGER trigger_update_unmapped_queue_updated_at
    BEFORE UPDATE ON public.unmapped_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.update_unmapped_queue_updated_at();

-- 코멘트
COMMENT ON TABLE public.unmapped_queue IS 'ID Resolver 실패 항목 - Admin이 수동 매핑 처리';

NOTIFY pgrst, 'reload config';

