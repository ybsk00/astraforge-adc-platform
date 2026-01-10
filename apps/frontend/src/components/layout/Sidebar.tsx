'use client';

import { Link, usePathname } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import {
    LayoutDashboard,
    Dna,
    Package,
    Settings,
    Cable,
    Layers,
    Download,
    Activity,
    Bell,
    Upload,
    FileText,
    Search,
    Database,
    AlertTriangle,
    Server,
    FileClock,
    Terminal,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuth } from '@/contexts/AuthContext';

export default function Sidebar() {
    const t = useTranslations('Common.menu');
    const pathname = usePathname();
    const { isAdmin } = useAuth();

    const menuItems = [
        { href: '/dashboard', icon: LayoutDashboard, label: t('overview') },
        { href: '/design/runs', icon: Dna, label: t('designRuns') },
        { href: '/catalog', icon: Package, label: t('catalog') },
    ];

    const adminMenuItems = [
        { href: '/admin/connectors', icon: Cable, label: t('connectors') },
        { href: '/admin/staging', icon: Layers, label: t('staging') },
        { href: '/admin/ingestion/logs', icon: Download, label: t('ingestion') },
        { href: '/admin/observability', icon: Activity, label: t('observability') },
        { href: '/admin/alerts', icon: Bell, label: t('alerts') },
    ];

    const dataMenuItems = [
        { href: '/data/upload', icon: Upload, label: t('dataUpload') },
        { href: '/data/uploads', icon: FileText, label: t('uploadHistory') },
        { href: '/evidence/search', icon: Search, label: t('literatureSearch') },
        { href: '/evidence/ingestion', icon: Database, label: t('ingestionStatus') },
        { href: '/evidence/quality', icon: AlertTriangle, label: t('evidenceQuality') },
    ];

    const opsMenuItems = [
        { href: '/ops/status', icon: Activity, label: t('systemStatus') },
        { href: '/ops/queues', icon: Server, label: t('queues') },
        { href: '/ops/audit', icon: FileClock, label: t('audit') },
        { href: '/ops/logs', icon: Terminal, label: t('logs') },
    ];

    const isActive = (path: string) => pathname === path || pathname.startsWith(path + '/');

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-40 pt-16">
            {/* Navigation */}

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-8">
                {/* Main Menu - Only shown to non-admins */}
                {!isAdmin && (
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
                )}

                {/* Data & Evidence Menu - Only shown to non-admins */}
                {!isAdmin && (
                    <div>
                        <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                            {t('dataEvidence')}
                        </div>
                        <ul className="space-y-1">
                            {dataMenuItems.map((item) => {
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
                )}

                {/* Ops Menu - Only shown to non-admins */}
                {!isAdmin && (
                    <div>
                        <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                            {t('ops')}
                        </div>
                        <ul className="space-y-1">
                            {opsMenuItems.map((item) => {
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
                )}

                {/* Admin Menu - Only shown to admins */}
                {isAdmin && (
                    <div>
                        <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                            Admin
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
                )}
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

