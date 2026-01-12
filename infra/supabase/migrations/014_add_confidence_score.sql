-- Add confidence_score and other potentially missing columns to golden_candidates
ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS confidence_score integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS approval_status text,
ADD COLUMN IF NOT EXISTS source_ref text;

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
