-- ================================================
-- Quick Fix: Add simple unique constraints for ON CONFLICT
-- Run this after schema.sql
-- ================================================

-- 1. raw_source_records: Add simple (source, external_id) constraint
-- First drop existing if needed, then recreate
DO $$
BEGIN
    -- Try to add constraint, ignore if already exists
    ALTER TABLE raw_source_records 
    ADD CONSTRAINT raw_source_records_source_external_id_key 
    UNIQUE (source, external_id);
EXCEPTION WHEN duplicate_table THEN
    NULL;
WHEN duplicate_object THEN
    NULL;
END $$;

-- 2. ingestion_cursors already has UNIQUE(source, query_hash) - should work

-- 3. target_profiles: ensure uniprot_id unique
DO $$
BEGIN
    ALTER TABLE target_profiles 
    ADD CONSTRAINT target_profiles_uniprot_id_key 
    UNIQUE (uniprot_id);
EXCEPTION WHEN duplicate_table THEN
    NULL;
WHEN duplicate_object THEN
    NULL;
END $$;

-- 4. compound_registry: ensure inchi_key unique  
DO $$
BEGIN
    ALTER TABLE compound_registry 
    ADD CONSTRAINT compound_registry_inchi_key_key 
    UNIQUE (inchi_key);
EXCEPTION WHEN duplicate_table THEN
    NULL;
WHEN duplicate_object THEN
    NULL;
END $$;

-- Verify constraints exist
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type 
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'UNIQUE' 
AND tc.table_name IN ('raw_source_records', 'ingestion_cursors', 'target_profiles', 'compound_registry')
ORDER BY tc.table_name;
