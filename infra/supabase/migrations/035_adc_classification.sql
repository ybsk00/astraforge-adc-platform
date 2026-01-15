-- Migration: ADC Classification Columns
-- Author: Antigravity
-- Date: 2026-01-15
-- Description: Add ADC scoring and classification columns for improved filtering

-- Add ADC classification columns to golden_seed_items
ALTER TABLE golden_seed_items 
ADD COLUMN IF NOT EXISTS adc_score INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS adc_classification TEXT DEFAULT 'not_scored'
    CHECK (adc_classification IN ('adc_confident', 'adc_possible', 'not_adc', 'not_scored')),
ADD COLUMN IF NOT EXISTS adc_reason JSONB,
ADD COLUMN IF NOT EXISTS is_adc_confirmed BOOLEAN DEFAULT FALSE;

-- Add ADC classification columns to golden_candidates
ALTER TABLE golden_candidates 
ADD COLUMN IF NOT EXISTS adc_score INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS adc_classification TEXT DEFAULT 'not_scored'
    CHECK (adc_classification IN ('adc_confident', 'adc_possible', 'not_adc', 'not_scored')),
ADD COLUMN IF NOT EXISTS adc_reason JSONB;

-- Index for fast filtering by classification
CREATE INDEX IF NOT EXISTS idx_seed_items_adc_classification 
ON golden_seed_items(adc_classification) WHERE adc_classification != 'not_scored';

CREATE INDEX IF NOT EXISTS idx_candidates_adc_classification 
ON golden_candidates(adc_classification) WHERE adc_classification != 'not_scored';

-- Comment on columns
COMMENT ON COLUMN golden_seed_items.adc_score IS 'ADC 스코어 (높을수록 ADC 확실)';
COMMENT ON COLUMN golden_seed_items.adc_classification IS 'ADC 분류: adc_confident, adc_possible, not_adc, not_scored';
COMMENT ON COLUMN golden_seed_items.adc_reason IS 'ADC 스코어링 근거 (매칭 키워드, 감점 사유)';
COMMENT ON COLUMN golden_seed_items.is_adc_confirmed IS 'Admin이 수동으로 ADC 확정';
