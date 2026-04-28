"use client";
import Image from "next/image";
import { useState } from "react";
import { healthCheck } from "./api/backend";
import ChatBox from "./components/ChatBox";
import SideMenu from "./components/SideMenu";
import { departments } from "./components/departments";

export default function Home() {
  const [health, setHealth] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDept, setSelectedDept] = useState(departments[0].id);

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

  const dept = departments.find((d) => d.id === selectedDept);

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-black font-sans">
      <SideMenu selected={selectedDept} onSelect={setSelectedDept} />
      <main className="flex flex-1 flex-col items-center justify-start py-16 px-8 bg-white dark:bg-black">
        <div className="w-full max-w-3xl flex flex-col gap-6">
          <h1 className="text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Welcome to EUZ_HELP
          </h1>
          <p className="text-lg leading-7 text-black/70 dark:text-zinc-400">
            Your AI assistant for all things EUZ. Ask me anything about our products, services, or company!
          </p>

          <section className="my-4 p-4 rounded bg-zinc-100 dark:bg-zinc-900">
            <h2 className="text-xl font-bold mb-2">{dept?.name}</h2>
            <div className="mb-1 text-zinc-700 dark:text-zinc-300">{dept?.description}</div>
            <div className="text-zinc-500 dark:text-zinc-400 text-sm">{dept?.info}</div>
          </section>

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
          <ChatBox department={dept?.name || ""} />
        </div>
      </main>
    </div>
  );
}
