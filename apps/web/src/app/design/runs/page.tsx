"use client";

/**
 * Design Runs 목록 페이지
 * 
 * /design/runs 경로
 */
import { useState, useEffect } from "react";
import Link from "next/link";
import NewRunModal from "@/components/design/NewRunModal";

interface DesignRun {
    id: string;
    status: string;
    indication: string;
    strategy: string;
    target_ids: string[];
    created_at: string;
    result_summary?: {
        accepted_candidates?: number;
        rejected_candidates?: number;
        pareto_fronts?: number;
        duration_ms?: number;
    };
}

const STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-500",
    running: "bg-blue-500 animate-pulse",
    completed: "bg-green-500",
    failed: "bg-red-500",
    cancelled: "bg-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
    pending: "대기 중",
    running: "실행 중",
    completed: "완료",
    failed: "실패",
    cancelled: "취소됨",
};

export default function DesignRunsPage() {
    const [runs, setRuns] = useState<DesignRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [showNewModal, setShowNewModal] = useState(false);
    const [statusFilter, setStatusFilter] = useState<string>("");

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    useEffect(() => {
        fetchRuns();
    }, [statusFilter]);

    const fetchRuns = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ limit: "20" });
            if (statusFilter) {
                params.set("status", statusFilter);
            }

            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs?${params}`);
            const data = await res.json();
            setRuns(data.items || []);
        } catch (error) {
            console.error("Failed to fetch runs:", error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString("ko-KR", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const formatDuration = (ms?: number) => {
        if (!ms) return "-";
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}min`;
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <header className="bg-gray-800 border-b border-gray-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                Design Runs
                            </h1>
                            <p className="text-sm text-gray-400 mt-1">
                                ADC 후보 설계 실행 관리
                            </p>
                        </div>
                        <button
                            onClick={() => setShowNewModal(true)}
                            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg font-medium transition-all"
                        >
                            + 새 실행
                        </button>
                    </div>
                </div>
            </header>

            {/* Filters */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex gap-2">
                    {["", "pending", "running", "completed", "failed"].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${statusFilter === status
                                    ? "bg-blue-600 text-white"
                                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                                }`}
                        >
                            {status === "" ? "전체" : STATUS_LABELS[status] || status}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                {loading ? (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
                    </div>
                ) : runs.length === 0 ? (
                    <div className="text-center py-12">
                        <p className="text-gray-400">실행 내역이 없습니다.</p>
                        <button
                            onClick={() => setShowNewModal(true)}
                            className="mt-4 text-blue-400 hover:text-blue-300"
                        >
                            첫 번째 실행 시작하기 →
                        </button>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {runs.map((run) => (
                            <Link
                                key={run.id}
                                href={`/design/runs/${run.id}`}
                                className="block bg-gray-800 rounded-xl p-4 hover:bg-gray-750 transition-all border border-gray-700 hover:border-gray-600"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3">
                                            <span
                                                className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[run.status] || "bg-gray-500"}`}
                                            />
                                            <span className="font-medium">{run.indication}</span>
                                            <span className="text-sm text-gray-400 bg-gray-700 px-2 py-0.5 rounded">
                                                {run.strategy}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400 mt-2">
                                            타겟 {run.target_ids?.length || 0}개 · {formatDate(run.created_at)}
                                        </p>
                                    </div>

                                    {run.status === "completed" && run.result_summary && (
                                        <div className="text-right text-sm">
                                            <p className="text-green-400 font-medium">
                                                {run.result_summary.accepted_candidates?.toLocaleString()} 후보
                                            </p>
                                            <p className="text-gray-400">
                                                파레토 {run.result_summary.pareto_fronts}개 · {formatDuration(run.result_summary.duration_ms)}
                                            </p>
                                        </div>
                                    )}

                                    {run.status === "running" && (
                                        <div className="text-right text-sm text-blue-400">
                                            실행 중...
                                        </div>
                                    )}
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>

            {/* New Run Modal */}
            {showNewModal && (
                <NewRunModal
                    onClose={() => setShowNewModal(false)}
                    onCreated={() => {
                        setShowNewModal(false);
                        fetchRuns();
                    }}
                />
            )}
        </div>
    );
}
