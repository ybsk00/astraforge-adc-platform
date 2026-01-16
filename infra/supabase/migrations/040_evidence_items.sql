-- ================================================
-- Migration 040: Evidence Items Table
-- Description: 근거 다건 저장 테이블 (1:N)
-- NOTE: golden_seed_items 테이블이 먼저 존재해야 합니다.
-- ================================================

-- 테이블 생성 (FK 제약 조건 없이)
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    golden_seed_item_id UUID,
    type TEXT NOT NULL,
    id_or_url TEXT,
    title TEXT,
    published_date DATE,
    snippet TEXT,
    source_quality TEXT DEFAULT 'standard',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- FK 제약 조건 추가 (golden_seed_items 테이블이 있을 경우)
DO $$
BEGIN
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
            RAISE NOTICE 'Added FK constraint to evidence_items';
        END IF;
    ELSE
        RAISE NOTICE 'golden_seed_items table not found - FK constraint not added';
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
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'Read policy already exists';
END $$;

DO $$
BEGIN
    CREATE POLICY "Authenticated users can manage evidence_items" 
        ON public.evidence_items 
        FOR ALL 
        TO authenticated 
        USING (true)
        WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'Manage policy already exists';
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
COMMENT ON TABLE public.evidence_items IS '근거 다건 저장: 각 Golden Seed Item에 대해 여러 근거를 연결';
COMMENT ON COLUMN public.evidence_items.type IS 'clinicaltrials, paper, patent, label, press, other';
COMMENT ON COLUMN public.evidence_items.id_or_url IS 'NCT ID, PMID, Patent number, or URL';
COMMENT ON COLUMN public.evidence_items.snippet IS '관련 문단 발췌 (하이라이트용)';

NOTIFY pgrst, 'reload config';
