-- 1) 암종 엔티티
create table if not exists public.entity_diseases (
  id uuid primary key default gen_random_uuid(),
  disease_name text not null,
  disease_group text,                 -- ex) "solid", "heme"
  ontology_source text,               -- ex) "EFO", "MONDO"
  ontology_id text,                   -- ex) "EFO_0000305"
  search_term text,                   -- 검색 기본어
  is_active boolean default true,
  created_at timestamptz default now(),
  unique (disease_name)
);

-- 2) 표적 엔티티
create table if not exists public.entity_targets (
  id uuid primary key default gen_random_uuid(),
  gene_symbol text not null,          -- HGNC symbol
  ensembl_gene_id text,               -- Open Targets 핵심키
  uniprot_accession text,             -- UniProt 키
  target_class text,                  -- ex) "kinase", "adc_antigen"
  is_active boolean default true,
  created_at timestamptz default now(),
  unique (gene_symbol)
);

-- 3) 약물/페이로드 엔티티
create table if not exists public.entity_drugs (
  id uuid primary key default gen_random_uuid(),
  drug_name text not null,
  drug_class text,                    -- ex) "small_molecule", "mAb", "payload"
  chembl_id text,                     -- ChEMBL ID
  pubchem_cid text,                   -- PubChem CID
  inchikey text,                      -- 구조 식별자
  is_active boolean default true,
  created_at timestamptz default now(),
  unique (drug_name)
);

-- 4) Seed Set (실행 단위)
create table if not exists public.seed_sets (
  id uuid primary key default gen_random_uuid(),
  seed_set_name text not null,
  description text,
  is_active boolean default true,
  created_at timestamptz default now(),
  unique (seed_set_name)
);

-- 5) Join Tables
create table if not exists public.seed_set_diseases (
  seed_set_id uuid references public.seed_sets(id) on delete cascade,
  disease_id  uuid references public.entity_diseases(id) on delete cascade,
  primary key (seed_set_id, disease_id)
);

create table if not exists public.seed_set_targets (
  seed_set_id uuid references public.seed_sets(id) on delete cascade,
  target_id   uuid references public.entity_targets(id) on delete cascade,
  primary key (seed_set_id, target_id)
);

create table if not exists public.seed_set_drugs (
  seed_set_id uuid references public.seed_sets(id) on delete cascade,
  drug_id     uuid references public.entity_drugs(id) on delete cascade,
  primary key (seed_set_id, drug_id)
);

-- 6) Staging Components (검수용)
create table if not exists public.staging_components (
  id uuid primary key default gen_random_uuid(),
  type text not null,                 -- target/linker/payload/antibody
  name text not null,
  canonical_smiles text,
  normalized jsonb,                   -- 표준화된 데이터
  source_info jsonb,                  -- 출처 정보
  status text default 'pending_review', -- pending_review/approved/rejected
  review_note text,
  approved_at timestamptz,
  created_at timestamptz default now()
);

-- RLS 설정 (Admin 전용)
alter table public.entity_diseases enable row level security;
alter table public.entity_targets enable row level security;
alter table public.entity_drugs enable row level security;
alter table public.seed_sets enable row level security;
alter table public.seed_set_diseases enable row level security;
alter table public.seed_set_targets enable row level security;
alter table public.seed_set_drugs enable row level security;
alter table public.staging_components enable row level security;

-- Admin 권한 부여 (기존 is_admin 함수 활용)
create policy "Admins have full access to entity_diseases" on public.entity_diseases for all using (is_admin());
create policy "Admins have full access to entity_targets" on public.entity_targets for all using (is_admin());
create policy "Admins have full access to entity_drugs" on public.entity_drugs for all using (is_admin());
create policy "Admins have full access to seed_sets" on public.seed_sets for all using (is_admin());
create policy "Admins have full access to seed_set_diseases" on public.seed_set_diseases for all using (is_admin());
create policy "Admins have full access to seed_set_targets" on public.seed_set_targets for all using (is_admin());
create policy "Admins have full access to seed_set_drugs" on public.seed_set_drugs for all using (is_admin());
create policy "Admins have full access to staging_components" on public.staging_components for all using (is_admin());
