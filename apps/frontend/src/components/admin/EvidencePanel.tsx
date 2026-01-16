'use client';

import { useState, useEffect } from 'react';
import {
    BookOpen,
    ExternalLink,
    AlertCircle,
    Loader2,
    Check,
    ChevronDown,
    ChevronUp,
    Sparkles,
    FileText,
    FlaskConical,
    Award,
    Newspaper,
    X,
    CheckCircle2
} from 'lucide-react';
import { clsx } from 'clsx';

// Types
interface EvidenceItem {
    id: string;
    type: string;
    id_or_url: string | null;
    title: string | null;
    published_date: string | null;
    snippet: string | null;
    source_quality: string | null;
    created_at: string;
}

interface FieldProvenance {
    id: string;
    field_name: string;
    field_value: string | null;
    evidence_item_id: string | null;
    confidence: number;
    quote_span: string | null;
    created_at: string;
}

interface GateCheckResult {
    passed: boolean;
    score: number;
    max_score: number;
    checks: {
        axis_assigned: boolean;
        target_resolved: boolean;
        construct_ready: boolean;
        construct_details: {
            payload_family: boolean;
            linker_type: boolean;
            conjugation_method: boolean;
        };
        evidence_count: number;
        evidence_sufficient: boolean;
        evidence_grade: string;
        evidence_grade_ok: boolean;
        outcome_consistent: boolean;
    };
}

interface EvidencePanelProps {
    seedId: string;
    onClose: () => void;
    drugName: string;
}

// Confidence Color function
export function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.9) return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (confidence >= 0.7) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (confidence >= 0.5) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-red-500/20 text-red-400 border-red-500/30';
}

export function getConfidenceBgColor(confidence: number): string {
    if (confidence >= 0.9) return 'bg-green-500';
    if (confidence >= 0.7) return 'bg-blue-500';
    if (confidence >= 0.5) return 'bg-amber-500';
    return 'bg-red-500';
}

// Evidence Type Icon
function EvidenceTypeIcon({ type }: { type: string }) {
    switch (type) {
        case 'clinicaltrials':
            return <FlaskConical className="w-4 h-4 text-green-400" />;
        case 'paper':
            return <FileText className="w-4 h-4 text-blue-400" />;
        case 'patent':
            return <Award className="w-4 h-4 text-purple-400" />;
        case 'label':
            return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
        case 'press':
            return <Newspaper className="w-4 h-4 text-amber-400" />;
        default:
            return <BookOpen className="w-4 h-4 text-slate-400" />;
    }
}

// Evidence Type Badge
function EvidenceTypeBadge({ type }: { type: string }) {
    const colors: Record<string, string> = {
        clinicaltrials: 'bg-green-500/20 text-green-400',
        paper: 'bg-blue-500/20 text-blue-400',
        patent: 'bg-purple-500/20 text-purple-400',
        label: 'bg-emerald-500/20 text-emerald-400',
        press: 'bg-amber-500/20 text-amber-400',
        other: 'bg-slate-500/20 text-slate-400'
    };

    const labels: Record<string, string> = {
        clinicaltrials: 'Clinical Trial',
        paper: 'Paper',
        patent: 'Patent',
        label: 'FDA Label',
        press: 'Press',
        other: 'Other'
    };

    return (
        <span className={clsx('px-2 py-0.5 text-xs font-medium rounded flex items-center gap-1', colors[type] || colors.other)}>
            <EvidenceTypeIcon type={type} />
            {labels[type] || type}
        </span>
    );
}

// Gate Check Display
function GateCheckDisplay({ gateCheck }: { gateCheck: GateCheckResult | null }) {
    if (!gateCheck) return null;

    const checks = gateCheck.checks;

    return (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    Gate Checklist
                </h3>
                <div className={clsx(
                    'px-2 py-1 text-xs font-bold rounded-full',
                    gateCheck.passed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                )}>
                    {gateCheck.score}/{gateCheck.max_score} {gateCheck.passed ? '✓ PASS' : '✗ FAIL'}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
                <CheckItem label="Axis Assigned" passed={checks.axis_assigned} />
                <CheckItem label="Target Resolved" passed={checks.target_resolved} />
                <CheckItem label="Construct Ready" passed={checks.construct_ready} />
                <CheckItem label={`Evidence ≥ 2 (${checks.evidence_count})`} passed={checks.evidence_sufficient} />
                <CheckItem label={`Grade ≥ B (${checks.evidence_grade})`} passed={checks.evidence_grade_ok} />
                <CheckItem label="Outcome Consistent" passed={checks.outcome_consistent} />
            </div>
        </div>
    );
}

function CheckItem({ label, passed }: { label: string; passed: boolean }) {
    return (
        <div className={clsx(
            'flex items-center gap-2 px-2 py-1 rounded',
            passed ? 'bg-green-500/10 text-green-400' : 'bg-slate-800 text-slate-500'
        )}>
            {passed ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            {label}
        </div>
    );
}

// Main Evidence Panel Component
export default function EvidencePanel({ seedId, onClose, drugName }: EvidencePanelProps) {
    const [loading, setLoading] = useState(true);
    const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
    const [provenanceItems, setProvenanceItems] = useState<FieldProvenance[]>([]);
    const [gateCheck, setGateCheck] = useState<GateCheckResult | null>(null);
    const [approving, setApproving] = useState(false);
    const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'evidence' | 'provenance' | 'gate'>('evidence');

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchData();
    }, [seedId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [evidenceRes, provenanceRes, gateRes] = await Promise.all([
                fetch(`${ENGINE_URL}/api/v1/golden-seeds/${seedId}/evidence`),
                fetch(`${ENGINE_URL}/api/v1/golden-seeds/${seedId}/provenance`),
                fetch(`${ENGINE_URL}/api/v1/golden-seeds/${seedId}/gate-check`)
            ]);

            if (evidenceRes.ok) {
                const data = await evidenceRes.json();
                setEvidenceItems(data.items || []);
            }

            if (provenanceRes.ok) {
                const data = await provenanceRes.json();
                setProvenanceItems(data.items || []);
            }

            if (gateRes.ok) {
                const data = await gateRes.json();
                setGateCheck(data);
            }
        } catch (error) {
            console.error('Failed to fetch evidence data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleApproveHighConfidence = async () => {
        setApproving(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/golden-seeds/${seedId}/approve-high-confidence?threshold=0.9`, {
                method: 'POST'
            });

            if (res.ok) {
                const result = await res.json();
                alert(`${result.approved_count}개 필드가 승인되었습니다: ${result.approved_fields?.join(', ') || 'None'}`);
                fetchData(); // Refresh
            } else {
                throw new Error('Failed to approve');
            }
        } catch (error) {
            console.error('Approve failed:', error);
            alert('승인 실패');
        } finally {
            setApproving(false);
        }
    };

    const highConfidenceCount = provenanceItems.filter(p => p.confidence >= 0.9).length;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <div>
                        <div className="flex items-center gap-3">
                            <BookOpen className="w-6 h-6 text-purple-400" />
                            <h2 className="text-xl font-bold text-white">근거 및 추적성</h2>
                        </div>
                        <p className="text-sm text-slate-400 mt-1">{drugName}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {highConfidenceCount > 0 && (
                            <button
                                onClick={handleApproveHighConfidence}
                                disabled={approving}
                                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-green-600/20"
                            >
                                {approving ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Sparkles className="w-4 h-4" />
                                )}
                                Approve High Confidence ({highConfidenceCount})
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

                {/* Tabs */}
                <div className="flex border-b border-slate-800">
                    <button
                        onClick={() => setActiveTab('evidence')}
                        className={clsx(
                            'px-6 py-3 text-sm font-medium transition-colors',
                            activeTab === 'evidence'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-white'
                        )}
                    >
                        Evidence ({evidenceItems.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('provenance')}
                        className={clsx(
                            'px-6 py-3 text-sm font-medium transition-colors',
                            activeTab === 'provenance'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-white'
                        )}
                    >
                        Provenance ({provenanceItems.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('gate')}
                        className={clsx(
                            'px-6 py-3 text-sm font-medium transition-colors',
                            activeTab === 'gate'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-white'
                        )}
                    >
                        Gate Check
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                            <p className="text-slate-500 mt-3">데이터 로딩 중...</p>
                        </div>
                    ) : activeTab === 'evidence' ? (
                        <div className="space-y-3">
                            {evidenceItems.length > 0 ? (
                                evidenceItems.map((item) => (
                                    <div
                                        key={item.id}
                                        className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden"
                                    >
                                        <button
                                            onClick={() => setExpandedEvidence(expandedEvidence === item.id ? null : item.id)}
                                            className="w-full flex items-center justify-between p-4 hover:bg-slate-800/30 transition-colors"
                                        >
                                            <div className="flex items-center gap-3">
                                                <EvidenceTypeBadge type={item.type} />
                                                <span className="text-white font-medium">
                                                    {item.title || item.id_or_url || 'Untitled'}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {item.published_date && (
                                                    <span className="text-xs text-slate-500">
                                                        {new Date(item.published_date).toLocaleDateString()}
                                                    </span>
                                                )}
                                                {expandedEvidence === item.id ? (
                                                    <ChevronUp className="w-4 h-4 text-slate-400" />
                                                ) : (
                                                    <ChevronDown className="w-4 h-4 text-slate-400" />
                                                )}
                                            </div>
                                        </button>
                                        {expandedEvidence === item.id && (
                                            <div className="px-4 pb-4 border-t border-slate-800 pt-3">
                                                {item.snippet && (
                                                    <p className="text-sm text-slate-300 mb-3">{item.snippet}</p>
                                                )}
                                                {item.id_or_url && (
                                                    <a
                                                        href={item.id_or_url.startsWith('http') ? item.id_or_url : `https://www.google.com/search?q=${item.id_or_url}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm"
                                                    >
                                                        <ExternalLink className="w-4 h-4" />
                                                        {item.id_or_url}
                                                    </a>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-12">
                                    <AlertCircle className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                                    <p className="text-slate-400">등록된 근거가 없습니다.</p>
                                </div>
                            )}
                        </div>
                    ) : activeTab === 'provenance' ? (
                        <div className="space-y-3">
                            {provenanceItems.length > 0 ? (
                                provenanceItems.map((item) => (
                                    <div
                                        key={item.id}
                                        className="bg-slate-950 border border-slate-800 rounded-xl p-4"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-white font-medium">{item.field_name}</span>
                                            <div className={clsx(
                                                'px-2 py-1 text-xs font-bold rounded-full border',
                                                getConfidenceColor(item.confidence)
                                            )}>
                                                {(item.confidence * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                        <div className="text-sm text-slate-300 bg-slate-900 px-3 py-2 rounded mb-2">
                                            {item.field_value || '-'}
                                        </div>
                                        {item.quote_span && (
                                            <div className="text-xs text-slate-500 italic">
                                                &quot;{item.quote_span}&quot;
                                            </div>
                                        )}
                                        <div className="flex items-center gap-2 mt-2">
                                            <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className={clsx('h-full rounded-full', getConfidenceBgColor(item.confidence))}
                                                    style={{ width: `${item.confidence * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-12">
                                    <AlertCircle className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                                    <p className="text-slate-400">추적성 데이터가 없습니다.</p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <GateCheckDisplay gateCheck={gateCheck} />
                    )}
                </div>
            </div>
        </div>
    );
}
