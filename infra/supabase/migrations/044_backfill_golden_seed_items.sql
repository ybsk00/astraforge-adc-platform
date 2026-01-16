-- ================================================
-- Migration 044: Backfill Golden Seed Items (Phase 1.5)
-- Description: 
--   1. 기존 레코드 curation_level = 'Manual' 설정
--   2. platform_axis 자동 태깅 (payload 기반)
--   3. evidence_items 기본 생성 (evidence_refs 기반)
-- ================================================

-- ================================================
-- 1. curation_level 기본값 설정
-- ================================================
UPDATE public.golden_seed_items
SET curation_level = 'Manual'
WHERE curation_level IS NULL OR curation_level = 'Draft';

-- ================================================
-- 2. platform_axis 자동 태깅 (payload 기반 추론)
-- ================================================

-- Vedotin/MMAE 계열
UPDATE public.golden_seed_items
SET platform_axis = 'VEDOTIN_MMAE'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%mmae%' OR
    LOWER(payload_family) LIKE '%vedotin%' OR
    LOWER(payload_exact_name) LIKE '%mmae%' OR
    LOWER(payload_exact_name) LIKE '%vedotin%' OR
    LOWER(drug_name_canonical) LIKE '%vedotin%'
  );

-- DXd/Deruxtecan 계열
UPDATE public.golden_seed_items
SET platform_axis = 'DXD'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%dxd%' OR
    LOWER(payload_family) LIKE '%deruxtecan%' OR
    LOWER(payload_exact_name) LIKE '%dxd%' OR
    LOWER(payload_exact_name) LIKE '%deruxtecan%' OR
    LOWER(drug_name_canonical) LIKE '%deruxtecan%' OR
    LOWER(drug_name_canonical) LIKE '%enhertu%'
  );

-- OptiDC/Kelun 계열
UPDATE public.golden_seed_items
SET platform_axis = 'OPTIDC_KELUN'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%optidc%' OR
    LOWER(drug_name_canonical) LIKE '%kelun%' OR
    LOWER(antibody) LIKE '%kelun%'
  );

-- Trodelvy/SN-38 계열 → Independent
UPDATE public.golden_seed_items
SET 
    platform_axis = 'INDEPENDENT',
    independent_subclass = 'Independent (Trodelvy-like/SN-38)'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%sn-38%' OR
    LOWER(payload_family) LIKE '%sn38%' OR
    LOWER(payload_family) LIKE '%govitecan%' OR
    LOWER(drug_name_canonical) LIKE '%trodelvy%' OR
    LOWER(drug_name_canonical) LIKE '%govitecan%'
  );

-- PBD 계열 → Independent
UPDATE public.golden_seed_items
SET 
    platform_axis = 'INDEPENDENT',
    independent_subclass = 'Independent (PBD)'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%pbd%' OR
    LOWER(payload_exact_name) LIKE '%pbd%'
  );

-- Maytansine/DM 계열 → Independent
UPDATE public.golden_seed_items
SET 
    platform_axis = 'INDEPENDENT',
    independent_subclass = 'Independent (Maytansine/DM)'
WHERE platform_axis IS NULL
  AND (
    LOWER(payload_family) LIKE '%maytansine%' OR
    LOWER(payload_family) LIKE '%dm1%' OR
    LOWER(payload_family) LIKE '%dm4%' OR
    LOWER(payload_exact_name) LIKE '%emtansine%' OR
    LOWER(drug_name_canonical) LIKE '%emtansine%' OR
    LOWER(drug_name_canonical) LIKE '%kadcyla%'
  );

-- 나머지 → Independent (Other)
UPDATE public.golden_seed_items
SET 
    platform_axis = 'INDEPENDENT',
    independent_subclass = 'Independent (Other - requires review)'
WHERE platform_axis IS NULL;

-- ================================================
-- 3. evidence_refs에서 evidence_items로 마이그레이션
-- ================================================
-- evidence_refs JSONB 배열의 각 항목을 evidence_items 테이블로 이동

-- Step 1: evidence_refs가 있고 evidence_items가 없는 레코드 처리
INSERT INTO public.evidence_items (golden_seed_item_id, type, id_or_url, title, snippet)
SELECT 
    gsi.id as golden_seed_item_id,
    COALESCE(ref->>'type', 'other') as type,
    COALESCE(ref->>'id', ref->>'url', ref->>'id_or_url') as id_or_url,
    ref->>'title' as title,
    ref->>'snippet' as snippet
FROM public.golden_seed_items gsi,
     jsonb_array_elements(gsi.evidence_refs) as ref
WHERE jsonb_array_length(gsi.evidence_refs) > 0
  AND NOT EXISTS (
    SELECT 1 FROM public.evidence_items ei 
    WHERE ei.golden_seed_item_id = gsi.id
  );

-- ================================================
-- 4. Outcome 기본값 설정
-- ================================================

-- Approved/Active → Unknown (검토 필요)
UPDATE public.golden_seed_items
SET outcome = 'Unknown'
WHERE outcome IS NULL;

-- ================================================
-- 5. 통계 출력
-- ================================================
DO $$
DECLARE
    total_count INT;
    vedotin_count INT;
    dxd_count INT;
    optidc_count INT;
    independent_count INT;
    evidence_count INT;
BEGIN
    SELECT COUNT(*) INTO total_count FROM public.golden_seed_items;
    SELECT COUNT(*) INTO vedotin_count FROM public.golden_seed_items WHERE platform_axis = 'VEDOTIN_MMAE';
    SELECT COUNT(*) INTO dxd_count FROM public.golden_seed_items WHERE platform_axis = 'DXD';
    SELECT COUNT(*) INTO optidc_count FROM public.golden_seed_items WHERE platform_axis = 'OPTIDC_KELUN';
    SELECT COUNT(*) INTO independent_count FROM public.golden_seed_items WHERE platform_axis = 'INDEPENDENT';
    SELECT COUNT(*) INTO evidence_count FROM public.evidence_items;
    
    RAISE NOTICE 'Migration 044 completed: Backfill Golden Seed Items';
    RAISE NOTICE '  Total records: %', total_count;
    RAISE NOTICE '  - VEDOTIN_MMAE: %', vedotin_count;
    RAISE NOTICE '  - DXD: %', dxd_count;
    RAISE NOTICE '  - OPTIDC_KELUN: %', optidc_count;
    RAISE NOTICE '  - INDEPENDENT: %', independent_count;
    RAISE NOTICE '  Evidence items created: %', evidence_count;
END $$;

NOTIFY pgrst, 'reload config';
