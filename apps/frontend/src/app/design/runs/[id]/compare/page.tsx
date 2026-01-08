"use client";

/**
 * 후보 비교 페이지
 * 
 * /design/runs/[id]/compare 경로
 */
import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import ScoreRadarChart from "@/components/design/ScoreRadarChart";

interface Candidate {
    id: string;
    candidate_hash: string;
    snapshot: {
        target?: { name?: string; gene_symbol?: string };
        payload?: { name?: string };
        linker?: { name?: string };
        antibody?: { name?: string };
    };
    candidate_scores?: {
        eng_fit: number;
        bio_fit: number;
        safety_fit: number;
        evidence_fit: number;
        score_components?: Record<string, any>;
    }[];
}

export default function ComparePage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const runId = params?.id as string;
    const candidateIds = searchParams?.get("ids")?.split(",") || [];

    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    useEffect(() => {
        if (candidateIds.length > 0) {
            fetchCandidates();
        } else {
            setLoading(false);
        }
    }, [candidateIds.join(",")]);

    const fetchCandidates = async () => {
        setLoading(true);
        try {
            const results = await Promise.all(
                candidateIds.map(async (id) => {
                    const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/candidates/${id}`);
                    if (res.ok) {
                        return res.json();
                    }
                    return null;
                })
            );
            setCandidates(results.filter(Boolean));
        } catch (error) {
            console.error("Failed to fetch candidates:", error);
        } finally {
            setLoading(false);
        }
    };

    const getScores = (candidate: Candidate) => {
        const scores = candidate.candidate_scores?.[0];
        return {
            eng_fit: scores?.eng_fit || 0,
            bio_fit: scores?.bio_fit || 0,
            safety_fit: scores?.safety_fit || 0,
            evidence_fit: scores?.evidence_fit || 0,
        };
    };

    const getScoreColor = (score: number) => {
        if (score >= 70) return "text-green-400";
        if (score >= 40) return "text-yellow-400";
        return "text-red-400";
    };

    const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
            </div>
        );
    }

    if (candidates.length === 0) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <p className="text-xl text-gray-400">비교할 후보를 선택해주세요.</p>
                    <Link href={`/design/runs/${runId}`} className="text-blue-400 mt-4 block">
                        ← 후보 목록으로
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <header className="bg-gray-800 border-b border-gray-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <Link href={`/design/runs/${runId}`} className="text-sm text-gray-400 hover:text-white mb-2 block">
                        ← 실행 상세
                    </Link>
                    <h1 className="text-2xl font-bold">후보 비교</h1>
                    <p className="text-sm text-gray-400 mt-1">
                        {candidates.length}개 후보 비교 중
                    </p>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Radar Charts */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
                    <h2 className="font-semibold mb-4">4축 스코어 비교</h2>
                    <div className="flex flex-wrap justify-center gap-8">
                        {candidates.map((candidate, i) => (
                            <div key={candidate.id} className="text-center">
                                <ScoreRadarChart
                                    scores={getScores(candidate)}
                                    size={180}
                                    color={COLORS[i % COLORS.length]}
                                />
                                <p className="mt-2 text-sm font-medium" style={{ color: COLORS[i % COLORS.length] }}>
                                    {candidate.snapshot.target?.name || `후보 ${i + 1}`}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Comparison Table */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-700">
                        <h2 className="font-semibold">상세 비교</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-750">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm text-gray-400">항목</th>
                                    {candidates.map((candidate, i) => (
                                        <th
                                            key={candidate.id}
                                            className="px-4 py-3 text-center text-sm"
                                            style={{ color: COLORS[i % COLORS.length] }}
                                        >
                                            {candidate.snapshot.target?.name || `후보 ${i + 1}`}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {/* Target */}
                                <tr>
                                    <td className="px-4 py-3 text-gray-400">타겟</td>
                                    {candidates.map((c) => (
                                        <td key={c.id} className="px-4 py-3 text-center">
                                            {c.snapshot.target?.name || "-"}
                                            {c.snapshot.target?.gene_symbol && (
                                                <span className="text-xs text-gray-500 ml-1">
                                                    ({c.snapshot.target.gene_symbol})
                                                </span>
                                            )}
                                        </td>
                                    ))}
                                </tr>

                                {/* Payload */}
                                <tr>
                                    <td className="px-4 py-3 text-gray-400">페이로드</td>
                                    {candidates.map((c) => (
                                        <td key={c.id} className="px-4 py-3 text-center">
                                            {c.snapshot.payload?.name || "-"}
                                        </td>
                                    ))}
                                </tr>

                                {/* Linker */}
                                <tr>
                                    <td className="px-4 py-3 text-gray-400">링커</td>
                                    {candidates.map((c) => (
                                        <td key={c.id} className="px-4 py-3 text-center">
                                            {c.snapshot.linker?.name || "-"}
                                        </td>
                                    ))}
                                </tr>

                                {/* Scores */}
                                {["eng_fit", "bio_fit", "safety_fit", "evidence_fit"].map((scoreKey) => (
                                    <tr key={scoreKey}>
                                        <td className="px-4 py-3 text-gray-400 capitalize">
                                            {scoreKey.replace("_", "-")}
                                        </td>
                                        {candidates.map((c) => {
                                            const score = getScores(c)[scoreKey as keyof ReturnType<typeof getScores>];
                                            return (
                                                <td
                                                    key={c.id}
                                                    className={`px-4 py-3 text-center font-bold text-lg ${getScoreColor(score)}`}
                                                >
                                                    {score.toFixed(1)}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}

                                {/* Total */}
                                <tr className="bg-gray-750">
                                    <td className="px-4 py-3 font-medium">종합 (가중합)</td>
                                    {candidates.map((c) => {
                                        const scores = getScores(c);
                                        const total = (
                                            scores.eng_fit * 0.25 +
                                            scores.bio_fit * 0.35 +
                                            scores.safety_fit * 0.30 +
                                            scores.evidence_fit * 0.10
                                        );
                                        return (
                                            <td
                                                key={c.id}
                                                className={`px-4 py-3 text-center font-bold text-xl ${getScoreColor(total)}`}
                                            >
                                                {total.toFixed(1)}
                                            </td>
                                        );
                                    })}
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Score Components Detail */}
                <div className="mt-6 bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h2 className="font-semibold mb-4">스코어 컴포넌트 상세</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {candidates.map((candidate, i) => {
                            const components = candidate.candidate_scores?.[0]?.score_components;
                            if (!components) return null;

                            return (
                                <div
                                    key={candidate.id}
                                    className="p-4 bg-gray-750 rounded-lg border-l-4"
                                    style={{ borderColor: COLORS[i % COLORS.length] }}
                                >
                                    <h3 className="font-medium mb-3" style={{ color: COLORS[i % COLORS.length] }}>
                                        {candidate.snapshot.target?.name || `후보 ${i + 1}`}
                                    </h3>
                                    <div className="space-y-3 text-sm">
                                        {Object.entries(components).map(([fitType, data]: [string, any]) => (
                                            <div key={fitType}>
                                                <p className="text-gray-400 uppercase text-xs mb-1">{fitType.replace("_", "-")}</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {Object.entries(data.terms || {}).map(([term, value]: [string, any]) => (
                                                        <span
                                                            key={term}
                                                            className={`px-2 py-0.5 rounded text-xs ${value > 30 ? "bg-red-900/50" : "bg-gray-700"
                                                                }`}
                                                        >
                                                            {term}: {typeof value === "number" ? value.toFixed(1) : value}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </main>
        </div>
    );
}
