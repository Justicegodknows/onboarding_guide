'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminDashboard from './components/AdminDashboard';

const AUTH_CHECK_TIMEOUT = 10000; // 10 second timeout

export default function AdminPage() {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    router.push('/login');
                    return;
                }

                // Create abort controller with timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), AUTH_CHECK_TIMEOUT);

                try {
                    const response = await fetch('/api/backend?endpoint=/auth/me', {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                        },
                        signal: controller.signal,
                    });

                    clearTimeout(timeoutId);

                    if (!response.ok) {
                        router.push('/login');
                        return;
                    }

                    const user = await response.json();
                    if (user.role !== 'ADMIN') {
                        router.push('/');
                        return;
                    }

                    setIsAuthenticated(true);
                } catch (err) {
                    clearTimeout(timeoutId);
                    if (err instanceof Error && err.name === 'AbortError') {
                        setError('Auth check timed out. Please try again.');
                        console.error('Auth check timeout');
                    } else {
                        console.error('Auth check failed:', err);
                        router.push('/login');
                    }
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    if (isLoading) {
        return (
            <div className="admin-loading">
                <p>Loading admin panel...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-loading">
                <p style={{ color: 'red' }}>{error}</p>
                <button onClick={() => window.location.reload()} style={{ marginTop: '10px' }}>
                    Retry
                </button>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return <AdminDashboard />;
}
