"use client";

import { useState, useTransition } from "react";
import { Play, Loader2, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

interface PipelinePanelProps {
    onStepComplete?: () => void;
}

interface StepStatus {
    step1: 'idle' | 'running' | 'success' | 'error';
    step2: 'idle' | 'running' | 'success' | 'error';
    step3: 'idle' | 'running' | 'success' | 'error';
    step4: 'idle' | 'running' | 'success' | 'error';
}

interface StepResult {
    step: number;
    message: string;
    type: 'success' | 'error';
}

export default function PipelinePanel({ onStepComplete }: PipelinePanelProps) {
    const [isPending, startTransition] = useTransition();
    const [stepStatus, setStepStatus] = useState<StepStatus>({
        step1: 'idle', step2: 'idle', step3: 'idle', step4: 'idle'
    });
    const [result, setResult] = useState<StepResult | null>(null);

    // Step 1 Modal State
    const [showStep1Modal, setShowStep1Modal] = useState(false);
    const [cancerType, setCancerType] = useState("breast cancer");
    const [targets, setTargets] = useState("HER2, TROP2");
    const [limit, setLimit] = useState(50);

    const runStep = async (step: number) => {
        const stepKey = `step${step}` as keyof StepStatus;
        setStepStatus(prev => ({ ...prev, [stepKey]: 'running' }));
        setResult(null);

        startTransition(async () => {
            try {
                let response;

                switch (step) {
                    case 1:
                        response = await fetch('/api/admin/golden/run-candidates', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                cancerType,
                                targets: targets.split(',').map(t => t.trim()),
                                limit
                            }),
                        });
                        break;
                    case 2:
                        response = await fetch('/api/admin/golden/run-enrich-components', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({}),
                        });
                        break;
                    case 3:
                        response = await fetch('/api/admin/golden/run-enrich-chemistry', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({}),
                        });
                        break;
                    case 4:
                        response = await fetch('/api/admin/golden/promote', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({}),
                        });
                        break;
                }

                if (!response?.ok) {
                    const error = await response?.json();
                    throw new Error(error?.error || `Step ${step} failed`);
                }

                const data = await response?.json();
                setStepStatus(prev => ({ ...prev, [stepKey]: 'success' }));
                setResult({
                    step,
                    message: data.message || `Step ${step} 완료`,
                    type: 'success'
                });

                if (step === 1) setShowStep1Modal(false);
                onStepComplete?.();

            } catch (error: unknown) {
                setStepStatus(prev => ({ ...prev, [stepKey]: 'error' }));
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                setResult({
                    step,
                    message: errorMessage,
                    type: 'error'
                });
            }
        });
    };

    const getStepIcon = (status: 'idle' | 'running' | 'success' | 'error') => {
        switch (status) {
            case 'running': return <Loader2 className="w-4 h-4 animate-spin" />;
            case 'success': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
            default: return <Play className="w-4 h-4" />;
        }
    };

    const getStepStyle = (status: 'idle' | 'running' | 'success' | 'error') => {
        switch (status) {
            case 'running': return "bg-blue-600 text-white";
            case 'success': return "bg-green-900/50 text-green-400 border-green-700";
            case 'error': return "bg-red-900/50 text-red-400 border-red-700";
            default: return "bg-slate-800 text-slate-300 hover:bg-slate-700";
        }
    };

    return (
        <>
            {/* Pipeline Steps */}
            <div className="flex items-center gap-2 p-3 bg-slate-900/50 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-500 mr-2">Pipeline:</span>

                {/* Step 1 */}
                <button
                    onClick={() => setShowStep1Modal(true)}
                    disabled={isPending}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${getStepStyle(stepStatus.step1)}`}
                >
                    {getStepIcon(stepStatus.step1)}
                    1. 후보 수집
                </button>

                <ArrowRight className="w-4 h-4 text-slate-600" />

                {/* Step 2 */}
                <button
                    onClick={() => runStep(2)}
                    disabled={isPending}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${getStepStyle(stepStatus.step2)}`}
                >
                    {getStepIcon(stepStatus.step2)}
                    2. 구성요소
                </button>

                <ArrowRight className="w-4 h-4 text-slate-600" />

                {/* Step 3 */}
                <button
                    onClick={() => runStep(3)}
                    disabled={isPending}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${getStepStyle(stepStatus.step3)}`}
                >
                    {getStepIcon(stepStatus.step3)}
                    3. 화학정보
                </button>

                <ArrowRight className="w-4 h-4 text-slate-600" />

                {/* Step 4 */}
                <button
                    onClick={() => runStep(4)}
                    disabled={isPending}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${getStepStyle(stepStatus.step4)}`}
                >
                    {getStepIcon(stepStatus.step4)}
                    4. 승격
                </button>
            </div>

            {/* Result Message */}
            {result && (
                <div className={`mt-2 p-2 rounded-lg text-sm flex items-center gap-2 ${result.type === 'success'
                    ? 'bg-green-900/30 text-green-400 border border-green-800'
                    : 'bg-red-900/30 text-red-400 border border-red-800'
                    }`}>
                    {result.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    Step {result.step}: {result.message}
                    <button onClick={() => setResult(null)} className="ml-auto hover:underline">닫기</button>
                </div>
            )}

            {/* Step 1 Modal */}
            {showStep1Modal && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                    <div className="bg-slate-900 rounded-xl border border-slate-700 p-6 w-full max-w-md shadow-2xl">
                        <h3 className="text-lg font-bold text-white mb-4">Step 1: 후보 수집 설정</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">암종 (Cancer Type)</label>
                                <input
                                    type="text"
                                    value={cancerType}
                                    onChange={(e) => setCancerType(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g., breast cancer"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">타겟 (쉼표로 구분)</label>
                                <input
                                    type="text"
                                    value={targets}
                                    onChange={(e) => setTargets(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g., HER2, TROP2, EGFR"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">최대 결과 수</label>
                                <input
                                    type="number"
                                    value={limit}
                                    onChange={(e) => setLimit(Number(e.target.value))}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    min={1}
                                    max={200}
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setShowStep1Modal(false)}
                                className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                            >
                                취소
                            </button>
                            <button
                                onClick={() => runStep(1)}
                                disabled={isPending || !cancerType.trim()}
                                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                {stepStatus.step1 === 'running' ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Play className="w-4 h-4" />
                                )}
                                실행
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
