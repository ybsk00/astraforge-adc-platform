'use client';

import { useLocale, useTranslations } from 'next-intl';
import { Link, usePathname, useRouter } from '@/i18n/routing';
import { ChangeEvent, useTransition } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export default function Header() {
    const t = useTranslations('Common');
    const tHome = useTranslations('HomePage.nav');
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();
    const [isPending, startTransition] = useTransition();
    const { isAdmin, user } = useAuth();

    const onSelectChange = (e: ChangeEvent<HTMLSelectElement>) => {
        const nextLocale = e.target.value;
        startTransition(() => {
            router.replace(pathname, { locale: nextLocale });
        });
    };

    // Define public pages where the public navigation should be shown
    const isPublicPage = pathname === '/' ||
        pathname.startsWith('/services') ||
        pathname.startsWith('/features') ||
        pathname.startsWith('/solutions') ||
        pathname.startsWith('/login');

    const isActive = (path: string) => pathname === path;

    return (
        <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                        A
                    </div>
                    <span className="text-xl font-bold text-white">ADC Platform</span>
                </Link>

                {/* Navigation */}
                <nav className="hidden md:flex items-center gap-8">
                    {isPublicPage ? (
                        <>
                            <Link
                                href="/services"
                                className={`text-sm font-medium transition-colors ${isActive('/services') ? 'text-white' : 'text-slate-300 hover:text-white'}`}
                            >
                                {tHome('services')}
                            </Link>
                            <Link
                                href="/features"
                                className={`text-sm font-medium transition-colors ${isActive('/features') ? 'text-white' : 'text-slate-300 hover:text-white'}`}
                            >
                                {tHome('features')}
                            </Link>
                            <Link
                                href="/solutions"
                                className={`text-sm font-medium transition-colors ${isActive('/solutions') ? 'text-white' : 'text-slate-300 hover:text-white'}`}
                            >
                                {tHome('solutions')}
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link href="/dashboard" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                                {t('dashboard')}
                            </Link>
                            <Link href="/design/runs" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                                {t('designRuns')}
                            </Link>
                            <Link href="/catalog" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                                {t('catalog')}
                            </Link>
                            {isAdmin && (
                                <Link href="/admin/connectors" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                                    {t('admin')}
                                </Link>
                            )}
                        </>
                    )}
                </nav>

                {/* Right Actions */}
                <div className="flex items-center gap-4">
                    {/* Language Switcher */}
                    <div className="relative">
                        <select
                            defaultValue={locale}
                            onChange={onSelectChange}
                            disabled={isPending}
                            className="bg-slate-800 text-slate-200 text-sm rounded-md border border-slate-700 px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none pr-8 cursor-pointer"
                            style={{ backgroundImage: 'none' }}
                        >
                            <option value="en">EN</option>
                            <option value="ko">KO</option>
                        </select>
                        {/* Custom Arrow Icon */}
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>

                    {/* Auth Buttons */}
                    {user ? (
                        <div className="flex items-center gap-3">
                            <Link
                                href="/dashboard"
                                className="text-slate-300 hover:text-white text-sm font-medium transition-colors"
                            >
                                {t('dashboard')}
                            </Link>
                            <button
                                onClick={async () => {
                                    const { createClient } = await import('@/lib/supabase/client');
                                    const supabase = createClient();
                                    await supabase.auth.signOut();
                                    router.refresh();
                                }}
                                className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium px-4 py-2 rounded-md border border-slate-700 transition-colors"
                            >
                                {t('logout')}
                            </button>
                        </div>
                    ) : (
                        <Link
                            href="/login"
                            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
                        >
                            {t('login')}
                        </Link>
                    )}
                </div>
            </div>
        </header>
    );
}
