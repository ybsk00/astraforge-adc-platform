-- Add result_summary and error_json columns to connector_runs table
ALTER TABLE public.connector_runs
ADD COLUMN IF NOT EXISTS result_summary jsonb DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS error_json jsonb DEFAULT '{}'::jsonb;

-- Notify PostgREST to reload schema cache (usually automatic, but good to know)
NOTIFY pgrst, 'reload config';
