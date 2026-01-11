'use client';

import { useState, useEffect } from 'react';
import {
    X,
    ChevronRight,
    ChevronLeft,
    Layers,
    Cable,
    Settings2,
    CheckCircle2,
    Loader2,
    Database,
    Search,
    Info,
    Pill,
    RefreshCw
} from 'lucide-react';
import { getSeedSets } from '@/lib/actions/admin';
import { clsx } from 'clsx';

interface NewRunModalProps {
    onClose: () => void;
    onCreated: () => void;
}

export default function NewRunModal({ onClose, onCreated }: NewRunModalProps) {
    const [step, setStep] = useState(1);
    const [seedSets, setSeedSets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Form State
    const [selectedSeedSetId, setSelectedSeedSetId] = useState<string>('');
    const [selectedConnectors, setSelectedConnectors] = useState<string[]>(['pubmed', 'opentargets']);
    const [maxPages, setMaxPages] = useState(10);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const fetchSets = async () => {
            try {
                const data = await getSeedSets();
                setSeedSets(data);
                if (data.length > 0) setSelectedSeedSetId(data[0].id);
            } catch (error) {
                console.error('Failed to fetch seed sets:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSets();
    }, []);

    const handleNext = () => setStep(prev => Math.min(prev + 1, 4));
    const handleBack = () => setStep(prev => Math.max(prev - 1, 1));

    const handleSubmit = async () => {
        if (!selectedSeedSetId) return;

        setSubmitting(true);
        try {
            const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';
            const res = await fetch(`${ENGINE_URL}/api/v1/pipeline/run-seed-set`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    seed_set_id: selectedSeedSetId,
                    connector_names: selectedConnectors,
                    max_pages: maxPages
                })
            });

            if (res.ok) {
                alert('데이터 수집 파이프라인이 성공적으로 시작되었습니다.');
                onCreated();
            } else {
                const errorData = await res.json();
                throw new Error(errorData.detail || '실행 시작에 실패했습니다.');
            }
        } catch (error: any) {
            console.error('Failed to start run:', error);
            alert(`실행 시작에 실패했습니다: ${error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const steps = [
        { id: 1, name: 'Seed Set 선택', icon: Layers },
        { id: 2, name: '커넥터 설정', icon: Cable },
        { id: 3, name: '실행 옵션', icon: Settings2 },
        { id: 4, name: '최종 확인', icon: CheckCircle2 },
    ];

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/20">
                            <Database className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">데이터 수집 Wizard</h2>
                            <p className="text-xs text-slate-500 mt-0.5">도메인 최적화 자동 수집 파이프라인 실행</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Stepper */}
                <div className="px-8 py-6 bg-slate-950/30 border-b border-slate-800">
                    <div className="flex items-center justify-between relative">
                        {/* Progress Line */}
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-slate-800 -z-10" />
                        <div
                            className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-blue-600 transition-all duration-300 -z-10"
                            style={{ width: `${((step - 1) / (steps.length - 1)) * 100}%` }}
                        />

                        {steps.map((s) => (
                            <div key={s.id} className="flex flex-col items-center gap-2">
                                <div className={clsx(
                                    "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                                    step >= s.id ? "bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-600/20" : "bg-slate-900 border-slate-800 text-slate-500"
                                )}>
                                    <s.icon className="w-5 h-5" />
                                </div>
                                <span className={clsx(
                                    "text-[10px] font-bold uppercase tracking-wider transition-colors duration-300",
                                    step >= s.id ? "text-blue-400" : "text-slate-600"
                                )}>
                                    {s.name}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {step === 1 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="flex items-center gap-2 text-blue-400 mb-2">
                                <Info className="w-4 h-4" />
                                <span className="text-sm font-medium">수집 대상이 될 Seed Set을 선택하세요.</span>
                            </div>
                            <div className="grid grid-cols-1 gap-3">
                                {loading ? (
                                    <div className="py-12 text-center">
                                        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
                                    </div>
                                ) : seedSets.map((set) => (
                                    <button
                                        key={set.id}
                                        onClick={() => setSelectedSeedSetId(set.id)}
                                        className={clsx(
                                            "flex items-center justify-between p-4 rounded-xl border transition-all text-left group",
                                            selectedSeedSetId === set.id
                                                ? "bg-blue-600/10 border-blue-600 shadow-lg shadow-blue-600/5"
                                                : "bg-slate-800/50 border-slate-800 hover:border-slate-700"
                                        )}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={clsx(
                                                "w-12 h-12 rounded-lg flex items-center justify-center transition-colors",
                                                selectedSeedSetId === set.id ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 group-hover:text-slate-200"
                                            )}>
                                                <Layers className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <div className="text-white font-semibold">{set.seed_set_name}</div>
                                                <div className="text-xs text-slate-500 mt-1">
                                                    Targets: {set.seed_set_targets?.length || 0} | Diseases: {set.seed_set_diseases?.length || 0}
                                                </div>
                                            </div>
                                        </div>
                                        {selectedSeedSetId === set.id && (
                                            <CheckCircle2 className="w-6 h-6 text-blue-500" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="flex items-center gap-2 text-blue-400 mb-2">
                                <Info className="w-4 h-4" />
                                <span className="text-sm font-medium">활성화할 데이터 소스를 선택하세요.</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {[
                                    { id: 'pubmed', name: 'PubMed', desc: '의생명 과학 문헌 및 초록 수집', icon: Database },
                                    { id: 'opentargets', name: 'Open Targets', desc: '타겟-질환 연관성 및 증거 수집', icon: Cable },
                                    { id: 'chembl', name: 'ChEMBL', desc: '약물 및 생물학적 활성 데이터 (준비중)', icon: Pill, disabled: true },
                                ].map((conn) => (
                                    <button
                                        key={conn.id}
                                        disabled={conn.disabled}
                                        onClick={() => {
                                            if (selectedConnectors.includes(conn.id)) {
                                                setSelectedConnectors(selectedConnectors.filter(id => id !== conn.id));
                                            } else {
                                                setSelectedConnectors([...selectedConnectors, conn.id]);
                                            }
                                        }}
                                        className={clsx(
                                            "flex flex-col p-5 rounded-xl border transition-all text-left relative overflow-hidden group",
                                            conn.disabled ? "opacity-50 cursor-not-allowed border-slate-800 bg-slate-900/50" :
                                                selectedConnectors.includes(conn.id)
                                                    ? "bg-blue-600/10 border-blue-600 shadow-lg"
                                                    : "bg-slate-800/50 border-slate-800 hover:border-slate-700"
                                        )}
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <div className={clsx(
                                                "w-10 h-10 rounded-lg flex items-center justify-center transition-colors",
                                                selectedConnectors.includes(conn.id) ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400"
                                            )}>
                                                <conn.icon className="w-5 h-5" />
                                            </div>
                                            {!conn.disabled && selectedConnectors.includes(conn.id) && (
                                                <CheckCircle2 className="w-5 h-5 text-blue-500" />
                                            )}
                                        </div>
                                        <div className="text-white font-semibold">{conn.name}</div>
                                        <div className="text-xs text-slate-500 mt-1">{conn.desc}</div>
                                        {conn.disabled && (
                                            <div className="absolute top-2 right-2 bg-slate-800 text-[8px] px-1.5 py-0.5 rounded text-slate-500 uppercase font-bold">Coming Soon</div>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-4">최대 수집 페이지 수 (Max Pages)</label>
                                <div className="flex items-center gap-6">
                                    <input
                                        type="range"
                                        min="1"
                                        max="100"
                                        value={maxPages}
                                        onChange={(e) => setMaxPages(parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="w-16 h-10 bg-slate-800 border border-slate-700 rounded-lg flex items-center justify-center text-white font-bold">
                                        {maxPages}
                                    </div>
                                </div>
                                <p className="text-[10px] text-slate-500 mt-3 flex items-center gap-1">
                                    <Info className="w-3 h-3" />
                                    페이지당 약 20~50건의 레코드가 수집됩니다. 값이 클수록 시간이 오래 걸립니다.
                                </p>
                            </div>

                            <div className="p-4 bg-blue-600/5 border border-blue-600/20 rounded-xl">
                                <h4 className="text-sm font-semibold text-blue-400 mb-2 flex items-center gap-2">
                                    <RefreshCw className="w-4 h-4" />
                                    ID Resolver 자동 실행
                                </h4>
                                <p className="text-xs text-slate-400 leading-relaxed">
                                    수집 시작 전, Seed Set 내의 Gene Symbol과 질환명을 Open Targets API를 통해 Ensembl ID 및 EFO ID로 자동 정규화합니다.
                                </p>
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="bg-slate-800/50 border border-slate-800 rounded-2xl p-6 space-y-4">
                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                                    실행 요약
                                </h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Seed Set</div>
                                        <div className="text-sm text-white font-medium">
                                            {seedSets.find(s => s.id === selectedSeedSetId)?.seed_set_name || '선택되지 않음'}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Connectors</div>
                                        <div className="text-sm text-white font-medium">
                                            {selectedConnectors.join(', ').toUpperCase()}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Max Pages</div>
                                        <div className="text-sm text-white font-medium">{maxPages} pages</div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">ID Resolution</div>
                                        <div className="text-sm text-green-400 font-medium">Enabled (Auto)</div>
                                    </div>
                                </div>
                            </div>
                            <p className="text-center text-xs text-slate-500">
                                '수집 시작' 버튼을 클릭하면 백엔드 파이프라인이 즉시 가동됩니다.<br />
                                수집 결과는 '데이터 & 근거' 메뉴에서 실시간으로 확인할 수 있습니다.
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-between gap-4">
                    <button
                        onClick={step === 1 ? onClose : handleBack}
                        className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
                    >
                        {step === 1 ? '취소' : <><ChevronLeft className="w-4 h-4" /> 이전</>}
                    </button>

                    {step < 4 ? (
                        <button
                            onClick={handleNext}
                            disabled={step === 1 && !selectedSeedSetId || step === 2 && selectedConnectors.length === 0}
                            className="px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2"
                        >
                            다음 단계 <ChevronRight className="w-4 h-4" />
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={submitting}
                            className="px-10 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 text-white font-bold rounded-xl transition-all shadow-xl shadow-blue-600/20 flex items-center gap-2"
                        >
                            {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
                            수집 시작
                        </button>
                    )}
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
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
