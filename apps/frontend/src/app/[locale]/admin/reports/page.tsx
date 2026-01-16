'use client';

import { useState, useEffect } from 'react';
import { getReports } from '@/lib/actions/admin';
import {
    RefreshCw,
    FileText,
    Download,
    Search,
    Filter,
    Loader2,
    Calendar,
    BarChart3,
    ExternalLink,
    Activity
} from 'lucide-react';
import { useTranslations } from 'next-intl';

interface Report {
    id: string;
    run_id: string;
    report_json: Record<string, unknown>;
    claim_evidence_rate: number;
    assumption_count: number;
    created_at: string;
    design_runs: {
        run_type: string;
        created_at: string;
    } | null;
}

export default function ReportsPage() {
    const t = useTranslations('Admin.reports');
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchReports = async () => {
        try {
            const data = await getReports();
            setReports(data as Report[]);
        } catch (err) {
            console.error('Failed to fetch reports:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []);

    if (loading && reports.length === 0) {
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
                        <h1 className="text-2xl font-bold text-white mb-1">{t('title')}</h1>
                        <p className="text-slate-400 text-sm">{t('subtitle')}</p>
                    </div>
                    <button
                        onClick={fetchReports}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        {t('refresh')}
                    </button>
                </div>

                {/* Filters/Search (Placeholder) */}
                <div className="flex flex-wrap gap-4 mb-6">
                    <div className="flex-1 min-w-[200px] relative">
                        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                            type="text"
                            placeholder={t('search')}
                            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    <button className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-400 flex items-center gap-2 hover:bg-slate-800 transition-colors">
                        <Filter className="w-4 h-4" />
                        {t('filter')}
                    </button>
                </div>

                {/* Reports Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {reports.length > 0 ? (
                        reports.map((report) => (
                            <div key={report.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all group">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-blue-500/10 rounded-xl group-hover:bg-blue-500/20 transition-colors">
                                        <FileText className="w-6 h-6 text-blue-400" />
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                                            <ExternalLink className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                <h3 className="text-lg font-semibold text-white mb-1">
                                    {report.design_runs?.run_type || 'Design Report'}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-slate-500 mb-4">
                                    <Calendar className="w-3.5 h-3.5" />
                                    {new Date(report.created_at).toLocaleDateString()}
                                </div>

                                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                                    <div>
                                        <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">{t('claimEvidence')}</div>
                                        <div className="flex items-center gap-2">
                                            <BarChart3 className="w-4 h-4 text-green-400" />
                                            <span className="text-sm font-bold text-white">
                                                {(report.claim_evidence_rate * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">{t('assumptions')}</div>
                                        <div className="flex items-center gap-2">
                                            <Activity className="w-4 h-4 text-amber-400" />
                                            <span className="text-sm font-bold text-white">
                                                {report.assumption_count}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-20 text-center">
                            <div className="inline-flex p-4 bg-slate-900 rounded-full mb-4">
                                <FileText className="w-8 h-8 text-slate-700" />
                            </div>
                            <h3 className="text-white font-medium">{t('noReports')}</h3>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
