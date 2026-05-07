"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
    deleteDocument,
    listDocuments,
    reingestDocument,
    uploadDocument,
    type UploadedDocument,
    type UploadResult,
} from "../api/backend";

const ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/csv",
];
const ALLOWED_EXT_LABEL = ".pdf, .docx, .txt, .md, .csv";

interface UploadEntry {
    file: File;
    status: "pending" | "uploading" | "done" | "error";
    result?: UploadResult;
    error?: string;
}

interface DocumentUploadPanelProps {
    token: string;
    isAdmin?: boolean;
}

export default function DocumentUploadPanel({ token, isAdmin = false }: DocumentUploadPanelProps) {
    const [queue, setQueue] = useState<UploadEntry[]>([]);
    const [documents, setDocuments] = useState<UploadedDocument[]>([]);
    const [loadingDocs, setLoadingDocs] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const fetchDocuments = useCallback(async () => {
        if (!token) return;
        setLoadingDocs(true);
        try {
            const docs = await listDocuments(token);
            setDocuments(docs);
        } catch {
            // non-critical — table stays empty
        } finally {
            setLoadingDocs(false);
        }
    }, [token]);

    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    const enqueueFiles = (files: FileList | File[]) => {
        const arr = Array.from(files);
        const valid = arr.filter((f) => ALLOWED_TYPES.includes(f.type) || f.name.match(/\.(pdf|docx|txt|md|csv)$/i));
        if (valid.length === 0) return;
        setQueue((prev) => [
            ...prev,
            ...valid.map((f) => ({ file: f, status: "pending" as const })),
        ]);
        valid.forEach((f) => processUpload(f));
    };

    const processUpload = async (file: File) => {
        setQueue((prev) =>
            prev.map((e) => (e.file === file ? { ...e, status: "uploading" } : e)),
        );
        try {
            const result = await uploadDocument(file, token);
            setQueue((prev) =>
                prev.map((e) => (e.file === file ? { ...e, status: "done", result } : e)),
            );
            // Refresh the documents list
            await fetchDocuments();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setQueue((prev) =>
                prev.map((e) => (e.file === file ? { ...e, status: "error", error: message } : e)),
            );
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        enqueueFiles(e.dataTransfer.files);
    };

    const handleDelete = async (docId: number) => {
        if (!isAdmin) return;
        try {
            await deleteDocument(docId, token);
            setDocuments((prev) => prev.filter((d) => d.id !== docId));
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Delete failed");
        }
    };

    const handleReingest = async (docId: number) => {
        if (!isAdmin) return;
        try {
            await reingestDocument(docId, token);
            alert("Re-ingestion triggered successfully.");
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Re-ingest failed");
        }
    };

    return (
        <div className="flex flex-col gap-6">
            {/* Drop Zone */}
            <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 cursor-pointer transition-colors select-none
          ${isDragging
                        ? "border-accent bg-cyan-50 dark:bg-cyan-950/20"
                        : "border-zinc-300 dark:border-zinc-700 hover:border-accent hover:bg-zinc-50 dark:hover:bg-zinc-900/40"
                    }`}
            >
                <input
                    ref={inputRef}
                    type="file"
                    multiple
                    accept=".pdf,.docx,.txt,.md,.csv"
                    className="sr-only"
                    title="Upload documents"
                    aria-label="Upload documents"
                    onChange={(e) => e.target.files && enqueueFiles(e.target.files)}
                />
                <svg className="w-10 h-10 text-zinc-400 mb-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                    Drag &amp; drop files here, or <span className="text-accent underline">browse</span>
                </p>
                <p className="text-xs text-zinc-400 mt-1">Supported: {ALLOWED_EXT_LABEL} · Max 50 MB</p>
            </div>

            {/* Upload Queue */}
            {queue.length > 0 && (
                <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-bold text-zinc-600 dark:text-zinc-400 uppercase tracking-wide">Upload Queue</h3>
                    {queue.map((entry, i) => (
                        <div
                            key={i}
                            className="flex items-center justify-between rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-4 py-3 text-sm"
                        >
                            <div className="flex items-center gap-3 min-w-0">
                                <FileIcon ext={entry.file.name.split(".").pop() ?? ""} />
                                <span className="truncate font-medium text-zinc-800 dark:text-zinc-100">{entry.file.name}</span>
                                <span className="text-xs text-zinc-400 shrink-0">{(entry.file.size / 1024).toFixed(1)} KB</span>
                            </div>
                            <StatusBadge entry={entry} />
                        </div>
                    ))}
                    <button
                        onClick={() => setQueue([])}
                        className="text-xs text-zinc-400 hover:text-zinc-600 self-end mt-1 underline"
                    >
                        Clear queue
                    </button>
                </div>
            )}

            {/* Documents Table */}
            <div>
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-bold text-zinc-600 dark:text-zinc-400 uppercase tracking-wide">
                        Uploaded Documents
                    </h3>
                    <button
                        onClick={fetchDocuments}
                        className="text-xs text-accent hover:underline"
                    >
                        {loadingDocs ? "Refreshing…" : "Refresh"}
                    </button>
                </div>

                {documents.length === 0 ? (
                    <p className="text-sm text-zinc-400 italic">No documents uploaded yet.</p>
                ) : (
                    <div className="overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-700">
                        <table className="w-full text-sm">
                            <thead className="bg-zinc-50 dark:bg-zinc-800 text-zinc-500 text-xs uppercase tracking-wide">
                                <tr>
                                    <th className="px-4 py-2 text-left">Filename</th>
                                    <th className="px-4 py-2 text-left">Uploaded</th>
                                    {isAdmin && <th className="px-4 py-2 text-right">Actions</th>}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                                {documents.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                                        <td className="px-4 py-3 font-medium text-zinc-800 dark:text-zinc-100 max-w-xs truncate">
                                            {doc.filename}
                                        </td>
                                        <td className="px-4 py-3 text-zinc-400">{doc.uploaded_at ?? "—"}</td>
                                        {isAdmin && (
                                            <td className="px-4 py-3 text-right flex justify-end gap-2">
                                                <button
                                                    onClick={() => handleReingest(doc.id)}
                                                    className="px-2 py-1 text-xs rounded-lg bg-cyan-50 text-cyan-700 hover:bg-cyan-100 border border-cyan-200 transition-colors"
                                                >
                                                    Re-ingest
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(doc.id)}
                                                    className="px-2 py-1 text-xs rounded-lg bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 transition-colors"
                                                >
                                                    Delete
                                                </button>
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Small sub-components
// ---------------------------------------------------------------------------

function FileIcon({ ext }: { ext: string }) {
    const colors: Record<string, string> = {
        pdf: "text-red-500",
        docx: "text-blue-500",
        txt: "text-zinc-500",
        md: "text-purple-500",
        csv: "text-green-500",
    };
    return (
        <span className={`text-xs font-bold uppercase ${colors[ext.toLowerCase()] ?? "text-zinc-400"}`}>
            {ext}
        </span>
    );
}

function StatusBadge({ entry }: { entry: UploadEntry }) {
    if (entry.status === "pending") return <span className="text-zinc-400 text-xs">Waiting…</span>;
    if (entry.status === "uploading")
        return (
            <span className="flex items-center gap-1 text-xs text-cyan-600">
                <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Uploading…
            </span>
        );
    if (entry.status === "done")
        return (
            <span className="flex items-center gap-1 text-xs text-green-600">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
                </svg>
                {entry.result?.chunks_added ?? 0} chunks
            </span>
        );
    return <span className="text-xs text-red-500 max-w-xs truncate">{entry.error}</span>;
}
