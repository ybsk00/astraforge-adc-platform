-- ================================================
-- Migration 040: Evidence Items Table
-- Description: 근거 다건 저장 테이블 (1:N)
-- NOTE: golden_seed_items 테이블이 먼저 존재해야 합니다.
-- ================================================

DO $$
BEGIN
    -- Check if golden_seed_items table exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'golden_seed_items'
    ) THEN
        RAISE NOTICE 'golden_seed_items table does not exist. Please run 028_golden_seed_items.sql first.';
        RETURN;
    END IF;
    
    -- Check if evidence_items table already exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        RAISE NOTICE 'evidence_items table already exists. Skipping creation.';
        RETURN;
    END IF;
    
    -- Create table
    CREATE TABLE public.evidence_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        golden_seed_item_id UUID REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
        type TEXT NOT NULL,
        id_or_url TEXT,
        title TEXT,
        published_date DATE,
        snippet TEXT,
        source_quality TEXT DEFAULT 'standard',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    RAISE NOTICE 'Created evidence_items table';
END $$;

-- 인덱스 (테이블 존재 시에만)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_evidence_items_seed 
            ON public.evidence_items(golden_seed_item_id);
        CREATE INDEX IF NOT EXISTS idx_evidence_items_type 
            ON public.evidence_items(type);
        RAISE NOTICE 'Created indexes on evidence_items';
    END IF;
END $$;

-- RLS 설정 (테이블 존재 시에만)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
        
        -- 정책 생성 (이미 존재하면 무시)
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'evidence_items' 
            AND policyname = 'Authenticated users can read evidence_items'
        ) THEN
            CREATE POLICY "Authenticated users can read evidence_items" 
                ON public.evidence_items 
                FOR SELECT 
                TO authenticated 
                USING (true);
        END IF;
        
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'evidence_items' 
            AND policyname = 'Authenticated users can manage evidence_items'
        ) THEN
            CREATE POLICY "Authenticated users can manage evidence_items" 
                ON public.evidence_items 
                FOR ALL 
                TO authenticated 
                USING (true)
                WITH CHECK (true);
        END IF;
        
        RAISE NOTICE 'Configured RLS on evidence_items';
    END IF;
END $$;

-- 트리거 (테이블 존재 시에만)
CREATE OR REPLACE FUNCTION public.update_evidence_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        DROP TRIGGER IF EXISTS trigger_update_evidence_items_updated_at ON public.evidence_items;
        CREATE TRIGGER trigger_update_evidence_items_updated_at
            BEFORE UPDATE ON public.evidence_items
            FOR EACH ROW
            EXECUTE FUNCTION public.update_evidence_items_updated_at();
        RAISE NOTICE 'Created trigger on evidence_items';
    END IF;
END $$;

-- 코멘트 (테이블 존재 시에만)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        COMMENT ON TABLE public.evidence_items IS '근거 다건 저장: 각 Golden Seed Item에 대해 여러 근거를 연결';
        COMMENT ON COLUMN public.evidence_items.type IS 'clinicaltrials, paper, patent, label, press, other';
        COMMENT ON COLUMN public.evidence_items.id_or_url IS 'NCT ID, PMID, Patent number, or URL';
        COMMENT ON COLUMN public.evidence_items.snippet IS '관련 문단 발췌 (하이라이트용)';
        RAISE NOTICE 'Added comments to evidence_items';
    END IF;
END $$;

-- 완료 메시지
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        RAISE NOTICE 'Migration 040 completed: Evidence Items table ready';
    ELSE
        RAISE NOTICE 'Migration 040: evidence_items table was not created. Check prerequisites.';
    END IF;
END $$;

NOTIFY pgrst, 'reload config';
