'use client';

import { useState, useCallback, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X, Download } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';

interface UploadItem {
    id: string;
    type: string;
    filename: string;
    status: 'uploaded' | 'parsing' | 'parsed' | 'failed';
    created_at: string;
    error_message?: string;
}

const STATUS_CONFIG = {
    uploaded: { label: '업로드됨', class: 'bg-blue-500/20 text-blue-400', icon: FileText },
    parsing: { label: '파싱 중', class: 'bg-yellow-500/20 text-yellow-400', icon: Loader2 },
    parsed: { label: '완료', class: 'bg-green-500/20 text-green-400', icon: CheckCircle },
    failed: { label: '실패', class: 'bg-red-500/20 text-red-400', icon: AlertCircle },
};

export default function DataUploadPage() {
    const t = useTranslations('Common');
    const { user } = useAuth();
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [uploads, setUploads] = useState<UploadItem[]>([]);
    const [loadingUploads, setLoadingUploads] = useState(true);

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    // 업로드 목록 조회
    const fetchUploads = useCallback(async () => {
        if (!user?.id) return;

        try {
            const response = await fetch(`${apiUrl}/api/v1/uploads?user_id=${user.id}`);
            if (response.ok) {
                const data = await response.json();
                setUploads(data);
            }
        } catch (err) {
            console.error('Failed to fetch uploads:', err);
        } finally {
            setLoadingUploads(false);
        }
    }, [user?.id, apiUrl]);

    useEffect(() => {
        fetchUploads();
    }, [fetchUploads]);

    // 폴링으로 상태 업데이트
    useEffect(() => {
        const hasProcessing = uploads.some(u => u.status === 'parsing');
        if (!hasProcessing) return;

        const interval = setInterval(fetchUploads, 3000);
        return () => clearInterval(interval);
    }, [uploads, fetchUploads]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            if (!selectedFile.name.endsWith('.csv')) {
                setError('CSV 파일만 업로드 가능합니다');
                return;
            }
            setFile(selectedFile);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file || !user?.id) return;

        setUploading(true);
        setError(null);
        setSuccess(null);
        setUploadProgress(0);

        try {
            // 1. Presign 요청
            setUploadProgress(10);
            const presignResponse = await fetch(`${apiUrl}/api/v1/uploads/presign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'candidate_csv',
                    filename: file.name,
                    mime_type: 'text/csv',
                    size_bytes: file.size,
                    user_id: user.id
                })
            });

            if (!presignResponse.ok) {
                throw new Error('업로드 준비 실패');
            }

            const presignData = await presignResponse.json();
            setUploadProgress(30);

            // 2. 파일 업로드 (Supabase Storage)
            const uploadResponse = await fetch(presignData.presigned_url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'text/csv',
                },
                body: file
            });

            if (!uploadResponse.ok) {
                throw new Error('파일 업로드 실패');
            }

            setUploadProgress(70);

            // 3. Commit 요청
            const commitResponse = await fetch(`${apiUrl}/api/v1/uploads/commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: presignData.upload_id,
                    user_id: user.id
                })
            });

            if (!commitResponse.ok) {
                throw new Error('업로드 완료 처리 실패');
            }

            setUploadProgress(100);
            setSuccess('업로드 완료! 데이터를 처리 중입니다...');
            setFile(null);

            // 업로드 목록 새로고침
            setTimeout(fetchUploads, 1000);

        } catch (err) {
            setError(err instanceof Error ? err.message : '업로드 중 오류가 발생했습니다');
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (uploadId: string) => {
        if (!user?.id || !confirm('이 업로드를 삭제하시겠습니까?')) return;

        try {
            const response = await fetch(`${apiUrl}/api/v1/uploads/${uploadId}?user_id=${user.id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchUploads();
            }
        } catch (err) {
            console.error('Delete failed:', err);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 ml-64 py-8 px-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        데이터 업로드
                    </h1>
                    <p className="text-slate-400">
                        CSV 파일을 업로드하여 후보 데이터를 등록합니다
                    </p>
                </div>

                {/* Upload Zone */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-8 mb-8">
                    <div className="flex flex-col items-center">
                        <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mb-4">
                            <Upload className="w-8 h-8 text-blue-400" />
                        </div>

                        <h3 className="text-lg font-medium text-white mb-2">
                            CSV 파일 업로드
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 text-center">
                            후보 데이터가 포함된 CSV 파일을 선택하세요<br />
                            <span className="text-slate-500">(필수 컬럼: name)</span>
                        </p>

                        {/* File Input */}
                        <div className="flex items-center gap-4 mb-4">
                            <label className="cursor-pointer bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors">
                                파일 선택
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    disabled={uploading}
                                />
                            </label>
                            {file && (
                                <div className="flex items-center gap-2 text-slate-300">
                                    <FileText className="w-4 h-4" />
                                    <span>{file.name}</span>
                                    <button
                                        onClick={() => setFile(null)}
                                        className="text-slate-500 hover:text-slate-300"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Upload Button */}
                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    업로드 중...
                                </>
                            ) : (
                                <>
                                    <Upload className="w-4 h-4" />
                                    업로드
                                </>
                            )}
                        </button>

                        {/* Progress Bar */}
                        {uploading && (
                            <div className="w-full max-w-md mt-4">
                                <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-blue-500 h-full transition-all duration-300"
                                        style={{ width: `${uploadProgress}%` }}
                                    />
                                </div>
                                <p className="text-slate-400 text-sm mt-1 text-center">
                                    {uploadProgress}%
                                </p>
                            </div>
                        )}

                        {/* Messages */}
                        {error && (
                            <div className="mt-4 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}
                        {success && (
                            <div className="mt-4 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 text-sm">
                                {success}
                            </div>
                        )}
                    </div>
                </div>

                {/* CSV Format Guide */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-6 mb-8">
                    <h3 className="text-lg font-medium text-white mb-4">CSV 형식 안내</h3>
                    <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-x-auto">
                        <div>name,DAR,LogP,AggRisk</div>
                        <div>Candidate A,4.0,2.5,0.3</div>
                        <div>Candidate B,6.0,3.2,0.5</div>
                    </div>
                    <p className="text-slate-400 text-sm mt-3">
                        <strong className="text-slate-300">필수 컬럼:</strong> name<br />
                        <strong className="text-slate-300">선택 컬럼:</strong> DAR, LogP, AggRisk, H_patch, CLV, INT
                    </p>
                </div>

                {/* Upload History */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl">
                    <div className="px-6 py-4 border-b border-slate-700">
                        <h3 className="text-lg font-medium text-white">업로드 내역</h3>
                    </div>

                    {loadingUploads ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                        </div>
                    ) : uploads.length === 0 ? (
                        <div className="text-center py-12 text-slate-400">
                            업로드 내역이 없습니다
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-700">
                            {uploads.map((upload) => {
                                const config = STATUS_CONFIG[upload.status];
                                const StatusIcon = config.icon;

                                return (
                                    <div key={upload.id} className="px-6 py-4 flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <FileText className="w-5 h-5 text-slate-400" />
                                            <div>
                                                <div className="text-white font-medium">{upload.filename}</div>
                                                <div className="text-slate-400 text-sm">
                                                    {new Date(upload.created_at).toLocaleString()}
                                                </div>
                                                {upload.error_message && (
                                                    <div className="text-red-400 text-sm mt-1">
                                                        {upload.error_message}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${config.class}`}>
                                                <StatusIcon className={`w-3 h-3 ${upload.status === 'parsing' ? 'animate-spin' : ''}`} />
                                                {config.label}
                                            </span>
                                            <button
                                                onClick={() => handleDelete(upload.id)}
                                                className="text-slate-500 hover:text-red-400 transition-colors"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
