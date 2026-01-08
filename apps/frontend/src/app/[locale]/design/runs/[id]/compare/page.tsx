'use client';

import { useState } from 'react';
import { Link } from '@/i18n/routing';
import {
    ArrowLeft,
    ArrowRightLeft,
    ChevronDown,
    Download,
    ExternalLink,
    Bookmark
} from 'lucide-react';
import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
    Tooltip,
    Legend
} from 'recharts';

interface ComparePageProps {
    params: { id: string };
}

export default function ComparePage({ params }: ComparePageProps) {
    // Mock Data
    const allCandidates = [
        { id: 'ADC-1042', name: 'HER2-Val-Cit-MMAE', score: 87 },
        { id: 'ADC-X99', name: 'IgG4-Hydrazone-Dox', score: 82 },
        { id: 'ADC-8832', name: 'EGFR-MC-MMAE', score: 90 },
    ];

    const [candidateA, setCandidateA] = useState(allCandidates[0]);
    const [candidateB, setCandidateB] = useState(allCandidates[1]);

    const candidateDataA = {
        ...candidateA,
        status: 'Lead',
        metrics: {
            efficacy: 88,
            toxicity: 85,
            stability: 90,
            solubility: 82,
            synthCost: 75,
        },
        details: {
            bindingAffinity: '0.4 nM',
            drugAntibodyRatio: '3.8',
            halfLife: '5.0 days',
            aggregation: '1.2%',
        },
        literature: [
            { title: 'High tumor regression observed in breast cancer models...', year: '2023', type: 'CLINICAL TRIAL' },
            { title: 'Novel linker stability in human plasma...', year: '2022', type: 'PATENT' },
        ],
    };

    const candidateDataB = {
        ...candidateB,
        status: 'Challenger',
        metrics: {
            efficacy: 78,
            toxicity: 75,
            stability: 85,
            solubility: 88,
            synthCost: 82,
        },
        details: {
            bindingAffinity: '1.2 nM',
            drugAntibodyRatio: '4.0',
            halfLife: '3.5 days',
            aggregation: '0.8%',
        },
        literature: [
            { title: 'Improved solubility profiles in high concentration...', year: '2024', type: 'PRE-CLINICAL' },
            { title: 'Off-target toxicity analysis in murine models...', year: '2023', type: 'TOXICITY REPORT' },
        ],
    };

    const radarData = [
        { subject: 'EFFICACY', A: candidateDataA.metrics.efficacy, B: candidateDataB.metrics.efficacy },
        { subject: 'TOXICITY', A: 100 - candidateDataA.metrics.toxicity, B: 100 - candidateDataB.metrics.toxicity },
        { subject: 'STABILITY', A: candidateDataA.metrics.stability, B: candidateDataB.metrics.stability },
        { subject: 'SOLUBILITY', A: candidateDataA.metrics.solubility, B: candidateDataB.metrics.solubility },
        { subject: 'SYNTH. COST', A: 100 - candidateDataA.metrics.synthCost, B: 100 - candidateDataB.metrics.synthCost },
    ];

    const keyMetrics = [
        { property: 'Binding Affinity (Kd)', a: candidateDataA.details.bindingAffinity, b: candidateDataB.details.bindingAffinity, analysis: 'Significant' },
        { property: 'Drug-to-Antibody Ratio (DAR)', a: candidateDataA.details.drugAntibodyRatio, b: candidateDataB.details.drugAntibodyRatio, analysis: 'Similar' },
        { property: 'Half-life (t1/2)', a: candidateDataA.details.halfLife, b: candidateDataB.details.halfLife, analysis: 'Moderate Diff' },
        { property: 'Aggregation (%)', a: candidateDataA.details.aggregation, b: candidateDataB.details.aggregation, analysis: 'A50 Favored' },
    ];

    const getAnalysisBadgeClass = (analysis: string) => {
        switch (analysis) {
            case 'Significant': return 'bg-purple-500/20 text-purple-400';
            case 'Similar': return 'bg-slate-500/20 text-slate-400';
            case 'Moderate Diff': return 'bg-yellow-500/20 text-yellow-400';
            case 'A50 Favored': return 'bg-green-500/20 text-green-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link
                        href={`/design/runs/${params.id}`}
                        className="text-slate-400 hover:text-white flex items-center gap-2 text-sm w-fit mb-4 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Analysis
                    </Link>

                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold text-white mb-2">후보 비교</h1>
                            <p className="text-sm text-slate-400">
                                {candidateA.id} vs {candidateB.id} 상세 비교 분석 및 선호도 결정
                            </p>
                        </div>

                        {/* Candidate Selectors */}
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <div className="text-xs text-slate-500 mb-1">Candidate A</div>
                                <select
                                    value={candidateA.id}
                                    onChange={(e) => setCandidateA(allCandidates.find(c => c.id === e.target.value) || allCandidates[0])}
                                    className="appearance-none bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {allCandidates.map(c => (
                                        <option key={c.id} value={c.id}>{c.id}</option>
                                    ))}
                                </select>
                                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-8 pointer-events-none" />
                            </div>

                            <ArrowRightLeft className="w-5 h-5 text-slate-500 mt-5" />

                            <div className="relative">
                                <div className="text-xs text-slate-500 mb-1">Candidate B</div>
                                <select
                                    value={candidateB.id}
                                    onChange={(e) => setCandidateB(allCandidates.find(c => c.id === e.target.value) || allCandidates[1])}
                                    className="appearance-none bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {allCandidates.map(c => (
                                        <option key={c.id} value={c.id}>{c.id}</option>
                                    ))}
                                </select>
                                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-8 pointer-events-none" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Radar Chart & Score Cards */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Radar Chart */}
                    <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                                <span className="text-sm text-slate-400">{candidateA.id}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                                <span className="text-sm text-slate-400">{candidateB.id}</span>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-4">📊 스코어 차이 시각화 (Efficacy vs Safety)</h3>
                        <p className="text-sm text-slate-400 mb-6">Overlay comparison of normalized performance metrics.</p>

                        <div className="h-[280px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                    <PolarGrid stroke="#334155" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar
                                        name={candidateA.id}
                                        dataKey="A"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        fill="#3b82f6"
                                        fillOpacity={0.2}
                                    />
                                    <Radar
                                        name={candidateB.id}
                                        dataKey="B"
                                        stroke="#8b5cf6"
                                        strokeWidth={2}
                                        fill="#8b5cf6"
                                        fillOpacity={0.2}
                                    />
                                    <Legend />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Score Cards */}
                    <div className="space-y-4">
                        {/* Candidate A Card */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                                        <span className="text-lg">🧬</span>
                                    </div>
                                    <div>
                                        <div className="text-white font-semibold">{candidateA.id}</div>
                                        <div className="text-xs text-slate-400">{candidateA.name}</div>
                                    </div>
                                </div>
                                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-400">
                                    {candidateDataA.status}
                                </span>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-3xl font-bold text-white">{candidateA.score}</span>
                                <span className="text-slate-400">/100</span>
                                <span className="text-xs text-green-400 ml-2">▲+3%</span>
                            </div>
                        </div>

                        {/* Candidate B Card */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                                        <span className="text-lg">🧬</span>
                                    </div>
                                    <div>
                                        <div className="text-white font-semibold">{candidateB.id}</div>
                                        <div className="text-xs text-slate-400">{candidateB.name}</div>
                                    </div>
                                </div>
                                <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">
                                    {candidateDataB.status}
                                </span>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-3xl font-bold text-white">{candidateB.score}</span>
                                <span className="text-slate-400">/100</span>
                                <span className="text-xs text-red-400 ml-2">▼-2%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Key Metrics Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl mb-8">
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-white">📋 상세 지표 비교 (Key Metrics)</h3>
                        <button className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-2 transition-colors">
                            <Download className="w-4 h-4" />
                            Download CSV
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-800">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Metric Property</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-blue-400 uppercase tracking-wider">{candidateA.id}</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-purple-400 uppercase tracking-wider">{candidateB.id}</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Analysis</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {keyMetrics.map((metric, index) => (
                                    <tr key={index} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 text-sm text-slate-300">{metric.property}</td>
                                        <td className="px-6 py-4 text-sm text-white font-medium">{metric.a}</td>
                                        <td className="px-6 py-4 text-sm text-white font-medium">{metric.b}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getAnalysisBadgeClass(metric.analysis)}`}>
                                                {metric.analysis}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Literature Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Candidate A Literature */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white">문헌 근거 ({candidateA.id})</h3>
                            <span className="text-sm text-slate-400">{candidateDataA.literature.length} Papers Found</span>
                        </div>
                        <div className="space-y-3">
                            {candidateDataA.literature.map((paper, index) => (
                                <div key={index} className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer group">
                                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${paper.type === 'CLINICAL TRIAL'
                                            ? 'bg-purple-500/20 text-purple-400'
                                            : 'bg-blue-500/20 text-blue-400'
                                        }`}>
                                        {paper.type}
                                    </span>
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="text-sm text-white group-hover:text-blue-400 transition-colors">
                                            "{paper.title}"
                                        </div>
                                        <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors flex-shrink-0" />
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">{paper.year}</div>
                                </div>
                            ))}
                        </div>
                        <button className="w-full mt-4 text-sm text-slate-400 hover:text-white transition-colors">
                            View All References
                        </button>
                    </div>

                    {/* Candidate B Literature */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white">문헌 근거 ({candidateB.id})</h3>
                            <span className="text-sm text-slate-400">{candidateDataB.literature.length} Papers Found</span>
                        </div>
                        <div className="space-y-3">
                            {candidateDataB.literature.map((paper, index) => (
                                <div key={index} className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer group">
                                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${paper.type === 'PRE-CLINICAL'
                                            ? 'bg-green-500/20 text-green-400'
                                            : 'bg-red-500/20 text-red-400'
                                        }`}>
                                        {paper.type}
                                    </span>
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="text-sm text-white group-hover:text-blue-400 transition-colors">
                                            "{paper.title}"
                                        </div>
                                        <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors flex-shrink-0" />
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">{paper.year}</div>
                                </div>
                            ))}
                        </div>
                        <button className="w-full mt-4 text-sm text-slate-400 hover:text-white transition-colors">
                            View All References
                        </button>
                    </div>
                </div>

                {/* Preference Vote */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                        <div className="text-sm text-slate-400">
                            <strong className="text-white">Preference Vote:</strong> Please select the candidate to proceed to the next development phase.
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded-lg border border-slate-700 transition-colors">
                                Mark for Review
                            </button>
                            <button className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                                <Bookmark className="w-4 h-4" />
                                Select {candidateA.id}
                            </button>
                            <button className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                                <Bookmark className="w-4 h-4" />
                                Select {candidateB.id}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
