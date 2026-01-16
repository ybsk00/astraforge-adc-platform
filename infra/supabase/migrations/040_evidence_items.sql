-- ================================================
-- Migration 040: Evidence Items Table
-- Description: 근거 다건 저장 테이블 (1:N)
-- ================================================

-- 테이블 생성 (기본)
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    id_or_url TEXT,
    title TEXT,
    published_date DATE,
    snippet TEXT,
    source_quality TEXT DEFAULT 'standard',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- golden_seed_item_id 컬럼 추가 (없으면)
ALTER TABLE public.evidence_items 
ADD COLUMN IF NOT EXISTS golden_seed_item_id UUID;

-- FK 제약 조건 추가 (golden_seed_items 테이블이 있고, FK가 없을 경우)
DO $$
BEGIN
    -- golden_seed_items 테이블이 있는지 확인
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'golden_seed_items'
    ) THEN
        -- FK 제약 조건이 없으면 추가
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'evidence_items_golden_seed_item_id_fkey'
            AND table_name = 'evidence_items'
        ) THEN
            ALTER TABLE public.evidence_items 
            ADD CONSTRAINT evidence_items_golden_seed_item_id_fkey 
            FOREIGN KEY (golden_seed_item_id) 
            REFERENCES public.golden_seed_items(id) 
            ON DELETE CASCADE;
            RAISE NOTICE 'Added FK constraint';
        END IF;
    END IF;
END $$;

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_evidence_items_seed 
    ON public.evidence_items(golden_seed_item_id);

CREATE INDEX IF NOT EXISTS idx_evidence_items_type 
    ON public.evidence_items(type);

-- RLS 설정
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;

-- 정책
DO $$
BEGIN
    CREATE POLICY "Authenticated users can read evidence_items" 
        ON public.evidence_items 
        FOR SELECT 
        TO authenticated 
        USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Authenticated users can manage evidence_items" 
        ON public.evidence_items 
        FOR ALL 
        TO authenticated 
        USING (true)
        WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 트리거 함수
CREATE OR REPLACE FUNCTION public.update_evidence_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거
DROP TRIGGER IF EXISTS trigger_update_evidence_items_updated_at ON public.evidence_items;
CREATE TRIGGER trigger_update_evidence_items_updated_at
    BEFORE UPDATE ON public.evidence_items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_evidence_items_updated_at();

-- 코멘트
COMMENT ON TABLE public.evidence_items IS '근거 다건 저장';
COMMENT ON COLUMN public.evidence_items.type IS 'clinicaltrials, paper, patent, label, press, other';

NOTIFY pgrst, 'reload config';
