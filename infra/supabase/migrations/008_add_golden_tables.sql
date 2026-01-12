-- ================================================
-- Migration 008: Add Golden Set Tables
-- Description: Create tables for Golden Set validation and trend analysis
-- ================================================

-- 1. Golden Set 후보 메타
CREATE TABLE IF NOT EXISTS public.golden_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_name text NOT NULL,                -- Kadcyla, Adcetris, Enhertu 등
  target text,                            -- HER2, CD30 등
  antibody text,
  linker text,
  payload text,
  dar_nominal numeric,
  approval_status text,                   -- approved / late_stage / reference
  source_ref text,                        -- DOI/PMID/URL 등
  notes text,
  created_at timestamptz DEFAULT now()
);

-- 2. Golden 실험치 (Metric별 값/단위/Assay)
CREATE TABLE IF NOT EXISTS public.golden_measurements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL REFERENCES public.golden_candidates(id) ON DELETE CASCADE,
  metric_name text NOT NULL,              -- IC50, Aggregation_pct, SerumStability_hr ...
  value numeric NOT NULL,
  unit text,                              -- nM, pM, %, hr 등
  assay_type text,                        -- cell_line, SPR, SEC, DLS ...
  condition text,                         -- buffer, temp, concentration 등 요약
  quality_flag text DEFAULT 'ok',          -- ok / estimated / low_confidence
  source_ref text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_golden_measurements_candidate ON public.golden_measurements(candidate_id);
CREATE INDEX IF NOT EXISTS idx_golden_measurements_metric ON public.golden_measurements(metric_name);

-- 3. Golden 검증 실행 이력
CREATE TABLE IF NOT EXISTS public.golden_validation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_version text NOT NULL,           -- golden set snapshot version
  scoring_version text NOT NULL,           -- scoring formula version
  rule_set_version text,
  retrieval_corpus_version text,
  report_template_version text,
  model_version text,
  status text NOT NULL DEFAULT 'completed', -- completed/failed
  pass boolean NOT NULL DEFAULT false,
  summary jsonb NOT NULL DEFAULT '{}'::jsonb, -- aggregate metrics (MAE, Spearman 등)
  created_at timestamptz DEFAULT now()
);

-- 4. Golden 검증 세부 지표
CREATE TABLE IF NOT EXISTS public.golden_validation_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES public.golden_validation_runs(id) ON DELETE CASCADE,
  axis text,                               -- Bio/Safety/Eng/Clin or "overall"
  metric text NOT NULL,                    -- MAE/RMSE/Spearman/TopKOverlap/KendallTau...
  value numeric,
  threshold numeric,
  pass boolean,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_golden_val_metrics_run ON public.golden_validation_metrics(run_id);

-- RLS 설정
ALTER TABLE public.golden_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.golden_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.golden_validation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.golden_validation_metrics ENABLE ROW LEVEL SECURITY;

-- Admin 권한 정책 (is_admin() 함수가 존재한다고 가정)
-- 만약 is_admin() 함수가 없다면, auth.uid()를 사용하는 간단한 정책으로 대체하거나 함수 생성 필요
-- 여기서는 안전하게 auth.role() = 'authenticated'로 임시 설정하거나, 기존 정책을 따름
-- 기존 마이그레이션(002 등)에서 is_admin()을 사용하지 않았으므로, 일단 authenticated 사용자에게 읽기 권한 부여

CREATE POLICY "Authenticated users can read golden_candidates" ON public.golden_candidates FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read golden_measurements" ON public.golden_measurements FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read golden_validation_runs" ON public.golden_validation_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read golden_validation_metrics" ON public.golden_validation_metrics FOR SELECT TO authenticated USING (true);

-- 쓰기 권한은 서비스 롤(service_role)은 항상 가능하므로 별도 정책 불필요 (Supabase 기본)
