export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DepartmentInfo {
    id: string;
    name: string;
    description: string;
    info: string;
    persona_system_prompt: string;
    trainer_persona_prompt: string;
}

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
    if (!res.ok) {
        let detail = '';
        try {
            const data = await res.json();
            detail = data?.detail || data?.message || JSON.stringify(data);
        } catch {
            detail = await res.text();
        }
        throw new Error(`Chat failed (${res.status}): ${detail || 'Unknown error'}`);
    }
    return res.json();
}

export async function sendTrainerChat(question: string, history: string[] = []) {
    const res = await fetch(`${API_URL}/api/v1/trainer/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
    });
    if (!res.ok) {
        let detail = '';
        try {
            const data = await res.json();
            detail = data?.detail || data?.message || JSON.stringify(data);
        } catch {
            detail = await res.text();
        }
        throw new Error(`Trainer chat failed (${res.status}): ${detail || 'Unknown error'}`);
    }
    return res.json();
}

export async function getDepartments(): Promise<DepartmentInfo[]> {
    const res = await fetch(`${API_URL}/api/v1/departments/`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to load departments');
    return res.json();
}

export async function getDepartment(departmentId: string): Promise<DepartmentInfo> {
    const res = await fetch(`${API_URL}/api/v1/departments/${departmentId}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`Department lookup failed (${res.status})`);
    return res.json();
}

export async function sendDepartmentChat(
    departmentId: string,
    question: string,
    history: string[] = []
) {
    const res = await fetch(`${API_URL}/api/v1/departments/${departmentId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
    });
    if (!res.ok) {
        let detail = '';
        try {
            const data = await res.json();
            detail = data?.detail || data?.message || JSON.stringify(data);
        } catch {
            detail = await res.text();
        }
        throw new Error(`Department chat failed (${res.status}): ${detail || 'Unknown error'}`);
    }
    return res.json();
}

export async function sendDepartmentTrainerChat(
    departmentId: string,
    question: string,
    history: string[] = []
) {
    const res = await fetch(`${API_URL}/api/v1/departments/${departmentId}/trainer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
    });
    if (!res.ok) {
        let detail = '';
        try {
            const data = await res.json();
            detail = data?.detail || data?.message || JSON.stringify(data);
        } catch {
            detail = await res.text();
        }
        throw new Error(`Department trainer chat failed (${res.status}): ${detail || 'Unknown error'}`);
    }
    return res.json();
}
