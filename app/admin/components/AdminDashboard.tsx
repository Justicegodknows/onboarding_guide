'use client';

import React, { useEffect, useState } from 'react';

interface Analytics {
    total_admin_documents: number;
    total_admin_chunks: number;
    recent_ingest_logs: Array<{
        id: number;
        admin_email: string;
        ingest_type: string;
        started_at: string;
        completed_at: string | null;
        total_chunks: number;
        ingested_chunks: number;
        status: string;
    }>;
    admin_user_count: number;
}

interface SystemStatus {
    status: string;
    uptime: string;
    database_status: string;
    vector_store_status: string;
    timestamp: string;
}

export default function AdminDashboard() {
    const [analytics, setAnalytics] = useState<Analytics | null>(null);
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No auth token');

                const [analyticsRes, statusRes] = await Promise.all([
                    fetch('/api/backend?endpoint=/api/v1/admin/analytics', {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                    fetch('/api/backend?endpoint=/api/v1/admin/status', {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                ]);

                if (!analyticsRes.ok || !statusRes.ok) {
                    throw new Error('Failed to fetch dashboard data');
                }

                const analyticsData = await analyticsRes.json();
                const statusData = await statusRes.json();

                setAnalytics(analyticsData);
                setSystemStatus(statusData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return <div className="admin-dashboard-loading">Loading dashboard...</div>;
    }

    if (error) {
        return <div className="admin-dashboard-error">Error: {error}</div>;
    }

    return (
        <div className="admin-dashboard">
            <h1>Admin Dashboard</h1>

            {/* Status Cards */}
            <div className="status-cards">
                {systemStatus && (
                    <>
                        <div className="status-card">
                            <h3>System Status</h3>
                            <p className="status-value">{systemStatus.status}</p>
                            <p className="status-detail">Database: {systemStatus.database_status}</p>
                        </div>
                        <div className="status-card">
                            <h3>Vector Store</h3>
                            <p className="status-value">{systemStatus.vector_store_status}</p>
                            <p className="status-detail">Timestamp: {new Date(systemStatus.timestamp).toLocaleString()}</p>
                        </div>
                    </>
                )}
            </div>

            {/* Analytics Section */}
            {analytics && (
                <div className="analytics-section">
                    <h2>Admin Database Statistics</h2>
                    <div className="analytics-grid">
                        <div className="stat-box">
                            <span className="stat-label">Total Admin Documents</span>
                            <span className="stat-value">{analytics.total_admin_documents}</span>
                        </div>
                        <div className="stat-box">
                            <span className="stat-label">Total Chunks Indexed</span>
                            <span className="stat-value">{analytics.total_admin_chunks}</span>
                        </div>
                        <div className="stat-box">
                            <span className="stat-label">Active Admin Users</span>
                            <span className="stat-value">{analytics.admin_user_count}</span>
                        </div>
                    </div>

                    {/* Recent Ingest Logs */}
                    <div className="ingest-logs">
                        <h3>Recent Ingestion Activity</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Date</th>
                                    <th>Chunks</th>
                                    <th>Ingested</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.recent_ingest_logs.map((log) => (
                                    <tr key={log.id}>
                                        <td>{log.ingest_type}</td>
                                        <td>{new Date(log.started_at).toLocaleString()}</td>
                                        <td>{log.total_chunks}</td>
                                        <td>{log.ingested_chunks}</td>
                                        <td>
                                            <span className={`status-badge status-${log.status}`}>
                                                {log.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
