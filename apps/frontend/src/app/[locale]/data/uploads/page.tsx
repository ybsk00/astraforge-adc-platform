'use client';

import { FileText, RefreshCw, ExternalLink } from 'lucide-react';

export default function UploadHistoryPage() {
    // Mock Data
    const uploads = [
        { id: 1, filename: 'assay_results_20231025.csv', type: 'Assay Results', size: '2.4 MB', status: 'completed', date: '2023-10-25 14:30' },
        { id: 2, filename: 'protocol_output_v2.json', type: 'Protocol Outputs', size: '156 KB', status: 'processing', date: '2023-10-25 14:28' },
        { id: 3, filename: 'invalid_data.xlsx', type: 'Misc', size: '5.1 MB', status: 'failed', date: '2023-10-24 09:15' },
    ];

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed': return 'bg-green-500/20 text-green-400';
            case 'processing': return 'bg-blue-500/20 text-blue-400';
            case 'failed': return 'bg-red-500/20 text-red-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">업로드 내역</h1>
                        <p className="text-slate-400">데이터 파일 업로드 및 처리 상태를 확인합니다.</p>
                    </div>
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors">
                        <RefreshCw className="w-5 h-5" />
                    </button>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">파일명</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">타입</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">크기</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">상태</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">업로드 일시</th>
                                <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase">작업</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {uploads.map((item) => (
                                <tr key={item.id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-slate-500" />
                                            <span className="text-sm text-white font-medium">{item.filename}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{item.type}</td>
                                    <td className="px-6 py-4 text-sm text-slate-500">{item.size}</td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                                            {item.status === 'processing' && '● '}{item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-500">{item.date}</td>
                                    <td className="px-6 py-4">
                                        <button className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                                            상세 <ExternalLink className="w-3 h-3" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
