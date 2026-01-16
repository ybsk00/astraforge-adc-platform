'use client';

import { Activity, Server, Database, Cpu } from 'lucide-react';

export default function OpsStatusPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">시스템 상태</h1>
                    <p className="text-slate-400">엔진, 워커, 데이터베이스, 인프라의 실시간 상태를 확인합니다.</p>
                </div>

                {/* System Health Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Engine API</h3>
                            <Activity className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full" />
                            <span className="text-xl font-bold text-white">Operational</span>
                        </div>
                        <div className="text-xs text-slate-500">Uptime: 99.9%</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Worker Nodes</h3>
                            <Cpu className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full" />
                            <span className="text-xl font-bold text-white">4/4 Active</span>
                        </div>
                        <div className="text-xs text-slate-500">Load: 45%</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Database</h3>
                            <Database className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full" />
                            <span className="text-xl font-bold text-white">Healthy</span>
                        </div>
                        <div className="text-xs text-slate-500">Connections: 12</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Vector Index</h3>
                            <Server className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                            <span className="text-xl font-bold text-white">Syncing</span>
                        </div>
                        <div className="text-xs text-slate-500">Lag: 2s</div>
                    </div>
                </div>

                {/* Component Status Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">상세 컴포넌트 상태</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Component</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Message</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Last Check</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-medium text-white">Redis Queue</td>
                                <td className="px-6 py-4"><span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">OK</span></td>
                                <td className="px-6 py-4 text-sm text-slate-500">Connected</td>
                                <td className="px-6 py-4 text-sm text-slate-500">Just now</td>
                            </tr>
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-medium text-white">LLM Gateway (Gemini)</td>
                                <td className="px-6 py-4"><span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">OK</span></td>
                                <td className="px-6 py-4 text-sm text-slate-500">Latency: 120ms</td>
                                <td className="px-6 py-4 text-sm text-slate-500">1 min ago</td>
                            </tr>
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-medium text-white">PubMed Connector</td>
                                <td className="px-6 py-4"><span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">Degraded</span></td>
                                <td className="px-6 py-4 text-sm text-slate-500">Rate limit warning</td>
                                <td className="px-6 py-4 text-sm text-slate-500">5 mins ago</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
