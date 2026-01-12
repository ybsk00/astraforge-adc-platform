-- ================================================
-- Migration 022: Add Program Key for Grouping
-- Description: Add program_key column to group identical drug combinations across different trials
-- ================================================

ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS program_key text;

CREATE INDEX IF NOT EXISTS golden_candidates_program_key_idx
ON public.golden_candidates (program_key);
