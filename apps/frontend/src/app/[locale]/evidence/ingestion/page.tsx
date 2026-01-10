'use client';

import { Database, RefreshCw, Play, AlertTriangle } from 'lucide-react';

export default function IngestionStatusPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">문헌 수집/인덱싱 상태</h1>
                        <p className="text-slate-400">PubMed 커넥터 및 데이터 인덱싱 파이프라인 상태를 모니터링합니다.</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors">
                            <RefreshCw className="w-4 h-4" />
                            새로고침
                        </button>
                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                            <Play className="w-4 h-4" />
                            수집 실행
                        </button>
                    </div>
                </div>

                {/* Status Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Last Run</h3>
                            <Database className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">10분 전</div>
                        <div className="text-xs text-green-400">성공적으로 완료됨</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Docs Ingested</h3>
                            <div className="text-xs font-mono text-slate-500">TODAY</div>
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">1,240</div>
                        <div className="text-xs text-slate-400">Total: 6.8M</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Embeddings</h3>
                            <div className="text-xs font-mono text-slate-500">PENDING</div>
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">45</div>
                        <div className="text-xs text-yellow-400">처리 대기 중</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-slate-400 text-sm font-medium">Failures</h3>
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                        </div>
                        <div className="text-2xl font-bold text-white mb-1">3</div>
                        <div className="text-xs text-red-400">재시도 필요</div>
                    </div>
                </div>

                {/* Recent Jobs Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800">
                        <h3 className="font-semibold text-white">최근 작업 로그</h3>
                    </div>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Document ID</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Updated At</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Error</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-mono text-slate-300">PMID:37829102</td>
                                <td className="px-6 py-4"><span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">Failed</span></td>
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 14:45</td>
                                <td className="px-6 py-4 text-sm text-red-400">Timeout during embedding</td>
                                <td className="px-6 py-4">
                                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">Retry</button>
                                </td>
                            </tr>
                            <tr className="hover:bg-slate-800/50">
                                <td className="px-6 py-4 text-sm font-mono text-slate-300">PMID:37829101</td>
                                <td className="px-6 py-4"><span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Done</span></td>
                                <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 14:42</td>
                                <td className="px-6 py-4 text-sm text-slate-500">-</td>
                                <td className="px-6 py-4 text-sm text-slate-500">-</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
