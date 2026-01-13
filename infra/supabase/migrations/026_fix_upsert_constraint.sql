-- Migration 026: Fix Golden Candidates Upsert Constraint
-- Description: Add unique index on (golden_set_id, program_key) to support upsert.

-- Drop old constraint/index if exists (likely on source_ref)
DROP INDEX IF EXISTS idx_golden_candidates_source_ref;
-- We might have a constraint name, usually table_column_key. 
-- Let's try to drop the constraint if it was created as a constraint.
ALTER TABLE public.golden_candidates DROP CONSTRAINT IF EXISTS golden_candidates_golden_set_id_source_ref_key;

-- Create the new unique index for program_key
CREATE UNIQUE INDEX IF NOT EXISTS idx_golden_candidates_program_key 
ON public.golden_candidates(golden_set_id, program_key);

-- Notify PostgREST
NOTIFY pgrst, 'reload config';
