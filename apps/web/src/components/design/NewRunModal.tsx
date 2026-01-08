"use client";

/**
 * 새 실행 생성 모달
 */
import { useState, useEffect } from "react";

interface Target {
    id: string;
    name: string;
    gene_symbol: string;
}

interface NewRunModalProps {
    onClose: () => void;
    onCreated: () => void;
}

export default function NewRunModal({ onClose, onCreated }: NewRunModalProps) {
    const [targets, setTargets] = useState<Target[]>([]);
    const [selectedTargets, setSelectedTargets] = useState<string[]>([]);
    const [indication, setIndication] = useState("");
    const [strategy, setStrategy] = useState("balanced");
    const [loading, setLoading] = useState(false);
    const [loadingTargets, setLoadingTargets] = useState(true);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    useEffect(() => {
        fetchTargets();
    }, []);

    const fetchTargets = async () => {
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/catalog/components?type=target&status=active&limit=100`);
            if (res.ok) {
                const data = await res.json();
                setTargets(data.items || []);
            }
        } catch (error) {
            console.error("Failed to fetch targets:", error);
        } finally {
            setLoadingTargets(false);
        }
    };

    const handleTargetToggle = (id: string) => {
        setSelectedTargets((prev) =>
            prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (selectedTargets.length === 0) {
            alert("타겟을 선택해주세요.");
            return;
        }

        if (!indication.trim()) {
            alert("적응증을 입력해주세요.");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/runs`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_ids: selectedTargets,
                    indication,
                    strategy,
                }),
            });

            if (res.ok) {
                onCreated();
            } else {
                const error = await res.json();
                alert(`실행 생성 실패: ${error.detail || "Unknown error"}`);
            }
        } catch (error) {
            console.error("Failed to create run:", error);
            alert("실행 생성 실패");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
                    <h2 className="text-xl font-semibold">새 Design Run</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white p-1"
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                    {/* Indication */}
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            적응증 <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={indication}
                            onChange={(e) => setIndication(e.target.value)}
                            placeholder="예: HER2+ Breast Cancer"
                            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Strategy */}
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            전략
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            {[
                                { id: "balanced", label: "균형", desc: "4축 균형 최적화" },
                                { id: "penetration", label: "침투", desc: "종양 침투 우선" },
                                { id: "stability", label: "안정성", desc: "혈장 안정성 우선" },
                                { id: "cmc", label: "CMC", desc: "제조 적합성 우선" },
                            ].map((opt) => (
                                <button
                                    key={opt.id}
                                    type="button"
                                    onClick={() => setStrategy(opt.id)}
                                    className={`p-3 rounded-lg border text-left transition-all ${strategy === opt.id
                                            ? "border-blue-500 bg-blue-500/10"
                                            : "border-gray-600 hover:border-gray-500"
                                        }`}
                                >
                                    <div className="font-medium">{opt.label}</div>
                                    <div className="text-xs text-gray-400">{opt.desc}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Targets */}
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            타겟 선택 <span className="text-red-400">*</span>
                            <span className="text-gray-400 font-normal ml-2">
                                ({selectedTargets.length}개 선택됨)
                            </span>
                        </label>
                        {loadingTargets ? (
                            <div className="text-center py-4 text-gray-400">로딩 중...</div>
                        ) : targets.length === 0 ? (
                            <div className="text-center py-4 text-gray-400">
                                등록된 타겟이 없습니다. 먼저 카탈로그에 타겟을 추가해주세요.
                            </div>
                        ) : (
                            <div className="max-h-48 overflow-y-auto bg-gray-700 rounded-lg p-2 space-y-1">
                                {targets.map((target) => (
                                    <label
                                        key={target.id}
                                        className={`flex items-center p-2 rounded cursor-pointer transition-all ${selectedTargets.includes(target.id)
                                                ? "bg-blue-500/20"
                                                : "hover:bg-gray-600"
                                            }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedTargets.includes(target.id)}
                                            onChange={() => handleTargetToggle(target.id)}
                                            className="mr-3 accent-blue-500"
                                        />
                                        <span className="font-medium">{target.name}</span>
                                        <span className="text-sm text-gray-400 ml-2">
                                            ({target.gene_symbol})
                                        </span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </form>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-700 flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-all"
                    >
                        취소
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={loading || selectedTargets.length === 0 || !indication.trim()}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "생성 중..." : "실행 시작"}
                    </button>
                </div>
            </div>
        </div>
    );
}
