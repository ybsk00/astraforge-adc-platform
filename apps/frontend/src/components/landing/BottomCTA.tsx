'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function BottomCTA() {
    const t = useTranslations('HomePage');

    return (
        <section className="py-32 bg-slate-950 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-blue-950/20 to-slate-950" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="max-w-4xl mx-auto text-center"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8">
                        <Sparkles className="w-4 h-4" />
                        <span>Start your simulation today</span>
                    </div>

                    <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
                        {t('cta.title')}
                    </h2>
                    <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
                        {t('cta.subtitle')}
                    </p>

                    <div className="flex flex-wrap justify-center gap-6">
                        <Link
                            href="/login"
                            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/25 flex items-center gap-2 text-lg group"
                        >
                            {t('cta.primary')}
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <button className="px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl border border-slate-700 transition-all text-lg">
                            {t('cta.secondary')}
                        </button>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}
