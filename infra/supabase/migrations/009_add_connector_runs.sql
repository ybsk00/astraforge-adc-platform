-- ================================================
-- Migration 009: Add Connector Runs Tables
-- Description: Create tables for Connector execution (DB Polling pattern)
-- ================================================

-- 1. Connectors (워커가 참조하는 커넥터 메타데이터)
CREATE TABLE IF NOT EXISTS public.connectors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    type text NOT NULL, -- api, crawler, db ...
    config jsonb DEFAULT '{}'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(name)
);

-- 2. Connector Runs (작업 큐)
CREATE TABLE IF NOT EXISTS public.connector_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id uuid REFERENCES public.connectors(id) ON DELETE CASCADE,
    seed_set_id uuid, -- Optional: 시드 기반 실행 시
    status text NOT NULL DEFAULT 'queued', -- queued, running, succeeded, failed
    attempt int DEFAULT 0,
    result_summary jsonb DEFAULT '{}'::jsonb,
    error_json jsonb,
    started_at timestamptz,
    ended_at timestamptz,
    next_retry_at timestamptz,
    locked_by text, -- Worker ID
    locked_at timestamptz,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_connector_runs_status ON public.connector_runs(status);
CREATE INDEX IF NOT EXISTS idx_connector_runs_locked ON public.connector_runs(locked_at);

-- RLS 설정
ALTER TABLE public.connectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.connector_runs ENABLE ROW LEVEL SECURITY;

-- 정책 설정
CREATE POLICY "Authenticated users can read connectors" ON public.connectors FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can insert connectors" ON public.connectors FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update connectors" ON public.connectors FOR UPDATE TO authenticated USING (true);

CREATE POLICY "Authenticated users can read connector_runs" ON public.connector_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can insert connector_runs" ON public.connector_runs FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update connector_runs" ON public.connector_runs FOR UPDATE TO authenticated USING (true);
