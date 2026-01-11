'use server';

import { createClient } from '@/lib/supabase/server';
import { revalidatePath } from 'next/cache';

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
        supabase.from('connector_runs').select('*', { count: 'exact', head: true }),
        supabase.from('design_runs').select('*', { count: 'exact', head: true }),
        supabase.from('audit_logs').select('*, profiles(name, email)').order('created_at', { ascending: false }).limit(5),
        supabase.from('connector_runs').select('*', { count: 'exact', head: true }).eq('status', 'queued')
    ]);

    return {
        connectorRunsCount: connectorRunsCount || 0,
        designRunsCount: designRunsCount || 0,
        recentLogs: recentLogs || [],
        queuedJobs: queuedJobs || 0
    };
}

/**
 * 커넥터 목록 조회 (최신 실행 상태 포함)
 */
export async function getConnectors() {
    const supabase = await createClient();
    const { data: connectors, error } = await supabase
        .from('connectors')
        .select(`
            *,
            connector_runs (
                status,
                started_at,
                ended_at,
                error_json
            )
        `)
        .order('created_at', { ascending: false });

    if (error) throw error;

    // 각 커넥터별로 최신 실행 1건만 추출
    return connectors.map(c => ({
        ...c,
        latest_run: c.connector_runs?.sort((a: any, b: any) =>
            new Date(b.started_at || b.created_at).getTime() - new Date(a.started_at || a.created_at).getTime()
        )[0] || null
    }));
}

/**
 * 커넥터 생성
 */
export async function createConnector(formData: { name: string; type: string; config: any }) {
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
export async function triggerConnectorRun(connectorId: string) {
    const supabase = await createClient();

    // 1. Job 생성
    const { data: run, error } = await supabase
        .from('connector_runs')
        .insert([{
            connector_id: connectorId,
            status: 'queued',
            attempt: 0
        }])
        .select()
        .single();

    if (error) throw error;

    // 2. 감사 로그 기록
    const { data: userData } = await supabase.auth.getUser();
    if (userData.user) {
        await supabase.from('audit_logs').insert([{
            actor_user_id: userData.user.id,
            action: 'TRIGGER_CONNECTOR',
            entity_type: 'connector',
            entity_id: connectorId,
            details: { run_id: run.id }
        }]);
    }

    revalidatePath('/admin/ingestion');
    return run;
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
        .from('connector_runs')
        .select(`
            status,
            started_at,
            connectors (name)
        `)
        .gte('created_at', startDate.toISOString());

    if (error) throw error;

    // 데이터 가공 (Source별, 일별 통계)
    const by_source: Record<string, any> = {};
    runs.forEach((run: any) => {
        const source = run.connectors?.name || 'unknown';
        if (!by_source[source]) {
            by_source[source] = { total_runs: 0, completed: 0, failed: 0, success_rate: 0 };
        }
        by_source[source].total_runs++;
        if (run.status === 'succeeded') by_source[source].completed++;
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
export async function getSeedTargets() {
    const supabase = await createClient();
    const { data, error } = await supabase
        .from('entity_targets')
        .select('*')
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
        .from('entity_diseases')
        .select('*')
        .order('disease_name', { ascending: true });

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
            seed_set_diseases(disease_id)
        `)
        .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
}

/**
 * Seed Set 생성
 */
export async function createSeedSet(name: string, targetIds: string[], diseaseIds: string[]) {
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
