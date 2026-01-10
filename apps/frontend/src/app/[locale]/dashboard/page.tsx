'use client';

import { Link } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import {
    Beaker,
    CheckCircle,
    FileText,
    Zap,
    Plus,
    Upload,
    Search,
    MoreVertical,
    Server,
    Database
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

export default function DashboardPage() {
    const t = useTranslations('Dashboard');

    // Mock Data
    const userName = 'Dr. Kim';
    const lastUpdate = '2023-10-04 09:30 AM';

    const stats = [
        {
            label: t('stats.activeCandidates'),
            value: '24',
            change: '+69%',
            trend: 'up',
            icon: Beaker,
            color: 'text-blue-400',
            bg: 'bg-gradient-to-br from-blue-500/20 to-blue-600/10',
        },
        {
            label: t('stats.completedDesigns'),
            value: '142',
            change: '',
            icon: CheckCircle,
            color: 'text-green-400',
            bg: 'bg-gradient-to-br from-green-500/20 to-green-600/10',
        },
        {
            label: t('stats.indexedLiterature'),
            value: '8,902',
            change: '+103',
            trend: 'up',
            icon: FileText,
            color: 'text-purple-400',
            bg: 'bg-gradient-to-br from-purple-500/20 to-purple-600/10',
        },
        {
            label: t('stats.weeklyProtocols'),
            value: '15',
            change: '',
            icon: Zap,
            color: 'text-yellow-400',
            bg: 'bg-gradient-to-br from-yellow-500/20 to-yellow-600/10',
        },
    ];

    const quickActions = [
        { label: t('actions.newDesign'), description: t('actions.newDesignDesc'), icon: Plus, href: '/design/runs', primary: true },
        { label: t('actions.dataUpload'), description: t('actions.dataUploadDesc'), icon: Upload, href: '/data-upload', primary: false },
        { label: t('actions.literatureSearch'), description: t('actions.literatureSearchDesc'), icon: Search, href: '/literature-search', primary: false },
    ];

    const recentRuns = [
        { id: '#ADC-2401', target: 'HER2', linker: 'Val-Cit-PAB', date: 'Oct 24, 2023', status: 'completed', score: 94.2 },
        { id: '#ADC-2402', target: 'Trop2', linker: 'GGFG', date: 'Oct 23, 2023', status: 'processing', score: null },
        { id: '#ADC-2398', target: 'Hyd-aazone', linker: '', date: 'Oct 22, 2023', status: 'completed', score: 88.5 },
        { id: '#ADC-2395', target: 'EGFR', linker: 'SMCC', date: 'Oct 20, 2023', status: 'failed', score: null },
    ];

    const weeklyData = [
        { day: 'MON', value: 200 },
        { day: 'TUE', value: 350 },
        { day: 'WED', value: 180 },
        { day: 'THU', value: 420 },
        { day: 'FRI', value: 280 },
    ];

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed': return 'bg-green-500/20 text-green-400';
            case 'processing': return 'bg-blue-500/20 text-blue-400';
            case 'failed': return 'bg-red-500/20 text-red-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'completed': return t('status.completed');
            case 'processing': return t('status.processing');
            case 'failed': return t('status.failed');
            default: return status;
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-blue-400 mb-1">{t('welcome', { name: userName })}</h1>
                    <p className="text-sm text-slate-400">{t('welcomeSubtitle')}</p>
                    <p className="text-xs text-slate-500 mt-1">{t('lastUpdate', { date: lastUpdate })}</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {stats.map((stat, index) => (
                        <div key={index} className={`${stat.bg} border border-slate-800 rounded-xl p-5`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className={`p-2.5 rounded-lg bg-slate-900/50`}>
                                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                                </div>
                                {stat.change && (
                                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${stat.trend === 'up' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                        }`}>
                                        {stat.change}
                                    </span>
                                )}
                            </div>
                            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">{stat.label}</div>
                            <div className="text-3xl font-bold text-white">{stat.value}</div>
                        </div>
                    ))}
                </div>

                {/* Quick Actions */}
                <div className="mb-8">
                    <h2 className="text-lg font-semibold text-white mb-4">{t('quickActions')}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {quickActions.map((action, index) => (
                            <Link
                                key={index}
                                href={action.href}
                                className={`group p-5 rounded-xl border transition-all ${action.primary
                                    ? 'bg-blue-600 hover:bg-blue-500 border-blue-500'
                                    : 'bg-slate-900 hover:bg-slate-800 border-slate-800 hover:border-slate-700'
                                    }`}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`p-3 rounded-lg ${action.primary ? 'bg-blue-500' : 'bg-slate-800'}`}>
                                        <action.icon className={`w-5 h-5 ${action.primary ? 'text-white' : 'text-slate-400'}`} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="text-white font-medium">{action.label}</div>
                                        <div className={`text-sm ${action.primary ? 'text-blue-100' : 'text-slate-400'}`}>
                                            {action.description}
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Recent Runs Table */}
                    <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white">{t('recentRuns')}</h3>
                            <Link href="/design/runs" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                                {t('viewAll')}
                            </Link>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-slate-800">
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.runId')}</th>
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.targetLinker')}</th>
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.date')}</th>
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.status')}</th>
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.score')}</th>
                                        <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase">{t('table.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {recentRuns.map((run, index) => (
                                        <tr key={index} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-5 py-4 text-sm font-mono text-blue-400">{run.id}</td>
                                            <td className="px-5 py-4">
                                                <div className="text-sm text-white font-medium">{run.target}</div>
                                                <div className="text-xs text-slate-400">{run.linker || '-'}</div>
                                            </td>
                                            <td className="px-5 py-4 text-sm text-slate-400">{run.date}</td>
                                            <td className="px-5 py-4">
                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadge(run.status)}`}>
                                                    {run.status === 'processing' ? '● ' : ''}{getStatusLabel(run.status)}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4">
                                                {run.score ? (
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                                                                style={{ width: `${run.score}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-sm text-white font-medium">{run.score}%</span>
                                                    </div>
                                                ) : (
                                                    <span className="text-sm text-slate-500">
                                                        {run.status === 'processing' ? t('status.calculating') : 'N/A'}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-5 py-4">
                                                <button className="text-slate-400 hover:text-white transition-colors">
                                                    <MoreVertical className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Right Sidebar */}
                    <div className="space-y-6">
                        {/* Weekly Analytics */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <h3 className="text-lg font-semibold text-white mb-2">{t('weeklyAnalysis')}</h3>
                            <div className="flex items-baseline gap-2 mb-4">
                                <span className="text-3xl font-bold text-white">1,240</span>
                                <span className="text-sm text-slate-400">{t('totalScans')}</span>
                            </div>
                            <div className="h-[120px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={weeklyData}>
                                        <defs>
                                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                                        <YAxis hide />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#3b82f6"
                                            strokeWidth={2}
                                            fillOpacity={1}
                                            fill="url(#colorValue)"
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* System Status */}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <h3 className="text-lg font-semibold text-white mb-4">{t('systemStatus')}</h3>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-green-500/20 rounded-lg">
                                            <Server className="w-4 h-4 text-green-400" />
                                        </div>
                                        <span className="text-sm text-slate-300">{t('system.computationNode')}</span>
                                    </div>
                                    <span className="text-sm text-green-400 font-medium">{t('system.operational')}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-blue-500/20 rounded-lg">
                                            <Database className="w-4 h-4 text-blue-400" />
                                        </div>
                                        <span className="text-sm text-slate-300">{t('system.databaseIndex')}</span>
                                    </div>
                                    <span className="text-sm text-blue-400 font-medium">{t('system.syncing')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
