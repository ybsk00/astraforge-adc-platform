-- ============================================
-- Golden Seed Items Manual Promotion SQL
-- JSON 데이터 기반 성공/실패 골든셋 승격
-- ============================================

-- ============================================
-- 1. 성공 골든셋 (Group A/B/C) - 15개
-- ============================================

-- Group A: Approved ADC (10개)
UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Trastuzumab deruxtecan';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Trastuzumab emtansine';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Brentuximab vedotin';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Sacituzumab govitecan';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Enfortumab vedotin';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Polatuzumab vedotin';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Tisotumab vedotin';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Loncastuximab tesirine';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Mirvetuximab soravtansine';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'approved',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Gemtuzumab ozogamicin';

-- Group B: Late Clinical (Phase 2/3) - 4개
UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'clinical_late',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Datopotamab deruxtecan';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'clinical_late',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Telisotuzumab vedotin';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'clinical_late',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Trastuzumab duocarmazine';

UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'clinical_late',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'ABBV-400';

-- Group C: Early Clinical (Phase 1) - 1개
UPDATE golden_seed_items SET
    is_final = true,
    is_failed_adc = false,
    golden_group = 'clinical_early',
    gate_status = 'final',
    is_adc_confirmed = true,
    is_manually_verified = true
WHERE drug_name_canonical = 'Farletuzumab ecteribulin';

-- ============================================
-- 2. 실패 골든셋 (Group D) - 2개
-- ============================================

-- Rova-T: Toxicity (Severe Effusion/Sepsis)
UPDATE golden_seed_items SET
    is_final = false,
    is_failed_adc = true,
    golden_group = 'failed',
    gate_status = 'failed_learning',
    is_adc_confirmed = true,
    is_manually_verified = true,
    failure_learning_notes = 'PBD dimer payload showed severe effusion and sepsis risk. DLL3 targeting may require safer payload class.'
WHERE drug_name_canonical = 'Rovalpituzumab tesirine';

-- SGN-CD33A: Safety (Patient Death in AML)
UPDATE golden_seed_items SET
    is_final = false,
    is_failed_adc = true,
    golden_group = 'failed',
    gate_status = 'failed_learning',
    is_adc_confirmed = true,
    is_manually_verified = true,
    failure_learning_notes = 'PBD dimer in AML setting caused patient deaths. CD33 targeting with PBD class has high safety risk in hematologic malignancies.'
WHERE drug_name_canonical = 'Vadastuximab talirine';

-- ============================================
-- 3. 확인 쿼리
-- ============================================

-- 성공 골든셋 확인
SELECT drug_name_canonical, golden_group, is_final, gate_status
FROM golden_seed_items 
WHERE is_final = true
ORDER BY golden_group, drug_name_canonical;

-- 실패 골든셋 확인
SELECT drug_name_canonical, golden_group, is_failed_adc, failure_mode, key_risk_signal, failure_learning_notes
FROM golden_seed_items 
WHERE is_failed_adc = true;
