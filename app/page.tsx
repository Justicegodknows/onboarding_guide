"use client";
import { useState } from "react";
import ChatBox from "./components/ChatBox";
import SideMenu from "./components/SideMenu";
import { departments } from "./components/departments";

export default function Home() {
  const [selectedDept, setSelectedDept] = useState(departments[0].id);

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

          <ChatBox department={dept?.name || ""} />
        </div>
      </main>
    </div>
  );
}
