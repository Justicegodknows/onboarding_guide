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
            <div className="rounded-[2rem] border border-gray-200 bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-3">
                        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-600">
                            Department Workspace
                        </p>
                        <h1 className="text-4xl font-semibold tracking-tight text-gray-900">
                            {name}
                        </h1>
                        <p className="max-w-3xl text-base leading-7 text-gray-600">
                            {info}
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={() => router.back()}
                            className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-blue-400 hover:text-blue-700"
                        >
                            ← Back
                        </button>
                        <Link
                            href="/"
                            className="rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
                        >
                            Homepage
                        </Link>
                    </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-[1.75rem] bg-blue-50 border border-blue-100 p-5 text-sm text-gray-700">
                        <p className="font-semibold uppercase tracking-[0.18em] text-blue-700">How this workspace helps</p>
                        <ul className="mt-4 space-y-3">
                            <li className="rounded-3xl border border-blue-100 bg-white p-4 shadow-sm">
                                <span className="font-semibold text-gray-900">Contextual answers</span> across department-specific documents.
                            </li>
                            <li className="rounded-3xl border border-blue-100 bg-white p-4 shadow-sm">
                                <span className="font-semibold text-gray-900">Quick onboarding</span> for new workflows and policies.
                            </li>
                            <li className="rounded-3xl border border-blue-100 bg-white p-4 shadow-sm">
                                <span className="font-semibold text-gray-900">Practical guidance</span> you can act on instantly.
                            </li>
                        </ul>
                    </div>
                    <div className="rounded-[1.75rem] border border-gray-200 bg-white p-5 shadow-sm">
                        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
                            Department Overview
                        </h2>
                        <p className="mt-4 text-base leading-7 text-gray-700">
                            {description}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid gap-8 xl:grid-cols-[1.75fr_0.95fr]">
                <div className="space-y-6">
                    <div className="rounded-[2rem] border border-gray-200 bg-white p-0 shadow-sm">
                        <ChatBox
                            title={`${name} — Main Chat Agent`}
                            department={name}
                            onSend={(question, history) => sendDepartmentChat(id, question, history, getToken())}
                        />
                    </div>
                </div>

                <aside className="space-y-6">
                    <div className="rounded-[2rem] border border-gray-200 bg-white p-6 shadow-sm">
                        <h2 className="text-xl font-semibold text-gray-900">Need help getting started?</h2>
                        <p className="mt-3 text-sm leading-7 text-gray-600">
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
                                    className="w-full rounded-3xl border border-gray-200 bg-gray-50 px-4 py-3 text-left text-sm text-gray-700 transition hover:border-blue-400 hover:bg-white hover:text-blue-700"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-[2rem] border border-gray-200 bg-white p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900">Trainer Assistant</h2>
                        <p className="mt-2 text-sm leading-6 text-gray-600">
                            A compact trainer chat for follow-up questions, learning, and refining your departmental knowledge.
                        </p>
                        <div className="mt-5 rounded-[1.75rem] border border-gray-200 bg-white p-4">
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
