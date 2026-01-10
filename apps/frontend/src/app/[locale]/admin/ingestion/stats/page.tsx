'use client';

import { useState, useEffect } from 'react';

interface SourceStats {
    source: string;
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    total_fetched: number;
    total_new: number;
    total_updated: number;
    avg_duration_ms: number;
    success_rate: number;
}

interface OverallStats {
    total_logs: number;
    total_fetched: number;
    total_new: number;
    successful_runs: number;
    failed_runs: number;
    sources_active: number;
}

const SOURCE_COLORS: Record<string, string> = {
    pubmed: '#9333ea',
    uniprot: '#3b82f6',
    opentargets: '#06b6d4',
    hpa: '#14b8a6',
    chembl: '#f97316',
    pubchem: '#f59e0b',
    clinicaltrials: '#ec4899',
    openfda: '#ef4444',
};

export default function IngestionStatsPage() {
    const [overall, setOverall] = useState<OverallStats | null>(null);
    const [sourceStats, setSourceStats] = useState<SourceStats[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        setLoading(true);
        try {
            // Overall stats
            const overallRes = await fetch('/api/v1/ingestion/stats');
            if (overallRes.ok) {
                const data = await overallRes.json();
                setOverall(data);
            }

            // Per-source stats
            const sources = ['pubmed', 'uniprot', 'opentargets', 'hpa', 'chembl', 'pubchem', 'clinicaltrials', 'openfda'];
            const stats: SourceStats[] = [];

            for (const source of sources) {
                try {
                    const res = await fetch(`/api/v1/connectors/${source}/stats`);
                    if (res.ok) {
                        const data = await res.json();
                        const successRate = data.total_runs > 0
                            ? (data.successful_runs / data.total_runs * 100)
                            : 0;
                        stats.push({ source, ...data, success_rate: successRate });
                    }
                } catch {
                    // Skip if error
                }
            }

            setSourceStats(stats);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toLocaleString();
    };

    const formatDuration = (ms: number) => {
        if (!ms) return '—';
        if (ms < 1000) return `${Math.round(ms)}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-3xl font-bold text-gray-900 mb-8">📊 Ingestion Statistics</h1>
                    <div className="text-gray-500">Loading...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">📊 Ingestion Statistics</h1>
                    <button
                        onClick={fetchStats}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                    >
                        ↻ Refresh
                    </button>
                </div>

                {/* Overall Stats */}
                {overall && (
                    <div className="grid grid-cols-6 gap-4 mb-8">
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-blue-600">
                                {formatNumber(overall.total_fetched || 0)}
                            </div>
                            <div className="text-sm text-gray-500">Total Fetched</div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-green-600">
                                {formatNumber(overall.total_new || 0)}
                            </div>
                            <div className="text-sm text-gray-500">New Records</div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-gray-800">
                                {overall.total_logs || 0}
                            </div>
                            <div className="text-sm text-gray-500">Total Runs</div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-green-500">
                                {overall.successful_runs || 0}
                            </div>
                            <div className="text-sm text-gray-500">Successful</div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-red-500">
                                {overall.failed_runs || 0}
                            </div>
                            <div className="text-sm text-gray-500">Failed</div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm border p-6">
                            <div className="text-3xl font-bold text-purple-600">
                                {overall.sources_active || sourceStats.length}
                            </div>
                            <div className="text-sm text-gray-500">Active Sources</div>
                        </div>
                    </div>
                )}

                {/* Per-Source Stats */}
                <div className="bg-white rounded-xl shadow-sm border overflow-hidden mb-8">
                    <div className="px-6 py-4 border-b">
                        <h2 className="text-lg font-semibold">Source Performance</h2>
                    </div>
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                            <tr>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Source</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Runs</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Success Rate</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Fetched</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">New</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Updated</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Avg Duration</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {sourceStats.map((stat) => (
                                <tr key={stat.source} className="hover:bg-gray-50">
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div
                                                className="w-3 h-3 rounded-full"
                                                style={{ backgroundColor: SOURCE_COLORS[stat.source] || '#9ca3af' }}
                                            />
                                            <span className="font-medium">{stat.source}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="text-green-600">{stat.successful_runs}</span>
                                        <span className="text-gray-400"> / </span>
                                        <span className="text-red-600">{stat.failed_runs}</span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-green-500 rounded-full"
                                                    style={{ width: `${stat.success_rate}%` }}
                                                />
                                            </div>
                                            <span className="text-sm">{stat.success_rate.toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 font-mono">
                                        {formatNumber(stat.total_fetched)}
                                    </td>
                                    <td className="px-4 py-3 font-mono text-green-600">
                                        {formatNumber(stat.total_new)}
                                    </td>
                                    <td className="px-4 py-3 font-mono text-blue-600">
                                        {formatNumber(stat.total_updated)}
                                    </td>
                                    <td className="px-4 py-3 font-mono">
                                        {formatDuration(stat.avg_duration_ms)}
                                    </td>
                                </tr>
                            ))}
                            {sourceStats.length === 0 && (
                                <tr>
                                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                                        No statistics available
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Visual Chart (Simple Bar Chart) */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h2 className="text-lg font-semibold mb-4">Records by Source</h2>
                    <div className="space-y-3">
                        {sourceStats.map((stat) => {
                            const maxFetched = Math.max(...sourceStats.map(s => s.total_fetched), 1);
                            const widthPercent = (stat.total_fetched / maxFetched) * 100;

                            return (
                                <div key={stat.source} className="flex items-center gap-4">
                                    <div className="w-28 text-sm font-medium text-gray-700">
                                        {stat.source}
                                    </div>
                                    <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-500"
                                            style={{
                                                width: `${widthPercent}%`,
                                                backgroundColor: SOURCE_COLORS[stat.source] || '#9ca3af'
                                            }}
                                        />
                                    </div>
                                    <div className="w-20 text-right text-sm font-mono text-gray-600">
                                        {formatNumber(stat.total_fetched)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
