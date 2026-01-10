import Sidebar from '@/components/layout/Sidebar';

export default function EvidenceLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-slate-950">
            <Sidebar />
            <main className="ml-64">
                {children}
            </main>
        </div>
    );
}
