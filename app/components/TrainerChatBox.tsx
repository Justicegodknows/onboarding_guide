"use client";
import { useState, useRef, useEffect } from "react";
import { sendTrainerChat } from "../api/backend";

interface Message {
    role: "user" | "trainer";
    text: string;
}

export default function TrainerChatBox() {
    const [open, setOpen] = useState(false);
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [history, setHistory] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (open) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, open]);

    async function handleSend() {
        const question = input.trim();
        if (!question) return;
        setInput("");
        setError(null);
        setMessages((prev) => [...prev, { role: "user", text: question }]);
        setLoading(true);
        try {
            const res = await sendTrainerChat(question, history);
            const answer: string = res.answer;
            setMessages((prev) => [...prev, { role: "trainer", text: answer }]);
            setHistory((prev) => [...prev, question]);
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
        <div className="mt-auto border-t pt-3">
            <button
                className="w-full flex items-center justify-between px-3 py-2 rounded bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 text-sm font-semibold transition-colors"
                onClick={() => setOpen((v) => !v)}
            >
                <span>🎓 Trainer Assistant</span>
                <span className="text-xs">{open ? "▲" : "▼"}</span>
            </button>

            {open && (
                <div className="flex flex-col mt-2 gap-2">
                    <div className="h-48 overflow-y-auto rounded border bg-white dark:bg-zinc-950 p-2 flex flex-col gap-2 text-xs">
                        {messages.length === 0 && (
                            <p className="text-zinc-400 italic">Ask the trainer anything…</p>
                        )}
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`rounded px-2 py-1 max-w-[90%] whitespace-pre-wrap ${msg.role === "user"
                                        ? "self-end bg-blue-600 text-white"
                                        : "self-start bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200"
                                    }`}
                            >
                                {msg.text}
                            </div>
                        ))}
                        {loading && (
                            <div className="self-start bg-zinc-100 dark:bg-zinc-800 rounded px-2 py-1 text-zinc-400 italic">
                                Thinking…
                            </div>
                        )}
                        {error && (
                            <div className="self-start bg-red-100 text-red-700 rounded px-2 py-1">
                                {error}
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    <div className="flex gap-1">
                        <input
                            className="flex-1 text-xs p-1.5 border rounded bg-white dark:bg-zinc-950 dark:text-white"
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask the trainer…"
                            disabled={loading}
                        />
                        <button
                            className="px-2 py-1 rounded bg-blue-600 text-white text-xs hover:bg-blue-700 disabled:opacity-50"
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
