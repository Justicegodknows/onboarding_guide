'use client';

import React, { useState } from 'react';

export default function IngestionPage() {
    const [source, setSource] = useState('local');
    const [folderPath, setFolderPath] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const handleIngest = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage(null);

        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No auth token');

            const payload: any = { source };
            if (source === 'folder' && folderPath) {
                payload.folder_path = folderPath;
            }

            // Create abort controller with 60 second timeout for ingestion (longer than searches)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            try {
                const response = await fetch('/api/backend?endpoint=/api/v1/admin/ingest', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal,
                });

                const data = await response.json();

                if (response.ok) {
                    setMessage({
                        type: 'success',
                        text: `Ingestion successful! ${data.ingested} chunks ingested.`,
                    });
                    setFolderPath('');
                } else {
                    setMessage({
                        type: 'error',
                        text: data.detail || 'Ingestion failed',
                    });
                }
            } finally {
                clearTimeout(timeoutId);
            }
        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : 'An error occurred';
            if (errorMsg.includes('abort')) {
                setMessage({
                    type: 'error',
                    text: 'Ingestion timed out. Please try again.',
                });
            } else {
                setMessage({
                    type: 'error',
                    text: errorMsg,
                });
            }
            console.error('Ingestion error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="ingestion-page">
            <h1>Data Ingestion</h1>
            <p>Ingest documents into the admin-exclusive database.</p>

            <form onSubmit={handleIngest} className="ingestion-form">
                <div className="form-group">
                    <label>Ingestion Source</label>
                    <select
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        disabled={isLoading}
                    >
                        <option value="local">Local Admin Documentation</option>
                        <option value="folder">Local Folder</option>
                        <option value="direct">Direct Upload</option>
                    </select>
                </div>

                {source === 'folder' && (
                    <div className="form-group">
                        <label>Folder Path</label>
                        <input
                            type="text"
                            placeholder="/path/to/documents"
                            value={folderPath}
                            onChange={(e) => setFolderPath(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isLoading}
                    className="ingest-btn"
                >
                    {isLoading ? 'Ingesting...' : 'Start Ingestion'}
                </button>
            </form>

            {message && (
                <div className={`message message-${message.type}`}>
                    {message.text}
                </div>
            )}

            <div className="ingestion-info">
                <h2>Ingestion Sources</h2>
                <ul>
                    <li><strong>Local:</strong> Pre-configured admin documentation</li>
                    <li><strong>Folder:</strong> Ingest all documents from a specific folder</li>
                    <li><strong>Direct:</strong> Upload documents directly (JSON format)</li>
                </ul>
            </div>
        </div>
    );
}
