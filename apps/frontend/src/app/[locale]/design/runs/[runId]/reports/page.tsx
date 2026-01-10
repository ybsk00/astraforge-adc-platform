'use client';

import { ArrowLeft, FileText, Download, CheckCircle } from 'lucide-react';
import { Link } from '@/i18n/routing';

export default function ReportsPage({ params }: { params: { runId: string } }) {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Link href={`/design/runs/${params.runId}`} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">리포트 생성</h1>
                        <p className="text-slate-400">설계 실행 결과에 대한 상세 리포트를 생성하고 관리합니다.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Generation Form */}
                    <div className="lg:col-span-1">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-6">새 리포트 생성</h3>
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        포함 범위
                                    </label>
                                    <select className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                                        <option>Top 10 Candidates</option>
                                        <option>Top 20 Candidates</option>
                                        <option>Top 50 Candidates</option>
                                        <option>Selected Candidates Only</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        포맷
                                    </label>
                                    <div className="flex gap-4">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="radio" name="format" defaultChecked className="text-blue-600 focus:ring-blue-500 bg-slate-800 border-slate-700" />
                                            <span className="text-white">PDF</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="radio" name="format" className="text-blue-600 focus:ring-blue-500 bg-slate-800 border-slate-700" />
                                            <span className="text-white">HTML</span>
                                        </label>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        포함할 섹션
                                    </label>
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="checkbox" defaultChecked className="rounded text-blue-600 focus:ring-blue-500 bg-slate-800 border-slate-700" />
                                            <span className="text-slate-300">Evidence Analysis</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="checkbox" defaultChecked className="rounded text-blue-600 focus:ring-blue-500 bg-slate-800 border-slate-700" />
                                            <span className="text-slate-300">Protocol Recommendations</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="checkbox" defaultChecked className="rounded text-blue-600 focus:ring-blue-500 bg-slate-800 border-slate-700" />
                                            <span className="text-slate-300">Score Breakdown</span>
                                        </label>
                                    </div>
                                </div>
                                <button className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors flex justify-center items-center gap-2">
                                    <FileText className="w-4 h-4" />
                                    리포트 생성
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* History */}
                    <div className="lg:col-span-2">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-800">
                                <h3 className="font-semibold text-white">생성 내역</h3>
                            </div>
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-slate-800">
                                        <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Date</th>
                                        <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Scope</th>
                                        <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Format</th>
                                        <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                                        <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    <tr className="hover:bg-slate-800/50">
                                        <td className="px-6 py-4 text-sm text-slate-500">2023-10-25 14:00</td>
                                        <td className="px-6 py-4 text-sm text-white">Top 10 Candidates</td>
                                        <td className="px-6 py-4 text-sm text-slate-400">PDF</td>
                                        <td className="px-6 py-4">
                                            <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/20 px-2 py-1 rounded">
                                                <CheckCircle className="w-3 h-3" /> Ready
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                                                <Download className="w-3 h-3" /> Download
                                            </button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
