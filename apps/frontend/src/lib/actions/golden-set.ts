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
        export async function getPromotedGoldenSets(limit: number = 10) {
            const supabase = await createClient();

            const { data, error } = await supabase
                .from('golden_sets')
                .select(`
            id,
            name,
            version,
            created_at,
            candidates:golden_candidates(count)
        `)
                .eq('status', 'promoted')
                .order('created_at', { ascending: false })
                .limit(limit);

            if (error) {
                console.error("Failed to fetch promoted golden sets:", error);
                return [];
            }

            return data.map((item: any) => ({
                ...item,
                candidate_count: item.candidates?.[0]?.count || 0
            }));
        }
