'use client';

import { Link, usePathname } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import {
    LayoutDashboard,
    Dna,
    Package,
    Settings,
    Network,
    Database,
    Activity,
    Bell,
    HardDrive
} from 'lucide-react';
import { clsx } from 'clsx';

export default function Sidebar() {
    const t = useTranslations('Common.menu');
    const pathname = usePathname();

    const menuItems = [
        { href: '/dashboard', icon: LayoutDashboard, label: t('overview') },
        { href: '/design/runs', icon: Dna, label: t('designRuns') },
        { href: '/catalog', icon: Package, label: t('catalog') },
    ];

    const adminItems = [
        { href: '/admin/connectors', icon: Network, label: t('connectors') },
        { href: '/admin/staging', icon: HardDrive, label: t('staging') },
        { href: '/admin/ingestion', icon: Database, label: t('ingestion') },
        { href: '/admin/observability', icon: Activity, label: t('observability') },
        { href: '/admin/alerts', icon: Bell, label: t('alerts') },
    ];

    const isActive = (path: string) => pathname === path || pathname.startsWith(path + '/');

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-40">
            {/* Logo */}
            <div className="h-16 flex items-center px-6 border-b border-slate-800">
                <Link href="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                        A
                    </div>
                    <span className="text-xl font-bold text-white">ADC Platform</span>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-8">
                {/* Main Menu */}
                <div>
                    <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Main
                    </div>
                    <ul className="space-y-1">
                        {menuItems.map((item) => {
                            const active = isActive(item.href);
                            return (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        className={clsx(
                                            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                                            active
                                                ? 'bg-blue-600/10 text-blue-400'
                                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                                        )}
                                    >
                                        <item.icon className="w-5 h-5" />
                                        {item.label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </div>

                {/* Admin Menu */}
                <div>
                    <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Admin
                    </div>
                    <ul className="space-y-1">
                        {adminItems.map((item) => {
                            const active = isActive(item.href);
                            return (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        className={clsx(
                                            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                                            active
                                                ? 'bg-blue-600/10 text-blue-400'
                                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                                        )}
                                    >
                                        <item.icon className="w-5 h-5" />
                                        {item.label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </nav>

            {/* Bottom Actions */}
            <div className="p-4 border-t border-slate-800">
                <Link
                    href="/settings"
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                >
                    <Settings className="w-5 h-5" />
                    {t('settings')}
                </Link>
            </div>
        </aside>
    );
}
