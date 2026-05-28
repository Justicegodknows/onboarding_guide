"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { loginUser } from "../api/backend";

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    // Already logged in → redirect home
    useEffect(() => {
        if (typeof window !== "undefined" && localStorage.getItem("vaultmind_token")) {
            router.replace("/");
        }
    }, [router]);

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        if (!username.trim() || !password) return;
        setError("");
        setLoading(true);
        try {
            const result = await loginUser(username.trim(), password);
            localStorage.setItem("vaultmind_token", result.access_token);
            localStorage.setItem("vaultmind_role", result.role);
            localStorage.setItem("vaultmind_user", result.username);
            localStorage.setItem("vaultmind_display_name", result.display_name);
            localStorage.setItem("vaultmind_dept", result.dept);
            router.replace("/");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-white px-4">
            <div className="relative w-full max-w-sm">
                {/* Logo / Brand */}
                <div className="mb-8 text-center">
                    <span className="inline-block text-xs font-bold uppercase tracking-[0.18em] text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1 rounded-full mb-4">
                        Private Knowledge AI
                    </span>
                    <h1 className="text-4xl font-bold text-gray-900 tracking-tight">VaultMind</h1>
                    <p className="text-sm text-gray-500 mt-2">Sign in to your workspace</p>
                </div>

                {/* Card */}
                <div className="rounded-3xl border border-gray-200 bg-white shadow-md px-8 py-9">
                    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
                        {/* Username */}
                        <div className="flex flex-col gap-1.5">
                            <label
                                htmlFor="vm-username"
                                className="text-xs font-bold uppercase tracking-widest text-gray-500"
                            >
                                Username
                            </label>
                            <input
                                id="vm-username"
                                type="text"
                                autoComplete="username"
                                autoFocus
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="e.g. EUZadmin"
                                required
                                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition"
                            />
                        </div>

                        {/* Password */}
                        <div className="flex flex-col gap-1.5">
                            <label
                                htmlFor="vm-password"
                                className="text-xs font-bold uppercase tracking-widest text-gray-500"
                            >
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    id="vm-password"
                                    type={showPassword ? "text" : "password"}
                                    autoComplete="current-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 pr-12 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((p) => !p)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition text-xs font-medium select-none"
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                >
                                    {showPassword ? "Hide" : "Show"}
                                </button>
                            </div>
                        </div>

                        {/* Error */}
                        {error && (
                            <div
                                role="alert"
                                className="flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
                            >
                                <svg className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                                </svg>
                                {error}
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={loading || !username.trim() || !password}
                            className="mt-1 w-full rounded-full bg-blue-700 py-3 text-sm font-bold text-white hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 shadow-md"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                    </svg>
                                    Signing in…
                                </span>
                            ) : (
                                "Sign In"
                            )}
                        </button>
                    </form>
                </div>

                <p className="mt-5 text-center text-sm text-gray-500">
                    Need an account?{' '}
                    <a href="/register" className="font-semibold text-blue-600 hover:text-blue-800 underline">
                        Register here
                    </a>
                </p>
                <p className="mt-4 text-center text-xs text-gray-400">
                    Default admin: <span className="font-mono font-semibold text-gray-600">EUZadmin</span> /{' '}
                    <span className="font-mono font-semibold text-gray-600">admin</span>
                </p>
            </div>
        </div>
    );
}
