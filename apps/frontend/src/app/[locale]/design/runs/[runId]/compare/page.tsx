'use client';

import { ArrowLeft, Download } from 'lucide-react';
import { Link } from '@/i18n/routing';

export default function ComparePage({ params }: { params: { runId: string } }) {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Link href={`/design/runs/${params.runId}`} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">후보 물질 비교</h1>
                        <p className="text-slate-400">선택한 후보 물질들의 주요 지표를 비교합니다.</p>
                    </div>
                    <div className="ml-auto">
                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors">
                            <Download className="w-4 h-4" />
                            리포트 생성
                        </button>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr>
                                <th className="p-6 border-b border-r border-slate-800 bg-slate-900/50 min-w-[200px]">Metric</th>
                                <th className="p-6 border-b border-r border-slate-800 min-w-[250px]">
                                    <div className="font-bold text-white mb-1">Candidate A</div>
                                    <div className="text-xs text-slate-500">HER2-ValCit-MMAE</div>
                                </th>
                                <th className="p-6 border-b border-r border-slate-800 min-w-[250px]">
                                    <div className="font-bold text-white mb-1">Candidate B</div>
                                    <div className="text-xs text-slate-500">HER2-GGFG-DXd</div>
                                </th>
                                <th className="p-6 border-b border-slate-800 min-w-[250px]">
                                    <div className="font-bold text-white mb-1">Candidate C</div>
                                    <div className="text-xs text-slate-500">HER2-SMCC-DM1</div>
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Total Score</td>
                                <td className="p-6 border-r border-slate-800 text-xl font-bold text-blue-400">0.92</td>
                                <td className="p-6 border-r border-slate-800 text-xl font-bold text-blue-400">0.89</td>
                                <td className="p-6 border-slate-800 text-xl font-bold text-slate-400">0.75</td>
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Engineering Score</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.95</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.88</td>
                                <td className="p-6 border-slate-800 text-white">0.82</td>
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Biological Score</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.88</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.91</td>
                                <td className="p-6 border-slate-800 text-white">0.70</td>
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Safety Score</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.91</td>
                                <td className="p-6 border-r border-slate-800 text-white">0.85</td>
                                <td className="p-6 border-slate-800 text-white">0.65</td>
                            </tr>
                            <tr>
                                <td className="p-6 border-r border-slate-800 font-medium text-slate-300">Evidence Count</td>
                                <td className="p-6 border-r border-slate-800 text-white">12 (2 Negative)</td>
                                <td className="p-6 border-r border-slate-800 text-white">8 (0 Negative)</td>
                                <td className="p-6 border-slate-800 text-white">5 (1 Negative)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
