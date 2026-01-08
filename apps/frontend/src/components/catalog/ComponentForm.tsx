'use client';

import { useState } from 'react';
import type { Component, ComponentCreate } from '@/lib/api';
import { api } from '@/lib/api';
import { X, Target, Syringe, Link as LinkIcon, Pill, FlaskConical } from 'lucide-react';

interface ComponentFormProps {
    component?: Component;
    onSuccess: () => void;
    onCancel: () => void;
}

const COMPONENT_TYPES = [
    { value: 'target', label: 'Target', icon: Target, color: 'text-red-400', bg: 'bg-red-500/20' },
    { value: 'antibody', label: 'Antibody', icon: Syringe, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    { value: 'linker', label: 'Linker', icon: LinkIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    { value: 'payload', label: 'Payload', icon: Pill, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    { value: 'conjugation', label: 'Conjugation', icon: FlaskConical, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
] as const;

const QUALITY_GRADES = [
    { value: 'gold', label: 'Gold', icon: '🥇', class: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
    { value: 'silver', label: 'Silver', icon: '🥈', class: 'bg-slate-500/20 text-slate-300 border-slate-500/30' },
    { value: 'bronze', label: 'Bronze', icon: '🥉', class: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
] as const;

export default function ComponentForm({ component, onSuccess, onCancel }: ComponentFormProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState<ComponentCreate>({
        type: component?.type || 'payload',
        name: component?.name || '',
        properties: component?.properties || {},
        quality_grade: component?.quality_grade || 'silver',
    });

    const [smiles, setSmiles] = useState(
        (component?.properties?.smiles as string) || ''
    );
    const [mechanism, setMechanism] = useState(
        (component?.properties?.mechanism as string) || ''
    );

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const properties: Record<string, unknown> = { ...formData.properties };
            if (smiles) properties.smiles = smiles;
            if (mechanism) properties.mechanism = mechanism;

            if (component) {
                await api.updateComponent(component.id, {
                    ...formData,
                    properties,
                });
            } else {
                await api.createComponent({
                    ...formData,
                    properties,
                });
            }

            onSuccess();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save component');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl w-full max-w-lg">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <h2 className="text-xl font-bold text-white">
                        {component ? '컴포넌트 수정' : '새 컴포넌트 등록'}
                    </h2>
                    <button
                        onClick={onCancel}
                        className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2 rounded-lg mb-4">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Type */}
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                컴포넌트 타입
                            </label>
                            <div className="grid grid-cols-5 gap-2">
                                {COMPONENT_TYPES.map((t) => {
                                    const IconComponent = t.icon;
                                    return (
                                        <button
                                            key={t.value}
                                            type="button"
                                            onClick={() => !component && setFormData({ ...formData, type: t.value as ComponentCreate['type'] })}
                                            disabled={!!component}
                                            className={`p-3 rounded-lg flex flex-col items-center gap-1 transition-all ${formData.type === t.value
                                                    ? `${t.bg} ring-2 ring-blue-500`
                                                    : 'bg-slate-800 hover:bg-slate-700'
                                                } ${component ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            <IconComponent className={`w-5 h-5 ${t.color}`} />
                                            <span className="text-xs text-slate-300">{t.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Name */}
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                이름
                            </label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="예: MMAE, Trastuzumab"
                                required
                            />
                        </div>

                        {/* SMILES */}
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                SMILES (선택)
                            </label>
                            <textarea
                                value={smiles}
                                onChange={(e) => setSmiles(e.target.value)}
                                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                                placeholder="CC(C)CC1NC(=O)..."
                                rows={2}
                            />
                        </div>

                        {/* Mechanism */}
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                작용 기전 (선택)
                            </label>
                            <input
                                type="text"
                                value={mechanism}
                                onChange={(e) => setMechanism(e.target.value)}
                                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="예: tubulin_inhibitor, dna_binder"
                            />
                        </div>

                        {/* Quality Grade */}
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                품질 등급
                            </label>
                            <div className="flex gap-2">
                                {QUALITY_GRADES.map((grade) => (
                                    <button
                                        key={grade.value}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, quality_grade: grade.value })}
                                        className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium border transition-all flex items-center justify-center gap-2 ${formData.quality_grade === grade.value
                                                ? `${grade.class} ring-2 ring-blue-500 ring-offset-1 ring-offset-slate-900`
                                                : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                                            }`}
                                    >
                                        <span>{grade.icon}</span>
                                        {grade.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3 pt-2">
                            <button
                                type="button"
                                onClick={onCancel}
                                className="flex-1 px-4 py-2.5 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
                            >
                                취소
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 transition-colors"
                            >
                                {loading ? '저장 중...' : component ? '수정' : '등록'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
