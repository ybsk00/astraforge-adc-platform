'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, Download, Loader2, AlertCircle } from 'lucide-react';
import { Link } from '@/i18n/routing';
import ScoreRadarChart from '@/components/design/ScoreRadarChart';

interface Candidate {
    id: string;
    target_id?: string;
    payload_id?: string;
    snapshot?: any;
    candidate_scores?: any[];
    assay_results?: any[];
}

export default function ComparePage({ params }: { params: { runId: string } }) {
    const searchParams = useSearchParams();
    const ids = searchParams.get('ids')?.split(',') || [];

    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    useEffect(() => {
        if (ids.length === 0) {
            setLoading(false);
            return;
        }

        const fetchCompareData = async () => {
            setLoading(true);
            try {
                const queryParams = new URLSearchParams();
                ids.forEach(id => queryParams.append('candidate_ids', id));

                const res = await fetch(`${ENGINE_URL}/api/v1/design/runs/${params.runId}/compare?${queryParams.toString()}`);
                if (res.ok) {
                    const data = await res.json();
                    setCandidates(data.items || []);
                } else {
                    setError('데이터를 불러오는 데 실패했습니다.');
                }
            } catch (err) {
                console.error('Failed to fetch compare data:', err);
                setError('서버 연결 오류가 발생했습니다.');
            } finally {
                setLoading(false);
            }
        };

        fetchCompareData();
    }, [params.runId, searchParams]);

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (error || candidates.length === 0) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-8 text-center">
                <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
                <h2 className="text-xl font-bold text-white mb-2">{error || '비교할 후보 물질이 없습니다.'}</h2>
                <Link href={`/design/runs/${params.runId}`} className="text-blue-400 hover:underline">
                    디자인 런 상세로 돌아가기
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Link href={`/design/runs/${params.runId}`} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">후보 물질 비교</h1>
                        <p className="text-slate-400">{candidates.length}개의 후보 물질 지표를 비교합니다.</p>
                    </div>
                    <div className="ml-auto">
                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                            <Download className="w-4 h-4" />
                            비교 리포트 생성
                        </button>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr>
                                <th className="p-6 border-b border-r border-slate-800 bg-slate-900/50 min-w-[200px] text-slate-400 text-sm font-medium">Metric</th>
                                {candidates.map((cand) => (
                                    <th key={cand.id} className="p-6 border-b border-r border-slate-800 min-w-[280px]">
                                        <div className="font-bold text-white mb-1">Candidate {cand.id.substring(0, 8)}</div>
                                        <div className="text-xs text-slate-500">
                                            {cand.snapshot?.target?.name || cand.target_id} - {cand.snapshot?.payload?.name || cand.payload_id}
                                        </div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Radar Analysis</td>
                                {candidates.map((cand) => {
                                    const scores = cand.candidate_scores?.[0] || {};
                                    return (
                                        <td key={cand.id} className="p-6 border-r border-slate-800">
                                            <div className="flex justify-center bg-slate-950/50 rounded-lg py-4">
                                                <ScoreRadarChart
                                                    scores={{
                                                        eng_fit: scores.eng_fit || 0,
                                                        bio_fit: scores.bio_fit || 0,
                                                        safety_fit: scores.safety_fit || 0,
                                                        evidence_fit: scores.evidence_fit || 0
                                                    }}
                                                    size={200}
                                                />
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Engineering Score</td>
                                {candidates.map((cand) => (
                                    <td key={cand.id} className="p-6 border-r border-slate-800 text-white font-bold">
                                        {(cand.candidate_scores?.[0]?.eng_fit || 0).toFixed(1)}
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Biological Score</td>
                                {candidates.map((cand) => (
                                    <td key={cand.id} className="p-6 border-r border-slate-800 text-white font-bold">
                                        {(cand.candidate_scores?.[0]?.bio_fit || 0).toFixed(1)}
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Safety Score</td>
                                {candidates.map((cand) => (
                                    <td key={cand.id} className="p-6 border-r border-slate-800 text-white font-bold">
                                        {(cand.candidate_scores?.[0]?.safety_fit || 0).toFixed(1)}
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Evidence Score</td>
                                {candidates.map((cand) => (
                                    <td key={cand.id} className="p-6 border-r border-slate-800 text-white font-bold">
                                        {(cand.candidate_scores?.[0]?.evidence_fit || 0).toFixed(1)}
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Assay Results</td>
                                {candidates.map((cand) => (
                                    <td key={cand.id} className="p-6 border-r border-slate-800">
                                        {cand.assay_results && cand.assay_results.length > 0 ? (
                                            <ul className="text-xs space-y-1 text-slate-400">
                                                {cand.assay_results.map((assay, idx) => (
                                                    <li key={idx}>• {assay.assay_type}: {assay.result_value}</li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <span className="text-xs text-slate-600 italic">No assay data</span>
                                        )}
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
