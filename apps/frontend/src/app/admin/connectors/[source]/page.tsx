'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface ConnectorDetail {
    source: string;
    name: string;
    description: string;
    category: string;
    rate_limit: string;
    cursors: any[];
    recent_logs: any[];
}

interface LogEntry {
    id: string;
    phase: string;
    status: string;
    duration_ms: number;
    records_fetched: number;
    records_new: number;
    records_updated: number;
    error_message: string | null;
    created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
    idle: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
    started: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
};

export default function ConnectorDetailPage() {
    const params = useParams();
    const router = useRouter();
    const source = params.source as string;

    const [detail, setDetail] = useState<ConnectorDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [runQuery, setRunQuery] = useState('');
    const [running, setRunning] = useState(false);

    // Engine API base URL
    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchDetail = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/connectors/${source}`);
            if (!res.ok) throw new Error('Failed to fetch');
            const data = await res.json();
            setDetail(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDetail();
        const interval = setInterval(fetchDetail, 10000);
        return () => clearInterval(interval);
    }, [source]);

    const handleRun = async () => {
        setRunning(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/connectors/${source}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: runQuery, limit: 50 }),
            });

            if (!res.ok) throw new Error('Failed to run');

            await fetchDetail();
            setRunQuery('');
        } catch (err) {
            alert('Failed to run connector');
        } finally {
            setRunning(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString('ko-KR');
    };

    const formatDuration = (ms: number) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-6xl mx-auto">
                    <div className="text-gray-500">Loading...</div>
                </div>
            </div>
        );
    }

    if (!detail) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-6xl mx-auto">
                    <div className="text-red-500">Connector not found</div>
                </div>
            </div>
        );
    }

    const latestCursor = detail.cursors?.[0];

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button
                        onClick={() => router.push('/admin/connectors')}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        ← Back
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">{detail.name}</h1>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[latestCursor?.status || 'idle']}`}>
                        {latestCursor?.status || 'idle'}
                    </span>
                </div>

                {/* Info Cards */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                        <div className="text-sm text-gray-500">Category</div>
                        <div className="text-lg font-semibold">{detail.category}</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                        <div className="text-sm text-gray-500">Rate Limit</div>
                        <div className="text-lg font-semibold">{detail.rate_limit}</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                        <div className="text-sm text-gray-500">Total Fetched</div>
                        <div className="text-lg font-semibold">
                            {latestCursor?.stats?.fetched?.toLocaleString() || 0}
                        </div>
                    </div>
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                        <div className="text-sm text-gray-500">Last Success</div>
                        <div className="text-lg font-semibold">
                            {latestCursor?.last_success_at
                                ? formatDate(latestCursor.last_success_at).split(' ')[0]
                                : '—'}
                        </div>
                    </div>
                </div>

                {/* Run Form */}
                <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
                    <h2 className="text-lg font-semibold mb-4">Run Connector</h2>
                    <div className="flex gap-4">
                        <input
                            type="text"
                            value={runQuery}
                            onChange={(e) => setRunQuery(e.target.value)}
                            placeholder="Query (optional)"
                            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={handleRun}
                            disabled={running}
                            className="px-6 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 disabled:bg-blue-300 transition"
                        >
                            {running ? 'Running...' : 'Run'}
                        </button>
                    </div>
                    {latestCursor?.error_message && (
                        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                            ⚠️ Last error: {latestCursor.error_message}
                        </div>
                    )}
                </div>

                {/* Recent Logs */}
                <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                    <div className="px-6 py-4 border-b">
                        <h2 className="text-lg font-semibold">Recent Logs</h2>
                    </div>
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                            <tr>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Time</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Phase</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Duration</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Fetched</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">New</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Updated</th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Error</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {detail.recent_logs?.map((log: LogEntry) => (
                                <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {formatDate(log.created_at)}
                                    </td>
                                    <td className="px-4 py-3 text-sm">{log.phase}</td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[log.status] || 'bg-gray-100'}`}>
                                            {log.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                        {log.duration_ms ? formatDuration(log.duration_ms) : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-sm">{log.records_fetched || 0}</td>
                                    <td className="px-4 py-3 text-sm text-green-600">{log.records_new || 0}</td>
                                    <td className="px-4 py-3 text-sm text-blue-600">{log.records_updated || 0}</td>
                                    <td className="px-4 py-3 text-sm text-red-500 truncate max-w-xs" title={log.error_message || ''}>
                                        {log.error_message || '—'}
                                    </td>
                                </tr>
                            ))}
                            {(!detail.recent_logs || detail.recent_logs.length === 0) && (
                                <tr>
                                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                                        No logs yet
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
