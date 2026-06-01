"use client";
import { useState, useRef, useEffect } from "react";
import { sendTrainerChat, uploadTrainerDocument } from "../api/backend";

interface Message {
    role: "user" | "trainer";
    text: string;
}

interface AttachedDoc {
    filename: string;
    text: string;
    truncated: boolean;
}

interface TrainerChatBoxProps {
    title?: string;
    onSend?: (question: string, history: string[]) => Promise<{ answer: string }>;
}

export default function TrainerChatBox({ title, onSend }: TrainerChatBoxProps) {
    const [open, setOpen] = useState(false);
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [history, setHistory] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [attachedDoc, setAttachedDoc] = useState<AttachedDoc | null>(null);
    const [uploadLoading, setUploadLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (open) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, open]);

    async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploadLoading(true);
        setError(null);
        try {
            const result = await uploadTrainerDocument(file);
            setAttachedDoc({ filename: result.filename, text: result.text, truncated: result.truncated });
        } catch (err: any) {
            setError(err.message);
        } finally {
            setUploadLoading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    }

    async function handleSend() {
        const question = input.trim();
        if (!question) return;
        setInput("");
        setError(null);

        // Build the question shown in chat (always just the user's text)
        setMessages((prev) => [...prev, { role: "user", text: question }]);

        // Build the actual payload: prepend document context if attached
        let payload = question;
        if (attachedDoc) {
            payload =
                `[Attached document: ${attachedDoc.filename}${attachedDoc.truncated ? " (truncated)" : ""}]\n\n` +
                `${attachedDoc.text}\n\n---\n\n${question}`;
            setAttachedDoc(null);
        }

        setLoading(true);
        try {
            const token = typeof window !== "undefined" ? localStorage.getItem("vaultmind_token") ?? undefined : undefined;
            const res = await (onSend
                ? onSend(payload, history)
                : sendTrainerChat(payload, history, token));
            const answer: string = res.answer;
            setMessages((prev) => [...prev, { role: "trainer", text: answer }]);
            setHistory((prev) => [...prev, payload]);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!loading && input.trim()) handleSend();
        }
    }

    return (
        <div className="mt-auto border-t border-gray-200 pt-3">
            <button
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-800 text-sm font-semibold transition-colors border border-blue-200"
                onClick={() => setOpen((v) => !v)}
            >
                <span>{title ?? "🎓 Trainer Assistant"}</span>
                <span className="text-xs text-blue-500">{open ? "▲" : "▼"}</span>
            </button>

            {open && (
                <div className="flex flex-col mt-2 gap-2">
                    <div className="h-48 overflow-y-auto rounded-xl border border-gray-200 bg-white p-2 flex flex-col gap-2 text-xs">
                        {messages.length === 0 && (
                            <p className="text-gray-400 italic">Ask the trainer anything…</p>
                        )}
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`rounded-xl px-2 py-1 max-w-[90%] whitespace-pre-wrap ${msg.role === "user"
                                    ? "self-end bg-blue-600 text-white"
                                    : "self-start bg-blue-50 text-gray-800 border border-blue-100"
                                    }`}
                            >
                                {msg.text}
                            </div>
                        ))}
                        {loading && (
                            <div className="self-start bg-blue-50 border border-blue-100 rounded-xl px-2 py-1 text-gray-400 italic">
                                Thinking…
                            </div>
                        )}
                        {error && (
                            <div className="self-start bg-red-50 text-red-700 rounded-xl px-2 py-1 border border-red-200">
                                {error}
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    {attachedDoc && (
                        <div className="flex items-center gap-1 text-xs bg-green-50 border border-green-200 rounded-lg px-2 py-1">
                            <span className="text-green-700 truncate flex-1">
                                📄 {attachedDoc.filename}{attachedDoc.truncated ? " (truncated)" : ""}
                            </span>
                            <button
                                className="text-green-500 hover:text-red-500 font-bold ml-1"
                                onClick={() => setAttachedDoc(null)}
                                title="Remove attachment"
                            >
                                ✕
                            </button>
                        </div>
                    )}

                    <div className="flex gap-1">
                        <input
                            ref={fileInputRef}
                            type="file"
                            className="hidden"
                            onChange={handleFileChange}
                            disabled={loading || uploadLoading}
                        />
                        <button
                            className="px-2 py-1 rounded-lg border border-gray-200 bg-white text-gray-500 text-xs hover:bg-gray-50 disabled:opacity-40 transition-colors"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={loading || uploadLoading}
                            title="Attach a document (PDF, DOCX, TXT, MD, CSV)"
                        >
                            {uploadLoading ? "…" : "📎"}
                        </button>
                        <input
                            className="flex-1 text-xs p-1.5 border border-gray-200 rounded-lg bg-white text-gray-900 focus:outline-none focus:border-blue-400"
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask the trainer…"
                            disabled={loading}
                        />
                        <button
                            className="px-2 py-1 rounded-lg bg-blue-600 text-white text-xs hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                        >
                            Send
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
