-- Migration 023: ID Resolver Schema (Phase 1.5)
-- Description: Create mapping_table for ID Resolver caching

CREATE TABLE IF NOT EXISTS public.mapping_table (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_text text NOT NULL,        -- The original text found in the source (e.g., "MMAE", "vedotin")
    normalized_key text NOT NULL,     -- Normalized version for lookup (e.g., "mmae", "vedotin")
    canonical_id uuid REFERENCES public.component_catalog(id), -- The resolved canonical entity
    entity_type text NOT NULL,        -- 'payload', 'linker', 'antibody', 'target'
    mapping_confidence float,         -- Confidence of this mapping (0.0 - 1.0)
    evidence_refs jsonb,              -- References supporting this mapping
    resolver_version text,            -- Version of the resolver logic used
    updated_at timestamptz DEFAULT now()
);

-- Unique index for fast lookup and upsert
CREATE UNIQUE INDEX IF NOT EXISTS idx_mapping_table_key_type ON public.mapping_table(normalized_key, entity_type);

-- Index on canonical_id for reverse lookup
CREATE INDEX IF NOT EXISTS idx_mapping_table_canonical_id ON public.mapping_table(canonical_id);

NOTIFY pgrst, 'reload config';
