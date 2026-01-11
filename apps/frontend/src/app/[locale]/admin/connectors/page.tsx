'use client';

import { useState, useEffect } from 'react';
import {
    Plus,
    X,
    Clock,
    Loader2,
    CheckCircle,
    AlertCircle,
    Activity,
    Database,
    FileText,
    RefreshCw,
    Play
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { getConnectors, triggerConnectorRun, createConnector } from '@/lib/actions/admin';

interface Connector {
    id: string;
    name: string;
    type: string;
    is_enabled: boolean;
    config: any;
    latest_run: {
        status: string;
        started_at: string | null;
        ended_at: string | null;
        error_json: any;
    } | null;
}

const STATUS_CONFIG: Record<string, { labelKey: string; icon: any; class: string }> = {
    queued: { labelKey: 'status.queued', icon: Clock, class: 'bg-amber-500/20 text-amber-400' },
    running: { labelKey: 'status.running', icon: Loader2, class: 'bg-blue-500/20 text-blue-400' },
    succeeded: { labelKey: 'status.succeeded', icon: CheckCircle, class: 'bg-green-500/20 text-green-400' },
    failed: { labelKey: 'status.failed', icon: AlertCircle, class: 'bg-red-500/20 text-red-400' },
    idle: { labelKey: 'status.idle', icon: CheckCircle, class: 'bg-slate-500/20 text-slate-400' },
};

const TYPE_CONFIG: Record<string, { icon: any; color: string; bg: string }> = {
    api: { icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    crawler: { icon: Database, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    default: { icon: FileText, color: 'text-slate-400', bg: 'bg-slate-500/20' },
};

export default function ConnectorsPage() {
    const t = useTranslations('Admin.connectors');
    const [connectors, setConnectors] = useState<Connector[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newConnector, setNewConnector] = useState({ name: '', type: 'api', config: {} });

    const fetchConnectors = async () => {
        try {
            const data = await getConnectors();
            setConnectors(data as any);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch connectors');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConnectors();
        const interval = setInterval(fetchConnectors, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleRun = async (id: string) => {
        try {
            await triggerConnectorRun(id);
            await fetchConnectors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to trigger run');
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createConnector(newConnector);
            setIsModalOpen(false);
            setNewConnector({ name: '', type: 'api', config: {} });
            await fetchConnectors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to create connector');
        }
    };

    if (loading && connectors.length === 0) {
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
                    <div className="flex gap-3">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            {t('add')}
                        </button>
                        <button
                            onClick={fetchConnectors}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" />
                            {t('refresh')}
                        </button>
                    </div>
                </div>

                {/* Connector Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {connectors.map((connector) => {
                        const status = connector.latest_run?.status || 'idle';
                        const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.idle;
                        const StatusIcon = statusConfig.icon;
                        const typeConfig = TYPE_CONFIG[connector.type] || TYPE_CONFIG.default;
                        const TypeIcon = typeConfig.icon;

                        return (
                            <div
                                key={connector.id}
                                className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2.5 rounded-lg ${typeConfig.bg}`}>
                                            <TypeIcon className={`w-5 h-5 ${typeConfig.color}`} />
                                        </div>
                                        <div>
                                            <h3 className="text-white font-semibold">{connector.name}</h3>
                                            <span className="text-xs text-slate-500 uppercase">{connector.type}</span>
                                        </div>
                                    </div>
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.class}`}>
                                        <StatusIcon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
                                        {t(statusConfig.labelKey)}
                                    </span>
                                </div>

                                <div className="text-xs text-slate-500 mb-6 space-y-2">
                                    <div className="flex justify-between">
                                        <span>{t('status.idle')}</span>
                                        <span className={connector.is_enabled ? 'text-green-400' : 'text-red-400'}>
                                            {connector.is_enabled ? t('status.enabled') : t('status.disabled')}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>{t('status.lastRun')}</span>
                                        <span className="text-white">
                                            {connector.latest_run?.started_at
                                                ? new Date(connector.latest_run.started_at).toLocaleString()
                                                : t('status.never')}
                                        </span>
                                    </div>
                                    {connector.latest_run?.error_json && (
                                        <div className="text-red-400 bg-red-400/10 p-2 rounded mt-2 text-[10px] break-all">
                                            {JSON.stringify(connector.latest_run.error_json)}
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={() => handleRun(connector.id)}
                                    disabled={status === 'running' || status === 'queued'}
                                    className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    {status === 'running' || status === 'queued' ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            {t('status.processing')}
                                        </>
                                    ) : (
                                        <>
                                            <Play className="w-4 h-4" />
                                            {t('status.run')}
                                        </>
                                    )}
                                </button>
                            </div>
                        );
                    })}
                </div>

                {/* Create Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden">
                            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                                <h2 className="text-xl font-bold text-white">{t('modal.title')}</h2>
                                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                            <form onSubmit={handleCreate} className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">{t('modal.name')}</label>
                                    <input
                                        required
                                        type="text"
                                        value={newConnector.name}
                                        onChange={e => setNewConnector({ ...newConnector, name: e.target.value })}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                        placeholder={t('modal.placeholder')}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">{t('modal.type')}</label>
                                    <select
                                        value={newConnector.type}
                                        onChange={e => setNewConnector({ ...newConnector, type: e.target.value })}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    >
                                        <option value="api">{t('modal.api')}</option>
                                        <option value="crawler">{t('modal.crawler')}</option>
                                    </select>
                                </div>
                                <div className="pt-4">
                                    <button
                                        type="submit"
                                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded-lg transition-colors"
                                    >
                                        {t('modal.create')}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
