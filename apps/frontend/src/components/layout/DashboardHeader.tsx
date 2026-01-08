'use client';

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from '@/i18n/routing';
import { ChangeEvent, useTransition } from 'react';
import { Search, Bell, User } from 'lucide-react';

export default function DashboardHeader() {
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
        <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-30 ml-64">
            {/* Search */}
            <div className="flex-1 max-w-xl">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search..."
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
                {/* Language Switcher */}
                <select
                    defaultValue={locale}
                    onChange={onSelectChange}
                    disabled={isPending}
                    className="bg-slate-800 text-slate-200 text-sm rounded-md border border-slate-700 px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="en">🇺🇸 EN</option>
                    <option value="ko">🇰🇷 KR</option>
                </select>

                {/* Notifications */}
                <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-slate-900"></span>
                </button>

                {/* Profile */}
                <button className="flex items-center gap-2 pl-2 border-l border-slate-800">
                    <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-slate-300">
                        <User className="w-4 h-4" />
                    </div>
                    <div className="text-left hidden md:block">
                        <div className="text-sm font-medium text-white">Dr. Kim</div>
                        <div className="text-xs text-slate-500">Lead Researcher</div>
                    </div>
                </button>
            </div>
        </header>
    );
}
