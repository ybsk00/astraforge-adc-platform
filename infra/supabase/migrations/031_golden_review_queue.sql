-- ================================================
-- Migration 031: Golden Review Queue for Diff View
-- Description: Enrichment 제안 및 Admin 승인/반려 관리
-- ================================================

CREATE TABLE IF NOT EXISTS public.golden_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- FK to golden_seed_items
    seed_item_id UUID NOT NULL REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
    
    -- 큐 타입
    queue_type TEXT NOT NULL, -- enrichment_update | proxy_suggestion | resolver_suggestion | conflict_detected
    
    -- 엔티티 타입
    entity_type TEXT DEFAULT 'seed_item',
    
    -- 제안된 변경사항 (Diff-ready 구조)
    -- 예: {"payload_smiles_standardized": {"old": "", "new": "C1=CC...", "source": "pubchem", "evidence": [...]}}
    proposed_patch JSONB NOT NULL,
    
    -- 근거
    evidence_refs JSONB DEFAULT '[]'::jsonb,
    
    -- 신뢰도 (0~1)
    confidence FLOAT DEFAULT 0.5,
    
    -- 상태
    status TEXT DEFAULT 'pending', -- pending | approved | rejected | applied
    
    -- 처리 정보
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_review_queue_seed ON public.golden_review_queue(seed_item_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON public.golden_review_queue(status);
CREATE INDEX IF NOT EXISTS idx_review_queue_type ON public.golden_review_queue(queue_type);

-- RLS 설정
ALTER TABLE public.golden_review_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read golden_review_queue" 
    ON public.golden_review_queue 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can modify golden_review_queue" 
    ON public.golden_review_queue 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_golden_review_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_golden_review_queue_updated_at
    BEFORE UPDATE ON public.golden_review_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.update_golden_review_queue_updated_at();

-- 코멘트
COMMENT ON TABLE public.golden_review_queue IS 'Enrichment 제안 및 Admin 승인/반려 관리 (Diff View)';
COMMENT ON COLUMN public.golden_review_queue.proposed_patch IS 'Diff 구조: {field: {old, new, source, evidence}}';
COMMENT ON COLUMN public.golden_review_queue.queue_type IS 'enrichment_update: 자동 보강, proxy_suggestion: Proxy 제안, resolver_suggestion: ID 매핑 제안';

NOTIFY pgrst, 'reload config';
