"use client";
import Image from "next/image";
import { useState } from "react";
import { healthCheck } from "./api/backend";
import ChatBox from "./components/ChatBox";

export default function Home() {
  const [health, setHealth] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function checkHealth() {
    setLoading(true);
    setHealth(null);
    try {
      const res = await healthCheck();
      setHealth(JSON.stringify(res));
    } catch (e: any) {
      setHealth(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">

        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Welcome to EUZ_HELP
          </h1>
          <p className="max-w-xs text-lg leading-7 text-black/70 dark:text-zinc-400">
            Your AI assistant for all things EUZ. Ask me anything about our products, services, or company!
          </p>

          {health && (
            <pre className="mt-4 p-2 bg-zinc-100 text-zinc-800 rounded text-left max-w-md overflow-x-auto">
              {health}
            </pre>
          )}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              checkHealth();
            }}
            className="mt-4 inline-flex items-center gap-2 rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {loading ? "Checking..." : "Check Backend Health"}
          </a>
          <ChatBox />
        </div>
      </main >
    </div >
  );
}
