-- Fix connector types
-- ClinicalTrials.gov and openFDA are APIs, not DBs
-- Seed Data and Resolve IDs are System tasks

UPDATE connectors
SET type = 'api'
WHERE name IN ('clinicaltrials', 'openfda');

UPDATE connectors
SET type = 'system'
WHERE name IN ('seed', 'resolve');

-- Ensure others are correct
UPDATE connectors SET type = 'api' WHERE name IN ('pubmed', 'uniprot', 'opentargets');
UPDATE connectors SET type = 'db' WHERE name IN ('hpa', 'chembl', 'pubchem');
