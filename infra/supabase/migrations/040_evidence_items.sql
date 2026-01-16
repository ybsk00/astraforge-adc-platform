-- ================================================
-- Migration 040: Evidence Items Table
-- Description: 근거 다건 저장 테이블 (1:N)
-- ================================================

-- 테이블 생성 (id만)
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

-- 모든 컬럼 추가 (없으면)
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS golden_seed_item_id UUID;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS type TEXT;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS id_or_url TEXT;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS published_date DATE;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS snippet TEXT;
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS source_quality TEXT DEFAULT 'standard';
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.evidence_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- type 컬럼에 NOT NULL 제약은 나중에 데이터 입력 후 추가 권장

-- FK 제약 조건 추가 (golden_seed_items 테이블이 있고, FK가 없을 경우)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'golden_seed_items'
    ) THEN
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
        END IF;
    END IF;
END $$;

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_evidence_items_seed ON public.evidence_items(golden_seed_item_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_type ON public.evidence_items(type);

-- RLS 설정
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;

-- 정책
DO $$ BEGIN
    CREATE POLICY "evidence_items_read" ON public.evidence_items FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "evidence_items_manage" ON public.evidence_items FOR ALL TO authenticated USING (true) WITH CHECK (true);
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

NOTIFY pgrst, 'reload config';
