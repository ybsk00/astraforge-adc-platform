"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";

export interface GoldenSet {
    id: string;
    name: string;
    version: string;
    status: string;
    created_at: string;
    candidate_count?: number;
}

export interface GoldenCandidate {
    id: string;
    drug_name: string;
    target: string;
    antibody: string;
    payload: string;
    linker: string;
    score: number;
    review_status: 'pending' | 'approved' | 'rejected';
    review_notes?: string;
    evidence_json?: any;
}

/**
 * Fetch all Golden Sets
 */
export async function getGoldenSets(page: number = 1, limit: number = 20) {
    const supabase = await createClient();
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await supabase
        .from('golden_sets')
        .select(`
            *,
            candidates:golden_candidates(count)
        `, { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(from, to);

    if (error) {
        console.error("Failed to fetch golden sets:", error);
        throw new Error("Failed to fetch golden sets");
    }

    return {
        data: data.map((item: any) => ({
            ...item,
            candidate_count: item.candidates?.[0]?.count || 0
        })),
        count: count || 0
    };
}

/**
 * Fetch a single Golden Set with Candidates
 */
export async function getGoldenSetById(id: string) {
    const supabase = await createClient();

    try {
        // 1. Fetch Golden Set Info
        const { data: setInfo, error: setError } = await supabase
            .from('golden_sets')
            .select('*')
            .eq('id', id)
            .single();

        if (setError) throw setError;

        // 2. Fetch Candidates
        const { data: candidates, error: candidateError } = await supabase
            .from('golden_candidates')
            .select('*')
            .eq('golden_set_id', id)
            .order('confidence_score', { ascending: false });

        if (candidateError) throw candidateError;

        return {
            ...setInfo,
            candidates: candidates?.map(c => ({
                ...c,
                score: c.confidence_score // Map for frontend compatibility
            })) || []
        };
    } catch (error) {
        console.error('Failed to fetch golden set:', error);
        return null;
    }
}

/**
 * Update Candidate Review Status
 */
export async function updateCandidateReviewStatus(
    candidateId: string,
    status: 'approved' | 'rejected' | 'pending',
    notes?: string
) {
    const supabase = await createClient();

    const updateData: any = { review_status: status };
    if (notes !== undefined) updateData.review_notes = notes;

    const { error } = await supabase
        .from('golden_candidates')
        .update(updateData)
        .eq('id', candidateId);

    if (error) throw error;

    revalidatePath('/admin/golden-sets');
}

/**
 * Promote Golden Set to Seed Set (RPC Call)
 */
export async function promoteGoldenSet(goldenSetId: string, seedSetName: string) {
    const supabase = await createClient();

    const { data, error } = await supabase
        .rpc('promote_golden_set', {
            p_golden_set_id: goldenSetId,
            p_seed_set_name: seedSetName
        });

    if (error) {
        console.error("Promotion failed:", error);
        throw new Error(error.message);
    }

    revalidatePath('/admin/golden-sets');
    revalidatePath('/admin/seeds');

    return data;
}

/**
 * Fetch Evidence for a Candidate
 */
export async function getGoldenCandidateEvidence(candidateId: string) {
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('golden_candidate_evidence')
        .select('*')
        .eq('candidate_id', candidateId)
        .order('created_at', { ascending: false });

    if (error) {
        console.error("Failed to fetch evidence:", error);
        return [];
    }

    return data;
}


/**
 * Delete Golden Set
 */
export async function deleteGoldenSet(id: string) {
    const supabase = await createClient();

    const { error } = await supabase
        .from('golden_sets')
        .delete()
        .eq('id', id);

    if (error) {
        console.error("Failed to delete golden set:", error);
        throw new Error("Failed to delete golden set");
    }

    revalidatePath('/admin/golden-sets');
}

/**
 * Fetch Promoted Golden Sets (Final)
 */
/**
 * Get Final (Promoted) Seeds for Dashboard
 * Now queries golden_seed_items with is_final=true
 */
export async function getPromotedGoldenSets(limit: number = 10) {
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('golden_seed_items')
        .select(`
            id,
            drug_name_canonical,
            resolved_target_symbol,
            payload_family,
            clinical_phase,
            outcome_label,
            is_final,
            updated_at
        `)
        .eq('is_final', true)
        .order('updated_at', { ascending: false })
        .limit(limit);

    if (error) {
        console.error("Failed to fetch promoted golden sets:", error);
        return [];
    }

    return data || [];
}

/**
 * Update Golden Candidate fields
 */
export async function updateGoldenCandidate(
    candidateId: string,
    data: {
        target?: string;
        antibody?: string;
        linker?: string;
        payload?: string;
        drug_name?: string;
    }
) {
    const supabase = await createClient();

    const updateData: Record<string, any> = {};
    if (data.target !== undefined) updateData.target = data.target;
    if (data.antibody !== undefined) updateData.antibody = data.antibody;
    if (data.linker !== undefined) updateData.linker = data.linker;
    if (data.payload !== undefined) updateData.payload = data.payload;
    if (data.drug_name !== undefined) updateData.drug_name = data.drug_name;
    updateData.updated_at = new Date().toISOString();

    const { error } = await supabase
        .from('golden_candidates')
        .update(updateData)
        .eq('id', candidateId);

    if (error) {
        console.error("Failed to update candidate:", error);
        throw new Error("Failed to update candidate");
    }

    revalidatePath('/admin/golden-sets');
}

/**
 * Search Component Catalog for RAG-like lookup
 */
export async function searchComponentCatalog(
    query: string,
    type?: 'target' | 'antibody' | 'linker' | 'payload'
) {
    const supabase = await createClient();

    let queryBuilder = supabase
        .from('component_catalog')
        .select('id, name, type, synonyms')
        .ilike('name', `%${query}%`)
        .limit(20);

    if (type) {
        queryBuilder = queryBuilder.eq('type', type);
    }

    const { data, error } = await queryBuilder;

    if (error) {
        console.error("Failed to search catalog:", error);
        return [];
    }

    return data || [];
}

// ============================================
// Manual Seed (golden_seed_items) Actions
// ============================================

export interface ManualSeed {
    id: string;
    source_candidate_id?: string;
    drug_name_canonical: string;
    aliases?: string;
    portfolio_group?: string;
    target: string;
    resolved_target_symbol?: string;
    antibody?: string;
    linker_family?: string;
    linker_trigger?: string;
    payload_family?: string;
    payload_exact_name?: string;
    payload_smiles_raw?: string;
    payload_smiles_standardized?: string;
    proxy_smiles_flag: boolean;
    proxy_reference?: string;
    clinical_phase?: string;
    program_status?: string;
    clinical_nct_id_primary?: string;
    outcome_label?: string;
    key_risk_category?: string;
    key_risk_signal?: string;
    primary_source_type?: string;
    primary_source_id?: string;
    evidence_refs: any[];
    gate_status: string;
    is_final: boolean;
    is_manually_verified: boolean;
    created_at: string;
    updated_at: string;
}

/**
 * Fetch Manual Seeds (golden_seed_items) with pagination and filters
 */
export async function getManualSeeds(
    page: number = 1,
    limit: number = 20,
    filters?: {
        gateStatus?: string;
        target?: string;
        isFinal?: boolean;
    }
) {
    const supabase = await createClient();
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    let query = supabase
        .from('golden_seed_items')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(from, to);

    if (filters?.gateStatus) {
        query = query.eq('gate_status', filters.gateStatus);
    }
    if (filters?.target) {
        query = query.ilike('target', `%${filters.target}%`);
    }
    if (filters?.isFinal !== undefined) {
        query = query.eq('is_final', filters.isFinal);
    }

    const { data, error, count } = await query;

    if (error) {
        console.error("Failed to fetch manual seeds:", error);
        throw new Error("Failed to fetch manual seeds");
    }

    return { data: data || [], count: count || 0 };
}

/**
 * Fetch a single Manual Seed by ID
 */
export async function getManualSeedById(id: string) {
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('golden_seed_items')
        .select('*')
        .eq('id', id)
        .single();

    if (error) {
        console.error("Failed to fetch manual seed:", error);
        return null;
    }

    return data;
}

/**
 * Update Manual Seed
 */
export async function updateManualSeed(
    id: string,
    data: Partial<ManualSeed>
) {
    const supabase = await createClient();

    // Remove read-only fields
    const { id: _, created_at, updated_at, ...updateData } = data as any;

    const { error } = await supabase
        .from('golden_seed_items')
        .update(updateData)
        .eq('id', id);

    if (error) {
        console.error("Failed to update manual seed:", error);
        throw new Error("Failed to update manual seed");
    }

    revalidatePath('/admin/golden-sets');
}

/**
 * Import Candidate from Auto (golden_candidates) to Manual (golden_seed_items)
 */
export async function importCandidateToManual(candidateId: string) {
    const supabase = await createClient();

    // 1. Fetch the candidate
    const { data: candidate, error: fetchError } = await supabase
        .from('golden_candidates')
        .select('*')
        .eq('id', candidateId)
        .single();

    if (fetchError || !candidate) {
        throw new Error("Candidate not found");
    }

    // 2. Check for duplicate
    const { data: existing } = await supabase
        .from('golden_seed_items')
        .select('id')
        .eq('drug_name_canonical', candidate.drug_name)
        .single();

    if (existing) {
        throw new Error(`Duplicate: ${candidate.drug_name} already exists in Manual seeds`);
    }

    // 3. Map fields from Auto to Manual
    const manualSeed = {
        source_candidate_id: candidateId,
        drug_name_canonical: candidate.drug_name,
        target: candidate.target || 'Unknown',
        antibody: candidate.antibody,
        linker_family: candidate.linker,
        payload_family: candidate.payload,
        primary_source_type: "Clinical Trial",
        primary_source_id: candidate.source_ref,
        clinical_phase: candidate.approval_status,
        gate_status: 'needs_review',  // Import always starts as needs_review
        is_final: false,
        evidence_refs: candidate.evidence_json ? [candidate.evidence_json] : [],
    };

    // 4. Insert to golden_seed_items
    const { error: insertError } = await supabase
        .from('golden_seed_items')
        .insert(manualSeed);

    if (insertError) {
        console.error("Failed to import candidate:", insertError);
        throw new Error("Failed to import candidate to manual seed");
    }

    revalidatePath('/admin/golden-sets');
    return { success: true, drugName: candidate.drug_name };
}

/**
 * Check if import would be duplicate
 */
export async function checkDuplicateImport(drugName: string) {
    const supabase = await createClient();

    const { data } = await supabase
        .from('golden_seed_items')
        .select('id, drug_name_canonical')
        .eq('drug_name_canonical', drugName)
        .single();

    return { isDuplicate: !!data, existingId: data?.id };
}

/**
 * Promote Manual Seed to Final (Option C Policy: NCT Optional)
 * 
 * Gate-1: Target Resolved (resolved_target_symbol)
 * Gate-2: SMILES Ready (payload_smiles_standardized OR proxy_smiles_flag)
 * Gate-3: Evidence Exists (evidence_refs >= 1)
 */
export async function promoteToFinal(id: string, userId?: string) {
    const supabase = await createClient();

    // 1. Fetch the seed
    const { data: seed, error: fetchError } = await supabase
        .from('golden_seed_items')
        .select('*')
        .eq('id', id)
        .single();

    if (fetchError || !seed) {
        throw new Error("Seed not found");
    }

    // 2. Check gate conditions (Option C: 3 required conditions)
    const gateChecks = {
        targetResolved: !!seed.resolved_target_symbol && seed.resolved_target_symbol !== '',
        smilesReady: !!seed.payload_smiles_standardized || seed.proxy_smiles_flag === true,
        evidenceExists: Array.isArray(seed.evidence_refs) && seed.evidence_refs.length >= 1,
        // Optional fields (not required for promotion)
        nctSelected: !!seed.clinical_nct_id_primary,
        rdkitComputed: seed.rdkit_mw !== null,
    };

    // Option C: Only 3 required gates (NCT is optional)
    const requiredChecks = [
        gateChecks.targetResolved,
        gateChecks.smilesReady,
        gateChecks.evidenceExists,
    ];

    const passedCount = requiredChecks.filter(Boolean).length;
    const allPassed = requiredChecks.every(Boolean);

    if (!allPassed) {
        throw new Error(`Gate conditions not met (${passedCount}/${requiredChecks.length}). Please fill required fields.`);
    }

    // 3. Promote
    const { error: updateError } = await supabase
        .from('golden_seed_items')
        .update({
            is_final: true,
            gate_status: 'final',
            is_manually_verified: true,
            finalized_by: userId || 'admin',
            finalized_at: new Date().toISOString(),
        })
        .eq('id', id);

    if (updateError) {
        console.error("Failed to promote seed:", updateError);
        throw new Error("Failed to promote seed to final");
    }

    revalidatePath('/admin/golden-sets');
    return { success: true, gateChecks };
}

/**
 * Get Auto Candidates (golden_candidates) for Tab 1
 */
export async function getAutoCandidates(
    page: number = 1,
    limit: number = 20,
    filters?: {
        target?: string;
        reviewStatus?: string;
    }
) {
    const supabase = await createClient();
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    let query = supabase
        .from('golden_candidates')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(from, to);

    if (filters?.target) {
        query = query.ilike('target', `%${filters.target}%`);
    }
    if (filters?.reviewStatus) {
        query = query.eq('review_status', filters.reviewStatus);
    }

    const { data, error, count } = await query;

    if (error) {
        console.error("Failed to fetch auto candidates:", error);
        throw new Error("Failed to fetch auto candidates");
    }

    return { data: data || [], count: count || 0 };
}

// ============================================
// Review Queue (golden_review_queue) Actions
// ============================================

export interface ReviewQueueItem {
    id: string;
    seed_item_id: string;
    change_type: string;
    field_name: string;
    old_value: string | null;
    new_value: string | null;
    proposed_patch: Record<string, any> | null;
    status: 'pending' | 'approved' | 'rejected';
    reviewer_comment?: string;
    source_job?: string;
    created_at: string;
    reviewed_at?: string;
    // Join fields
    seed_item?: {
        drug_name_canonical: string;
        target: string;
    };
}

/**
 * Get Review Queue items (pending by default)
 */
export async function getReviewQueue(
    page: number = 1,
    limit: number = 50,
    status: 'pending' | 'approved' | 'rejected' | 'all' = 'pending'
) {
    const supabase = await createClient();
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    let query = supabase
        .from('golden_review_queue')
        .select(`
            *,
            seed_item:golden_seed_items(drug_name_canonical, target)
        `, { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(from, to);

    if (status !== 'all') {
        query = query.eq('status', status);
    }

    const { data, error, count } = await query;

    if (error) {
        console.error("Failed to fetch review queue:", error);
        throw new Error("Failed to fetch review queue");
    }

    return { data: data || [], count: count || 0 };
}

/**
 * Approve a Review Queue item
 */
export async function approveReviewItem(id: string, comment?: string) {
    const supabase = await createClient();

    // 1. Fetch the review item
    const { data: item, error: fetchError } = await supabase
        .from('golden_review_queue')
        .select('*')
        .eq('id', id)
        .single();

    if (fetchError || !item) {
        throw new Error("Review item not found");
    }

    // 2. Apply the proposed patch to the seed item
    if (item.proposed_patch && item.seed_item_id) {
        const { error: patchError } = await supabase
            .from('golden_seed_items')
            .update(item.proposed_patch)
            .eq('id', item.seed_item_id);

        if (patchError) {
            console.error("Failed to apply patch:", patchError);
            throw new Error("Failed to apply changes");
        }
    }

    // 3. Mark the review item as approved
    const { error: updateError } = await supabase
        .from('golden_review_queue')
        .update({
            status: 'approved',
            reviewer_comment: comment,
            reviewed_at: new Date().toISOString(),
        })
        .eq('id', id);

    if (updateError) {
        throw new Error("Failed to update review status");
    }

    revalidatePath('/admin/golden-sets');
    return { success: true };
}

/**
 * Reject a Review Queue item
 */
export async function rejectReviewItem(id: string, comment?: string) {
    const supabase = await createClient();

    const { error } = await supabase
        .from('golden_review_queue')
        .update({
            status: 'rejected',
            reviewer_comment: comment,
            reviewed_at: new Date().toISOString(),
        })
        .eq('id', id);

    if (error) {
        throw new Error("Failed to reject review item");
    }

    revalidatePath('/admin/golden-sets');
    return { success: true };
}

// ============================================
// Pipeline Step Runners
// ============================================

/**
 * Run Step 1: Collect candidates from ClinicalTrials
 */
export async function runPipelineStep1(cancerType: string, targets: string[], limit: number = 50) {
    const response = await fetch('/api/admin/golden/run-candidates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cancerType, targets, limit }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to run Step 1');
    }

    revalidatePath('/admin/golden-sets');
    return response.json();
}

/**
 * Run Step 2: Enrich components (target, linker, payload)
 */
export async function runPipelineStep2(seedIds?: string[]) {
    const response = await fetch('/api/admin/golden/run-enrich-components', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seedIds }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to run Step 2');
    }

    revalidatePath('/admin/golden-sets');
    return response.json();
}

/**
 * Run Step 3: Enrich chemistry (SMILES, Antibody Identity)
 */
export async function runPipelineStep3(seedIds?: string[]) {
    const response = await fetch('/api/admin/golden/run-enrich-chemistry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seedIds }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to run Step 3');
    }

    revalidatePath('/admin/golden-sets');
    return response.json();
}

/**
 * Run Step 4: Promote approved seeds to final
 */
export async function runPipelineStep4(seedIds?: string[]) {
    const response = await fetch('/api/admin/golden/promote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seedIds }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to run Step 4');
    }

    revalidatePath('/admin/golden-sets');
    return response.json();
}
