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

export default function AnalyticsPage() {
    const [analytics, setAnalytics] = useState<Analytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No auth token');

                const response = await fetch('/api/backend?endpoint=/api/v1/admin/analytics', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                if (!response.ok) throw new Error('Failed to fetch analytics');
                const data = await response.json();
                setAnalytics(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    if (loading) return <div className="loading">Loading analytics...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="analytics-page">
            <h1>Analytics Dashboard</h1>

            {analytics && (
                <>
                    <div className="analytics-grid">
                        <div className="analytics-card">
                            <h3>Total Admin Documents</h3>
                            <p className="big-number">{analytics.total_admin_documents}</p>
                        </div>
                        <div className="analytics-card">
                            <h3>Total Chunks Indexed</h3>
                            <p className="big-number">{analytics.total_admin_chunks}</p>
                        </div>
                        <div className="analytics-card">
                            <h3>Active Admin Users</h3>
                            <p className="big-number">{analytics.admin_user_count}</p>
                        </div>
                        <div className="analytics-card">
                            <h3>Recent Ingestions</h3>
                            <p className="big-number">{analytics.recent_ingest_logs.length}</p>
                        </div>
                    </div>

                    <div className="ingest-logs-section">
                        <h2>Recent Ingestion Logs</h2>
                        <table className="logs-table">
                            <thead>
                                <tr>
                                    <th>Admin</th>
                                    <th>Type</th>
                                    <th>Started</th>
                                    <th>Total Chunks</th>
                                    <th>Ingested</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.recent_ingest_logs.map((log) => (
                                    <tr key={log.id}>
                                        <td>{log.admin_email}</td>
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
                </>
            )}
        </div>
    );
}
