import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const supabase = await createClient();

        // 1. 최근 검증 실행 내역 조회
        const { data: runs, error: runsError } = await supabase
            .from('golden_validation_runs')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(20);

        if (runsError) throw runsError;
        if (!runs || runs.length === 0) {
            return NextResponse.json({ items: [] });
        }

        const runIds = runs.map(r => r.id);

        // 2. 상세 지표 조회
        const { data: metrics, error: metricsError } = await supabase
            .from('golden_validation_metrics')
            .select('*')
            .in('run_id', runIds);

        if (metricsError) throw metricsError;

        // 3. 데이터 가공 (run_id별로 metrics 그룹화)
        const metricsMap: Record<string, Record<string, Record<string, number>>> = {};
        metrics?.forEach(m => {
            const rid = m.run_id;
            const axis = m.axis || 'overall';
            if (!metricsMap[rid]) {
                metricsMap[rid] = {};
            }
            if (!metricsMap[rid][axis]) {
                metricsMap[rid][axis] = {};
            }
            metricsMap[rid][axis][m.metric] = m.value;
        });

        // 4. 최종 결과 조립
        const items = runs.map(r => {
            const rid = r.id;
            const runMetrics = metricsMap[rid] || {};
            const summary = runMetrics.overall || {};

            return {
                id: rid,
                created_at: r.created_at,
                pass: r.pass,
                scoring_version: r.scoring_version,
                dataset_version: r.dataset_version || 'v1.0',
                metrics: runMetrics,
                summary: summary
            };
        });

        return NextResponse.json({ items });

    } catch (error: unknown) {
        console.error('get_golden_trend_failed:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        return NextResponse.json(
            { error: 'Failed to fetch golden trend data', details: errorMessage },
            { status: 500 }
        );
    }
}
