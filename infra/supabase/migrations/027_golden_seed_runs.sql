-- Golden Seed Runs table for job queue
-- This allows UI to submit jobs directly to Supabase, which the worker polls and executes

CREATE TABLE IF NOT EXISTS golden_seed_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL DEFAULT 'queued',  -- queued, running, completed, failed
    config JSONB NOT NULL DEFAULT '{}',  -- {targets: ["HER2"], per_target_limit: 30}
    result JSONB,  -- {total_fetched: 100, errors: []}
    error_message TEXT,
    locked_by VARCHAR(100),
    locked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Index for polling
CREATE INDEX IF NOT EXISTS idx_golden_seed_runs_status ON golden_seed_runs(status);
CREATE INDEX IF NOT EXISTS idx_golden_seed_runs_created_at ON golden_seed_runs(created_at DESC);

-- Comment
COMMENT ON TABLE golden_seed_runs IS 'Job queue for Golden Seed collection runs';
