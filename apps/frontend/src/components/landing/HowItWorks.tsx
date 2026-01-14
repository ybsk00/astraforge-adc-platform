'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { MousePointerClick, Globe, FlaskConical, FileBarChart, ArrowRight } from 'lucide-react';

export default function HowItWorks() {
    const t = useTranslations('HomePage');

    const steps = [
        {
            id: 'step1',
            icon: <MousePointerClick className="w-8 h-8" />,
            color: 'blue'
        },
        {
            id: 'step2',
            icon: <Globe className="w-8 h-8" />,
            color: 'purple'
        },
        {
            id: 'step3',
            icon: <FlaskConical className="w-8 h-8" />,
            color: 'green'
        },
        {
            id: 'step4',
            icon: <FileBarChart className="w-8 h-8" />,
            color: 'cyan'
        }
    ];

    return (
        <section className="py-24 bg-slate-950 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-500/5 blur-[100px] rounded-full pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10">
                <div className="text-center mb-20">
                    <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                        {t('howItWorks.title')}
                    </h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        {t('howItWorks.subtitle')}
                    </p>
                </div>

                <div className="relative">
                    {/* Connecting Line (Desktop) */}
                    <div className="hidden lg:block absolute top-12 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />

                    <div className="grid lg:grid-cols-4 gap-8">
                        {steps.map((step, idx) => (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: idx * 0.15 }}
                                className="relative group"
                            >
                                {/* Step Number Bubble */}
                                <div className="relative flex justify-center mb-8">
                                    <div className="w-24 h-24 rounded-full bg-slate-900 border-4 border-slate-950 shadow-xl flex items-center justify-center relative z-10 group-hover:scale-110 transition-transform duration-300">
                                        <div className={`absolute inset-0 rounded-full bg-${step.color}-500/10 opacity-0 group-hover:opacity-100 transition-opacity`} />
                                        <div className={`text-${step.color}-400`}>
                                            {step.icon}
                                        </div>

                                        {/* Step Number Badge */}
                                        <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-sm font-bold text-white">
                                            {idx + 1}
                                        </div>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="text-center px-4">
                                    <h3 className="text-xl font-bold text-white mb-3">
                                        {t(`howItWorks.${step.id}`)}
                                    </h3>
                                    <p className="text-sm text-slate-400 leading-relaxed">
                                        {t(`howItWorks.${step.id}Desc`)}
                                    </p>
                                </div>

                                {/* Arrow (Mobile only) */}
                                {idx < steps.length - 1 && (
                                    <div className="lg:hidden flex justify-center my-8 text-slate-700">
                                        <ArrowRight className="w-6 h-6 rotate-90" />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
