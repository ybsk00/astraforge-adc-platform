import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * Review Queue 제안 승인 API
 * POST /api/admin/golden/review/approve
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const reviewId = body.review_id;
        const approvedBy = body.approved_by || 'admin';
        const comment = body.comment || '';

        if (!reviewId) {
            return NextResponse.json(
                { detail: 'review_id is required' },
                { status: 400 }
            );
        }

        const supabase = await createClient();

        // 1. Review 조회
        const { data: review, error: fetchError } = await supabase
            .from('golden_review_queue')
            .select('*, golden_seed_items(*)')
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

        const seedItem = review.golden_seed_items;
        const proposedPatch = review.proposed_patch;

        // 2. Verified 체크 (필드별)
        const fieldVerified = seedItem?.field_verified || {};
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const updateData: Record<string, any> = {};
        const skippedFields: string[] = [];

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        for (const [field, patchInfo] of Object.entries(proposedPatch) as [string, any][]) {
            if (field.startsWith('_')) continue; // 메타 필드 스킵

            // 필드별 Verified 체크
            if (fieldVerified[field] === true) {
                // Verified 필드는 스킵 (자동 overwrite 금지)
                skippedFields.push(field);
                continue;
            }

            // 업데이트 데이터 준비
            updateData[field] = patchInfo.new;
        }

        // 3. Seed Item 업데이트 (스킵된 필드 제외)
        if (Object.keys(updateData).length > 0 && seedItem) {
            updateData.updated_at = new Date().toISOString();

            await supabase
                .from('golden_seed_items')
                .update(updateData)
                .eq('id', seedItem.id);
        }

        // 4. Review 상태 업데이트
        await supabase
            .from('golden_review_queue')
            .update({
                status: 'approved',
                reviewed_by: approvedBy,
                reviewed_at: new Date().toISOString(),
                review_notes: comment + (skippedFields.length > 0
                    ? ` [Skipped verified fields: ${skippedFields.join(', ')}]`
                    : '')
            })
            .eq('id', reviewId);

        return NextResponse.json({
            status: 'approved',
            updated_fields: Object.keys(updateData),
            skipped_verified_fields: skippedFields
        });

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
        console.error('Review approve error:', error);
        return NextResponse.json(
            { status: 'error', detail: error.message },
            { status: 500 }
        );
    }
}
