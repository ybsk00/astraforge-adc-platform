import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * Step 3: SMILES/Identity 채우기 (확장)
 * - (A) Payload SMILES (PubChem + Proxy)
 * - (B) Linker SMILES (linker_library + PubChem)
 * - (C) Antibody Identity (DrugBank/UniProt)
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const seedIds = body.seed_ids || [];
        const mode = body.mode || 'all'; // 'payload' | 'linker' | 'antibody' | 'all'

        if (!seedIds.length) {
            return NextResponse.json(
                { detail: 'seed_ids is required' },
                { status: 400 }
            );
        }

        const supabase = await createClient();

        let smilesFound = 0;
        let proxyProposed = 0;
        let identityFound = 0;

        for (const seedId of seedIds) {
            // Seed 조회
            const { data: seed, error } = await supabase
                .from('golden_seed_items')
                .select('*')
                .eq('id', seedId)
                .single();

            if (error || !seed) continue;

            // Verified 체크
            if (seed.is_manually_verified) {
                // Verified된 경우 → Review Queue에만 제안
                // (아래 로직에서 자동 처리)
            }

            // (A) Payload SMILES
            if (mode === 'all' || mode === 'payload') {
                if (seed.payload_exact_name && !seed.payload_smiles_standardized) {
                    const payloadResult = await resolvePayloadSmiles(seed.payload_exact_name);

                    if (payloadResult.smiles) {
                        // Review Queue에 제안 (Verified 보호)
                        await createChemistryProposal(supabase, seedId, 'payload', {
                            payload_smiles_standardized: payloadResult.smiles,
                            payload_cid: payloadResult.cid,
                            is_proxy_payload: false
                        }, seed.is_manually_verified);
                        smilesFound++;
                    } else {
                        // Proxy 제안
                        await createChemistryProposal(supabase, seedId, 'payload_proxy', {
                            is_proxy_payload: true,
                            proxy_payload_reference: payloadResult.proxyCandidate || seed.payload_family,
                            proxy_payload_evidence_refs: [{
                                type: 'auto_suggestion',
                                note: `No exact SMILES found for ${seed.payload_exact_name}`,
                                suggested_proxy: payloadResult.proxyCandidate
                            }]
                        }, seed.is_manually_verified);
                        proxyProposed++;
                    }
                }
            }

            // (B) Linker SMILES
            if (mode === 'all' || mode === 'linker') {
                if (seed.linker_family && !seed.linker_smiles) {
                    const linkerResult = await resolveLinkerSmiles(supabase, seed.linker_family);

                    if (linkerResult.smiles) {
                        await createChemistryProposal(supabase, seedId, 'linker', {
                            linker_smiles: linkerResult.smiles,
                            linker_id_ref: linkerResult.linkerLibraryId,
                            is_proxy_linker: false
                        }, seed.is_manually_verified);
                        smilesFound++;
                    } else {
                        await createChemistryProposal(supabase, seedId, 'linker_proxy', {
                            is_proxy_linker: true,
                            proxy_linker_reference: linkerResult.suggestedProxy
                        }, seed.is_manually_verified);
                        proxyProposed++;
                    }
                }
            }

            // (C) Antibody Identity
            if (mode === 'all' || mode === 'antibody') {
                if (seed.antibody && !seed.antibody_name_canonical) {
                    const antibodyResult = await resolveAntibodyIdentity(seed.antibody, seed.drug_name_canonical);

                    if (antibodyResult.found) {
                        await createChemistryProposal(supabase, seedId, 'antibody', {
                            antibody_name_canonical: antibodyResult.name,
                            antibody_format: antibodyResult.format,
                            antibody_uniprot_id: antibodyResult.uniprotId,
                            antibody_drugbank_id: antibodyResult.drugbankId,
                            is_proxy_antibody: false
                        }, seed.is_manually_verified);
                        identityFound++;
                    }
                }
            }
        }

        return NextResponse.json({
            status: 'ok',
            processed: seedIds.length,
            smiles_found: smilesFound,
            proxy_proposed: proxyProposed,
            identity_found: identityFound
        });

    } catch (error: any) {
        console.error('Step 3 API error:', error);
        return NextResponse.json(
            { status: 'error', detail: error.message },
            { status: 500 }
        );
    }
}

/**
 * PubChem에서 SMILES 조회
 */
async function resolvePayloadSmiles(payloadName: string): Promise<{
    smiles: string | null;
    cid: string | null;
    proxyCandidate: string | null;
}> {
    try {
        const encodedName = encodeURIComponent(payloadName);
        const response = await fetch(
            `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodedName}/property/CanonicalSMILES/JSON`,
            { next: { revalidate: 86400 } } // 24시간 캐시
        );

        if (response.ok) {
            const data = await response.json();
            const props = data.PropertyTable?.Properties?.[0];
            if (props) {
                return {
                    smiles: props.CanonicalSMILES,
                    cid: String(props.CID),
                    proxyCandidate: null
                };
            }
        }
    } catch (error) {
        console.error('PubChem lookup failed:', error);
    }

    // Proxy 후보 제안 (동일 family 기반)
    const proxyMap: Record<string, string> = {
        'dxd': 'Exatecan (CID: 208903)',
        'mmae': 'Auristatin E (CID: 11542190)',
        'dm1': 'Maytansine (CID: 5281828)',
        'sn-38': 'SN-38 (CID: 104842)'
    };

    const lowerName = payloadName.toLowerCase();
    for (const [key, proxy] of Object.entries(proxyMap)) {
        if (lowerName.includes(key)) {
            return { smiles: null, cid: null, proxyCandidate: proxy };
        }
    }

    return { smiles: null, cid: null, proxyCandidate: null };
}

/**
 * Linker Library에서 SMILES 조회
 */
async function resolveLinkerSmiles(supabase: any, linkerFamily: string): Promise<{
    smiles: string | null;
    linkerLibraryId: string | null;
    suggestedProxy: string | null;
}> {
    // linker_library에서 검색
    const { data: linker } = await supabase
        .from('linker_library')
        .select('id, smiles, linker_name')
        .ilike('linker_name', `%${linkerFamily}%`)
        .maybeSingle();

    if (linker?.smiles) {
        return {
            smiles: linker.smiles,
            linkerLibraryId: linker.id,
            suggestedProxy: null
        };
    }

    // Family 매칭 시도
    const { data: familyMatch } = await supabase
        .from('linker_library')
        .select('id, smiles, linker_name')
        .eq('linker_family', linkerFamily)
        .limit(1)
        .maybeSingle();

    if (familyMatch?.smiles) {
        return {
            smiles: familyMatch.smiles,
            linkerLibraryId: familyMatch.id,
            suggestedProxy: null
        };
    }

    return {
        smiles: null,
        linkerLibraryId: null,
        suggestedProxy: 'MC-VC-PABC (Standard Cleavable)'
    };
}

/**
 * 항체 Identity 조회 (기본 규칙 기반)
 */
async function resolveAntibodyIdentity(antibodyName: string, drugName: string): Promise<{
    found: boolean;
    name: string | null;
    format: string | null;
    uniprotId: string | null;
    drugbankId: string | null;
}> {
    // 간단한 규칙 기반 매핑 (실제로는 DrugBank/UniProt API 호출 필요)
    const knownAntibodies: Record<string, any> = {
        'trastuzumab': { name: 'Trastuzumab', format: 'mAb', drugbankId: 'DB00072' },
        'pertuzumab': { name: 'Pertuzumab', format: 'mAb', drugbankId: 'DB06366' },
        'sacituzumab': { name: 'Sacituzumab', format: 'mAb', drugbankId: 'DB15140' },
        'enfortumab': { name: 'Enfortumab', format: 'mAb', drugbankId: 'DB15318' },
        'brentuximab': { name: 'Brentuximab', format: 'mAb', drugbankId: 'DB08870' },
        'polatuzumab': { name: 'Polatuzumab', format: 'mAb', drugbankId: 'DB14968' }
    };

    const lowerName = antibodyName.toLowerCase();
    for (const [key, info] of Object.entries(knownAntibodies)) {
        if (lowerName.includes(key)) {
            return {
                found: true,
                ...info,
                uniprotId: null
            };
        }
    }

    return {
        found: false,
        name: null,
        format: null,
        uniprotId: null,
        drugbankId: null
    };
}

/**
 * Review Queue에 Chemistry 제안 생성
 */
async function createChemistryProposal(
    supabase: any,
    seedItemId: string,
    componentType: string,
    proposedChanges: Record<string, any>,
    isVerified: boolean
) {
    const proposedPatch: Record<string, any> = {};

    for (const [field, value] of Object.entries(proposedChanges)) {
        if (value !== null && value !== undefined) {
            proposedPatch[field] = {
                old: null,
                new: value,
                source: `enrich_chemistry_${componentType}`
            };
        }
    }

    await supabase.from('golden_review_queue').insert({
        seed_item_id: seedItemId,
        queue_type: isVerified ? 'verified_update_proposal' : 'enrichment_update',
        entity_type: 'seed_item',
        proposed_patch: proposedPatch,
        confidence: 0.8,
        status: 'pending',
        evidence_refs: [{
            type: 'auto_enrichment',
            component: componentType,
            timestamp: new Date().toISOString()
        }]
    });
}
