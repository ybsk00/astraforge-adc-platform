'use client';

import { useState, useEffect } from 'react';
import {
    RefreshCw,
    Check,
    X,
    Clock,
    Target,
    Syringe,
    Link as LinkIcon,
    Pill,
    FlaskConical
} from 'lucide-react';

interface StagingComponent {
    id: string;
    type: string;
    name: string;
    properties: Record<string, unknown>;
    quality_grade: string;
    source: {
        source?: string;
        external_id?: string;
        fetched_at?: string;
    };
    status: 'pending' | 'approved' | 'rejected';
    review_note: string | null;
    created_at: string;
}

interface StagingStats {
    total: number;
    by_status: {
        pending: number;
        approved: number;
        rejected: number;
    };
    by_type: Record<string, number>;
}

type LucideIcon = React.ComponentType<{ className?: string }>;

const TYPE_CONFIG: Record<string, { icon: LucideIcon; color: string; bg: string }> = {
    target: { icon: Target, color: 'text-red-400', bg: 'bg-red-500/20' },
    antibody: { icon: Syringe, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    linker: { icon: LinkIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    payload: { icon: Pill, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    conjugation: { icon: FlaskConical, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
};

const STATUS_CONFIG = {
    pending: { label: 'Pending', class: 'bg-yellow-500/20 text-yellow-400', icon: Clock },
    approved: { label: 'Approved', class: 'bg-green-500/20 text-green-400', icon: Check },
    rejected: { label: 'Rejected', class: 'bg-red-500/20 text-red-400', icon: X },
};

const GRADE_CONFIG: Record<string, { label: string; class: string }> = {
    gold: { label: 'Gold', class: 'bg-yellow-500/20 text-yellow-400' },
    silver: { label: 'Silver', class: 'bg-slate-400/20 text-slate-300' },
    bronze: { label: 'Bronze', class: 'bg-orange-500/20 text-orange-400' },
};

export default function StagingPage() {
    const [components, setComponents] = useState<StagingComponent[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [filterType, setFilterType] = useState<string>('');
    const [filterStatus, setFilterStatus] = useState<string>('pending');
    const [stats, setStats] = useState<StagingStats | null>(null);

    const fetchComponents = async () => {
        try {
            const params = new URLSearchParams();
            if (filterType) params.append('type', filterType);
            if (filterStatus) params.append('status', filterStatus);

            const res = await fetch(`/api/v1/staging/components?${params}`);
            if (!res.ok) throw new Error('Failed to fetch staging components');
            const data = await res.json();
            setComponents(data.items || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const res = await fetch('/api/v1/staging/stats');
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats', err);
        }
    };

    useEffect(() => {
        fetchComponents();
        fetchStats();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filterType, filterStatus]);

    const handleApprove = async (id: string) => {
        try {
            const res = await fetch(`/api/v1/staging/components/${id}/approve`, { method: 'POST' });
            if (!res.ok) throw new Error('Failed to approve');
            await fetchComponents();
            await fetchStats();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to approve');
        }
    };

    const handleReject = async (id: string) => {
        const note = prompt('거절 사유를 입력하세요 (선택):');
        try {
            const res = await fetch(`/api/v1/staging/components/${id}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ review_note: note }),
            });
            if (!res.ok) throw new Error('Failed to reject');
            await fetchComponents();
            await fetchStats();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to reject');
        }
    };

    const handleBulkApprove = async () => {
        if (selectedIds.size === 0) {
            alert('선택된 항목이 없습니다');
            return;
        }
        if (!confirm(`${selectedIds.size}개 항목을 승인하시겠습니까?`)) return;

        try {
            const res = await fetch('/api/v1/staging/components/bulk/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: Array.from(selectedIds) }),
            });
            if (!res.ok) throw new Error('Failed to bulk approve');
            const result = await res.json();
            alert(`승인: ${result.approved}개, 실패: ${result.failed}개`);
            setSelectedIds(new Set());
            await fetchComponents();
            await fetchStats();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to bulk approve');
        }
    };

    const toggleSelect = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) newSelected.delete(id);
        else newSelected.add(id);
        setSelectedIds(newSelected);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === components.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(components.map(c => c.id)));
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center">
                <div className="text-slate-400">Loading...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">스테이징 승인</h1>
                        <p className="text-slate-400 text-sm">수집된 컴포넌트를 검토하고 카탈로그에 승인합니다.</p>
                    </div>
                    <div className="flex gap-3">
                        {selectedIds.size > 0 && (
                            <button
                                onClick={handleBulkApprove}
                                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                            >
                                <Check className="w-4 h-4" />
                                선택 승인 ({selectedIds.size})
                            </button>
                        )}
                        <button
                            onClick={() => { fetchComponents(); fetchStats(); }}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" />
                            새로고침
                        </button>
                    </div>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-yellow-500/20 rounded-lg">
                                    <Clock className="w-5 h-5 text-yellow-400" />
                                </div>
                                <span className="text-sm text-slate-400">Pending</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_status?.pending || 0}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-green-500/20 rounded-lg">
                                    <Check className="w-5 h-5 text-green-400" />
                                </div>
                                <span className="text-sm text-slate-400">Approved</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_status?.approved || 0}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-red-500/20 rounded-lg">
                                    <X className="w-5 h-5 text-red-400" />
                                </div>
                                <span className="text-sm text-slate-400">Rejected</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_status?.rejected || 0}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="text-sm text-slate-400 mb-2">Total</div>
                            <div className="text-3xl font-bold text-white">{stats.total || 0}</div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 flex flex-col md:flex-row gap-4">
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="approved">Approved</option>
                        <option value="rejected">Rejected</option>
                    </select>

                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Types</option>
                        <option value="target">Target</option>
                        <option value="antibody">Antibody</option>
                        <option value="linker">Linker</option>
                        <option value="payload">Payload</option>
                        <option value="conjugation">Conjugation</option>
                    </select>
                </div>

                {/* Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-800">
                                    <th className="px-6 py-4">
                                        <input
                                            type="checkbox"
                                            checked={selectedIds.size === components.length && components.length > 0}
                                            onChange={toggleSelectAll}
                                            className="rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500"
                                        />
                                    </th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Type</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Name</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Grade</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Source</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Created</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {components.map((comp) => {
                                    const typeConfig = TYPE_CONFIG[comp.type] || TYPE_CONFIG.target;
                                    const TypeIcon = typeConfig.icon;
                                    const statusConfig = STATUS_CONFIG[comp.status];
                                    const StatusIcon = statusConfig.icon;

                                    return (
                                        <tr key={comp.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedIds.has(comp.id)}
                                                    onChange={() => toggleSelect(comp.id)}
                                                    className="rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500"
                                                />
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <div className={`p-1.5 rounded ${typeConfig.bg}`}>
                                                        <TypeIcon className={`w-4 h-4 ${typeConfig.color}`} />
                                                    </div>
                                                    <span className="text-xs text-slate-400 capitalize">{comp.type}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-white font-medium">{comp.name}</td>
                                            <td className="px-6 py-4">
                                                {comp.quality_grade && GRADE_CONFIG[comp.quality_grade] && (
                                                    <span className={`px-2 py-1 rounded text-xs font-medium ${GRADE_CONFIG[comp.quality_grade].class}`}>
                                                        {GRADE_CONFIG[comp.quality_grade].label}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {comp.source?.source || '—'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.class}`}>
                                                    <StatusIcon className="w-3 h-3" />
                                                    {statusConfig.label}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {formatDate(comp.created_at)}
                                            </td>
                                            <td className="px-6 py-4">
                                                {comp.status === 'pending' && (
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleApprove(comp.id)}
                                                            className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white text-xs rounded transition-colors flex items-center gap-1"
                                                        >
                                                            <Check className="w-3 h-3" /> 승인
                                                        </button>
                                                        <button
                                                            onClick={() => handleReject(comp.id)}
                                                            className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs rounded transition-colors flex items-center gap-1"
                                                        >
                                                            <X className="w-3 h-3" /> 거절
                                                        </button>
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                                {components.length === 0 && (
                                    <tr>
                                        <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                                            No components found
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
