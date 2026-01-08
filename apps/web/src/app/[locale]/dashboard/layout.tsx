import Sidebar from '@/components/layout/Sidebar';
import DashboardHeader from '@/components/layout/DashboardHeader';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-slate-950">
            <Sidebar />
            <DashboardHeader />
            <main className="ml-64 p-6">
                {children}
            </main>
        </div>
    );
}
