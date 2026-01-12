'use client';

import { Link, usePathname } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import {
    Settings,
    Cable,
    Layers,
    Download,
    Activity,
    Bell,
    LayoutDashboard,
    Database,
    ClipboardCheck,
    Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';

export default function AdminSidebar() {
    const t = useTranslations('Common.menu');
    const pathname = usePathname();

    const adminMenuItems = [
        { href: '/admin', icon: LayoutDashboard, label: t('dashboard') },
        { href: '/admin/golden-sets', icon: Sparkles, label: t('goldenSets') },
        { href: '/admin/seeds', icon: Database, label: t('seeds') },
        { href: '/admin/connectors', icon: Cable, label: t('connectors') },
        { href: '/admin/runs', icon: Layers, label: t('designRuns') },
        { href: '/admin/reports', icon: Download, label: t('reports') },
        { href: '/admin/observability', icon: Activity, label: t('observability') },
        { href: '/admin/review', icon: ClipboardCheck, label: t('review') },
        { href: '/admin/alerts', icon: Bell, label: t('alerts') },
    ];

    const isActive = (path: string) => pathname === path || pathname.startsWith(path + '/');

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-50">
            {/* Navigation */}

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-8">
                {/* Admin Menu */}
                <div>
                    <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        {t('admin')}
                    </div>
                    <ul className="space-y-1">
                        {adminMenuItems.map((item) => {
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
