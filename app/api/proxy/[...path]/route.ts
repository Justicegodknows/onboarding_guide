import { NextRequest, NextResponse } from 'next/server';

const DGX_BACKEND_URL = process.env.DGX_BACKEND_URL || 'http://192.168.18.199:8000';

async function handler(req: NextRequest) {
    try {
        // Extract the path segments from /api/proxy/...
        const segments = req.nextUrl.pathname.replace(/^\/api\/proxy\/?/, '').split('/').filter(Boolean);
        const path = segments.join('/');
        const queryString = req.nextUrl.search;

        // Build the target URL on DGX
        const targetUrl = `${DGX_BACKEND_URL}/${path}${queryString}`;

        // Forward headers (exclude host-related headers to prevent conflicts)
        const headers = new Headers(req.headers);
        headers.delete('host');
        headers.delete('connection');

        // Make the request to DGX backend
        const response = await fetch(targetUrl, {
            method: req.method,
            headers: headers,
            body: req.method !== 'GET' && req.method !== 'HEAD' ? await req.text() : undefined,
        });

        // Read the response body
        const responseBody = await response.arrayBuffer();

        // CORS headers to allow frontend requests
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        };

        // Return the proxied response with CORS headers
        return new NextResponse(responseBody, {
            status: response.status,
            statusText: response.statusText,
            headers: {
                ...Object.fromEntries(response.headers),
                ...corsHeaders,
            },
        });
    } catch (error) {
        console.error('Proxy error:', error);
        return NextResponse.json(
            { error: 'Proxy error', details: String(error) },
            { status: 500 }
        );
    }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const DELETE = handler;
export const PATCH = handler;
export const OPTIONS = handler;
