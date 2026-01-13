-- Migration 025: Phase 1.5 & 2 Schema Updates (Unmapped Queue, Evidence, Deduplication)

-- 1. Unmapped Queue (Phase 1.5)
-- Tracks items that failed ID resolution for manual review
CREATE TABLE IF NOT EXISTS public.unmapped_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_text text NOT NULL,
    entity_type text NOT NULL, -- 'payload', 'linker', 'antibody', 'target'
    context_source_id text,    -- e.g. 'NCT01234567'
    status text DEFAULT 'pending', -- 'pending', 'resolved', 'ignored'
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_unmapped_queue_status ON public.unmapped_queue(status);
CREATE INDEX IF NOT EXISTS idx_unmapped_queue_type ON public.unmapped_queue(entity_type);

-- 2. Evidence Tables (Phase 2)
-- Centralized evidence storage for traceability
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type text NOT NULL, -- 'clinical_trial', 'publication', 'patent'
    external_id text NOT NULL, -- 'NCT...', 'PMID...', 'US...'
    url text,
    summary text,
    metadata jsonb,            -- Extra details (title, authors, date)
    created_at timestamptz DEFAULT now(),
    UNIQUE(source_type, external_id)
);

CREATE TABLE IF NOT EXISTS public.candidate_evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id uuid REFERENCES public.golden_candidates(id) ON DELETE CASCADE,
    evidence_id uuid REFERENCES public.evidence_items(id) ON DELETE CASCADE,
    relevance_score float DEFAULT 1.0,
    created_at timestamptz DEFAULT now(),
    UNIQUE(candidate_id, evidence_id)
);

-- 3. Golden Seed Raw Deduplication (Phase 2)
-- Ensure we don't store duplicate raw data for the same source hash
-- Note: We might need to handle existing duplicates if any, but for now we assume clean or acceptable to fail
-- If table already exists, we try to add the index.
CREATE UNIQUE INDEX IF NOT EXISTS idx_golden_seed_raw_dedup ON public.golden_seed_raw(source, source_hash);

-- 4. Report & Release Gate (Phase 4 - Pre-creating tables as requested)
CREATE TABLE IF NOT EXISTS public.report_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id uuid, -- User ID
    request_params jsonb,
    status text DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id uuid REFERENCES public.report_requests(id),
    title text,
    content jsonb, -- The report data
    status text DEFAULT 'draft', -- 'draft', 'released', 'archived'
    version text,
    run_inputs_hash text,
    policy_version text,
    dataset_version text,
    created_at timestamptz DEFAULT now(),
    released_at timestamptz
);

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
