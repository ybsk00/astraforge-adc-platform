import { getAdminStats } from '@/lib/actions/admin';
import { getTranslations } from 'next-intl/server';
import {
    Cable,
    Database,
    Activity,
    Clock,
    CheckCircle2,
    AlertCircle,
    FileText,
    History
} from 'lucide-react';

export default async function AdminDashboardPage() {
    const t = await getTranslations('Common');
    const stats = await getAdminStats();

    const kpiCards = [
        {
            title: t('menu.connectors'),
            value: stats.connectorRunsCount,
            icon: Cable,
            desc: 'Total connector executions',
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10'
        },
        {
            title: 'Design Runs',
            value: stats.designRunsCount,
            icon: FileText,
            desc: 'Total design runs generated',
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10'
        },
        {
            title: 'Queued Jobs',
            value: stats.queuedJobs,
            icon: Clock,
            desc: 'Jobs waiting in queue',
            color: 'text-amber-400',
            bgColor: 'bg-amber-400/10'
        }
    ];

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-1">Admin Dashboard</h1>
                    <p className="text-sm text-slate-400">Real-time system overview and management.</p>
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

                {/* Recent Activity */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <History className="w-5 h-5 text-blue-400" />
                            <h2 className="text-lg font-semibold text-white">Recent Audit Logs</h2>
                        </div>
                        <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                            View All
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">User</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Entity</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {stats.recentLogs.length > 0 ? (
                                    stats.recentLogs.map((log: any) => (
                                        <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="text-sm font-medium text-white">{log.profiles?.name || 'System'}</div>
                                                <div className="text-xs text-slate-500">{log.profiles?.email}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="px-2 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                                                    {log.action}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {log.entity_type} ({log.entity_id})
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-500">
                                                {new Date(log.created_at).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-slate-500 text-sm">
                                            No recent activity found.
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
