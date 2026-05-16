"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { registerEmployee, loginUser } from "../api/backend";

export default function RegisterPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [displayName, setDisplayName] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [dept, setDept] = useState("General");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        if (!email.trim() || !password || !confirmPassword) return;
        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setError("");
        setLoading(true);

        try {
            await registerEmployee({
                email: email.trim(),
                password,
                dept,
                display_name: displayName.trim(),
                role: "USER",
            });

            const loginResult = await loginUser(email.trim(), password);

            localStorage.setItem("vaultmind_token", loginResult.access_token);
            localStorage.setItem("vaultmind_role", loginResult.role);
            localStorage.setItem("vaultmind_user", loginResult.username);
            localStorage.setItem("vaultmind_display_name", loginResult.display_name);
            localStorage.setItem("vaultmind_dept", loginResult.dept);
            router.replace("/");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Registration failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-zinc-50 px-4">
            <div className="pointer-events-none fixed inset-0 overflow-hidden">
                <div className="absolute -top-32 -left-24 h-96 w-96 rounded-full bg-cyan-200/50 blur-3xl" />
                <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-200/40 blur-3xl" />
            </div>

            <div className="relative w-full max-w-md">
                <div className="mb-8 text-center">
                    <span className="inline-block text-xs font-bold uppercase tracking-[0.18em] text-cyan-700 bg-cyan-100 px-3 py-1 rounded-full mb-4">
                        Private Knowledge AI
                    </span>
                    <h1 className="text-4xl font-bold text-zinc-900 tracking-tight">Create your account</h1>
                    <p className="text-sm text-zinc-500 mt-2">Register a secure VaultMind user account.</p>
                </div>

                <div className="rounded-3xl border border-zinc-200 bg-white shadow-xl px-8 py-9">
                    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label htmlFor="vm-email" className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                                Email or username
                            </label>
                            <input
                                id="vm-email"
                                type="text"
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@company.com or EUZadmin"
                                required
                                className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label htmlFor="vm-display-name" className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                                Display name
                            </label>
                            <input
                                id="vm-display-name"
                                type="text"
                                autoComplete="name"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                placeholder="Your full name"
                                className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition"
                            />
                        </div>

                        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                            <div className="flex flex-col gap-1.5">
                                <label htmlFor="vm-password" className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                                    Password
                                </label>
                                <input
                                    id="vm-password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition"
                                />
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <label htmlFor="vm-confirm-password" className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                                    Confirm password
                                </label>
                                <input
                                    id="vm-confirm-password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label htmlFor="vm-dept" className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                                Department
                            </label>
                            <input
                                id="vm-dept"
                                type="text"
                                autoComplete="organization"
                                value={dept}
                                onChange={(e) => setDept(e.target.value)}
                                placeholder="General"
                                className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition"
                            />
                        </div>

                        {error && (
                            <div role="alert" className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || !email.trim() || !password || !confirmPassword}
                            className="mt-1 w-full rounded-full bg-[#0D1B2A] py-3 text-sm font-bold text-white hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 shadow-lg"
                        >
                            {loading ? "Creating account…" : "Create account"}
                        </button>
                    </form>
                </div>

                <p className="mt-5 text-center text-sm text-zinc-500">
                    Already have an account?{' '}
                    <a href="/login" className="font-semibold text-cyan-700 hover:text-cyan-900 underline">
                        Sign in
                    </a>
                </p>
            </div>
        </div>
    );
}
