'use client';

import { useState, useEffect } from 'react';
import {
    Sparkles,
    X,
    Check,
    AlertCircle,
    Loader2,
    RefreshCw,
    ChevronRight,
    ArrowRight
} from 'lucide-react';
import { clsx } from 'clsx';

interface DiffItem {
    field_name: string;
    old_value: string | null;
    new_value: string | null;
    confidence: number;
    source: string | null;
    changed: boolean;
}

interface DiffViewProps {
    seedId: string;
    jobId: string;
    drugName: string;
    onClose: () => void;
    onApplied?: () => void;
}

function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.9) return 'text-green-400';
    if (confidence >= 0.7) return 'text-blue-400';
    if (confidence >= 0.5) return 'text-amber-400';
    return 'text-red-400';
}

function getConfidenceBgColor(confidence: number): string {
    if (confidence >= 0.9) return 'bg-green-500';
    if (confidence >= 0.7) return 'bg-blue-500';
    if (confidence >= 0.5) return 'bg-amber-500';
    return 'bg-red-500';
}

export default function DiffView({ seedId, jobId, drugName, onClose, onApplied }: DiffViewProps) {
    const [loading, setLoading] = useState(true);
    const [applying, setApplying] = useState(false);
    const [status, setStatus] = useState<'pending' | 'ready' | 'applied'>('pending');
    const [diffItems, setDiffItems] = useState<DiffItem[]>([]);
    const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
    const [error, setError] = useState<string | null>(null);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchDiffPreview();
    }, [seedId, jobId]);

    const fetchDiffPreview = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/golden-seeds/${seedId}/diff-preview?job_id=${jobId}`);
            if (!res.ok) throw new Error('Failed to fetch diff');

            const data = await res.json();
            setStatus(data.status);
            setDiffItems(data.diff || []);

            // 기본적으로 변경된 필드 모두 선택
            const changedFields = (data.diff || [])
                .filter((d: DiffItem) => d.changed)
                .map((d: DiffItem) => d.field_name);
            setSelectedFields(new Set(changedFields));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const toggleField = (fieldName: string) => {
        setSelectedFields(prev => {
            const next = new Set(prev);
            if (next.has(fieldName)) {
                next.delete(fieldName);
            } else {
                next.add(fieldName);
            }
            return next;
        });
    };

    const selectAll = () => {
        const allChanged = diffItems
            .filter(d => d.changed)
            .map(d => d.field_name);
        setSelectedFields(new Set(allChanged));
    };

    const selectNone = () => {
        setSelectedFields(new Set());
    };

    const handleApply = async () => {
        if (selectedFields.size === 0) {
            alert('적용할 필드를 선택해주세요.');
            return;
        }

        setApplying(true);
        try {
            const res = await fetch(
                `${ENGINE_URL}/api/v1/golden-seeds/${seedId}/apply-diff?job_id=${jobId}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fields: Array.from(selectedFields) }),
                }
            );

            if (!res.ok) throw new Error('Failed to apply diff');

            const result = await res.json();
            setStatus('applied');
            alert(`${result.applied_count}개 필드가 적용되었습니다.`);
            onApplied?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Apply failed');
        } finally {
            setApplying(false);
        }
    };

    const changedCount = diffItems.filter(d => d.changed).length;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <div>
                        <div className="flex items-center gap-3">
                            <Sparkles className="w-6 h-6 text-purple-400" />
                            <h2 className="text-xl font-bold text-white">LLM Enrich Diff</h2>
                            {status === 'pending' && (
                                <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded">
                                    Processing...
                                </span>
                            )}
                            {status === 'ready' && (
                                <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded">
                                    {changedCount} Changes
                                </span>
                            )}
                            {status === 'applied' && (
                                <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded flex items-center gap-1">
                                    <Check className="w-3 h-3" /> Applied
                                </span>
                            )}
                        </div>
                        <p className="text-sm text-slate-400 mt-1">{drugName}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {status === 'pending' && (
                            <button
                                onClick={fetchDiffPreview}
                                className="p-2 hover:bg-slate-800 text-slate-400 rounded-lg transition-colors"
                                title="Refresh"
                            >
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-slate-800 text-slate-400 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                            <p className="text-slate-500 mt-3">Diff 로딩 중...</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-12">
                            <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
                            <p className="text-red-400">{error}</p>
                            <button
                                onClick={fetchDiffPreview}
                                className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
                            >
                                다시 시도
                            </button>
                        </div>
                    ) : status === 'pending' ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-10 h-10 text-purple-400 animate-spin mx-auto mb-3" />
                            <p className="text-slate-400">LLM이 데이터를 분석 중입니다...</p>
                            <p className="text-sm text-slate-500 mt-1">완료되면 자동으로 업데이트됩니다.</p>
                            <button
                                onClick={fetchDiffPreview}
                                className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg inline-flex items-center gap-2"
                            >
                                <RefreshCw className="w-4 h-4" />
                                새로고침
                            </button>
                        </div>
                    ) : diffItems.length === 0 ? (
                        <div className="text-center py-12">
                            <Check className="w-10 h-10 text-green-400 mx-auto mb-3" />
                            <p className="text-slate-400">변경 사항이 없습니다.</p>
                        </div>
                    ) : (
                        <>
                            {/* Selection Controls */}
                            <div className="flex items-center justify-between mb-4">
                                <div className="text-sm text-slate-400">
                                    {selectedFields.size}/{changedCount} 선택됨
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={selectAll}
                                        className="text-xs text-blue-400 hover:text-blue-300"
                                    >
                                        모두 선택
                                    </button>
                                    <span className="text-slate-600">|</span>
                                    <button
                                        onClick={selectNone}
                                        className="text-xs text-slate-400 hover:text-slate-300"
                                    >
                                        선택 해제
                                    </button>
                                </div>
                            </div>

                            {/* Diff Items */}
                            <div className="space-y-3">
                                {diffItems.map((item) => (
                                    <div
                                        key={item.field_name}
                                        className={clsx(
                                            'bg-slate-950 border rounded-xl overflow-hidden transition-colors',
                                            item.changed
                                                ? selectedFields.has(item.field_name)
                                                    ? 'border-blue-500/50'
                                                    : 'border-slate-700'
                                                : 'border-slate-800 opacity-50'
                                        )}
                                    >
                                        <button
                                            onClick={() => item.changed && toggleField(item.field_name)}
                                            disabled={!item.changed || status === 'applied'}
                                            className="w-full p-4 text-left"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        {item.changed && status !== 'applied' && (
                                                            <div className={clsx(
                                                                'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0',
                                                                selectedFields.has(item.field_name)
                                                                    ? 'bg-blue-500 border-blue-500'
                                                                    : 'border-slate-600'
                                                            )}>
                                                                {selectedFields.has(item.field_name) && (
                                                                    <Check className="w-3 h-3 text-white" />
                                                                )}
                                                            </div>
                                                        )}
                                                        <span className="text-white font-medium">
                                                            {item.field_name}
                                                        </span>
                                                        <span className={clsx(
                                                            'text-xs font-bold',
                                                            getConfidenceColor(item.confidence)
                                                        )}>
                                                            {(item.confidence * 100).toFixed(0)}%
                                                        </span>
                                                    </div>

                                                    {item.changed ? (
                                                        <div className="flex items-center gap-3 text-sm">
                                                            <div className="flex-1 min-w-0">
                                                                <div className="text-xs text-slate-500 mb-1">Before</div>
                                                                <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-3 py-2 rounded truncate">
                                                                    {item.old_value || '(empty)'}
                                                                </div>
                                                            </div>
                                                            <ArrowRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
                                                            <div className="flex-1 min-w-0">
                                                                <div className="text-xs text-slate-500 mb-1">After</div>
                                                                <div className="bg-green-500/10 border border-green-500/20 text-green-400 px-3 py-2 rounded truncate">
                                                                    {item.new_value || '(empty)'}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="text-sm text-slate-500">
                                                            변경 없음: {item.old_value || '(empty)'}
                                                        </div>
                                                    )}

                                                    {item.source && (
                                                        <div className="mt-2 text-xs text-slate-500 italic truncate">
                                                            Source: "{item.source}"
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Confidence Bar */}
                                                <div className="w-20 flex-shrink-0">
                                                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                                        <div
                                                            className={clsx('h-full rounded-full', getConfidenceBgColor(item.confidence))}
                                                            style={{ width: `${item.confidence * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                {/* Footer */}
                {status === 'ready' && changedCount > 0 && (
                    <div className="flex items-center justify-between p-6 border-t border-slate-800 bg-slate-950/50">
                        <div className="text-sm text-slate-400">
                            선택된 {selectedFields.size}개 필드를 적용합니다.
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleApply}
                                disabled={applying || selectedFields.size === 0}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {applying ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Check className="w-4 h-4" />
                                )}
                                선택 적용
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
