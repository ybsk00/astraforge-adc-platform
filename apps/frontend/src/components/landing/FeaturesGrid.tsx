'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import {
    Calculator,
    SearchCheck,
    FlaskConical,
    ClipboardList,
    Database,
    FileText
} from 'lucide-react';

export default function FeaturesGrid() {
    const t = useTranslations('HomePage');

    const features = [
        {
            id: 'scoring',
            icon: <Calculator className="w-6 h-6" />,
            color: 'blue'
        },
        {
            id: 'evidence',
            icon: <SearchCheck className="w-6 h-6" />,
            color: 'green'
        },
        {
            id: 'safety',
            icon: <FlaskConical className="w-6 h-6" />,
            color: 'red'
        },
        {
            id: 'protocol',
            icon: <ClipboardList className="w-6 h-6" />,
            color: 'purple'
        },
        {
            id: 'goldenSet',
            icon: <Database className="w-6 h-6" />,
            color: 'yellow'
        },
        {
            id: 'report',
            icon: <FileText className="w-6 h-6" />,
            color: 'cyan'
        }
    ];

    const getColorClasses = (color: string) => {
        const colors: Record<string, string> = {
            blue: 'bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20',
            green: 'bg-green-500/10 text-green-400 group-hover:bg-green-500/20',
            red: 'bg-red-500/10 text-red-400 group-hover:bg-red-500/20',
            purple: 'bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20',
            yellow: 'bg-yellow-500/10 text-yellow-400 group-hover:bg-yellow-500/20',
            cyan: 'bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500/20',
        };
        return colors[color] || colors.blue;
    };

    return (
        <section id="features" className="py-24 bg-slate-950 relative">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16">
                    <h2 className="text-sm text-blue-400 font-medium uppercase tracking-wider mb-3">
                        {t('featuresLabel')}
                    </h2>
                    <h3 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                        {t('featuresTitle')}
                    </h3>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        {t('featuresSubtitle')}
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, idx) => (
                        <motion.div
                            key={feature.id}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                            className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 hover:border-slate-700 transition-all group hover:-translate-y-1"
                        >
                            <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 transition-colors ${getColorClasses(feature.color)}`}>
                                {feature.icon}
                            </div>
                            <h4 className="text-xl font-bold text-white mb-3">
                                {t(`features.${feature.id}`)}
                            </h4>
                            <p className="text-slate-400 leading-relaxed text-sm">
                                {t(`features.${feature.id}Desc`)}
                            </p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
