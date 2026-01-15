import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * Step 1: 골든셋 로우데이터 찾기
 * ClinicalTrials.gov에서 암종+ADC 후보 수집 → golden_candidates 저장
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const cancerType = body.cancer_type || 'cancer';
        const targetList = body.target_list || [];
        const limit = body.limit || 200;

        const supabase = await createClient();

        // ClinicalTrials.gov API v2 호출
        const results = await searchClinicalTrials(cancerType, targetList, limit);

        if (!results.length) {
            return NextResponse.json({
                status: 'ok',
                inserted: 0,
                updated: 0,
                message: 'No candidates found'
            });
        }

        // golden_candidates에 upsert
        let insertedCount = 0;
        let updatedCount = 0;

        for (const candidate of results) {
            // 중복 체크 (nct_id 기준)
            const nctIds = candidate.nct_ids || [];
            const primaryNct = nctIds[0];

            if (primaryNct) {
                const { data: existing } = await supabase
                    .from('golden_candidates')
                    .select('id')
                    .contains('evidence_refs', [{ id: primaryNct }])
                    .maybeSingle();

                if (existing) {
                    // Update
                    await supabase
                        .from('golden_candidates')
                        .update({
                            cancer_type: cancerType,
                            interventions_raw: candidate.interventions_raw,
                            summary_raw: candidate.summary_raw,
                            extracted_target_raw: candidate.extracted_target,
                            extracted_payload_raw: candidate.extracted_payload,
                            extracted_linker_raw: candidate.extracted_linker,
                            updated_at: new Date().toISOString()
                        })
                        .eq('id', existing.id);
                    updatedCount++;
                } else {
                    // Insert
                    await supabase
                        .from('golden_candidates')
                        .insert({
                            drug_name: candidate.drug_name,
                            target: candidate.target || 'Unknown',
                            antibody: candidate.antibody,
                            linker: candidate.linker,
                            payload: candidate.payload,
                            cancer_type: cancerType,
                            interventions_raw: candidate.interventions_raw,
                            summary_raw: candidate.summary_raw,
                            extracted_target_raw: candidate.extracted_target,
                            extracted_payload_raw: candidate.extracted_payload,
                            extracted_linker_raw: candidate.extracted_linker,
                            approval_status: candidate.phase,
                            confidence_score: candidate.match_score || 0.5,
                            evidence_refs: nctIds.map((nct: string) => ({
                                type: 'NCT',
                                id: nct,
                                url: `https://clinicaltrials.gov/study/${nct}`
                            }))
                        });
                    insertedCount++;
                }
            }
        }

        return NextResponse.json({
            status: 'ok',
            inserted: insertedCount,
            updated: updatedCount,
            total_found: results.length
        });

    } catch (error: any) {
        console.error('Step 1 API error:', error);
        return NextResponse.json(
            { status: 'error', detail: error.message },
            { status: 500 }
        );
    }
}

/**
 * ClinicalTrials.gov API v2 검색
 */
async function searchClinicalTrials(
    cancerType: string,
    targetList: string[],
    limit: number
): Promise<any[]> {
    const CT_API_BASE = 'https://clinicaltrials.gov/api/v2/studies';

    // ADC 키워드 세트
    const adcTerms = [
        '"antibody-drug conjugate"',
        '"antibody drug conjugate"',
        '"ADC"',
        '"immunoconjugate"',
        '"antibody conjugate"'
    ].join(' OR ');

    // 암종 + 타겟 조합 쿼리
    let query = `(${adcTerms}) AND "${cancerType}"`;

    if (targetList.length > 0) {
        const targetOr = targetList.map(t => `"${t}"`).join(' OR ');
        query += ` AND (${targetOr})`;
    }

    const params = new URLSearchParams({
        'query.term': query,
        'filter.overallStatus': 'RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED',
        'pageSize': Math.min(limit, 100).toString(),
        'fields': [
            'NCTId',
            'BriefTitle',
            'OfficialTitle',
            'OverallStatus',
            'Phase',
            'Condition',
            'InterventionName',
            'InterventionType',
            'LeadSponsorName',
            'StartDate'
        ].join(','),
        'format': 'json'
    });

    try {
        const response = await fetch(`${CT_API_BASE}?${params}`, {
            headers: { 'Accept': 'application/json' },
            next: { revalidate: 3600 } // 1시간 캐시
        });

        if (!response.ok) {
            throw new Error(`ClinicalTrials API error: ${response.status}`);
        }

        const data = await response.json();
        const studies = data.studies || [];

        return studies.map((study: any) => {
            const proto = study.protocolSection || {};
            const ident = proto.identificationModule || {};
            const status = proto.statusModule || {};
            const arms = proto.armsInterventionsModule || {};
            const conditions = proto.conditionsModule || {};

            // Drug/Intervention 추출
            const interventions = arms.interventions || [];
            const drugInterventions = interventions.filter(
                (i: any) => i.type === 'DRUG' || i.type === 'BIOLOGICAL'
            );
            const drugName = drugInterventions[0]?.name || ident.briefTitle?.split(' ')[0] || 'Unknown';

            // 간단한 구성요소 추출 (Step 2에서 정밀 추출)
            const interventionText = drugInterventions.map((i: any) => i.name).join(' ').toLowerCase();

            return {
                nct_ids: [ident.nctId],
                drug_name: drugName,
                target: extractTarget(interventionText),
                antibody: extractAntibody(interventionText),
                linker: extractLinker(interventionText),
                payload: extractPayload(interventionText),
                phase: (status.phases || ['Unknown'])[0],
                conditions: conditions.conditions || [],
                interventions_raw: interventions,
                summary_raw: ident.officialTitle || ident.briefTitle,
                match_score: calculateMatchScore(drugInterventions),
                extracted_target: null,
                extracted_payload: null,
                extracted_linker: null
            };
        });

    } catch (error) {
        console.error('ClinicalTrials search error:', error);
        return [];
    }
}

// 간단한 추출 함수들 (Step 2에서 정밀화)
function extractTarget(text: string): string {
    const targets: Record<string, string> = {
        'trastuzumab': 'HER2',
        'pertuzumab': 'HER2',
        'datopotamab': 'TROP2',
        'sacituzumab': 'TROP2',
        'enfortumab': 'Nectin-4',
        'brentuximab': 'CD30',
        'polatuzumab': 'CD79b',
        'belantamab': 'BCMA'
    };
    for (const [key, val] of Object.entries(targets)) {
        if (text.includes(key)) return val;
    }
    return 'Unknown';
}

function extractAntibody(text: string): string | null {
    const match = text.match(/([a-z]+mab|[a-z]+tuzumab|[a-z]+zumab)/i);
    return match ? match[0] : null;
}

function extractLinker(text: string): string | null {
    const linkers = ['vedotin', 'deruxtecan', 'govitecan', 'mertansine', 'ozogamicin'];
    for (const l of linkers) {
        if (text.includes(l)) return l;
    }
    return null;
}

function extractPayload(text: string): string | null {
    const payloads: Record<string, string> = {
        'vedotin': 'MMAE',
        'deruxtecan': 'DXd',
        'govitecan': 'SN-38',
        'mertansine': 'DM1',
        'ozogamicin': 'Calicheamicin'
    };
    for (const [key, val] of Object.entries(payloads)) {
        if (text.includes(key)) return val;
    }
    return null;
}

function calculateMatchScore(interventions: any[]): number {
    if (!interventions.length) return 0.3;

    const text = interventions.map(i => (i.name || '').toLowerCase()).join(' ');
    let score = 0.5;

    if (text.includes('antibody-drug conjugate') || text.includes('adc')) score += 0.3;
    if (text.includes('vedotin') || text.includes('deruxtecan') || text.includes('mab')) score += 0.2;

    return Math.min(score, 1.0);
}
