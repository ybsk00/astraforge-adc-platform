-- ================================================
-- Migration 010: Add Lock Columns to Design Runs
-- Description: Add locked_by and locked_at columns for worker polling
-- ================================================

-- 1. Add columns if not exist
ALTER TABLE public.design_runs 
ADD COLUMN IF NOT EXISTS attempt int DEFAULT 0,
ADD COLUMN IF NOT EXISTS next_retry_at timestamptz,
ADD COLUMN IF NOT EXISTS locked_by text,
ADD COLUMN IF NOT EXISTS locked_at timestamptz;

-- 2. Add index for performance
CREATE INDEX IF NOT EXISTS idx_design_runs_locked ON public.design_runs(locked_at);
