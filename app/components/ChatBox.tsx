"use client";
import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api/backend";

interface ChatBoxProps {
    department?: string;
    title?: string;
    onSend?: (question: string, history: string[]) => Promise<{ answer: string }>;
    onClose?: () => void;
}

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: any[];
}

export default function ChatBox({ department, title, onSend, onClose }: ChatBoxProps) {
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [history, setHistory] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (bottomRef.current && typeof bottomRef.current.scrollIntoView === "function") {
            bottomRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, loading]);

    async function handleSend() {
        const currentQuestion = question.trim();
        if (!currentQuestion) return;

        setMessages((prev) => [...prev, { role: "user", content: currentQuestion }]);
        setQuestion("");
        setLoading(true);
        setError(null);

        try {
            const deptQuestion = department ? `[${department}] ${currentQuestion}` : currentQuestion;
            const questionToSend = onSend ? currentQuestion : deptQuestion;
            const token = typeof window !== 'undefined' ? localStorage.getItem('vaultmind_token') ?? undefined : undefined;
            const res = await (onSend
                ? onSend(questionToSend, history)
                : sendChat(questionToSend, history, token));
            setMessages((prev) => [...prev, { role: "assistant", content: res.answer, sources: res.sources }]);
            setHistory((prev) => [...prev, questionToSend]);
        } catch (e: any) {
            setError(e.message || "Failed to fetch response from VaultMind");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="w-screen h-screen flex flex-col bg-white dark:bg-zinc-900">
            <div className="flex items-center justify-between gap-3 px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">🔒</span>
                    <h2 className="text-xl font-bold text-primary dark:text-white">{title ?? "Chat with RAG Agent"}</h2>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors p-2"
                        aria-label="Close chat"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-muted py-20">
                        <p className="text-lg font-medium">Welcome to VaultMind</p>
                        <p className="text-sm">Ask any question about company documents.</p>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} mb-4`}>
                        <div className={`max-w-2xl ${msg.role === "user"
                            ? "bg-primary text-white"
                            : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                            } px-4 py-3 rounded-lg`}>
                            <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-zinc-100 dark:bg-zinc-800 p-3 rounded-lg rounded-bl-none animate-pulse text-sm shadow-sm">
                            VaultMind is searching documents...
                        </div>
                    </div>
                )}
                {error && (
                    <div className="text-center text-red-500 text-xs mt-2 bg-red-50 p-2 rounded border border-red-100">
                        {error}
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <div className="flex gap-3 px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                <input
                    className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent dark:bg-zinc-800 dark:text-white dark:border-zinc-700"
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder={department ? `Ask about ${department}...` : "Type your question..."}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    disabled={loading}
                />
                <button
                    className="bg-primary text-white px-6 py-3 rounded-lg font-bold hover:bg-opacity-90 transition-all disabled:bg-zinc-400"
                    onClick={handleSend}
                    disabled={loading || !question.trim()}
                >
                    Send
                </button>
            </div>
        </div>
    );
}
