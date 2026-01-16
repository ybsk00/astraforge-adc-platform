import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * Step 4: 승격 (Final)
 * Gate 통과 시 golden_final_items로 스냅샷 복제
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const seedIds = body.seed_ids || [];
        const promotedBy = body.promoted_by || 'admin';

        if (!seedIds.length) {
            return NextResponse.json(
                { detail: 'seed_ids is required' },
                { status: 400 }
            );
        }

        const supabase = await createClient();

        let promotedCount = 0;
        let failedCount = 0;
        const failedReasons: Record<string, string> = {};

        for (const seedId of seedIds) {
            // 1. Seed 조회
            const { data: seed, error } = await supabase
                .from('golden_seed_items')
                .select('*')
                .eq('id', seedId)
                .single();

            if (error || !seed) {
                failedCount++;
                failedReasons[seedId] = 'Seed not found';
                continue;
            }

            // 2. Gate 체크 (옵션 C)
            const gateResult = checkGate(seed);

            if (!gateResult.passed) {
                failedCount++;
                failedReasons[seedId] = `Gate failed: ${gateResult.missing.join(', ')}`;
                continue;
            }

            // 3. 이미 승격되었는지 확인
            const { data: existing } = await supabase
                .from('golden_final_items')
                .select('id')
                .eq('seed_id', seedId)
                .maybeSingle();

            if (existing) {
                failedCount++;
                failedReasons[seedId] = 'Already promoted';
                continue;
            }

            // 4. Final 스냅샷 생성
            await supabase.from('golden_final_items').insert({
                seed_id: seedId,
                snapshot: seed, // 전체 Seed 데이터 스냅샷
                gate_status: gateResult.gates,
                promoted_by: promotedBy,
                promoted_at: new Date().toISOString()
            });

            // 5. Seed 상태 업데이트
            await supabase
                .from('golden_seed_items')
                .update({
                    is_final: true,
                    gate_status: 'final',
                    finalized_by: promotedBy,
                    finalized_at: new Date().toISOString()
                })
                .eq('id', seedId);

            promotedCount++;
        }

        return NextResponse.json({
            status: 'ok',
            promoted: promotedCount,
            failed: failedCount,
            failed_reasons: failedReasons
        });

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
        console.error('Promote API error:', error);
        return NextResponse.json(
            { status: 'error', detail: error.message },
            { status: 500 }
        );
    }
}

/**
 * Gate 체크 (옵션 C)
 * 
 * 필수:
 * 1. resolved_target_symbol 존재
 * 2. payload_smiles_standardized 존재 OR is_proxy_payload = true
 * 3. evidence_refs >= 1
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function checkGate(seed: any): {
    passed: boolean;
    gates: Record<string, boolean>;
    missing: string[];
} {
    const gates = {
        target_resolved: Boolean(seed.resolved_target_symbol?.trim()),
        smiles_ready: Boolean(seed.payload_smiles_standardized?.trim()) || seed.is_proxy_payload === true || seed.proxy_smiles_flag === true,
        evidence_exists: Array.isArray(seed.evidence_refs) && seed.evidence_refs.length >= 1
    };

    const missing: string[] = [];
    if (!gates.target_resolved) missing.push('resolved_target_symbol');
    if (!gates.smiles_ready) missing.push('payload_smiles OR proxy');
    if (!gates.evidence_exists) missing.push('evidence_refs');

    return {
        passed: missing.length === 0,
        gates,
        missing
    };
}
