'use client';

import { useState, useEffect } from 'react';
import {
    CheckCircle2,
    ExternalLink,
    Search,
    AlertCircle,
    Loader2,
    Database,
    FileText
} from 'lucide-react';
import { clsx } from 'clsx';
import {
    getSeedLinkers,
    getSeedPayloads,
    updateEntityStructure,
    resolveLinkerStructure,
    resolvePayloadStructure
} from '@/lib/actions/admin';

interface ReviewItem {
    id: string;
    name?: string;
    drug_name?: string;
    structure_status: string;
    structure_source?: string;
    structure_confidence?: number;
    smiles?: string;
    inchi_key?: string;
    external_id?: string;
    synonyms?: string[];
}

export default function ReviewQueuePage() {
    const [activeTab, setActiveTab] = useState<'linkers' | 'payloads'>('linkers');
    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState<ReviewItem[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null);
    const [resolving, setResolving] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const data = activeTab === 'linkers' ? await getSeedLinkers() : await getSeedPayloads();
            // 검수가 필요한 항목(resolved, needs_review) 우선 표시
            setItems((data as ReviewItem[]).sort((a: ReviewItem, b: ReviewItem) => {
                if (a.structure_status === 'confirmed' && b.structure_status !== 'confirmed') return 1;
                if (a.structure_status !== 'confirmed' && b.structure_status === 'confirmed') return -1;
                return (b.structure_confidence || 0) - (a.structure_confidence || 0);
            }));
        } catch (error) {
            console.error('Failed to fetch review items:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    const handleApprove = async (item: ReviewItem) => {
        try {
            await updateEntityStructure(
                activeTab === 'linkers' ? 'linker' : 'payload',
                item.id,
                { structure_status: 'confirmed' }
            );
            await fetchData();
            setSelectedItem(null);
        } catch {
            alert('승인에 실패했습니다.');
        }
    };

    const handleResolve = async (item: ReviewItem) => {
        setResolving(item.id);
        try {
            if (activeTab === 'linkers') {
                await resolveLinkerStructure(item.id);
            } else {
                await resolvePayloadStructure(item.id);
            }
            await fetchData();
        } catch {
            alert('구조 조회에 실패했습니다.');
        } finally {
            setResolving(null);
        }
    };

    const filteredItems = items.filter(item =>
        (item.name || item.drug_name)?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-1">검수 큐 (Review Queue)</h1>
                    <p className="text-slate-400 text-sm">RAG 수집 및 API 조회 결과에 대한 데이터 품질 검수를 진행합니다.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* List Section */}
                    <div className="lg:col-span-1 space-y-4">
                        <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800">
                            <button
                                onClick={() => setActiveTab('linkers')}
                                className={clsx(
                                    "flex-1 py-2 rounded-lg text-sm font-medium transition-all",
                                    activeTab === 'linkers' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                                )}
                            >
                                Linkers
                            </button>
                            <button
                                onClick={() => setActiveTab('payloads')}
                                className={clsx(
                                    "flex-1 py-2 rounded-lg text-sm font-medium transition-all",
                                    activeTab === 'payloads' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-200"
                                )}
                            >
                                Payloads
                            </button>
                        </div>

                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="이름 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            />
                        </div>

                        <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto pr-2 custom-scrollbar">
                            {loading ? (
                                <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                                    <Loader2 className="w-8 h-8 animate-spin mb-2" />
                                    <p className="text-sm">데이터 로딩 중...</p>
                                </div>
                            ) : filteredItems.length === 0 ? (
                                <div className="text-center py-12 text-slate-500 text-sm">
                                    검수할 항목이 없습니다.
                                </div>
                            ) : (
                                filteredItems.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => setSelectedItem(item)}
                                        className={clsx(
                                            "w-full text-left p-4 rounded-xl border transition-all group",
                                            selectedItem?.id === item.id
                                                ? "bg-blue-600/10 border-blue-500/50"
                                                : "bg-slate-900 border-slate-800 hover:border-slate-700"
                                        )}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <span className="font-medium text-white truncate pr-2">
                                                {item.name || item.drug_name}
                                            </span>
                                            <div className={clsx(
                                                "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                                                item.structure_status === 'confirmed' ? "bg-emerald-500/20 text-emerald-400" :
                                                    item.structure_status === 'resolved' ? "bg-blue-500/20 text-blue-400" :
                                                        "bg-amber-500/20 text-amber-400"
                                            )}>
                                                {item.structure_status}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3 text-[11px] text-slate-500">
                                            <div className="flex items-center gap-1">
                                                <Database className="w-3 h-3" />
                                                {item.structure_source || 'N/A'}
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <AlertCircle className="w-3 h-3" />
                                                Score: {item.structure_confidence || 0}
                                            </div>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Detail Section */}
                    <div className="lg:col-span-2">
                        {selectedItem ? (
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 lg:p-8 sticky top-8">
                                <div className="flex items-start justify-between mb-8">
                                    <div>
                                        <h2 className="text-2xl font-bold text-white mb-2">
                                            {selectedItem.name || selectedItem.drug_name}
                                        </h2>
                                        <div className="flex flex-wrap gap-2">
                                            {selectedItem.synonyms?.map((s: string, i: number) => (
                                                <span key={i} className="px-2 py-1 bg-slate-800 text-slate-400 text-xs rounded-md">
                                                    {s}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleResolve(selectedItem)}
                                            disabled={resolving === selectedItem.id}
                                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors disabled:opacity-50"
                                        >
                                            <Loader2 className={clsx("w-4 h-4", resolving === selectedItem.id && "animate-spin")} />
                                            구조 재조회
                                        </button>
                                        <button
                                            onClick={() => handleApprove(selectedItem)}
                                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                                        >
                                            <CheckCircle2 className="w-4 h-4" />
                                            최종 승인
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* Structure Info */}
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">화학 구조 정보</h3>
                                            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 space-y-4">
                                                <div>
                                                    <label className="text-[10px] text-slate-500 uppercase font-bold block mb-1">SMILES</label>
                                                    <code className="text-xs text-blue-400 break-all bg-blue-500/5 p-2 rounded block border border-blue-500/10">
                                                        {selectedItem.smiles || '정보 없음'}
                                                    </code>
                                                </div>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="text-[10px] text-slate-500 uppercase font-bold block mb-1">InChIKey</label>
                                                        <span className="text-xs text-slate-300 font-mono">{selectedItem.inchi_key || 'N/A'}</span>
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] text-slate-500 uppercase font-bold block mb-1">External ID</label>
                                                        <span className="text-xs text-slate-300 font-mono">{selectedItem.external_id || 'N/A'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">신뢰도 분석</h3>
                                            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800">
                                                <div className="flex items-center justify-between mb-4">
                                                    <span className="text-sm text-slate-300">종합 신뢰도 점수</span>
                                                    <span className={clsx(
                                                        "text-lg font-bold",
                                                        (selectedItem.structure_confidence || 0) >= 80 ? "text-emerald-400" :
                                                            (selectedItem.structure_confidence || 0) >= 50 ? "text-blue-400" :
                                                                "text-amber-400"
                                                    )}>
                                                        {selectedItem.structure_confidence || 0}%
                                                    </span>
                                                </div>
                                                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                                    <div
                                                        className={clsx(
                                                            "h-full transition-all duration-500",
                                                            selectedItem.structure_confidence >= 80 ? "bg-emerald-500" :
                                                                selectedItem.structure_confidence >= 50 ? "bg-blue-500" :
                                                                    "bg-amber-500"
                                                        )}
                                                        style={{ width: `${selectedItem.structure_confidence || 0}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Evidence Section (Placeholder for now) */}
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">수집된 근거 (Evidence)</h3>
                                            <div className="space-y-3">
                                                <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 flex items-start gap-3">
                                                    <FileText className="w-5 h-5 text-slate-500 mt-1" />
                                                    <div>
                                                        <p className="text-xs text-slate-300 leading-relaxed mb-2">
                                                            The linker-payload combination of {selectedItem.name || selectedItem.drug_name} showed significant stability in human plasma...
                                                        </p>
                                                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                                                            <span className="bg-slate-800 px-1.5 py-0.5 rounded">PubMed</span>
                                                            <span>PMID: 34567890</span>
                                                            <ExternalLink className="w-2 h-2" />
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="text-center py-4">
                                                    <button className="text-xs text-blue-400 hover:text-blue-300 font-medium">
                                                        모든 근거 보기 (5개)
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center bg-slate-900/50 border border-slate-800 border-dashed rounded-2xl p-12 text-slate-500">
                                <div className="w-16 h-16 bg-slate-900 rounded-full flex items-center justify-center mb-4">
                                    <CheckCircle2 className="w-8 h-8 opacity-20" />
                                </div>
                                <h3 className="text-lg font-medium text-white mb-2">검수 항목을 선택하세요</h3>
                                <p className="text-sm text-center max-w-xs">
                                    왼쪽 리스트에서 검수가 필요한 링커 또는 페이로드를 선택하여 상세 정보를 확인하고 승인할 수 있습니다.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
