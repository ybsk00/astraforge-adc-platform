-- ================================================
-- Migration 044: Backfill Golden Seed Items (Phase 1.5)
-- Description: 
--   1. 기존 레코드 curation_level = 'Manual' 설정
--   2. platform_axis 자동 태깅 (payload 기반)
--   3. evidence_items 기본 생성 (evidence_refs 기반)
-- 
-- NOTE: 이 마이그레이션은 039_golden_seed_items_extension.sql 이후에 실행되어야 합니다.
-- ================================================

DO $$
DECLARE
    col_exists BOOLEAN;
    total_count INT;
    vedotin_count INT;
    dxd_count INT;
    optidc_count INT;
    independent_count INT;
    evidence_count INT;
BEGIN
    -- Check if curation_level column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'golden_seed_items' 
        AND column_name = 'curation_level'
    ) INTO col_exists;
    
    IF NOT col_exists THEN
        RAISE NOTICE 'Column curation_level does not exist. Please run 039_golden_seed_items_extension.sql first.';
        RETURN;
    END IF;

    -- ================================================
    -- 1. curation_level 기본값 설정
    -- ================================================
    UPDATE public.golden_seed_items
    SET curation_level = 'Manual'
    WHERE curation_level IS NULL OR curation_level = 'Draft';
    
    RAISE NOTICE 'Updated curation_level to Manual';

    -- ================================================
    -- 2. platform_axis 자동 태깅 (payload 기반 추론)
    -- ================================================
    
    -- Vedotin/MMAE 계열
    UPDATE public.golden_seed_items
    SET platform_axis = 'VEDOTIN_MMAE'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%mmae%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%vedotin%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%mmae%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%vedotin%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%vedotin%'
      );

    -- DXd/Deruxtecan 계열
    UPDATE public.golden_seed_items
    SET platform_axis = 'DXD'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%dxd%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%deruxtecan%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%dxd%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%deruxtecan%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%deruxtecan%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%enhertu%'
      );

    -- OptiDC/Kelun 계열
    UPDATE public.golden_seed_items
    SET platform_axis = 'OPTIDC_KELUN'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%optidc%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%kelun%' OR
        LOWER(COALESCE(antibody, '')) LIKE '%kelun%'
      );

    -- Trodelvy/SN-38 계열 → Independent
    UPDATE public.golden_seed_items
    SET 
        platform_axis = 'INDEPENDENT',
        independent_subclass = 'Independent (Trodelvy-like/SN-38)'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%sn-38%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%sn38%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%govitecan%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%trodelvy%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%govitecan%'
      );

    -- PBD 계열 → Independent
    UPDATE public.golden_seed_items
    SET 
        platform_axis = 'INDEPENDENT',
        independent_subclass = 'Independent (PBD)'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%pbd%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%pbd%'
      );

    -- Maytansine/DM 계열 → Independent
    UPDATE public.golden_seed_items
    SET 
        platform_axis = 'INDEPENDENT',
        independent_subclass = 'Independent (Maytansine/DM)'
    WHERE platform_axis IS NULL
      AND (
        LOWER(COALESCE(payload_family, '')) LIKE '%maytansine%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%dm1%' OR
        LOWER(COALESCE(payload_family, '')) LIKE '%dm4%' OR
        LOWER(COALESCE(payload_exact_name, '')) LIKE '%emtansine%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%emtansine%' OR
        LOWER(COALESCE(drug_name_canonical, '')) LIKE '%kadcyla%'
      );

    -- 나머지 → Independent (Other)
    UPDATE public.golden_seed_items
    SET 
        platform_axis = 'INDEPENDENT',
        independent_subclass = 'Independent (Other - requires review)'
    WHERE platform_axis IS NULL;
    
    RAISE NOTICE 'Updated platform_axis based on payload keywords';

    -- ================================================
    -- 3. Outcome 기본값 설정
    -- ================================================
    UPDATE public.golden_seed_items
    SET outcome = 'Unknown'
    WHERE outcome IS NULL;
    
    RAISE NOTICE 'Set default outcome to Unknown';

    -- ================================================
    -- 4. 통계 출력
    -- ================================================
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
    RAISE NOTICE '  Evidence items: %', evidence_count;
    
END $$;

-- ================================================
-- 5. evidence_refs에서 evidence_items로 마이그레이션
-- (별도 블록: evidence_items 테이블 존재 확인)
-- ================================================
DO $$
BEGIN
    -- Check if evidence_items table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_items'
    ) THEN
        -- evidence_refs가 있고 evidence_items가 없는 레코드 처리
        INSERT INTO public.evidence_items (golden_seed_item_id, type, id_or_url, title, snippet, source_type, external_id)
        SELECT 
            gsi.id as golden_seed_item_id,
            COALESCE(ref->>'type', 'other') as type,
            COALESCE(ref->>'id', ref->>'url', ref->>'id_or_url') as id_or_url,
            ref->>'title' as title,
            ref->>'snippet' as snippet,
            COALESCE(ref->>'source_type', ref->>'type', 'other') as source_type,
            COALESCE(ref->>'external_id', ref->>'id', ref->>'url', ref->>'id_or_url', 'unknown') as external_id
        FROM public.golden_seed_items gsi,
             jsonb_array_elements(gsi.evidence_refs) as ref
        WHERE gsi.evidence_refs IS NOT NULL
          AND jsonb_array_length(gsi.evidence_refs) > 0
          AND NOT EXISTS (
            SELECT 1 FROM public.evidence_items ei 
            WHERE ei.golden_seed_item_id = gsi.id
          );
        
        RAISE NOTICE 'Migrated evidence_refs to evidence_items table';
    ELSE
        RAISE NOTICE 'evidence_items table does not exist. Skipping migration.';
    END IF;
END $$;

NOTIFY pgrst, 'reload config';
