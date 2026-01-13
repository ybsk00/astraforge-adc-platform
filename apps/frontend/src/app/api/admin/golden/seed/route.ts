import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const targets = body.targets || [];
        const limit = body.limit || 30;

        if (!targets.length) {
            return NextResponse.json(
                { detail: 'At least one target is required' },
                { status: 400 }
            );
        }

        const supabase = await createClient();

        // Insert job into golden_seed_runs table
        const { data, error } = await supabase
            .from('golden_seed_runs')
            .insert({
                status: 'queued',
                config: {
                    targets: targets,
                    per_target_limit: limit,
                    mode: 'target_only'
                }
            })
            .select()
            .single();

        if (error) {
            console.error('Supabase insert error:', error);
            return NextResponse.json(
                { detail: error.message },
                { status: 500 }
            );
        }

        return NextResponse.json({
            status: 'accepted',
            run_id: data.id,
            message: `Job queued for ${targets.length} targets. Local worker will process it.`
        });

    } catch (error: any) {
        console.error('API error:', error);
        return NextResponse.json(
            { detail: 'Failed to queue job' },
            { status: 500 }
        );
    }
}
