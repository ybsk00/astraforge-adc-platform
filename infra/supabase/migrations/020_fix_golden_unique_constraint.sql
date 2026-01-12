-- ================================================
-- Migration 020: Fix Golden Candidate Unique Constraint
-- Description: Include golden_set_id in the unique constraint to allow same drug in different sets
-- ================================================

-- 1. Drop old constraint
ALTER TABLE public.golden_candidates
DROP CONSTRAINT IF EXISTS golden_candidates_unique_key;

-- 2. Add new constraint with golden_set_id
ALTER TABLE public.golden_candidates
ADD CONSTRAINT golden_candidates_unique_key UNIQUE (golden_set_id, drug_name, target, antibody, linker, payload);
