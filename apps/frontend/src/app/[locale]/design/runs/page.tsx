'use client';

import { useState } from 'react';
import { Link } from '@/i18n/routing';
import {
    Search,
    Filter,
    Plus,
    Download,
    MoreVertical,
    ChevronLeft,
    ChevronRight,
    Beaker
} from 'lucide-react';
import NewRunModal from '@/components/design/NewRunModal';

export default function DesignRunsPage() {
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [isNewRunModalOpen, setIsNewRunModalOpen] = useState(false);

    // Mock Data
    const runs = [
        {
            id: '#RUN-853',
            target: 'BCMA-V2',
            targetDesc: 'Ligand: IgG1-mab',
            algorithm: 'GROMACS',
            date: '2023-10-21',
            status: 'Completed',
            score: 91.0
        },
        {
            id: '#RUN-852',
            target: 'TROP2-ADC',
            targetDesc: 'Ligand: Trop-2 antibody',
            algorithm: 'AutoDock',
            date: '2023-10-22',
            status: 'Completed',
            score: 88.1
        },
        {
            id: '#RUN-851',
            target: 'CD19-Payload',
            targetDesc: 'Ligand: CD19-CAR',
            algorithm: 'Rosetta',
            date: '2023-10-23',
            status: 'Failed',
            score: 12.5
        },
        {
            id: '#RUN-850',
            target: 'EGFR-Linker',
            targetDesc: 'Ligand: Cetuximab',
            algorithm: 'GROMACS',
            date: '2023-10-25',
            status: 'Processing',
            score: null
        },
        {
            id: '#RUN-849',
            target: 'HER2-Conjugate',
            targetDesc: 'Ligand: Trastuzumab',
            algorithm: 'AutoDock',
            date: '2023-10-24',
            status: 'Completed',
            score: 94.2
        },
    ];

    const statusFilters = [
        { key: 'all', label: '전체', count: 16 },
        { key: 'processing', label: '진행중', count: 2 },
        { key: 'completed', label: '완료', count: 1 },
        { key: 'failed', label: '실패', count: 1 },
    ];

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'Completed': return 'bg-green-500/20 text-green-400';
            case 'Processing': return 'bg-blue-500/20 text-blue-400';
            case 'Failed': return 'bg-red-500/20 text-red-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    const getScoreColor = (score: number | null) => {
        if (score === null) return '';
        if (score >= 90) return 'text-green-400';
        if (score >= 70) return 'text-blue-400';
        if (score >= 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getScoreBarColor = (score: number | null) => {
        if (score === null) return 'bg-slate-600';
        if (score >= 90) return 'bg-gradient-to-r from-green-500 to-green-400';
        if (score >= 70) return 'bg-gradient-to-r from-blue-500 to-blue-400';
        if (score >= 50) return 'bg-gradient-to-r from-yellow-500 to-yellow-400';
        return 'bg-gradient-to-r from-red-500 to-red-400';
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">설계 실행</h1>
                        <p className="text-slate-400 text-sm">모든 약물 설계 및 후보 물질 스코어링 작업을 관리합니다.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => alert('기능 준비 중입니다.')}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <Download className="w-4 h-4" />
                            가져오기
                        </button>
                        <button
                            onClick={() => setIsNewRunModalOpen(true)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            + 새런생성
                        </button>
                    </div>
                </div>

                {/* Search and Filter */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        {/* Search */}
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Run ID, 화합물 이름 또는 대상 단백질 검색..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Status Filters */}
                        <div className="flex items-center gap-2">
                            {statusFilters.map((sf) => (
                                <button
                                    key={sf.key}
                                    onClick={() => setFilter(sf.key)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === sf.key
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                                        }`}
                                >
                                    {sf.label} {sf.count}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-800">
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">RUN ID</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">대상 단백질 (TARGET)</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">알고리즘</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">시작 날짜</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">상태</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">스코어</th>
                                    <th className="px-6 py-4 text-xs font-medium text-slate-500 uppercase tracking-wider">작업</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {runs.map((run) => (
                                    <tr key={run.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-mono text-blue-400">{run.id}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                                                    <Beaker className="w-5 h-5 text-slate-500" />
                                                </div>
                                                <div>
                                                    <div className="text-sm text-white font-medium">{run.target}</div>
                                                    <div className="text-xs text-slate-400">{run.targetDesc}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-2.5 py-1 rounded text-xs font-medium bg-purple-500/20 text-purple-400">
                                                {run.algorithm}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{run.date}</td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadge(run.status)}`}>
                                                {run.status === 'Processing' && '● '}{run.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {run.score !== null ? (
                                                <div className="flex items-center gap-3">
                                                    <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full ${getScoreBarColor(run.score)}`}
                                                            style={{ width: `${run.score}%` }}
                                                        />
                                                    </div>
                                                    <span className={`text-sm font-medium ${getScoreColor(run.score)}`}>
                                                        {run.score}%
                                                    </span>
                                                </div>
                                            ) : (
                                                <span className="text-sm text-slate-500">계산 중...</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <button className="p-1.5 text-slate-400 hover:text-white transition-colors">
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                        <div className="text-sm text-slate-400">
                            Showing <span className="text-white font-medium">1</span> to <span className="text-white font-medium">5</span> of <span className="text-white font-medium">16</span> results
                        </div>
                        <div className="flex items-center gap-2">
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded border border-slate-700 transition-colors">
                                이전
                            </button>
                            <button className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded font-medium">1</button>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded">2</button>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded">3</button>
                            <span className="text-slate-500">...</span>
                            <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm rounded border border-slate-700 transition-colors">
                                다음
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            {isNewRunModalOpen && (
                <NewRunModal
                    onClose={() => setIsNewRunModalOpen(false)}
                    onCreated={() => {
                        setIsNewRunModalOpen(false);
                        // TODO: Refresh list
                        window.location.reload();
                    }}
                />
            )}
        </div>
    );
}
