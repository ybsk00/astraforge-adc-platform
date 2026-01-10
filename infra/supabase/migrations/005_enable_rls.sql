-- ================================================
-- Migration 005: Enable RLS & Add Missing Tables
-- Description: Consolidate schema (assay_results) and enforce RLS
-- ================================================

-- 1. Create assay_results table (if not exists)
-- This table was in schema.sql but missing from previous migrations
CREATE TABLE IF NOT EXISTS public.assay_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX IF NOT EXISTS idx_assay_results_ws_candidate ON public.assay_results(workspace_id, candidate_id, created_at DESC);

-- 2. Enable RLS on all key tables
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.design_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assay_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.literature_documents ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies

-- Helper function to check workspace membership
-- Assumes app_users.email matches auth.email()
CREATE OR REPLACE FUNCTION public.is_workspace_member(ws_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 
    FROM public.app_users au
    WHERE au.workspace_id = ws_id
    AND au.email = auth.email()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Workspaces: Members can view their own workspace
CREATE POLICY "Members can view own workspace"
    ON public.workspaces FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.app_users au
            WHERE au.workspace_id = workspaces.id
            AND au.email = auth.email()
        )
    );

-- App Users: Users can view profiles in their workspace
CREATE POLICY "Users can view profiles in same workspace"
    ON public.app_users FOR SELECT
    USING (
        workspace_id IN (
            SELECT workspace_id FROM public.app_users WHERE email = auth.email()
        )
    );

-- Design Runs: Workspace isolation
CREATE POLICY "Workspace members can view runs"
    ON public.design_runs FOR SELECT
    USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Workspace members can create runs"
    ON public.design_runs FOR INSERT
    WITH CHECK (public.is_workspace_member(workspace_id));

CREATE POLICY "Workspace members can update runs"
    ON public.design_runs FOR UPDATE
    USING (public.is_workspace_member(workspace_id));

-- Candidates: Workspace isolation (via run -> workspace, but candidates table doesn't have workspace_id directly)
-- We need to join with design_runs.
-- Note: RLS with joins can be slow. Better to add workspace_id to candidates or trust the run_id check if run_id is verified.
-- However, for strict RLS, we should check.
-- Adding workspace_id to candidates would be better for performance, but let's use join for now as per schema.
CREATE POLICY "Workspace members can view candidates"
    ON public.candidates FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.design_runs dr
            WHERE dr.id = candidates.run_id
            AND public.is_workspace_member(dr.workspace_id)
        )
    );

-- Assay Results: Workspace isolation
CREATE POLICY "Workspace members can view assay results"
    ON public.assay_results FOR SELECT
    USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Workspace members can create assay results"
    ON public.assay_results FOR INSERT
    WITH CHECK (public.is_workspace_member(workspace_id));

-- Component Catalog: Workspace isolation + Public items (workspace_id IS NULL)
CREATE POLICY "Workspace members can view catalog"
    ON public.component_catalog FOR SELECT
    USING (
        workspace_id IS NULL 
        OR public.is_workspace_member(workspace_id)
    );

CREATE POLICY "Workspace members can create catalog items"
    ON public.component_catalog FOR INSERT
    WITH CHECK (
        workspace_id IS NOT NULL 
        AND public.is_workspace_member(workspace_id)
    );

-- Literature Documents: Workspace isolation
CREATE POLICY "Workspace members can view literature"
    ON public.literature_documents FOR SELECT
    USING (public.is_workspace_member(workspace_id));

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
