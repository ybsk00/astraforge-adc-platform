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
    Play,
    Download
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { getConnectors, triggerConnectorRun, createConnector, setupDefaultConnectors } from '@/lib/actions/admin';
import { clsx } from 'clsx';

interface Connector {
    id: string;
    name: string;
    type: string;
    is_enabled: boolean;
    config: Record<string, unknown>;
    latest_run: {
        status: string;
        started_at: string | null;
        ended_at: string | null;
        result_summary: Record<string, unknown> | null;
        error_json: Record<string, unknown> | null;
    } | null;
}

type LucideIcon = React.ComponentType<{ className?: string }>;

const STATUS_CONFIG: Record<string, { labelKey: string; icon: LucideIcon; class: string; color: string }> = {
    queued: { labelKey: 'status.queued', icon: Clock, class: 'bg-amber-500/20 text-amber-400 border-amber-500/20', color: 'text-amber-400' },
    running: { labelKey: 'status.running', icon: Loader2, class: 'bg-blue-500/20 text-blue-400 border-blue-500/20', color: 'text-blue-400' },
    succeeded: { labelKey: 'status.succeeded', icon: CheckCircle, class: 'bg-green-500/20 text-green-400 border-green-500/20', color: 'text-green-400' },
    failed: { labelKey: 'status.failed', icon: AlertCircle, class: 'bg-red-500/20 text-red-400 border-red-500/20', color: 'text-red-400' },
    idle: { labelKey: 'status.idle', icon: CheckCircle, class: 'bg-slate-500/20 text-slate-400 border-slate-500/20', color: 'text-slate-400' },
};

const TYPE_CONFIG: Record<string, { icon: LucideIcon; color: string; bg: string }> = {
    api: { icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    crawler: { icon: Database, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    golden_seed: { icon: Database, color: 'text-amber-400', bg: 'bg-amber-500/20' },
    default: { icon: FileText, color: 'text-slate-400', bg: 'bg-slate-500/20' },
};

export default function ConnectorsPage() {
    const t = useTranslations('Admin.connectors');
    const [connectors, setConnectors] = useState<Connector[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newConnector, setNewConnector] = useState({ name: '', type: 'api', config: {} });

    const fetchConnectors = async () => {
        try {
            const data = await getConnectors();
            setConnectors(data as Connector[]);
        } catch (err) {
            console.error('Failed to fetch connectors:', err);
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

    const handleFetchDefaults = async () => {
        try {
            setLoading(true);
            await setupDefaultConnectors();
            await fetchConnectors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to fetch default connectors');
        } finally {
            setLoading(false);
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
                            onClick={handleFetchDefaults}
                            disabled={loading}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-indigo-600/20 disabled:opacity-50"
                        >
                            <Download className="w-4 h-4" />
                            {t('fetchDefaults')}
                        </button>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-blue-600/20"
                        >
                            <Plus className="w-4 h-4" />
                            {t('add')}
                        </button>
                        <button
                            onClick={fetchConnectors}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
                            {t('refresh')}
                        </button>
                    </div>
                </div>

                {/* Golden Seed Collection Section */}
                <div className="mb-12 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 blur-3xl rounded-full -mr-32 -mt-32 pointer-events-none" />

                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 rounded-xl bg-amber-500/20 border border-amber-500/20 shadow-inner">
                                <Database className="w-6 h-6 text-amber-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Golden Seed Collection</h2>
                                <p className="text-slate-400 text-sm">Target-Centric Data Collection Trigger</p>
                            </div>
                        </div>

                        <GoldenSeedTrigger />
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
                                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden shadow-xl"
                            >
                                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/5 blur-3xl rounded-full -mr-16 -mt-16 group-hover:bg-blue-600/10 transition-colors" />

                                <div className="flex justify-between items-start mb-6 relative z-10">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-3 rounded-xl ${typeConfig.bg} border border-white/5 shadow-inner`}>
                                            <TypeIcon className={`w-5 h-5 ${typeConfig.color}`} />
                                        </div>
                                        <div>
                                            <h3 className="text-white font-bold text-lg">{connector.name}</h3>
                                            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">{connector.type}</span>
                                        </div>
                                    </div>
                                    <span className={clsx(
                                        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border uppercase tracking-wider",
                                        statusConfig.class
                                    )}>
                                        <StatusIcon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
                                        {t(statusConfig.labelKey)}
                                    </span>
                                </div>

                                <div className="text-xs text-slate-400 mb-8 space-y-3 relative z-10">
                                    <div className="flex justify-between items-center bg-slate-950/50 p-2 rounded-lg border border-white/5">
                                        <span className="text-slate-500 font-medium">상태</span>
                                        <span className={clsx(
                                            "font-bold",
                                            connector.is_enabled ? 'text-green-400' : 'text-red-400'
                                        )}>
                                            {connector.is_enabled ? t('status.enabled') : t('status.disabled')}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center bg-slate-950/50 p-2 rounded-lg border border-white/5">
                                        <span className="text-slate-500 font-medium">{t('status.lastRun')}</span>
                                        <span className="text-slate-200 font-mono">
                                            {connector.latest_run?.started_at
                                                ? new Date(connector.latest_run.started_at).toLocaleTimeString()
                                                : t('status.never')}
                                        </span>
                                    </div>
                                    {connector.latest_run?.error_json && (
                                        <div className="text-red-400 bg-red-400/10 p-3 rounded-xl mt-2 text-[10px] break-all border border-red-400/20">
                                            <div className="font-bold mb-1 flex items-center gap-1">
                                                <AlertCircle className="w-3 h-3" /> Error Details
                                            </div>
                                            {JSON.stringify(connector.latest_run.error_json)}
                                        </div>
                                    )}
                                    {connector.latest_run?.status === 'succeeded' && connector.latest_run?.result_summary && (
                                        <div className="text-green-400 bg-green-400/10 p-3 rounded-xl mt-2 text-[10px] break-all border border-green-400/20">
                                            <div className="font-bold mb-1 flex items-center gap-1">
                                                <CheckCircle className="w-3 h-3" /> Result Summary
                                            </div>
                                            <pre className="whitespace-pre-wrap font-mono">
                                                {JSON.stringify(connector.latest_run.result_summary, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>

                                <div className="flex flex-col gap-2 relative z-10">
                                    <button
                                        onClick={() => handleRun(connector.id)}
                                        disabled={status === 'running' || status === 'queued'}
                                        className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20"
                                    >
                                        {status === 'running' || status === 'queued' ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                {t('status.processing')}
                                            </>
                                        ) : (
                                            <>
                                                <Play className="w-4 h-4 fill-current" />
                                                {t('status.run')}
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Create Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
                            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                                <h2 className="text-xl font-bold text-white">{t('modal.title')}</h2>
                                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                            <form onSubmit={handleCreate} className="p-6 space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">{t('modal.name')}</label>
                                    <input
                                        required
                                        type="text"
                                        value={newConnector.name}
                                        onChange={e => setNewConnector({ ...newConnector, name: e.target.value })}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all"
                                        placeholder={t('modal.placeholder')}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">{t('modal.type')}</label>
                                    <select
                                        value={newConnector.type}
                                        onChange={e => setNewConnector({ ...newConnector, type: e.target.value })}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all appearance-none"
                                    >
                                        <option value="api">{t('modal.api')}</option>
                                        <option value="crawler">{t('modal.crawler')}</option>
                                    </select>
                                </div>
                                <div className="pt-4">
                                    <button
                                        type="submit"
                                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
                                    >
                                        <Plus className="w-5 h-5" />
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


function GoldenSeedTrigger() {
    const [targets, setTargets] = useState<string[]>([]);
    const [currentTarget, setCurrentTarget] = useState('');
    const [limit, setLimit] = useState(30);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

    // Target List Modal State
    const [isTargetListOpen, setIsTargetListOpen] = useState(false);
    const [popularTargets] = useState([
        "HER2", "TROP2", "EGFR", "CD19", "CD22", "CD30", "CD33", "CD79b", "BCMA", "Nectin-4",
        "HER3", "MET", "CEACAM5", "CLDN18.2", "B7-H3", "GPC3", "ROR1", "FRα", "PSMA", "TF",
        "CD123", "CD37", "CD70", "CD138", "CD276", "DLL3", "EFNA4", "ENPP3", "FGFR2", "FLT3",
        "FOLR1", "GCC", "HAVCR1", "LIV-1", "LRRC15", "LY6E", "MUC1", "MUC16", "NaPi2b", "PTK7",
        "SLC34A2", "STEAP1", "TACSTD2", "TNFRSF17", "TPBG", "5T4", "AGS-16", "AXL", "B7-H4", "CA6"
    ]);

    const handleAddTarget = () => {
        if (!currentTarget.trim()) return;
        if (targets.includes(currentTarget.trim().toUpperCase())) return;
        setTargets([...targets, currentTarget.trim().toUpperCase()]);
        setCurrentTarget('');
    };

    const handleSelectTarget = (target: string) => {
        if (!targets.includes(target)) {
            setTargets([...targets, target]);
        }
        setIsTargetListOpen(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddTarget();
        }
    };

    const removeTarget = (target: string) => {
        setTargets(targets.filter(t => t !== target));
    };

    const handleStartCollection = async () => {
        if (targets.length === 0) return;

        setLoading(true);
        setError('');
        setResult(null);

        try {
            const response = await fetch('/api/admin/golden/seed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    targets: targets,
                    limit: limit
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to start collection');
            }

            const data = await response.json();
            setResult(data);
            setTargets([]); // Clear after success
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Inputs */}
                <div className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Target List <span className="text-red-500">*</span>
                        </label>
                        <div className="flex gap-2 mb-3">
                            <input
                                type="text"
                                value={currentTarget}
                                onChange={(e) => setCurrentTarget(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Enter target (e.g. HER2, TROP2)"
                                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition-all"
                            />
                            <button
                                onClick={() => setIsTargetListOpen(true)}
                                className="px-4 bg-slate-800 hover:bg-slate-700 text-blue-400 hover:text-blue-300 rounded-xl transition-colors flex items-center gap-2 border border-slate-700"
                                title="View Popular Targets"
                            >
                                <Database className="w-5 h-5" />
                                <span className="hidden sm:inline">주요 표적 (50)</span>
                            </button>
                            <button
                                onClick={handleAddTarget}
                                disabled={!currentTarget.trim()}
                                className="px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl transition-colors shadow-lg shadow-blue-600/20"
                            >
                                <Plus className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2 min-h-[40px] p-3 bg-slate-950/50 rounded-xl border border-slate-800/50">
                            {targets.length === 0 && (
                                <span className="text-slate-600 text-sm italic">No targets added yet.</span>
                            )}
                            {targets.map((target) => (
                                <span key={target} className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 text-amber-400 text-sm font-medium rounded-lg border border-amber-500/20 animate-in zoom-in duration-200">
                                    {target}
                                    <button onClick={() => removeTarget(target)} className="hover:text-white transition-colors">
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Collection Limit (Per Target)
                        </label>
                        <input
                            type="number"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value))}
                            min={1}
                            max={100}
                            className="w-full md:w-32 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-amber-500 transition-all"
                        />
                    </div>
                </div>

                {/* Action & Status */}
                <div className="flex flex-col justify-end space-y-4">
                    <button
                        onClick={handleStartCollection}
                        disabled={loading || targets.length === 0}
                        className={clsx(
                            "w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all shadow-lg",
                            loading || targets.length === 0
                                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                : "bg-amber-600 hover:bg-amber-500 text-white shadow-amber-600/20"
                        )}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Starting Collection...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5 fill-current" />
                                Start Collection Job
                            </>
                        )}
                    </button>

                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3 text-red-400 animate-in fade-in slide-in-from-bottom-2">
                            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold mb-1">Error</h3>
                                <p className="text-sm opacity-90">{error}</p>
                            </div>
                        </div>
                    )}

                    {result && (
                        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl flex items-start gap-3 text-green-400 animate-in fade-in slide-in-from-bottom-2">
                            <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold mb-1">Collection Started</h3>
                                <div className="text-sm opacity-90 space-y-1">
                                    <p>Run ID: <span className="font-mono text-xs bg-green-500/20 px-1.5 py-0.5 rounded">{result.run_id}</span></p>
                                    <p>{result.message}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Target List Modal */}
            {isTargetListOpen && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200 flex flex-col">
                        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                            <div>
                                <h2 className="text-xl font-bold text-white">주요 ADC 표적 리스트</h2>
                                <p className="text-sm text-slate-400 mt-1">자주 사용되는 50개의 주요 표적입니다.</p>
                            </div>
                            <button onClick={() => setIsTargetListOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {popularTargets.map((target) => (
                                    <button
                                        key={target}
                                        onClick={() => handleSelectTarget(target)}
                                        disabled={targets.includes(target)}
                                        className={clsx(
                                            "px-3 py-2 rounded-lg text-sm font-medium transition-all border",
                                            targets.includes(target)
                                                ? "bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed"
                                                : "bg-slate-950 text-slate-300 border-slate-800 hover:border-blue-500 hover:text-blue-400 hover:bg-blue-500/5"
                                        )}
                                    >
                                        {target}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-end">
                            <button
                                onClick={() => setIsTargetListOpen(false)}
                                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                            >
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
