'use server';

import { createClient } from '@/lib/supabase/server';
import { revalidatePath } from 'next/cache';
import { CONNECTOR_REGISTRY } from '@/lib/connectors/registry';

/**
 * Admin Dashboard 통계 데이터 조회
 */
export async function getAdminStats() {
    const supabase = await createClient();

    const [
        { count: connectorRunsCount },
        { count: designRunsCount },
        { data: recentLogs },
        { count: queuedJobs }
    ] = await Promise.all([
        supabase.from('ingestion_logs').select('*', { count: 'exact', head: true }),
        supabase.from('design_runs').select('*', { count: 'exact', head: true }),
        supabase.from('audit_logs').select('*, profiles(name, email)').order('created_at', { ascending: false }).limit(5),
        supabase.from('ingestion_logs').select('*', { count: 'exact', head: true }).eq('status', 'started')
    ]);

    return {
        connectorRunsCount: connectorRunsCount || 0,
        designRunsCount: designRunsCount || 0,
        recentLogs: recentLogs || [],
        queuedJobs: queuedJobs || 0
    };
}

/**
 * 커넥터 목록 조회 (Supabase 직접 조회)
 */
export async function getConnectors() {
    const supabase = await createClient();

    // 1. DB에서 커넥터 정보 조회
    const { data: dbConnectors } = await supabase
        .from('connectors')
        .select('*');

    // 2. 최근 실행 이력 조회 (최신 100개)
    const { data: recentRuns } = await supabase
        .from('connector_runs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

    // 3. 레지스트리와 병합
    return Object.entries(CONNECTOR_REGISTRY)
        .filter(([source]) => source !== 'GOLDEN_SEED_ADC_100') // Hide legacy connector
        .map(([source, info]) => {
            const dbConnector = dbConnectors?.find(c => c.name === source);
            const latestRun = dbConnector
                ? recentRuns?.find(r => r.connector_id === dbConnector.id)
                : null;

            return {
                id: source,
                name: info.name,
                type: info.category,
                is_enabled: !!dbConnector,
                config: dbConnector?.config || {},
                latest_run: latestRun ? {
                    status: latestRun.status,
                    started_at: latestRun.started_at || latestRun.created_at,
                    ended_at: latestRun.ended_at,
                    result_summary: latestRun.result_summary,
                    error_json: latestRun.error_json
                } : null
            };
        });
}

/**
 * 커넥터 생성
 */
export async function createConnector(formData: { name: string; type: string; config: Record<string, unknown> }) {
    const supabase = await createClient();

    // 1. 커넥터 생성
    const { data: connector, error } = await supabase
        .from('connectors')
        .insert([formData])
        .select()
        .single();

    if (error) throw error;

    // 2. 감사 로그 기록
    const { data: userData } = await supabase.auth.getUser();
    if (userData.user) {
        await supabase.from('audit_logs').insert([{
            actor_user_id: userData.user.id,
            action: 'CREATE_CONNECTOR',
            entity_type: 'connector',
            entity_id: connector.id,
            details: { name: formData.name }
        }]);
    }

    revalidatePath('/admin/connectors');
    return connector;
}

/**
 * 커넥터 실행 트리거
 */
/**
 * 커넥터 실행 트리거 (DB Polling 패턴)
 */
export async function triggerConnectorRun(connectorId: string) {
    const supabase = await createClient();

    // 1. Connector ID 조회 (source 이름으로 조회)
    const { data: connector } = await supabase
        .from('connectors')
        .select('id')
        .eq('name', connectorId) // connectorId가 source 이름(예: pubmed)이라고 가정
        .single();

    if (!connector) {
        // 커넥터가 없으면 생성 시도 (동기화)
        const info = CONNECTOR_REGISTRY[connectorId];
        if (info) {
            const { error: createError } = await supabase
                .from('connectors')
                .insert([{
                    name: connectorId,
                    type: info.category === 'literature' || info.category === 'target' ? 'api' : 'db', // 임시 타입 추론
                    config: {}
                }])
                .select()
                .single();

            if (createError) throw createError;

            // 재귀 호출로 실행
            return triggerConnectorRun(connectorId);
        }
        throw new Error(`Connector not found: ${connectorId}`);
    }

    // 2. 작업 큐에 추가
    const { data: run, error } = await supabase
        .from('connector_runs')
        .insert([{
            connector_id: connector.id,
            status: 'queued',
            attempt: 0
        }])
        .select()
        .single();

    if (error) throw error;

    revalidatePath('/admin/connectors');
    return run;
}

/**
 * 기본 커넥터 설정 (Supabase 직접 삽입)
 */
export async function setupDefaultConnectors() {
    const supabase = await createClient();

    // 1. 현재 등록된 소스 확인
    const { data: existing } = await supabase.from('ingestion_cursors').select('source');
    const existingSources = new Set(existing?.map(e => e.source) || []);

    // 2. 누락된 커넥터 필터링 (ingestion_cursors)
    const newCursors = Object.keys(CONNECTOR_REGISTRY)
        .filter(source => !existingSources.has(source))
        .map(source => ({
            source,
            status: 'idle',
            cursor: {},
            stats: { fetched: 0, new: 0, updated: 0 }
        }));

    if (newCursors.length > 0) {
        const { error } = await supabase.from('ingestion_cursors').insert(newCursors);
        if (error) throw error;
    }

    // 3. connectors 테이블 동기화 (Worker용)
    const { data: existingConnectors } = await supabase.from('connectors').select('name');
    const existingConnectorNames = new Set(existingConnectors?.map(c => c.name) || []);

    const newConnectors = Object.entries(CONNECTOR_REGISTRY)
        .filter(([name]) => !existingConnectorNames.has(name))
        .map(([name, info]) => ({
            name,
            type: info.category === 'literature' || info.category === 'target' ? 'api' : 'db', // 단순화된 타입 매핑
            config: {}
        }));

    if (newConnectors.length > 0) {
        const { error } = await supabase.from('connectors').insert(newConnectors);
        if (error) throw error;
    }

    revalidatePath('/admin/connectors');
    return { status: 'success', added_cursors: newCursors.length, added_connectors: newConnectors.length };
}

/**
 * Design Runs 목록 조회
 */
export async function getDesignRuns() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('design_runs')
        .select('*, profiles(name, email)')
        .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
}

/**
 * Reports 목록 조회
 */
export async function getReports() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('reports')
        .select('*, design_runs(run_type, created_at)')
        .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
}

/**
 * 모니터링 메트릭 조회
 */
export async function getObservabilityMetrics(days: number = 7) {
    const supabase = await createClient();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const { data: runs, error } = await supabase
        .from('ingestion_logs')
        .select(`
            status,
            created_at,
            source
        `)
        .gte('created_at', startDate.toISOString());

    if (error) throw error;

    // 데이터 가공 (Source별, 일별 통계)
    interface MetricStats {
        total_runs: number;
        completed: number;
        failed: number;
        success_rate: number;
    }
    const by_source: Record<string, MetricStats> = {};

    runs.forEach((run) => {
        const source = run.source || 'unknown';
        if (!by_source[source]) {
            by_source[source] = { total_runs: 0, completed: 0, failed: 0, success_rate: 0 };
        }
        by_source[source].total_runs++;
        if (run.status === 'completed') by_source[source].completed++;
        if (run.status === 'failed') by_source[source].failed++;
    });

    Object.keys(by_source).forEach(source => {
        const s = by_source[source];
        s.success_rate = s.total_runs > 0 ? Math.round((s.completed / s.total_runs) * 100) : 0;
    });

    return {
        by_source,
        total_logs: runs.length,
        period_days: days
    };
}

/**
 * 알림 목록 조회
 */
export async function getAlerts() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50);

    if (error) throw error;
    return data;
}

/**
 * 알림 읽음 처리
 */
export async function markAlertAsRead(alertId: string) {
    const supabase = await createClient();
    const { error } = await supabase
        .from('alerts')
        .update({ is_read: true })
        .eq('id', alertId);

    if (error) throw error;
    revalidatePath('/admin/alerts');
}

/**
 * 알림 삭제
 */
export async function deleteAlert(alertId: string) {
    const supabase = await createClient();
    const { error } = await supabase
        .from('alerts')
        .delete()
        .eq('id', alertId);

    if (error) throw error;
    revalidatePath('/admin/alerts');
}

/**
 * Seed Targets 목록 조회
 */
/**
 * Seed Targets 목록 조회
 */
export async function getSeedTargets() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('component_catalog')
        .select('*')
        .eq('type', 'target')
        .order('gene_symbol', { ascending: true });

    if (error) throw error;
    return data;
}

/**
 * Seed Diseases 목록 조회
 */
export async function getSeedDiseases() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('entity_diseases') // Diseases are still in entity_diseases for now
        .select('*')
        .order('disease_name', { ascending: true });

    if (error) throw error;
    return data;
}

/**
 * Seed Antibodies 목록 조회
 */
export async function getSeedAntibodies() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('component_catalog')
        .select('*')
        .eq('type', 'antibody')
        .order('name', { ascending: true });

    if (error) throw error;
    return data;
}

/**
 * Seed Linkers 목록 조회
 */
export async function getSeedLinkers() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('component_catalog')
        .select('*')
        .eq('type', 'linker')
        .order('name', { ascending: true });

    if (error) throw error;
    return data;
}

/**
 * Seed Payloads 목록 조회
 */
export async function getSeedPayloads() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('component_catalog')
        .select('*, drug_name:name') // Alias name to drug_name for frontend compatibility
        .eq('type', 'payload')
        .order('name', { ascending: true });

    if (error) throw error;
    return data;
}

/**
 * Seed Sets 목록 조회
 */
export async function getSeedSets() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('seed_sets')
        .select(`
            *,
            seed_set_targets(target_id),
            seed_set_diseases(disease_id),
            seed_set_linkers(linker_id),
            seed_set_payloads(drug_id)
        `)
        .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
}

/**
 * Seed Set 생성
 */
export async function createSeedSet(
    name: string,
    targetIds: string[],
    diseaseIds: string[],
    linkerIds: string[] = [],
    payloadIds: string[] = []
) {
    const supabase = await createClient();

    // 1. Seed Set 생성
    const { data: seedSet, error: setError } = await supabase
        .from('seed_sets')
        .insert([{ seed_set_name: name }])
        .select()
        .single();

    if (setError) throw setError;

    // 2. Targets 연결
    if (targetIds.length > 0) {
        const targetInserts = targetIds.map(tid => ({ seed_set_id: seedSet.id, target_id: tid }));
        const { error: tError } = await supabase.from('seed_set_targets').insert(targetInserts);
        if (tError) throw tError;
    }

    // 3. Diseases 연결
    if (diseaseIds.length > 0) {
        const diseaseInserts = diseaseIds.map(did => ({ seed_set_id: seedSet.id, disease_id: did }));
        const { error: dError } = await supabase.from('seed_set_diseases').insert(diseaseInserts);
        if (dError) throw dError;
    }

    // 4. Linkers 연결
    if (linkerIds.length > 0) {
        const linkerInserts = linkerIds.map(lid => ({ seed_set_id: seedSet.id, linker_id: lid }));
        const { error: lError } = await supabase.from('seed_set_linkers').insert(linkerInserts);
        if (lError) throw lError;
    }

    // 5. Payloads 연결
    if (payloadIds.length > 0) {
        const payloadInserts = payloadIds.map(pid => ({ seed_set_id: seedSet.id, drug_id: pid }));
        const { error: pError } = await supabase.from('seed_set_payloads').insert(payloadInserts);
        if (pError) throw pError;
    }

    revalidatePath('/admin/seeds');
    return seedSet;
}

/**
 * 수집 결과(문헌 및 근거) 조회
 */
export async function getIngestionResults(limit: number = 50) {
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('literature_documents')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit);

    if (error) throw error;
    return data;
}

/**
 * 링커 구조 자동 조회 및 업데이트
 */
export async function resolveLinkerStructure(linkerId: string) {
    const supabase = await createClient();
    const { data: linker, error: fetchError } = await supabase
        .from('entity_linkers')
        .select('*')
        .eq('id', linkerId)
        .single();

    if (fetchError) throw fetchError;

    const { resolveStructure } = await import('@/lib/chem/resolver');
    const candidates = await resolveStructure(linker.name, linker.synonyms || []);

    if (candidates.length > 0) {
        const best = candidates[0];
        const { error: updateError } = await supabase
            .from('entity_linkers')
            .update({
                smiles: best.smiles,
                inchi_key: best.inchi_key,
                external_id: best.external_id,
                structure_source: best.source,
                structure_status: best.confidence >= 90 ? 'confirmed' : 'resolved',
                structure_confidence: best.confidence
            })
            .eq('id', linkerId);

        if (updateError) throw updateError;
    }

    revalidatePath('/admin/seeds');
    return candidates;
}

/**
 * 페이로드 구조 자동 조회 및 업데이트
 */
export async function resolvePayloadStructure(payloadId: string) {
    const supabase = await createClient();
    const { data: payload, error: fetchError } = await supabase
        .from('entity_drugs')
        .select('*')
        .eq('id', payloadId)
        .single();

    if (fetchError) throw fetchError;

    const { resolveStructure } = await import('@/lib/chem/resolver');
    const candidates = await resolveStructure(payload.drug_name, payload.synonyms || []);

    if (candidates.length > 0) {
        const best = candidates[0];
        const { error: updateError } = await supabase
            .from('entity_drugs')
            .update({
                smiles: best.smiles,
                inchi_key: best.inchi_key,
                external_id: best.external_id,
                structure_source: best.source,
                structure_status: best.confidence >= 90 ? 'confirmed' : 'resolved',
                structure_confidence: best.confidence
            })
            .eq('id', payloadId);

        if (updateError) throw updateError;
    }

    revalidatePath('/admin/seeds');
    return candidates;
}

/**
 * 엔티티 구조 수동 업데이트 (검수용)
 */
export async function updateEntityStructure(
    type: 'linker' | 'payload',
    id: string,
    data: {
        smiles?: string;
        inchi_key?: string;
        structure_status: string;
        structure_confidence?: number;
    }
) {
    const supabase = await createClient();
    const table = type === 'linker' ? 'entity_linkers' : 'entity_drugs';

    const { error } = await supabase
        .from(table)
        .update({
            ...data,
            structure_source: 'manual'
        })
        .eq('id', id);

    if (error) throw error;

    revalidatePath('/admin/seeds');
}
