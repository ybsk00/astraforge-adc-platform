"use client";

import { useState } from "react";
import { promoteGoldenSet } from "@/lib/actions/golden-set";
import { Rocket, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface Props {
    goldenSetId: string;
    defaultName: string;
}

export default function PromoteButton({ goldenSetId, defaultName }: Props) {
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handlePromote = async () => {
        if (!confirm("승인된(Approved) 후보들만 정식 시드로 승격됩니다.\n계속하시겠습니까?")) return;

        setLoading(true);
        try {
            const result = await promoteGoldenSet(goldenSetId, defaultName);
            toast.success("시드 승격이 완료되었습니다!");
            console.log("Promotion Result:", result);
            router.refresh();
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error(`승격 실패: ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handlePromote}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20"
        >
            {loading ? (
                <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    처리 중...
                </>
            ) : (
                <>
                    <Rocket className="w-4 h-4" />
                    시드로 승격 (Promote)
                </>
            )}
        </button>
    );
}
