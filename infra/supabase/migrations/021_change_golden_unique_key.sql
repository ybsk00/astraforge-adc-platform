-- ================================================
-- Migration 021: Change Golden Candidate Unique Key
-- Description: Change unique constraint to (golden_set_id, source_ref) to allow multiple trials/entries per drug
-- ================================================

-- 1. Drop previous constraint (from Migration 020)
ALTER TABLE public.golden_candidates
DROP CONSTRAINT IF EXISTS golden_candidates_unique_key;

-- 2. Add new constraint based on Set ID and Source Reference (e.g. NCT ID)
-- This allows the same drug to appear multiple times if it comes from different sources (trials)
ALTER TABLE public.golden_candidates
ADD CONSTRAINT golden_candidates_unique_key UNIQUE (golden_set_id, source_ref);
