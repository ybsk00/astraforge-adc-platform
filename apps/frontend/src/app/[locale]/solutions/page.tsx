'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { Target, Sliders, AlertTriangle, BookOpen, Rocket } from 'lucide-react';

export default function SolutionsPage() {
    const t = useTranslations('SolutionsPage');

    const solutions = [
        { key: 'target', icon: Target, color: 'text-red-400', bg: 'bg-red-400/10' },
        { key: 'optimization', icon: Sliders, color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { key: 'risk', icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
        { key: 'knowledge', icon: BookOpen, color: 'text-green-400', bg: 'bg-green-400/10' }
    ];

    return (
        <main className="min-h-screen pt-24 pb-12 px-4 bg-transparent relative">
            <div className="container mx-auto max-w-6xl">
                {/* Header */}
                <div className="text-center mb-20">
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                        {t('title')}
                    </h1>
                    <p className="text-xl text-slate-300 max-w-3xl mx-auto">
                        {t('subtitle')}
                    </p>
                </div>

                {/* Solutions Grid */}
                <div className="grid md:grid-cols-2 gap-8 mb-24">
                    {solutions.map((sol, index) => (
                        <motion.div
                            key={sol.key}
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ delay: index * 0.1 }}
                            className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-8 hover:bg-slate-800/50 transition-colors group"
                        >
                            <div className={`w-14 h-14 ${sol.bg} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                                <sol.icon className={`w-7 h-7 ${sol.color}`} />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-4">{t(`${sol.key}.title`)}</h2>
                            <p className="text-slate-300 mb-6 leading-relaxed min-h-[3rem]">
                                {t(`${sol.key}.desc`)}
                            </p>
                            <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800">
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">Example</span>
                                <p className="text-sm text-slate-400">{t(`${sol.key}.example`)}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Deployment Options */}
                <motion.section
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 border border-slate-700 rounded-3xl p-8 md:p-12 text-center"
                >
                    <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Rocket className="w-8 h-8 text-blue-400" />
                    </div>
                    <h2 className="text-3xl font-bold text-white mb-8">{t('deployment.title')}</h2>
                    <div className="grid md:grid-cols-3 gap-6">
                        {[0, 1, 2].map((i) => (
                            <div key={i} className="bg-slate-950/50 rounded-xl p-6 border border-slate-800">
                                <p className="text-slate-200 font-medium">{t(`deployment.items.${i}`)}</p>
                            </div>
                        ))}
                    </div>
                </motion.section>
            </div>
        </main>
    );
}
