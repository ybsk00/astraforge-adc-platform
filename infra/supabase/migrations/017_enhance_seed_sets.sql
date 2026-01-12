-- Enhance seed_sets table for promotion logic
ALTER TABLE public.seed_sets
ADD COLUMN IF NOT EXISTS source_golden_set_id uuid REFERENCES public.golden_sets(id),
ADD COLUMN IF NOT EXISTS status text DEFAULT 'active'; -- 'active', 'archived', 'draft'

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
