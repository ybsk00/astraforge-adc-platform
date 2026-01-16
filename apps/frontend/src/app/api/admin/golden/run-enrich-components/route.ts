import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';
import { calculateAdcScore } from '@/lib/adc-scoring';
import { SupabaseClient } from '@supabase/supabase-js';

// Target 동의어 사전 (HGNC 기반)
const TARGET_SYNONYMS: Record<string, string> = {
    'her2': 'ERBB2', 'erbb2': 'ERBB2', 'neu': 'ERBB2', 'cd340': 'ERBB2',
    'trop2': 'TACSTD2', 'tacstd2': 'TACSTD2',
    'nectin4': 'NECTIN4', 'nectin-4': 'NECTIN4', 'pvrl4': 'NECTIN4',
    'cd30': 'TNFRSF8', 'tnfrsf8': 'TNFRSF8',
    'cd19': 'CD19', 'cd22': 'CD22', 'cd33': 'CD33',
    'cd79b': 'CD79B', 'bcma': 'TNFRSF17', 'tnfrsf17': 'TNFRSF17',
    'her3': 'ERBB3', 'erbb3': 'ERBB3',
    'egfr': 'EGFR', 'her1': 'EGFR',
    'met': 'MET', 'c-met': 'MET',
    'folr1': 'FOLR1', 'fra': 'FOLR1', 'folate receptor': 'FOLR1'
};

// Payload 사전
const PAYLOAD_DICTIONARY: Record<string, string> = {
    'mmae': 'MMAE', 'vedotin': 'MMAE', 'auristatin e': 'MMAE',
    'mmaf': 'MMAF', 'mafodotin': 'MMAF', 'auristatin f': 'MMAF',
    'dm1': 'DM1', 'emtansine': 'DM1', 'mertansine': 'DM1',
    'dm4': 'DM4', 'ravtansine': 'DM4', 'soravtansine': 'DM4',
    'dxd': 'DXd', 'deruxtecan': 'DXd', 'exatecan derivative': 'DXd',
    'sn-38': 'SN-38', 'sn38': 'SN-38', 'govitecan': 'SN-38',
    'calicheamicin': 'Calicheamicin', 'ozogamicin': 'Calicheamicin',
    'pbd': 'PBD', 'tesirine': 'PBD', 'talirine': 'PBD'
};

// Linker 사전
const LINKER_DICTIONARY: Record<string, string> = {
    'vc': 'VC', 'val-cit': 'VC', 'valine-citrulline': 'VC',
    'mc-vc-pabc': 'MC-VC-PABC', 'vc-pab': 'VC-PAB',
    'ggfg': 'GGFG',
    'smcc': 'SMCC', 'mcc': 'MCC',
    'spdb': 'SPDB', 'disulfide': 'Disulfide',
    'hydrazone': 'Hydrazone'
};

interface Candidate {
    id: string;
    drug_name: string;
    summary_raw: string;
    interventions_raw?: string[];
    target: string | null;
    adc_classification?: string;
    adc_score?: number;
    adc_reason?: string;
    approval_status?: string;
    evidence_refs?: any[];
}

/**
 * Step 2: 표적/링커/페이로드 채우기
 * 구성요소 추출 + resolve_ids → Review Queue에 제안 적재
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const candidateIds = body.candidate_ids || [];
        const processAll = body.process_all || false;

        const supabase = await createClient();

        // 대상 후보 조회
        let query = supabase
            .from('golden_candidates')
            .select('*');

        if (!processAll && candidateIds.length > 0) {
            query = query.in('id', candidateIds);
        } else if (!processAll) {
            // 최근 100개만 처리
            query = query.order('created_at', { ascending: false }).limit(100);
        }

        const { data: candidates, error } = await query;

        if (error) throw error;
        if (!candidates?.length) {
            return NextResponse.json({
                status: 'ok',
                proposals_created: 0,
                skipped_not_adc: 0,
                message: 'No candidates to process'
            });
        }

        let proposalsCreated = 0;
        let skippedNotAdc = 0;

        for (const candidate of candidates) {
            // 1. 구성요소 추출
            const extracted = extractComponents(candidate);

            // 2. Target 표준화
            const resolvedTarget = resolveTarget(extracted.target || candidate.target);

            // 3. Payload 표준화
            const resolvedPayload = resolvePayload(extracted.payload);

            // 4. Linker 표준화
            const resolvedLinker = resolveLinker(extracted.linker);

            // 4.5. ADC 분류
            const adcResult = candidate.adc_classification
                ? { score: candidate.adc_score || 0, classification: candidate.adc_classification, reason: candidate.adc_reason }
                : calculateAdcScore([candidate.drug_name, candidate.summary_raw].join(' '));

            // not_adc 인 경우 스킵
            if (adcResult.classification === 'not_adc') {
                skippedNotAdc++;
                continue;
            }

            // 5. Seed Item 존재 여부 확인 (이미 Import된 경우)
            const { data: existingSeed } = await supabase
                .from('golden_seed_items')
                .select('id, is_manually_verified')
                .eq('source_candidate_id', candidate.id)
                .maybeSingle();

            if (existingSeed) {
                // 이미 Seed가 있는 경우 → Review Queue에 제안
                if (existingSeed.is_manually_verified) {
                    // Verified된 경우 → 절대 overwrite 금지, Review Queue에만 적재
                    await createReviewProposal(supabase, existingSeed.id, {
                        resolved_target_symbol: resolvedTarget,
                        payload_family: resolvedPayload.family,
                        payload_exact_name: resolvedPayload.name,
                        linker_family: resolvedLinker.family
                    }, 'enrich_components_job');
                    proposalsCreated++;
                } else {
                    // 비Verified → Review Queue에 제안 (Overwrite 가능하지만 승인 필요)
                    await createReviewProposal(supabase, existingSeed.id, {
                        resolved_target_symbol: resolvedTarget,
                        payload_family: resolvedPayload.family,
                        payload_exact_name: resolvedPayload.name,
                        linker_family: resolvedLinker.family
                    }, 'enrich_components_job');
                    proposalsCreated++;
                }
            } else {
                // Seed가 없는 경우 → 새 Seed 생성 + Review Queue
                const { data: newSeed } = await supabase
                    .from('golden_seed_items')
                    .insert({
                        source_candidate_id: candidate.id,
                        drug_name_canonical: candidate.drug_name,
                        target: candidate.target || 'Unknown',
                        resolved_target_symbol: resolvedTarget,
                        antibody: extracted.antibody,
                        linker_family: resolvedLinker.family,
                        payload_family: resolvedPayload.family,
                        payload_exact_name: resolvedPayload.name,
                        clinical_phase: candidate.approval_status,
                        evidence_refs: candidate.evidence_refs || [],
                        gate_status: 'needs_review',
                        adc_score: adcResult.score,
                        adc_classification: adcResult.classification,
                        adc_reason: adcResult.reason
                    })
                    .select()
                    .single();

                if (newSeed) {
                    // Review Queue에 "새 Seed 생성됨" 알림
                    await createReviewProposal(supabase, newSeed.id, {
                        _action: 'new_seed_created',
                        source_candidate_id: candidate.id
                    }, 'import_from_candidates');
                    proposalsCreated++;
                }
            }
        }

        return NextResponse.json({
            status: 'ok',
            processed: candidates.length,
            proposals_created: proposalsCreated,
            skipped_not_adc: skippedNotAdc
        });

    } catch (error: unknown) {
        console.error('Step 2 API error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        return NextResponse.json(
            { status: 'error', detail: errorMessage },
            { status: 500 }
        );
    }
}

/**
 * 후보에서 구성요소 추출
 */
function extractComponents(candidate: Candidate): {
    target: string | null;
    antibody: string | null;
    linker: string | null;
    payload: string | null;
} {
    const text = [
        candidate.drug_name,
        candidate.summary_raw,
        JSON.stringify(candidate.interventions_raw || [])
    ].join(' ').toLowerCase();

    return {
        target: extractFromText(text, Object.keys(TARGET_SYNONYMS)),
        antibody: extractAntibodyName(text),
        linker: extractFromText(text, Object.keys(LINKER_DICTIONARY)),
        payload: extractFromText(text, Object.keys(PAYLOAD_DICTIONARY))
    };
}

function extractFromText(text: string, keywords: string[]): string | null {
    for (const kw of keywords) {
        if (text.includes(kw.toLowerCase())) return kw;
    }
    return null;
}

function extractAntibodyName(text: string): string | null {
    const match = text.match(/([a-z]+(?:tu|zu|xi|mu)mab)/i);
    return match ? match[1] : null;
}

function resolveTarget(rawTarget: string | null): string | null {
    if (!rawTarget) return null;
    return TARGET_SYNONYMS[rawTarget.toLowerCase()] || rawTarget.toUpperCase();
}

function resolvePayload(rawPayload: string | null): { family: string | null; name: string | null } {
    if (!rawPayload) return { family: null, name: null };
    const resolved = PAYLOAD_DICTIONARY[rawPayload.toLowerCase()];
    return {
        family: resolved || null,
        name: resolved || rawPayload
    };
}

function resolveLinker(rawLinker: string | null): { family: string | null } {
    if (!rawLinker) return { family: null };
    return {
        family: LINKER_DICTIONARY[rawLinker.toLowerCase()] || rawLinker
    };
}

/**
 * Review Queue에 제안 생성
 */
async function createReviewProposal(
    supabase: SupabaseClient,
    seedItemId: string,
    proposedChanges: Record<string, unknown>,
    jobName: string
) {
    // Diff 형식으로 변환
    const proposedPatch: Record<string, { old: unknown; new: unknown; source: string }> = {};

    for (const [field, newValue] of Object.entries(proposedChanges)) {
        if (newValue !== null && newValue !== undefined) {
            proposedPatch[field] = {
                old: null, // 실제 구현에서는 기존값 조회
                new: newValue,
                source: jobName
            };
        }
    }

    await supabase.from('golden_review_queue').insert({
        seed_item_id: seedItemId,
        queue_type: 'enrichment_update',
        entity_type: 'seed_item',
        proposed_patch: proposedPatch,
        confidence: 0.7,
        status: 'pending'
    });
}
