'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Search, FlaskConical, DollarSign, BrainCircuit } from 'lucide-react';

export default function ProblemSolution() {
    const t = useTranslations('HomePage');

    const problems = [
        {
            icon: <Search className="w-6 h-6 text-red-400" />,
            title: t('problem.p1Title'),
            desc: t('problem.p1Desc')
        },
        {
            icon: <FlaskConical className="w-6 h-6 text-red-400" />,
            title: t('problem.p2Title'),
            desc: t('problem.p2Desc')
        },
        {
            icon: <DollarSign className="w-6 h-6 text-red-400" />,
            title: t('problem.p3Title'),
            desc: t('problem.p3Desc')
        }
    ];

    return (
        <section className="py-24 bg-slate-950 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

            <div className="container mx-auto px-4 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                        {t('problem.title')} <span className="text-slate-500">vs</span> {t('solution.title')}
                    </h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        {t('problem.subtitle')}
                    </p>
                </div>

                <div className="grid lg:grid-cols-2 gap-8 lg:gap-16">
                    {/* Problem Side */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="space-y-8"
                    >
                        <div className="bg-red-950/10 border border-red-900/30 rounded-2xl p-8 relative overflow-hidden group">
                            {/* Image Background */}
                            <div className="absolute inset-0 z-0">
                                <img
                                    src="/images/landing/drug_discovery_funnel.jpg"
                                    alt="Drug Discovery Funnel"
                                    className="w-full h-full object-cover opacity-20 group-hover:opacity-30 transition-opacity duration-500"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent" />
                            </div>

                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-3 bg-red-500/10 rounded-lg backdrop-blur-sm border border-red-500/20">
                                        <AlertTriangle className="w-6 h-6 text-red-500" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white">Traditional Approach</h3>
                                </div>

                                <div className="space-y-6">
                                    {problems.map((item, idx) => (
                                        <div key={idx} className="flex gap-4">
                                            <div className="mt-1 shrink-0 p-2 bg-red-500/5 rounded-lg border border-red-500/10 backdrop-blur-sm">
                                                {item.icon}
                                            </div>
                                            <div>
                                                <h4 className="text-white font-medium mb-1">{item.title}</h4>
                                                <p className="text-sm text-slate-400 leading-relaxed">
                                                    {item.desc}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Solution Side */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="space-y-8"
                    >
                        <div className="bg-blue-950/10 border border-blue-900/30 rounded-2xl p-8 h-full relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-3 bg-blue-500/10 rounded-lg">
                                        <BrainCircuit className="w-6 h-6 text-blue-500" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white">ADC Platform Engine</h3>
                                </div>

                                <div className="prose prose-invert max-w-none">
                                    <p className="text-lg text-blue-100 leading-relaxed mb-6">
                                        {t('solution.subtitle')}
                                    </p>
                                    <p className="text-slate-400 leading-relaxed mb-8">
                                        {t('solution.desc')}
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                        <div className="flex items-center gap-2 mb-2 text-green-400">
                                            <CheckCircle2 className="w-4 h-4" />
                                            <span className="text-sm font-bold">Golden Set</span>
                                        </div>
                                        <span className="text-xs text-slate-500">Verified Success Patterns</span>
                                    </div>
                                    <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                        <div className="flex items-center gap-2 mb-2 text-blue-400">
                                            <CheckCircle2 className="w-4 h-4" />
                                            <span className="text-sm font-bold">AI Scoring</span>
                                        </div>
                                        <span className="text-xs text-slate-500">0-100 Probability Score</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
