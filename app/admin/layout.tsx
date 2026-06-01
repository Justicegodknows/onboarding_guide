import React from 'react';
import AdminSidebar from './components/AdminSidebar';
import './admin.css';

export const metadata = {
    title: 'Admin Dashboard - VaultMind',
    description: 'Administrative control panel for VaultMind system',
};

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="admin-layout">
            <AdminSidebar />
            <main className="admin-main-content">
                {children}
            </main>
        </div>
    );
}
