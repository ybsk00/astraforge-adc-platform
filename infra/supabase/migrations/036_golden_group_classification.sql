-- Migration: Golden Group Classification + Failed ADC Analysis
-- Author: Antigravity
-- Date: 2026-01-15
-- Description: Add golden_group column and failure analysis fields

-- Add golden_group column
ALTER TABLE golden_seed_items 
ADD COLUMN IF NOT EXISTS golden_group TEXT DEFAULT 'pending'
    CHECK (golden_group IN ('approved', 'clinical_late', 'clinical_early', 'failed', 'pending'));

-- Add failure analysis columns
ALTER TABLE golden_seed_items
ADD COLUMN IF NOT EXISTS is_failed_adc BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS failure_learning_notes TEXT;

-- Note: failure_mode, key_risk_category, key_risk_signal already exist in the table from JSON import
-- We will use these existing columns for failure analysis

-- Index for filtering
CREATE INDEX IF NOT EXISTS idx_seed_items_golden_group 
ON golden_seed_items(golden_group);

CREATE INDEX IF NOT EXISTS idx_seed_items_is_failed_adc 
ON golden_seed_items(is_failed_adc) WHERE is_failed_adc = true;

-- Exclusive constraint: cannot be both is_final=true AND is_failed_adc=true
-- Using partial unique index approach for compatibility
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_final_vs_failed'
    ) THEN
        ALTER TABLE golden_seed_items
        ADD CONSTRAINT chk_final_vs_failed
        CHECK (NOT (is_final = true AND is_failed_adc = true));
    END IF;
END $$;

-- Comments
COMMENT ON COLUMN golden_seed_items.golden_group IS 'Golden Set Group: approved (A), clinical_late (B), clinical_early (C), failed (D), pending';
COMMENT ON COLUMN golden_seed_items.is_failed_adc IS 'Failed ADC for learning/risk analysis (mutually exclusive with is_final)';
COMMENT ON COLUMN golden_seed_items.failure_learning_notes IS 'Human-curated notes on failure patterns and lessons learned';

-- ============================================
-- Data Promotion from JSON (golden_seed_items_rows.json)
-- ============================================

-- Group A: Approved ADC (10개)
UPDATE golden_seed_items
SET is_final = true, 
    is_failed_adc = false,
    golden_group = 'approved', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group A%'
  AND is_final = false;

-- Group B: Late Clinical (Phase 2/3) (4개)
UPDATE golden_seed_items
SET is_final = true, 
    is_failed_adc = false,
    golden_group = 'clinical_late', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group B%'
  AND is_final = false;

-- Group C: Early Clinical (Phase 1) (1개)
UPDATE golden_seed_items
SET is_final = true, 
    is_failed_adc = false,
    golden_group = 'clinical_early', 
    gate_status = 'final',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group C%'
  AND is_final = false;

-- Group D: Failed ADC (2개) - 실패 학습용
UPDATE golden_seed_items
SET is_failed_adc = true,
    is_final = false,
    golden_group = 'failed', 
    gate_status = 'failed_learning',
    is_adc_confirmed = true,
    adc_classification = 'adc_confident'
WHERE portfolio_group LIKE 'Group D%';

