'use client';

import { useLocale, useTranslations } from 'next-intl';
import { Link, usePathname, useRouter } from '@/i18n/routing';
import { ChangeEvent, useTransition } from 'react';

export default function Header() {
    const t = useTranslations('Common');
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();
    const [isPending, startTransition] = useTransition();

    const onSelectChange = (e: ChangeEvent<HTMLSelectElement>) => {
        const nextLocale = e.target.value;
        startTransition(() => {
            router.replace(pathname, { locale: nextLocale });
        });
    };

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
                    <Link href="/dashboard" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                        {t('dashboard')}
                    </Link>
                    <Link href="/design/runs" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                        {t('designRuns')}
                    </Link>
                    <Link href="/catalog" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                        {t('catalog')}
                    </Link>
                    <Link href="/admin/connectors" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                        {t('admin')}
                    </Link>
                </nav>

                {/* Right Actions */}
                <div className="flex items-center gap-4">
                    {/* Language Switcher */}
                    <div className="relative">
                        <select
                            defaultValue={locale}
                            onChange={onSelectChange}
                            disabled={isPending}
                            className="bg-slate-800 text-slate-200 text-sm rounded-md border border-slate-700 px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="en">🇺🇸 EN</option>
                            <option value="ko">🇰🇷 KR</option>
                        </select>
                    </div>

                    {/* Login Button */}
                    <Link
                        href="/login"
                        className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
                    >
                        {t('login')}
                    </Link>
                </div>
            </div>
        </header>
    );
}
