'use client';

import { useState, useEffect, useCallback } from 'react';
import {
    Database,
    RefreshCw,
    AlertTriangle,
    Loader2,
    FileText,
    Search,
    ExternalLink,
    Clock,
    CheckCircle2,
    Activity,
    Layers,
    ChevronRight
} from 'lucide-react';
import { getIngestionResults } from '@/lib/actions/admin';
import { clsx } from 'clsx';

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

interface IngestionResult {
    id: string;
    source: string;
    title?: string;
    abstract?: string;
    external_id?: string;
    url?: string;
    created_at: string;
}

export default function IngestionStatusPage() {
    const [activeTab, setActiveTab] = useState<'status' | 'results'>('status');
    const [stats, setStats] = useState<IngestionStats | null>(null);
    const [logs, setLogs] = useState<IngestionLog[]>([]);
    const [results, setResults] = useState<IngestionResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchData = useCallback(async () => {
        try {
            const [statsRes, logsRes, resultsData] = await Promise.all([
                fetch(`${apiUrl}/api/v1/ingestion/stats`),
                fetch(`${apiUrl}/api/v1/ingestion/logs?limit=10`),
                getIngestionResults(50)
            ]);

            if (statsRes.ok) {
                setStats(await statsRes.json());
            }
            if (logsRes.ok) {
                const logsData = await logsRes.json();
                setLogs(logsData.logs || []);
            }
            setResults(resultsData);
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

    const filteredResults = results.filter(r =>
        r.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.abstract?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.external_id?.toLowerCase().includes(searchQuery.toLowerCase())
    );

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
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">데이터 수집 및 결과 탐색기</h1>
                        <p className="text-slate-400 text-sm">파이프라인 실행 상태 모니터링 및 수집된 문헌/근거 탐색</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={clsx("w-4 h-4", refreshing && "animate-spin")} />
                            새로고침
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 mb-8 w-fit">
                    <button
                        onClick={() => setActiveTab('status')}
                        className={clsx(
                            "flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-medium transition-all",
                            activeTab === 'status' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        <Activity className="w-4 h-4" />
                        수집 상태
                    </button>
                    <button
                        onClick={() => setActiveTab('results')}
                        className={clsx(
                            "flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-medium transition-all",
                            activeTab === 'results' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        <Layers className="w-4 h-4" />
                        결과 탐색기
                    </button>
                </div>

                {activeTab === 'status' ? (
                    <div className="space-y-8 animate-in fade-in duration-300">
                        {/* Status Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">최근 24시간 실행</h3>
                                    <div className="p-2 bg-blue-500/10 rounded-lg">
                                        <Clock className="w-5 h-5 text-blue-500" />
                                    </div>
                                </div>
                                <div className="text-3xl font-bold text-white mb-1">{stats?.last_24h_runs || 0}</div>
                                <div className="text-xs text-blue-400 flex items-center gap-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                                    Active Sources: {stats?.sources_active || 0}
                                </div>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">수집된 문서</h3>
                                    <div className="p-2 bg-purple-500/10 rounded-lg">
                                        <Database className="w-5 h-5 text-purple-500" />
                                    </div>
                                </div>
                                <div className="text-3xl font-bold text-white mb-1">{stats?.total_fetched.toLocaleString() || 0}</div>
                                <div className="text-xs text-slate-500">New: {stats?.total_new.toLocaleString() || 0}</div>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">성공률</h3>
                                    <div className="p-2 bg-green-500/10 rounded-lg">
                                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                                    </div>
                                </div>
                                <div className="text-3xl font-bold text-white mb-1">
                                    {stats ? Math.round((stats.successful_runs / stats.total_logs) * 100) : 0}%
                                </div>
                                <div className="text-xs text-green-400">{stats?.successful_runs || 0} successful runs</div>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">장애 발생</h3>
                                    <div className="p-2 bg-red-500/10 rounded-lg">
                                        <AlertTriangle className="w-5 h-5 text-red-500" />
                                    </div>
                                </div>
                                <div className="text-3xl font-bold text-white mb-1">{stats?.failed_runs || 0}</div>
                                <div className="text-xs text-red-400">Requires Attention</div>
                            </div>
                        </div>

                        {/* Recent Jobs Table */}
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                            <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50">
                                <h3 className="font-bold text-white">최근 작업 로그</h3>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="bg-slate-950/50">
                                            <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source</th>
                                            <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Fetched</th>
                                            <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Created At</th>
                                            <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Error</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800">
                                        {logs.length === 0 ? (
                                            <tr>
                                                <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                                                    작업 내역이 없습니다.
                                                </td>
                                            </tr>
                                        ) : (
                                            logs.map((log) => (
                                                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                                                    <td className="px-6 py-4 text-sm font-mono text-blue-400">{log.source}</td>
                                                    <td className="px-6 py-4">
                                                        <span className={clsx(
                                                            "text-[10px] px-2 py-1 rounded-full font-bold uppercase border",
                                                            log.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                                log.status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                                    'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                                        )}>
                                                            {log.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-slate-300 font-medium">{log.records_fetched}</td>
                                                    <td className="px-6 py-4 text-sm text-slate-500">
                                                        {new Date(log.created_at).toLocaleString()}
                                                    </td>
                                                    <td className="px-6 py-4 text-xs text-red-400 max-w-xs truncate">{log.error_message || '-'}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6 animate-in fade-in duration-300">
                        {/* Search Bar */}
                        <div className="relative max-w-md">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="문헌 제목, 초록, ID 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-all shadow-xl"
                            />
                        </div>

                        {/* Results Grid */}
                        <div className="grid grid-cols-1 gap-4">
                            {filteredResults.length === 0 ? (
                                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
                                    수집된 결과가 없습니다.
                                </div>
                            ) : (
                                filteredResults.map((res) => (
                                    <div key={res.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group shadow-xl">
                                        <div className="flex justify-between items-start gap-4 mb-3">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="px-2 py-0.5 bg-blue-600/10 text-blue-400 text-[10px] font-bold rounded uppercase border border-blue-600/20">
                                                        {res.source}
                                                    </span>
                                                    <span className="text-[10px] text-slate-500 font-mono">
                                                        ID: {res.external_id}
                                                    </span>
                                                </div>
                                                <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors leading-tight">
                                                    {res.title}
                                                </h3>
                                            </div>
                                            <a
                                                href={res.url || `https://pubmed.ncbi.nlm.nih.gov/${res.external_id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-all"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        </div>
                                        <p className="text-sm text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                                            {res.abstract || '초록 정보가 없습니다.'}
                                        </p>
                                        <div className="flex items-center justify-between pt-4 border-t border-slate-800/50">
                                            <div className="flex items-center gap-4">
                                                <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                                                    <Clock className="w-3 h-3" />
                                                    {new Date(res.created_at).toLocaleDateString()}
                                                </div>
                                                <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                                                    <FileText className="w-3 h-3" />
                                                    Evidence Score: <span className="text-green-400 font-bold">0.92</span>
                                                </div>
                                            </div>
                                            <button className="text-xs font-bold text-blue-500 hover:text-blue-400 transition-colors flex items-center gap-1">
                                                상세 분석 보기
                                                <ChevronRight className="w-3 h-3" />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #1e293b;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #334155;
                }
            `}</style>
        </div>
    );
}
