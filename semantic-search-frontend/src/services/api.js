// All requests go to "/api", which the Vite dev server (vite.config.js)
// and nginx in Docker forward to the backend. VITE_API_URL overrides it.
const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const SESSION_STORAGE = "semantic-ai-session";


// ============================================================
// SESSION (signed-in account or API key)
// ============================================================

/**
 * Session shape:
 *   { method: "account", token, user: {username, full_name, role} }
 *   { method: "api_key", apiKey, user: {username, role} }
 */
export function getSession() {
    try {
        const raw = localStorage.getItem(SESSION_STORAGE);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

export function saveSession(session) {
    try {
        if (session) {
            localStorage.setItem(SESSION_STORAGE, JSON.stringify(session));
        } else {
            localStorage.removeItem(SESSION_STORAGE);
        }
    } catch {
        // Storage unavailable (private mode): session lasts for this page only.
    }
}

function authHeaders(extra = {}) {
    const session = getSession();
    if (session?.method === "account" && session.token) {
        return { ...extra, Authorization: `Bearer ${session.token}` };
    }
    if (session?.method === "api_key" && session.apiKey) {
        return { ...extra, "X-API-Key": session.apiKey };
    }
    return { ...extra };
}

async function errorMessage(response, fallback) {
    let detail = null;
    try {
        const data = await response.json();
        if (data && typeof data.detail === "string") detail = data.detail;
        else if (data && Array.isArray(data.detail)) detail = data.detail.map((d) => d.msg).join("; ");
        else if (data && data.error) detail = data.error;
    } catch {
        // Not JSON.
    }
    if (response.status === 404 && (!detail || detail === "Not Found")) {
        return "The backend did not recognise this request. An older backend may be running on port 8000 - restart the current backend.";
    }
    if (response.status === 502 || response.status === 503 || response.status === 504) {
        return "Cannot reach the backend. Make sure it is running.";
    }
    return detail || fallback;
}

async function request(path, options = {}) {
    let response;

    try {
        response = await fetch(`${BASE_URL}${path}`, {
            ...options,
            headers: authHeaders({
                ...(options.body && !(options.body instanceof FormData)
                    ? { "Content-Type": "application/json" }
                    : {}),
                ...(options.headers || {})
            })
        });
    } catch {
        throw new Error("Cannot reach the backend. Make sure it is running.");
    }

    if (!response.ok) {
        const message = await errorMessage(response, `Request failed (${response.status})`);

        // Signed-in session expired or the account was disabled.
        if (response.status === 401 && getSession()) {
            window.dispatchEvent(new CustomEvent("auth:expired", { detail: message }));
        }

        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    const data = await response.json();

    if (data && data.success === false) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}

const get = (path) => request(path);
const post = (path, body) => request(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
const patch = (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body) });
const del = (path) => request(path, { method: "DELETE" });


// ============================================================
// AUTHENTICATION
// ============================================================

export function getAuthStatus() {
    return get("/auth/status");
}

export function getMe() {
    return get("/auth/me");
}

export async function login(username, password) {
    const data = await post("/auth/login", { username, password });
    return { method: "account", token: data.token, user: data.user };
}

export async function setupAdmin({ setupKey, username, password, fullName }) {
    const data = await post("/auth/setup", {
        setup_key: setupKey,
        username,
        password,
        full_name: fullName
    });
    return { method: "account", token: data.token, user: data.user };
}

/** Validate an API key by asking the backend which role it grants. */
export async function loginWithApiKey(apiKey) {
    const response = await fetch(`${BASE_URL}/auth/me`, { headers: { "X-API-Key": apiKey } })
        .catch(() => { throw new Error("Cannot reach the backend. Make sure it is running."); });

    if (!response.ok) {
        throw new Error(await errorMessage(response, "Could not verify the API key."));
    }

    const me = await response.json();

    if (me.role === "viewer") {
        throw new Error("This API key is not valid. Check ADMIN_API_KEY / AGENT_API_KEY in the backend .env file.");
    }

    return {
        method: "api_key",
        apiKey,
        user: {
            username: me.username,
            full_name: me.role === "admin" ? "Admin (API key)" : "Agent (API key)",
            role: me.role === "agent" ? "employee" : me.role
        }
    };
}

export function changePassword(currentPassword, newPassword) {
    return post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword
    });
}


// ============================================================
// SEARCH
// ============================================================

export function searchDocuments(query) {
    return post("/search", { query });
}

/**
 * Stream an answer. `onEvent` receives each event:
 *   {type: "sources"} -> {type: "token"} ... -> {type: "done"}
 * Resolves with the final "done" event.
 */
export async function searchDocumentsStream(query, onEvent) {
    let response;

    try {
        response = await fetch(`${BASE_URL}/search/stream`, {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ query })
        });
    } catch {
        throw new Error("Cannot reach the backend. Make sure it is running.");
    }

    if (!response.ok || !response.body) {
        throw new Error(await errorMessage(response, "Search failed"));
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalEvent = null;

    const handleLine = (line) => {
        if (!line.trim()) return;
        const event = JSON.parse(line);
        if (event.type === "error") {
            throw new Error(event.error || "Search failed");
        }
        if (event.type === "done") {
            finalEvent = event;
        }
        onEvent(event);
    };

    for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        lines.forEach(handleLine);
    }

    buffer += decoder.decode();
    handleLine(buffer);

    if (!finalEvent) {
        throw new Error("The answer stream ended unexpectedly.");
    }

    return finalEvent;
}


// ============================================================
// DOCUMENTS
// ============================================================

export function listDocuments() {
    return get("/documents");
}

export async function uploadDocuments(formData) {
    try {
        return await request("/documents/upload", { method: "POST", body: formData });
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export async function deleteDocument(path) {
    try {
        return await del(`/documents?path=${encodeURIComponent(path)}`);
    } catch (error) {
        return { success: false, error: error.message };
    }
}

export function getDocumentContent(path) {
    return get(`/documents/content?path=${encodeURIComponent(path)}`);
}


// ============================================================
// AUTOMATION & REVIEW QUEUE
// ============================================================

export const getAutomationDashboard = () => get("/automation/dashboard");
export const getAutomationHistory = () => get("/automation/history");
export const runAutomation = () => post("/automation/run");
export const startScheduler = () => post("/automation/scheduler/start");
export const stopScheduler = () => post("/automation/scheduler/stop");
export const processTestMessage = (message) => post("/automation/process", message);

export function getEscalations(status) {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return get(`/automation/escalations${query}`);
}

export function resolveEscalation(id, resolutionNote) {
    return post(`/automation/escalations/${encodeURIComponent(id)}/resolve`, {
        resolution_note: resolutionNote || null
    });
}

export function replyToEscalation(id, reply, resolutionNote) {
    return post(`/automation/escalations/${encodeURIComponent(id)}/reply`, {
        reply,
        resolution_note: resolutionNote || null
    });
}


// ============================================================
// ANALYTICS
// ============================================================

export const getAnalytics = (days = 30) => get(`/analytics/overview?days=${days}`);


// ============================================================
// ADMIN
// ============================================================

export const listUsers = () => get("/admin/users");
export const createUser = (user) => post("/admin/users", user);
export const updateUser = (id, changes) => patch(`/admin/users/${id}`, changes);
export const deleteUser = (id) => del(`/admin/users/${id}`);

export function getAuditLog({ limit = 50, offset = 0, action = "", actor = "" } = {}) {
    const params = new URLSearchParams({ limit, offset });
    if (action) params.set("action", action);
    if (actor) params.set("actor", actor);
    return get(`/admin/audit?${params}`);
}

export const getSystemInfo = () => get("/admin/system");
export const updateSettings = (changes) => patch("/admin/settings", changes);
export const reindexKnowledgeBase = () => post("/admin/reindex");
