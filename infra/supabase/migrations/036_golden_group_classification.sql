-- Migration: Golden Group Classification
-- Author: Antigravity
-- Date: 2026-01-15
-- Description: Add golden_group column for 4-group classification

-- Add golden_group column
ALTER TABLE golden_seed_items 
ADD COLUMN IF NOT EXISTS golden_group TEXT DEFAULT 'pending'
    CHECK (golden_group IN ('approved', 'clinical_late', 'clinical_early', 'failed', 'pending'));

-- Index for filtering
CREATE INDEX IF NOT EXISTS idx_seed_items_golden_group 
ON golden_seed_items(golden_group);

-- Comment
COMMENT ON COLUMN golden_seed_items.golden_group IS 'Golden Set Group: approved (A), clinical_late (B), clinical_early (C), failed (D), pending';

-- ============================================
-- Data Promotion from JSON (golden_seed_items_rows.json)
-- ============================================

-- Group A: Approved ADC (10개)
UPDATE golden_seed_items
SET is_final = true, 
    golden_group = 'approved', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group A%'
  AND is_final = false;

-- Group B: Late Clinical (Phase 2/3) (4개)
UPDATE golden_seed_items
SET is_final = true, 
    golden_group = 'clinical_late', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group B%'
  AND is_final = false;

-- Group C: Early Clinical (Phase 1) (1개)
UPDATE golden_seed_items
SET is_final = true, 
    golden_group = 'clinical_early', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group C%'
  AND is_final = false;

-- Group D: Failed ADC (2개) - 실패 학습용
UPDATE golden_seed_items
SET golden_group = 'failed', 
    gate_status = 'failed_learning',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group D%';
