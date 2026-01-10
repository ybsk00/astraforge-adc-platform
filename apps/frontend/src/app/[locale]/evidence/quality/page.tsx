'use client';

import { AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';

export default function EvidenceQualityPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">근거 품질 및 충돌 관리</h1>
                    <p className="text-slate-400">Forced Evidence, Conflict Alert, Negative Signals 등을 모니터링하고 해결합니다.</p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertTriangle className="w-6 h-6 text-red-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">12</div>
                            <div className="text-sm text-slate-400">Conflicts Detected</div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center">
                            <HelpCircle className="w-6 h-6 text-yellow-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">45</div>
                            <div className="text-sm text-slate-400">Missing Citations</div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-blue-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">8</div>
                            <div className="text-sm text-slate-400">Negative Signals</div>
                        </div>
                    </div>
                </div>

                {/* Issues List */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">품질 이슈 목록</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Run ID / Candidate</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Issue Type</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Severity</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Created At</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4">
                                    <div className="text-sm font-medium text-white">#RUN-853</div>
                                    <div className="text-xs text-slate-500">Candidate-A12</div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-sm text-red-400">Conflict</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">High</span>
                                </td>
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 10:00</td>
                                <td className="px-6 py-4">
                                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">Resolve</button>
                                </td>
                            </tr>
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4">
                                    <div className="text-sm font-medium text-white">#RUN-852</div>
                                    <div className="text-xs text-slate-500">Candidate-B05</div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-sm text-yellow-400">Missing Citation</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">Medium</span>
                                </td>
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-24 15:30</td>
                                <td className="px-6 py-4">
                                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">Review</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
