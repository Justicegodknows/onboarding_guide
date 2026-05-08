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
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);
    try {
        const res = await fetch(`${API_URL}/api/v1/trainer/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, history }),
            signal: controller.signal,
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
    } catch (error: any) {
        if (error?.name === 'AbortError') {
            throw new Error('Trainer request timed out after 60s. Please try again.');
        }
        throw error;
    } finally {
        clearTimeout(timeout);
    }
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

export interface LoginResult {
    access_token: string;
    token_type: string;
    username: string;
    role: string;
    dept: string;
    display_name: string;
}

export async function loginUser(username: string, password: string): Promise<LoginResult> {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await fetch(`${API_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
    });

    if (!res.ok) {
        const details = await res.json().catch(() => ({}));
        throw new Error(details?.detail || "Incorrect username or password");
    }

    return res.json();
}

/** @deprecated Use loginUser instead */
export async function loginEmployee(email: string, password: string) {
    return loginUser(email, password);
}

export async function getMe(token: string) {
    const res = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Session expired");
    return res.json() as Promise<{ id: string; role: string; dept: string; display_name: string }>;
}

// ---------------------------------------------------------------------------
// Document ingestion
// ---------------------------------------------------------------------------

export interface UploadedDocument {
    id: number;
    filename: string;
    uploaded_by: number | null;
    uploaded_at: string | null;
    metadata: string | null;
}

export interface UploadResult {
    document_id: string;
    db_id: number;
    filename: string;
    size_bytes: number;
    ingest_status: string;
    chunks_added: number;
}

export async function uploadDocument(file: File, token: string): Promise<UploadResult> {
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
    });

    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Upload failed (${res.status})`);
    }
    return res.json();
}

export async function listDocuments(token: string): Promise<UploadedDocument[]> {
    const res = await fetch(`${API_URL}/api/v1/documents/`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to load documents (${res.status})`);
    return res.json();
}

export async function deleteDocument(docId: number, token: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/documents/${docId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Delete failed (${res.status})`);
    }
}

export async function reingestDocument(docId: number, token: string): Promise<unknown> {
    const res = await fetch(`${API_URL}/api/v1/documents/${docId}/reingest`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Re-ingest failed (${res.status})`);
    }
    return res.json();
}

// ---------------------------------------------------------------------------
// Integrations
// ---------------------------------------------------------------------------

export type IntegrationType =
    | "email"
    | "jira"
    | "google_calendar"
    | "slack"
    | "microsoft_teams"
    | "github"
    | "notion"
    | "custom";

export interface Integration {
    id: number;
    owner_email: string | null;
    integration_type: IntegrationType;
    name: string;
    status: "active" | "inactive" | "error";
    is_org_wide: boolean;
    created_at: string;
    updated_at: string;
}

export interface CreateIntegrationPayload {
    integration_type: IntegrationType;
    name: string;
    config: Record<string, unknown>;
    is_org_wide?: boolean;
}

export async function listIntegrations(token: string): Promise<Integration[]> {
    const res = await fetch(`${API_URL}/api/v1/integrations/`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to load integrations (${res.status})`);
    return res.json();
}

export async function createIntegration(
    payload: CreateIntegrationPayload,
    token: string,
): Promise<Integration> {
    const res = await fetch(`${API_URL}/api/v1/integrations/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Create integration failed (${res.status})`);
    }
    return res.json();
}

export async function updateIntegration(
    id: number,
    payload: Partial<{ name: string; config: Record<string, unknown>; status: "active" | "inactive"; is_org_wide: boolean }>,
    token: string,
): Promise<Integration> {
    const res = await fetch(`${API_URL}/api/v1/integrations/${id}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Update integration failed (${res.status})`);
    }
    return res.json();
}

export async function deleteIntegration(id: number, token: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/integrations/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Delete integration failed (${res.status})`);
    }
}

export async function testIntegration(id: number, token: string): Promise<{ success: boolean; message: string; status: string }> {
    const res = await fetch(`${API_URL}/api/v1/integrations/${id}/test`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Test integration failed (${res.status})`);
    }
    return res.json();
}

