'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    getGoldenSetById,
    updateCandidateReviewStatus,
    promoteGoldenSet,
    getGoldenCandidateEvidence,
    deleteGoldenSet
} from '@/lib/actions/golden-set';
import {
    ArrowLeft,
    CheckCircle2,
    XCircle,
    AlertCircle,
    Loader2,
    Search,
    Plus,
    Upload,
    Save,
    Trash2,
    ExternalLink,
    FileText,
    ShieldCheck
} from 'lucide-react';
import { clsx } from 'clsx';
import { createClient } from '@/lib/supabase/client';

export default function GoldenSetDetailPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const [setInfo, setSetInfo] = useState<any>(null);
    const [candidates, setCandidates] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [promoting, setPromoting] = useState(false);

    // Manual Upload State
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [newCandidate, setNewCandidate] = useState({
        target: '',
        antibody: '',
        linker: '',
        payload: '',
        disease: '',
        score: 0
    });

    // Search State
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    const fetchData = async () => {
        try {
            const data = await getGoldenSetById(params.id);
            setSetInfo(data);
            setCandidates(data.candidates);
        } catch (error) {
            console.error('Failed to fetch golden set:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [params.id]);

    const handlePromote = async () => {
        if (!confirm('이 골든 셋을 최종 승격하시겠습니까? 승격 시 시드 데이터로 활용됩니다.')) return;

        setPromoting(true);
        try {
            await promoteGoldenSet(params.id, `${setInfo.name}_v${setInfo.version}`);
            alert('성공적으로 승격되었습니다.');
            router.push('/admin/golden-sets');
        } catch (error) {
            console.error('Promotion failed:', error);
            alert('승격에 실패했습니다.');
        } finally {
            setPromoting(false);
        }
    };

    const handleManualUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        const supabase = createClient();

        try {
            const { error } = await supabase.from('golden_candidates').insert({
                golden_set_id: params.id,
                target: newCandidate.target,
                antibody: newCandidate.antibody,
                linker: newCandidate.linker,
                payload: newCandidate.payload,
                disease: newCandidate.disease,
                score: newCandidate.score || 0,
                review_status: 'approved',
                drug_name: `${newCandidate.antibody}-${newCandidate.linker}-${newCandidate.payload}`
            });

            if (error) throw error;

            setIsUploadModalOpen(false);
            setNewCandidate({ target: '', antibody: '', linker: '', payload: '', disease: '', score: 0 });
            fetchData();
        } catch (error) {
            console.error('Upload failed:', error);
            alert('업로드 실패');
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setSearching(true);
        const supabase = createClient();

        try {
            // Search in component_catalog
            const { data, error } = await supabase
                .from('component_catalog')
                .select('*')
                .ilike('name', `%${searchQuery}%`)
                .limit(20);

            if (error) throw error;
            setSearchResults(data || []);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setSearching(false);
        }
    };

    const handleAddFromSearch = async (item: any) => {
        const supabase = createClient();

        try {
            const candidateData = {
                golden_set_id: params.id,
                target: item.type === 'target' ? item.name : '',
                antibody: item.type === 'antibody' ? item.name : '',
                linker: item.type === 'linker' ? item.name : '',
                payload: item.type === 'payload' ? item.name : '',
                score: 0,
                review_status: 'approved',
                drug_name: item.name
            };

            const { error } = await supabase.from('golden_candidates').insert(candidateData);
            if (error) throw error;

            alert('추가되었습니다.');
            fetchData();
        } catch (error) {
            console.error('Add failed:', error);
            alert('추가 실패');
        }
    };

    const handleDelete = async () => {
        if (!confirm('정말로 이 골든 셋을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

        try {
            await deleteGoldenSet(params.id);
            alert('삭제되었습니다.');
            router.push('/admin/golden-sets');
        } catch (error) {
            console.error('Delete failed:', error);
            alert('삭제 실패');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (!setInfo) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400">
                <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
                <h2 className="text-xl font-bold text-white mb-2">골든 셋을 찾을 수 없습니다.</h2>
                <p>ID가 올바르지 않거나 삭제되었을 수 있습니다.</p>
                <button onClick={() => router.back()} className="mt-6 px-4 py-2 bg-slate-800 rounded-lg hover:bg-slate-700 text-white">
                    뒤로 가기
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={() => router.back()} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-2xl font-bold text-white">{setInfo.name}</h1>
                            <span className="px-2 py-0.5 text-xs font-medium bg-slate-800 text-slate-300 rounded border border-slate-700">
                                {setInfo.version}
                            </span>
                            {setInfo.status === 'promoted' && (
                                <span className="px-2 py-0.5 text-xs font-medium bg-green-900/30 text-green-400 rounded border border-green-800 flex items-center gap-1">
                                    <CheckCircle2 className="w-3 h-3" /> Promoted
                                </span>
                            )}
                        </div>
                        <p className="text-sm text-slate-400">
                            Created on {setInfo.created_at ? new Date(setInfo.created_at).toLocaleString() : 'Unknown'} • {candidates.length} Candidates
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleDelete}
                            className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors border border-red-500/20"
                        >
                            <Trash2 className="w-4 h-4" />
                            삭제
                        </button>
                        <button
                            onClick={() => setIsSearchModalOpen(true)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Search className="w-4 h-4" />
                            검색 추가
                        </button>
                        <button
                            onClick={() => setIsUploadModalOpen(true)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <Upload className="w-4 h-4" />
                            수동 업로드
                        </button>
                        {setInfo.status !== 'promoted' && (
                            <button
                                onClick={handlePromote}
                                disabled={promoting}
                                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-green-600/20"
                            >
                                {promoting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                                최종 승격
                            </button>
                        )}
                    </div>
                </div>

                {/* Candidates Table */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-950/50">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Drug Name</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Components</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Score</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {candidates.map((candidate) => (
                                    <tr key={candidate.id} className="hover:bg-slate-800/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-white">{candidate.drug_name}</div>
                                            <div className="text-xs text-slate-500">{candidate.id.split('-')[0]}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="space-y-1 text-xs">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500 w-16">Target:</span>
                                                    <span className="text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">{candidate.target || '-'}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500 w-16">Antibody:</span>
                                                    <span className="text-purple-400 bg-purple-400/10 px-1.5 py-0.5 rounded">{candidate.antibody || '-'}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500 w-16">Linker:</span>
                                                    <span className="text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">{candidate.linker || '-'}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500 w-16">Payload:</span>
                                                    <span className="text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">{candidate.payload || '-'}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-blue-500 rounded-full"
                                                        style={{ width: `${Math.min(candidate.score, 100)}%` }}
                                                    />
                                                </div>
                                                <span className="text-sm font-mono text-slate-300">{candidate.score}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={clsx(
                                                "px-2 py-1 text-xs font-medium rounded-full border",
                                                candidate.review_status === 'approved' ? "bg-green-500/10 text-green-400 border-green-500/20" :
                                                    candidate.review_status === 'rejected' ? "bg-red-500/10 text-red-400 border-red-500/20" :
                                                        "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                            )}>
                                                {candidate.review_status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Manual Upload Modal */}
                {isUploadModalOpen && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
                            <h2 className="text-xl font-bold text-white mb-6">수동 후보 등록</h2>
                            <form onSubmit={handleManualUpload} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Target</label>
                                        <input
                                            type="text"
                                            value={newCandidate.target}
                                            onChange={e => setNewCandidate({ ...newCandidate, target: e.target.value })}
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Antibody</label>
                                        <input
                                            type="text"
                                            value={newCandidate.antibody}
                                            onChange={e => setNewCandidate({ ...newCandidate, antibody: e.target.value })}
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Linker</label>
                                        <input
                                            type="text"
                                            value={newCandidate.linker}
                                            onChange={e => setNewCandidate({ ...newCandidate, linker: e.target.value })}
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Payload</label>
                                        <input
                                            type="text"
                                            value={newCandidate.payload}
                                            onChange={e => setNewCandidate({ ...newCandidate, payload: e.target.value })}
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Score (0-100)</label>
                                    <input
                                        type="number"
                                        value={newCandidate.score}
                                        onChange={e => setNewCandidate({ ...newCandidate, score: parseInt(e.target.value) })}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                    />
                                </div>

                                <div className="flex justify-end gap-3 mt-6">
                                    <button
                                        type="button"
                                        onClick={() => setIsUploadModalOpen(false)}
                                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
                                    >
                                        취소
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
                                    >
                                        등록
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Search Modal */}
                {isSearchModalOpen && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl h-[600px] flex flex-col">
                            <h2 className="text-xl font-bold text-white mb-4">카탈로그 검색 추가</h2>
                            <div className="flex gap-2 mb-4">
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                                    placeholder="Search components..."
                                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                                />
                                <button
                                    onClick={handleSearch}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
                                >
                                    <Search className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
                                {searching ? (
                                    <div className="text-center py-8 text-slate-500">Searching...</div>
                                ) : searchResults.length > 0 ? (
                                    searchResults.map(item => (
                                        <div key={item.id} className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg hover:border-slate-700">
                                            <div>
                                                <div className="font-medium text-white">{item.name}</div>
                                                <div className="text-xs text-slate-500 uppercase">{item.type}</div>
                                            </div>
                                            <button
                                                onClick={() => handleAddFromSearch(item)}
                                                className="p-2 hover:bg-blue-600/20 text-blue-400 rounded-lg transition-colors"
                                            >
                                                <Plus className="w-4 h-4" />
                                            </button>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-slate-500">No results found</div>
                                )}
                            </div>

                            <div className="flex justify-end mt-4 pt-4 border-t border-slate-800">
                                <button
                                    onClick={() => setIsSearchModalOpen(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
                                >
                                    닫기
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
