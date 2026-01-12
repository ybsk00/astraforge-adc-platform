-- 1. Enhance golden_candidates
ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS golden_set_id uuid REFERENCES public.golden_sets(id),
ADD COLUMN IF NOT EXISTS review_status text DEFAULT 'pending', -- pending, approved, rejected
ADD COLUMN IF NOT EXISTS review_notes text;

-- 2. Create golden_candidate_evidence table
CREATE TABLE IF NOT EXISTS public.golden_candidate_evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id uuid REFERENCES public.golden_candidates(id) ON DELETE CASCADE,
    source text NOT NULL, -- e.g., 'clinicaltrials', 'pubmed'
    url text,
    snippet text,
    ref_id text, -- e.g., NCT number or PMID
    created_at timestamptz DEFAULT now()
);

-- Index for faster lookup
CREATE INDEX IF NOT EXISTS idx_golden_candidate_evidence_candidate_id ON public.golden_candidate_evidence(candidate_id);

-- 3. Enhance seed_sets for lineage and idempotency
-- Ensure source_golden_set_id exists (in case 017 was skipped)
ALTER TABLE public.seed_sets
ADD COLUMN IF NOT EXISTS source_golden_set_id uuid REFERENCES public.golden_sets(id),
ADD COLUMN IF NOT EXISTS status text DEFAULT 'active'; -- 'active', 'archived', 'draft'

-- Add UNIQUE constraint to prevent promoting the same golden set multiple times
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'seed_sets_source_golden_set_id_key'
    ) THEN
        ALTER TABLE public.seed_sets
        ADD CONSTRAINT seed_sets_source_golden_set_id_key UNIQUE (source_golden_set_id);
    END IF;
END $$;

-- 4. Add status to golden_sets if not exists
ALTER TABLE public.golden_sets
ADD COLUMN IF NOT EXISTS status text DEFAULT 'draft'; -- draft, promoted, archived

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
