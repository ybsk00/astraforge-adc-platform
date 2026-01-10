'use client';

import { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, Loader2 } from 'lucide-react';

interface QualityIssue {
    id: string;
    type: string;
    description: string;
    severity: string;
    status: string;
    evidence_id: string;
    created_at: string;
}

export default function EvidenceQualityPage() {
    const [issues, setIssues] = useState<QualityIssue[]>([]);
    const [loading, setLoading] = useState(true);

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchIssues = useCallback(async () => {
        try {
            const response = await fetch(`${apiUrl}/api/v1/evidence/quality/issues`);
            if (response.ok) {
                const data = await response.json();
                setIssues(data);
            }
        } catch (err) {
            console.error('Failed to fetch quality issues:', err);
        } finally {
            setLoading(false);
        }
    }, [apiUrl]);

    useEffect(() => {
        fetchIssues();
    }, [fetchIssues]);

    const handleResolve = async (issueId: string) => {
        try {
            const response = await fetch(`${apiUrl}/api/v1/evidence/quality/resolve?issue_id=${issueId}&resolution=manual_fix`, {
                method: 'POST'
            });
            if (response.ok) {
                fetchIssues();
            }
        } catch (err) {
            console.error('Failed to resolve issue:', err);
        }
    };

    const getSeverityBadge = (severity: string) => {
        switch (severity) {
            case 'high': return 'bg-red-500/20 text-red-400';
            case 'medium': return 'bg-yellow-500/20 text-yellow-400';
            case 'low': return 'bg-blue-500/20 text-blue-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    const stats = {
        conflicts: issues.filter(i => i.type === 'conflict').length,
        missing: issues.filter(i => i.type === 'missing_citation').length,
        negative: issues.filter(i => i.type === 'retracted').length,
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
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">근거 품질 및 충돌 관리</h1>
                    <p className="text-slate-400">Forced Evidence, Conflict Alert, Negative Signals 등을 모니터링하고 해결합니다.</p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertTriangle className="w-6 h-6 text-red-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">{stats.conflicts}</div>
                            <div className="text-sm text-slate-400">Conflicts Detected</div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center">
                            <HelpCircle className="w-6 h-6 text-yellow-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">{stats.missing}</div>
                            <div className="text-sm text-slate-400">Missing Citations</div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-blue-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">{stats.negative}</div>
                            <div className="text-sm text-slate-400">Negative Signals</div>
                        </div>
                    </div>
                </div>

                {/* Issues List */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">품질 이슈 목록</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Evidence ID</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Issue Type</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Severity</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Created At</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {issues.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                                        No quality issues found.
                                    </td>
                                </tr>
                            ) : (
                                issues.map((issue) => (
                                    <tr key={issue.id} className="hover:bg-slate-800/50">
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-medium text-white">{issue.evidence_id || '-'}</div>
                                            <div className="text-xs text-slate-500">{issue.description}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-slate-300 capitalize">{issue.type.replace('_', ' ')}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`text-xs px-2 py-1 rounded ${getSeverityBadge(issue.severity)} uppercase`}>
                                                {issue.severity}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-500">
                                            {new Date(issue.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            {issue.status === 'open' ? (
                                                <button
                                                    onClick={() => handleResolve(issue.id)}
                                                    className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                                                >
                                                    Resolve
                                                </button>
                                            ) : (
                                                <span className="text-green-500 text-sm">Resolved</span>
                                            )}
                                        </td>
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
