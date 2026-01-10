'use client';

import { useState, useCallback, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X, Download } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface UploadItem {
    id: string;
    type: string;
    filename: string;
    status: 'uploaded' | 'parsing' | 'parsed' | 'failed';
    created_at: string;
    error_message?: string;
}

export default function DataUploadPage() {
    const t = useTranslations('DataUpload');
    const { user } = useAuth();
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [uploads, setUploads] = useState<UploadItem[]>([]);
    const [loadingUploads, setLoadingUploads] = useState(true);

    const apiUrl = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    const getStatusConfig = (status: string) => {
        switch (status) {
            case 'uploaded':
                return { label: t('status.uploaded'), class: 'bg-blue-500/20 text-blue-400', icon: FileText };
            case 'parsing':
                return { label: t('status.parsing'), class: 'bg-yellow-500/20 text-yellow-400', icon: Loader2 };
            case 'parsed':
                return { label: t('status.parsed'), class: 'bg-green-500/20 text-green-400', icon: CheckCircle };
            case 'failed':
                return { label: t('status.failed'), class: 'bg-red-500/20 text-red-400', icon: AlertCircle };
            default:
                return { label: status, class: 'bg-slate-500/20 text-slate-400', icon: FileText };
        }
    };

    // Upload list fetch
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

    // Polling for status updates
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
                setError('CSV files only');
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
            // 1. Presign request
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
                throw new Error('Upload preparation failed');
            }

            const presignData = await presignResponse.json();
            setUploadProgress(30);

            // 2. File upload (Supabase Storage)
            const uploadResponse = await fetch(presignData.presigned_url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'text/csv',
                },
                body: file
            });

            if (!uploadResponse.ok) {
                throw new Error('File upload failed');
            }

            setUploadProgress(70);

            // 3. Commit request
            const commitResponse = await fetch(`${apiUrl}/api/v1/uploads/commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: presignData.upload_id,
                    user_id: user.id
                })
            });

            if (!commitResponse.ok) {
                throw new Error('Upload commit failed');
            }

            setUploadProgress(100);
            setSuccess(t('uploadComplete'));
            setFile(null);

            // Refresh upload list
            setTimeout(fetchUploads, 1000);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload error occurred');
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (uploadId: string) => {
        if (!user?.id || !confirm('Delete this upload?')) return;

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
                        {t('title')}
                    </h1>
                    <p className="text-slate-400">
                        {t('subtitle')}
                    </p>
                </div>

                {/* Upload Zone */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-8 mb-8">
                    <div className="flex flex-col items-center">
                        <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mb-4">
                            <Upload className="w-8 h-8 text-blue-400" />
                        </div>

                        <h3 className="text-lg font-medium text-white mb-2">
                            {t('csvUpload')}
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 text-center">
                            {t('subtitle')}<br />
                            <span className="text-slate-500">({t('requiredColumns')}: name)</span>
                        </p>

                        {/* File Input */}
                        <div className="flex items-center gap-4 mb-4">
                            <label className="cursor-pointer bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors">
                                {t('selectFile')}
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
                                    {t('uploading')}
                                </>
                            ) : (
                                <>
                                    <Upload className="w-4 h-4" />
                                    {t('upload')}
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
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-white">{t('csvFormatGuide')}</h3>
                        <a
                            href="/samples/sample_candidates.csv"
                            download="sample_candidates.csv"
                            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
                        >
                            <Download className="w-4 h-4" />
                            {t('sampleDownload')}
                        </a>
                    </div>
                    <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-x-auto">
                        <div>name,DAR,LogP,AggRisk</div>
                        <div>Candidate A,4.0,2.5,0.3</div>
                        <div>Candidate B,6.0,3.2,0.5</div>
                    </div>
                    <p className="text-slate-400 text-sm mt-3">
                        <strong className="text-slate-300">{t('requiredColumns')}:</strong> name<br />
                        <strong className="text-slate-300">{t('optionalColumns')}:</strong> DAR, LogP, AggRisk, H_patch, CLV, INT
                    </p>
                </div>

                {/* Upload History */}
                <div className="bg-slate-800/30 border border-slate-700 rounded-xl">
                    <div className="px-6 py-4 border-b border-slate-700">
                        <h3 className="text-lg font-medium text-white">{t('uploadHistory')}</h3>
                    </div>

                    {loadingUploads ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                        </div>
                    ) : uploads.length === 0 ? (
                        <div className="text-center py-12 text-slate-400">
                            {t('noHistory')}
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-700">
                            {uploads.map((upload) => {
                                const config = getStatusConfig(upload.status);
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
