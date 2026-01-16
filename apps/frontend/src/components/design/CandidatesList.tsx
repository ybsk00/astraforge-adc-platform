"use client";

/**
 * 후보 목록 컴포넌트
 */
import { useState, useEffect, useCallback } from "react";

interface Candidate {
    id: string;
    candidate_hash: string;
    target_name?: string;
    payload_name?: string;
    eng_fit: number;
    bio_fit: number;
    safety_fit: number;
    evidence_fit: number;
    pareto_rank?: number;
}

interface CandidatesListProps {
    runId: string;
    onSelect?: (candidate: Candidate) => void;
}

const SCORE_COLORS: Record<string, string> = {
    high: "text-green-400",
    medium: "text-yellow-400",
    low: "text-red-400",
};

function getScoreColor(score: number): string {
    if (score >= 70) return SCORE_COLORS.high;
    if (score >= 40) return SCORE_COLORS.medium;
    return SCORE_COLORS.low;
}

export default function CandidatesList({ runId, onSelect }: CandidatesListProps) {
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState("eng_fit");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    const fetchCandidates = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                sort_by: sortBy,
                sort_order: sortOrder,
                limit: "50",
            });

            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/candidates?${params}`);
            if (res.ok) {
                const data = await res.json();
                setCandidates(data.items || []);
            }
        } catch (error) {
            console.error("Failed to fetch candidates:", error);
        } finally {
            setLoading(false);
        }
    }, [runId, sortBy, sortOrder, ENGINE_URL]);

    useEffect(() => {
        fetchCandidates();
    }, [fetchCandidates]);

    const handleSort = (field: string) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortBy(field);
            setSortOrder("desc");
        }
    };

    const handleSelectToggle = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) {
            newSelected.delete(id);
        } else {
            newSelected.add(id);
        }
        setSelectedIds(newSelected);
    };

    const SortButton = ({ field, label }: { field: string; label: string }) => (
        <button
            onClick={() => handleSort(field)}
            className={`px-2 py-1 text-xs rounded transition-all ${sortBy === field
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
        >
            {label} {sortBy === field && (sortOrder === "desc" ? "↓" : "↑")}
        </button>
    );

    if (loading) {
        return (
            <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
            </div>
        );
    }

    if (candidates.length === 0) {
        return (
            <div className="p-8 text-center text-gray-400">
                후보가 없습니다.
            </div>
        );
    }

    return (
        <div>
            {/* Sort Controls */}
            <div className="px-4 py-2 bg-gray-750 border-b border-gray-700 flex gap-2 flex-wrap">
                <span className="text-sm text-gray-400 mr-2">정렬:</span>
                <SortButton field="eng_fit" label="Eng-Fit" />
                <SortButton field="bio_fit" label="Bio-Fit" />
                <SortButton field="safety_fit" label="Safety-Fit" />
                <SortButton field="evidence_fit" label="Evidence-Fit" />
            </div>

            {/* Candidates Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-750">
                        <tr className="text-left text-sm text-gray-400">
                            <th className="px-4 py-2 w-10">
                                <input
                                    type="checkbox"
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setSelectedIds(new Set(candidates.map((c) => c.id)));
                                        } else {
                                            setSelectedIds(new Set());
                                        }
                                    }}
                                    checked={selectedIds.size === candidates.length && candidates.length > 0}
                                />
                            </th>
                            <th className="px-4 py-2">Rank</th>
                            <th className="px-4 py-2">Target</th>
                            <th className="px-4 py-2">Payload</th>
                            <th className="px-4 py-2 text-center">Eng</th>
                            <th className="px-4 py-2 text-center">Bio</th>
                            <th className="px-4 py-2 text-center">Safety</th>
                            <th className="px-4 py-2 text-center">Evidence</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {candidates.map((candidate, index) => (
                            <tr
                                key={candidate.id}
                                className="hover:bg-gray-750 cursor-pointer transition-all"
                                onClick={() => onSelect?.(candidate)}
                            >
                                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                                    <input
                                        type="checkbox"
                                        checked={selectedIds.has(candidate.id)}
                                        onChange={() => handleSelectToggle(candidate.id)}
                                        className="accent-blue-500"
                                    />
                                </td>
                                <td className="px-4 py-3">
                                    {candidate.pareto_rank != null ? (
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${candidate.pareto_rank === 0
                                            ? "bg-yellow-500/20 text-yellow-400"
                                            : "bg-gray-600 text-gray-300"
                                            }`}>
                                            P{candidate.pareto_rank}
                                        </span>
                                    ) : (
                                        <span className="text-gray-500">#{index + 1}</span>
                                    )}
                                </td>
                                <td className="px-4 py-3 font-medium">
                                    {candidate.target_name || "-"}
                                </td>
                                <td className="px-4 py-3 text-gray-400">
                                    {candidate.payload_name || "-"}
                                </td>
                                <td className={`px-4 py-3 text-center font-medium ${getScoreColor(candidate.eng_fit)}`}>
                                    {candidate.eng_fit.toFixed(1)}
                                </td>
                                <td className={`px-4 py-3 text-center font-medium ${getScoreColor(candidate.bio_fit)}`}>
                                    {candidate.bio_fit.toFixed(1)}
                                </td>
                                <td className={`px-4 py-3 text-center font-medium ${getScoreColor(candidate.safety_fit)}`}>
                                    {candidate.safety_fit.toFixed(1)}
                                </td>
                                <td className={`px-4 py-3 text-center font-medium ${getScoreColor(candidate.evidence_fit)}`}>
                                    {candidate.evidence_fit.toFixed(1)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Selected Actions */}
            {selectedIds.size > 0 && (
                <div className="px-4 py-3 bg-blue-900/30 border-t border-blue-700 flex justify-between items-center">
                    <span className="text-sm">
                        {selectedIds.size}개 선택됨
                    </span>
                    <button
                        onClick={() => {
                            const ids = Array.from(selectedIds).join(",");
                            window.location.href = `/design/runs/${runId}/compare?ids=${ids}`;
                        }}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                    >
                        비교하기
                    </button>
                </div>
            )}
        </div>
    );
}
