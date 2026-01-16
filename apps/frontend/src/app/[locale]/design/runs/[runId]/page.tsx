'use client';

import { useState } from 'react';
import { ArrowLeft, BarChart2, Download } from 'lucide-react';
import { Link } from '@/i18n/routing';
import CandidatesList from '@/components/design/CandidatesList';
import ParetoFrontView from '@/components/design/ParetoFrontView';
import ReportPreview from '@/components/design/ReportPreview';

export default function RunDetailsPage({ params }: { params: { runId: string } }) {
    const [activeTab, setActiveTab] = useState('candidates');

    // TODO: Fetch real run data from API
    const run = {
        id: params.runId,
        status: 'completed',
        progress: 100,
        created_at: '2023-10-25 14:00',
        scoring_version: 'v2.1',
        ruleset_version: 'v1.5',
    };

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
                            <h1 className="text-2xl font-bold text-white">Run #{run.id}</h1>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 uppercase">
                                {run.status}
                            </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                            <span>Created: {run.created_at}</span>
                            <span>Scoring: {run.scoring_version}</span>
                            <span>Ruleset: {run.ruleset_version}</span>
                        </div>
                    </div>
                    <div className="ml-auto flex gap-3">
                        <Link href={`/design/runs/${run.id}/reports`} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                            <Download className="w-4 h-4" />
                            리포트
                        </Link>
                        <Link href={`/design/runs/${run.id}/compare`} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                            <BarChart2 className="w-4 h-4" />
                            비교하기
                        </Link>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-white">Run Progress</span>
                        <span className="text-sm text-slate-400">{run.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full transition-all duration-500" style={{ width: `${run.progress}%` }} />
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-800 mb-6">
                    <button
                        onClick={() => setActiveTab('candidates')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'candidates'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-white'
                            }`}
                    >
                        후보 목록 (Candidates)
                    </button>
                    <button
                        onClick={() => setActiveTab('pareto')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'pareto'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-white'
                            }`}
                    >
                        파레토 프론트 (Pareto)
                    </button>
                    <button
                        onClick={() => setActiveTab('logs')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'logs'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-white'
                            }`}
                    >
                        실행 로그 (Logs)
                    </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'candidates' && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                        <CandidatesList runId={params.runId} />
                    </div>
                )}

                {activeTab === 'pareto' && (
                    <div className="space-y-8">
                        <ReportPreview runId={params.runId} />
                        <ParetoFrontView runId={params.runId} />
                    </div>
                )}

                {activeTab === 'logs' && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-sm text-slate-300">
                        <div className="mb-2 text-green-400">[INFO] Run started at 2023-10-25 14:00:00</div>
                        <div className="mb-2">[INFO] Generating candidates...</div>
                        <div className="mb-2">[INFO] Scoring candidates...</div>
                        <div className="mb-2 text-green-400">[INFO] Run completed successfully.</div>
                    </div>
                )}
            </div>
        </div>
    );
}
