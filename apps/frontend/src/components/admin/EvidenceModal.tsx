"use client";

import { useState, useEffect } from "react";
import { getGoldenCandidateEvidence } from "@/lib/actions/golden-set";
import { X, ExternalLink, Loader2, FileText, AlertCircle } from "lucide-react";

interface Props {
    candidateId: string;
    candidateName: string;
    isOpen: boolean;
    onClose: () => void;
    fallbackEvidence?: any; // evidence_json from golden_candidates
}

export default function EvidenceModal({ candidateId, candidateName, isOpen, onClose, fallbackEvidence }: Props) {
    const [evidence, setEvidence] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen && candidateId) {
            fetchEvidence();
        }
    }, [isOpen, candidateId]);

    const fetchEvidence = async () => {
        setLoading(true);
        try {
            const data = await getGoldenCandidateEvidence(candidateId);
            setEvidence(data);
        } catch (error) {
            console.error("Failed to load evidence", error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-400" />
                        <h3 className="text-lg font-bold text-white">
                            근거 자료 (Evidence)
                            <span className="ml-2 text-sm font-normal text-slate-400">- {candidateName}</span>
                        </h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                            <Loader2 className="w-8 h-8 animate-spin mb-2" />
                            <p>근거 데이터를 불러오는 중...</p>
                        </div>
                    ) : evidence.length > 0 ? (
                        evidence.map((item) => (
                            <div key={item.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                                <div className="flex items-start justify-between mb-2">
                                    <span className="px-2 py-0.5 text-xs font-bold bg-blue-900/30 text-blue-400 rounded border border-blue-800 uppercase">
                                        {item.source}
                                    </span>
                                    {item.url && (
                                        <a
                                            href={item.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-1 text-xs text-slate-400 hover:text-blue-400 transition-colors"
                                        >
                                            원본 보기 <ExternalLink className="w-3 h-3" />
                                        </a>
                                    )}
                                </div>
                                <p className="text-sm text-slate-300 leading-relaxed">
                                    {item.snippet || "No snippet available."}
                                </p>
                                {item.ref_id && (
                                    <p className="text-xs text-slate-500 mt-2">
                                        Ref ID: {item.ref_id}
                                    </p>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-8">
                            <div className="inline-flex p-3 rounded-full bg-slate-800/50 mb-3">
                                <AlertCircle className="w-6 h-6 text-slate-500" />
                            </div>
                            <p className="text-slate-400 font-medium">등록된 근거 데이터가 없습니다.</p>

                            {/* Fallback to evidence_json if available */}
                            {fallbackEvidence && (
                                <div className="mt-4 text-left bg-slate-950 p-4 rounded-lg border border-slate-800">
                                    <p className="text-xs text-slate-500 mb-2">백업 데이터 (JSON):</p>
                                    <pre className="text-xs text-slate-400 overflow-x-auto whitespace-pre-wrap">
                                        {JSON.stringify(fallbackEvidence, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-slate-800 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm transition-colors"
                    >
                        닫기
                    </button>
                </div>
            </div>
        </div>
    );
}
