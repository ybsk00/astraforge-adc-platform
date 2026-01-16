"use client";

/**
 * 파레토 프론트 시각화 컴포넌트
 */
import { useState, useEffect, useCallback } from "react";
import ScoreRadarChart from "./ScoreRadarChart";

interface Candidate {
    id: string;
    target_name?: string;
    payload_name?: string;
    eng_fit: number;
    bio_fit: number;
    safety_fit: number;
    evidence_fit: number;
    pareto_rank: number;
}

interface ParetoFrontViewProps {
    runId: string;
}

export default function ParetoFrontView({ runId }: ParetoFrontViewProps) {
    const [fronts, setFronts] = useState<Record<number, Candidate[]>>({});
    const [loading, setLoading] = useState(true);
    const [activeFront, setActiveFront] = useState(0);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    const fetchParetoData = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/pareto`);
            if (res.ok) {
                const data = await res.json();
                // 백엔드 응답(data.fronts)을 랭크별로 그룹화된 객체로 변환
                const grouped: Record<number, Candidate[]> = {};
                (data.fronts || []).forEach((front: any) => {
                    const rank = front.front_index;
                    grouped[rank] = (front.run_pareto_members || []).map((m: any) => ({
                        id: m.candidate_id,
                        pareto_rank: rank,
                        // 스코어 데이터는 m.candidates 또는 별도 조인이 필요할 수 있으나 
                        // 현재는 m 내에 포함되어 있다고 가정하거나 m.candidate_id로 매핑
                        ...m.candidates_snapshot // 스코어 포함된 스냅샷 가정
                    }));
                });
                setFronts(grouped);
            }
        } catch (error) {
            console.error("Failed to fetch pareto data:", error);
        } finally {
            setLoading(false);
        }
    }, [runId, ENGINE_URL]);

    useEffect(() => {
        fetchParetoData();
    }, [fetchParetoData]);

    if (loading) return <div className="p-8 text-center animate-pulse">파레토 데이터 로드 중...</div>;

    const ranks = Object.keys(fronts).map(Number).sort((a, b) => a - b);

    return (
        <div className="space-y-6">
            {/* Front Tabs */}
            <div className="flex gap-2 border-b border-gray-700">
                {ranks.map((rank) => (
                    <button
                        key={rank}
                        onClick={() => setActiveFront(rank)}
                        className={`px-4 py-2 text-sm font-medium transition-all ${activeFront === rank
                            ? "border-b-2 border-blue-500 text-blue-400"
                            : "text-gray-400 hover:text-gray-200"
                            }`}
                    >
                        Front {rank} ({fronts[rank].length})
                    </button>
                ))}
            </div>

            {/* Candidates in Active Front */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {fronts[activeFront]?.map((cand) => (
                    <div key={cand.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-blue-500/50 transition-all">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h4 className="font-bold text-gray-100">{cand.target_name} + {cand.payload_name}</h4>
                                <p className="text-xs text-gray-500">ID: {cand.id.substring(0, 8)}</p>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${activeFront === 0 ? "bg-yellow-500/20 text-yellow-400" : "bg-gray-700 text-gray-400"
                                }`}>
                                P{activeFront}
                            </span>
                        </div>

                        <div className="flex justify-center bg-gray-900/50 rounded py-2">
                            <ScoreRadarChart
                                scores={{
                                    eng_fit: cand.eng_fit,
                                    bio_fit: cand.bio_fit || 0,
                                    safety_fit: cand.safety_fit || 0,
                                    evidence_fit: cand.evidence_fit || 0
                                }}
                                size={160}
                                showLabels={true}
                            />
                        </div>

                        <div className="mt-4 grid grid-cols-2 gap-2 text-center">
                            <div className="bg-gray-700/30 rounded p-1">
                                <p className="text-[10px] text-gray-500">Bio</p>
                                <p className="text-xs font-bold text-green-400">{cand.bio_fit.toFixed(1)}</p>
                            </div>
                            <div className="bg-gray-700/30 rounded p-1">
                                <p className="text-[10px] text-gray-500">Safety</p>
                                <p className="text-xs font-bold text-yellow-400">{cand.safety_fit.toFixed(1)}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
