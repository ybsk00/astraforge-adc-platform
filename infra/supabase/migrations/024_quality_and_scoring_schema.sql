-- Migration 024: Quality Gate & Scoring Schema (Phase 2.5 & 4)
-- Description: Create quality_reports and scoring_policies tables

-- 1. Quality Reports (Phase 2.5)
CREATE TABLE IF NOT EXISTS public.quality_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id text,                      -- ID of the job run that generated this report
    check_type text NOT NULL,         -- 'catalog_completeness', 'golden_set_quality', etc.
    status text NOT NULL,             -- 'pass', 'fail', 'warning'
    results jsonb,                    -- Detailed results (e.g., missing_smiles_count: 5)
    fail_thresholds jsonb,            -- The thresholds used to determine failure
    created_at timestamptz DEFAULT now()
);

-- Index for querying reports
CREATE INDEX IF NOT EXISTS idx_quality_reports_status ON public.quality_reports(status);
CREATE INDEX IF NOT EXISTS idx_quality_reports_check_type ON public.quality_reports(check_type);

-- 2. Scoring Policies (Phase 4 Skeleton)
CREATE TABLE IF NOT EXISTS public.scoring_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_version text NOT NULL UNIQUE, -- e.g., 'v1.0.0'
    weights jsonb NOT NULL,              -- e.g., { "evidence": 0.4, "similarity": 0.3, "risk": 0.2, "fit": 0.1 }
    thresholds jsonb,                    -- e.g., { "min_confidence": 0.7 }
    compatibility_rules_version text,    -- Reference to the compatibility matrix version
    is_active boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);

-- Insert Default Policy (v1.0.0)
INSERT INTO public.scoring_policies (policy_version, weights, thresholds, compatibility_rules_version, is_active)
VALUES (
    'v1.0.0',
    '{ "evidence": 0.4, "similarity": 0.25, "risk": 0.25, "fit": 0.1 }'::jsonb,
    '{ "min_confidence": 0.6, "min_evidence_count": 1 }'::jsonb,
    'v1',
    true
)
ON CONFLICT (policy_version) DO NOTHING;

NOTIFY pgrst, 'reload config';
