import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * Review Queue 제안 거절 API
 * POST /api/admin/golden/review/reject
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const reviewId = body.review_id;
        const rejectedBy = body.rejected_by || 'admin';
        const comment = body.comment || '';

        if (!reviewId) {
            return NextResponse.json(
                { detail: 'review_id is required' },
                { status: 400 }
            );
        }

        const supabase = await createClient();

        // 1. Review 상태 확인
        const { data: review, error: fetchError } = await supabase
            .from('golden_review_queue')
            .select('status')
            .eq('id', reviewId)
            .single();

        if (fetchError || !review) {
            return NextResponse.json(
                { detail: 'Review not found' },
                { status: 404 }
            );
        }

        if (review.status !== 'pending') {
            return NextResponse.json(
                { detail: `Review already ${review.status}` },
                { status: 400 }
            );
        }

        // 2. Review 상태 업데이트 (rejected)
        await supabase
            .from('golden_review_queue')
            .update({
                status: 'rejected',
                reviewed_by: rejectedBy,
                reviewed_at: new Date().toISOString(),
                review_notes: comment
            })
            .eq('id', reviewId);

        return NextResponse.json({
            status: 'rejected',
            review_id: reviewId
        });

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
        console.error('Review reject error:', error);
        return NextResponse.json(
            { status: 'error', detail: error.message },
            { status: 500 }
        );
    }
}
