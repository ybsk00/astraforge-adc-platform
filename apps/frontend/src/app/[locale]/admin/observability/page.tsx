'use client';

import { useState, useEffect } from 'react';

interface MetricsData {
    by_source: Record<string, {
        total_runs: number;
        completed: number;
        failed: number;
        fetched: number;
        new: number;
        updated: number;
        errors: number;
        success_rate: number;
    }>;
    daily_trend: Array<{
        date: string;
        runs: number;
        completed: number;
        failed: number;
    }>;
    period_days: number;
    total_logs: number;
}

interface ErrorData {
    id: string;
    source: string;
    phase: string;
    created_at: string;
    error: string;
}

export default function ObservabilityPage() {
    const [metrics, setMetrics] = useState<MetricsData | null>(null);
    const [errors, setErrors] = useState<ErrorData[]>([]);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(7);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchData();
    }, [days]);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Metrics 조회
            const metricsRes = await fetch(`${ENGINE_URL}/api/v1/observability/metrics?days=${days}`);
            if (metricsRes.ok) {
                const data = await metricsRes.json();
                setMetrics(data);
            }

            // Errors 조회
            const errorsRes = await fetch(`${ENGINE_URL}/api/v1/observability/errors?limit=20`);
            if (errorsRes.ok) {
                const data = await errorsRes.json();
                setErrors(data.errors || []);
            }
        } catch (err) {
            console.error('Failed to fetch observability data:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-2xl font-bold text-gray-900 mb-8">📊 Observability</h1>
                    <div className="text-gray-500">Loading...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-2xl font-bold text-gray-900">📊 Observability Dashboard</h1>
                    <select
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                        className="border rounded-lg px-3 py-2"
                    >
                        <option value={7}>최근 7일</option>
                        <option value={14}>최근 14일</option>
                        <option value={30}>최근 30일</option>
                    </select>
                </div>

                {/* Summary Cards */}
                {metrics && (
                    <div className="grid grid-cols-4 gap-4 mb-8">
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                            <div className="text-sm text-gray-500">Total Runs</div>
                            <div className="text-2xl font-bold">{metrics.total_logs}</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4 shadow-sm border border-green-200">
                            <div className="text-sm text-green-600">Sources Active</div>
                            <div className="text-2xl font-bold text-green-700">
                                {Object.keys(metrics.by_source).length}
                            </div>
                        </div>
                        <div className="bg-blue-50 rounded-lg p-4 shadow-sm border border-blue-200">
                            <div className="text-sm text-blue-600">Documents Fetched</div>
                            <div className="text-2xl font-bold text-blue-700">
                                {Object.values(metrics.by_source).reduce((sum, s) => sum + s.fetched, 0)}
                            </div>
                        </div>
                        <div className="bg-red-50 rounded-lg p-4 shadow-sm border border-red-200">
                            <div className="text-sm text-red-600">Errors</div>
                            <div className="text-2xl font-bold text-red-700">
                                {Object.values(metrics.by_source).reduce((sum, s) => sum + s.errors, 0)}
                            </div>
                        </div>
                    </div>
                )}

                {/* Source Metrics Table */}
                {metrics && (
                    <div className="bg-white rounded-lg shadow-sm border mb-8">
                        <div className="px-4 py-3 border-b">
                            <h2 className="font-semibold text-gray-900">Source별 메트릭</h2>
                        </div>
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Source</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Runs</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Success</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Failed</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Fetched</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">New</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Rate</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {Object.entries(metrics.by_source).map(([source, stats]) => (
                                    <tr key={source} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 font-medium">{source}</td>
                                        <td className="px-4 py-3 text-right">{stats.total_runs}</td>
                                        <td className="px-4 py-3 text-right text-green-600">{stats.completed}</td>
                                        <td className="px-4 py-3 text-right text-red-600">{stats.failed}</td>
                                        <td className="px-4 py-3 text-right">{stats.fetched}</td>
                                        <td className="px-4 py-3 text-right text-blue-600">{stats.new}</td>
                                        <td className="px-4 py-3 text-right">
                                            <span className={`px-2 py-1 rounded text-xs ${stats.success_rate >= 90 ? 'bg-green-100 text-green-800' :
                                                    stats.success_rate >= 70 ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-red-100 text-red-800'
                                                }`}>
                                                {stats.success_rate}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Daily Trend Chart (Simple Bar) */}
                {metrics && metrics.daily_trend.length > 0 && (
                    <div className="bg-white rounded-lg shadow-sm border mb-8">
                        <div className="px-4 py-3 border-b">
                            <h2 className="font-semibold text-gray-900">일별 처리량 트렌드</h2>
                        </div>
                        <div className="p-4">
                            <div className="flex items-end gap-1 h-32">
                                {metrics.daily_trend.map((day, idx) => {
                                    const maxRuns = Math.max(...metrics.daily_trend.map(d => d.runs), 1);
                                    const height = (day.runs / maxRuns) * 100;
                                    const failedHeight = (day.failed / maxRuns) * 100;

                                    return (
                                        <div key={idx} className="flex-1 flex flex-col items-center">
                                            <div
                                                className="w-full bg-green-400 rounded-t"
                                                style={{ height: `${height - failedHeight}%` }}
                                                title={`${day.date}: ${day.completed} completed`}
                                            />
                                            {failedHeight > 0 && (
                                                <div
                                                    className="w-full bg-red-400"
                                                    style={{ height: `${failedHeight}%` }}
                                                    title={`${day.date}: ${day.failed} failed`}
                                                />
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="flex gap-1 mt-2">
                                {metrics.daily_trend.map((day, idx) => (
                                    <div key={idx} className="flex-1 text-center text-xs text-gray-500">
                                        {day.date.slice(5)} {/* MM-DD */}
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="px-4 pb-4 flex gap-4 text-sm">
                            <span className="flex items-center gap-1">
                                <span className="w-3 h-3 bg-green-400 rounded"></span> Completed
                            </span>
                            <span className="flex items-center gap-1">
                                <span className="w-3 h-3 bg-red-400 rounded"></span> Failed
                            </span>
                        </div>
                    </div>
                )}

                {/* Recent Errors */}
                <div className="bg-white rounded-lg shadow-sm border">
                    <div className="px-4 py-3 border-b flex justify-between items-center">
                        <h2 className="font-semibold text-gray-900">최근 오류 로그</h2>
                        <span className="text-sm text-gray-500">{errors.length}개</span>
                    </div>
                    <div className="divide-y">
                        {errors.length === 0 ? (
                            <div className="px-4 py-8 text-center text-gray-500">
                                오류가 없습니다 🎉
                            </div>
                        ) : (
                            errors.slice(0, 10).map((err) => (
                                <div key={err.id} className="px-4 py-3 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <span className="font-medium text-red-600">{err.source}</span>
                                            <span className="text-gray-400 mx-2">•</span>
                                            <span className="text-gray-500 text-sm">{err.phase}</span>
                                        </div>
                                        <span className="text-xs text-gray-400">
                                            {formatDate(err.created_at)}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-1 truncate">
                                        {err.error}
                                    </p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
