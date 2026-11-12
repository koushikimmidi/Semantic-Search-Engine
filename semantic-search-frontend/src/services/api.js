const BASE_URL = typeof window !== "undefined" && window.location.hostname ? `http://${window.location.hostname}:8000` : "http://127.0.0.1:8000";

export async function searchDocuments(query) {

    const response = await fetch(`${BASE_URL}/search`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            query
        })

    });

    if (!response.ok) {

        throw new Error("Search Failed");

    }

    const data = await response.json();

    if (data && data.success === false) {

        throw new Error(data.error || "Search Failed");

    }

    return data;

}

export async function listDocuments() {
    const response = await fetch(`${BASE_URL}/documents`);
    if (!response.ok) {
        throw new Error("Failed to fetch documents list");
    }
    return await response.json();
}

export async function uploadDocuments(formData) {
    const response = await fetch(`${BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData
    });
    if (!response.ok) {
        throw new Error("Failed to upload documents");
    }
    return await response.json();
}

export async function deleteDocument(path) {
    const response = await fetch(`${BASE_URL}/documents?path=${encodeURIComponent(path)}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error("Failed to delete document");
    }
    return await response.json();
}

export async function getDocumentContent(path) {
    const response = await fetch(`${BASE_URL}/documents/content?path=${encodeURIComponent(path)}`);
    if (!response.ok) {
        throw new Error("Failed to get document content");
    }
    return await response.json();
}

// ============================================================
// AUTOMATION
// ============================================================

async function requestJson(path, options = {}) {
    const response = await fetch(`${BASE_URL}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options
    });
    if (!response.ok) {
        throw new Error(`Request failed: ${path} (${response.status})`);
    }
    const data = await response.json();
    if (data && data.success === false) {
        throw new Error(data.error || `Request failed: ${path}`);
    }
    return data;
}

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
