"use client";

import { useState, useEffect, useTransition } from "react";
import Link from "next/link";
import { Database, Calendar, CheckCircle2, ArrowRight, Import, Loader2, AlertCircle, Filter, RefreshCw, Trophy, ClipboardList } from "lucide-react";
import { getAutoCandidates, getManualSeeds, importCandidateToManual, getPromotedGoldenSets, getReviewQueue, ReviewQueueItem } from "@/lib/actions/golden-set";
import PipelinePanel from "./components/PipelinePanel";
import ReviewQueueTab from "./components/ReviewQueueTab";

type TabType = "auto" | "manual" | "review" | "final";

interface AutoCandidate {
    id: string;
    drug_name: string;
    target: string;
    antibody?: string;
    linker?: string;
    payload?: string;
    source_ref?: string;
    review_status?: string;
    created_at: string;
}

interface ManualSeed {
    id: string;
    drug_name_canonical: string;
    target: string;
    antibody?: string;
    payload_family?: string;
    gate_status: string;
    is_final: boolean;
    outcome_label?: string;
    portfolio_group?: string;
    created_at: string;
}

interface FinalSeed {
    id: string;
    drug_name_canonical: string;
    resolved_target_symbol?: string;
    payload_family?: string;
    clinical_phase?: string;
    outcome_label?: string;
    is_final: boolean;
    updated_at: string;
}

export default function GoldenSetsPage() {
    const [activeTab, setActiveTab] = useState<TabType>("auto");
    const [autoCandidates, setAutoCandidates] = useState<AutoCandidate[]>([]);
    const [manualSeeds, setManualSeeds] = useState<ManualSeed[]>([]);
    const [finalSeeds, setFinalSeeds] = useState<FinalSeed[]>([]);
    const [reviewItems, setReviewItems] = useState<ReviewQueueItem[]>([]);
    const [autoCount, setAutoCount] = useState(0);
    const [manualCount, setManualCount] = useState(0);
    const [finalCount, setFinalCount] = useState(0);
    const [reviewCount, setReviewCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [isPending, startTransition] = useTransition();
    const [importingId, setImportingId] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    // Fetch data on tab change
    useEffect(() => {
        fetchData();
    }, [activeTab]);


    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === "auto") {
                const result = await getAutoCandidates(1, 50);
                setAutoCandidates(result.data);
                setAutoCount(result.count);
            } else if (activeTab === "manual") {
                const result = await getManualSeeds(1, 50, { isFinal: false });
                setManualSeeds(result.data);
                setManualCount(result.count);
            } else if (activeTab === "review") {
                const result = await getReviewQueue(1, 50, 'pending');
                setReviewItems(result.data);
                setReviewCount(result.count);
            } else {
                // Final tab
                const data = await getPromotedGoldenSets(50);
                setFinalSeeds(data);
                setFinalCount(data.length);
            }
        } catch (error) {
            console.error("Failed to fetch data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleImport = async (candidateId: string, drugName: string) => {
        setImportingId(candidateId);
        setMessage(null);

        startTransition(async () => {
            try {
                await importCandidateToManual(candidateId);
                setMessage({ type: "success", text: `✓ ${drugName} imported to Manual seeds` });
                // Refresh data
                const result = await getAutoCandidates(1, 50);
                setAutoCandidates(result.data);
            } catch (error: any) {
                setMessage({ type: "error", text: error.message || "Import failed" });
            } finally {
                setImportingId(null);
            }
        });
    };

    const getGateStatusBadge = (status: string, isFinal: boolean) => {
        if (isFinal) {
            return (
                <span className="px-2 py-0.5 text-xs font-medium bg-green-900/30 text-green-400 rounded border border-green-800 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Final
                </span>
            );
        }
        const colors: Record<string, string> = {
            draft: "bg-slate-800 text-slate-400 border-slate-700",
            needs_review: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
            ready_to_promote: "bg-blue-900/30 text-blue-400 border-blue-800",
        };
        return (
            <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[status] || colors.draft}`}>
                {status.replace("_", " ")}
            </span>
        );
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Golden Sets</h1>
                        <p className="text-sm text-slate-400">
                            Auto: 자동 수집 후보 → Manual: 정답지 큐레이션 → Review: 검토 → Final: 승격
                        </p>
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                        새로고침
                    </button>
                </div>

                {/* Pipeline Panel */}
                <div className="mb-6">
                    <PipelinePanel onStepComplete={fetchData} />
                </div>

                {/* Message Toast */}
                {message && (
                    <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${message.type === "success"
                        ? "bg-green-900/30 text-green-400 border border-green-800"
                        : "bg-red-900/30 text-red-400 border border-red-800"
                        }`}>
                        {message.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        {message.text}
                        <button onClick={() => setMessage(null)} className="ml-auto text-sm hover:underline">닫기</button>
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex gap-2 mb-6 border-b border-slate-800 pb-2">
                    <button
                        onClick={() => setActiveTab("auto")}
                        className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${activeTab === "auto"
                            ? "bg-blue-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                            }`}
                    >
                        Auto (자동 수집)
                        <span className="ml-2 px-2 py-0.5 bg-slate-900 rounded text-xs">{autoCount}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("manual")}
                        className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${activeTab === "manual"
                            ? "bg-purple-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                            }`}
                    >
                        Manual (수동 Seed)
                        <span className="ml-2 px-2 py-0.5 bg-slate-900 rounded text-xs">{manualCount}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("review")}
                        className={`px-4 py-2 rounded-t-lg font-medium transition-colors flex items-center gap-1 ${activeTab === "review"
                            ? "bg-yellow-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                            }`}
                    >
                        <ClipboardList className="w-4 h-4" />
                        Review (검토)
                        <span className="ml-2 px-2 py-0.5 bg-slate-900 rounded text-xs">{reviewCount}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("final")}
                        className={`px-4 py-2 rounded-t-lg font-medium transition-colors flex items-center gap-1 ${activeTab === "final"
                            ? "bg-green-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                            }`}
                    >
                        <Trophy className="w-4 h-4" />
                        Final (승격)
                        <span className="ml-2 px-2 py-0.5 bg-slate-900 rounded text-xs">{finalCount}</span>
                    </button>
                </div>

                {/* Content */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
                    </div>
                ) : activeTab === "auto" ? (
                    /* ======================== TAB 1: AUTO ======================== */
                    <div className="space-y-3">
                        {autoCandidates.length === 0 ? (
                            <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                                <Database className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-400">자동 수집된 후보가 없습니다</h3>
                                <p className="text-sm text-slate-500 mt-2">Golden Seed 커넥터를 실행하세요.</p>
                            </div>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-800">
                                        <th className="py-3 px-4">Drug Name</th>
                                        <th className="py-3 px-4">Target</th>
                                        <th className="py-3 px-4">Antibody</th>
                                        <th className="py-3 px-4">Source</th>
                                        <th className="py-3 px-4">Status</th>
                                        <th className="py-3 px-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {autoCandidates.map((c) => (
                                        <tr key={c.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                                            <td className="py-3 px-4 font-medium text-white">{c.drug_name}</td>
                                            <td className="py-3 px-4 text-slate-300">{c.target}</td>
                                            <td className="py-3 px-4 text-slate-400">{c.antibody || "-"}</td>
                                            <td className="py-3 px-4 text-slate-500 text-sm">{c.source_ref || "-"}</td>
                                            <td className="py-3 px-4">
                                                <span className="px-2 py-0.5 text-xs bg-slate-800 text-slate-400 rounded">
                                                    {c.review_status || "pending"}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <button
                                                    onClick={() => handleImport(c.id, c.drug_name)}
                                                    disabled={importingId === c.id || isPending}
                                                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 text-white text-sm rounded-lg transition-colors"
                                                >
                                                    {importingId === c.id ? (
                                                        <Loader2 className="w-3 h-3 animate-spin" />
                                                    ) : (
                                                        <Import className="w-3 h-3" />
                                                    )}
                                                    Import
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                ) : activeTab === "manual" ? (
                    /* ======================== TAB 2: MANUAL ======================== */
                    <div className="space-y-3">
                        {manualSeeds.length === 0 ? (
                            <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                                <Database className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-400">수동 Seed가 없습니다</h3>
                                <p className="text-sm text-slate-500 mt-2">
                                    Auto 탭에서 Import하거나, 스크립트로 직접 적재하세요.
                                </p>
                            </div>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-800">
                                        <th className="py-3 px-4">Drug Name</th>
                                        <th className="py-3 px-4">Target</th>
                                        <th className="py-3 px-4">Payload</th>
                                        <th className="py-3 px-4">Group</th>
                                        <th className="py-3 px-4">Gate Status</th>
                                        <th className="py-3 px-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {manualSeeds.map((s) => (
                                        <tr key={s.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                                            <td className="py-3 px-4 font-medium text-white">{s.drug_name_canonical}</td>
                                            <td className="py-3 px-4 text-slate-300">{s.target}</td>
                                            <td className="py-3 px-4 text-slate-400">{s.payload_family || "-"}</td>
                                            <td className="py-3 px-4 text-slate-500 text-sm">{s.portfolio_group || "-"}</td>
                                            <td className="py-3 px-4">
                                                {getGateStatusBadge(s.gate_status, s.is_final)}
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <Link
                                                    href={`/admin/golden-sets/manual/${s.id}`}
                                                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                                                >
                                                    Edit <ArrowRight className="w-3 h-3" />
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                ) : activeTab === "review" ? (
                    /* ======================== TAB 3: REVIEW ======================== */
                    <ReviewQueueTab items={reviewItems} onRefresh={fetchData} />
                ) : (
                    /* ======================== TAB 4: FINAL ======================== */
                    <div className="space-y-3">
                        {finalSeeds.length === 0 ? (
                            <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                                <Trophy className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-400">승격된 Final Seed가 없습니다</h3>
                                <p className="text-sm text-slate-500 mt-2">Manual 탭에서 Seed를 편집하고 승격하세요.</p>
                            </div>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="text-left text-sm text-slate-400 border-b border-slate-800">
                                        <th className="py-3 px-4">Drug Name</th>
                                        <th className="py-3 px-4">Target</th>
                                        <th className="py-3 px-4">Payload</th>
                                        <th className="py-3 px-4">Phase</th>
                                        <th className="py-3 px-4 text-right">상세</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {finalSeeds.map((s) => {
                                        const phaseBadge = getPhaseBadge(s.clinical_phase);
                                        return (
                                            <tr key={s.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                                                <td className="py-3 px-4">
                                                    <div className="flex items-center gap-2">
                                                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                                                        <span className="font-medium text-white">{s.drug_name_canonical}</span>
                                                    </div>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <span className="px-2 py-1 text-xs font-medium rounded bg-blue-900/30 text-blue-400 border border-blue-800/50">
                                                        {s.resolved_target_symbol || "-"}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 text-slate-400">{s.payload_family || "-"}</td>
                                                <td className="py-3 px-4">
                                                    <span className={`px-2 py-1 text-xs font-medium rounded ${phaseBadge.bg} ${phaseBadge.text}`}>
                                                        {phaseBadge.label}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 text-right">
                                                    <Link
                                                        href={`/admin/golden-sets/manual/${s.id}`}
                                                        className="text-sm text-blue-400 hover:text-blue-300"
                                                    >
                                                        보기
                                                    </Link>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// Phase badge helper
function getPhaseBadge(phase: string | null | undefined) {
    if (!phase) return { bg: 'bg-slate-700', text: 'text-slate-400', label: '-' };
    if (phase === 'Approved') return { bg: 'bg-green-900/50', text: 'text-green-400', label: phase };
    if (phase.includes('3')) return { bg: 'bg-blue-900/50', text: 'text-blue-400', label: phase };
    if (phase.includes('2')) return { bg: 'bg-purple-900/50', text: 'text-purple-400', label: phase };
    return { bg: 'bg-slate-700', text: 'text-slate-400', label: phase };
}

