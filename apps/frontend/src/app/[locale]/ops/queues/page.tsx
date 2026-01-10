'use client';

import { Server, RefreshCw, Play } from 'lucide-react';

export default function OpsQueuesPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">작업 큐 관리</h1>
                        <p className="text-slate-400">백그라운드 작업 큐 상태를 모니터링하고 실패한 작업을 재시도합니다.</p>
                    </div>
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors">
                        <RefreshCw className="w-5 h-5" />
                    </button>
                </div>

                {/* Queue Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Design Run Queue</h3>
                            <Server className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="text-xl font-bold text-white">2</div>
                                <div className="text-xs text-slate-500">Active</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">5</div>
                                <div className="text-xs text-slate-500">Queued</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-red-400">1</div>
                                <div className="text-xs text-slate-500">Failed</div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Ingestion Queue</h3>
                            <Server className="w-5 h-5 text-purple-500" />
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="text-xl font-bold text-white">12</div>
                                <div className="text-xs text-slate-500">Active</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">150</div>
                                <div className="text-xs text-slate-500">Queued</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">0</div>
                                <div className="text-xs text-slate-500">Failed</div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Email Queue</h3>
                            <Server className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="text-xl font-bold text-white">0</div>
                                <div className="text-xs text-slate-500">Active</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">0</div>
                                <div className="text-xs text-slate-500">Queued</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">0</div>
                                <div className="text-xs text-slate-500">Failed</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Failed Jobs */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">실패한 작업 목록</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Job ID</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Queue</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Function</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Failed At</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Error</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-mono text-slate-300">job_8f7a2c...</td>
                                <td className="px-6 py-4 text-sm text-slate-400">design_run_queue</td>
                                <td className="px-6 py-4 text-sm text-white">design_run_execute</td>
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 14:00</td>
                                <td className="px-6 py-4 text-sm text-red-400">ValueError: Invalid target ID</td>
                                <td className="px-6 py-4">
                                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                                        <Play className="w-3 h-3" /> 재시도
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
