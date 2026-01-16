'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, type Component, type CatalogStats } from '@/lib/api';
import ComponentForm from './ComponentForm';
import Link from 'next/link';
import { Search, Plus, Target, Syringe, Link as LinkIcon, Pill, FlaskConical } from 'lucide-react';

const STATUS_BADGE: Record<string, { label: string; class: string }> = {
    pending_compute: { label: 'Processing', class: 'bg-blue-500/20 text-blue-400' },
    active: { label: 'Active', class: 'bg-green-500/20 text-green-400' },
    failed: { label: 'Failed', class: 'bg-red-500/20 text-red-400' },
    deprecated: { label: 'Deprecated', class: 'bg-slate-500/20 text-slate-400' },
};

const TYPE_CONFIG: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
    target: { icon: Target, color: 'text-red-400', bg: 'bg-red-500/20' },
    antibody: { icon: Syringe, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    linker: { icon: LinkIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    payload: { icon: Pill, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    conjugation: { icon: FlaskConical, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
};

const GRADE_BADGE: Record<string, { label: string; class: string }> = {
    gold: { label: 'Gold', class: 'bg-yellow-500/20 text-yellow-400' },
    silver: { label: 'Silver', class: 'bg-slate-400/20 text-slate-300' },
    bronze: { label: 'Bronze', class: 'bg-orange-500/20 text-orange-400' },
};

export default function ComponentList() {
    const [components, setComponents] = useState<Component[]>([]);
    const [stats, setStats] = useState<CatalogStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [typeFilter, setTypeFilter] = useState<string>('');
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [search, setSearch] = useState('');

    // Modal
    const [showForm, setShowForm] = useState(false);
    const [editComponent, setEditComponent] = useState<Component | undefined>();

    const loadComponents = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const [componentsData, statsData] = await Promise.all([
                api.getComponents({
                    type: typeFilter || undefined,
                    status: statusFilter || undefined,
                    search: search || undefined,
                }),
                api.getCatalogStats(),
            ]);

            setComponents(componentsData.items);
            setStats(statsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load components');
        } finally {
            setLoading(false);
        }
    }, [typeFilter, statusFilter, search]);

    useEffect(() => {
        loadComponents();
    }, [loadComponents]);

    const handleRetry = async (id: string) => {
        try {
            await api.retryComponent(id);
            loadComponents();
        } catch {
            alert('Failed to retry');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to deprecate this component?')) return;

        try {
            await api.deleteComponent(id);
            loadComponents();
        } catch {
            alert('Failed to delete');
        }
    };

    const handleFormSuccess = () => {
        setShowForm(false);
        setEditComponent(undefined);
        loadComponents();
    };

    const getScoreColor = (score?: number) => {
        if (score === undefined) return 'text-slate-500';
        if (score >= 90) return 'text-green-400';
        if (score >= 70) return 'text-blue-400';
        if (score >= 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">컴포넌트 카탈로그</h1>
                        <p className="text-slate-400 text-sm">
                            ADC를 구성하는 모든 생물학적 및 화학적 컴포넌트를 조회합니다.
                        </p>
                    </div>
                    <button
                        onClick={() => {
                            setEditComponent(undefined);
                            setShowForm(true);
                        }}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        + 새 컴포넌트 등록
                    </button>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                        {Object.entries(TYPE_CONFIG).map(([type, config]) => {
                            const IconComponent = config.icon;
                            return (
                                <div
                                    key={type}
                                    onClick={() => setTypeFilter(type === typeFilter ? '' : type)}
                                    className={`bg-slate-900 border rounded-xl p-4 cursor-pointer transition-all ${typeFilter === type
                                        ? 'border-blue-500 ring-1 ring-blue-500/50'
                                        : 'border-slate-800 hover:border-slate-700'
                                        }`}
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className={`p-2 rounded-lg ${config.bg}`}>
                                            <IconComponent className={`w-5 h-5 ${config.color}`} />
                                        </div>
                                        <span className="text-xs text-slate-500 uppercase">{type}</span>
                                    </div>
                                    <div className="text-2xl font-bold text-white">
                                        {stats.by_type[type] || 0}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="컴포넌트 이름 또는 SMILES로 검색..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">모든 상태</option>
                            {Object.entries(STATUS_BADGE).map(([status, config]) => (
                                <option key={status} value={status}>
                                    {config.label}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-6">
                        {error}
                    </div>
                )}

                {/* Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    {loading ? (
                        <div className="p-8 text-center text-slate-400">Loading...</div>
                    ) : components.length === 0 ? (
                        <div className="p-8 text-center text-slate-400">
                            컴포넌트가 없습니다. 첫 번째 컴포넌트를 등록하세요!
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="border-b border-slate-800">
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                Type
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                Name
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                Grade
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                Score
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                Status
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                                SMILES
                                            </th>
                                            <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">
                                                Actions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800">
                                        {components.map((component) => {
                                            const typeConfig = TYPE_CONFIG[component.type] || TYPE_CONFIG.target;
                                            const IconComponent = typeConfig.icon;
                                            const score = component.properties?.score as number | undefined;

                                            return (
                                                <tr key={component.id} className="hover:bg-slate-800/50 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-2">
                                                            <div className={`p-1.5 rounded ${typeConfig.bg}`}>
                                                                <IconComponent className={`w-4 h-4 ${typeConfig.color}`} />
                                                            </div>
                                                            <span className="text-xs text-slate-400 capitalize">{component.type}</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <Link
                                                            href={`/catalog/${component.id}`}
                                                            className="text-white font-medium hover:text-blue-400 transition-colors"
                                                        >
                                                            {component.name}
                                                        </Link>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        {component.quality_grade && GRADE_BADGE[component.quality_grade] && (
                                                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${GRADE_BADGE[component.quality_grade].class}`}>
                                                                {GRADE_BADGE[component.quality_grade].label}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`font-medium ${getScoreColor(score)}`}>
                                                            {score !== undefined ? `${score}%` : '-'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span
                                                            className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${STATUS_BADGE[component.status]?.class}`}
                                                        >
                                                            {STATUS_BADGE[component.status]?.label}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 font-mono text-xs text-slate-500 max-w-[200px] truncate">
                                                        {(component.properties?.smiles as string) || '-'}
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <div className="flex gap-3 justify-end">
                                                            {component.status === 'failed' && (
                                                                <button
                                                                    onClick={() => handleRetry(component.id)}
                                                                    className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
                                                                >
                                                                    Retry
                                                                </button>
                                                            )}
                                                            <button
                                                                onClick={() => {
                                                                    setEditComponent(component);
                                                                    setShowForm(true);
                                                                }}
                                                                className="text-slate-400 hover:text-white text-sm transition-colors"
                                                            >
                                                                Edit
                                                            </button>
                                                            {component.status !== 'deprecated' && (
                                                                <button
                                                                    onClick={() => handleDelete(component.id)}
                                                                    className="text-red-400 hover:text-red-300 text-sm transition-colors"
                                                                >
                                                                    Delete
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                                <div className="text-sm text-slate-400">
                                    {components.length}개 컴포넌트 표시 중
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* Modal */}
                {showForm && (
                    <ComponentForm
                        component={editComponent}
                        onSuccess={handleFormSuccess}
                        onCancel={() => {
                            setShowForm(false);
                            setEditComponent(undefined);
                        }}
                    />
                )}
            </div>
        </div>
    );
}
