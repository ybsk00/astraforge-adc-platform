"use client";

import { useState, useEffect, useTransition, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    ArrowLeft, Save, Loader2, CheckCircle2, AlertCircle,
    Lock, Unlock, CheckSquare, Square, Trophy
} from "lucide-react";
import { getManualSeedById, updateManualSeed, promoteToFinal } from "@/lib/actions/golden-set";

interface ManualSeed {
    id: string;
    drug_name_canonical: string;
    aliases?: string;
    portfolio_group?: string;
    target: string;
    resolved_target_symbol?: string;
    antibody?: string;
    linker_family?: string;
    linker_trigger?: string;
    payload_family?: string;
    payload_exact_name?: string;
    payload_smiles_raw?: string;
    payload_smiles_standardized?: string;
    proxy_smiles_flag: boolean;
    proxy_reference?: string;
    clinical_phase?: string;
    program_status?: string;
    clinical_nct_id_primary?: string;
    outcome_label?: string;
    key_risk_category?: string;
    key_risk_signal?: string;
    primary_source_type?: string;
    primary_source_id?: string;
    evidence_refs: any[];
    gate_status: string;
    is_final: boolean;
    is_manually_verified: boolean;
    rdkit_mw?: number;
}

export default function ManualSeedDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const resolvedParams = use(params);
    const router = useRouter();
    const [seed, setSeed] = useState<ManualSeed | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [promoting, setPromoting] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [formData, setFormData] = useState<Partial<ManualSeed>>({});

    useEffect(() => {
        fetchSeed();
    }, [resolvedParams.id]);

    const fetchSeed = async () => {
        setLoading(true);
        try {
            const data = await getManualSeedById(resolvedParams.id);
            if (data) {
                setSeed(data);
                setFormData(data);
            }
        } catch (error) {
            console.error("Failed to fetch seed:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!seed) return;
        setSaving(true);
        setMessage(null);

        try {
            await updateManualSeed(seed.id, formData);
            setMessage({ type: "success", text: "저장되었습니다" });
            await fetchSeed(); // Refresh
        } catch (error: any) {
            setMessage({ type: "error", text: error.message || "저장 실패" });
        } finally {
            setSaving(false);
        }
    };

    const handlePromote = async () => {
        if (!seed) return;
        setPromoting(true);
        setMessage(null);

        try {
            await promoteToFinal(seed.id);
            setMessage({ type: "success", text: "✓ Final로 승격되었습니다!" });
            await fetchSeed(); // Refresh
        } catch (error: any) {
            setMessage({ type: "error", text: error.message || "승격 실패" });
        } finally {
            setPromoting(false);
        }
    };

    const updateField = (field: keyof ManualSeed, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    // Gate Checklist Conditions (Option C: NCT Optional)
    const gateChecks = seed ? {
        targetResolved: !!formData.resolved_target_symbol && formData.resolved_target_symbol !== '',
        smilesReady: !!formData.payload_smiles_standardized || formData.proxy_smiles_flag === true,
        evidenceExists: Array.isArray(formData.evidence_refs) && formData.evidence_refs.length >= 1,
        // Optional fields
        nctSelected: !!formData.clinical_nct_id_primary,
        rdkitComputed: seed.rdkit_mw !== null && seed.rdkit_mw !== undefined,
    } : { targetResolved: false, smilesReady: false, evidenceExists: false, nctSelected: false, rdkitComputed: false };

    // Option C: Only 3 required gates (NCT is optional)
    const requiredChecks = [gateChecks.targetResolved, gateChecks.smilesReady, gateChecks.evidenceExists];
    const passedCount = requiredChecks.filter(Boolean).length;
    const canPromote = requiredChecks.every(Boolean) && !seed?.is_final;

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
            </div>
        );
    }

    if (!seed) {
        return (
            <div className="min-h-screen bg-slate-950 p-8">
                <div className="text-center text-slate-400">Seed를 찾을 수 없습니다</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-6">
                    <Link href="/admin/golden-sets" className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5 text-slate-400" />
                    </Link>
                    <div className="flex-1">
                        <h1 className="text-2xl font-bold text-white">{seed.drug_name_canonical}</h1>
                        <p className="text-sm text-slate-400">Manual Seed 상세 편집</p>
                    </div>
                    <div className="flex items-center gap-2">
                        {seed.is_final && (
                            <span className="px-3 py-1 bg-green-900/30 text-green-400 rounded-lg text-sm flex items-center gap-1">
                                <CheckCircle2 className="w-4 h-4" /> Final
                            </span>
                        )}
                        {seed.is_manually_verified && (
                            <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 rounded-lg text-sm flex items-center gap-1">
                                <Lock className="w-4 h-4" /> Verified
                            </span>
                        )}
                    </div>
                </div>

                {/* Message */}
                {message && (
                    <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${message.type === "success"
                        ? "bg-green-900/30 text-green-400 border border-green-800"
                        : "bg-red-900/30 text-red-400 border border-red-800"
                        }`}>
                        {message.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        {message.text}
                    </div>
                )}

                {/* Gate Checklist Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                    <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Trophy className="w-5 h-5 text-yellow-500" />
                        Gate Checklist ({passedCount}/{requiredChecks.length})
                        <span className="text-xs text-slate-500 font-normal">(Option C: NCT Optional)</span>
                    </h2>
                    {/* Required Gates */}
                    <div className="grid grid-cols-3 gap-3 mb-4">
                        {[
                            { key: 'targetResolved', label: 'Target Resolved', desc: 'resolved_target_symbol' },
                            { key: 'smilesReady', label: 'SMILES Ready', desc: 'SMILES 또는 Proxy Flag' },
                            { key: 'evidenceExists', label: 'Evidence ≥ 1', desc: 'evidence_refs' },
                        ].map(({ key, label, desc }) => (
                            <div key={key} className={`flex items-center gap-3 p-3 rounded-lg ${gateChecks[key as keyof typeof gateChecks]
                                ? 'bg-green-900/20 border border-green-800'
                                : 'bg-slate-800/50 border border-slate-700'
                                }`}>
                                {gateChecks[key as keyof typeof gateChecks]
                                    ? <CheckSquare className="w-5 h-5 text-green-400" />
                                    : <Square className="w-5 h-5 text-slate-500" />}
                                <div>
                                    <div className="text-sm font-medium text-white">{label}</div>
                                    <div className="text-xs text-slate-500">{desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                    {/* Optional Fields */}
                    <div className="text-xs text-slate-500 mb-2">임상 추적용 (옵션)</div>
                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { key: 'nctSelected', label: 'Primary NCT', desc: '임상 동기화용', optional: true },
                            { key: 'rdkitComputed', label: 'RDKit', desc: 'MW/LogP 등', optional: true },
                        ].map(({ key, label, desc }) => (
                            <div key={key} className={`flex items-center gap-3 p-2 rounded-lg ${gateChecks[key as keyof typeof gateChecks]
                                ? 'bg-blue-900/20 border border-blue-800/50'
                                : 'bg-slate-800/30 border border-slate-700/50'
                                }`}>
                                {gateChecks[key as keyof typeof gateChecks]
                                    ? <CheckSquare className="w-4 h-4 text-blue-400" />
                                    : <Square className="w-4 h-4 text-slate-600" />}
                                <div>
                                    <div className="text-xs font-medium text-slate-400">{label}</div>
                                    <div className="text-xs text-slate-600">{desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                    {/* Promote Button */}
                    <div className="mt-4 pt-4 border-t border-slate-700">
                        <button
                            onClick={handlePromote}
                            disabled={!canPromote || promoting}
                            className={`w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${canPromote
                                ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white'
                                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                }`}
                        >
                            {promoting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trophy className="w-4 h-4" />}
                            {seed.is_final ? 'Already Final' : canPromote ? '승격 (Promote to Final)' : '조건 미충족'}
                        </button>
                    </div>
                </div>

                {/* Edit Form */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                    {/* Basic Info */}
                    <section>
                        <h3 className="text-md font-semibold text-white mb-4 border-b border-slate-700 pb-2">기본 정보</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Drug Name</label>
                                <input
                                    type="text"
                                    value={formData.drug_name_canonical || ''}
                                    onChange={e => updateField('drug_name_canonical', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Target</label>
                                <input
                                    type="text"
                                    value={formData.target || ''}
                                    onChange={e => updateField('target', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Resolved Target Symbol ⭐</label>
                                <input
                                    type="text"
                                    value={formData.resolved_target_symbol || ''}
                                    onChange={e => updateField('resolved_target_symbol', e.target.value)}
                                    placeholder="예: ERBB2, FOLR1, MET"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Antibody</label>
                                <input
                                    type="text"
                                    value={formData.antibody || ''}
                                    onChange={e => updateField('antibody', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Clinical */}
                    <section>
                        <h3 className="text-md font-semibold text-white mb-4 border-b border-slate-700 pb-2">임상 정보</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Primary NCT ID ⭐</label>
                                <input
                                    type="text"
                                    value={formData.clinical_nct_id_primary || ''}
                                    onChange={e => updateField('clinical_nct_id_primary', e.target.value)}
                                    placeholder="NCT12345678"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Clinical Phase</label>
                                <select
                                    value={formData.clinical_phase || ''}
                                    onChange={e => updateField('clinical_phase', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                >
                                    <option value="">선택</option>
                                    <option value="Approved">Approved</option>
                                    <option value="Phase 3">Phase 3</option>
                                    <option value="Phase 2">Phase 2</option>
                                    <option value="Phase 1">Phase 1</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Program Status</label>
                                <select
                                    value={formData.program_status || ''}
                                    onChange={e => updateField('program_status', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                >
                                    <option value="">선택</option>
                                    <option value="Active">Active</option>
                                    <option value="Terminated">Terminated</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Outcome</label>
                                <select
                                    value={formData.outcome_label || ''}
                                    onChange={e => updateField('outcome_label', e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                >
                                    <option value="">선택</option>
                                    <option value="Success">Success</option>
                                    <option value="Fail">Fail</option>
                                    <option value="Uncertain">Uncertain</option>
                                    <option value="Caution">Caution</option>
                                </select>
                            </div>
                        </div>
                    </section>

                    {/* Chemistry */}
                    <section>
                        <h3 className="text-md font-semibold text-white mb-4 border-b border-slate-700 pb-2">Chemistry (SMILES)</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="block text-sm text-slate-400 mb-1">Payload SMILES (Standardized) ⭐</label>
                                <input
                                    type="text"
                                    value={formData.payload_smiles_standardized || ''}
                                    onChange={e => updateField('payload_smiles_standardized', e.target.value)}
                                    placeholder="정규화된 SMILES 문자열"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono text-sm"
                                />
                            </div>
                            <div className="flex items-center gap-3">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.proxy_smiles_flag || false}
                                        onChange={e => updateField('proxy_smiles_flag', e.target.checked)}
                                        className="w-4 h-4 rounded border-slate-600"
                                    />
                                    <span className="text-sm text-slate-300">Proxy SMILES Flag ⭐</span>
                                </label>
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Proxy Reference</label>
                                <input
                                    type="text"
                                    value={formData.proxy_reference || ''}
                                    onChange={e => updateField('proxy_reference', e.target.value)}
                                    placeholder="예: SN-38 core"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Evidence */}
                    <section>
                        <h3 className="text-md font-semibold text-white mb-4 border-b border-slate-700 pb-2">Evidence ⭐</h3>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Primary Source ID</label>
                            <input
                                type="text"
                                value={formData.primary_source_id || ''}
                                onChange={e => {
                                    updateField('primary_source_id', e.target.value);
                                    // Auto-add to evidence_refs if not empty
                                    if (e.target.value) {
                                        updateField('evidence_refs', [{ id: e.target.value, type: formData.primary_source_type || 'unknown' }]);
                                    }
                                }}
                                placeholder="NCT번호, BLA번호, PMID 등"
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                현재 Evidence: {formData.evidence_refs?.length || 0}개
                            </p>
                        </div>
                    </section>

                    {/* Verified Toggle */}
                    <section className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                        <div>
                            <div className="text-sm font-medium text-white">Verified Lock</div>
                            <div className="text-xs text-slate-500">활성화 시 자동화 Job이 덮어쓰지 않습니다</div>
                        </div>
                        <button
                            onClick={() => updateField('is_manually_verified', !formData.is_manually_verified)}
                            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${formData.is_manually_verified
                                ? 'bg-yellow-600 text-white'
                                : 'bg-slate-700 text-slate-400'
                                }`}
                        >
                            {formData.is_manually_verified ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                            {formData.is_manually_verified ? 'Verified' : 'Unverified'}
                        </button>
                    </section>

                    {/* Save Button */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                        <Link
                            href="/admin/golden-sets"
                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
                        >
                            취소
                        </Link>
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            저장
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
