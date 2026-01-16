'use client';

import { useState } from 'react';
import {
    Play,
    Loader2,
    CheckCircle2,
    AlertCircle,
    Dna,
    Plus,
    X
} from 'lucide-react';
import { clsx } from 'clsx';

interface CollectionResult {
    run_id: string;
    job_id: string;
    message: string;
}

export default function GoldenSeedCollectionPage() {
    const [targets, setTargets] = useState<string[]>([]);
    const [currentTarget, setCurrentTarget] = useState('');
    const [limit, setLimit] = useState(30);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<CollectionResult | null>(null);
    const [error, setError] = useState('');

    const handleAddTarget = () => {
        if (!currentTarget.trim()) return;
        if (targets.includes(currentTarget.trim().toUpperCase())) return;
        setTargets([...targets, currentTarget.trim().toUpperCase()]);
        setCurrentTarget('');
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
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : 'Collection failed';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-3xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">Golden Seed Collection</h1>
                    <p className="text-slate-400 text-sm">
                        Target-Centric Data Collection Trigger. Enter targets to fetch clinical trials and generate RAW data.
                    </p>
                </div>

                {/* Main Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">

                    {/* Target Input */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Target List <span className="text-red-500">*</span>
                        </label>
                        <div className="flex gap-2 mb-3">
                            <div className="relative flex-1">
                                <Dna className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                <input
                                    type="text"
                                    value={currentTarget}
                                    onChange={(e) => setCurrentTarget(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Enter target (e.g. HER2, TROP2) and press Enter"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all"
                                />
                            </div>
                            <button
                                onClick={handleAddTarget}
                                disabled={!currentTarget.trim()}
                                className="px-4 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white rounded-xl transition-colors"
                            >
                                <Plus className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Target Tags */}
                        <div className="flex flex-wrap gap-2 min-h-[40px] p-3 bg-slate-950/50 rounded-xl border border-slate-800/50">
                            {targets.length === 0 && (
                                <span className="text-slate-600 text-sm italic">No targets added yet.</span>
                            )}
                            {targets.map((target) => (
                                <span key={target} className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-600/10 text-blue-400 text-sm font-medium rounded-lg border border-blue-600/20 animate-in zoom-in duration-200">
                                    {target}
                                    <button onClick={() => removeTarget(target)} className="hover:text-white transition-colors">
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Limit Input */}
                    <div className="mb-8">
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Collection Limit (Per Target)
                        </label>
                        <input
                            type="number"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value))}
                            min={1}
                            max={100}
                            className="w-full md:w-32 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-all"
                        />
                        <p className="text-xs text-slate-500 mt-1">Maximum 100 trials per target recommended.</p>
                    </div>

                    {/* Action Button */}
                    <button
                        onClick={handleStartCollection}
                        disabled={loading || targets.length === 0}
                        className={clsx(
                            "w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all shadow-lg",
                            loading || targets.length === 0
                                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20"
                        )}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Starting Collection...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5" />
                                Start Collection Job
                            </>
                        )}
                    </button>

                    {/* Result / Error Messages */}
                    {error && (
                        <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3 text-red-400 animate-in fade-in slide-in-from-bottom-2">
                            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold mb-1">Error</h3>
                                <p className="text-sm opacity-90">{error}</p>
                            </div>
                        </div>
                    )}

                    {result && (
                        <div className="mt-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl flex items-start gap-3 text-green-400 animate-in fade-in slide-in-from-bottom-2">
                            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold mb-1">Collection Started Successfully</h3>
                                <div className="text-sm opacity-90 space-y-1">
                                    <p>Run ID: <span className="font-mono text-xs bg-green-500/20 px-1.5 py-0.5 rounded">{result.run_id}</span></p>
                                    <p>Job ID: <span className="font-mono text-xs bg-green-500/20 px-1.5 py-0.5 rounded">{result.job_id}</span></p>
                                    <p>{result.message}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
