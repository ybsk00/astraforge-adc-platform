'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, ShieldCheck, Database, FileText } from 'lucide-react';
import HeroVideo from '../ui/HeroVideo';

export default function HeroSection() {
    const t = useTranslations('HomePage');

    return (
        <section className="relative pt-32 pb-24 overflow-hidden min-h-screen flex items-center">
            {/* Background Elements */}
            <div className="absolute inset-0 bg-slate-950">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950 to-slate-950" />
                <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />
            </div>

            <div className="container mx-auto px-4 relative z-10">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Text Content */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-6">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                            </span>
                            ADC Candidate Design & Simulation Engine
                        </div>

                        <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight mb-2">
                            {t('titlePrefix')}
                        </h1>
                        <h1 className="text-5xl lg:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 leading-tight mb-6">
                            {t.rich('titleMain', { br: () => <br /> })}
                        </h1>

                        <p className="text-lg text-slate-400 mb-8 max-w-lg leading-relaxed">
                            {t('subtitle')}
                        </p>

                        <div className="flex flex-wrap gap-4 mb-12">
                            <Link
                                href="/login"
                                className="group px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition-all shadow-lg shadow-blue-600/25 flex items-center gap-2"
                            >
                                {t('start')}
                                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </Link>
                            <button className="px-8 py-4 bg-slate-800/50 hover:bg-slate-800 text-white font-semibold rounded-lg border border-slate-700 transition-all flex items-center gap-2">
                                {t('demo')}
                            </button>
                        </div>

                        {/* Trust Badges */}
                        <div className="border-t border-slate-800 pt-8">
                            <div className="flex flex-wrap gap-6 text-sm text-slate-500">
                                <div className="flex items-center gap-2">
                                    <Database className="w-4 h-4 text-blue-500" />
                                    {t('badges.data')}
                                </div>
                                <div className="flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-blue-500" />
                                    {t('badges.evidence')}
                                </div>
                                <div className="flex items-center gap-2">
                                    <ShieldCheck className="w-4 h-4 text-blue-500" />
                                    {t('badges.quality')}
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Hero Visual */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="relative lg:h-[600px] flex items-center justify-center"
                    >
                        <div className="absolute inset-0 bg-blue-500/5 blur-3xl rounded-full" />
                        <div className="relative w-full h-full">
                            <HeroVideo />
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
