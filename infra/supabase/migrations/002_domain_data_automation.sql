-- ================================================
-- Migration: Add Domain Data Automation Tables
-- Run this if you already have the base schema
-- ================================================

-- 1. Add missing columns to staging_components (if needed)
ALTER TABLE staging_components 
ADD COLUMN IF NOT EXISTS canonical_smiles TEXT;

ALTER TABLE staging_components 
ADD COLUMN IF NOT EXISTS normalized JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE staging_components 
ADD COLUMN IF NOT EXISTS source JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE staging_components 
ADD COLUMN IF NOT EXISTS review_note TEXT;

-- Update status check constraint if needed
ALTER TABLE staging_components 
DROP CONSTRAINT IF EXISTS staging_components_status_check;

ALTER TABLE staging_components 
ADD CONSTRAINT staging_components_status_check 
CHECK (status IN ('pending_review', 'approved', 'rejected', 'pending'));

-- 2. Add smiles column to component_catalog if needed
ALTER TABLE component_catalog 
ADD COLUMN IF NOT EXISTS smiles TEXT;

-- ================================================
-- 3. Create Domain Data Automation Tables
-- ================================================

-- Raw Source Records (원본 보존)
CREATE TABLE IF NOT EXISTS raw_source_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum TEXT NOT NULL,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_source_source 
ON raw_source_records(source, fetched_at DESC);

-- Ingestion Cursors (증분 수집 상태 관리)
CREATE TABLE IF NOT EXISTS ingestion_cursors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    cursor JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_success_at TIMESTAMPTZ,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'running', 'failed')),
    error_message TEXT,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source, query_hash)
);

CREATE INDEX IF NOT EXISTS idx_ingestion_cursors_source 
ON ingestion_cursors(source, status);

-- Target Profiles (표적 메타 정규화)
CREATE TABLE IF NOT EXISTS target_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES component_catalog(id) ON DELETE CASCADE,
    uniprot_id TEXT,
    gene_symbol TEXT,
    ensembl_id TEXT,
    protein_name TEXT,
    organism TEXT DEFAULT 'Homo sapiens',
    function_summary TEXT,
    expression JSONB DEFAULT '{}'::jsonb,
    associations JSONB DEFAULT '{}'::jsonb,
    clinical JSONB DEFAULT '{}'::jsonb,
    safety_signals JSONB DEFAULT '{}'::jsonb,
    external_refs JSONB DEFAULT '{}'::jsonb,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_target_profiles_uniprot 
ON target_profiles(uniprot_id) WHERE uniprot_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_target_profiles_gene 
ON target_profiles(gene_symbol);

-- Compound Registry (화합물 ID 통합 매핑)
CREATE TABLE IF NOT EXISTS compound_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES component_catalog(id) ON DELETE CASCADE,
    canonical_smiles TEXT,
    inchi_key TEXT,
    chembl_id TEXT,
    pubchem_cid TEXT,
    synonyms JSONB DEFAULT '[]'::jsonb,
    activities JSONB DEFAULT '{}'::jsonb,
    properties JSONB DEFAULT '{}'::jsonb,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_compound_registry_inchikey 
ON compound_registry(inchi_key) WHERE inchi_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_compound_registry_chembl 
ON compound_registry(chembl_id);

-- Ingestion Logs (상세 실행 로그)
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cursor_id UUID REFERENCES ingestion_cursors(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    phase TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
    duration_ms INT,
    records_fetched INT DEFAULT 0,
    records_new INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_source_time 
ON ingestion_logs(source, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_status 
ON ingestion_logs(status);

-- ================================================
-- Done! Domain Data Automation tables created.
-- ================================================
