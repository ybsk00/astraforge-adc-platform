-- ADC 플랫폼 핵심 인프라 보완 스키마 (v1.3 대응)

-- 1) 런 진행률 및 상태 추적
create table if not exists public.run_progress (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.design_runs(id) on delete cascade,
  phase text not null,                -- normalization, generation, scoring, pareto, evidence, protocol
  step_number int not null,
  total_steps int default 9,
  status text default 'pending',      -- pending, running, completed, failed
  message text,                       -- 상세 상태 메시지 또는 에러 로그
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now()
);

-- 2) 하드 리젝트 사유 요약
create table if not exists public.candidate_reject_summaries (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.design_runs(id) on delete cascade,
  reject_reason text not null,        -- ex) "Lipinski Violation", "High Toxicity Prediction"
  count int default 0,
  created_at timestamptz default now()
);

-- 3) 스코어링 파라미터 버전 관리
create table if not exists public.scoring_params (
  id uuid primary key default gen_random_uuid(),
  version_name text not null,         -- ex) "v0.2_standard"
  weights jsonb not null,             -- {bio: 0.4, safety: 0.3, ...}
  thresholds jsonb not null,          -- {hard_reject: 20, ...}
  is_active boolean default false,
  created_by uuid references auth.users(id),
  created_at timestamptz default now()
);

-- 4) 룰 히트 기록 (Audit/QA용)
create table if not exists public.candidate_rule_hits (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references public.design_candidates(id) on delete cascade,
  rule_id text not null,
  rule_name text,
  impact_score float,
  evidence_context text,
  created_at timestamptz default now()
);

-- 5) 룰 성능 통계
create table if not exists public.rule_performance (
  id uuid primary key default gen_random_uuid(),
  rule_id text not null,
  hit_count int default 0,
  false_positive_count int default 0,
  precision float,
  last_updated timestamptz default now(),
  unique (rule_id)
);

-- 6) 파레토 프론트 관리
create table if not exists public.run_pareto_fronts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.design_runs(id) on delete cascade,
  front_index int not null,           -- 0: Best (Pareto Front), 1: Second, ...
  member_count int default 0,
  dimensions jsonb,                   -- ["bio_fit", "safety_fit", "eng_fit"]
  created_at timestamptz default now()
);

create table if not exists public.run_pareto_members (
  pareto_front_id uuid references public.run_pareto_fronts(id) on delete cascade,
  candidate_id uuid references public.design_candidates(id) on delete cascade,
  primary key (pareto_front_id, candidate_id)
);

-- 7) 근거 시그널 (Evidence Engine)
create table if not exists public.evidence_signals (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references public.design_candidates(id) on delete cascade,
  signal_type text not null,          -- positive, negative, conflict
  source_type text,                   -- literature, patent, clinical_trial
  content text,
  confidence_score float,
  created_at timestamptz default now()
);

-- 8) 전문가 피드백
create table if not exists public.human_feedback (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references public.design_candidates(id) on delete cascade,
  user_id uuid references auth.users(id),
  rating int check (rating between 1 and 5),
  comment text,
  is_gold_standard boolean default false,
  created_at timestamptz default now()
);

-- 9) 시스템 감사 로그
create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,           -- RUN_CREATED, RULESET_CHANGED, REPORT_GENERATED
  user_id uuid references auth.users(id),
  resource_id text,
  payload jsonb,
  ip_address text,
  created_at timestamptz default now()
);

-- RLS 설정
alter table public.run_progress enable row level security;
alter table public.candidate_reject_summaries enable row level security;
alter table public.scoring_params enable row level security;
alter table public.candidate_rule_hits enable row level security;
alter table public.rule_performance enable row level security;
alter table public.run_pareto_fronts enable row level security;
alter table public.run_pareto_members enable row level security;
alter table public.evidence_signals enable row level security;
alter table public.human_feedback enable row level security;
alter table public.audit_events enable row level security;

-- Admin 권한 (기존 is_admin 함수가 있다고 가정)
do $$ 
begin
    drop policy if exists "Admins have full access to run_progress" on public.run_progress;
    drop policy if exists "Admins have full access to candidate_reject_summaries" on public.candidate_reject_summaries;
    drop policy if exists "Admins have full access to scoring_params" on public.scoring_params;
    drop policy if exists "Admins have full access to candidate_rule_hits" on public.candidate_rule_hits;
    drop policy if exists "Admins have full access to rule_performance" on public.rule_performance;
    drop policy if exists "Admins have full access to run_pareto_fronts" on public.run_pareto_fronts;
    drop policy if exists "Admins have full access to run_pareto_members" on public.run_pareto_members;
    drop policy if exists "Admins have full access to evidence_signals" on public.evidence_signals;
    drop policy if exists "Admins have full access to human_feedback" on public.human_feedback;
    drop policy if exists "Admins have full access to audit_events" on public.audit_events;
end $$;

create policy "Admins have full access to run_progress" on public.run_progress for all using (is_admin());
create policy "Admins have full access to candidate_reject_summaries" on public.candidate_reject_summaries for all using (is_admin());
create policy "Admins have full access to scoring_params" on public.scoring_params for all using (is_admin());
create policy "Admins have full access to candidate_rule_hits" on public.candidate_rule_hits for all using (is_admin());
create policy "Admins have full access to rule_performance" on public.rule_performance for all using (is_admin());
create policy "Admins have full access to run_pareto_fronts" on public.run_pareto_fronts for all using (is_admin());
create policy "Admins have full access to run_pareto_members" on public.run_pareto_members for all using (is_admin());
create policy "Admins have full access to evidence_signals" on public.evidence_signals for all using (is_admin());
create policy "Admins have full access to human_feedback" on public.human_feedback for all using (is_admin());
create policy "Admins have full access to audit_events" on public.audit_events for all using (is_admin());
-- 10) RDKit 물성 및 적절성 평가 결과
create table if not exists public.computations_payload_rdkit (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.design_runs(id) on delete cascade,
  payload_id uuid references public.entity_drugs(id) on delete cascade,
  mw float,
  clogp float,
  tpsa float,
  hbd int,
  hba int,
  rotb int,
  rings int,
  arom_rings int,
  fsp3 float,
  aggregation_score float,
  bystander_proxy_score float,
  toxicity_alerts jsonb,              -- [{rule_id, name, severity, matched_smarts}]
  pains_alerts jsonb,                 -- [{rule_id, name}]
  computed_at timestamptz default now()
);

-- 11) 다중항체(bsAb) 적용 가능성 평가 결과
create table if not exists public.computations_target_multispecific (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.design_runs(id) on delete cascade,
  target_a_id uuid references public.entity_targets(id) on delete cascade,
  target_b_id uuid references public.entity_targets(id) on delete cascade,
  expression_selectivity_score float,
  coexpression_risk_score float,
  internalization_score float,
  safety_overlap_score float,
  bsab_applicability_score float,
  rationale jsonb,                    -- {risky_organs: [], UniProt_location: ...}
  computed_at timestamptz default now()
);

-- RLS 설정 추가
alter table public.computations_payload_rdkit enable row level security;
alter table public.computations_target_multispecific enable row level security;

-- Admin 권한 추가
do $$ 
begin
    drop policy if exists "Admins have full access to computations_payload_rdkit" on public.computations_payload_rdkit;
    drop policy if exists "Admins have full access to computations_target_multispecific" on public.computations_target_multispecific;
end $$;

create policy "Admins have full access to computations_payload_rdkit" on public.computations_payload_rdkit for all using (is_admin());
create policy "Admins have full access to computations_target_multispecific" on public.computations_target_multispecific for all using (is_admin());

-- Note: 자동 검증 트리거(Phase 13)
-- scoring_params 테이블의 is_active 변경 시 Supabase Webhook을 통해 
-- Engine의 /api/v1/automation/trigger-validation 엔드포인트를 호출하도록 설정합니다.
-- 감사 로그 타입: GOLDEN_SET_AUTO_VALIDATION, GOLDEN_SET_AUTO_VALIDATION_FAILED

-- 12) Golden Set 후보 메타
create table if not exists public.golden_candidates (
  id uuid primary key default gen_random_uuid(),
  drug_name text not null,                -- Kadcyla, Adcetris, Enhertu 등
  target text,                            -- HER2, CD30 등
  antibody text,
  linker text,
  payload text,
  dar_nominal numeric,
  approval_status text,                   -- approved / late_stage / reference
  source_ref text,                        -- DOI/PMID/URL 등
  notes text,
  created_at timestamptz default now()
);

-- 13) Golden 실험치 (Metric별 값/단위/Assay)
create table if not exists public.golden_measurements (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null references public.golden_candidates(id) on delete cascade,
  metric_name text not null,              -- IC50, Aggregation_pct, SerumStability_hr ...
  value numeric not null,
  unit text,                              -- nM, pM, %, hr 등
  assay_type text,                        -- cell_line, SPR, SEC, DLS ...
  condition text,                         -- buffer, temp, concentration 등 요약
  quality_flag text default 'ok',          -- ok / estimated / low_confidence
  source_ref text,
  created_at timestamptz default now()
);

create index if not exists idx_golden_measurements_candidate on public.golden_measurements(candidate_id);
create index if not exists idx_golden_measurements_metric on public.golden_measurements(metric_name);

-- 14) Golden 검증 실행 이력
create table if not exists public.golden_validation_runs (
  id uuid primary key default gen_random_uuid(),
  dataset_version text not null,           -- golden set snapshot version
  scoring_version text not null,           -- scoring formula version
  rule_set_version text,
  retrieval_corpus_version text,
  report_template_version text,
  model_version text,
  status text not null default 'completed', -- completed/failed
  pass boolean not null default false,
  summary jsonb not null default '{}'::jsonb, -- aggregate metrics (MAE, Spearman 등)
  created_at timestamptz default now()
);

-- 15) Golden 검증 세부 지표
create table if not exists public.golden_validation_metrics (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.golden_validation_runs(id) on delete cascade,
  axis text,                               -- Bio/Safety/Eng/Clin or "overall"
  metric text not null,                    -- MAE/RMSE/Spearman/TopKOverlap/KendallTau...
  value numeric,
  threshold numeric,
  pass boolean,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_golden_val_metrics_run on public.golden_validation_metrics(run_id);

-- 16) 리포트 캐시 메타
create table if not exists public.report_cache (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.design_runs(id) on delete cascade,
  cache_key text not null,                -- sha256(run_id + versions...)
  bucket text not null default 'reports',
  object_path text not null,              -- e.g. reports/<run_id>/<cache_key>.pdf
  sha256 text,
  bytes bigint,
  scoring_version text not null,
  rule_set_version text,
  retrieval_corpus_version text,
  report_template_version text,
  model_version text,
  created_at timestamptz default now(),
  unique (cache_key)
);

-- RLS 설정
alter table public.golden_candidates enable row level security;
alter table public.golden_measurements enable row level security;
alter table public.golden_validation_runs enable row level security;
alter table public.golden_validation_metrics enable row level security;
alter table public.report_cache enable row level security;

-- Admin 권한
create policy "Admins have full access to golden_candidates" on public.golden_candidates for all using (is_admin());
create policy "Admins have full access to golden_measurements" on public.golden_measurements for all using (is_admin());
create policy "Admins have full access to golden_validation_runs" on public.golden_validation_runs for all using (is_admin());
create policy "Admins have full access to golden_validation_metrics" on public.golden_validation_metrics for all using (is_admin());
create policy "Admins have full access to report_cache" on public.report_cache for all using (is_admin());
