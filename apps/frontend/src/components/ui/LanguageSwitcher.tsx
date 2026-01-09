'use client';

import { useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/routing';

export default function LanguageSwitcher() {
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const switchLocale = (newLocale: 'en' | 'ko') => {
        router.replace(pathname, { locale: newLocale });
    };

    return (
        <div className="flex items-center gap-1 text-sm">
            <button
                onClick={() => switchLocale('ko')}
                className={`px-2 py-1 rounded transition-colors ${locale === 'ko'
                        ? 'text-white font-medium'
                        : 'text-slate-400 hover:text-white'
                    }`}
            >
                한
            </button>
            <span className="text-slate-600">|</span>
            <button
                onClick={() => switchLocale('en')}
                className={`px-2 py-1 rounded transition-colors ${locale === 'en'
                        ? 'text-white font-medium'
                        : 'text-slate-400 hover:text-white'
                    }`}
            >
                EN
            </button>
        </div>
    );
}
