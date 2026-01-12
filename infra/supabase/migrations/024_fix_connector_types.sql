-- Fix connector types
-- ClinicalTrials.gov and openFDA are APIs, not DBs
-- Seed Data and Resolve IDs are System tasks

UPDATE connectors
SET type = 'api'
WHERE name IN ('ClinicalTrials.gov', 'openFDA');

UPDATE connectors
SET type = 'system'
WHERE name IN ('Seed Data', 'Resolve IDs');

-- Ensure others are correct
UPDATE connectors SET type = 'api' WHERE name IN ('PubMed', 'UniProt', 'Open Targets');
UPDATE connectors SET type = 'db' WHERE name IN ('Human Protein Atlas', 'ChEMBL', 'PubChem');
