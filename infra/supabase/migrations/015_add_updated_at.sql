-- Add updated_at column to golden_candidates
ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
