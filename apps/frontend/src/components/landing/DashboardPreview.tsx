'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { Activity, Database, AlertTriangle } from 'lucide-react';

export default function DashboardPreview() {
    const t = useTranslations('HomePage');

    return (
        <section id="interface" className="py-24 bg-slate-950 relative overflow-hidden">
            <div className="container mx-auto px-4 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                        {t('dashboard.title')}
                    </h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        {t('dashboard.subtitle')}
                    </p>
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8 }}
                    className="relative max-w-6xl mx-auto"
                >
                    {/* Glow effect */}
                    <div className="absolute inset-0 bg-blue-500/10 blur-3xl rounded-full opacity-30" />

                    {/* Dashboard Container */}
                    <div className="relative bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                        {/* Window Controls */}
                        <div className="h-10 bg-slate-800/50 border-b border-slate-700/50 flex items-center px-4 gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                        </div>

                        <div className="relative aspect-video bg-slate-950 group">
                            <img
                                src="/images/landing/adc_dashboard_preview.png"
                                alt="ADC Platform Dashboard"
                                className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-500"
                            />
                            {/* Overlay gradient for better integration */}
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/20 to-transparent pointer-events-none" />
                        </div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}
