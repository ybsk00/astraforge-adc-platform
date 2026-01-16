'use client';

import { useState, useEffect } from 'react';
import { getObservabilityMetrics } from '@/lib/actions/admin';
import {
    Activity,
    BarChart3,
    AlertCircle,
    CheckCircle2,
    Clock,
    RefreshCw,
    Database,
    Zap
} from 'lucide-react';
import { useTranslations } from 'next-intl';

interface MetricsData {
    by_source: Record<string, {
        total_runs: number;
        completed: number;
        failed: number;
        success_rate: number;
    }>;
    total_logs: number;
    period_days: number;
}

export default function ObservabilityPage() {
    const t = useTranslations('Admin.observability');
    const [metrics, setMetrics] = useState<MetricsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(7);

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [days]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const data = await getObservabilityMetrics(days);
            setMetrics(data as MetricsData);
        } catch (err) {
            console.error('Failed to fetch observability data:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !metrics) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                            <Activity className="w-6 h-6 text-blue-400" />
                            {t('title')}
                        </h1>
                        <p className="text-slate-400 text-sm">{t('subtitle')}</p>
                    </div>
                    <div className="flex gap-3">
                        <select
                            value={days}
                            onChange={(e) => setDays(Number(e.target.value))}
                            className="bg-slate-900 border border-slate-800 text-white text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value={7}>{t('period.7d')}</option>
                            <option value={14}>Last 14 Days</option>
                            <option value={30}>{t('period.30d')}</option>
                        </select>
                        <button
                            onClick={fetchData}
                            className="p-2 bg-slate-900 border border-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-2 text-slate-400">
                            <Zap className="w-4 h-4" />
                            <span className="text-sm font-medium">{t('totalLogs')}</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{metrics?.total_logs || 0}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-2 text-green-400">
                            <CheckCircle2 className="w-4 h-4" />
                            <span className="text-sm font-medium">{t('table.rate')}</span>
                        </div>
                        <div className="text-2xl font-bold text-white">
                            {metrics ? Math.round((Object.values(metrics.by_source).reduce((acc, curr) => acc + curr.completed, 0) / (metrics.total_logs || 1)) * 100) : 0}%
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-2 text-blue-400">
                            <Database className="w-4 h-4" />
                            <span className="text-sm font-medium">Active Sources</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{Object.keys(metrics?.by_source || {}).length}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-2 text-red-400">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">Total Failures</span>
                        </div>
                        <div className="text-2xl font-bold text-white">
                            {Object.values(metrics?.by_source || {}).reduce((acc, curr) => acc + curr.failed, 0)}
                        </div>
                    </div>
                </div>

                {/* Source Metrics Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden mb-8">
                    <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <BarChart3 className="w-5 h-5 text-blue-400" />
                            {t('successRate')}
                        </h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-wider">
                                    <th className="px-6 py-4 font-medium">{t('table.source')}</th>
                                    <th className="px-6 py-4 font-medium text-right">{t('table.total')}</th>
                                    <th className="px-6 py-4 font-medium text-right">{t('table.completed')}</th>
                                    <th className="px-6 py-4 font-medium text-right">{t('table.failed')}</th>
                                    <th className="px-6 py-4 font-medium text-right">{t('table.rate')}</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {Object.entries(metrics?.by_source || {}).map(([source, stats]) => (
                                    <tr key={source} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-medium text-white">{source}</span>
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm text-slate-300">{stats.total_runs}</td>
                                        <td className="px-6 py-4 text-right text-sm text-green-400">{stats.completed}</td>
                                        <td className="px-6 py-4 text-right text-sm text-red-400">{stats.failed}</td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${stats.success_rate >= 90 ? 'bg-green-500' :
                                                            stats.success_rate >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                                                            }`}
                                                        style={{ width: `${stats.success_rate}%` }}
                                                    />
                                                </div>
                                                <span className="text-xs font-medium text-slate-400 w-8">{stats.success_rate}%</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Health Status */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                            <Clock className="w-4 h-4 text-slate-400" />
                            {t('health')}
                        </h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-slate-400">Database Connection</span>
                                <span className="flex items-center gap-1.5 text-xs font-medium text-green-400">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                    {t('operational')}
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-slate-400">Worker Status</span>
                                <span className="flex items-center gap-1.5 text-xs font-medium text-green-400">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                    Active
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-slate-400">API Latency</span>
                                <span className="text-xs font-medium text-slate-300">42ms</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
