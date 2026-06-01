'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function AdminSidebar() {
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/login');
    };

    return (
        <aside className="admin-sidebar">
            <div className="admin-sidebar-header">
                <h1>VaultMind Admin</h1>
            </div>

            <nav className="admin-nav">
                <div className="nav-section">
                    <h2>Dashboard</h2>
                    <Link href="/admin" className="nav-link">
                        📊 Overview
                    </Link>
                </div>

                <div className="nav-section">
                    <h2>Data Management</h2>
                    <Link href="/admin/ingestion" className="nav-link">
                        📥 Data Ingestion
                    </Link>
                    <Link href="/admin/documents" className="nav-link">
                        📄 Documents
                    </Link>
                </div>

                <div className="nav-section">
                    <h2>Admin Tools</h2>
                    <Link href="/admin/users" className="nav-link">
                        👥 User Management
                    </Link>
                    <Link href="/admin/analytics" className="nav-link">
                        📈 Analytics
                    </Link>
                    <Link href="/admin/search" className="nav-link">
                        🔍 Search Admin DB
                    </Link>
                </div>

                <div className="nav-section">
                    <h2>System</h2>
                    <Link href="/admin/status" className="nav-link">
                        ⚙️ System Status
                    </Link>
                </div>
            </nav>

            <div className="admin-sidebar-footer">
                <button
                    className="logout-btn"
                    onClick={handleLogout}
                >
                    🚪 Logout
                </button>
            </div>
        </aside>
    );
}
