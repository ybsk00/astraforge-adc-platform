'use client';

import { useState } from 'react';
import { Search, Filter, BookOpen, FileText, Plus, Loader2 } from 'lucide-react';

interface EvidenceItem {
    id: string;
    title: string;
    authors: string[];
    journal: string;
    year: number;
    abstract: string;
    relevance_score: number;
    type?: string; // Optional, as API might not return it yet
    polarity?: string; // Optional
}

export default function EvidenceSearchPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<EvidenceItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v1/evidence/search?q=${encodeURIComponent(query)}&limit=20`);

            if (response.ok) {
                const data = await response.json();
                setResults(data.results || []);
            } else {
                console.error('Search failed');
                setResults([]);
            }
        } catch (error) {
            console.error('Search error:', error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const getPolarityBadge = (polarity?: string) => {
        switch (polarity) {
            case 'positive': return 'bg-green-500/20 text-green-400';
            case 'negative': return 'bg-red-500/20 text-red-400';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">심층 문헌 검색</h1>
                    <p className="text-slate-400">PubMed 및 특허 데이터베이스에서 관련 문헌을 검색합니다.</p>
                </div>

                {/* Search Bar */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                    <form onSubmit={handleSearch} className="flex gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="키워드, 저자, 또는 DOI 검색..."
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                            검색
                        </button>
                    </form>

                    {/* Filters */}
                    <div className="flex items-center gap-4 mt-4">
                        <div className="flex items-center gap-2 text-slate-400 text-sm">
                            <Filter className="w-4 h-4" />
                            <span>필터:</span>
                        </div>
                        <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option>모든 연도</option>
                            <option>최근 1년</option>
                            <option>최근 5년</option>
                        </select>
                        <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option>모든 타입</option>
                            <option>논문 (Article)</option>
                            <option>리뷰 (Review)</option>
                            <option>임상시험 (Clinical Trial)</option>
                        </select>
                    </div>
                </div>

                {/* Results */}
                <div className="space-y-4">
                    {loading ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
                            <p className="text-slate-400">문헌을 검색하고 분석 중입니다...</p>
                        </div>
                    ) : searched && results.length === 0 ? (
                        <div className="text-center py-12 text-slate-400">
                            검색 결과가 없습니다.
                        </div>
                    ) : (
                        results.map((item) => (
                            <div key={item.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-3">
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPolarityBadge(item.polarity)} uppercase`}>
                                            {item.polarity || 'Neutral'}
                                        </span>
                                        <span className="text-slate-500 text-sm">{item.type || 'Article'}</span>
                                        <span className="text-blue-400 text-xs">Score: {(item.relevance_score * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors" title="인덱싱에 추가">
                                            <Plus className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2 hover:text-blue-400 cursor-pointer">
                                    {item.title}
                                </h3>
                                <div className="flex items-center gap-4 text-sm text-slate-400 mb-4">
                                    <span className="flex items-center gap-1">
                                        <BookOpen className="w-4 h-4" />
                                        {item.journal}
                                    </span>
                                    <span>{item.year}</span>
                                    <span>{item.authors.slice(0, 3).join(', ')}{item.authors.length > 3 ? ' et al.' : ''}</span>
                                </div>
                                <p className="text-slate-400 text-sm mb-4 line-clamp-2">
                                    {item.abstract}
                                </p>
                                <div className="flex gap-2">
                                    <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded border border-slate-700 transition-colors flex items-center gap-2">
                                        <FileText className="w-3 h-3" />
                                        원문 보기
                                    </button>
                                    <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded border border-slate-700 transition-colors">
                                        청킹 보기
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
