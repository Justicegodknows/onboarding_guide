export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function healthCheck() {
    const res = await fetch(`${API_URL}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
}

export async function sendChat(question: string, history: string[] = []) {
    const res = await fetch(`${API_URL}/api/v1/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
    });
    if (!res.ok) throw new Error('Chat failed');
    return res.json();
}

export type EmployeeRole = "USER" | "ADMIN";

export interface RegisterPayload {
    email: string;
    password: string;
    role: EmployeeRole;
    dept: string;
}

export async function registerEmployee(payload: RegisterPayload) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const details = await res.json().catch(() => ({}));
        throw new Error(details?.detail || "Registration failed");
    }

    return res.json();
}

export async function loginEmployee(email: string, password: string) {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await fetch(`${API_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
    });

    if (!res.ok) {
        const details = await res.json().catch(() => ({}));
        throw new Error(details?.detail || "Login failed");
    }

    return res.json();
}
