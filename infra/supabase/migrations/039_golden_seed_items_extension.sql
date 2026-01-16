-- ================================================
-- Migration 039: Golden Seed Items Extension (True Golden Set)
-- Description: 
--   1. 4대축 분류 필드 추가
--   2. Construct Ready 필드 추가 (Gate 필수)
--   3. 실패 구조화 필드 추가 (Phase 4 연결)
--   4. 상태/결과 표준화 필드 추가 (Outcome Consistent)
--   5. 품질 관리 필드 추가
-- ================================================

-- ================================================
-- 1. 4대축 분류 필드
-- ================================================
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS platform_axis TEXT;
-- Values: VEDOTIN_MMAE / DXD / OPTIDC_KELUN / INDEPENDENT

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS independent_subclass TEXT;
-- axis=INDEPENDENT일 때 필수
-- Examples: Independent (Trodelvy-like/SN-38), Independent (PBD), Independent (Novel payload)

-- synonyms 배열 (동의어 목록)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS synonyms TEXT[];

-- ================================================
-- 2. Construct Ready 필드 (Gate Checklist 필수)
-- ================================================
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS payload_family TEXT;
-- Values: MMAE / DXd / OptiDC / SN-38 / PBD / Maytansine / Other

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS payload_specific TEXT;
-- Optional: 정확한 payload 이름

-- linker_type이 이미 있을 수 있으므로 IF NOT EXISTS 사용
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS linker_type TEXT;
-- Values: Cleavable / Non-cleavable

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS conjugation_method TEXT;
-- Values: Cysteine / Lysine / Site-specific / Other

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS dar_range TEXT;
-- Examples: 4, 8, 2-4, ~7.4

-- ================================================
-- 3. 실패 구조화 필드 (Phase 4 연결)
-- ================================================
-- failure_mode가 이미 있을 수 있으므로 확인
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS failure_mode TEXT;
-- Values: Toxicity / CMC-Aggregation / PK / Efficacy / Immunogenicity / Other

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS key_failure_signal TEXT;
-- 주요 실패 신호 (예: Hepatotoxicity, ILD, Ocular toxicity)

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS discontinued_reason_summary TEXT;
-- 중단 사유 요약

-- ================================================
-- 4. 상태/결과 표준화 (Outcome Consistent)
-- ================================================
-- program_status가 이미 있을 수 있으므로 확인
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS program_status TEXT;
-- Values: Active / Approved / Discontinued

-- clinical_stage (기존 clinical_phase와 통합 검토 필요)
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS clinical_stage TEXT;
-- Values: Preclinical / Phase1 / Phase2 / Phase3 / Approved / Discontinued

-- outcome
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS outcome TEXT;
-- Values: Success / Fail / Unknown

-- ================================================
-- 5. 품질 관리 필드
-- ================================================
ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS evidence_grade TEXT;
-- Values: A / B / C / D / F
-- Gate 조건: B 이상 (score >= 4)

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS curation_level TEXT DEFAULT 'Draft';
-- Values: Draft / Manual / Review / Final

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS reviewed_by TEXT;

ALTER TABLE public.golden_seed_items 
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

-- ================================================
-- 인덱스 추가
-- ================================================
CREATE INDEX IF NOT EXISTS idx_golden_seed_items_platform_axis 
    ON public.golden_seed_items(platform_axis);

CREATE INDEX IF NOT EXISTS idx_golden_seed_items_outcome 
    ON public.golden_seed_items(outcome);

CREATE INDEX IF NOT EXISTS idx_golden_seed_items_curation_level 
    ON public.golden_seed_items(curation_level);

-- ================================================
-- 코멘트
-- ================================================
COMMENT ON COLUMN public.golden_seed_items.platform_axis IS '4대축 분류: VEDOTIN_MMAE, DXD, OPTIDC_KELUN, INDEPENDENT';
COMMENT ON COLUMN public.golden_seed_items.independent_subclass IS 'Independent 축일 때 필수 서브클래스';
COMMENT ON COLUMN public.golden_seed_items.payload_family IS 'Construct Ready: payload 계열 (Gate 필수)';
COMMENT ON COLUMN public.golden_seed_items.linker_type IS 'Construct Ready: linker 타입 (Gate 필수)';
COMMENT ON COLUMN public.golden_seed_items.conjugation_method IS 'Construct Ready: 접합 방법 (Gate 필수)';
COMMENT ON COLUMN public.golden_seed_items.failure_mode IS '실패 모드: Toxicity, CMC-Aggregation, PK, Efficacy, Immunogenicity, Other';
COMMENT ON COLUMN public.golden_seed_items.evidence_grade IS '근거 등급: A(최고) ~ F(최저), Gate 조건 B 이상';
COMMENT ON COLUMN public.golden_seed_items.curation_level IS '큐레이션 수준: Draft, Manual, Review, Final';

-- ================================================
-- 완료 메시지
-- ================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 039 completed: Golden Seed Items Extension for True Golden Set';
    RAISE NOTICE '- Added: 4대축 분류 필드 (platform_axis, independent_subclass, synonyms)';
    RAISE NOTICE '- Added: Construct Ready 필드 (payload_family, payload_specific, linker_type, conjugation_method, dar_range)';
    RAISE NOTICE '- Added: 실패 구조화 필드 (failure_mode, key_failure_signal, discontinued_reason_summary)';
    RAISE NOTICE '- Added: 상태/결과 표준화 필드 (program_status, clinical_stage, outcome)';
    RAISE NOTICE '- Added: 품질 관리 필드 (evidence_grade, curation_level, is_verified, reviewed_by, reviewed_at)';
END $$;

NOTIFY pgrst, 'reload config';
