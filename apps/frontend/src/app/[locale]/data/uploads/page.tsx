'use client';

import { useState, useEffect, useCallback } from 'react';
import { FileText, RefreshCw, ExternalLink, Loader2, Trash2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface UploadItem {
    id: string;
    type: string;
    filename: string;
    status: 'uploaded' | 'parsing' | 'parsed' | 'failed';
    size_bytes?: number;
    created_at: string;
    error_message?: string;
}

export default function UploadHistoryPage() {
    const { user } = useAuth();
    const [uploads, setUploads] = useState<UploadItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const fetchUploads = useCallback(async () => {
        if (!user?.id) return;

        setLoading(true);
        try {
            const response = await fetch(`${apiUrl}/api/v1/uploads?user_id=${user.id}`);
            if (response.ok) {
                const data = await response.json();
                setUploads(data);
                setError(null);
            } else {
                setError('Failed to fetch uploads');
            }
        } catch (err) {
            console.error('Failed to fetch uploads:', err);
            setError('Failed to connect to server');
        } finally {
            setLoading(false);
        }
    }, [user?.id, apiUrl]);

    useEffect(() => {
        fetchUploads();
    }, [fetchUploads]);

    const handleDelete = async (uploadId: string) => {
        if (!user?.id || !confirm('Are you sure you want to delete this upload?')) return;

        try {
            const response = await fetch(`${apiUrl}/api/v1/uploads/${uploadId}?user_id=${user.id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchUploads();
            } else {
                alert('Failed to delete upload');
            }
        } catch (err) {
            console.error('Delete failed:', err);
            alert('Error deleting upload');
        }
    };

    const formatSize = (bytes?: number) => {
        if (!bytes) return '-';
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'parsed': return 'bg-green-500/20 text-green-400';
            case 'parsing': return 'bg-blue-500/20 text-blue-400';
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
                    <button
                        onClick={fetchUploads}
                        disabled={loading}
                        className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
                        {error}
                    </div>
                )}

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
                            {loading && uploads.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                                        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                                        Loading uploads...
                                    </td>
                                </tr>
                            ) : uploads.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                                        업로드 내역이 없습니다.
                                    </td>
                                </tr>
                            ) : (
                                uploads.map((item) => (
                                    <tr key={item.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <FileText className="w-5 h-5 text-slate-500" />
                                                <span className="text-sm text-white font-medium">{item.filename}</span>
                                            </div>
                                            {item.error_message && (
                                                <div className="text-xs text-red-400 mt-1 pl-8">{item.error_message}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{item.type}</td>
                                        <td className="px-6 py-4 text-sm text-slate-500">{formatSize(item.size_bytes)}</td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                                                {item.status === 'parsing' && '● '}{item.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-500">
                                            {new Date(item.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <button className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                                                    상세 <ExternalLink className="w-3 h-3" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(item.id)}
                                                    className="text-slate-500 hover:text-red-400 transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
