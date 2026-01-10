'use client';

import { useTranslations } from 'next-intl';

export default function AdminDashboardPage() {
    const t = useTranslations('Common');

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-blue-400 mb-1">Admin Dashboard</h1>
                    <p className="text-sm text-slate-400">Welcome to the administration area.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-2">{t('menu.connectors')}</h3>
                        <p className="text-slate-400 text-sm">Manage external data connectors and integrations.</p>
                    </div>

                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-2">{t('menu.ingestion')}</h3>
                        <p className="text-slate-400 text-sm">Monitor data ingestion pipelines and logs.</p>
                    </div>

                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-2">{t('menu.observability')}</h3>
                        <p className="text-slate-400 text-sm">System health metrics and performance monitoring.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
