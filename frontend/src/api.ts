/** API client — all backend calls */

const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

// --- Settings ---
export const getSettings = () => request<any>('/settings');
export const updateSettings = (data: any) =>
    request<any>('/settings', { method: 'PUT', body: JSON.stringify(data) });

// --- Onboarding ---
export const getOnboardingStatus = () => request<any>('/onboarding/status');
export const saveProfile = (data: any) =>
    request<any>('/onboarding/profile', { method: 'POST', body: JSON.stringify(data) });

// --- Projects ---
export const getProjects = () => request<any[]>('/projects');
export const createProject = (name?: string) =>
    request<any>('/projects', { method: 'POST', body: JSON.stringify({ name: name || 'New Chat' }) });
export const getProject = (id: string) => request<any>(`/projects/${id}`);
export const deleteProject = (id: string) =>
    request<any>(`/projects/${id}`, { method: 'DELETE' });
export const updateProject = (id: string, data: any) =>
    request<any>(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) });

// --- Debug ---
export const getDebugInfo = (messageId: string) => request<any>(`/debug/${messageId}`);

// --- Feedback ---
export const submitFeedback = (data: { message_id: string; project_id: string; rating: number; comment?: string }) =>
    request<any>('/feedback', { method: 'POST', body: JSON.stringify(data) });

// --- WebSocket ---
export function createWebSocket(projectId: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return new WebSocket(`${protocol}//${host}/api/ws/${projectId}`);
}
