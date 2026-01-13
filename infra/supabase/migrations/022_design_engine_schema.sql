-- Migration 022: Design Engine Schema (Phase 1)
-- Description: Add columns for Design Engine (SMILES, Synonyms, RAW/FINAL separation)

-- 1. Enhance component_catalog
ALTER TABLE public.component_catalog
ADD COLUMN IF NOT EXISTS smiles text,
ADD COLUMN IF NOT EXISTS synonyms text[],
ADD COLUMN IF NOT EXISTS canonical_name text,
ADD COLUMN IF NOT EXISTS linker_type text, -- e.g., 'cleavable', 'non-cleavable'
ADD COLUMN IF NOT EXISTS trigger text;    -- e.g., 'cathepsin-b', 'acid'

-- 2. Create golden_seed_raw table (for Lineage & Reproducibility)
CREATE TABLE IF NOT EXISTS public.golden_seed_raw (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source text NOT NULL, -- e.g., 'clinicaltrials', 'pubmed'
    source_id text,       -- e.g., 'NCT01234567'
    source_hash text,     -- Hash of the raw content or query parameters for deduplication
    raw_payload jsonb,    -- The full raw JSON response
    fetched_at timestamptz DEFAULT now(),
    parser_version text,  -- Version of the parser used
    query_profile text,   -- e.g., 'payload_discovery', 'adc_validation'
    dataset_version text  -- Version of the dataset this belongs to
);

-- Index for deduplication check
CREATE INDEX IF NOT EXISTS idx_golden_seed_raw_source_hash ON public.golden_seed_raw(source_hash);
CREATE INDEX IF NOT EXISTS idx_golden_seed_raw_source_id ON public.golden_seed_raw(source_id);

-- 3. Enhance golden_candidates (for Quality Gate & Ranking)
ALTER TABLE public.golden_candidates
ADD COLUMN IF NOT EXISTS is_final boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS confidence_score float,       -- Ranking score (Evidence + Similarity + Rules)
ADD COLUMN IF NOT EXISTS mapping_confidence float,     -- Resolver confidence (0.0 - 1.0)
ADD COLUMN IF NOT EXISTS evidence_refs jsonb,          -- References (e.g., [{"type": "clinical", "id": "NCT..."}])
ADD COLUMN IF NOT EXISTS raw_data_id uuid REFERENCES public.golden_seed_raw(id),
ADD COLUMN IF NOT EXISTS dataset_version text,
ADD COLUMN IF NOT EXISTS run_inputs_hash text;         -- Hash of the inputs used to generate this candidate

-- Index for filtering final candidates
CREATE INDEX IF NOT EXISTS idx_golden_candidates_is_final ON public.golden_candidates(is_final);

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
