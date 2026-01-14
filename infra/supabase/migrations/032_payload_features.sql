-- ================================================
-- Migration 032: Payload Features for RDKit Results
-- Description: RDKit 계산 결과 저장 (Proxy 여부 명시)
-- ================================================

CREATE TABLE IF NOT EXISTS public.payload_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- FK to golden_seed_items
    seed_item_id UUID NOT NULL REFERENCES public.golden_seed_items(id) ON DELETE CASCADE,
    
    -- 계산에 사용된 SMILES
    smiles_used TEXT NOT NULL,
    
    -- Proxy 기반 여부
    is_proxy_derived BOOLEAN DEFAULT false,
    
    -- 기본 물성
    mw FLOAT,              -- Molecular Weight
    logp FLOAT,            -- LogP (친유성)
    tpsa FLOAT,            -- Topological Polar Surface Area
    hbd INTEGER,           -- Hydrogen Bond Donors
    hba INTEGER,           -- Hydrogen Bond Acceptors
    rotatable_bonds INTEGER,
    
    -- 추가 지표
    fraction_csp3 FLOAT,
    num_rings INTEGER,
    formal_charge INTEGER,
    
    -- 품질 점수
    qed_score FLOAT,       -- Quantitative Estimate of Drug-likeness
    sa_score FLOAT,        -- Synthetic Accessibility
    pains_flag BOOLEAN DEFAULT false,  -- PAINS 경고
    
    -- 전처리 정보
    salt_removed BOOLEAN DEFAULT false,
    
    -- RDKit 버전
    rdkit_version TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint (seed_item당 1개)
CREATE UNIQUE INDEX IF NOT EXISTS idx_payload_features_seed 
    ON public.payload_features(seed_item_id);

-- RLS 설정
ALTER TABLE public.payload_features ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read payload_features" 
    ON public.payload_features 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Authenticated users can modify payload_features" 
    ON public.payload_features 
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION public.update_payload_features_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_payload_features_updated_at
    BEFORE UPDATE ON public.payload_features
    FOR EACH ROW
    EXECUTE FUNCTION public.update_payload_features_updated_at();

-- 코멘트
COMMENT ON TABLE public.payload_features IS 'RDKit 계산 결과 저장 - Proxy 여부 명시';
COMMENT ON COLUMN public.payload_features.is_proxy_derived IS 'true: Proxy 구조 기반 계산, 보고서에 명시 필요';
COMMENT ON COLUMN public.payload_features.qed_score IS 'QED: 0~1 (높을수록 약물 유사)';

NOTIFY pgrst, 'reload config';
