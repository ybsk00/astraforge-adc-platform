-- Populate connectors table with default values from registry
INSERT INTO public.connectors (name, type, config, is_active)
VALUES 
    ('pubmed', 'api', '{}', true),
    ('uniprot', 'api', '{}', true),
    ('opentargets', 'api', '{}', true),
    ('hpa', 'db', '{}', true),
    ('chembl', 'db', '{}', true),
    ('pubchem', 'db', '{}', true),
    ('clinicaltrials', 'api', '{}', true),
    ('openfda', 'api', '{}', true),
    ('seed', 'system', '{}', true),
    ('resolve', 'system', '{}', true)
ON CONFLICT (name) DO UPDATE SET
    is_active = EXCLUDED.is_active;
