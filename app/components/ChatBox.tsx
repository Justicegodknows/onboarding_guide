"use client";
import { useEffect, useRef, useState } from "react";
import { sendAgentChat, sendChat } from "../api/backend";

interface ChatBoxProps {
    department?: string;
    title?: string;
    onSend?: (question: string, history: string[]) => Promise<{ answer: string }>;
    onClose?: () => void;
    fullPage?: boolean;
    agentMode?: boolean;
}

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: any[];
}

import Link from "next/link";

export default function ChatBox({ department, title, onSend, onClose, fullPage = false, agentMode = false }: ChatBoxProps) {
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
                : (
                    agentMode
                        ? sendAgentChat(questionToSend, null, token)
                        : sendChat(questionToSend, history, token)
                ));
            setMessages((prev) => [...prev, { role: "assistant", content: res.answer, sources: res.sources }]);
            setHistory((prev) => [...prev, questionToSend]);
        } catch (e: any) {
            setError(e.message || "Failed to fetch response from VaultMind");
        } finally {
            setLoading(false);
        }
    }

    const containerClasses = fullPage
        ? "min-h-screen h-screen w-screen"
        : "h-full min-h-[32rem] w-full rounded-[1.75rem] border border-gray-200 bg-white shadow-sm";

    return (
        <div className={`flex flex-col bg-white ${containerClasses}`}>
            {/* Header */}
            <div className="flex items-center justify-between gap-3 px-6 py-4 border-b border-gray-200 bg-white">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">🔒</span>
                    <h2 className="text-xl font-bold text-gray-900">{title ?? "Chat with RAG Agent"}</h2>
                </div>
                {!agentMode && (
                    <Link
                        href="/nemoclaw"
                        className="flex items-center gap-2 text-xs text-blue-600 hover:text-blue-800 mr-2 px-3 py-1 border border-blue-600 rounded-full hover:bg-blue-50 transition-colors"
                    >
                        <span>⚖️</span>
                        Nemoclaw Mode
                    </Link>
                )}
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-700 transition-colors p-2"
                        aria-label="Close chat"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-white">
                {messages.length === 0 && (
                    <div className="text-center py-20">
                        <p className="text-lg font-medium text-gray-800">Welcome to VaultMind</p>
                        <p className="text-sm text-gray-500 mt-1">Ask any question about company documents.</p>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} mb-4`}>
                        <div className={`max-w-2xl px-5 py-4 rounded-3xl shadow-sm ${msg.role === "user"
                            ? "bg-blue-700 text-white"
                            : "bg-blue-50 text-gray-900 border border-blue-100"
                            }`}
                        >
                            <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-blue-50 border border-blue-100 p-3 rounded-3xl animate-pulse text-sm shadow-sm text-gray-600">
                            VaultMind is searching documents...
                        </div>
                    </div>
                )}
                {error && (
                    <div className="text-center text-red-600 text-xs mt-2 bg-red-50 p-2 rounded border border-red-200">
                        {error}
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="flex flex-col gap-3 px-6 py-4 border-t border-gray-200 bg-white sm:flex-row">
                <input
                    className="flex-1 rounded-3xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder={department ? `Ask about ${department}...` : "Type your question..."}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    disabled={loading}
                />
                <button
                    className="inline-flex items-center justify-center rounded-3xl bg-blue-700 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    onClick={handleSend}
                    disabled={loading || !question.trim()}
                >
                    Send
                </button>
            </div>
        </div>
    );
}
