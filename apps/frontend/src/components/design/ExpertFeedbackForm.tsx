"use client";

/**
 * 전문가 피드백 입력 폼
 */
import { useState } from "react";

interface ExpertFeedbackFormProps {
    candidateId: string;
    onSuccess?: () => void;
}

export default function ExpertFeedbackForm({ candidateId, onSuccess }: ExpertFeedbackFormProps) {
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState("");
    const [isGold, setIsGold] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (rating === 0) {
            alert("평점을 선택해주세요.");
            return;
        }

        setSubmitting(true);
        try {
            const res = await fetch(`${ENGINE_URL}/api/v1/design/candidates/${candidateId}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    rating,
                    comment,
                    is_gold_standard: isGold
                })
            });

            if (res.ok) {
                setComment("");
                setRating(0);
                setIsGold(false);
                onSuccess?.();
                alert("피드백이 저장되었습니다.");
            }
        } catch (error) {
            console.error("Failed to submit feedback:", error);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-4">
            <h4 className="text-sm font-bold text-gray-200">전문가 피드백</h4>

            {/* Rating */}
            <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">평점:</span>
                <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            type="button"
                            onClick={() => setRating(star)}
                            className={`text-xl transition-all ${rating >= star ? "text-yellow-400" : "text-gray-600"
                                }`}
                        >
                            ★
                        </button>
                    ))}
                </div>
            </div>

            {/* Comment */}
            <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="후보 물질에 대한 전문가 의견을 입력하세요..."
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm text-gray-200 focus:border-blue-500 outline-none h-24"
            />

            {/* Gold Standard Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    checked={isGold}
                    onChange={(e) => setIsGold(e.target.checked)}
                    className="accent-blue-500"
                />
                <span className="text-xs text-gray-400">Golden Set으로 지정 (추후 학습용)</span>
            </label>

            {/* Submit */}
            <button
                type="submit"
                disabled={submitting}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-sm font-bold transition-all"
            >
                {submitting ? "저장 중..." : "피드백 제출"}
            </button>
        </form>
    );
}
