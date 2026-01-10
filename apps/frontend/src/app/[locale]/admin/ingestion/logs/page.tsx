'use client';

import { useState, useEffect } from 'react';
import {
    RefreshCw,
    ChevronLeft,
    ChevronRight,
    CheckCircle,
    Clock,
    XCircle
} from 'lucide-react';

interface LogEntry {
    id: string;
    source: string;
    phase: string;
    status: string;
    duration_ms: number | null;
    records_fetched: number;
    records_new: number;
    records_updated: number;
    error_code: string | null;
    error_message: string | null;
    created_at: string;
}

const STATUS_CONFIG: Record<string, { label: string; icon: any; class: string }> = {
    started: { label: 'Started', icon: Clock, class: 'bg-yellow-500/20 text-yellow-400' },
    completed: { label: 'Completed', icon: CheckCircle, class: 'bg-green-500/20 text-green-400' },
    failed: { label: 'Failed', icon: XCircle, class: 'bg-red-500/20 text-red-400' },
};

const SOURCE_CONFIG: Record<string, string> = {
    pubmed: 'bg-purple-500/20 text-purple-400',
    uniprot: 'bg-blue-500/20 text-blue-400',
    opentargets: 'bg-cyan-500/20 text-cyan-400',
    hpa: 'bg-teal-500/20 text-teal-400',
    chembl: 'bg-orange-500/20 text-orange-400',
    pubchem: 'bg-amber-500/20 text-amber-400',
    clinicaltrials: 'bg-pink-500/20 text-pink-400',
    openfda: 'bg-red-500/20 text-red-400',
};

export default function IngestionLogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterSource, setFilterSource] = useState('');
    const [filterStatus, setFilterStatus] = useState('');
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const limit = 50;

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filterSource) params.append('source', filterSource);
            if (filterStatus) params.append('status', filterStatus);
            params.append('limit', String(limit));
            params.append('offset', String(offset));

            const res = await fetch(`/api/v1/ingestion/logs?${params}`);
            if (!res.ok) throw new Error('Failed to fetch');
            const data = await res.json();
            setLogs(data.logs || []);
            setTotal(data.total || 0);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [filterSource, filterStatus, offset]);

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString('ko-KR');
    };

    const formatDuration = (ms: number | null) => {
        if (!ms) return '—';
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    };

    const sources = ['pubmed', 'uniprot', 'opentargets', 'hpa', 'chembl', 'pubchem', 'clinicaltrials', 'openfda'];

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">수집 로그</h1>
                        <p className="text-slate-400 text-sm">외부 데이터 소스의 수집 이력을 조회합니다.</p>
                    </div>
                    <button
                        onClick={fetchLogs}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        새로고침
                    </button>
                </div>

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 flex flex-col md:flex-row gap-4">
                    <select
                        value={filterSource}
                        onChange={(e) => { setFilterSource(e.target.value); setOffset(0); }}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Sources</option>
                        {sources.map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>

                    <select
                        value={filterStatus}
                        onChange={(e) => { setFilterStatus(e.target.value); setOffset(0); }}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Status</option>
                        <option value="started">Started</option>
                        <option value="completed">Completed</option>
                        <option value="failed">Failed</option>
                    </select>

                    <div className="ml-auto text-sm text-slate-400 self-center">
                        Showing {logs.length} of {total} logs
                    </div>
                </div>

                {/* Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-800">
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Time</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Source</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Phase</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Duration</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Fetched</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">New</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Updated</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Error</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {logs.map((log) => {
                                    const statusConfig = STATUS_CONFIG[log.status] || STATUS_CONFIG.started;
                                    const StatusIcon = statusConfig.icon;

                                    return (
                                        <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {formatDate(log.created_at)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2.5 py-1 rounded text-xs font-medium ${SOURCE_CONFIG[log.source] || 'bg-slate-500/20 text-slate-400'}`}>
                                                    {log.source}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-white">{log.phase}</td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.class}`}>
                                                    <StatusIcon className="w-3 h-3" />
                                                    {statusConfig.label}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm font-mono text-slate-300">
                                                {formatDuration(log.duration_ms)}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-white">{log.records_fetched || 0}</td>
                                            <td className="px-6 py-4 text-sm text-green-400">{log.records_new || 0}</td>
                                            <td className="px-6 py-4 text-sm text-blue-400">{log.records_updated || 0}</td>
                                            <td className="px-6 py-4 text-sm text-red-400 truncate max-w-xs" title={log.error_message || ''}>
                                                {log.error_message || '—'}
                                            </td>
                                        </tr>
                                    );
                                })}
                                {logs.length === 0 && !loading && (
                                    <tr>
                                        <td colSpan={9} className="px-6 py-8 text-center text-slate-400">
                                            No logs found
                                        </td>
                                    </tr>
                                )}
                                {loading && (
                                    <tr>
                                        <td colSpan={9} className="px-6 py-8 text-center text-slate-400">
                                            Loading...
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {total > limit && (
                        <div className="px-6 py-4 border-t border-slate-800 flex justify-between items-center">
                            <span className="text-sm text-slate-400">
                                Page {Math.floor(offset / limit) + 1} of {Math.ceil(total / limit)}
                            </span>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setOffset(Math.max(0, offset - limit))}
                                    disabled={offset === 0}
                                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                >
                                    <ChevronLeft className="w-4 h-4" /> 이전
                                </button>
                                <button
                                    onClick={() => setOffset(offset + limit)}
                                    disabled={offset + limit >= total}
                                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                >
                                    다음 <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
