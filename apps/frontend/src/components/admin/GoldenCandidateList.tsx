"use client";

import { useState } from "react";
import { GoldenCandidate, updateCandidateReviewStatus } from "@/lib/actions/golden-set";
import { Check, X, Search, Filter, FileText, Eye } from "lucide-react";
import { toast } from "sonner";
import EvidenceModal from "./EvidenceModal";

interface Props {
    candidates: GoldenCandidate[];
}

export default function GoldenCandidateList({ candidates = [] }: Props) {
    const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
    const [search, setSearch] = useState("");
    const [selectedCandidate, setSelectedCandidate] = useState<GoldenCandidate | null>(null);

    const filtered = candidates.filter(c => {
        if (filter !== 'all' && c.review_status !== filter) return false;
        if (search) {
            const term = search.toLowerCase();
            return (
                c.drug_name.toLowerCase().includes(term) ||
                c.target.toLowerCase().includes(term) ||
                c.antibody.toLowerCase().includes(term) ||
                c.payload.toLowerCase().includes(term)
            );
        }
        return true;
    });

    const handleStatusUpdate = async (id: string, status: 'approved' | 'rejected') => {
        try {
            await updateCandidateReviewStatus(id, status);
            toast.success(`후보 상태가 ${status === 'approved' ? '승인' : '거절'}되었습니다.`);
        } catch (error) {
            toast.error("상태 업데이트 실패");
        }
    };

    return (
        <>
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                {/* Toolbar */}
                <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row gap-4 justify-between items-center">
                    <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 w-full md:w-64">
                        <Search className="w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search candidates..."
                            className="bg-transparent border-none outline-none text-sm text-white w-full placeholder:text-slate-600"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-slate-500" />
                        <select
                            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white outline-none"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value as any)}
                        >
                            <option value="all">모든 상태</option>
                            <option value="pending">대기 중 (Pending)</option>
                            <option value="approved">승인됨 (Approved)</option>
                            <option value="rejected">거절됨 (Rejected)</option>
                        </select>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-950/50 text-xs text-slate-400 uppercase tracking-wider">
                                <th className="px-6 py-4 font-semibold">Drug Name</th>
                                <th className="px-6 py-4 font-semibold">Target</th>
                                <th className="px-6 py-4 font-semibold">Antibody</th>
                                <th className="px-6 py-4 font-semibold">Payload</th>
                                <th className="px-6 py-4 font-semibold">Linker</th>
                                <th className="px-6 py-4 font-semibold text-center">Score</th>
                                <th className="px-6 py-4 font-semibold text-center">Evidence</th>
                                <th className="px-6 py-4 font-semibold text-center">Status</th>
                                <th className="px-6 py-4 font-semibold text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {filtered.map((c) => (
                                <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">{c.drug_name}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{c.target}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{c.antibody}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{c.payload}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{c.linker}</td>
                                    <td className="px-6 py-4 text-sm text-center">
                                        <span className="px-2 py-1 bg-slate-800 rounded text-slate-300 font-mono text-xs">
                                            {c.score.toFixed(2)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <button
                                            onClick={() => setSelectedCandidate(c)}
                                            className="p-1.5 rounded hover:bg-blue-900/30 text-slate-500 hover:text-blue-400 transition-colors"
                                            title="View Evidence"
                                        >
                                            <Eye className="w-4 h-4" />
                                        </button>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${c.review_status === 'approved' ? 'bg-green-900/20 text-green-400 border-green-800' :
                                            c.review_status === 'rejected' ? 'bg-red-900/20 text-red-400 border-red-800' :
                                                'bg-amber-900/20 text-amber-400 border-amber-800'
                                            }`}>
                                            {c.review_status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleStatusUpdate(c.id, 'approved')}
                                                disabled={c.review_status === 'approved'}
                                                className="p-1.5 rounded hover:bg-green-900/30 text-slate-500 hover:text-green-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                                title="Approve"
                                            >
                                                <Check className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleStatusUpdate(c.id, 'rejected')}
                                                disabled={c.review_status === 'rejected'}
                                                className="p-1.5 rounded hover:bg-red-900/30 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                                title="Reject"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
                    Showing {filtered.length} of {candidates.length} candidates
                </div>
            </div>

            {selectedCandidate && (
                <EvidenceModal
                    candidateId={selectedCandidate.id}
                    candidateName={selectedCandidate.drug_name}
                    isOpen={!!selectedCandidate}
                    onClose={() => setSelectedCandidate(null)}
                    fallbackEvidence={selectedCandidate.evidence_json}
                />
            )}
        </>
    );
}
