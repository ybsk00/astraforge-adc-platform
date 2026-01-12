'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AdminSidebar from '@/components/layout/AdminSidebar';
import DashboardHeader from '@/components/layout/DashboardHeader';
import { useAuth } from '@/contexts/AuthContext';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { isAdmin, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !isAdmin) {
            router.replace('/dashboard');
        }
    }, [isAdmin, isLoading, router]);

    // Show loading state while checking auth
    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-slate-400">Loading...</div>
            </div>
        );
    }

    // Don't render until we confirm user is admin
    if (!isAdmin) {
        return null;
    }

    return (
        <div className="min-h-screen bg-slate-950">
            <AdminSidebar />
            <DashboardHeader />
            <main className="ml-64 p-6 pt-20">
                {children}
            </main>
        </div>
    );
}
