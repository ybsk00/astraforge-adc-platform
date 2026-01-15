"use client";

import { useState, useTransition } from "react";
import { CheckCircle2, XCircle, AlertCircle, Loader2, Eye } from "lucide-react";
import { approveReviewItem, rejectReviewItem, ReviewQueueItem } from "@/lib/actions/golden-set";

interface ReviewQueueTabProps {
    items: ReviewQueueItem[];
    onRefresh: () => void;
}

export default function ReviewQueueTab({ items, onRefresh }: ReviewQueueTabProps) {
    const [isPending, startTransition] = useTransition();
    const [processingId, setProcessingId] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [comment, setComment] = useState("");
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    const handleApprove = (id: string) => {
        setProcessingId(id);
        startTransition(async () => {
            try {
                await approveReviewItem(id, comment || undefined);
                setMessage({ type: "success", text: "변경 사항이 승인되었습니다." });
                setComment("");
                onRefresh();
            } catch (error: any) {
                setMessage({ type: "error", text: error.message });
            } finally {
                setProcessingId(null);
            }
        });
    };

    const handleReject = (id: string) => {
        setProcessingId(id);
        startTransition(async () => {
            try {
                await rejectReviewItem(id, comment || undefined);
                setMessage({ type: "success", text: "변경 사항이 거절되었습니다." });
                setComment("");
                onRefresh();
            } catch (error: any) {
                setMessage({ type: "error", text: error.message });
            } finally {
                setProcessingId(null);
            }
        });
    };

    if (items.length === 0) {
        return (
            <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-400">검토 대기 중인 항목이 없습니다</h3>
                <p className="text-sm text-slate-500 mt-2">모든 변경 사항이 처리되었습니다.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Message Toast */}
            {message && (
                <div className={`p-3 rounded-lg flex items-center gap-2 ${message.type === "success"
                    ? "bg-green-900/30 text-green-400 border border-green-800"
                    : "bg-red-900/30 text-red-400 border border-red-800"
                    }`}>
                    {message.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    {message.text}
                    <button onClick={() => setMessage(null)} className="ml-auto text-sm hover:underline">닫기</button>
                </div>
            )}

            {/* Review Items */}
            {items.map((item) => {
                const seed = item.seed_item;
                const hasTarget = !!(seed?.resolved_target_symbol || seed?.target);
                const hasAntibody = !!seed?.antibody;
                const hasLinker = !!seed?.linker_family;
                const hasPayload = !!seed?.payload_family;
                const hasSmiles = !!seed?.payload_smiles_standardized || !!seed?.proxy_smiles_flag;

                return (
                    <div key={item.id} className="bg-slate-900/70 rounded-xl border border-slate-800 overflow-hidden">
                        {/* Header */}
                        <div className="p-4 border-b border-slate-800">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <span className="px-2 py-1 text-xs font-medium bg-yellow-900/30 text-yellow-400 rounded border border-yellow-800">
                                        {item.change_type}
                                    </span>
                                    <span className="font-medium text-white">
                                        {seed?.drug_name_canonical || "Unknown Drug"}
                                    </span>
                                    <span className="text-slate-500">•</span>
                                    <span className="text-sm text-slate-400">{item.field_name}</span>
                                </div>
                                <button
                                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                                    className="flex items-center gap-1 px-2 py-1 text-sm text-slate-400 hover:text-white transition-colors"
                                >
                                    <Eye className="w-4 h-4" />
                                    {expandedId === item.id ? "접기" : "Diff View"}
                                </button>
                            </div>

                            {/* Component Status Badges */}
                            <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs text-slate-500 mr-1">구성요소:</span>
                                <span className={`px-1.5 py-0.5 text-xs rounded ${hasTarget ? 'bg-blue-900/40 text-blue-400' : 'bg-slate-800 text-slate-500'}`}>
                                    Target: {seed?.resolved_target_symbol || seed?.target || '-'}
                                </span>
                                <span className={`px-1.5 py-0.5 text-xs rounded ${hasAntibody ? 'bg-cyan-900/40 text-cyan-400' : 'bg-slate-800 text-slate-500'}`}>
                                    Ab: {seed?.antibody || '-'}
                                </span>
                                <span className={`px-1.5 py-0.5 text-xs rounded ${hasLinker ? 'bg-purple-900/40 text-purple-400' : 'bg-slate-800 text-slate-500'}`}>
                                    Linker: {seed?.linker_family || '-'}
                                </span>
                                <span className={`px-1.5 py-0.5 text-xs rounded ${hasPayload ? 'bg-green-900/40 text-green-400' : 'bg-slate-800 text-slate-500'}`}>
                                    Payload: {seed?.payload_family || '-'}
                                </span>
                                {hasSmiles ? (
                                    <span className="px-1.5 py-0.5 text-xs rounded bg-emerald-900/40 text-emerald-400" title={seed?.payload_smiles_standardized || 'Proxy'}>
                                        SMILES: {seed?.proxy_smiles_flag ? 'Proxy' : '✓'}
                                    </span>
                                ) : (
                                    <span className="px-1.5 py-0.5 text-xs rounded bg-red-900/40 text-red-400">
                                        SMILES: ✗
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Diff View (Expanded) */}
                        {expandedId === item.id && (
                            <div className="p-4 bg-slate-950/50 border-b border-slate-800">
                                <div className="grid grid-cols-2 gap-4">
                                    {/* Old Value */}
                                    <div>
                                        <div className="text-xs text-red-400 font-medium mb-2 flex items-center gap-1">
                                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                            기존값 (삭제)
                                        </div>
                                        <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-3 font-mono text-sm text-red-300 break-all min-h-[60px]">
                                            {item.old_value || <span className="text-slate-500">(없음)</span>}
                                        </div>
                                    </div>
                                    {/* New Value */}
                                    <div>
                                        <div className="text-xs text-green-400 font-medium mb-2 flex items-center gap-1">
                                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                            신규값 (추가)
                                        </div>
                                        <div className="bg-green-950/30 border border-green-900/50 rounded-lg p-3 font-mono text-sm text-green-300 break-all min-h-[60px]">
                                            {item.new_value || <span className="text-slate-500">(없음)</span>}
                                        </div>
                                    </div>
                                </div>

                                {/* Source Info */}
                                {item.source_job && (
                                    <div className="mt-3 text-xs text-slate-500">
                                        Source: {item.source_job}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Actions */}
                        <div className="p-4 flex items-center gap-3">
                            <input
                                type="text"
                                placeholder="코멘트 (선택사항)"
                                value={expandedId === item.id ? comment : ""}
                                onChange={(e) => setComment(e.target.value)}
                                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={processingId === item.id}
                            />
                            <button
                                onClick={() => handleApprove(item.id)}
                                disabled={isPending || processingId === item.id}
                                className="flex items-center gap-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors"
                            >
                                {processingId === item.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <CheckCircle2 className="w-4 h-4" />
                                )}
                                Approve
                            </button>
                            <button
                                onClick={() => handleReject(item.id)}
                                disabled={isPending || processingId === item.id}
                                className="flex items-center gap-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors"
                            >
                                {processingId === item.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <XCircle className="w-4 h-4" />
                                )}
                                Reject
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
