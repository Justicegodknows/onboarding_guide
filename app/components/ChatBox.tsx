"use client";
import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api/backend";

interface ChatBoxProps {
    department?: string;
    title?: string;
    onSend?: (question: string, history: string[]) => Promise<{ answer: string }>;
}

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: any[];
}

export default function ChatBox({ department, title, onSend }: ChatBoxProps) {
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
        <div className="w-full max-w-3xl mx-auto mt-8 p-6 border rounded-2xl bg-white shadow-lg dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800">
            <div className="flex items-center gap-2 mb-6 border-b pb-4">
                <span className="text-2xl">🔒</span>
                <h2 className="text-2xl font-extrabold text-primary dark:text-white">{title ?? "Chat with RAG Agent"}</h2>
            </div>

            <div className="space-y-4 mb-6 h-96 overflow-y-auto p-2 rounded-xl bg-zinc-50/70 dark:bg-zinc-950/50 border border-zinc-100 dark:border-zinc-800">
                {messages.length === 0 && (
                    <div className="text-center text-muted py-20">
                        <p className="text-lg font-medium">Welcome to VaultMind</p>
                        <p className="text-sm">Ask any question about company documents.</p>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === "user"
                            ? "bg-primary text-white rounded-br-none"
                            : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100 rounded-bl-none border-l-4 border-accent"
                            }`}>
                            <div className="text-sm whitespace-pre-wrap">{msg.content}</div>

                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-3 pt-2 border-t border-zinc-300 dark:border-zinc-700">
                                    <p className="text-xs font-bold text-accent mb-1 uppercase">Sources:</p>
                                    <div className="grid gap-2">
                                        {msg.sources.map((src, idx) => (
                                            <div key={idx} className="text-[10px] p-2 bg-white dark:bg-zinc-700 rounded-lg border border-zinc-200 dark:border-zinc-600">
                                                <span className="font-bold text-primary dark:text-white">[{idx + 1}] {src.source}</span>
                                                <p className="italic text-zinc-600 dark:text-zinc-400">{src.content}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
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

            <div className="flex gap-2">
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
