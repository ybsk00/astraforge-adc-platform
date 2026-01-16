-- ================================================
-- Migration 043: LLM Jobs Table
-- Description: LLM 작업 큐 (Enrich/Discovery 등)
-- ================================================

CREATE TABLE IF NOT EXISTS public.llm_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 작업 타입
    job_type TEXT NOT NULL,
    -- Values: discovery / enrich / evidence_expand / failure_struct / synonym_resolve
    
    -- 연결된 Golden Seed Item (optional)
    golden_seed_item_id UUID REFERENCES public.golden_seed_items(id) ON DELETE SET NULL,
    
    -- 상태
    status TEXT DEFAULT 'queued',
    -- Values: queued / running / done / failed / cancelled
    
    -- 입력/출력
    input_payload JSONB,
    -- Examples: { "axis": "DXD", "query": "..." }
    
    output_payload JSONB,
    -- Examples: { "fields": { "target": "HER2", "confidence": 0.9 }, "evidence_refs": [...] }
    
    -- 에러
    error_message TEXT,
    
    -- 재시도 정보
    attempt INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_llm_jobs_status 
    ON public.llm_jobs(status);

CREATE INDEX IF NOT EXISTS idx_llm_jobs_type 
    ON public.llm_jobs(job_type);

CREATE INDEX IF NOT EXISTS idx_llm_jobs_seed 
    ON public.llm_jobs(golden_seed_item_id);

CREATE INDEX IF NOT EXISTS idx_llm_jobs_created 
    ON public.llm_jobs(created_at);

-- RLS 설정
ALTER TABLE public.llm_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read llm_jobs" 
    ON public.llm_jobs 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Service role can manage llm_jobs" 
    ON public.llm_jobs 
    FOR ALL 
    TO service_role 
    USING (true);

-- 코멘트
COMMENT ON TABLE public.llm_jobs IS 'LLM 작업 큐: discovery, enrich, evidence_expand, failure_struct';
COMMENT ON COLUMN public.llm_jobs.job_type IS 'discovery: 후보 생성, enrich: 필드 채움, evidence_expand: 근거 확장, failure_struct: 실패 구조화';
COMMENT ON COLUMN public.llm_jobs.input_payload IS '작업 입력 파라미터 (JSONB)';
COMMENT ON COLUMN public.llm_jobs.output_payload IS '작업 결과 (JSONB)';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration 043 completed: LLM Jobs table created';
END $$;

NOTIFY pgrst, 'reload config';
