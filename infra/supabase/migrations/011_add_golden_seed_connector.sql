-- ================================================
-- Migration 011: Add Golden Seed Connector
-- Description: Register the Golden Seed ADC 100 connector
-- ================================================

-- 1. Ensure is_active column exists (Safe migration)
ALTER TABLE public.connectors 
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;

-- 2. Ensure UNIQUE constraint on name exists (Required for ON CONFLICT)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'connectors_name_key'
    ) THEN
        ALTER TABLE public.connectors ADD CONSTRAINT connectors_name_key UNIQUE (name);
    END IF;
END $$;

-- 3. Register Connector
INSERT INTO public.connectors (name, type, config, is_active)
VALUES (
    'GOLDEN_SEED_ADC_100',
    'golden_seed',
    jsonb_build_object(
        'target_count', 100,
        'candidate_fetch_size', 500,
        'sources', jsonb_build_array('clinicaltrials', 'pubmed'),
        'min_evidence', 2,
        'search_terms', jsonb_build_array('antibody-drug conjugate', 'ADC', 'cancer therapy'),
        'selection_rule', 'score_desc_then_drug_name_asc',
        'seed_version', 'v1',
        'allow_sources', jsonb_build_array('clinicaltrials', 'pubmed')
    ),
    true
)
ON CONFLICT (name) DO UPDATE SET
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active;
