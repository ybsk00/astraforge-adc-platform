'use client';

import { useState, useEffect, useCallback } from 'react';
import { Database, RefreshCw, Play, AlertTriangle, Loader2 } from 'lucide-react';

interface IngestionStats {
    total_logs: number;
    total_fetched: number;
    total_new: number;
    successful_runs: number;
    failed_runs: number;
    sources_active: number;
    last_24h_runs: number;
    last_24h_fetched: number;
}

interface IngestionLog {
    id: string;
    source: string;
    status: string;
    records_fetched: number;
    error_message?: string;
    created_at: string;
}

export default function IngestionStatusPage() {
    const [stats, setStats] = useState<IngestionStats | null>(null);
    const [logs, setLogs] = useState<IngestionLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchData = useCallback(async () => {
        try {
            const [statsRes, logsRes] = await Promise.all([
                fetch(`${apiUrl}/api/v1/ingestion/stats`),
                fetch(`${apiUrl}/api/v1/ingestion/logs?limit=10`)
            ]);

            if (statsRes.ok) {
                setStats(await statsRes.json());
            }
            if (logsRes.ok) {
                const logsData = await logsRes.json();
                setLogs(logsData.logs || []);
            }
        } catch (err) {
            console.error('Failed to fetch ingestion data:', err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [apiUrl]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchData();
    };

    const handleRunIngestion = async () => {
        if (!confirm('Start new ingestion job?')) return;
        // TODO: Implement trigger API
        alert('Ingestion triggered (Not implemented yet)');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">문헌 수집/인덱싱 상태</h1>
                        <p className="text-slate-400">PubMed 커넥터 및 데이터 인덱싱 파이프라인 상태를 모니터링합니다.</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                            새로고침
                        </button>
                        <button
                            onClick={handleRunIngestion}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Play className="w-4 h-4" />
                            수집 실행
                        </button>
                    </div>
                </div>

                {/* Status Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Last 24h Runs</h3>
                            <Database className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">{stats?.last_24h_runs || 0}</div>
                        <div className="text-xs text-green-400">Active Sources: {stats?.sources_active || 0}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Docs Ingested</h3>
                            <div className="text-xs font-mono text-slate-500">TOTAL</div>
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">{stats?.total_fetched.toLocaleString() || 0}</div>
                        <div className="text-xs text-slate-400">New: {stats?.total_new.toLocaleString() || 0}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Successful Runs</h3>
                            <div className="text-xs font-mono text-slate-500">ALL TIME</div>
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">{stats?.successful_runs || 0}</div>
                        <div className="text-xs text-blue-400">Success Rate: {stats ? Math.round((stats.successful_runs / stats.total_logs) * 100) : 0}%</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Failures</h3>
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">{stats?.failed_runs || 0}</div>
                        <div className="text-xs text-red-400">Requires Attention</div>
                    </div>
                </div>

                {/* Recent Jobs Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">최근 작업 로그</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Source</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Fetched</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Created At</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Error</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {logs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                                        No logs found.
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-slate-800/50">
                                        <td className="px-6 py-4 text-sm font-mono text-slate-300">{log.source}</td>
                                        <td className="px-6 py-4">
                                            <span className={`text-xs px-2 py-1 rounded ${log.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                                    log.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-blue-500/20 text-blue-400'
                                                }`}>
                                                {log.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-500">{log.records_fetched}</td>
                                        <td className="px-6 py-4 text-sm text-slate-500">
                                            {new Date(log.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-red-400">{log.error_message || '-'}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
