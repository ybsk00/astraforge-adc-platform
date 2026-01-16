'use client';

import Link from 'next/link';
import {
    Edit,
    Trash2,
    RefreshCw,
    Target,
    Syringe,
    Link as LinkIcon,
    Pill,
    FlaskConical,
    FileText,
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

type LucideIcon = React.ComponentType<{ className?: string }>;

interface ComponentDetailPageProps {
    params: { id: string };
}

const TYPE_CONFIG: Record<string, { icon: LucideIcon; color: string; bg: string; label: string }> = {
    target: { icon: Target, color: 'text-red-400', bg: 'bg-red-500/20', label: 'Target' },
    antibody: { icon: Syringe, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Antibody' },
    linker: { icon: LinkIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'Linker' },
    payload: { icon: Pill, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Payload' },
    conjugation: { icon: FlaskConical, color: 'text-cyan-400', bg: 'bg-cyan-500/20', label: 'Conjugation' },
};

const GRADE_BADGE: Record<string, { label: string; class: string }> = {
    gold: { label: 'Gold', class: 'bg-yellow-500/20 text-yellow-400' },
    silver: { label: 'Silver', class: 'bg-slate-400/20 text-slate-300' },
    bronze: { label: 'Bronze', class: 'bg-orange-500/20 text-orange-400' },
};

export default function ComponentDetailPage({ params }: ComponentDetailPageProps) {
    // Mock Data
    const component = {
        id: params.id,
        name: 'Trastuzumab',
        type: 'antibody',
        quality_grade: 'gold',
        status: 'active',
        description: 'Humanized IgG1 monoclonal antibody targeting HER2 receptor. FDA-approved for breast and gastric cancer treatment.',
        properties: {
            smiles: 'Complex protein structure - N/A',
            molecularWeight: '148 kDa',
            bindingAffinity: '0.5 nM',
            halfLife: '5.8 days',
            isotype: 'IgG1',
            source: 'CHO cells',
        },
        scores: {
            stability: 92,
            efficacy: 88,
            safety: 95,
            manufacturability: 85,
        },
        literature: [
            { title: 'Clinical efficacy of trastuzumab in HER2+ breast cancer', journal: 'J Clin Oncol', year: '2022', citations: 245 },
            { title: 'PK/PD modeling of trastuzumab-based ADCs', journal: 'mAbs', year: '2023', citations: 78 },
            { title: 'Safety profile analysis in long-term treatment', journal: 'Lancet Oncol', year: '2021', citations: 189 },
        ],
        usedInRuns: [
            { id: '#RUN-853', target: 'HER2-ADC', date: '2023-10-21', score: 91.0 },
            { id: '#RUN-842', target: 'HER2-Linker Opt', date: '2023-09-15', score: 88.5 },
        ],
        createdAt: '2023-08-15',
        updatedAt: '2023-10-24',
    };

    const radarData = Object.entries(component.scores).map(([key, value]) => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1),
        value,
        fullMark: 100,
    }));

    const typeConfig = TYPE_CONFIG[component.type] || TYPE_CONFIG.target;
    const IconComponent = typeConfig.icon;

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Breadcrumb */}
                <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
                    <Link href="/catalog" className="hover:text-white transition-colors">Catalog</Link>
                    <span>›</span>
                    <span className="text-white">{component.name}</span>
                </nav>

                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-8">
                    <div className="flex items-start gap-4">
                        <div className={`p-4 rounded-xl ${typeConfig.bg}`}>
                            <IconComponent className={`w-8 h-8 ${typeConfig.color}`} />
                        </div>
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <h1 className="text-2xl font-bold text-white">{component.name}</h1>
                                {component.quality_grade && GRADE_BADGE[component.quality_grade] && (
                                    <span className={`px-2.5 py-1 rounded text-xs font-medium ${GRADE_BADGE[component.quality_grade].class}`}>
                                        {GRADE_BADGE[component.quality_grade].label}
                                    </span>
                                )}
                                <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                                    Active
                                </span>
                            </div>
                            <p className="text-slate-400 text-sm">{typeConfig.label} • ID: {component.id}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                            <Edit className="w-4 h-4" />
                            Edit
                        </button>
                        <button className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded-lg border border-red-500/30 flex items-center gap-2 transition-colors">
                            <Trash2 className="w-4 h-4" />
                            Deprecate
                        </button>
                    </div>
                </div>

                {/* Description */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                    <p className="text-slate-300 leading-relaxed">{component.description}</p>
                </div>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Properties */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Properties</h3>
                        <div className="space-y-4">
                            {Object.entries(component.properties).map(([key, value]) => (
                                <div key={key} className="flex justify-between items-center border-b border-slate-800 pb-3 last:border-0">
                                    <span className="text-sm text-slate-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                                    <span className="text-sm text-white font-medium">{value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Score Analysis */}
                    <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white">Score Analysis</h3>
                            <div className="flex items-center gap-2">
                                <span className="text-3xl font-bold text-white">
                                    {Math.round(Object.values(component.scores).reduce((a, b) => a + b, 0) / Object.values(component.scores).length)}
                                </span>
                                <span className="text-slate-400">/100</span>
                            </div>
                        </div>
                        <div className="h-[250px] w-full">
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
                    </div>
                </div>

                {/* Literature & Used In Runs */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Literature */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <FileText className="w-5 h-5 text-blue-400" />
                                Related Literature
                            </h3>
                            <span className="text-sm text-slate-400">{component.literature.length} papers</span>
                        </div>
                        <div className="space-y-3">
                            {component.literature.map((paper, index) => (
                                <div
                                    key={index}
                                    className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer group"
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1">
                                            <div className="text-sm text-white group-hover:text-blue-400 transition-colors mb-1">
                                                {paper.title}
                                            </div>
                                            <div className="text-xs text-slate-400">
                                                {paper.journal} • {paper.year} • {paper.citations} citations
                                            </div>
                                        </div>
                                        <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors flex-shrink-0" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Used In Runs */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <RefreshCw className="w-5 h-5 text-green-400" />
                                Used In Runs
                            </h3>
                            <span className="text-sm text-slate-400">{component.usedInRuns.length} runs</span>
                        </div>
                        <div className="space-y-3">
                            {component.usedInRuns.map((run, index) => (
                                <Link
                                    key={index}
                                    href={`/design/runs/${run.id.replace('#', '')}`}
                                    className="block p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors group"
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-sm text-blue-400 font-mono mb-1">{run.id}</div>
                                            <div className="text-xs text-slate-400">{run.target} • {run.date}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-lg font-bold text-white">{run.score}%</div>
                                            <div className="text-xs text-green-400">Score</div>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Metadata Footer */}
                <div className="mt-8 text-center text-xs text-slate-500">
                    Created: {component.createdAt} • Last Updated: {component.updatedAt}
                </div>
            </div>
        </div>
    );
}
