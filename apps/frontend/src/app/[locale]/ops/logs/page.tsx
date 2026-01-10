'use client';

import { Terminal, Copy, ExternalLink } from 'lucide-react';

export default function OpsLogsPage() {
    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">시스템 로그</h1>
                    <p className="text-slate-400">애플리케이션 및 인프라의 런타임 로그를 조회합니다.</p>
                </div>

                {/* Log Viewer */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden font-mono text-sm">
                    <div className="px-4 py-2 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
                        <div className="flex gap-2">
                            <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">Service: All</span>
                            <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">Level: Error/Warn</span>
                        </div>
                        <button className="text-slate-400 hover:text-white transition-colors">
                            <Copy className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="p-4 space-y-2 h-[600px] overflow-y-auto">
                        <div className="flex gap-3 text-slate-300">
                            <span className="text-slate-500 shrink-0">2023-10-25 15:45:12</span>
                            <span className="text-green-400 shrink-0">[INFO]</span>
                            <span className="text-blue-400 shrink-0">[Worker]</span>
                            <span>Job design_run_execute started for run_id=853</span>
                        </div>
                        <div className="flex gap-3 text-slate-300">
                            <span className="text-slate-500 shrink-0">2023-10-25 15:45:15</span>
                            <span className="text-green-400 shrink-0">[INFO]</span>
                            <span className="text-blue-400 shrink-0">[Worker]</span>
                            <span>Loaded 120 targets from catalog</span>
                        </div>
                        <div className="flex gap-3 text-red-300 bg-red-500/10 p-1 rounded">
                            <span className="text-slate-500 shrink-0">2023-10-25 15:46:00</span>
                            <span className="text-red-400 shrink-0">[ERROR]</span>
                            <span className="text-blue-400 shrink-0">[API]</span>
                            <span>Failed to connect to PubMed API: Connection timed out</span>
                        </div>
                        <div className="flex gap-3 text-slate-300">
                            <span className="text-slate-500 shrink-0">2023-10-25 15:46:05</span>
                            <span className="text-yellow-400 shrink-0">[WARN]</span>
                            <span className="text-blue-400 shrink-0">[Worker]</span>
                            <span>Retrying operation (attempt 1/3)...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
