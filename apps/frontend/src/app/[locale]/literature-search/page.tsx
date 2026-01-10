'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Search, Filter, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { Link } from '@/i18n/routing';

interface Component {
    id: string;
    type: string;
    name: string;
    quality_grade: string;
    status: string;
    properties?: Record<string, unknown>;
    created_at: string;
}

interface SearchResult {
    items: Component[];
    total: number;
    limit: number;
    offset: number;
}

const TYPE_LABELS: Record<string, string> = {
    target: 'Target',
    antibody: 'Antibody',
    linker: 'Linker',
    payload: 'Payload',
    conjugation: 'Conjugation',
};

const GRADE_BADGE: Record<string, { label: string; class: string }> = {
    gold: { label: 'Gold', class: 'bg-yellow-500/20 text-yellow-400' },
    silver: { label: 'Silver', class: 'bg-slate-400/20 text-slate-300' },
    bronze: { label: 'Bronze', class: 'bg-orange-500/20 text-orange-400' },
};

const STATUS_BADGE: Record<string, { label: string; class: string }> = {
    active: { label: 'Active', class: 'bg-green-500/20 text-green-400' },
    pending_compute: { label: 'Pending', class: 'bg-blue-500/20 text-blue-400' },
    failed: { label: 'Failed', class: 'bg-red-500/20 text-red-400' },
    deprecated: { label: 'Deprecated', class: 'bg-slate-500/20 text-slate-400' },
};

export default function LiteratureSearchPage() {
    const t = useTranslations('LiteratureSearch');
    const [searchQuery, setSearchQuery] = useState('');
    const [submittedQuery, setSubmittedQuery] = useState('');
    const [typeFilter, setTypeFilter] = useState<string>('');
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [results, setResults] = useState<SearchResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(0);
    const limit = 20;

    const fetchResults = useCallback(async () => {
        if (!submittedQuery && !typeFilter && !statusFilter) {
            setResults(null);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();
            if (submittedQuery) params.append('search', submittedQuery);
            if (typeFilter) params.append('type', typeFilter);
            if (statusFilter) params.append('status', statusFilter);
            params.append('limit', limit.toString());
            params.append('offset', (page * limit).toString());

            const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v1/catalog/components?${params}`);

            if (!response.ok) {
                throw new Error('Search error');
            }

            const data = await response.json();
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search error');
        } finally {
            setLoading(false);
        }
    }, [submittedQuery, typeFilter, statusFilter, page]);

    useEffect(() => {
        fetchResults();
    }, [fetchResults]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(0);
        setSubmittedQuery(searchQuery);
    };

    const totalPages = results ? Math.ceil(results.total / limit) : 0;

    return (
        <div className="min-h-screen bg-slate-950 ml-64 py-8 px-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {t('title')}
                    </h1>
                    <p className="text-slate-400">
                        {t('subtitle')}
                    </p>
                </div>

                {/* Search Form */}
                <form onSubmit={handleSearch} className="mb-6">
                    <div className="flex gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder={t('searchPlaceholder')}
                                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-12 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <button
                            type="submit"
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                        >
                            {t('search')}
                        </button>
                    </div>
                </form>

                {/* Filters */}
                <div className="flex gap-4 mb-6">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-400 text-sm">Filter:</span>
                    </div>
                    <select
                        value={typeFilter}
                        onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">{t('allTypes')}</option>
                        <option value="target">Target</option>
                        <option value="antibody">Antibody</option>
                        <option value="linker">Linker</option>
                        <option value="payload">Payload</option>
                        <option value="conjugation">Conjugation</option>
                    </select>
                    <select
                        value={statusFilter}
                        onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">{t('allStatus')}</option>
                        <option value="active">Active</option>
                        <option value="pending_compute">Pending</option>
                        <option value="failed">Failed</option>
                    </select>
                </div>

                {/* Results */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl">
                    {loading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                            <span className="ml-2 text-slate-400">{t('searching')}</span>
                        </div>
                    ) : error ? (
                        <div className="text-center py-20">
                            <p className="text-red-400">{error}</p>
                        </div>
                    ) : !results ? (
                        <div className="text-center py-20">
                            <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                            <p className="text-slate-400">{t('searchPlaceholder')}</p>
                        </div>
                    ) : results.items.length === 0 ? (
                        <div className="text-center py-20">
                            <p className="text-slate-400">{t('noResults')}</p>
                        </div>
                    ) : (
                        <>
                            {/* Results Header */}
                            <div className="px-6 py-4 border-b border-slate-700">
                                <p className="text-slate-300">
                                    {t('results', { count: results.total })}
                                </p>
                            </div>

                            {/* Results Table */}
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-slate-700">
                                            <th className="text-left px-6 py-3 text-slate-400 text-sm font-medium">Type</th>
                                            <th className="text-left px-6 py-3 text-slate-400 text-sm font-medium">Name</th>
                                            <th className="text-left px-6 py-3 text-slate-400 text-sm font-medium">Grade</th>
                                            <th className="text-left px-6 py-3 text-slate-400 text-sm font-medium">Status</th>
                                            <th className="text-left px-6 py-3 text-slate-400 text-sm font-medium">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {results.items.map((item) => (
                                            <tr key={item.id} className="border-b border-slate-700/50 hover:bg-slate-800/50">
                                                <td className="px-6 py-4">
                                                    <span className="text-slate-300">{TYPE_LABELS[item.type] || item.type}</span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <Link
                                                        href={`/catalog/${item.id}`}
                                                        className="text-blue-400 hover:text-blue-300 font-medium"
                                                    >
                                                        {item.name}
                                                    </Link>
                                                </td>
                                                <td className="px-6 py-4">
                                                    {item.quality_grade && GRADE_BADGE[item.quality_grade] && (
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${GRADE_BADGE[item.quality_grade].class}`}>
                                                            {GRADE_BADGE[item.quality_grade].label}
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4">
                                                    {STATUS_BADGE[item.status] && (
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_BADGE[item.status].class}`}>
                                                            {STATUS_BADGE[item.status].label}
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-slate-400 text-sm">
                                                    {new Date(item.created_at).toLocaleDateString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700">
                                    <button
                                        onClick={() => setPage(p => Math.max(0, p - 1))}
                                        disabled={page === 0}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                        {t('previous')}
                                    </button>
                                    <span className="text-slate-400 text-sm">
                                        {page + 1} / {totalPages}
                                    </span>
                                    <button
                                        onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                                        disabled={page >= totalPages - 1}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {t('next')}
                                        <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
