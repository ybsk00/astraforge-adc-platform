'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { ShieldCheck, Eye, Scale } from 'lucide-react';

export default function TrustSection() {
    const t = useTranslations('HomePage');

    const items = [
        {
            id: 'p1',
            icon: <ShieldCheck className="w-8 h-8" />,
            color: 'blue'
        },
        {
            id: 'p2',
            icon: <Eye className="w-8 h-8" />,
            color: 'green'
        },
        {
            id: 'p3',
            icon: <Scale className="w-8 h-8" />,
            color: 'purple'
        }
    ];

    return (
        <section className="py-24 bg-slate-900 border-y border-slate-800">
            <div className="container mx-auto px-4">
                <div className="grid lg:grid-cols-2 gap-16 items-center">
                    {/* Left: Content */}
                    <div>
                        <h2 className="text-sm text-blue-400 font-medium uppercase tracking-wider mb-3">
                            {t('trust.title')}
                        </h2>
                        <h3 className="text-3xl lg:text-4xl font-bold text-white mb-6">
                            {t('trust.subtitle')}
                        </h3>

                        <div className="space-y-8 mt-12">
                            {items.map((item, idx) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ duration: 0.5, delay: idx * 0.1 }}
                                    className="flex gap-6"
                                >
                                    <div className={`shrink-0 w-16 h-16 rounded-2xl bg-${item.color}-500/10 flex items-center justify-center text-${item.color}-400`}>
                                        {item.icon}
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold text-white mb-2">
                                            {t(`trust.${item.id}Title`)}
                                        </h4>
                                        <p className="text-slate-400 leading-relaxed">
                                            {t(`trust.${item.id}Desc`)}
                                        </p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>

                    {/* Right: Visual */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="relative"
                    >
                        <div className="absolute inset-0 bg-blue-500/10 blur-3xl rounded-full opacity-50" />
                        <div className="relative bg-slate-950 border border-slate-800 rounded-2xl p-8 shadow-2xl">
                            {/* Mock Data Integrity Visual */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">Data Source Integrity</span>
                                    <span className="text-green-400 text-sm font-bold">99.9% Verified</span>
                                </div>

                                <div className="space-y-3">
                                    {[1, 2, 3].map((i) => (
                                        <div key={i} className="bg-slate-900 rounded-lg p-4 flex items-center gap-4">
                                            <div className="w-2 h-2 rounded-full bg-green-500" />
                                            <div className="flex-1">
                                                <div className="h-2 bg-slate-800 rounded w-24 mb-2" />
                                                <div className="h-1.5 bg-slate-800/50 rounded w-32" />
                                            </div>
                                            <div className="text-xs text-slate-500 font-mono">
                                                VERIFIED
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="mt-6 pt-6 border-t border-slate-800">
                                    <div className="flex items-center gap-3 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                                        <ShieldCheck className="w-5 h-5 text-blue-400" />
                                        <div>
                                            <div className="text-sm font-bold text-white">Golden Set Certified</div>
                                            <div className="text-xs text-blue-300/70">Manually reviewed by experts</div>
                                        </div>
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
