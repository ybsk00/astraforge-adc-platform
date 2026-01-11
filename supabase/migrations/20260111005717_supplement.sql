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
alter table public.computations_payload_rdkit enable row level security;
alter table public.computations_target_multispecific enable row level security;

-- Admin 권한
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
    drop policy if exists "Admins have full access to computations_payload_rdkit" on public.computations_payload_rdkit;
    drop policy if exists "Admins have full access to computations_target_multispecific" on public.computations_target_multispecific;
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
create policy "Admins have full access to computations_payload_rdkit" on public.computations_payload_rdkit for all using (is_admin());
create policy "Admins have full access to computations_target_multispecific" on public.computations_target_multispecific for all using (is_admin());
