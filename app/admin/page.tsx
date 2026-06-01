'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminDashboard from './components/AdminDashboard';

export default function AdminPage() {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    router.push('/login');
                    return;
                }

                // Verify admin role
                const response = await fetch('/api/backend?endpoint=/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });

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

    if (!isAuthenticated) {
        return null;
    }

    return <AdminDashboard />;
}
