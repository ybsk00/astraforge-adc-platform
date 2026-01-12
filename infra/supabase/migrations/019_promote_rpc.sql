-- Atomic Function to Promote Golden Set to Seed Set
CREATE OR REPLACE FUNCTION public.promote_golden_set(
    p_golden_set_id uuid,
    p_seed_set_name text
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
    v_seed_set_id uuid;
    v_candidate RECORD;
    v_target_id uuid;
    v_linker_id uuid;
    v_payload_id uuid;
    v_inserted_targets int := 0;
    v_inserted_linkers int := 0;
    v_inserted_payloads int := 0;
    v_linked_count int := 0;
BEGIN
    -- 1. Check idempotency (Already promoted?)
    IF EXISTS (SELECT 1 FROM public.seed_sets WHERE source_golden_set_id = p_golden_set_id) THEN
        RAISE EXCEPTION 'This Golden Set has already been promoted.';
    END IF;

    -- 2. Create Seed Set
    INSERT INTO public.seed_sets (seed_set_name, source_golden_set_id, status)
    VALUES (p_seed_set_name, p_golden_set_id, 'active')
    RETURNING id INTO v_seed_set_id;

    -- 3. Iterate over APPROVED candidates
    FOR v_candidate IN 
        SELECT * FROM public.golden_candidates 
        WHERE golden_set_id = p_golden_set_id 
        AND review_status = 'approved'
    LOOP
        -- A. Upsert Target
        -- Assuming entity_targets has unique constraint on gene_symbol
        INSERT INTO public.entity_targets (gene_symbol, name, type)
        VALUES (v_candidate.target, v_candidate.target, 'protein')
        ON CONFLICT (gene_symbol) DO UPDATE SET updated_at = now()
        RETURNING id INTO v_target_id;
        
        -- If no row returned (because of DO NOTHING or similar), fetch it
        IF v_target_id IS NULL THEN
            SELECT id INTO v_target_id FROM public.entity_targets WHERE gene_symbol = v_candidate.target;
        ELSE
            v_inserted_targets := v_inserted_targets + 1;
        END IF;

        -- Link Target to Seed Set
        INSERT INTO public.seed_set_targets (seed_set_id, target_id)
        VALUES (v_seed_set_id, v_target_id)
        ON CONFLICT DO NOTHING;


        -- B. Upsert Linker
        -- Assuming entity_linkers has unique constraint on name
        INSERT INTO public.entity_linkers (name)
        VALUES (v_candidate.linker)
        ON CONFLICT (name) DO UPDATE SET updated_at = now()
        RETURNING id INTO v_linker_id;

        IF v_linker_id IS NULL THEN
            SELECT id INTO v_linker_id FROM public.entity_linkers WHERE name = v_candidate.linker;
        ELSE
            v_inserted_linkers := v_inserted_linkers + 1;
        END IF;

        -- Link Linker to Seed Set
        INSERT INTO public.seed_set_linkers (seed_set_id, linker_id)
        VALUES (v_seed_set_id, v_linker_id)
        ON CONFLICT DO NOTHING;


        -- C. Upsert Payload (Drug)
        -- Assuming entity_drugs has unique constraint on drug_name
        INSERT INTO public.entity_drugs (drug_name, drug_role)
        VALUES (v_candidate.payload, 'payload')
        ON CONFLICT (drug_name) DO UPDATE SET updated_at = now()
        RETURNING id INTO v_payload_id;

        IF v_payload_id IS NULL THEN
            SELECT id INTO v_payload_id FROM public.entity_drugs WHERE drug_name = v_candidate.payload;
        ELSE
            v_inserted_payloads := v_inserted_payloads + 1;
        END IF;

        -- Link Payload to Seed Set
        INSERT INTO public.seed_set_payloads (seed_set_id, drug_id)
        VALUES (v_seed_set_id, v_payload_id)
        ON CONFLICT DO NOTHING;
        
        v_linked_count := v_linked_count + 1;
    END LOOP;

    -- 4. Update Golden Set Status
    UPDATE public.golden_sets
    SET status = 'promoted'
    WHERE id = p_golden_set_id;

    -- 5. Return Summary
    RETURN jsonb_build_object(
        'seed_set_id', v_seed_set_id,
        'candidates_processed', v_linked_count,
        'new_targets', v_inserted_targets,
        'new_linkers', v_inserted_linkers,
        'new_payloads', v_inserted_payloads
    );
END;
$$;
