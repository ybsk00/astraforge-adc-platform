'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
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
    Loader2,
    Cable,
    Play,
    ChevronRight,
    Trash2
} from 'lucide-react';
import {
    getSeedTargets,
    getSeedDiseases,
    getSeedLinkers,
    getSeedPayloads,
    getSeedSets,
    createSeedSet
} from '@/lib/actions/admin';
import { clsx } from 'clsx';

type TabType = 'targets' | 'diseases' | 'linkers' | 'payloads' | 'sets';

export default function SeedManagementPage() {
    const t = useTranslations('Admin.seeds');
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<TabType>('targets');
    const [targets, setTargets] = useState<any[]>([]);
    const [diseases, setDiseases] = useState<any[]>([]);
    const [linkers, setLinkers] = useState<any[]>([]);
    const [payloads, setPayloads] = useState<any[]>([]);
    const [seedSets, setSeedSets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newSetName, setNewSetName] = useState('');
    const [selectedTargets, setSelectedTargets] = useState<any[]>([]);
    const [selectedDiseases, setSelectedDiseases] = useState<any[]>([]);
    const [selectedLinkers, setSelectedLinkers] = useState<any[]>([]);
    const [selectedPayloads, setSelectedPayloads] = useState<any[]>([]);
    const [modalSearch, setModalSearch] = useState({ targets: '', diseases: '', linkers: '', payloads: '' });
    const [submitting, setSubmitting] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [tData, dData, lData, pData, sData] = await Promise.all([
                getSeedTargets(),
                getSeedDiseases(),
                getSeedLinkers(),
                getSeedPayloads(),
                getSeedSets()
            ]);
            setTargets(tData);
            setDiseases(dData);
            setLinkers(lData);
            setPayloads(pData);
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
            await createSeedSet(
                newSetName,
                selectedTargets.map(t => t.id),
                selectedDiseases.map(d => d.id),
                selectedLinkers.map(l => l.id),
                selectedPayloads.map(p => p.id)
            );
            setIsModalOpen(false);
            setNewSetName('');
            setSelectedTargets([]);
            setSelectedDiseases([]);
            setSelectedLinkers([]);
            setSelectedPayloads([]);
            await fetchData();
        } catch (error) {
            console.error('Failed to create seed set:', error);
            alert(t('modal.error'));
        } finally {
            setSubmitting(false);
        }
    };

    const filteredData = () => {
        const query = searchQuery.toLowerCase();
        switch (activeTab) {
            case 'targets':
                return targets.filter(t => t.gene_symbol?.toLowerCase().includes(query) || t.ensembl_gene_id?.toLowerCase().includes(query));
            case 'diseases':
                return diseases.filter(d => d.disease_name?.toLowerCase().includes(query) || d.efo_id?.toLowerCase().includes(query));
            case 'linkers':
                return linkers.filter(l => l.name?.toLowerCase().includes(query));
            case 'payloads':
                return payloads.filter(p => p.drug_name?.toLowerCase().includes(query));
            case 'sets':
                return seedSets.filter(s => s.seed_set_name?.toLowerCase().includes(query));
            default:
                return [];
        }
    };

    const data = filteredData();

    // Modal filtering helper
    const getFilteredModalItems = (items: any[], query: string, key: string) => {
        return items.filter(item => (item[key] || '').toLowerCase().includes(query.toLowerCase()));
    };

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
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-blue-600/20"
                        >
                            <Plus className="w-4 h-4" />
                            {t('modal.title')}
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
                    <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 overflow-x-auto custom-scrollbar">
                        {(['targets', 'diseases', 'linkers', 'payloads', 'sets'] as TabType[]).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={clsx(
                                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                                    activeTab === tab ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                                )}
                            >
                                {tab === 'targets' && <Dna className="w-4 h-4" />}
                                {tab === 'diseases' && <Stethoscope className="w-4 h-4" />}
                                {tab === 'linkers' && <Cable className="w-4 h-4" />}
                                {tab === 'payloads' && <Pill className="w-4 h-4" />}
                                {tab === 'sets' && <Layers className="w-4 h-4" />}
                                {t(`tabs.${tab}`)}
                            </button>
                        ))}
                    </div>

                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder={t('modal.searchPlaceholder')}
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
                                                        {activeTab === 'targets' && <Dna className="w-4 h-4" />}
                                                        {activeTab === 'diseases' && <Stethoscope className="w-4 h-4" />}
                                                        {activeTab === 'linkers' && <Cable className="w-4 h-4" />}
                                                        {activeTab === 'payloads' && <Pill className="w-4 h-4" />}
                                                        {activeTab === 'sets' && <Layers className="w-4 h-4" />}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-white">
                                                            {activeTab === 'targets' ? item.gene_symbol :
                                                                activeTab === 'diseases' ? item.disease_name :
                                                                    activeTab === 'linkers' ? item.name :
                                                                        activeTab === 'payloads' ? item.drug_name :
                                                                            item.seed_set_name}
                                                        </div>
                                                        {activeTab === 'targets' && (
                                                            <div className="text-[10px] text-slate-500 uppercase">{item.full_name}</div>
                                                        )}
                                                        {activeTab === 'sets' && (
                                                            <div className="text-[10px] text-slate-500 flex gap-2 mt-0.5">
                                                                <span>T: {item.seed_set_targets?.length || 0}</span>
                                                                <span>D: {item.seed_set_diseases?.length || 0}</span>
                                                                <span>L: {item.seed_set_linkers?.length || 0}</span>
                                                                <span>P: {item.seed_set_payloads?.length || 0}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <code className="text-xs text-slate-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                                                    {activeTab === 'targets' ? item.ensembl_gene_id || 'N/A' :
                                                        activeTab === 'diseases' ? item.efo_id || 'N/A' :
                                                            activeTab === 'linkers' ? item.linker_type || 'N/A' :
                                                                activeTab === 'payloads' ? item.chembl_id || 'N/A' :
                                                                    item.id.split('-')[0]}
                                                </code>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={clsx(
                                                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium border",
                                                    "bg-green-500/10 text-green-400 border-green-500/20"
                                                )}>
                                                    <CheckCircle2 className="w-3 h-3" />
                                                    Resolved
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                {activeTab === 'sets' ? (
                                                    <button
                                                        onClick={() => router.push('/admin/runs')}
                                                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white text-xs font-medium rounded-lg transition-all border border-blue-600/20"
                                                    >
                                                        <Play className="w-3 h-3" />
                                                        설계 실행
                                                    </button>
                                                ) : (
                                                    <button className="text-slate-500 hover:text-white transition-colors">
                                                        <RefreshCw className="w-4 h-4" />
                                                    </button>
                                                )}
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
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200 flex flex-col">
                            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                                <div>
                                    <h2 className="text-xl font-bold text-white">{t('modal.title')}</h2>
                                    <p className="text-xs text-slate-500 mt-1">{t('modal.subtitle')}</p>
                                </div>
                                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
                                {/* Name Input */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">{t('modal.nameLabel')}</label>
                                    <input
                                        required
                                        type="text"
                                        value={newSetName}
                                        onChange={e => setNewSetName(e.target.value)}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all"
                                        placeholder={t('modal.namePlaceholder')}
                                    />
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* Target Selection */}
                                    <SelectionSection
                                        title={t('modal.selectTargets')}
                                        items={targets}
                                        selectedItems={selectedTargets}
                                        setSelectedItems={setSelectedTargets}
                                        searchQuery={modalSearch.targets}
                                        setSearchQuery={(q) => setModalSearch({ ...modalSearch, targets: q })}
                                        displayKey="gene_symbol"
                                        t={t}
                                    />

                                    {/* Disease Selection */}
                                    <SelectionSection
                                        title={t('modal.selectDiseases')}
                                        items={diseases}
                                        selectedItems={selectedDiseases}
                                        setSelectedItems={setSelectedDiseases}
                                        searchQuery={modalSearch.diseases}
                                        setSearchQuery={(q) => setModalSearch({ ...modalSearch, diseases: q })}
                                        displayKey="disease_name"
                                        t={t}
                                    />

                                    {/* Linker Selection */}
                                    <SelectionSection
                                        title={t('modal.selectLinkers')}
                                        items={linkers}
                                        selectedItems={selectedLinkers}
                                        setSelectedItems={setSelectedLinkers}
                                        searchQuery={modalSearch.linkers}
                                        setSearchQuery={(q) => setModalSearch({ ...modalSearch, linkers: q })}
                                        displayKey="name"
                                        t={t}
                                    />

                                    {/* Payload Selection */}
                                    <SelectionSection
                                        title={t('modal.selectPayloads')}
                                        items={payloads}
                                        selectedItems={selectedPayloads}
                                        setSelectedItems={setSelectedPayloads}
                                        searchQuery={modalSearch.payloads}
                                        setSearchQuery={(q) => setModalSearch({ ...modalSearch, payloads: q })}
                                        displayKey="drug_name"
                                        t={t}
                                    />
                                </div>
                            </div>

                            <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors"
                                >
                                    {t('modal.cancel')}
                                </button>
                                <button
                                    onClick={handleCreateSet}
                                    disabled={submitting || !newSetName || (selectedTargets.length === 0 && selectedDiseases.length === 0)}
                                    className="flex-[2] bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
                                >
                                    {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
                                    {t('modal.submit')}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                    height: 6px;
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

function SelectionSection({ title, items, selectedItems, setSelectedItems, searchQuery, setSearchQuery, displayKey, t }: any) {
    const filteredItems = useMemo(() =>
        items.filter((item: any) => (item[displayKey] || '').toLowerCase().includes(searchQuery.toLowerCase())),
        [items, searchQuery, displayKey]
    );

    const toggleItem = (item: any) => {
        if (selectedItems.some((si: any) => si.id === item.id)) {
            setSelectedItems(selectedItems.filter((si: any) => si.id !== item.id));
        } else {
            setSelectedItems([...selectedItems, item]);
        }
    };

    return (
        <div className="flex flex-col h-[350px]">
            <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-400">{title} ({selectedItems.length})</label>
                <div className="flex gap-2">
                    <button
                        onClick={() => setSelectedItems(items)}
                        className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
                    >
                        {t('modal.selectAll')}
                    </button>
                    <button
                        onClick={() => setSelectedItems([])}
                        className="text-[10px] text-slate-500 hover:text-slate-400 transition-colors"
                    >
                        {t('modal.deselectAll')}
                    </button>
                </div>
            </div>

            {/* Search in Modal Section */}
            <div className="relative mb-2">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-all"
                    placeholder={t('modal.searchPlaceholder')}
                />
            </div>

            {/* Selected Items Badges */}
            {selectedItems.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3 max-h-20 overflow-y-auto custom-scrollbar p-1">
                    {selectedItems.map((item: any) => (
                        <span key={item.id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-600/20 text-blue-400 text-[10px] font-medium rounded-md border border-blue-600/30">
                            {item[displayKey]}
                            <button onClick={() => toggleItem(item)} className="hover:text-white">
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                </div>
            )}

            {/* Items List */}
            <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl overflow-y-auto p-2 space-y-1 custom-scrollbar">
                {filteredItems.length > 0 ? (
                    filteredItems.map((item: any) => {
                        const isSelected = selectedItems.some((si: any) => si.id === item.id);
                        return (
                            <label
                                key={item.id}
                                className={clsx(
                                    "flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all border",
                                    isSelected ? "bg-blue-600/10 border-blue-600/30 text-blue-400" : "hover:bg-slate-900 border-transparent text-slate-400"
                                )}
                            >
                                <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => toggleItem(item)}
                                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
                                />
                                <span className="text-sm">{item[displayKey]}</span>
                                {isSelected && <CheckCircle2 className="w-3.5 h-3.5 ml-auto" />}
                            </label>
                        );
                    })
                ) : (
                    <div className="h-full flex items-center justify-center text-slate-600 text-xs italic">
                        No results found
                    </div>
                )}
            </div>
        </div>
    );
}
