import { getGoldenSetById } from "@/lib/actions/golden-set";
import Link from "next/link";
import { ArrowLeft, Database, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import GoldenCandidateList from "@/components/admin/GoldenCandidateList";
import PromoteButton from "@/components/admin/PromoteButton";

export default async function GoldenSetDetailPage({ params }: { params: { id: string } }) {
    const goldenSet = await getGoldenSetById(params.id);

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/admin/golden-sets"
                            className="p-2 hover:bg-slate-900 rounded-lg text-slate-400 transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-2xl font-bold text-white">{goldenSet.name}</h1>
                                <span className="px-2 py-0.5 text-xs font-medium bg-slate-800 text-slate-300 rounded border border-slate-700">
                                    {goldenSet.version}
                                </span>
                                {goldenSet.status === 'promoted' && (
                                    <span className="px-2 py-0.5 text-xs font-medium bg-green-900/30 text-green-400 rounded border border-green-800 flex items-center gap-1">
                                        <CheckCircle2 className="w-3 h-3" /> Promoted
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-slate-400 mt-1">
                                생성일: {new Date(goldenSet.created_at).toLocaleString()}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {goldenSet.status !== 'promoted' && (
                            <PromoteButton
                                goldenSetId={goldenSet.id}
                                defaultName={`${goldenSet.name.replace('GOLDEN', 'SEED')}_${new Date().toISOString().slice(0, 10)}`}
                            />
                        )}
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-500 mb-1">총 후보 수</p>
                        <p className="text-2xl font-bold text-white">{goldenSet.candidates.length}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-500 mb-1">승인됨 (Approved)</p>
                        <p className="text-2xl font-bold text-green-400">
                            {goldenSet.candidates.filter(c => c.review_status === 'approved').length}
                        </p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-500 mb-1">거절됨 (Rejected)</p>
                        <p className="text-2xl font-bold text-red-400">
                            {goldenSet.candidates.filter(c => c.review_status === 'rejected').length}
                        </p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-500 mb-1">대기 중 (Pending)</p>
                        <p className="text-2xl font-bold text-amber-400">
                            {goldenSet.candidates.filter(c => c.review_status === 'pending').length}
                        </p>
                    </div>
                </div>

                {/* Candidate List Component */}
                <GoldenCandidateList candidates={goldenSet.candidates} />
            </div>
        </div>
    );
}
