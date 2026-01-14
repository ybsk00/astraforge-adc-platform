-- ================================================
-- Migration 028: Golden Seed Items for Manual Curation
-- Description: Create golden_seed_items table for manual ADC seed management
-- Workflow: Auto (golden_candidates) → Import → Manual (golden_seed_items) → Final
-- ================================================

-- 1. Golden Seed Items (Manual Seed 전용)
CREATE TABLE IF NOT EXISTS public.golden_seed_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Import 출처 추적 (Auto에서 Import한 경우)
    source_candidate_id UUID REFERENCES public.golden_candidates(id) ON DELETE SET NULL,
    
    -- 기본 정보 (필수)
    drug_name_canonical TEXT NOT NULL,
    aliases TEXT,  -- pipe 구분자 (예: "Enhertu|DS-8201")
    portfolio_group TEXT,  -- "Group A (Approved)", "Group B (Late)" 등
    
    -- 컴포넌트 정보
    target TEXT NOT NULL,
    resolved_target_symbol TEXT,  -- 표준화된 타겟 (예: HER2 → ERBB2)
    antibody TEXT,
    linker_family TEXT,
    linker_trigger TEXT,
    payload_family TEXT,
    payload_exact_name TEXT,
    
    -- SMILES 및 화학 정보
    payload_smiles_raw TEXT,
    payload_smiles_standardized TEXT,
    payload_cid TEXT,
    payload_inchi_key TEXT,
    proxy_smiles_flag BOOLEAN DEFAULT false,
    proxy_reference TEXT,
    is_proxy_derived BOOLEAN DEFAULT false,
    
    -- 임상 정보
    clinical_phase TEXT,
    program_status TEXT,
    clinical_nct_id_primary TEXT,
    clinical_nct_ids_secondary JSONB DEFAULT '[]'::jsonb,
    
    -- 결과/레이블
    outcome_label TEXT,  -- Success/Fail/Uncertain/Caution
    key_risk_category TEXT,
    key_risk_signal TEXT,
    failure_mode TEXT,
    
    -- 근거/출처
    primary_source_type TEXT,  -- "FDA Label", "Clinical Trial", "Review Paper"
    primary_source_id TEXT,    -- BLA번호, NCT번호, PMID 등
    evidence_refs JSONB DEFAULT '[]'::jsonb,
    
    -- 품질 게이트 상태
    -- draft: 초기 상태
    -- needs_review: Import 후 검토 필요
    -- ready_to_promote: 승격 조건 충족
    -- final: 승격 완료
    gate_status TEXT DEFAULT 'draft',
    is_final BOOLEAN DEFAULT false,
    
    -- 수동 검증/잠금 (Overwrite Protection)
    is_manually_verified BOOLEAN DEFAULT false,
    field_verified JSONB DEFAULT '{}'::jsonb,
    last_verified_at TIMESTAMPTZ,
    verified_by TEXT,
    
    -- RDKit 특성치 (Phase 2에서 채움)
    rdkit_mw FLOAT,
    rdkit_logp FLOAT,
    rdkit_tpsa FLOAT,
    rdkit_hbd INTEGER,
    rdkit_hba INTEGER,
    rdkit_qed FLOAT,
    
    -- 승격 정보
    finalized_by TEXT,
    finalized_at TIMESTAMPTZ,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint (동일 약물 중복 방지)
ALTER TABLE public.golden_seed_items
ADD CONSTRAINT golden_seed_items_unique_drug UNIQUE (drug_name_canonical);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_golden_seed_items_gate_status ON public.golden_seed_items(gate_status);
CREATE INDEX IF NOT EXISTS idx_golden_seed_items_is_final ON public.golden_seed_items(is_final);
CREATE INDEX IF NOT EXISTS idx_golden_seed_items_target ON public.golden_seed_items(target);
CREATE INDEX IF NOT EXISTS idx_golden_seed_items_source ON public.golden_seed_items(source_candidate_id);

-- RLS 설정
ALTER TABLE public.golden_seed_items ENABLE ROW LEVEL SECURITY;

-- 읽기 정책 (인증된 사용자)
CREATE POLICY "Authenticated users can read golden_seed_items" 
    ON public.golden_seed_items 
    FOR SELECT 
    TO authenticated 
    USING (true);

-- 쓰기는 service_role만 가능 (Supabase 기본)

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_golden_seed_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_golden_seed_items_updated_at
    BEFORE UPDATE ON public.golden_seed_items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_golden_seed_items_updated_at();

-- 코멘트
COMMENT ON TABLE public.golden_seed_items IS 'Manual curated ADC seeds for reference. Auto → Import → Manual → Final workflow.';
COMMENT ON COLUMN public.golden_seed_items.source_candidate_id IS 'FK to golden_candidates if imported from Auto collection';
COMMENT ON COLUMN public.golden_seed_items.gate_status IS 'draft/needs_review/ready_to_promote/final';
COMMENT ON COLUMN public.golden_seed_items.is_manually_verified IS 'If true, no Job can overwrite this record';

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
