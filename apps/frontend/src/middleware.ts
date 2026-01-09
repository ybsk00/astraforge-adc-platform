import { updateSession } from '@/lib/supabase/middleware';
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { NextRequest, NextResponse } from 'next/server';

const intlMiddleware = createMiddleware(routing);

export async function middleware(request: NextRequest) {
    // Handle i18n first
    const intlResponse = intlMiddleware(request);

    // Then update Supabase session
    const supabaseResponse = await updateSession(request);

    // If Supabase middleware returns a redirect, use it
    if (supabaseResponse.status !== 200) {
        return supabaseResponse;
    }

    return intlResponse;
}

export const config = {
    // Match all pathnames except for
    // - API routes
    // - Static files
    // - _next (Next.js internals)
    matcher: ['/((?!api|_next|.*\\..*).*)'],
};
