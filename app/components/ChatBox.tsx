"use client";
import { useState } from "react";
import { sendChat } from "../api/backend";

interface ChatBoxProps {
    department?: string;
}

export default function ChatBox({ department }: ChatBoxProps) {
    const [question, setQuestion] = useState("");
    const [history, setHistory] = useState<string[]>([]);
    const [answer, setAnswer] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSend() {
        setLoading(true);
        setError(null);
        setAnswer(null);
        try {
            // Prepend department context to the question
            const deptQuestion = department ? `[${department}] ${question}` : question;
            const res = await sendChat(deptQuestion, history);
            setAnswer(res.answer);
            setHistory([...history, deptQuestion]);
            setQuestion("");
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="w-full max-w-lg mx-auto mt-8 p-4 border rounded bg-white dark:bg-zinc-900">
            <h2 className="text-xl font-semibold mb-2">Chat with RAG Agent</h2>
            <div className="mb-2">
                <input
                    className="w-full p-2 border rounded"
                    type="text"
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    placeholder={department ? `Ask about ${department}...` : "Type your question..."}
                    disabled={loading}
                />
            </div>
            <button
                className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                onClick={handleSend}
                disabled={loading || !question.trim()}
            >
                {loading ? "Sending..." : "Send"}
            </button>
            {answer && (
                <div className="mt-4 p-2 bg-zinc-100 text-zinc-800 rounded">
                    <strong>Answer:</strong> {answer}
                </div>
            )}
            {error && (
                <div className="mt-4 p-2 bg-red-100 text-red-800 rounded">
                    <strong>Error:</strong> {error}
                </div>
            )}
        </div>
    );
}
