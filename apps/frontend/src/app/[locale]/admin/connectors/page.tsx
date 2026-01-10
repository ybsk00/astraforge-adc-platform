'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    RefreshCw,
    Play,
    AlertCircle,
    CheckCircle,
    Loader2,
    ExternalLink,
    Database,
    FileText,
    Target,
    FlaskConical,
    Activity,
    Shield
} from 'lucide-react';

interface Connector {
    source: string;
    name: string;
    description: string;
    category: string;
    rate_limit: string;
    status: 'idle' | 'running' | 'failed';
    last_success_at: string | null;
    stats: {
        fetched?: number;
        new?: number;
        updated?: number;
        errors?: number;
    };
    error_message: string | null;
}

const STATUS_CONFIG = {
    idle: { label: 'Idle', icon: CheckCircle, class: 'bg-green-500/20 text-green-400' },
    running: { label: 'Running', icon: Loader2, class: 'bg-blue-500/20 text-blue-400' },
    failed: { label: 'Failed', icon: AlertCircle, class: 'bg-red-500/20 text-red-400' },
};

const CATEGORY_CONFIG: Record<string, { icon: any; color: string; bg: string }> = {
    literature: { icon: FileText, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    target: { icon: Target, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    expression: { icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
    compound: { icon: FlaskConical, color: 'text-orange-400', bg: 'bg-orange-500/20' },
    clinical: { icon: Database, color: 'text-pink-400', bg: 'bg-pink-500/20' },
    safety: { icon: Shield, color: 'text-red-400', bg: 'bg-red-500/20' },
};

export default function ConnectorsPage() {
    const [connectors, setConnectors] = useState<Connector[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [runningConnector, setRunningConnector] = useState<string | null>(null);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchConnectors = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/connectors`);
            if (!res.ok) throw new Error('Failed to fetch connectors');
            const data = await res.json();
            setConnectors(data.connectors || []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConnectors();
        const interval = setInterval(fetchConnectors, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleRun = async (source: string) => {
        setRunningConnector(source);
        setConnectors(prev => prev.map(c =>
            c.source === source ? { ...c, status: 'running' as const } : c
        ));

        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/connectors/${source}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: 50 }),
            });

            if (!res.ok) throw new Error('Failed to start connector');

            await new Promise(resolve => setTimeout(resolve, 3000));
            await fetchConnectors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to run connector');
            await fetchConnectors();
        } finally {
            setRunningConnector(null);
        }
    };

    const handleRetry = async (source: string) => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/connectors/${source}/retry`, {
                method: 'POST',
            });

            if (!res.ok) throw new Error('Failed to retry connector');
            await fetchConnectors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to retry connector');
        }
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '—';
        const date = new Date(dateStr);
        return date.toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center">
                <div className="text-slate-400">Loading connectors...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-950 p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg">
                        Error: {error}
                    </div>
                </div>
            </div>
        );
    }

    const stats = {
        idle: connectors.filter(c => c.status === 'idle').length,
        running: connectors.filter(c => c.status === 'running').length,
        failed: connectors.filter(c => c.status === 'failed').length,
        totalFetched: connectors.reduce((sum, c) => sum + (c.stats?.fetched || 0), 0),
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">커넥터 대시보드</h1>
                        <p className="text-slate-400 text-sm">외부 데이터 소스를 연결 및 관리합니다.</p>
                    </div>
                    <button
                        onClick={fetchConnectors}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        새로고침
                    </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-green-500/20 rounded-lg">
                                <CheckCircle className="w-5 h-5 text-green-400" />
                            </div>
                            <span className="text-sm text-slate-400">Idle</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{stats.idle}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-blue-500/20 rounded-lg">
                                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                            </div>
                            <span className="text-sm text-slate-400">Running</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{stats.running}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-red-500/20 rounded-lg">
                                <AlertCircle className="w-5 h-5 text-red-400" />
                            </div>
                            <span className="text-sm text-slate-400">Failed</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{stats.failed}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-purple-500/20 rounded-lg">
                                <Database className="w-5 h-5 text-purple-400" />
                            </div>
                            <span className="text-sm text-slate-400">Total Fetched</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{stats.totalFetched.toLocaleString()}</div>
                    </div>
                </div>

                {/* Connector Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {connectors.map((connector) => {
                        const statusConfig = STATUS_CONFIG[connector.status];
                        const StatusIcon = statusConfig.icon;
                        const categoryConfig = CATEGORY_CONFIG[connector.category] || CATEGORY_CONFIG.literature;
                        const CategoryIcon = categoryConfig.icon;

                        return (
                            <div
                                key={connector.source}
                                className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2.5 rounded-lg ${categoryConfig.bg}`}>
                                            <CategoryIcon className={`w-5 h-5 ${categoryConfig.color}`} />
                                        </div>
                                        <div>
                                            <h3 className="text-white font-semibold">{connector.name}</h3>
                                            <span className="text-xs text-slate-500 uppercase">{connector.category}</span>
                                        </div>
                                    </div>
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.class}`}>
                                        <StatusIcon className={`w-3 h-3 ${connector.status === 'running' ? 'animate-spin' : ''}`} />
                                        {statusConfig.label}
                                    </span>
                                </div>

                                <p className="text-sm text-slate-400 mb-4 line-clamp-2">
                                    {connector.description}
                                </p>

                                <div className="text-xs text-slate-500 mb-4 space-y-1">
                                    <div className="flex justify-between">
                                        <span>Fetched</span>
                                        <span className="text-white">{connector.stats?.fetched || 0}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Last Run</span>
                                        <span className="text-white">{formatDate(connector.last_success_at)}</span>
                                    </div>
                                    {connector.error_message && (
                                        <div className="text-red-400 truncate pt-1" title={connector.error_message}>
                                            ⚠️ {connector.error_message}
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-2">
                                    {connector.status === 'failed' ? (
                                        <button
                                            onClick={() => handleRetry(connector.source)}
                                            className="flex-1 px-3 py-2 bg-yellow-600 hover:bg-yellow-500 text-white text-sm font-medium rounded-lg transition-colors"
                                        >
                                            Retry
                                        </button>
                                    ) : connector.status === 'running' ? (
                                        <button
                                            disabled
                                            className="flex-1 px-3 py-2 bg-slate-800 text-slate-500 text-sm font-medium rounded-lg cursor-not-allowed"
                                        >
                                            Running...
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleRun(connector.source)}
                                            disabled={runningConnector === connector.source}
                                            className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors disabled:bg-slate-700 flex items-center justify-center gap-2"
                                        >
                                            <Play className="w-4 h-4" />
                                            {runningConnector === connector.source ? 'Starting...' : 'Run'}
                                        </button>
                                    )}
                                    <Link
                                        href={`/admin/connectors/${connector.source}`}
                                        className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-1 transition-colors"
                                    >
                                        <ExternalLink className="w-4 h-4" />
                                    </Link>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
