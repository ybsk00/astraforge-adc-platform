'use client';

import { useState } from 'react';
import { Link } from '@/i18n/routing';
import {
    ArrowLeft,
    Download,
    MoreHorizontal,
    Search,
    Filter,
    Beaker,
    Activity,
    ShieldAlert,
    Users,
    ChevronLeft,
    ChevronRight,
    ArrowUpDown
} from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

interface RunDetailPageProps {
    params: { id: string };
}

export default function RunDetailPage({ params }: RunDetailPageProps) {
    const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);

    // Mock Data
    const runData = {
        id: params.id || 'ADC-2023-08-X',
        status: 'COMPLETED',
        indication: 'Lung Cancer (NSCLC)',
        strategy: 'Linker Optimization',
        targetProtein: 'HER2 / ERBB2',
        createdDate: 'Aug 15, 2023',
        scores: {
            engineering: { value: 8.4, max: 10 },
            biology: { value: 7.2, max: 10 },
            safety: { value: 9.1, max: 10 },
        },
        totalCandidates: 1240,
        passedFilter: 805,
        changePercent: '+12%',
    };

    const scoreDistribution = [
        { range: '95-100', count: 25 },
        { range: '90-95', count: 85 },
        { range: '85-90', count: 180 },
        { range: '80-85', count: 320 },
        { range: '75-80', count: 380 },
        { range: '70-75', count: 150 },
        { range: '<70', count: 100 },
    ];

    const candidates = [
        { id: 'ADC-8832', rank: 1, structure: '/api/placeholder/48/48', engineering: 9.2, biology: 8.5, safety: 9.8, totalScore: 9.45 },
        { id: 'ADC-8841', rank: 2, structure: '/api/placeholder/48/48', engineering: 8.8, biology: 9.1, safety: 8.9, totalScore: 9.12 },
        { id: 'ADC-8902', rank: 3, structure: '/api/placeholder/48/48', engineering: 7.5, biology: 8.2, safety: 9.5, totalScore: 8.95 },
        { id: 'ADC-9120', rank: 4, structure: '/api/placeholder/48/48', engineering: 8.1, biology: 6.9, safety: 9.0, totalScore: 8.42 },
    ];

    const toggleCandidate = (id: string) => {
        setSelectedCandidates(prev =>
            prev.includes(id)
                ? prev.filter(c => c !== id)
                : [...prev, id]
        );
    };

    const getScoreColor = (score: number) => {
        if (score >= 9) return 'text-green-400';
        if (score >= 7) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getScoreBarColor = (score: number) => {
        if (score >= 9) return 'bg-green-500';
        if (score >= 7) return 'bg-blue-500';
        return 'bg-yellow-500';
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Breadcrumb */}
                <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
                    <Link href="/design/runs" className="hover:text-white transition-colors">Home</Link>
                    <span>›</span>
                    <Link href="/design/runs" className="hover:text-white transition-colors">Design Runs</Link>
                    <span>›</span>
                    <span className="text-white">Run #{runData.id}</span>
                </nav>

                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-2xl font-bold text-white">Run ID: {runData.id}</h1>
                            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
                                {runData.status}
                            </span>
                        </div>
                        <p className="text-slate-400 text-sm">
                            NSCLC Targeting Design Run • Linker Optimization Strategy
                        </p>
                    </div>

                    <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                        <Download className="w-4 h-4" />
                        Export Report
                    </button>
                </div>

                {/* Info Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">INDICATION</div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-400">⚕️</span>
                            <span className="text-white font-medium">{runData.indication}</span>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">STRATEGY</div>
                        <div className="flex items-center gap-2">
                            <span className="text-blue-400">🔗</span>
                            <span className="text-white font-medium">{runData.strategy}</span>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">TARGET PROTEIN</div>
                        <div className="flex items-center gap-2">
                            <span className="text-purple-400">🎯</span>
                            <span className="text-white font-medium">{runData.targetProtein}</span>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">CREATED</div>
                        <div className="flex items-center gap-2">
                            <span className="text-yellow-400">📅</span>
                            <span className="text-white font-medium">{runData.createdDate}</span>
                        </div>
                    </div>
                </div>

                {/* Score Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    {/* Engineering Score */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <Beaker className="w-5 h-5 text-blue-400" />
                            </div>
                            <div className="text-sm text-slate-400">Engineering Score (Avg)</div>
                        </div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-bold text-white">{runData.scores.engineering.value}</span>
                            <span className="text-slate-500">/ {runData.scores.engineering.max}</span>
                        </div>
                    </div>

                    {/* Biology Score */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                                <Activity className="w-5 h-5 text-green-400" />
                            </div>
                            <div className="text-sm text-slate-400">Biology Score (Avg)</div>
                        </div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-bold text-white">{runData.scores.biology.value}</span>
                            <span className="text-slate-500">/ {runData.scores.biology.max}</span>
                        </div>
                    </div>

                    {/* Safety Score */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                <ShieldAlert className="w-5 h-5 text-purple-400" />
                            </div>
                            <div className="text-sm text-slate-400">Safety Score (Avg)</div>
                        </div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-bold text-white">{runData.scores.safety.value}</span>
                            <span className="text-slate-500">/ {runData.scores.safety.max}</span>
                        </div>
                    </div>

                    {/* Total Candidates */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                                <Users className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div className="text-sm text-slate-400">Total Candidates</div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-white">{runData.totalCandidates.toLocaleString()}</span>
                            <span className="text-xs text-green-400">{runData.changePercent}</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">{runData.passedFilter} Passed initial filter</div>
                    </div>
                </div>

                {/* Candidates Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <h3 className="text-lg font-semibold text-white">Candidates</h3>
                            <div className="relative">
                                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type="text"
                                    placeholder="Search ID or Structure..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <button className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                                <Filter className="w-4 h-4" />
                                Filters
                            </button>
                            <button className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                                <ArrowUpDown className="w-4 h-4" />
                                Sort: Total Score
                            </button>
                            <span className="text-sm text-slate-400">{selectedCandidates.length} selected</span>
                            <Link
                                href={selectedCandidates.length >= 2
                                    ? `/design/runs/${runData.id}/compare?ids=${selectedCandidates.join(',')}`
                                    : '#'}
                                className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${selectedCandidates.length >= 2
                                        ? 'bg-blue-600 hover:bg-blue-500 text-white'
                                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                    }`}
                            >
                                Compare Selected
                            </Link>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-slate-900/50 border-b border-slate-800">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider w-12"></th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">RANK</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">ID</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">STRUCTURE</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">ENGINEERING</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">BIOLOGY</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">SAFETY</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">TOTAL SCORE</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">ACTIONS</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {candidates.map((cand) => (
                                    <tr key={cand.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <input
                                                type="checkbox"
                                                checked={selectedCandidates.includes(cand.id)}
                                                onChange={() => toggleCandidate(cand.id)}
                                                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500/50"
                                            />
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-white font-medium">#{cand.rank}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-blue-400 font-mono">{cand.id}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center">
                                                <Beaker className="w-6 h-6 text-slate-500" />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <span className={`font-medium ${getScoreColor(cand.engineering)}`}>{cand.engineering}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <span className={`font-medium ${getScoreColor(cand.biology)}`}>{cand.biology}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <span className={`font-medium ${getScoreColor(cand.safety)}`}>{cand.safety}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${getScoreBarColor(cand.totalScore)} rounded-full`}
                                                        style={{ width: `${(cand.totalScore / 10) * 100}%` }}
                                                    />
                                                </div>
                                                <span className="text-white font-semibold">{cand.totalScore}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <Link
                                                href={`/design/runs/${runData.id}/candidates/${cand.id}`}
                                                className="text-sm text-blue-400 hover:text-blue-300 font-medium"
                                            >
                                                View Details
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="p-4 border-t border-slate-800 flex items-center justify-between">
                        <div className="text-sm text-slate-400">
                            Showing 1-4 of {runData.totalCandidates.toLocaleString()}
                        </div>
                        <div className="flex items-center gap-2">
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded border border-slate-700 flex items-center gap-1 transition-colors">
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <button className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded font-medium">1</button>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded">2</button>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded">3</button>
                            <span className="text-slate-500">...</span>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded">42</button>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded border border-slate-700 flex items-center gap-1 transition-colors">
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
