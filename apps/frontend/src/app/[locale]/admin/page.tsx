import { getAdminStats } from '@/lib/actions/admin';
import { getPromotedGoldenSets } from '@/lib/actions/golden-set';
import { getTranslations } from 'next-intl/server';
import {
    Cable,
    FileText,
    Clock,
    CheckCircle2,
    ArrowRight,
    Beaker,
    Target
} from 'lucide-react';
import Link from 'next/link';

interface FinalSeed {
    id: string;
    drug_name_canonical: string;
    resolved_target_symbol?: string;
    payload_family?: string;
    clinical_phase?: string;
}

export default async function AdminDashboardPage() {
    const t = await getTranslations('Admin');
    const stats = await getAdminStats();
    const finalSeeds = await getPromotedGoldenSets() as FinalSeed[];

    const kpiCards = [
        {
            title: t('stats.connectors'),
            value: stats.connectorRunsCount,
            icon: Cable,
            desc: t('stats.connectorsDesc'),
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10'
        },
        {
            title: t('stats.designRuns'),
            value: stats.designRunsCount,
            icon: FileText,
            desc: t('stats.designRunsDesc'),
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10'
        },
        {
            title: t('stats.queuedJobs'),
            value: stats.queuedJobs,
            icon: Clock,
            desc: t('stats.queuedJobsDesc'),
            color: 'text-amber-400',
            bgColor: 'bg-amber-400/10'
        }
    ];

    // Phase badge color helper
    const getPhaseBadge = (phase: string | null) => {
        if (!phase) return { bg: 'bg-slate-700', text: 'text-slate-400', label: '-' };
        if (phase === 'Approved') return { bg: 'bg-green-900/50', text: 'text-green-400', label: phase };
        if (phase.includes('3')) return { bg: 'bg-blue-900/50', text: 'text-blue-400', label: phase };
        if (phase.includes('2')) return { bg: 'bg-purple-900/50', text: 'text-purple-400', label: phase };
        return { bg: 'bg-slate-700', text: 'text-slate-400', label: phase };
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-1">{t('title')}</h1>
                    <p className="text-sm text-slate-400">{t('subtitle')}</p>
                </div>

                {/* KPI Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {kpiCards.map((card, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className={`p-2 rounded-lg ${card.bgColor}`}>
                                    <card.icon className={`w-6 h-6 ${card.color}`} />
                                </div>
                                <span className="text-2xl font-bold text-white">{card.value}</span>
                            </div>
                            <h3 className="text-sm font-medium text-slate-400">{card.title}</h3>
                            <p className="text-xs text-slate-500 mt-1">{card.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Final Seeds Summary Card */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/20 border border-green-800/50 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <CheckCircle2 className="w-6 h-6 text-green-400" />
                            <span className="text-2xl font-bold text-white">{finalSeeds.length}</span>
                        </div>
                        <div className="text-sm text-green-400">Final Seeds</div>
                        <div className="text-xs text-slate-500 mt-1">승격 완료된 Golden Set</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <Target className="w-5 h-5 text-blue-400" />
                            <span className="text-lg font-bold text-white">
                                {new Set(finalSeeds.map((s: FinalSeed) => s.resolved_target_symbol).filter(Boolean)).size}
                            </span>
                        </div>
                        <div className="text-sm text-slate-400">Unique Targets</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <Beaker className="w-5 h-5 text-purple-400" />
                            <span className="text-lg font-bold text-white">
                                {new Set(finalSeeds.map((s: FinalSeed) => s.payload_family).filter(Boolean)).size}
                            </span>
                        </div>
                        <div className="text-sm text-slate-400">Payload Families</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <CheckCircle2 className="w-5 h-5 text-amber-400" />
                            <span className="text-lg font-bold text-white">
                                {finalSeeds.filter((s: FinalSeed) => s.clinical_phase === 'Approved').length}
                            </span>
                        </div>
                        <div className="text-sm text-slate-400">Approved</div>
                    </div>
                </div>

                {/* Final Seeds Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                            <h2 className="text-lg font-semibold text-white">최종 승격된 Golden Seeds</h2>
                            <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-green-900/50 text-green-400 rounded">
                                {finalSeeds.length}
                            </span>
                        </div>
                        <Link href="/admin/golden-sets" className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                            전체 보기 <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Drug Name</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Target</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Payload</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Phase</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">상세</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {finalSeeds.length > 0 ? (
                                    finalSeeds.slice(0, 10).map((seed: FinalSeed) => {
                                        const phaseBadge = getPhaseBadge(seed.clinical_phase || null);
                                        return (
                                            <tr key={seed.id} className="hover:bg-slate-800/30 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="text-sm font-medium text-white">{seed.drug_name_canonical}</div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="px-2 py-1 text-xs font-medium rounded bg-blue-900/30 text-blue-400 border border-blue-800/50">
                                                        {seed.resolved_target_symbol || '-'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-400">
                                                    {seed.payload_family || '-'}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 text-xs font-medium rounded ${phaseBadge.bg} ${phaseBadge.text}`}>
                                                        {phaseBadge.label}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <Link
                                                        href={`/admin/golden-sets/manual/${seed.id}`}
                                                        className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                                    >
                                                        보기
                                                    </Link>
                                                </td>
                                            </tr>
                                        );
                                    })
                                ) : (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-8 text-center text-slate-500 text-sm">
                                            승격된 Golden Seed가 없습니다.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

