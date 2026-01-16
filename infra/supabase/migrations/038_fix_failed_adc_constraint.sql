-- Migration: Fix Failed ADC constraint and promote to final
-- Author: Antigravity
-- Date: 2026-01-16
-- Description: Remove exclusive constraint, allow failed ADCs to have is_final=true

-- 1. Remove the exclusive constraint (if exists)
ALTER TABLE golden_seed_items
DROP CONSTRAINT IF EXISTS chk_final_vs_failed;

-- 2. Update failed ADCs to have is_final = true (so they only appear in Final tab)
UPDATE golden_seed_items
SET is_final = true
WHERE is_failed_adc = true
  AND is_final = false;

-- 3. Verify
SELECT drug_name_canonical, golden_group, is_final, is_failed_adc
FROM golden_seed_items
WHERE golden_group = 'failed';
