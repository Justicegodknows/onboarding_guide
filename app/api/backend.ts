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
