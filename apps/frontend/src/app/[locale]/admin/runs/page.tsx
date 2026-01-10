'use client';

import { useState, useEffect } from 'react';
import { getDesignRuns } from '@/lib/actions/admin';
import {
    RefreshCw,
    Clock,
    Loader2,
    CheckCircle2,
    AlertCircle,
    Play,
    History,
    User,
    Layers
} from 'lucide-react';

interface DesignRun {
    id: string;
    run_type: string;
    status: string;
    progress: number;
    created_at: string;
    profiles: {
        name: string;
        email: string;
    } | null;
}

const STATUS_CONFIG: Record<string, { label: string; icon: any; class: string; color: string }> = {
    queued: { label: 'Queued', icon: Clock, class: 'bg-amber-500/20 text-amber-400', color: 'text-amber-400' },
    running: { label: 'Running', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    retrieving: { label: 'Retrieving', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    structuring: { label: 'Structuring', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    writing: { label: 'Writing', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    qa: { label: 'QA Review', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    rendering: { label: 'Rendering', icon: Loader2, class: 'bg-blue-500/20 text-blue-400', color: 'text-blue-400' },
    done: { label: 'Completed', icon: CheckCircle2, class: 'bg-green-500/20 text-green-400', color: 'text-green-400' },
    failed: { label: 'Failed', icon: AlertCircle, class: 'bg-red-500/20 text-red-400', color: 'text-red-400' },
};

export default function RunsPage() {
    const [runs, setRuns] = useState<DesignRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchRuns = async () => {
        try {
            const data = await getDesignRuns();
            setRuns(data as any);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch runs');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRuns();
        const interval = setInterval(fetchRuns, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading && runs.length === 0) {
        return (
            <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Design Runs</h1>
                        <p className="text-slate-400 text-sm">Monitor and manage all report generation processes.</p>
                    </div>
                    <button
                        onClick={fetchRuns}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>

                {/* Runs Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Run Info</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Creator</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Progress</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Created At</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {runs.length > 0 ? (
                                    runs.map((run) => {
                                        const statusConfig = STATUS_CONFIG[run.status] || STATUS_CONFIG.queued;
                                        const StatusIcon = statusConfig.icon;

                                        return (
                                            <tr key={run.id} className="hover:bg-slate-800/30 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 bg-slate-800 rounded-lg">
                                                            <Layers className="w-4 h-4 text-blue-400" />
                                                        </div>
                                                        <div>
                                                            <div className="text-sm font-medium text-white">{run.run_type}</div>
                                                            <div className="text-[10px] text-slate-500 font-mono">{run.id.slice(0, 8)}...</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-2">
                                                        <User className="w-4 h-4 text-slate-500" />
                                                        <div>
                                                            <div className="text-sm text-slate-300">{run.profiles?.name || 'Unknown'}</div>
                                                            <div className="text-xs text-slate-500">{run.profiles?.email}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.class}`}>
                                                        <StatusIcon className={`w-3 h-3 ${run.status !== 'done' && run.status !== 'failed' && run.status !== 'queued' ? 'animate-spin' : ''}`} />
                                                        {statusConfig.label}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="w-full max-w-[100px]">
                                                        <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                                                            <span>{run.progress}%</span>
                                                        </div>
                                                        <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full transition-all duration-500 ${statusConfig.color.replace('text-', 'bg-')}`}
                                                                style={{ width: `${run.progress}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-500">
                                                    {new Date(run.created_at).toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                                                        <History className="w-4 h-4" />
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })
                                ) : (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 text-sm">
                                            No design runs found.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
