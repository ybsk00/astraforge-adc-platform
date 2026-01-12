'use client';

import { useTranslations } from 'next-intl';
import { Settings, Construction } from 'lucide-react';

export default function SettingsPage() {
    const t = useTranslations('Common.menu');

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8 flex items-center justify-center">
            <div className="text-center">
                <div className="w-16 h-16 bg-blue-600/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <Settings className="w-8 h-8 text-blue-400" />
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">{t('settings')}</h1>
                <div className="flex items-center justify-center gap-2 text-slate-400">
                    <Construction className="w-4 h-4" />
                    <p>페이지 준비 중입니다.</p>
                </div>
            </div>
        </div>
    );
}
