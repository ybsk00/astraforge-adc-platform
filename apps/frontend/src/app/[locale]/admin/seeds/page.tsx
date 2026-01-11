'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import {
    Database,
    Plus,
    RefreshCw,
    Search,
    CheckCircle2,
    Dna,
    Stethoscope,
    Pill,
    Layers,
    X,
    Loader2
} from 'lucide-react';
import {
    getSeedTargets,
    getSeedDiseases,
    getSeedSets,
    createSeedSet
} from '@/lib/actions/admin';
import { clsx } from 'clsx';

export default function SeedManagementPage() {
    const t = useTranslations('Admin.seeds');
    const [activeTab, setActiveTab] = useState<'targets' | 'diseases' | 'sets'>('targets');
    const [targets, setTargets] = useState<any[]>([]);
    const [diseases, setDiseases] = useState<any[]>([]);
    const [seedSets, setSeedSets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newSetName, setNewSetName] = useState('');
    const [selectedTargets, setSelectedTargets] = useState<string[]>([]);
    const [selectedDiseases, setSelectedDiseases] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [tData, dData, sData] = await Promise.all([
                getSeedTargets(),
                getSeedDiseases(),
                getSeedSets()
            ]);
            setTargets(tData);
            setDiseases(dData);
            setSeedSets(sData);
        } catch (error) {
            console.error('Failed to fetch seed data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateSet = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newSetName || (selectedTargets.length === 0 && selectedDiseases.length === 0)) return;

        setSubmitting(true);
        try {
            await createSeedSet(newSetName, selectedTargets, selectedDiseases);
            setIsModalOpen(false);
            setNewSetName('');
            setSelectedTargets([]);
            setSelectedDiseases([]);
            await fetchData();
        } catch (error) {
            console.error('Failed to create seed set:', error);
            alert('Seed Set 생성에 실패했습니다.');
        } finally {
            setSubmitting(false);
        }
    };

    const filteredData = () => {
        const query = searchQuery.toLowerCase();
        if (activeTab === 'targets') {
            return targets.filter(t =>
                t.gene_symbol?.toLowerCase().includes(query) ||
                t.ensembl_gene_id?.toLowerCase().includes(query)
            );
        } else if (activeTab === 'diseases') {
            return diseases.filter(d =>
                d.disease_name?.toLowerCase().includes(query) ||
                d.efo_id?.toLowerCase().includes(query)
            );
        } else {
            return seedSets.filter(s =>
                s.seed_set_name?.toLowerCase().includes(query)
            );
        }
    };

    const data = filteredData();

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">{t('title')}</h1>
                        <p className="text-slate-400 text-sm">{t('subtitle')}</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            Seed Set 생성
                        </button>
                        <button
                            onClick={fetchData}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
                            {useTranslations('Admin.connectors')('refresh')}
                        </button>
                    </div>
                </div>

                {/* Tabs & Search */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800">
                        <button
                            onClick={() => setActiveTab('targets')}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                activeTab === 'targets' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            <Dna className="w-4 h-4" />
                            {t('tabs.targets')}
                        </button>
                        <button
                            onClick={() => setActiveTab('diseases')}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                activeTab === 'diseases' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            <Stethoscope className="w-4 h-4" />
                            {t('tabs.diseases')}
                        </button>
                        <button
                            onClick={() => setActiveTab('sets')}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                activeTab === 'sets' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            <Layers className="w-4 h-4" />
                            {t('tabs.sets')}
                        </button>
                    </div>

                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="검색어 입력..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full md:w-64 bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        />
                    </div>
                </div>

                {/* Content Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('table.name')}</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('table.id')}</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('table.status')}</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">{t('table.actions')}</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {loading ? (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center">
                                            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
                                            <p className="text-slate-500 text-sm">데이터를 불러오는 중...</p>
                                        </td>
                                    </tr>
                                ) : data.length > 0 ? (
                                    data.map((item: any) => (
                                        <tr key={item.id} className="hover:bg-slate-800/30 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-blue-400">
                                                        {activeTab === 'targets' ? <Dna className="w-4 h-4" /> :
                                                            activeTab === 'diseases' ? <Stethoscope className="w-4 h-4" /> :
                                                                <Layers className="w-4 h-4" />}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-white">
                                                            {activeTab === 'targets' ? item.gene_symbol :
                                                                activeTab === 'diseases' ? item.disease_name :
                                                                    item.seed_set_name}
                                                        </div>
                                                        {activeTab === 'targets' && (
                                                            <div className="text-[10px] text-slate-500 uppercase">{item.full_name}</div>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <code className="text-xs text-slate-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                                                    {activeTab === 'targets' ? item.ensembl_gene_id || 'N/A' :
                                                        activeTab === 'diseases' ? item.efo_id || 'N/A' :
                                                            item.id.split('-')[0]}
                                                </code>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={clsx(
                                                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium border",
                                                    (activeTab === 'sets' || (activeTab === 'targets' && item.ensembl_gene_id) || (activeTab === 'diseases' && item.efo_id))
                                                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                                                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                                )}>
                                                    {(activeTab === 'sets' || (activeTab === 'targets' && item.ensembl_gene_id) || (activeTab === 'diseases' && item.efo_id))
                                                        ? <CheckCircle2 className="w-3 h-3" />
                                                        : <RefreshCw className="w-3 h-3" />}
                                                    {(activeTab === 'sets' || (activeTab === 'targets' && item.ensembl_gene_id) || (activeTab === 'diseases' && item.efo_id))
                                                        ? "Resolved" : "Pending"}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button className="text-slate-500 hover:text-white transition-colors">
                                                    <RefreshCw className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500 text-sm">
                                            데이터가 없습니다.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Create Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
                            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                                <div>
                                    <h2 className="text-xl font-bold text-white">신규 Seed Set 생성</h2>
                                    <p className="text-xs text-slate-500 mt-1">타겟과 질환을 조합하여 새로운 수집 단위를 정의합니다.</p>
                                </div>
                                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                            <form onSubmit={handleCreateSet} className="p-6 space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">Seed Set 이름</label>
                                    <input
                                        required
                                        type="text"
                                        value={newSetName}
                                        onChange={e => setNewSetName(e.target.value)}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all"
                                        placeholder="예: Top 250 Targets - Breast Cancer"
                                    />
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Target Selection */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">타겟 선택 ({selectedTargets.length})</label>
                                        <div className="bg-slate-950 border border-slate-800 rounded-xl h-48 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                                            {targets.map(t => (
                                                <label key={t.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-900 cursor-pointer transition-colors">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedTargets.includes(t.id)}
                                                        onChange={(e) => {
                                                            if (e.target.checked) setSelectedTargets([...selectedTargets, t.id]);
                                                            else setSelectedTargets(selectedTargets.filter(id => id !== t.id));
                                                        }}
                                                        className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
                                                    />
                                                    <span className="text-sm text-slate-300">{t.gene_symbol}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Disease Selection */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">질환 선택 ({selectedDiseases.length})</label>
                                        <div className="bg-slate-950 border border-slate-800 rounded-xl h-48 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                                            {diseases.map(d => (
                                                <label key={d.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-900 cursor-pointer transition-colors">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedDiseases.includes(d.id)}
                                                        onChange={(e) => {
                                                            if (e.target.checked) setSelectedDiseases([...selectedDiseases, d.id]);
                                                            else setSelectedDiseases(selectedDiseases.filter(id => id !== d.id));
                                                        }}
                                                        className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
                                                    />
                                                    <span className="text-sm text-slate-300">{d.disease_name}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors"
                                    >
                                        취소
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={submitting || !newSetName || (selectedTargets.length === 0 && selectedDiseases.length === 0)}
                                        className="flex-[2] bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
                                    >
                                        {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
                                        Seed Set 생성 완료
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #1e293b;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #334155;
                }
            `}</style>
        </div>
    );
}
