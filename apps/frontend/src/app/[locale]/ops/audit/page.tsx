'use client';

import { Search } from 'lucide-react';

export default function OpsAuditPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">감사 로그 (Audit)</h1>
                    <p className="text-slate-400">사용자 활동 및 주요 시스템 이벤트를 추적합니다.</p>
                </div>

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="사용자, 액션, 또는 리소스 ID 검색..."
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option>모든 이벤트</option>
                        <option>로그인/로그아웃</option>
                        <option>데이터 변경</option>
                        <option>설정 변경</option>
                    </select>
                    <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 transition-colors">
                        필터 적용
                    </button>
                </div>

                {/* Audit Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Timestamp</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Actor</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Target</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Metadata</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 15:30:22</td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center text-xs text-blue-400 font-bold">JD</div>
                                        <span className="text-sm text-white">John Doe</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4"><span className="text-sm text-blue-400 font-medium">CREATE_RUN</span></td>
                                <td className="px-6 py-4 text-sm text-slate-300">Run #853</td>
                                <td className="px-6 py-4 text-xs font-mono text-slate-500">{"{strategy: 'balanced'}"}</td>
                            </tr>
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 15:28:10</td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center text-xs text-blue-400 font-bold">JD</div>
                                        <span className="text-sm text-white">John Doe</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4"><span className="text-sm text-green-400 font-medium">LOGIN</span></td>
                                <td className="px-6 py-4 text-sm text-slate-300">-</td>
                                <td className="px-6 py-4 text-xs font-mono text-slate-500">{"{ip: '192.168.1.1'}"}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
