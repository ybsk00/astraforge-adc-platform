import { getAdminStats } from '@/lib/actions/admin';
import { getPromotedGoldenSets } from '@/lib/actions/golden-set';
import { getTranslations } from 'next-intl/server';
import {
    Cable,
    Database,
    Activity,
    Clock,
    CheckCircle2,
    FileText,
    ShieldCheck,
    ArrowRight
} from 'lucide-react';
import GoldenValidationTrend from '@/components/admin/GoldenValidationTrend';
import Link from 'next/link';

export default async function AdminDashboardPage() {
    const t = await getTranslations('Admin');
    const stats = await getAdminStats();
    const promotedSets = await getPromotedGoldenSets();

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

                {/* Golden Set Validation Trend */}
                <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <ShieldCheck className="w-5 h-5 text-green-400" />
                        <h2 className="text-lg font-semibold text-white">Golden Set 검증 트렌드</h2>
                    </div>
                    <GoldenValidationTrend />
                </div>

                {/* Final Promoted Golden Sets */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                            <h2 className="text-lg font-semibold text-white">최종 승격된 Golden Sets</h2>
                        </div>
                        <Link href="/admin/golden-sets" className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                            전체 보기 <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">이름</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">버전</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">후보 수</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">승격일</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">관리</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {promotedSets.length > 0 ? (
                                    promotedSets.map((set: any) => (
                                        <tr key={set.id} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="text-sm font-medium text-white">{set.name}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="px-2 py-1 text-xs font-medium rounded bg-slate-800 text-slate-300 border border-slate-700">
                                                    {set.version}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {set.candidate_count}개
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-500">
                                                {new Date(set.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <Link
                                                    href={`/admin/golden-sets/${set.id}`}
                                                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                                >
                                                    상세 보기
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-8 text-center text-slate-500 text-sm">
                                            승격된 골든 셋이 없습니다.
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
