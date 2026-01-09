'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Zap, Shield, Users, Layers } from 'lucide-react';

export default function ServicesPage() {
    const t = useTranslations('ServicesPage');

    const fadeIn = {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.6 }
    };

    return (
        <main className="min-h-screen pt-24 pb-12 px-4 bg-transparent relative">
            <div className="container mx-auto max-w-6xl">
                {/* Header */}
                <motion.div
                    initial="initial"
                    animate="animate"
                    variants={fadeIn}
                    className="text-center mb-20"
                >
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        {t('title')}
                    </h1>
                    <p className="text-xl text-slate-300 max-w-3xl mx-auto">
                        {t('subtitle')}
                    </p>
                </motion.div>

                {/* Intro Section */}
                <motion.section
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    className="mb-24 bg-slate-900/40 backdrop-blur-sm border border-slate-800 rounded-3xl p-8 md:p-12"
                >
                    <h2 className="text-3xl font-bold text-white mb-6">{t('intro.title')}</h2>
                    <p className="text-lg text-slate-300 leading-relaxed">
                        {t('intro.desc')}
                    </p>
                </motion.section>

                {/* Problems Section */}
                <section className="mb-24">
                    <h2 className="text-3xl font-bold text-white mb-12 text-center">{t('problems.title')}</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        {[0, 1, 2, 3].map((i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6 flex items-start gap-4"
                            >
                                <div className="p-2 bg-red-500/10 rounded-lg shrink-0">
                                    <Shield className="w-6 h-6 text-red-400" />
                                </div>
                                <p className="text-slate-300">{t(`problems.items.${i}`)}</p>
                            </motion.div>
                        ))}
                    </div>
                </section>

                {/* Core Values Section */}
                <section className="mb-24">
                    <h2 className="text-3xl font-bold text-white mb-12 text-center">{t('values.title')}</h2>
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {[
                            { icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
                            { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-400/10' },
                            { icon: Layers, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                            { icon: Users, color: 'text-purple-400', bg: 'bg-purple-400/10' }
                        ].map((item, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6 hover:bg-slate-800/50 transition-colors"
                            >
                                <div className={`w-12 h-12 ${item.bg} rounded-lg flex items-center justify-center mb-6`}>
                                    <item.icon className={`w-6 h-6 ${item.color}`} />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-3">{t(`values.items.${i}.title`)}</h3>
                                <p className="text-slate-400 text-sm">{t(`values.items.${i}.desc`)}</p>
                            </motion.div>
                        ))}
                    </div>
                </section>

                {/* Workflow Section */}
                <section className="mb-24">
                    <h2 className="text-3xl font-bold text-white mb-12 text-center">{t('flow.title')}</h2>
                    <div className="relative">
                        {/* Connecting Line */}
                        <div className="absolute left-8 top-8 bottom-8 w-0.5 bg-slate-700 hidden md:block"></div>

                        <div className="space-y-8">
                            {[0, 1, 2, 3, 4, 5].map((i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: 20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    className="relative flex items-center gap-6 md:pl-16"
                                >
                                    <div className="hidden md:flex absolute left-0 w-16 h-16 items-center justify-center bg-slate-900 border border-slate-700 rounded-full z-10">
                                        <span className="text-xl font-bold text-blue-400">{i + 1}</span>
                                    </div>
                                    <div className="flex-1 bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
                                        <div className="flex items-center gap-4 md:hidden mb-2">
                                            <span className="text-lg font-bold text-blue-400">Step {i + 1}</span>
                                        </div>
                                        <p className="text-slate-200 text-lg">{t(`flow.items.${i}`)}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Differentiators Section */}
                <section className="mb-12">
                    <h2 className="text-3xl font-bold text-white mb-12 text-center">{t('diff.title')}</h2>
                    <div className="grid md:grid-cols-2 gap-8">
                        {[0, 1, 2, 3].map((i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, scale: 0.95 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700 rounded-2xl p-8"
                            >
                                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                    <ArrowRight className="w-5 h-5 text-blue-400" />
                                    {t(`diff.items.${i}.title`)}
                                </h3>
                                <p className="text-slate-400">{t(`diff.items.${i}.desc`)}</p>
                            </motion.div>
                        ))}
                    </div>
                </section>
            </div>
        </main>
    );
}
