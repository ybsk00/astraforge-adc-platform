'use client';

import { ArrowLeft, Share2, Download, ThumbsUp, ThumbsDown, AlertTriangle } from 'lucide-react';
import { Link } from '@/i18n/routing';

export default function CandidateDetailsPage({ params }: { params: { candidateId: string } }) {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/design/runs" className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-2xl font-bold text-white">Candidate {params.candidateId}</h1>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                                Score: 0.92
                            </span>
                        </div>
                        <p className="text-slate-400">HER2 (Target) - Val-Cit (Linker) - MMAE (Payload)</p>
                    </div>
                    <div className="ml-auto flex gap-3">
                        <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                            <Share2 className="w-4 h-4" />
                            공유
                        </button>
                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                            <Download className="w-4 h-4" />
                            리포트
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Score Breakdown */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">점수 분석</h3>
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="p-4 bg-slate-950 rounded-lg text-center">
                                    <div className="text-sm text-slate-400 mb-1">Engineering</div>
                                    <div className="text-xl font-bold text-blue-400">0.95</div>
                                </div>
                                <div className="p-4 bg-slate-950 rounded-lg text-center">
                                    <div className="text-sm text-slate-400 mb-1">Biological</div>
                                    <div className="text-xl font-bold text-green-400">0.88</div>
                                </div>
                                <div className="p-4 bg-slate-950 rounded-lg text-center">
                                    <div className="text-sm text-slate-400 mb-1">Safety</div>
                                    <div className="text-xl font-bold text-yellow-400">0.91</div>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-300">Binding Affinity</span>
                                    <span className="text-white font-mono">0.98 (High)</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                    <div className="bg-blue-500 h-full" style={{ width: '98%' }} />
                                </div>
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-300">Solubility</span>
                                    <span className="text-white font-mono">0.85 (Good)</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                    <div className="bg-green-500 h-full" style={{ width: '85%' }} />
                                </div>
                            </div>
                        </div>

                        {/* Evidence */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">관련 근거 (Evidence)</h3>
                            <div className="space-y-4">
                                <div className="p-4 bg-slate-950 rounded-lg border-l-4 border-green-500">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-xs font-bold text-green-400 uppercase">Positive</span>
                                        <span className="text-xs text-slate-500">PMID: 37829102</span>
                                    </div>
                                    <p className="text-sm text-slate-300 mb-2">
                                        "The combination of HER2 antibody and MMAE showed significant tumor regression in xenograft models..."
                                    </p>
                                    <div className="text-xs text-slate-500">Nature Medicine (2023)</div>
                                </div>
                                <div className="p-4 bg-slate-950 rounded-lg border-l-4 border-red-500">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-xs font-bold text-red-400 uppercase">Negative Signal</span>
                                        <span className="text-xs text-slate-500">PMID: 36123456</span>
                                    </div>
                                    <p className="text-sm text-slate-300 mb-2">
                                        "High dose MMAE payloads have been associated with neutropenia in some clinical trials..."
                                    </p>
                                    <div className="text-xs text-slate-500">Clinical Cancer Research (2022)</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Feedback */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">전문가 피드백</h3>
                            <div className="flex gap-2 mb-4">
                                <button className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-green-400 rounded-lg border border-slate-700 transition-colors flex justify-center items-center gap-2">
                                    <ThumbsUp className="w-4 h-4" /> Agree
                                </button>
                                <button className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-red-400 rounded-lg border border-slate-700 transition-colors flex justify-center items-center gap-2">
                                    <ThumbsDown className="w-4 h-4" /> Disagree
                                </button>
                            </div>
                            <textarea
                                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                                rows={4}
                                placeholder="의견을 작성하세요..."
                            />
                            <button className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors">
                                피드백 저장
                            </button>
                        </div>

                        {/* Rule Hits */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Rule Hits</h3>
                            <div className="space-y-3">
                                <div className="flex items-start gap-3 text-sm">
                                    <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                                    <div>
                                        <div className="text-white font-medium">Rule #105</div>
                                        <div className="text-slate-400">Payload toxicity warning threshold exceeded</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
