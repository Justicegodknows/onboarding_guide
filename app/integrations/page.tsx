"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
    createIntegration,
    deleteIntegration,
    listIntegrations,
    testIntegration,
    updateIntegration,
    type CreateIntegrationPayload,
    type Integration,
    type IntegrationType,
} from "../api/backend";

// ---------------------------------------------------------------------------
// Integration catalogue — defines available integrations and their config fields
// ---------------------------------------------------------------------------

interface ConfigField {
    key: string;
    label: string;
    type: "text" | "password" | "number" | "url";
    placeholder?: string;
    required?: boolean;
}

interface IntegrationDef {
    type: IntegrationType;
    label: string;
    description: string;
    icon: string;
    fields: ConfigField[];
}

const INTEGRATION_CATALOGUE: IntegrationDef[] = [
    {
        type: "email",
        label: "Email (SMTP)",
        description: "Connect an SMTP server for email notifications or inbox ingestion.",
        icon: "✉️",
        fields: [
            { key: "smtp_host", label: "SMTP Host", type: "text", placeholder: "smtp.gmail.com", required: true },
            { key: "smtp_port", label: "SMTP Port", type: "number", placeholder: "587", required: true },
            { key: "username", label: "Username / Email", type: "text", placeholder: "you@company.com", required: true },
            { key: "password", label: "Password / App Password", type: "password", required: true },
            { key: "use_tls", label: "Use STARTTLS (true/false)", type: "text", placeholder: "true" },
        ],
    },
    {
        type: "jira",
        label: "Jira",
        description: "Integrate with Jira Cloud or Server to sync issues and project context.",
        icon: "🐛",
        fields: [
            { key: "base_url", label: "Jira Base URL", type: "url", placeholder: "https://yourcompany.atlassian.net", required: true },
            { key: "email", label: "Jira Account Email", type: "text", placeholder: "you@company.com", required: true },
            { key: "api_token", label: "API Token", type: "password", required: true },
        ],
    },
    {
        type: "google_calendar",
        label: "Google Calendar",
        description: "Access calendar events to enrich onboarding schedules and reminders.",
        icon: "📅",
        fields: [
            { key: "api_key", label: "Google API Key", type: "password", required: true },
            { key: "calendar_id", label: "Calendar ID (optional)", type: "text", placeholder: "primary" },
        ],
    },
    {
        type: "slack",
        label: "Slack",
        description: "Send notifications to Slack channels or ingest messages as knowledge.",
        icon: "💬",
        fields: [
            { key: "bot_token", label: "Bot OAuth Token", type: "password", placeholder: "xoxb-..." },
            { key: "webhook_url", label: "Incoming Webhook URL (alternative)", type: "url", placeholder: "https://hooks.slack.com/..." },
        ],
    },
    {
        type: "microsoft_teams",
        label: "Microsoft Teams",
        description: "Post summaries and alerts to Teams channels via webhooks.",
        icon: "🟦",
        fields: [
            { key: "webhook_url", label: "Incoming Webhook URL", type: "url", required: true },
        ],
    },
    {
        type: "github",
        label: "GitHub",
        description: "Connect GitHub to ingest READMEs, wikis, and issue descriptions.",
        icon: "🐙",
        fields: [
            { key: "token", label: "Personal Access Token or GitHub App Token", type: "password", required: true },
            { key: "org", label: "Organisation / User (optional)", type: "text", placeholder: "my-org" },
        ],
    },
    {
        type: "notion",
        label: "Notion",
        description: "Ingest Notion pages and databases into the knowledge base.",
        icon: "📓",
        fields: [
            { key: "token", label: "Integration Token", type: "password", required: true },
            { key: "database_id", label: "Database ID (optional)", type: "text" },
        ],
    },
    {
        type: "custom",
        label: "Custom Integration",
        description: "Add any other service by providing a base URL and API credentials.",
        icon: "🔌",
        fields: [
            { key: "base_url", label: "Base URL", type: "url", placeholder: "https://api.myservice.com/v1" },
            { key: "api_key", label: "API Key", type: "password" },
            { key: "test_url", label: "Health-check URL (optional)", type: "url" },
        ],
    },
];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function IntegrationsPage() {
    const [token, setToken] = useState<string | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedDef, setSelectedDef] = useState<IntegrationDef | null>(null);
    const [editTarget, setEditTarget] = useState<Integration | null>(null);
    const [testResults, setTestResults] = useState<Record<number, { success: boolean; message: string } | null>>({});

    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem("vaultmind_token");
        const storedRole = localStorage.getItem("vaultmind_role");
        setToken(stored);
        setRole(storedRole);
    }, []);

    const fetchIntegrations = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        try {
            setIntegrations(await listIntegrations(token));
        } catch {
            // non-fatal
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        if (token) fetchIntegrations();
    }, [token, fetchIntegrations]);

    if (!mounted) return null;

    if (!token) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-background px-6">
                <div className="max-w-sm w-full bg-white border border-zinc-200 rounded-2xl p-8 shadow-lg text-center">
                    <h1 className="text-2xl font-bold text-black mb-2">Sign in required</h1>
                    <p className="text-zinc-500 text-sm mb-6">You must be signed in to manage integrations.</p>
                    <Link href="/" className="inline-block px-6 py-2.5 bg-primary text-white rounded-full font-semibold hover:opacity-90 transition">
                        Go to Home
                    </Link>
                </div>
            </main>
        );
    }

    const connectedTypes = new Set(integrations.map((i) => i.integration_type));
    const isAdmin = role === "ADMIN";

    const handleTest = async (id: number) => {
        if (!token) return;
        setTestResults((prev) => ({ ...prev, [id]: null }));
        try {
            const res = await testIntegration(id, token);
            setTestResults((prev) => ({ ...prev, [id]: { success: res.success, message: res.message } }));
            setIntegrations((prev) =>
                prev.map((i) => (i.id === id ? { ...i, status: res.status as Integration["status"] } : i)),
            );
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Test failed";
            setTestResults((prev) => ({ ...prev, [id]: { success: false, message: msg } }));
        }
    };

    const handleDelete = async (id: number) => {
        if (!token) return;
        try {
            await deleteIntegration(id, token);
            setIntegrations((prev) => prev.filter((i) => i.id !== id));
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Delete failed");
        }
    };

    return (
        <main className="min-h-screen bg-background text-foreground px-6 py-12">
            <div className="max-w-5xl mx-auto space-y-10">
                <header className="space-y-2">
                    <Link href="/" className="inline-block text-sm font-semibold text-accent hover:underline mb-2">
                        ← Back to Home
                    </Link>
                    <h1 className="text-4xl font-extrabold text-black">Integrations</h1>
                    <p className="text-zinc-500 text-sm">
                        Connect VaultMind to your external tools. Credentials are stored securely and used only for authenticated API calls.
                        {!isAdmin && " Some settings require admin privileges."}
                    </p>
                </header>

                {/* Connected integrations */}
                {integrations.length > 0 && (
                    <section>
                        <h2 className="text-lg font-bold text-black mb-4">Connected</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {integrations.map((intg) => {
                                const def = INTEGRATION_CATALOGUE.find((d) => d.type === intg.integration_type);
                                const testResult = testResults[intg.id];
                                return (
                                    <div
                                        key={intg.id}
                                        className="bg-white border border-zinc-200 rounded-2xl p-5 shadow-sm flex flex-col gap-3"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{def?.icon ?? "🔌"}</span>
                                                <div>
                                                    <p className="font-bold text-black">{intg.name}</p>
                                                    <p className="text-xs text-zinc-400 uppercase tracking-wide">{intg.integration_type}</p>
                                                </div>
                                            </div>
                                            <StatusPill status={intg.status} />
                                        </div>

                                        {intg.is_org_wide && (
                                            <span className="self-start text-xs bg-blue-50 text-blue-600 border border-blue-200 rounded-full px-2 py-0.5">
                                                Org-wide
                                            </span>
                                        )}

                                        {testResult && (
                                            <p className={`text-xs rounded-lg px-3 py-1.5 ${testResult.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
                                                {testResult.message}
                                            </p>
                                        )}

                                        <div className="flex gap-2 flex-wrap">
                                            <button
                                                onClick={() => handleTest(intg.id)}
                                                className="px-3 py-1.5 text-xs rounded-lg bg-cyan-50 text-cyan-700 hover:bg-cyan-100 border border-cyan-200 transition-colors font-medium"
                                            >
                                                Test
                                            </button>
                                            <button
                                                onClick={() => { setSelectedDef(def ?? null); setEditTarget(intg); }}
                                                className="px-3 py-1.5 text-xs rounded-lg bg-zinc-50 text-zinc-700 hover:bg-zinc-100 border border-zinc-200 transition-colors font-medium"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDelete(intg.id)}
                                                className="px-3 py-1.5 text-xs rounded-lg bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 transition-colors font-medium"
                                            >
                                                Disconnect
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                )}

                {/* Available integrations catalogue */}
                <section>
                    <h2 className="text-lg font-bold text-black mb-4">Available Integrations</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {INTEGRATION_CATALOGUE.map((def) => {
                            const isConnected = connectedTypes.has(def.type);
                            return (
                                <button
                                    key={def.type}
                                    onClick={() => { setSelectedDef(def); setEditTarget(null); }}
                                    className={`text-left bg-white border rounded-2xl p-5 shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5 flex flex-col gap-2
                    ${isConnected ? "border-cyan-300 ring-1 ring-cyan-200" : "border-zinc-200"}`}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="text-2xl">{def.icon}</span>
                                        {isConnected && (
                                            <span className="text-xs bg-cyan-50 text-cyan-700 border border-cyan-200 rounded-full px-2 py-0.5">
                                                Connected
                                            </span>
                                        )}
                                    </div>
                                    <p className="font-bold text-black">{def.label}</p>
                                    <p className="text-xs text-zinc-500 leading-relaxed">{def.description}</p>
                                </button>
                            );
                        })}
                    </div>
                </section>
            </div>

            {/* Configuration modal */}
            {selectedDef && (
                <IntegrationModal
                    def={selectedDef}
                    editTarget={editTarget}
                    token={token}
                    isAdmin={isAdmin}
                    onClose={() => { setSelectedDef(null); setEditTarget(null); }}
                    onSaved={() => { fetchIntegrations(); setSelectedDef(null); setEditTarget(null); }}
                />
            )}
        </main>
    );
}

// ---------------------------------------------------------------------------
// Config modal
// ---------------------------------------------------------------------------

interface ModalProps {
    def: IntegrationDef;
    editTarget: Integration | null;
    token: string;
    isAdmin: boolean;
    onClose: () => void;
    onSaved: () => void;
}

function IntegrationModal({ def, editTarget, token, isAdmin, onClose, onSaved }: ModalProps) {
    const [name, setName] = useState(editTarget?.name ?? def.label);
    const [orgWide, setOrgWide] = useState(editTarget?.is_org_wide ?? false);
    const [fields, setFields] = useState<Record<string, string>>({});
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const setField = (key: string, value: string) =>
        setFields((prev) => ({ ...prev, [key]: value }));

    const handleSave = async () => {
        setError(null);
        setSaving(true);
        // Validate required fields
        for (const f of def.fields) {
            if (f.required && !fields[f.key]?.trim()) {
                setError(`${f.label} is required.`);
                setSaving(false);
                return;
            }
        }
        try {
            if (editTarget) {
                await updateIntegration(editTarget.id, { name, config: fields, is_org_wide: orgWide }, token);
            } else {
                const payload: CreateIntegrationPayload = {
                    integration_type: def.type,
                    name,
                    config: fields,
                    is_org_wide: isAdmin ? orgWide : false,
                };
                await createIntegration(payload, token);
            }
            onSaved();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">{def.icon}</span>
                        <h2 className="font-bold text-black">
                            {editTarget ? `Edit ${def.label}` : `Connect ${def.label}`}
                        </h2>
                    </div>
                    <button onClick={onClose} className="text-zinc-400 hover:text-zinc-700 text-xl font-bold leading-none">×</button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-1">
                            Display Name
                        </label>
                        <input
                            className="w-full border border-zinc-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                            title="Integration display name"
                            placeholder="e.g. Company Email Server"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </div>

                    {def.fields.map((f) => (
                        <div key={f.key}>
                            <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-1">
                                {f.label}{f.required && <span className="text-red-500 ml-0.5">*</span>}
                            </label>
                            <input
                                type={f.type}
                                className="w-full border border-zinc-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent font-mono"
                                placeholder={f.placeholder}
                                value={fields[f.key] ?? ""}
                                onChange={(e) => setField(f.key, e.target.value)}
                                autoComplete="off"
                            />
                        </div>
                    ))}

                    {isAdmin && (
                        <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                            <input
                                type="checkbox"
                                className="rounded accent-cyan-600"
                                checked={orgWide}
                                onChange={(e) => setOrgWide(e.target.checked)}
                            />
                            <span className="text-zinc-700">Make this integration available to all users</span>
                        </label>
                    )}

                    {error && (
                        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{error}</p>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm rounded-xl border border-zinc-200 hover:bg-zinc-50 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-5 py-2 text-sm rounded-xl bg-primary text-white font-semibold hover:opacity-90 transition disabled:opacity-50"
                    >
                        {saving ? "Saving…" : editTarget ? "Update" : "Connect"}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Status pill
// ---------------------------------------------------------------------------

function StatusPill({ status }: { status: string }) {
    const styles: Record<string, string> = {
        active: "bg-green-50 text-green-700 border-green-200",
        inactive: "bg-zinc-50 text-zinc-500 border-zinc-200",
        error: "bg-red-50 text-red-600 border-red-200",
    };
    return (
        <span className={`text-xs border rounded-full px-2 py-0.5 font-medium ${styles[status] ?? styles.inactive}`}>
            {status}
        </span>
    );
}
