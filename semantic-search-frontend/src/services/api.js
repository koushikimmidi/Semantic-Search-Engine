// API base URL: VITE_API_URL at build time, otherwise the same host
// as the page on port 8000.
const BASE_URL =
    import.meta.env.VITE_API_URL ||
    (typeof window !== "undefined" && window.location.hostname
        ? `http://${window.location.hostname}:8000`
        : "http://127.0.0.1:8000");

const API_KEY_STORAGE = "semantic-ai-api-key";


// ============================================================
// API KEY (agent / admin roles)
// ============================================================

export function getApiKey() {
    try {
        return localStorage.getItem(API_KEY_STORAGE) || "";
    } catch {
        return "";
    }
}

export function setApiKey(key) {
    try {
        if (key) {
            localStorage.setItem(API_KEY_STORAGE, key);
        } else {
            localStorage.removeItem(API_KEY_STORAGE);
        }
    } catch {
        // Storage unavailable (private mode): key lasts for this page only.
    }
}

function authHeaders(extra = {}) {
    const key = getApiKey();
    return key ? { ...extra, "X-API-Key": key } : { ...extra };
}

async function errorMessage(response, fallback) {
    try {
        const data = await response.json();
        if (data && typeof data.detail === "string") return data.detail;
        if (data && data.error) return data.error;
    } catch {
        // Not JSON.
    }
    if (response.status === 401 || response.status === 403) {
        return "Not authorized. Add a valid API key in the sidebar.";
    }
    return fallback;
}

async function requestJson(path, options = {}) {
    const response = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: authHeaders({
            "Content-Type": "application/json",
            ...(options.headers || {})
        })
    });

    if (!response.ok) {
        const error = new Error(await errorMessage(response, `Request failed (${response.status})`));
        error.status = response.status;
        throw error;
    }

    const data = await response.json();

    if (data && data.success === false) {
        throw new Error(data.error || `Request failed: ${path}`);
    }

    return data;
}

export function getAuthInfo() {
    return requestJson("/auth/me");
}


// ============================================================
// SEARCH
// ============================================================

export function searchDocuments(query) {
    return requestJson("/search", {
        method: "POST",
        body: JSON.stringify({ query })
    });
}

/**
 * Stream an answer. `onEvent` receives each event:
 *   {type: "sources"} -> {type: "token"} ... -> {type: "done"}
 * Resolves with the final "done" event.
 */
export async function searchDocumentsStream(query, onEvent) {
    const response = await fetch(`${BASE_URL}/search/stream`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ query })
    });

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

export async function listDocuments() {
    const response = await fetch(`${BASE_URL}/documents`, { headers: authHeaders() });
    if (!response.ok) {
        throw new Error("Failed to fetch documents list");
    }
    return await response.json();
}

export async function uploadDocuments(formData) {
    const response = await fetch(`${BASE_URL}/documents/upload`, {
        method: "POST",
        headers: authHeaders(),
        body: formData
    });
    if (!response.ok) {
        return { success: false, error: await errorMessage(response, "Failed to upload documents") };
    }
    return await response.json();
}

export async function deleteDocument(path) {
    const response = await fetch(`${BASE_URL}/documents?path=${encodeURIComponent(path)}`, {
        method: "DELETE",
        headers: authHeaders()
    });
    if (!response.ok) {
        return { success: false, error: await errorMessage(response, "Failed to delete document") };
    }
    return await response.json();
}

export async function getDocumentContent(path) {
    const response = await fetch(
        `${BASE_URL}/documents/content?path=${encodeURIComponent(path)}`,
        { headers: authHeaders() }
    );
    if (!response.ok) {
        throw new Error("Failed to get document content");
    }
    return await response.json();
}


// ============================================================
// AUTOMATION
// ============================================================

export function getAutomationDashboard() {
    return requestJson("/automation/dashboard");
}

export function getAutomationHistory() {
    return requestJson("/automation/history");
}

export function runAutomation() {
    return requestJson("/automation/run", { method: "POST" });
}

export function startScheduler() {
    return requestJson("/automation/scheduler/start", { method: "POST" });
}

export function stopScheduler() {
    return requestJson("/automation/scheduler/stop", { method: "POST" });
}

export function processTestMessage(message) {
    return requestJson("/automation/process", {
        method: "POST",
        body: JSON.stringify(message)
    });
}

export function getEscalations(status) {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return requestJson(`/automation/escalations${query}`);
}

export function resolveEscalation(id, resolutionNote) {
    return requestJson(`/automation/escalations/${encodeURIComponent(id)}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution_note: resolutionNote || null })
    });
}

export function replyToEscalation(id, reply, resolutionNote) {
    return requestJson(`/automation/escalations/${encodeURIComponent(id)}/reply`, {
        method: "POST",
        body: JSON.stringify({ reply, resolution_note: resolutionNote || null })
    });
}
