-- ================================================
-- ADC Platform Database Schema
-- Version: 1.0.0
-- Date: 2026-01-06
-- ================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ================================================
-- 1. MULTI-TENANCY / USERS
-- ================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'member',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, email)
);

CREATE INDEX IF NOT EXISTS idx_app_users_workspace ON app_users(workspace_id);

-- ================================================
-- 2. CATALOG (5 Components)
-- ================================================

CREATE TABLE IF NOT EXISTS component_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('target', 'antibody', 'linker', 'payload', 'conjugation')),
    name TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_grade TEXT DEFAULT 'silver' CHECK (quality_grade IN ('gold', 'silver', 'bronze')),
    status TEXT NOT NULL DEFAULT 'pending_compute' 
        CHECK (status IN ('pending_compute', 'active', 'failed', 'deprecated')),
    compute_error TEXT,
    computed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_component_catalog_type_status ON component_catalog(type, status);
CREATE INDEX IF NOT EXISTS idx_component_catalog_workspace ON component_catalog(workspace_id);

-- Staging table for catalog approval workflow
CREATE TABLE IF NOT EXISTS staging_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_smiles TEXT,
    normalized JSONB NOT NULL DEFAULT '{}'::jsonb,
    source JSONB NOT NULL DEFAULT '{}'::jsonb,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_grade TEXT DEFAULT 'silver',
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'approved', 'rejected')),
    review_note TEXT,
    approved_by UUID REFERENCES app_users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- 3. VERSION MANAGEMENT
-- ================================================

CREATE TABLE IF NOT EXISTS rule_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version TEXT NOT NULL UNIQUE,
    yaml_text TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version TEXT NOT NULL UNIQUE,
    manifest JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scoring_params (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version TEXT NOT NULL UNIQUE,
    params JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- 4. DESIGN RUNS / CANDIDATES / SCORES
-- ================================================

CREATE TABLE IF NOT EXISTS design_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES app_users(id) ON DELETE SET NULL,
    target_ids UUID[] NOT NULL,
    indication TEXT NOT NULL,
    strategy TEXT NOT NULL DEFAULT 'balanced',
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    scoring_version TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    catalog_snapshot TEXT,
    result_summary JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_design_runs_workspace ON design_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_design_runs_status ON design_runs(status);

CREATE TABLE IF NOT EXISTS run_progress (
    run_id UUID PRIMARY KEY REFERENCES design_runs(id) ON DELETE CASCADE,
    phase TEXT NOT NULL DEFAULT 'pending',
    processed_candidates INT NOT NULL DEFAULT 0,
    accepted_candidates INT NOT NULL DEFAULT 0,
    rejected_candidates INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    target_id UUID NOT NULL,
    antibody_id UUID,
    linker_id UUID,
    payload_id UUID,
    conjugation_id UUID,
    candidate_hash TEXT NOT NULL,
    snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(run_id, candidate_hash)
);

CREATE INDEX IF NOT EXISTS idx_candidates_run ON candidates(run_id);

CREATE TABLE IF NOT EXISTS candidate_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    eng_fit NUMERIC NOT NULL DEFAULT 0,
    bio_fit NUMERIC NOT NULL DEFAULT 0,
    safety_fit NUMERIC NOT NULL DEFAULT 0,
    evidence_fit NUMERIC NOT NULL DEFAULT 0,
    evidence_ready BOOLEAN NOT NULL DEFAULT FALSE,
    score_components JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_scores_candidate ON candidate_scores(candidate_id);

CREATE TABLE IF NOT EXISTS candidate_reject_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    reason_code TEXT NOT NULL,
    reason_text TEXT,
    rejected_count INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(run_id, reason_code)
);

-- ================================================
-- 5. PARETO FRONTS
-- ================================================

CREATE TABLE IF NOT EXISTS run_pareto_fronts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    front_index INT NOT NULL DEFAULT 0,
    objectives JSONB NOT NULL,
    member_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS run_pareto_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    front_id UUID NOT NULL REFERENCES run_pareto_fronts(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    rank INT,
    crowding_distance NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- 6. RULES / FEATURE IMPORTANCE
-- ================================================

CREATE TABLE IF NOT EXISTS candidate_rule_hits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    rule_set_version TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    action TEXT NOT NULL,
    delta NUMERIC,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_hits_run_rule ON candidate_rule_hits(run_id, rule_id);

CREATE TABLE IF NOT EXISTS rule_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    rule_set_version TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    n INT NOT NULL DEFAULT 0,
    success_n INT NOT NULL DEFAULT 0,
    failure_n INT NOT NULL DEFAULT 0,
    success_rate NUMERIC,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, rule_set_version, rule_id)
);

CREATE TABLE IF NOT EXISTS feature_importance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    score_type TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    weight_impact NUMERIC NOT NULL,
    method TEXT NOT NULL DEFAULT 'rule+formula',
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feature_importance_run ON feature_importance(run_id, score_type);

-- ================================================
-- 7. LITERATURE / EVIDENCE
-- ================================================

CREATE TABLE IF NOT EXISTS literature_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    pmid TEXT,
    doi TEXT,
    title TEXT NOT NULL,
    authors JSONB,
    abstract TEXT,
    publication_date DATE,
    journal TEXT,
    is_excluded BOOLEAN NOT NULL DEFAULT FALSE,
    exclusion_reason TEXT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_literature_documents_pmid ON literature_documents(pmid) WHERE pmid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_literature_documents_workspace ON literature_documents(workspace_id);

CREATE TABLE IF NOT EXISTS literature_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES literature_documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    embedding VECTOR(1536),
    embedding_status TEXT NOT NULL DEFAULT 'pending' CHECK (embedding_status IN ('pending', 'completed', 'failed')),
    polarity TEXT DEFAULT 'neutral' CHECK (polarity IN ('positive', 'negative', 'neutral')),
    tsvector_content TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_literature_chunks_document ON literature_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_literature_chunks_embedding ON literature_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_literature_chunks_tsvector ON literature_chunks USING gin(tsvector_content);

CREATE TABLE IF NOT EXISTS literature_ingestion_cursors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL DEFAULT 'pubmed',
    query_hash TEXT NOT NULL,
    last_success_at TIMESTAMPTZ,
    last_mindate DATE,
    last_maxdate DATE,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source, query_hash)
);

CREATE TABLE IF NOT EXISTS evidence_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES literature_documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES literature_chunks(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL,
    polarity TEXT NOT NULL,
    strength NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- 8. CANDIDATE EVIDENCE / PROTOCOLS
-- ================================================

CREATE TABLE IF NOT EXISTS candidate_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    summary TEXT,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    conflict_alert BOOLEAN NOT NULL DEFAULT FALSE,
    conflict_details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS protocol_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    template JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    qc_panel JSONB NOT NULL DEFAULT '[]'::jsonb,
    go_no_go JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- 9. FEEDBACK / EXPERIMENTS
-- ================================================

CREATE TABLE IF NOT EXISTS human_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES app_users(id) ON DELETE SET NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    feedback_type TEXT NOT NULL,
    rating INT,
    comment TEXT,
    exclude_from_training BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_human_feedback_ws_entity ON human_feedback(workspace_id, entity_type, entity_id);

CREATE TABLE IF NOT EXISTS assay_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    run_id UUID REFERENCES design_runs(id) ON DELETE SET NULL,
    candidate_id UUID REFERENCES candidates(id) ON DELETE SET NULL,
    assay_type TEXT NOT NULL,
    measured_value NUMERIC,
    unit TEXT,
    is_success BOOLEAN,
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE,
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT NOT NULL DEFAULT 'manual',
    measured_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assay_results_ws_candidate ON assay_results(workspace_id, candidate_id, created_at DESC);

-- ================================================
-- 10. AUDIT EVENTS
-- ================================================

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    user_id UUID REFERENCES app_users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_workspace ON audit_events(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);

-- ================================================
-- 11. DOMAIN DATA AUTOMATION (Connectors)
-- ================================================

-- Raw Source Records (원본 보존)
CREATE TABLE IF NOT EXISTS raw_source_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,  -- pubmed/uniprot/opentargets/chembl/pubchem/hpa/clinicaltrials/openfda
    external_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum TEXT NOT NULL,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_source_unique ON raw_source_records(source, external_id, COALESCE(workspace_id, '00000000-0000-0000-0000-000000000000'::uuid));
CREATE INDEX IF NOT EXISTS idx_raw_source_source ON raw_source_records(source, fetched_at DESC);

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

CREATE INDEX IF NOT EXISTS idx_ingestion_cursors_source ON ingestion_cursors(source, status);

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
    expression JSONB DEFAULT '{}'::jsonb,      -- HPA 발현 데이터
    associations JSONB DEFAULT '{}'::jsonb,    -- Open Targets 연관
    clinical JSONB DEFAULT '{}'::jsonb,        -- ClinicalTrials 정보
    safety_signals JSONB DEFAULT '{}'::jsonb,  -- openFDA 신호
    external_refs JSONB DEFAULT '{}'::jsonb,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_target_profiles_uniprot ON target_profiles(uniprot_id) WHERE uniprot_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_target_profiles_gene ON target_profiles(gene_symbol);
CREATE INDEX IF NOT EXISTS idx_target_profiles_component ON target_profiles(component_id);

-- Compound Registry (화합물 ID 통합 매핑)
CREATE TABLE IF NOT EXISTS compound_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES component_catalog(id) ON DELETE CASCADE,
    canonical_smiles TEXT,
    inchi_key TEXT,
    chembl_id TEXT,
    pubchem_cid TEXT,
    synonyms JSONB DEFAULT '[]'::jsonb,
    activities JSONB DEFAULT '{}'::jsonb,      -- ChEMBL 활성 요약
    properties JSONB DEFAULT '{}'::jsonb,      -- 물성
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_compound_registry_inchikey ON compound_registry(inchi_key) WHERE inchi_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_compound_registry_chembl ON compound_registry(chembl_id);
CREATE INDEX IF NOT EXISTS idx_compound_registry_pubchem ON compound_registry(pubchem_cid);
CREATE INDEX IF NOT EXISTS idx_compound_registry_component ON compound_registry(component_id);

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

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_source_time ON ingestion_logs(source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_cursor ON ingestion_logs(cursor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_status ON ingestion_logs(status);

-- ================================================
-- RLS POLICIES (예시 - workspace_id 기반)
-- ================================================

-- Enable RLS on all user-facing tables
ALTER TABLE design_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE literature_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_feedback ENABLE ROW LEVEL SECURITY;

-- Example policy (adjust based on actual auth setup)
-- CREATE POLICY workspace_isolation ON design_runs
--     FOR ALL
--     USING (workspace_id = current_setting('request.jwt.claims', true)::json->>'workspace_id');
