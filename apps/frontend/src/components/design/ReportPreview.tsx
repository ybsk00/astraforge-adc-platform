"use client";

/**
 * 리포트 미리보기 및 내보내기 컴포넌트
 */
import { useState } from "react";
import { Download, FileText, CheckCircle } from "lucide-react";

interface ReportPreviewProps {
    runId: string;
}

export default function ReportPreview({ runId }: ReportPreviewProps) {
    const [generating, setGenerating] = useState(false);
    const [reportUrl, setReportUrl] = useState<string | null>(null);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    const handleGenerateReport = async () => {
        setGenerating(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${runId}/report`, {
                method: "POST"
            });
            if (res.ok) {
                const data = await res.json();
                setReportUrl(data.url);
            }
        } catch (error) {
            console.error("Failed to generate report:", error);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                        <FileText className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">분석 리포트 생성</h3>
                        <p className="text-sm text-gray-400">Executive Summary 및 후보 물질 상세 분석 포함</p>
                    </div>
                </div>
                {!reportUrl ? (
                    <button
                        onClick={handleGenerateReport}
                        disabled={generating}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-sm font-bold rounded-lg flex items-center gap-2 transition-all"
                    >
                        {generating ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                        ) : (
                            <Download className="w-4 h-4" />
                        )}
                        {generating ? "생성 중..." : "리포트 생성하기"}
                    </button>
                ) : (
                    <a
                        href={reportUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded-lg flex items-center gap-2 transition-all"
                    >
                        <CheckCircle className="w-4 h-4" />
                        리포트 다운로드
                    </a>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                    <p className="text-xs text-gray-500 mb-1">총 후보 수</p>
                    <p className="text-xl font-bold text-white">1,240</p>
                </div>
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                    <p className="text-xs text-gray-500 mb-1">파레토 최적 후보 (P0)</p>
                    <p className="text-xl font-bold text-yellow-400">12</p>
                </div>
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                    <p className="text-xs text-gray-500 mb-1">평균 Bio-Fit</p>
                    <p className="text-xl font-bold text-green-400">84.5</p>
                </div>
            </div>

            <div className="mt-6 p-4 bg-blue-900/10 border border-blue-500/20 rounded-lg">
                <h4 className="text-xs font-bold text-blue-400 uppercase mb-2">Preview Summary</h4>
                <p className="text-sm text-gray-300 leading-relaxed">
                    본 리포트는 HER2 타겟 ADC 설계에 대한 다차원 최적화 결과를 담고 있습니다.
                    RDKit 기반의 물성 계산 결과, 응집 위험도가 낮은 상위 12개 후보 물질이 선별되었으며,
                    특히 P0 그룹의 후보들은 Bio-fit과 Safety-fit 사이의 최적의 균형을 보여줍니다.
                </p>
            </div>
        </div>
    );
}
