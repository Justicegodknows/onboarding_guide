"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { DepartmentInfo } from "../api/backend";
import ChatBox from "./ChatBox";

interface HomeClientProps {
    departments: DepartmentInfo[];
}

interface AuthState {
    token: string;
    username: string;
    displayName: string;
    role: string;
    dept: string;
}

export default function HomeClient({ departments }: HomeClientProps) {
    const router = useRouter();
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [activeOnboardingStep, setActiveOnboardingStep] = useState(0);
    const [auth, setAuth] = useState<AuthState | null>(null);

    useEffect(() => {
        const token = localStorage.getItem("vaultmind_token");
        if (token) {
            setAuth({
                token,
                username: localStorage.getItem("vaultmind_user") ?? "",
                displayName: localStorage.getItem("vaultmind_display_name") ?? localStorage.getItem("vaultmind_user") ?? "",
                role: localStorage.getItem("vaultmind_role") ?? "USER",
                dept: localStorage.getItem("vaultmind_dept") ?? "",
            });
        }
    }, []);

    function handleLogout() {
        ["vaultmind_token", "vaultmind_role", "vaultmind_user", "vaultmind_display_name", "vaultmind_dept"]
            .forEach((k) => localStorage.removeItem(k));
        setAuth(null);
        setIsChatOpen(false);
    }

    const onboardingSteps = [
        {
            title: "Meet VaultMind",
            description: "Search your company knowledge with guided prompts and grounded answers.",
            chipClassName: "bg-cyan-100",
        },
        {
            title: "Choose A Workspace",
            description: "Open your department context and focus on role-specific onboarding guidance.",
            chipClassName: "bg-blue-100",
        },
        {
            title: "Get Source-Backed Help",
            description: "Ask questions and act confidently using evidence pulled from your internal docs.",
            chipClassName: "bg-zinc-100",
        },
    ] as const;

    useEffect(() => {
        const interval = window.setInterval(() => {
            setActiveOnboardingStep((prev) => (prev + 1) % onboardingSteps.length);
        }, 2800);

        return () => window.clearInterval(interval);
    }, [onboardingSteps.length]);

    const currentStep = onboardingSteps[activeOnboardingStep];

    return (
        <div className="relative min-h-screen bg-zinc-50 dark:bg-black py-16 px-6 md:px-8 font-sans overflow-hidden">
            <div className="pointer-events-none absolute inset-0 opacity-60">
                <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-cyan-200/60 blur-3xl" />
                <div className="absolute top-20 right-0 h-80 w-80 rounded-full bg-blue-200/50 blur-3xl" />
            </div>

            <div className="relative w-full max-w-5xl mx-auto flex flex-col gap-10">
                <header className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-8 items-center rounded-3xl border border-zinc-200/80 bg-white/85 backdrop-blur-sm p-8 shadow-xl">
                    <div className="text-left">
                        <p className="inline-block text-xs font-bold uppercase tracking-[0.18em] text-cyan-700 bg-cyan-100 px-3 py-1 rounded-full mb-4">
                            Private Knowledge AI
                        </p>
                        <h1 className="text-4xl md:text-5xl font-bold leading-tight tracking-tight text-black dark:text-zinc-50">
                            VaultMind
                        </h1>
                        <p className="text-lg leading-7 text-black/70 dark:text-zinc-400 mt-3 max-w-3xl">
                            Private, local-first AI assistant for internal company knowledge. Explore departmental workspaces,
                            onboard faster, and chat with grounded responses from your document base.
                        </p>
                        {/* Auth badge */}
                        {auth ? (
                            <div className="flex items-center gap-2 mb-4">
                                <div className="flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1.5 shadow-sm">
                                    <span className="h-6 w-6 rounded-full bg-cyan-500 flex items-center justify-center text-white text-xs font-bold select-none">
                                        {auth.displayName.charAt(0).toUpperCase()}
                                    </span>
                                    <span className="text-sm font-semibold text-zinc-800">{auth.displayName}</span>
                                    {auth.role === "ADMIN" && (
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-700 bg-cyan-100 px-2 py-0.5 rounded-full">Admin</span>
                                    )}
                                </div>
                                <button
                                    onClick={handleLogout}
                                    className="text-xs font-semibold text-zinc-500 hover:text-red-500 transition-colors underline underline-offset-2"
                                >
                                    Sign out
                                </button>
                            </div>
                        ) : null}

                        <div className="flex flex-wrap gap-4 mt-6">
                            <button
                                onClick={() => setIsChatOpen((prev) => !prev)}
                                className="px-8 py-3 bg-primary text-white rounded-full font-bold hover:bg-opacity-90 hover:-translate-y-0.5 transition-all shadow-xl"
                            >
                                {isChatOpen ? "Hide Assistant" : "Open Assistant"}
                            </button>
                            <Link
                                href="/documents"
                                className="px-8 py-3 bg-white text-black border border-zinc-300 rounded-full font-bold hover:bg-zinc-100 hover:-translate-y-0.5 transition-all shadow-xl"
                            >
                                Upload Docs
                            </Link>
                            <Link
                                href="/integrations"
                                className="px-8 py-3 bg-white text-black border border-zinc-300 rounded-full font-bold hover:bg-zinc-100 hover:-translate-y-0.5 transition-all shadow-xl"
                            >
                                Integrations
                            </Link>
                            <Link
                                href="/docs"
                                className="px-8 py-3 bg-white text-black border border-zinc-300 rounded-full font-bold hover:bg-zinc-100 hover:-translate-y-0.5 transition-all shadow-xl"
                            >
                                User Guide
                            </Link>
                            {!auth ? (
                                <Link
                                    href="/login"
                                    className="px-8 py-3 bg-cyan-500 text-white rounded-full font-bold hover:bg-cyan-600 hover:-translate-y-0.5 transition-all shadow-xl"
                                >
                                    Sign In
                                </Link>
                            ) : null}
                        </div>
                    </div>

                    <div className="relative h-90 w-full max-w-90 mx-auto">
                        <div className="absolute inset-0 rounded-4xl bg-linear-to-br from-cyan-100 to-blue-100 border border-cyan-200 shadow-inner" />

                        <div className="absolute top-5 left-5 right-5 h-62.5 rounded-[1.75rem] bg-cyan-400/80 shadow-2xl -rotate-6" />
                        <div className="absolute top-9 left-6 right-6 h-62.5 rounded-[1.75rem] bg-blue-500/80 shadow-2xl rotate-[4deg]" />

                        <div className="absolute top-12 left-7 right-7 h-62.5 rounded-[1.75rem] bg-white p-6 shadow-2xl border border-zinc-100">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">Onboarding</p>
                            <h3 className="text-2xl font-extrabold text-zinc-900 mt-2 transition-all duration-300">{currentStep.title}</h3>
                            <p className="text-sm text-zinc-600 mt-2 leading-relaxed">
                                {currentStep.description}
                            </p>

                            <div className="mt-5 grid grid-cols-3 gap-2">
                                {onboardingSteps.map((step, idx) => (
                                    <div
                                        key={step.title}
                                        className={`h-16 rounded-xl transition-all duration-300 ${step.chipClassName} ${idx === activeOnboardingStep ? "ring-2 ring-cyan-500 scale-[1.03]" : "opacity-80"}`}
                                    />
                                ))}
                            </div>

                            <div className="mt-6 flex items-center justify-between">
                                <div className="flex gap-2">
                                    {onboardingSteps.map((step, idx) => (
                                        <span
                                            key={`dot-${step.title}`}
                                            className={`h-2.5 rounded-full transition-all duration-300 ${idx === activeOnboardingStep ? "w-6 bg-cyan-500" : "w-2.5 bg-zinc-300"}`}
                                        />
                                    ))}
                                </div>
                                <span className="text-xs font-bold text-zinc-500">Step {activeOnboardingStep + 1}/{onboardingSteps.length}</span>
                            </div>
                        </div>
                    </div>
                </header>

                {isChatOpen && (
                    <section className="w-full">
                        <ChatBox title="VaultMind Assistant" />
                    </section>
                )}

                <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="rounded-2xl bg-cyan-50 border border-cyan-200 p-5">
                        <p className="text-xs uppercase tracking-[0.18em] text-cyan-700 font-bold">01 Discover</p>
                        <p className="mt-2 text-sm text-zinc-700">Browse department workspaces and locate relevant internal domains quickly.</p>
                    </div>
                    <div className="rounded-2xl bg-blue-50 border border-blue-200 p-5">
                        <p className="text-xs uppercase tracking-[0.18em] text-blue-700 font-bold">02 Ask</p>
                        <p className="mt-2 text-sm text-zinc-700">Ask context-aware questions and iterate using conversation history.</p>
                    </div>
                    <div className="rounded-2xl bg-zinc-100 border border-zinc-200 p-5">
                        <p className="text-xs uppercase tracking-[0.18em] text-zinc-700 font-bold">03 Act</p>
                        <p className="mt-2 text-sm text-zinc-700">Use source-backed answers for onboarding, compliance, and operations tasks.</p>
                    </div>
                </section>

                <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {departments.map((department) => (
                        <Link
                            key={department.id}
                            href={`/departments/${department.id}`}
                            className="block rounded-2xl border bg-white/90 dark:bg-zinc-900 p-6 hover:border-blue-400 hover:shadow-lg transition-all"
                        >
                            <h2 className="text-xl font-bold mb-2">{department.name}</h2>
                            <p className="text-zinc-700 dark:text-zinc-300 mb-2">{department.description}</p>
                            <p className="text-sm text-zinc-500 dark:text-zinc-400">{department.info}</p>
                        </Link>
                    ))}
                </section>

                <section className="w-full max-w-4xl bg-zinc-100 p-8 rounded-3xl border border-zinc-200 text-left">
                    <h2 className="text-2xl font-bold text-black mb-4">Who is VaultMind for?</h2>
                    <p className="text-zinc-700 mb-6">
                        Built for organizations that manage sensitive internal knowledge and need private AI workflows
                        with secure, role-aware access.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                            <span className="text-accent font-bold block mb-1">Operations Teams</span>
                            <p className="text-sm text-zinc-600">Get consistent answers from policies, SOPs, and internal docs.</p>
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                            <span className="text-accent font-bold block mb-1">Compliance and IT</span>
                            <p className="text-sm text-zinc-600">Keep documents local with secure infrastructure and governance.</p>
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                            <span className="text-accent font-bold block mb-1">New Employee Onboarding</span>
                            <p className="text-sm text-zinc-600">Help hires find internal knowledge faster through guided Q&A.</p>
                        </div>
                    </div>
                </section>

                <section className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
                    <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left ring-1 ring-white/10">
                        <div className="text-3xl mb-4">🔒</div>
                        <h3 className="text-xl font-bold mb-3">Local-First AI</h3>
                        <p className="text-sm opacity-90 leading-relaxed">
                            Data stays inside your environment across ingestion, retrieval, and answer generation.
                        </p>
                    </div>
                    <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left ring-1 ring-white/10">
                        <div className="text-3xl mb-4">🧭</div>
                        <h3 className="text-xl font-bold mb-3">Grounded Responses</h3>
                        <p className="text-sm opacity-90 leading-relaxed">
                            RAG answers are anchored to indexed company documents and source context.
                        </p>
                    </div>
                    <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left ring-1 ring-white/10">
                        <div className="text-3xl mb-4">📚</div>
                        <h3 className="text-xl font-bold mb-3">Department Workspaces</h3>
                        <p className="text-sm opacity-90 leading-relaxed">
                            Dedicated spaces provide focused prompts and assistant behavior per business unit.
                        </p>
                    </div>
                </section>

                <section className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
                    <Link
                        href="/documents"
                        className="group flex flex-col gap-3 rounded-3xl border border-zinc-200 bg-white p-7 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all"
                    >
                        <div className="text-3xl">📂</div>
                        <h3 className="text-xl font-bold text-black group-hover:text-accent transition-colors">Document Ingestion</h3>
                        <p className="text-sm text-zinc-500 leading-relaxed">
                            Upload PDFs, Word documents, Markdown files, and CSVs. Each document is automatically chunked, embedded, and stored in the knowledge base for instant retrieval.
                        </p>
                        <span className="text-xs font-semibold text-accent mt-auto">Open Upload Panel →</span>
                    </Link>
                    <Link
                        href="/integrations"
                        className="group flex flex-col gap-3 rounded-3xl border border-zinc-200 bg-white p-7 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all"
                    >
                        <div className="text-3xl">🔌</div>
                        <h3 className="text-xl font-bold text-black group-hover:text-accent transition-colors">Integrations</h3>
                        <p className="text-sm text-zinc-500 leading-relaxed">
                            Connect email (SMTP), Jira, Google Calendar, Slack, Microsoft Teams, GitHub, and Notion to enrich the knowledge base and enable automated workflows.
                        </p>
                        <span className="text-xs font-semibold text-accent mt-auto">Manage Integrations →</span>
                    </Link>
                </section>
            </div>
        </div>
    );
}
