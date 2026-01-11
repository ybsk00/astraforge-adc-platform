"use client";

/**
 * Golden Set 검증 트렌드 시각화 컴포넌트
 */
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from "recharts";
import { Activity, TrendingDown, TrendingUp, AlertCircle } from "lucide-react";

interface ValidationRun {
    id: string;
    created_at: string;
    pass: boolean;
    scoring_version: string;
    summary: {
        MAE?: number;
        Spearman?: number;
        TopKOverlap?: number;
    };
}

export default function GoldenValidationTrend() {
    const [data, setData] = useState<ValidationRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeAxis, setActiveAxis] = useState("overall");

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    useEffect(() => {
        fetchTrendData();
    }, []);

    const fetchTrendData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/admin/golden/trend`);
            if (res.ok) {
                const result = await res.json();
                // 날짜순 정렬
                const sorted = result.items.sort((a: any, b: any) =>
                    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                );
                setData(sorted);
            }
        } catch (error) {
            console.error("Failed to fetch trend data:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="h-64 flex items-center justify-center bg-gray-900/50 rounded-xl animate-pulse text-gray-500">트렌드 데이터 로드 중...</div>;

    if (data.length === 0) return (
        <div className="h-64 flex flex-col items-center justify-center bg-gray-900/50 rounded-xl border border-dashed border-gray-700 text-gray-500">
            <AlertCircle className="w-8 h-8 mb-2 opacity-20" />
            <p className="text-sm">검증 데이터가 없습니다.</p>
        </div>
    );

    const latest = data[data.length - 1];

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                        <p className="text-xs text-gray-400">최신 MAE (오차)</p>
                        <TrendingDown className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{latest.summary.MAE?.toFixed(2) || "N/A"}</p>
                    <p className="text-[10px] text-gray-500 mt-1">Lower is better | {latest.scoring_version}</p>
                </div>
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                        <p className="text-xs text-gray-400">최신 Spearman (상관성)</p>
                        <TrendingUp className="w-4 h-4 text-blue-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{latest.summary.Spearman?.toFixed(2) || "N/A"}</p>
                    <p className="text-[10px] text-gray-500 mt-1">Higher is better | {latest.scoring_version}</p>
                </div>
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                        <p className="text-xs text-gray-400">최신 Pass 여부</p>
                        <Activity className={`w-4 h-4 ${latest.pass ? "text-green-400" : "text-red-400"}`} />
                    </div>
                    <p className={`text-2xl font-bold ${latest.pass ? "text-green-400" : "text-red-400"}`}>
                        {latest.pass ? "PASSED" : "FAILED"}
                    </p>
                    <p className="text-[10px] text-gray-500 mt-1">Based on thresholds</p>
                </div>
            </div>

            {/* Chart */}
            <div className="bg-gray-800 border border-gray-700 p-6 rounded-xl">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-bold text-gray-200">산식 성능 트렌드 (MAE & Spearman)</h3>
                    <div className="flex bg-gray-900 rounded-lg p-1">
                        {["overall", "Bio", "Safety", "Eng"].map((axis) => (
                            <button
                                key={axis}
                                onClick={() => setActiveAxis(axis)}
                                className={`px-3 py-1 text-[10px] font-bold rounded transition-all ${activeAxis === axis ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-300"
                                    }`}
                            >
                                {axis.toUpperCase()}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                            <XAxis
                                dataKey="created_at"
                                stroke="#9CA3AF"
                                fontSize={10}
                                tickFormatter={(str) => new Date(str).toLocaleDateString()}
                            />
                            <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={10} label={{ value: 'MAE', angle: -90, position: 'insideLeft', fill: '#9CA3AF', fontSize: 10 }} />
                            <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" fontSize={10} label={{ value: 'Spearman', angle: 90, position: 'insideRight', fill: '#9CA3AF', fontSize: 10 }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }}
                                itemStyle={{ fontSize: '12px' }}
                            />
                            <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '20px' }} />
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="summary.MAE"
                                name="MAE (오차)"
                                stroke="#F87171"
                                strokeWidth={2}
                                dot={{ r: 4, fill: '#F87171' }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="summary.Spearman"
                                name="Spearman (상관성)"
                                stroke="#60A5FA"
                                strokeWidth={2}
                                dot={{ r: 4, fill: '#60A5FA' }}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
