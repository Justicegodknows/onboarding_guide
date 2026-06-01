'use client';

import React, { useEffect, useState } from 'react';

interface SystemStatus {
    status: string;
    uptime: string;
    database_status: string;
    vector_store_status: string;
    timestamp: string;
}

export default function StatusPage() {
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No auth token');

                const response = await fetch('/api/backend?endpoint=/api/v1/admin/status', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                if (!response.ok) throw new Error('Failed to fetch status');
                const data = await response.json();
                setStatus(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="loading">Loading system status...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    const getStatusColor = (status: string) => {
        if (status.includes('healthy')) return 'green';
        if (status.includes('error')) return 'red';
        return 'yellow';
    };

    return (
        <div className="status-page">
            <h1>System Status</h1>

            {status && (
                <div className="status-grid">
                    <div className="status-item">
                        <h3>Overall Status</h3>
                        <div className="status-value" style={{ color: getStatusColor(status.status) }}>
                            {status.status}
                        </div>
                    </div>

                    <div className="status-item">
                        <h3>Uptime</h3>
                        <div className="status-value">
                            {status.uptime}
                        </div>
                    </div>

                    <div className="status-item">
                        <h3>Database</h3>
                        <div className="status-value" style={{ color: getStatusColor(status.database_status) }}>
                            {status.database_status}
                        </div>
                    </div>

                    <div className="status-item">
                        <h3>Vector Store</h3>
                        <div className="status-value" style={{ color: getStatusColor(status.vector_store_status) }}>
                            {status.vector_store_status}
                        </div>
                    </div>

                    <div className="status-item full-width">
                        <h3>Last Update</h3>
                        <div className="status-timestamp">
                            {new Date(status.timestamp).toLocaleString()}
                        </div>
                    </div>
                </div>
            )}

            <div className="status-info">
                <h2>Component Details</h2>
                <ul>
                    <li><strong>Database:</strong> PostgreSQL/SQLAlchemy for authentication and admin data</li>
                    <li><strong>Vector Store:</strong> ChromaDB for admin-exclusive document embeddings</li>
                    <li><strong>System:</strong> FastAPI backend with async support</li>
                </ul>
            </div>
        </div>
    );
}
