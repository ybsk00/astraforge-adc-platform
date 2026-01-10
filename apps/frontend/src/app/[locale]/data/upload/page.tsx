'use client';

import { useState } from 'react';
import { Upload, FileText, AlertCircle } from 'lucide-react';

export default function DataUploadPage() {
    const [file, setFile] = useState<File | null>(null);
    const [type, setType] = useState('assay_results');
    const [uploading, setUploading] = useState(false);

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        // Simulate upload
        await new Promise(resolve => setTimeout(resolve, 2000));
        alert('업로드 완료! (Mock)');
        setUploading(false);
        setFile(null);
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">데이터 업로드</h1>
                    <p className="text-slate-400">실험 결과(assay) 또는 외부 파일을 업로드하여 시스템에 등록합니다.</p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <form onSubmit={handleUpload} className="space-y-6">
                        {/* Type Selection */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                업로드 타입
                            </label>
                            <select
                                value={type}
                                onChange={(e) => setType(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="assay_results">실험 결과 (Assay Results)</option>
                                <option value="protocol_outputs">프로토콜 출력 (Protocol Outputs)</option>
                                <option value="misc">기타 (Misc)</option>
                            </select>
                        </div>

                        {/* File Drop Area */}
                        <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors">
                            <input
                                type="file"
                                id="file-upload"
                                className="hidden"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                            />
                            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-4">
                                <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center">
                                    <Upload className="w-8 h-8 text-blue-500" />
                                </div>
                                <div>
                                    <p className="text-lg font-medium text-white mb-1">
                                        {file ? file.name : '파일을 선택하거나 이곳에 드래그하세요'}
                                    </p>
                                    <p className="text-sm text-slate-500">
                                        CSV, XLSX, JSON, PDF 지원 (최대 50MB)
                                    </p>
                                </div>
                            </label>
                        </div>

                        {/* Info Box */}
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex gap-3">
                            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
                            <div className="text-sm text-blue-200">
                                <p className="font-medium mb-1">안내</p>
                                <p>업로드된 파일은 백그라운드에서 파싱 및 검증 과정을 거칩니다. 처리 결과는 '업로드 내역'에서 확인할 수 있습니다.</p>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={!file || uploading}
                                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {uploading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        업로드 중...
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4" />
                                        업로드 시작
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
