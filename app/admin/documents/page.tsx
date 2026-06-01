'use client';

import React, { useEffect, useState } from 'react';

interface Document {
    id: number;
    filename: string;
    uploaded_by: string;
    uploaded_at: string;
    source_type: string;
    chunk_count: number;
    status: string;
}

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDocuments = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No auth token');

                const response = await fetch('/api/backend?endpoint=/api/v1/admin/documents', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                if (!response.ok) throw new Error('Failed to fetch documents');
                const data = await response.json();
                setDocuments(data.documents || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchDocuments();
    }, []);

    if (loading) return <div className="loading">Loading documents...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="documents-page">
            <h1>Admin Documents</h1>

            <div className="documents-stats">
                <p>Total Documents: <strong>{documents.length}</strong></p>
            </div>

            {documents.length === 0 ? (
                <p className="no-data">No documents yet</p>
            ) : (
                <div className="documents-table-container">
                    <table className="documents-table">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Type</th>
                                <th>Uploaded By</th>
                                <th>Date</th>
                                <th>Chunks</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {documents.map((doc) => (
                                <tr key={doc.id}>
                                    <td>{doc.filename}</td>
                                    <td>{doc.source_type}</td>
                                    <td>{doc.uploaded_by}</td>
                                    <td>{new Date(doc.uploaded_at).toLocaleDateString()}</td>
                                    <td>{doc.chunk_count}</td>
                                    <td>
                                        <span className={`status-badge status-${doc.status}`}>
                                            {doc.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
