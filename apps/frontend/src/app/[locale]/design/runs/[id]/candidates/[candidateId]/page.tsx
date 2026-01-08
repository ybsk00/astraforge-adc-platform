'use client';

import { useState } from 'react';
import { Link } from '@/i18n/routing';
import {
    ArrowLeft,
    Save,
    Download,
    Target,
    Syringe,
    Link as LinkIcon,
    Pill,
    ChevronRight,
    FileText,
    ThumbsUp,
    ThumbsDown,
    Clock,
    ExternalLink
} from 'lucide-react';
import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
    Tooltip
} from 'recharts';

interface CandidateDetailPageProps {
    params: { id: string; candidateId: string };
}

export default function CandidateDetailPage({ params }: CandidateDetailPageProps) {
    const [feedbackRating, setFeedbackRating] = useState<'approve' | 'hold' | 'reject' | null>(null);
    const [reviewComment, setReviewComment] = useState('');

    // Mock Data
    const candidate = {
        id: params.candidateId || 'ADC-2024-X92',
        status: 'HIGH POTENTIAL',
        createdDate: 'Oct 24, 2024',
        projectName: 'Project HER2-Targeted Therapy',
        composition: {
            target: {
                name: 'HER2',
                description: 'Receptor Tyrosine-Protein Kinase erbB-2',
                relevance: '89%',
            },
            antibody: {
                name: 'Trastuzumab',
                description: 'Humanized IgG1 monoclonal',
                tag: 'Stable in Plasma',
            },
            linker: {
                name: 'Val-Cit',
                description: 'Cleavable (Protease-sensitive)',
            },
            payload: {
                name: 'MMAE',
                description: 'Monomethyl auristatin E',
                tag: 'High Potency',
            },
        },
        scores: {
            total: 88,
            efficacy: 85,
            toxicity: 75,
            stability: 90,
            developability: 82,
        },
        metrics: {
            bindingAffinity: '0.5 nM',
            drugAntibodyRatio: '3.8',
            plasmaStability: '>95% (7d)',
            solubility: 'High',
            offTargetToxicity: 'Low',
        },
        protocols: [
            { name: 'Cytotoxicity Assay V2', description: 'Standard 72h incubation' },
            { name: 'Plasma Stability Test', description: 'Extended 14-day protocol' },
        ],
        literature: [
            { title: 'Novel Linker Stability in Val-Cit Conjugates targeting HER2', year: '2023', type: 'CLINICAL TRIAL' },
            { title: 'MMAE Toxicity Profiles in Solid Tumors', year: '2022', type: 'REVIEW' },
        ],
    };

    const radarData = [
        { subject: 'Efficacy', value: candidate.scores.efficacy, fullMark: 100 },
        { subject: 'Toxicity', value: 100 - candidate.scores.toxicity, fullMark: 100 },
        { subject: 'Stability', value: candidate.scores.stability, fullMark: 100 },
        { subject: 'Developability', value: candidate.scores.developability, fullMark: 100 },
    ];

    const handleSubmitReview = () => {
        console.log('Submitting review:', { rating: feedbackRating, comment: reviewComment });
        // API call would go here
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            {/* Header */}
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col gap-4 mb-8">
                    <Link
                        href={`/design/runs/${params.id}`}
                        className="text-slate-400 hover:text-white flex items-center gap-2 text-sm w-fit transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Run
                    </Link>

                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-2xl font-bold text-white">{candidate.id}</h1>
                                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
                                    {candidate.status}
                                </span>
                            </div>
                            <p className="text-slate-400 text-sm">
                                Created on {candidate.createdDate} • {candidate.projectName}
                            </p>
                        </div>

                        <div className="flex items-center gap-3">
                            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                                <Save className="w-4 h-4" />
                                Save
                            </button>
                            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                                <Download className="w-4 h-4" />
                                Export Report
                            </button>
                        </div>
                    </div>
                </div>

                {/* Composition Section */}
                <div className="mb-8">
                    <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="text-slate-500">📋</span>
                        후보 구성 정보 (Composition)
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Target */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                                    <Target className="w-4 h-4 text-red-400" />
                                </div>
                                <span className="text-xs text-slate-500 uppercase tracking-wider">TARGET</span>
                                <div className="ml-auto w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                                    <span className="text-white text-xs">✓</span>
                                </div>
                            </div>
                            <div className="text-lg font-semibold text-white mb-1">{candidate.composition.target.name}</div>
                            <p className="text-sm text-slate-400 mb-3">{candidate.composition.target.description}</p>
                            <div className="flex items-center justify-between">
                                <span className="text-xs text-slate-500">Relevance</span>
                                <span className="text-sm font-medium text-blue-400">{candidate.composition.target.relevance}</span>
                            </div>
                        </div>

                        {/* Antibody */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                    <Syringe className="w-4 h-4 text-blue-400" />
                                </div>
                                <span className="text-xs text-slate-500 uppercase tracking-wider">ANTIBODY</span>
                            </div>
                            <div className="text-lg font-semibold text-white mb-1">{candidate.composition.antibody.name}</div>
                            <p className="text-sm text-slate-400 mb-3">{candidate.composition.antibody.description}</p>
                            <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-cyan-500/20 text-cyan-400">
                                {candidate.composition.antibody.tag}
                            </span>
                        </div>

                        {/* Linker */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                                    <LinkIcon className="w-4 h-4 text-yellow-400" />
                                </div>
                                <span className="text-xs text-slate-500 uppercase tracking-wider">LINKER</span>
                            </div>
                            <div className="text-lg font-semibold text-white mb-1">{candidate.composition.linker.name}</div>
                            <p className="text-sm text-slate-400">{candidate.composition.linker.description}</p>
                        </div>

                        {/* Payload */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                    <Pill className="w-4 h-4 text-purple-400" />
                                </div>
                                <span className="text-xs text-slate-500 uppercase tracking-wider">PAYLOAD</span>
                            </div>
                            <div className="text-lg font-semibold text-white mb-1">{candidate.composition.payload.name}</div>
                            <p className="text-sm text-slate-400 mb-3">{candidate.composition.payload.description}</p>
                            <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-pink-500/20 text-pink-400">
                                {candidate.composition.payload.tag}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    {/* 4-Axis Score Analysis */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">4-Axis Score Analysis</h3>
                            <div className="text-right">
                                <div className="text-3xl font-bold text-white">
                                    {candidate.scores.total}<span className="text-lg text-slate-400">/100</span>
                                </div>
                                <div className="text-xs text-green-400">+5% vs Previous</div>
                            </div>
                        </div>

                        <div className="h-[280px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                    <PolarGrid stroke="#334155" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar
                                        name="Score"
                                        dataKey="value"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        fill="#3b82f6"
                                        fillOpacity={0.3}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-800">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-400">Binding Affinity (Kd)</span>
                                <span className="text-sm font-medium text-white">{candidate.metrics.bindingAffinity}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-400">Drug-Antibody Ratio</span>
                                <span className="text-sm font-medium text-white">{candidate.metrics.drugAntibodyRatio}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-400">Plasma Stability</span>
                                <span className="text-sm font-medium text-white">{candidate.metrics.plasmaStability}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-400">Solubility</span>
                                <span className="text-sm font-medium text-white">{candidate.metrics.solubility}</span>
                            </div>
                        </div>
                    </div>

                    {/* Protocols & Feedback */}
                    <div className="space-y-6">
                        {/* Recommended Protocols */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="text-green-400">⚡</span>
                                추천 프로토콜 (Protocols)
                            </h3>
                            <p className="text-sm text-slate-400 mb-4">
                                Based on the high stability score, the following assay protocols are recommended for the next phase.
                            </p>
                            <div className="space-y-3">
                                {candidate.protocols.map((protocol, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-blue-400" />
                                            <div>
                                                <div className="text-sm font-medium text-white">{protocol.name}</div>
                                                <div className="text-xs text-slate-400">{protocol.description}</div>
                                            </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                                    </div>
                                ))}
                            </div>
                            <button className="w-full mt-4 text-sm text-blue-400 hover:text-blue-300 transition-colors">
                                Generate Custom Protocol
                            </button>
                        </div>

                        {/* Expert Feedback */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="text-yellow-400">💬</span>
                                전문가 피드백 (Feedback)
                            </h3>

                            <div className="mb-4">
                                <div className="text-sm text-slate-400 mb-3">OVERALL RATING</div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setFeedbackRating('reject')}
                                        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${feedbackRating === 'reject'
                                                ? 'bg-red-500 text-white'
                                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                            }`}
                                    >
                                        <ThumbsDown className="w-4 h-4" />
                                        Reject
                                    </button>
                                    <button
                                        onClick={() => setFeedbackRating('hold')}
                                        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${feedbackRating === 'hold'
                                                ? 'bg-yellow-500 text-black'
                                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                            }`}
                                    >
                                        <Clock className="w-4 h-4" />
                                        Hold
                                    </button>
                                    <button
                                        onClick={() => setFeedbackRating('approve')}
                                        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${feedbackRating === 'approve'
                                                ? 'bg-green-500 text-white'
                                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                            }`}
                                    >
                                        <ThumbsUp className="w-4 h-4" />
                                        Approve
                                    </button>
                                </div>
                            </div>

                            <div className="mb-4">
                                <div className="text-sm text-slate-400 mb-2">REVIEW COMMENTS</div>
                                <textarea
                                    value={reviewComment}
                                    onChange={(e) => setReviewComment(e.target.value)}
                                    placeholder="Enter specific observations regarding binding affinity or toxicity risks..."
                                    className="w-full h-24 bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                />
                            </div>

                            <button
                                onClick={handleSubmitReview}
                                className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 transition-colors"
                            >
                                Submit Review
                            </button>
                        </div>
                    </div>
                </div>

                {/* Literature Section */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                            <span className="text-blue-400">📚</span>
                            문헌 인용 (Literature)
                        </h3>
                        <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                            View all (12)
                        </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {candidate.literature.map((paper, index) => (
                            <div
                                key={index}
                                className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer group"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1">
                                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${paper.type === 'CLINICAL TRIAL'
                                                ? 'bg-purple-500/20 text-purple-400'
                                                : 'bg-blue-500/20 text-blue-400'
                                            }`}>
                                            {paper.type}
                                        </span>
                                        <div className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">
                                            "{paper.title}"
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">{paper.year}</div>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors flex-shrink-0 mt-1" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
