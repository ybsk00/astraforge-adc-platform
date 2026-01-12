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
export async function getGoldenSets() {
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('golden_sets')
        .select(`
            *,
            candidates:golden_candidates(count)
        `)
        .order('created_at', { ascending: false });

    if (error) {
        console.error("Failed to fetch golden sets:", error);
        throw new Error("Failed to fetch golden sets");
    }

    return data.map((item: any) => ({
        ...item,
        candidate_count: item.candidates?.[0]?.count || 0
    }));
}

/**
 * Fetch a single Golden Set with Candidates
 */
export async function getGoldenSetById(id: string) {
    const supabase = await createClient();

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
        .order('score', { ascending: false });

    if (candidateError) throw candidateError;

    return {
        ...(setInfo as GoldenSet),
        candidates: candidates as GoldenCandidate[]
    };
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
