"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { sendDepartmentChat, sendDepartmentTrainerChat } from "../api/backend";
import ChatBox from "./ChatBox";
import TrainerChatBox from "./TrainerChatBox";

interface DepartmentWorkspaceProps {
    id: string;
    name: string;
    description: string;
    info: string;
}

function getToken(): string | undefined {
    return typeof window !== 'undefined' ? localStorage.getItem('vaultmind_token') ?? undefined : undefined;
}

export default function DepartmentWorkspace({ id, name, description, info }: DepartmentWorkspaceProps) {
    const router = useRouter();

    return (
        <div className="w-full max-w-6xl mx-auto flex flex-col gap-10">
            <div className="rounded-[2rem] border border-zinc-200 bg-white/90 p-6 shadow-sm shadow-zinc-200/20 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/95 dark:shadow-none">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-3">
                        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-700 dark:text-cyan-300">
                            Department Workspace
                        </p>
                        <h1 className="text-4xl font-semibold tracking-tight text-zinc-950 dark:text-white">
                            {name}
                        </h1>
                        <p className="max-w-3xl text-base leading-7 text-zinc-600 dark:text-zinc-300">
                            {info}
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={() => router.back()}
                            className="rounded-full border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold text-zinc-700 transition hover:border-cyan-400 hover:text-cyan-700 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200 dark:hover:border-cyan-500"
                        >
                            ← Back
                        </button>
                        <Link
                            href="/"
                            className="rounded-full bg-cyan-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-cyan-700"
                        >
                            Homepage
                        </Link>
                    </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-[1.75rem] bg-cyan-50 p-5 text-sm text-zinc-700 dark:bg-cyan-900/10 dark:text-zinc-300">
                        <p className="font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-200">How this workspace helps</p>
                        <ul className="mt-4 space-y-3">
                            <li className="rounded-3xl border border-cyan-100 bg-white p-4 shadow-sm dark:border-cyan-800/60 dark:bg-zinc-950">
                                <span className="font-semibold">Contextual answers</span> across department-specific documents.
                            </li>
                            <li className="rounded-3xl border border-cyan-100 bg-white p-4 shadow-sm dark:border-cyan-800/60 dark:bg-zinc-950">
                                <span className="font-semibold">Quick onboarding</span> for new workflows and policies.
                            </li>
                            <li className="rounded-3xl border border-cyan-100 bg-white p-4 shadow-sm dark:border-cyan-800/60 dark:bg-zinc-950">
                                <span className="font-semibold">Practical guidance</span> you can act on instantly.
                            </li>
                        </ul>
                    </div>
                    <div className="rounded-[1.75rem] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
                        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                            Department Overview
                        </h2>
                        <p className="mt-4 text-base leading-7 text-zinc-700 dark:text-zinc-300">
                            {description}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid gap-8 xl:grid-cols-[1.75fr_0.95fr]">
                <div className="space-y-6">
                    <div className="rounded-[2rem] border border-zinc-200 bg-white p-0 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
                        <ChatBox
                            title={`${name} — Main Chat Agent`}
                            department={name}
                            onSend={(question, history) => sendDepartmentChat(id, question, history, getToken())}
                        />
                    </div>
                </div>

                <aside className="space-y-6">
                    <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
                        <h2 className="text-xl font-semibold text-zinc-950 dark:text-white">Need help getting started?</h2>
                        <p className="mt-3 text-sm leading-7 text-zinc-600 dark:text-zinc-300">
                            Use these starter prompts to quickly get precise answers from the department agent.
                        </p>
                        <div className="mt-5 grid gap-3">
                            {[
                                `What are the most important ${name.toLowerCase()} policies?`,
                                `How do I complete a ${name.toLowerCase()} request?`,
                                `Which documents should I read first for ${name.toLowerCase()}?`,
                            ].map((suggestion) => (
                                <button
                                    key={suggestion}
                                    type="button"
                                    className="w-full rounded-3xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-left text-sm text-zinc-700 transition hover:border-cyan-400 hover:bg-white dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-[2rem] border border-zinc-200 bg-zinc-50 p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                        <h2 className="text-lg font-semibold text-zinc-950 dark:text-white">Trainer Assistant</h2>
                        <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                            A compact trainer chat for follow-up questions, learning, and refining your departmental knowledge.
                        </p>
                        <div className="mt-5 rounded-[1.75rem] border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
                            <TrainerChatBox
                                title={`${name} — Trainer Sub-Agent`}
                                onSend={(question, history) => sendDepartmentTrainerChat(id, question, history, getToken())}
                            />
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
}
