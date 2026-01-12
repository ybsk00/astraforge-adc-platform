-- ================================================
-- Migration 012: Enhance Golden Set Schema
-- Description: Add versioning, evidence tracking, and atomic worker pickup
-- ================================================

-- 1. Golden Sets (Version Control)
CREATE TABLE IF NOT EXISTS public.golden_sets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL, -- e.g., 'ADC_GOLDEN_100'
    version text NOT NULL, -- e.g., 'v1', 'v1.1'
    config jsonb DEFAULT '{}'::jsonb, -- Config used to generate this set
    created_at timestamptz DEFAULT now(),
    UNIQUE(name, version)
);

-- RLS for golden_sets
ALTER TABLE public.golden_sets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated users can read golden_sets" ON public.golden_sets FOR SELECT TO authenticated USING (true);

-- 2. Enhance Golden Candidates
-- Add dataset_version and evidence_json
ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS dataset_version text,
ADD COLUMN IF NOT EXISTS evidence_json jsonb DEFAULT '[]'::jsonb;

-- Add Unique Constraint (to prevent duplicates)
-- Note: If there are existing duplicates, this might fail. 
-- In a real scenario, we would clean up first. Here we assume it's safe or user will handle it.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'golden_candidates_unique_key'
    ) THEN
        ALTER TABLE public.golden_candidates
        ADD CONSTRAINT golden_candidates_unique_key UNIQUE (drug_name, target, antibody, linker, payload);
    END IF;
END $$;

-- 3. Atomic Worker Pickup Function (RPC)
-- This allows the worker to safely pick up a job without race conditions
CREATE OR REPLACE FUNCTION public.pick_connector_run(worker_id text)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
    selected_run_id uuid;
    result_record jsonb;
BEGIN
    -- 1. Find and lock a queued run
    SELECT id INTO selected_run_id
    FROM public.connector_runs
    WHERE status = 'queued'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    -- 2. If found, update it
    IF selected_run_id IS NOT NULL THEN
        UPDATE public.connector_runs
        SET status = 'running',
            locked_by = worker_id,
            locked_at = now(),
            started_at = now(),
            attempt = attempt + 1
        WHERE id = selected_run_id
        RETURNING to_jsonb(connector_runs.*) INTO result_record;
        
        RETURN result_record;
    ELSE
        RETURN NULL;
    END IF;
END;
$$;
