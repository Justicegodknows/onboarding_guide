"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DocumentUploadPanel from "../components/DocumentUploadPanel";

export default function DocumentsPage() {
    const [token, setToken] = useState<string | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem("vaultmind_token");
        const storedRole = localStorage.getItem("vaultmind_role");
        setToken(stored);
        setRole(storedRole);
    }, []);

    if (!mounted) return null;

    if (!token) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-white px-6">
                <div className="max-w-sm w-full bg-white border border-gray-200 rounded-2xl p-8 shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">Sign in required</h1>
                    <p className="text-gray-500 text-sm mb-6">You must be signed in to upload documents.</p>
                    <Link
                        href="/"
                        className="inline-block px-6 py-2.5 bg-blue-700 text-white rounded-full font-semibold hover:bg-blue-800 transition"
                    >
                        Go to Home
                    </Link>
                </div>
            </main>
        );
    }

    const isAdmin = role === "ADMIN";

    return (
        <main className="min-h-screen bg-white text-gray-900 px-6 py-12">
            <div className="max-w-4xl mx-auto space-y-8">
                <header className="space-y-2">
                    <Link href="/" className="inline-block text-sm font-semibold text-blue-600 hover:text-blue-800 hover:underline mb-2">
                        ← Back to Home
                    </Link>
                    <h1 className="text-4xl font-extrabold text-gray-900">Document Ingestion</h1>
                    <p className="text-gray-500 text-sm">
                        Upload company documents. Each file is automatically chunked and embedded into the VaultMind knowledge base.
                        {!isAdmin && " Contact an admin to delete or re-ingest documents."}
                    </p>
                </header>

                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                    <DocumentUploadPanel token={token} isAdmin={isAdmin} />
                </div>

                <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5 text-sm text-blue-900 space-y-1">
                    <p className="font-bold">How it works</p>
                    <ul className="list-disc pl-5 space-y-1 text-gray-700">
                        <li>Files are stored securely in the VaultMind uploads directory.</li>
                        <li>PyMuPDF parses PDFs; python-docx handles Word files; plain text is read directly.</li>
                        <li>Content is split into 1 000-character chunks with 100-character overlaps.</li>
                        <li>Each chunk is embedded using the configured NVIDIA NIM embedding model and stored in ChromaDB.</li>
                        <li>The RAG chat assistant can immediately query the new documents.</li>
                    </ul>
                </div>
            </div>
        </main>
    );
}
