"use client";

/**
 * Golden Set 검증 트렌드 시각화 컴포넌트
 */
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
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
    metrics: {
        [axis: string]: {
            MAE?: number;
            Spearman?: number;
            TopKOverlap?: number;
        };
    };
}

export default function GoldenValidationTrend() {
    const [data, setData] = useState<ValidationRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeAxis, setActiveAxis] = useState("overall");

    useEffect(() => {
        fetchTrendData();
    }, []);

    const fetchTrendData = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`/api/admin/golden/trend`);
            if (res.ok) {
                const result = await res.json();
                // 날짜순 정렬
                const sorted = result.items.sort((a: ValidationRun, b: ValidationRun) =>
                    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                );
                setData(sorted);
            } else {
                const errorData = await res.json().catch(() => ({}));
                console.error("Failed to fetch trend data:", res.status, res.statusText, errorData);
                setError(`서버 응답 오류: ${res.status} ${errorData.details || errorData.error || ''}`);
            }
        } catch (error) {
            console.error("Failed to fetch trend data:", error);
            setError("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="h-64 flex items-center justify-center bg-gray-900/50 rounded-xl animate-pulse text-gray-500">트렌드 데이터 로드 중...</div>;

    if (error) return (
        <div className="h-64 flex flex-col items-center justify-center bg-red-900/10 rounded-xl border border-dashed border-red-700/50 text-red-400 p-6 text-center">
            <AlertCircle className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm font-bold mb-1">데이터 로드 실패</p>
            <p className="text-xs opacity-70 mb-4">{error}</p>
            <button
                onClick={fetchTrendData}
                className="px-4 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-700/50 rounded-lg text-xs transition-all"
            >
                다시 시도
            </button>
        </div>
    );

    if (data.length === 0) return (
        <div className="h-64 flex flex-col items-center justify-center bg-gray-900/50 rounded-xl border border-dashed border-gray-700 text-gray-500">
            <AlertCircle className="w-8 h-8 mb-2 opacity-20" />
            <p className="text-sm">검증 데이터가 없습니다.</p>
        </div>
    );

    const latest = data[data.length - 1];
    const currentMetrics = latest.metrics[activeAxis] || latest.summary;

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                        <p className="text-xs text-gray-400">{activeAxis.toUpperCase()} MAE (오차)</p>
                        <TrendingDown className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{currentMetrics.MAE?.toFixed(2) || "N/A"}</p>
                    <p className="text-[10px] text-gray-500 mt-1">Lower is better | {latest.scoring_version}</p>
                </div>
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                        <p className="text-xs text-gray-400">{activeAxis.toUpperCase()} Spearman (상관성)</p>
                        <TrendingUp className="w-4 h-4 text-blue-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{currentMetrics.Spearman?.toFixed(2) || "N/A"}</p>
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
                    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
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
                                dataKey={`metrics.${activeAxis}.MAE`}
                                name={`${activeAxis} MAE (오차)`}
                                stroke="#F87171"
                                strokeWidth={2}
                                dot={{ r: 4, fill: '#F87171' }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey={`metrics.${activeAxis}.Spearman`}
                                name={`${activeAxis} Spearman (상관성)`}
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
