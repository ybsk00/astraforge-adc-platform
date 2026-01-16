'use client';

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { useState } from 'react';

export default function FAQSection() {
    const t = useTranslations('HomePage');
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    const faqs = [
        { id: 'q1', question: t('faq.q1'), answer: t('faq.a1') },
        { id: 'q2', question: t('faq.q2'), answer: t('faq.a2') },
        { id: 'q3', question: t('faq.q3'), answer: t('faq.a3') }
    ];

    return (
        <section className="py-24 bg-slate-950">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16">
                    <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                        {t('faq.title')}
                    </h2>
                </div>

                <div className="max-w-3xl mx-auto space-y-4">
                    {faqs.map((faq, idx) => (
                        <motion.div
                            key={faq.id}
                            initial={{ opacity: 0, y: 10 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.4, delay: idx * 0.1 }}
                            className="border border-slate-800 rounded-xl overflow-hidden bg-slate-900/30"
                        >
                            <button
                                onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                                className="w-full flex items-center justify-between p-6 text-left hover:bg-slate-800/50 transition-colors"
                            >
                                <span className="text-lg font-medium text-white pr-8">
                                    {faq.question}
                                </span>
                                <span className={`shrink-0 text-blue-400 transition-transform duration-300 ${openIndex === idx ? 'rotate-45' : ''}`}>
                                    <Plus className="w-6 h-6" />
                                </span>
                            </button>

                            <motion.div
                                initial={false}
                                animate={{ height: openIndex === idx ? 'auto' : 0 }}
                                transition={{ duration: 0.3 }}
                                className="overflow-hidden"
                            >
                                <div className="p-6 pt-0 text-slate-400 leading-relaxed border-t border-slate-800/50">
                                    {faq.answer}
                                </div>
                            </motion.div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
