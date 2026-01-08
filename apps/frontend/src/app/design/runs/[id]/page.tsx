"use client";

/**
 * Design Run 상세 페이지
 * 
 * /design/runs/[id] 경로
 */
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import CandidatesList from "@/components/design/CandidatesList";
import ScoreRadarChart from "@/components/design/ScoreRadarChart";

interface DesignRun {
    id: string;
    status: string;
    indication: string;
    strategy: string;
    target_ids: string[];
    created_at: string;
    started_at?: string;
    completed_at?: string;
    result_summary?: {
        total_combinations?: number;
        accepted_candidates?: number;
        rejected_candidates?: number;
        pareto_fronts?: number;
        top_candidates?: number;
        duration_ms?: number;
    };
}

interface Progress {
    phase: string;
    processed_candidates: number;
    accepted_candidates: number;
    rejected_candidates: number;
}

const STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-500",
    running: "bg-blue-500",
    completed: "bg-green-500",
    failed: "bg-red-500",
    cancelled: "bg-gray-500",
};

const PHASE_LABELS: Record<string, string> = {
    loading: "카탈로그 로딩",
    generating: "후보 생성",
    saving: "저장 중",
    pareto: "파레토 계산",
    evidence: "근거 생성",
    protocol: "프로토콜 생성",
    completed: "완료",
    failed: "실패",
};

export default function RunDetailPage() {
    const params = useParams();
    const router = useRouter();
    const runId = params?.id as string;

    const [run, setRun] = useState<DesignRun | null>(null);
    const [progress, setProgress] = useState<Progress | null>(null);
    const [loading, setLoading] = useState(true);
    const [cancelling, setCancelling] = useState(false);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    useEffect(() => {
        if (runId) {
            fetchRun();

            // Polling for running runs
            const interval = setInterval(() => {
                if (run?.status === "running" || run?.status === "pending") {
                    fetchRun();
                    fetchProgress();
                }
            }, 3000);

            return () => clearInterval(interval);
        }
    }, [runId, run?.status]);

    const fetchRun = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}`);
            if (res.ok) {
                const data = await res.json();
                setRun(data);
            }
        } catch (error) {
            console.error("Failed to fetch run:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchProgress = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/progress`);
            if (res.ok) {
                const data = await res.json();
                setProgress(data);
            }
        } catch (error) {
            console.error("Failed to fetch progress:", error);
        }
    };

    const handleCancel = async () => {
        if (!confirm("정말 취소하시겠습니까?")) return;

        setCancelling(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/cancel`, {
                method: "POST",
            });
            if (res.ok) {
                fetchRun();
            }
        } catch (error) {
            console.error("Failed to cancel:", error);
        } finally {
            setCancelling(false);
        }
    };

    const handleRerun = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/rerun`, {
                method: "POST",
            });
            if (res.ok) {
                const data = await res.json();
                router.push(`/design/runs/${data.run_id}`);
            }
        } catch (error) {
            console.error("Failed to rerun:", error);
        }
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleString("ko-KR");
    };

    const formatDuration = (ms?: number) => {
        if (!ms) return "-";
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}초`;
        return `${(ms / 60000).toFixed(1)}분`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
            </div>
        );
    }

    if (!run) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <p className="text-xl text-gray-400">실행을 찾을 수 없습니다.</p>
                    <Link href="/design/runs" className="text-blue-400 mt-4 block">
                        ← 목록으로
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
                    <div className="flex justify-between items-start">
                        <div>
                            <Link href="/design/runs" className="text-sm text-gray-400 hover:text-white mb-2 block">
                                ← Design Runs
                            </Link>
                            <h1 className="text-2xl font-bold flex items-center gap-3">
                                <span className={`w-3 h-3 rounded-full ${STATUS_COLORS[run.status]}`} />
                                {run.indication}
                            </h1>
                            <p className="text-sm text-gray-400 mt-1">
                                전략: {run.strategy} · 타겟: {run.target_ids?.length || 0}개
                            </p>
                        </div>

                        <div className="flex gap-2">
                            {(run.status === "running" || run.status === "pending") && (
                                <button
                                    onClick={handleCancel}
                                    disabled={cancelling}
                                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-50"
                                >
                                    {cancelling ? "취소 중..." : "취소"}
                                </button>
                            )}
                            {(run.status === "completed" || run.status === "failed") && (
                                <button
                                    onClick={handleRerun}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
                                >
                                    재실행
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Progress (Running) */}
                {run.status === "running" && progress && (
                    <div className="mb-6 bg-gray-800 rounded-xl p-4 border border-gray-700">
                        <div className="flex items-center gap-4">
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
                            <div className="flex-1">
                                <p className="font-medium">{PHASE_LABELS[progress.phase] || progress.phase}</p>
                                <p className="text-sm text-gray-400">
                                    처리: {progress.processed_candidates?.toLocaleString()} ·
                                    수락: {progress.accepted_candidates?.toLocaleString()} ·
                                    거절: {progress.rejected_candidates?.toLocaleString()}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Stats Grid */}
                {run.status === "completed" && run.result_summary && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                        {[
                            { label: "전체 조합", value: run.result_summary.total_combinations?.toLocaleString() },
                            { label: "수락 후보", value: run.result_summary.accepted_candidates?.toLocaleString(), color: "text-green-400" },
                            { label: "거절 후보", value: run.result_summary.rejected_candidates?.toLocaleString(), color: "text-red-400" },
                            { label: "파레토 프론트", value: run.result_summary.pareto_fronts },
                            { label: "실행 시간", value: formatDuration(run.result_summary.duration_ms) },
                        ].map((stat, i) => (
                            <div key={i} className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                                <p className="text-sm text-gray-400">{stat.label}</p>
                                <p className={`text-2xl font-bold mt-1 ${stat.color || ""}`}>
                                    {stat.value || "-"}
                                </p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Candidates (Completed) */}
                {run.status === "completed" && (
                    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                            <h2 className="font-semibold">후보 목록</h2>
                            <Link
                                href={`/design/runs/${runId}/compare`}
                                className="text-sm text-blue-400 hover:text-blue-300"
                            >
                                비교하기 →
                            </Link>
                        </div>
                        <CandidatesList runId={runId} />
                    </div>
                )}

                {/* Timeline */}
                <div className="mt-6 bg-gray-800 rounded-xl p-4 border border-gray-700">
                    <h3 className="font-medium mb-3">타임라인</h3>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">생성</span>
                            <span>{formatDate(run.created_at)}</span>
                        </div>
                        {run.started_at && (
                            <div className="flex justify-between">
                                <span className="text-gray-400">시작</span>
                                <span>{formatDate(run.started_at)}</span>
                            </div>
                        )}
                        {run.completed_at && (
                            <div className="flex justify-between">
                                <span className="text-gray-400">완료</span>
                                <span>{formatDate(run.completed_at)}</span>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
