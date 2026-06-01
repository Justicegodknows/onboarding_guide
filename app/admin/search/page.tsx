'use client';

import React, { useState } from 'react';

interface SearchResult {
    content: string;
    metadata: Record<string, any>;
    score: number;
    source_db: string;
}

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [searchMode, setSearchMode] = useState<'admin-only' | 'dual'>('dual');
    const [results, setResults] = useState<{ main: SearchResult[]; admin: SearchResult[] } | SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No auth token');

            const endpoint = searchMode === 'admin-only'
                ? '/api/v1/admin/search/admin-only'
                : '/api/v1/admin/search/dual';

            // Create abort controller with 30 second timeout for searches
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);

            try {
                const response = await fetch(
                    `/api/backend?endpoint=${endpoint}&query=${encodeURIComponent(query)}&top_k=10`,
                    {
                        headers: { 'Authorization': `Bearer ${token}` },
                        signal: controller.signal,
                    }
                );

                if (!response.ok) throw new Error('Search failed');
                const data = await response.json();
                setResults(data.results);
            } finally {
                clearTimeout(timeoutId);
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Search error';
            if (errorMsg.includes('abort')) {
                setError('Search timed out. Please try a simpler query.');
            } else {
                setError(errorMsg);
            }
            console.error('Search error:', err);
        } finally {
            setLoading(false);
        }
    };

    const isAdminOnlyResults = (results: any): results is SearchResult[] => {
        return Array.isArray(results);
    };

    const isDualResults = (results: any): results is { main: SearchResult[]; admin: SearchResult[] } => {
        return results && 'main' in results && 'admin' in results;
    };

    return (
        <div className="search-page">
            <h1>Search Admin Database</h1>

            <form onSubmit={handleSearch} className="search-form">
                <div className="search-controls">
                    <div className="form-group">
                        <input
                            type="text"
                            placeholder="Enter search query..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label>
                            <input
                                type="radio"
                                value="admin-only"
                                checked={searchMode === 'admin-only'}
                                onChange={(e) => setSearchMode(e.target.value as 'admin-only')}
                                disabled={loading}
                            />
                            Admin Only
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="dual"
                                checked={searchMode === 'dual'}
                                onChange={(e) => setSearchMode(e.target.value as 'dual')}
                                disabled={loading}
                            />
                            Both Databases
                        </label>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="search-btn"
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </form>

            {error && <div className="error-message">{error}</div>}

            {results && (
                <div className="search-results">
                    {isAdminOnlyResults(results) && (
                        <div>
                            <h2>Results ({results.length})</h2>
                            {results.length === 0 ? (
                                <p>No results found</p>
                            ) : (
                                <div className="results-list">
                                    {results.map((result, idx) => (
                                        <div key={idx} className="result-item">
                                            <div className="result-score">Relevance: {(result.score * 100).toFixed(1)}%</div>
                                            <p className="result-content">{result.content.substring(0, 300)}...</p>
                                            {result.metadata && (
                                                <div className="result-metadata">
                                                    <small>{JSON.stringify(result.metadata).substring(0, 100)}...</small>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {isDualResults(results) && (
                        <div>
                            <div className="dual-results">
                                <div className="results-section">
                                    <h2>Main Database ({results.main.length})</h2>
                                    {results.main.length === 0 ? (
                                        <p>No results</p>
                                    ) : (
                                        <div className="results-list">
                                            {results.main.map((result, idx) => (
                                                <div key={idx} className="result-item main-result">
                                                    <div className="result-score">Relevance: {(result.score * 100).toFixed(1)}%</div>
                                                    <p className="result-content">{result.content.substring(0, 250)}...</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <div className="results-section">
                                    <h2>Admin Database ({results.admin.length})</h2>
                                    {results.admin.length === 0 ? (
                                        <p>No results</p>
                                    ) : (
                                        <div className="results-list">
                                            {results.admin.map((result, idx) => (
                                                <div key={idx} className="result-item admin-result">
                                                    <div className="result-score">Relevance: {(result.score * 100).toFixed(1)}%</div>
                                                    <p className="result-content">{result.content.substring(0, 250)}...</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
