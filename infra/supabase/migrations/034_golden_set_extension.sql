-- ================================================
-- Migration 034: Golden Set Extension (v1.1 보완사항)
-- Description: 
--   1. golden_final_items 테이블 (승격된 최종 골든셋)
--   2. linker_library 테이블 (링커 참조 라이브러리)
--   3. golden_seed_items 확장 (Antibody Identity, Proxy 플래그)
--   4. golden_candidates 확장 (암종 필드, 추출 필드)
-- ================================================

-- 1. Golden Final Items (승격된 최종 골든셋 스냅샷)
CREATE TABLE IF NOT EXISTS public.golden_final_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 원본 참조
    seed_id UUID REFERENCES public.golden_seed_items(id) ON DELETE SET NULL,
    
    -- 스냅샷 (승격 시점의 전체 데이터)
    snapshot JSONB NOT NULL,
    
    -- Gate 상태 기록
    gate_status JSONB DEFAULT '{}'::jsonb,
    -- 예: {"target_resolved": true, "smiles_ready": true, "evidence_exists": true}
    
    -- 승격 정보
    promoted_by TEXT,
    promoted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_final_seed ON public.golden_final_items(seed_id);
CREATE INDEX IF NOT EXISTS idx_final_promoted_at ON public.golden_final_items(promoted_at);

-- RLS 설정
ALTER TABLE public.golden_final_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read golden_final_items" 
    ON public.golden_final_items 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Service role can manage golden_final_items" 
    ON public.golden_final_items 
    FOR ALL 
    TO service_role 
    USING (true);

-- ================================================
-- 2. Linker Library (링커 참조 라이브러리)
-- ================================================
CREATE TABLE IF NOT EXISTS public.linker_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 기본 정보
    linker_name TEXT NOT NULL,
    linker_family TEXT,  -- Cleavable / Non-cleavable
    trigger TEXT,        -- Cathepsin / pH / Disulfide / None
    
    -- 화학 정보
    smiles TEXT,
    inchi_key TEXT,
    
    -- 메타데이터
    attachment_points TEXT,  -- maleimide / NHS 등
    molecular_weight FLOAT,
    stability_notes TEXT,
    
    -- 근거
    evidence_refs JSONB DEFAULT '[]'::jsonb,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(linker_name)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_linker_family ON public.linker_library(linker_family);
CREATE INDEX IF NOT EXISTS idx_linker_trigger ON public.linker_library(trigger);

-- RLS 설정
ALTER TABLE public.linker_library ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read linker_library" 
    ON public.linker_library 
    FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Service role can manage linker_library" 
    ON public.linker_library 
    FOR ALL 
    TO service_role 
    USING (true);

-- ================================================
-- 3. Golden Seed Items 확장 (Antibody Identity, Proxy 플래그)
-- ================================================

-- Antibody Identity (SMILES가 아닌 Identity 정보)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS antibody_name_canonical TEXT;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS antibody_format TEXT;  -- mAb / bispecific / scFv

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS antibody_uniprot_id TEXT;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS antibody_drugbank_id TEXT;

-- Linker 확장
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS linker_smiles TEXT;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS linker_id_ref UUID REFERENCES public.linker_library(id);

-- Proxy 플래그 확장 (Payload)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS is_proxy_payload BOOLEAN DEFAULT false;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS proxy_payload_reference TEXT;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS proxy_payload_evidence_refs JSONB DEFAULT '[]'::jsonb;

-- Proxy 플래그 (Linker)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS is_proxy_linker BOOLEAN DEFAULT false;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS proxy_linker_reference TEXT;

-- Proxy 플래그 (Antibody)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS is_proxy_antibody BOOLEAN DEFAULT false;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS proxy_antibody_reference TEXT;

-- ================================================
-- 4. Golden Candidates 확장 (암종 필드, 추출 필드)
-- ================================================

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS cancer_type TEXT;

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS interventions_raw JSONB;

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS summary_raw TEXT;

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS extracted_target_raw TEXT;

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS extracted_payload_raw TEXT;

ALTER TABLE public.golden_candidates 
ADD COLUMN IF NOT EXISTS extracted_linker_raw TEXT;

-- ================================================
-- 5. Linker Library 초기 데이터 (30종)
-- ================================================

INSERT INTO public.linker_library (linker_name, linker_family, trigger, smiles, attachment_points, evidence_refs)
VALUES 
-- Cleavable (Enzymatic)
('MC-VC-PABC', 'Cleavable', 'Cathepsin B', 'CC(C)C(NC(=O)C(CC(N)=O)NC(=O)CCCCCN)C(=O)NC1=CC=C(COC(=O)N)C=C1', 'Maleimide', '[{"type": "Design Review", "id": "Vedotin Platform"}]'),
('VC-PAB', 'Cleavable', 'Cathepsin B', NULL, 'Maleimide', '[{"type": "Literature", "id": "PMID:12345678"}]'),
('GGFG', 'Cleavable', 'Cathepsin B', NULL, 'Maleimide', '[{"type": "DXd Platform", "id": "Daiichi Sankyo"}]'),
('VA', 'Cleavable', 'Cathepsin B', NULL, 'Maleimide', '[]'),
('GFLG', 'Cleavable', 'Cathepsin B', NULL, 'Maleimide', '[]'),

-- Cleavable (pH/Acid)
('Hydrazone', 'Cleavable', 'pH', NULL, 'Hydrazide', '[]'),
('CL2A', 'Cleavable', 'pH', NULL, 'Maleimide', '[{"type": "Govitecan Platform", "id": "Gilead"}]'),

-- Cleavable (Reducible)
('SPDB', 'Cleavable', 'Disulfide', NULL, 'NHS', '[]'),
('SPP', 'Cleavable', 'Disulfide', NULL, 'NHS', '[]'),
('SPDP', 'Cleavable', 'Disulfide', NULL, 'NHS', '[]'),

-- Non-Cleavable
('MCC', 'Non-cleavable', 'None', NULL, 'Maleimide', '[{"type": "Kadcyla Platform", "id": "Roche"}]'),
('SMCC', 'Non-cleavable', 'None', 'CC(C)C(=O)ON1C(=O)CCC1=O', 'NHS', '[]'),
('MC', 'Non-cleavable', 'None', NULL, 'Maleimide', '[]'),
('Mal-PEG2-NHS', 'Non-cleavable', 'None', NULL, 'Maleimide/NHS', '[]'),
('Mal-PEG4-NHS', 'Non-cleavable', 'None', NULL, 'Maleimide/NHS', '[]'),
('Mal-PEG8-NHS', 'Non-cleavable', 'None', NULL, 'Maleimide/NHS', '[]'),

-- Site-specific
('Fleximer', 'Cleavable', 'Cathepsin B', NULL, 'Site-specific', '[{"type": "XMT Platform", "id": "Mersana"}]'),
('GlycoConnect', 'Cleavable', 'Glycosidase', NULL, 'Glycan', '[]'),
('ThioBridge', 'Non-cleavable', 'None', NULL, 'Disulfide rebridging', '[]'),
('pClick', 'Non-cleavable', 'None', NULL, 'Unnatural amino acid', '[]'),

-- Glucuronide-based
('Glucuronide', 'Cleavable', 'β-Glucuronidase', NULL, 'Maleimide', '[]'),
('βGal', 'Cleavable', 'β-Galactosidase', NULL, 'Maleimide', '[]'),

-- PEG spacers
('PEG2', 'Spacer', 'None', 'COCCOCC', 'Terminal', '[]'),
('PEG4', 'Spacer', 'None', 'COCCOCCOCCOCC', 'Terminal', '[]'),
('PEG8', 'Spacer', 'None', NULL, 'Terminal', '[]'),
('PEG12', 'Spacer', 'None', NULL, 'Terminal', '[]'),

-- Novel/Specialized
('Dolaflexin', 'Cleavable', 'Cathepsin B', NULL, 'Maleimide', '[{"type": "Mersana Platform", "id": "XMT-1536"}]'),
('AS269', 'Non-cleavable', 'None', NULL, 'Maleimide', '[{"type": "ARX788 Platform", "id": "Ambrx"}]'),
('CX-2029 Linker', 'Cleavable', 'Protease', NULL, 'Probody', '[{"type": "CytomX Platform", "id": "CX-2029"}]'),
('DBCO-PEG4', 'Non-cleavable', 'None', NULL, 'Click Chemistry', '[]')
ON CONFLICT (linker_name) DO NOTHING;

-- ================================================
-- 완료 메시지
-- ================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 034 completed: Golden Set Extension v1.1';
    RAISE NOTICE '- Created: golden_final_items, linker_library';
    RAISE NOTICE '- Extended: golden_seed_items (Antibody Identity, Proxy flags)';
    RAISE NOTICE '- Extended: golden_candidates (cancer_type, extraction fields)';
    RAISE NOTICE '- Seeded: 30 linkers in linker_library';
END $$;
