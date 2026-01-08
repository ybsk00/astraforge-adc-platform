-- ================================================
-- Migration: Refine Component Catalog Schema
-- Description: Add external IDs and flags for Domain Data Automation
-- ================================================

-- 1. Add new columns to component_catalog
ALTER TABLE component_catalog
ADD COLUMN IF NOT EXISTS gene_symbol TEXT,
ADD COLUMN IF NOT EXISTS uniprot_accession TEXT,
ADD COLUMN IF NOT EXISTS ensembl_gene_id TEXT,
ADD COLUMN IF NOT EXISTS inchikey TEXT,
ADD COLUMN IF NOT EXISTS pubchem_cid TEXT,
ADD COLUMN IF NOT EXISTS chembl_id TEXT,
ADD COLUMN IF NOT EXISTS is_gold BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 2. Update type check constraint to include 'adc_product'
ALTER TABLE component_catalog
DROP CONSTRAINT IF EXISTS component_catalog_type_check;

ALTER TABLE component_catalog
ADD CONSTRAINT component_catalog_type_check
CHECK (type IN ('target', 'antibody', 'linker', 'payload', 'conjugation', 'adc_product'));

-- 3. Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_component_catalog_gene_symbol ON component_catalog(gene_symbol);
CREATE INDEX IF NOT EXISTS idx_component_catalog_uniprot ON component_catalog(uniprot_accession);
CREATE INDEX IF NOT EXISTS idx_component_catalog_inchikey ON component_catalog(inchikey);
CREATE INDEX IF NOT EXISTS idx_component_catalog_is_gold ON component_catalog(is_gold);

-- 4. Add unique constraint for type + name to prevent duplicates
-- Note: We use COALESCE for workspace_id to handle both public (null) and private items if needed,
-- but for now let's just enforce unique name per type globally or per workspace.
-- Given the plan implies a global "Gold" set, we'll enforce uniqueness on (type, name) where workspace_id is null (public).
CREATE UNIQUE INDEX IF NOT EXISTS idx_component_catalog_unique_public 
ON component_catalog(type, name) 
WHERE workspace_id IS NULL;
