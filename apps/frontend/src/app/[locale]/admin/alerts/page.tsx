'use client';

import { useState, useEffect } from 'react';
import { getAlerts } from '@/lib/actions/admin';
import {
    Bell,
    AlertTriangle,
    Info,
    XCircle,
    CheckCircle2,
    Search,
    MoreVertical,
    Trash2,
    CheckCircle,
    RefreshCw
} from 'lucide-react';
import { useTranslations } from 'next-intl';

interface Alert {
    id: string;
    type: 'error' | 'warning' | 'info' | 'success';
    source: string;
    message: string;
    created_at: string;
    is_read: boolean;
}

export default function AlertsPage() {
    const t = useTranslations('Admin.alerts');
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const data = await getAlerts();
            setAlerts(data as Alert[]);
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredAlerts = alerts.filter(alert => {
        const matchesFilter = filter === 'all' || alert.type === filter;
        const matchesSearch = alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
            alert.source.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    const stats = {
        total: alerts.length,
        unread: alerts.filter(a => !a.is_read).length,
        error: alerts.filter(a => a.type === 'error').length,
        warning: alerts.filter(a => a.type === 'warning').length
    };

    if (loading && alerts.length === 0) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                            <Bell className="w-6 h-6 text-yellow-400" />
                            {t('title')}
                        </h1>
                        <p className="text-slate-400 text-sm">{t('subtitle')}</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchData}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            {t('refresh')}
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm">
                            <CheckCircle className="w-4 h-4" />
                            {t('markRead')}
                        </button>
                    </div>
                </div>

                {/* Stats Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-slate-400 text-xs font-medium mb-1">Total Alerts</div>
                        <div className="text-xl font-bold text-white">{stats.total}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-red-400 text-xs font-medium mb-1">{t('error')}</div>
                        <div className="text-xl font-bold text-white">{stats.error}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-yellow-400 text-xs font-medium mb-1">{t('warning')}</div>
                        <div className="text-xl font-bold text-white">{stats.warning}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-blue-400 text-xs font-medium mb-1">{t('unread')}</div>
                        <div className="text-xl font-bold text-white">{stats.unread}</div>
                    </div>
                </div>

                {/* Filters & Search */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder={t('search')}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div className="flex gap-2">
                        {(['all', 'error', 'warning', 'info'] as const).map((filterType) => (
                            <button
                                key={filterType}
                                onClick={() => setFilter(filterType)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === filterType
                                    ? 'bg-slate-800 text-white border border-slate-700'
                                    : 'text-slate-400 hover:text-white'
                                    }`}
                            >
                                {t(filterType)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Alerts List */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="divide-y divide-slate-800">
                        {filteredAlerts.length === 0 ? (
                            <div className="p-12 text-center">
                                <div className="w-12 h-12 bg-slate-950 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle2 className="w-6 h-6 text-slate-600" />
                                </div>
                                <h3 className="text-white font-medium mb-1">{t('noAlerts')}</h3>
                            </div>
                        ) : (
                            filteredAlerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className={`p-4 flex gap-4 hover:bg-slate-800/30 transition-colors ${!alert.is_read ? 'bg-blue-500/5' : ''}`}
                                >
                                    <div className={`mt-1 p-2 rounded-lg shrink-0 ${alert.type === 'error' ? 'bg-red-500/10 text-red-500' :
                                        alert.type === 'warning' ? 'bg-yellow-500/10 text-yellow-500' :
                                            'bg-blue-500/10 text-blue-500'
                                        }`}>
                                        {alert.type === 'error' ? <XCircle className="w-5 h-5" /> :
                                            alert.type === 'warning' ? <AlertTriangle className="w-5 h-5" /> :
                                                <Info className="w-5 h-5" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2 mb-1">
                                            <span className="text-sm font-semibold text-white truncate">{alert.source}</span>
                                            <span className="text-xs text-slate-500 whitespace-nowrap">
                                                {new Date(alert.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-300 mb-2 leading-relaxed">
                                            {alert.message}
                                        </p>
                                        <div className="flex items-center gap-4">
                                            {!alert.is_read && (
                                                <button className="text-xs font-medium text-blue-400 hover:text-blue-300">
                                                    {t('markRead')}
                                                </button>
                                            )}
                                            <button className="text-xs font-medium text-slate-500 hover:text-red-400 flex items-center gap-1">
                                                <Trash2 className="w-3 h-3" />
                                                {t('delete')}
                                            </button>
                                        </div>
                                    </div>
                                    <button className="p-1 text-slate-600 hover:text-white shrink-0">
                                        <MoreVertical className="w-4 h-4" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
