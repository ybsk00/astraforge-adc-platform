import { Link, usePathname } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';

export default function Navigation() {
    const t = useTranslations('HomePage');
    const tCommon = useTranslations('Common');
    const pathname = usePathname();

    const isActive = (path: string) => pathname === path;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <span className="text-white text-sm font-bold">◇</span>
                    </div>
                    <span className="text-white font-bold">ADC Platform</span>
                </Link>
                <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
                    <Link
                        href="/services"
                        className={`hover:text-white transition-colors ${isActive('/services') ? 'text-white font-medium' : ''}`}
                    >
                        {t('nav.services')}
                    </Link>
                    <Link
                        href="/features"
                        className={`hover:text-white transition-colors ${isActive('/features') ? 'text-white font-medium' : ''}`}
                    >
                        {t('nav.features')}
                    </Link>
                    <Link
                        href="/solutions"
                        className={`hover:text-white transition-colors ${isActive('/solutions') ? 'text-white font-medium' : ''}`}
                    >
                        {t('nav.solutions')}
                    </Link>
                </div>
                <div className="flex items-center gap-4">
                    <LanguageSwitcher />
                    <Link
                        href="/login"
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                        {tCommon('login')}
                    </Link>
                </div>
            </div>
        </nav>
    );
}
