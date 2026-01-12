import { getGoldenSets } from "@/lib/actions/golden-set";
import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { Database, Calendar, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

export default async function GoldenSetsPage({
    searchParams,
}: {
    searchParams: { page?: string };
}) {
    const t = await getTranslations("Admin");
    const page = Number(searchParams.page) || 1;
    const limit = 20;
    const { data: goldenSets, count } = await getGoldenSets(page, limit);
    const totalPages = Math.ceil(count / limit);

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Golden Sets</h1>
                        <p className="text-sm text-slate-400">자동 생성된 골든 셋 후보군을 관리하고 시드로 승격합니다.</p>
                    </div>
                </div>

                <div className="grid gap-4">
                    {goldenSets.length === 0 ? (
                        <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                            <Database className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-slate-400">생성된 골든 셋이 없습니다.</h3>
                            <p className="text-sm text-slate-500 mt-2">커넥터 관리 페이지에서 Golden Seed 커넥터를 실행해주세요.</p>
                            <Link
                                href="/admin/connectors"
                                className="inline-flex items-center mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
                            >
                                커넥터 관리로 이동
                            </Link>
                        </div>
                    ) : (
                        <>
                            {goldenSets.map((set: any) => (
                                <div key={set.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-lg ${set.status === 'promoted' ? 'bg-green-500/10 text-green-400' :
                                                set.status === 'archived' ? 'bg-slate-800 text-slate-500' :
                                                    'bg-blue-500/10 text-blue-400'
                                                }`}>
                                                <Database className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <h3 className="text-lg font-bold text-white">{set.name}</h3>
                                                    <span className="px-2 py-0.5 text-xs font-medium bg-slate-800 text-slate-300 rounded border border-slate-700">
                                                        {set.version}
                                                    </span>
                                                    {set.status === 'promoted' && (
                                                        <span className="px-2 py-0.5 text-xs font-medium bg-green-900/30 text-green-400 rounded border border-green-800 flex items-center gap-1">
                                                            <CheckCircle2 className="w-3 h-3" /> Promoted
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                                                    <div className="flex items-center gap-1">
                                                        <Calendar className="w-3 h-3" />
                                                        {new Date(set.created_at).toLocaleString()}
                                                    </div>
                                                    <div>•</div>
                                                    <div>
                                                        후보 <span className="text-slate-300 font-medium">{set.candidate_count}</span>개
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <Link
                                            href={`/admin/golden-sets/${set.id}`}
                                            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm transition-colors"
                                        >
                                            상세 보기 <ArrowRight className="w-4 h-4" />
                                        </Link>
                                    </div>
                                </div>
                            ))}

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex justify-center gap-2 mt-8">
                                    {page > 1 && (
                                        <Link
                                            href={`/admin/golden-sets?page=${page - 1}`}
                                            className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
                                        >
                                            이전
                                        </Link>
                                    )}
                                    <span className="px-4 py-2 text-slate-500">
                                        Page {page} of {totalPages}
                                    </span>
                                    {page < totalPages && (
                                        <Link
                                            href={`/admin/golden-sets?page=${page + 1}`}
                                            className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
                                        >
                                            다음
                                        </Link>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
