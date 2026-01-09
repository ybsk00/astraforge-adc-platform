'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';

export default function SupportPage() {
    const t = useTranslations('Common');

    const supportOptions = [
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
            ),
            title: 'Email Support',
            description: 'Get help via email within 24 hours',
            action: 'support@astraforge.ai',
            href: 'mailto:support@astraforge.ai'
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            ),
            title: 'Documentation',
            description: 'Browse our comprehensive guides',
            action: 'View Docs',
            href: '#'
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ),
            title: 'FAQ',
            description: 'Find answers to common questions',
            action: 'Browse FAQ',
            href: '#'
        }
    ];

    return (
        <main className="min-h-screen flex items-center justify-center bg-slate-900 relative overflow-hidden py-12">
            {/* Background Effects */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
                <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[100px]" />
                <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[100px]" />
            </div>

            <div className="w-full max-w-2xl z-10 p-4">
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-xl text-white font-bold text-2xl mb-4">
                        A
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">How Can We Help?</h1>
                    <p className="text-slate-400">Get the support you need for your drug discovery platform.</p>
                </div>

                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    {supportOptions.map((option, index) => (
                        <a
                            key={index}
                            href={option.href}
                            className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center hover:border-blue-500/50 transition-all group"
                        >
                            <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600/20 rounded-xl text-blue-400 mb-4 group-hover:bg-blue-600/30 transition-colors">
                                {option.icon}
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">{option.title}</h3>
                            <p className="text-slate-400 text-sm mb-4">{option.description}</p>
                            <span className="text-blue-400 text-sm font-medium">{option.action}</span>
                        </a>
                    ))}
                </div>

                <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
                    <h2 className="text-xl font-semibold text-white mb-6">Send us a message</h2>
                    <form className="space-y-5">
                        <div className="grid md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
                                    Your Name
                                </label>
                                <input
                                    id="name"
                                    type="text"
                                    placeholder="John Doe"
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                />
                            </div>
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    placeholder="name@company.com"
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="subject" className="block text-sm font-medium text-slate-300 mb-2">
                                Subject
                            </label>
                            <select
                                id="subject"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            >
                                <option value="">Select a topic</option>
                                <option value="technical">Technical Issue</option>
                                <option value="billing">Billing Question</option>
                                <option value="feature">Feature Request</option>
                                <option value="other">Other</option>
                            </select>
                        </div>

                        <div>
                            <label htmlFor="message" className="block text-sm font-medium text-slate-300 mb-2">
                                Message
                            </label>
                            <textarea
                                id="message"
                                rows={4}
                                placeholder="Describe your issue or question..."
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                            />
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-lg transition-colors shadow-lg shadow-blue-600/20"
                        >
                            Send Message
                        </button>
                    </form>
                </div>

                <div className="text-center mt-8">
                    <Link href="/login" className="text-blue-400 hover:text-blue-300 font-medium">
                        ← Back to Login
                    </Link>
                </div>
            </div>
        </main>
    );
}
