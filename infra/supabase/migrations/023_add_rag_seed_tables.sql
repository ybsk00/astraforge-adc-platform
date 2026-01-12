-- 1. Seed Query Sets (RAG 검색 입력 묶음)
create table if not exists seed_query_sets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  status text not null default 'active', -- active/archived
  created_at timestamptz not null default now()
);

create table if not exists seed_queries (
  id uuid primary key default gen_random_uuid(),
  seed_query_set_id uuid not null references seed_query_sets(id) on delete cascade,
  query_text text not null,     -- 예: "HER2 antibody-drug conjugate linker payload"
  top_k int not null default 50,
  min_score numeric not null default 0.0,
  created_at timestamptz not null default now()
);

-- 2. Entity Tables (엔티티 사전)
create table if not exists entity_targets (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_antibodies (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_linkers (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  linker_type text,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_payloads (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  payload_class text,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

create table if not exists entity_drugs (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  synonyms text[] default '{}',
  created_at timestamptz not null default now()
);

-- 3. Seed Sets (운영에 쓰는 묶음)
create table if not exists seed_sets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  version text not null,
  status text not null default 'draft', -- draft/active/archived
  source text not null default 'rag',   -- rag/manual/golden_promoted 등
  seed_query_set_id uuid references seed_query_sets(id),
  created_at timestamptz not null default now(),
  unique(name, version)
);

-- Seed Set Items (구성요소 조합)
create table if not exists seed_set_items (
  id uuid primary key default gen_random_uuid(),
  seed_set_id uuid not null references seed_sets(id) on delete cascade,
  target_id uuid references entity_targets(id),
  antibody_id uuid references entity_antibodies(id),
  linker_id uuid references entity_linkers(id),
  payload_id uuid references entity_payloads(id),
  drug_id uuid references entity_drugs(id),
  confidence_score int not null default 0,
  evidence_count int not null default 0,
  created_at timestamptz not null default now()
);

-- 중복 방지 (동일 seed_set 내 동일 조합)
create unique index if not exists seed_set_items_unique_key
on seed_set_items (seed_set_id, target_id, antibody_id, linker_id, payload_id, drug_id);

-- 4. Evidence (근거 연결)
create table if not exists entity_evidence (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null,     -- target/antibody/linker/payload/drug/seed_item
  entity_id uuid not null,
  source text not null,          -- PubMed
  ref_id text not null,          -- PMID
  chunk_id uuid references literature_chunks(id),
  snippet text,
  created_at timestamptz not null default now()
);

-- 중복 방지
create unique index if not exists entity_evidence_unique_key
on entity_evidence (entity_type, entity_id, source, ref_id, chunk_id);
