'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { Database, Search, PenTool, BarChart2, Users } from 'lucide-react';

export default function FeaturesPage() {
    const t = useTranslations('FeaturesPage');

    const features = [
        { key: 'data', icon: Database, color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { key: 'search', icon: Search, color: 'text-purple-400', bg: 'bg-purple-400/10' },
        { key: 'design', icon: PenTool, color: 'text-green-400', bg: 'bg-green-400/10' },
        { key: 'scoring', icon: BarChart2, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
        { key: 'collab', icon: Users, color: 'text-red-400', bg: 'bg-red-400/10' }
    ];

    return (
        <main className="min-h-screen pt-24 pb-12 px-4 bg-transparent relative">
            <div className="container mx-auto max-w-6xl">
                {/* Header */}
                <div className="text-center mb-20">
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-green-400">
                        {t('title')}
                    </h1>
                    <p className="text-xl text-slate-300 max-w-3xl mx-auto">
                        {t('subtitle')}
                    </p>
                </div>

                {/* Features Grid */}
                <div className="space-y-24">
                    {features.map((feature, index) => (
                        <motion.section
                            key={feature.key}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-100px" }}
                            transition={{ duration: 0.6 }}
                            className={`flex flex-col ${index % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'} gap-12 items-center`}
                        >
                            {/* Icon/Visual Side */}
                            <div className="flex-1 w-full">
                                <div className="bg-slate-800/30 border border-slate-700/50 rounded-3xl p-12 flex items-center justify-center aspect-video md:aspect-square relative overflow-hidden group">
                                    <div className={`absolute inset-0 ${feature.bg} blur-3xl opacity-20 group-hover:opacity-30 transition-opacity`}></div>
                                    <feature.icon className={`w-24 h-24 ${feature.color} relative z-10`} />
                                </div>
                            </div>

                            {/* Content Side */}
                            <div className="flex-1 space-y-6">
                                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${feature.bg} border border-slate-700/50`}>
                                    <feature.icon className={`w-4 h-4 ${feature.color}`} />
                                    <span className={`text-sm font-bold ${feature.color} uppercase tracking-wider`}>
                                        Feature {index + 1}
                                    </span>
                                </div>
                                <h2 className="text-3xl font-bold text-white">{t(`${feature.key}.title`)}</h2>
                                <ul className="space-y-4">
                                    {[0, 1, 2].map((i) => {
                                        // Check if item exists to avoid errors if array length varies
                                        try {
                                            const itemText = t(`${feature.key}.items.${i}`);
                                            // If translation key is missing or returns key itself (next-intl behavior depends on config), skip
                                            if (itemText.includes('FeaturesPage')) return null;

                                            return (
                                                <li key={i} className="flex items-start gap-3 text-slate-300">
                                                    <div className={`mt-1.5 w-1.5 h-1.5 rounded-full ${feature.color.replace('text-', 'bg-')}`}></div>
                                                    <span>{itemText}</span>
                                                </li>
                                            );
                                        } catch {
                                            return null;
                                        }
                                    })}
                                </ul>
                            </div>
                        </motion.section>
                    ))}
                </div>
            </div>
        </main>
    );
}
