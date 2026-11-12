import { useState, useEffect } from "react";
import { listDocuments, getAuthInfo, getApiKey, setApiKey } from "../services/api";
import "../styles/sidebar.css";

function Sidebar({
    darkMode,
    toggleTheme,
    activeTab,
    setActiveTab,
    onNewSearch,
    history = [],
    activeHistoryId,
    onSelectHistory,
    onDeleteHistory,
    onClearHistory,
    onAuthChange
}) {
    const [fileCount, setFileCount] = useState(0);
    const [status, setStatus] = useState("checking");
    const [auth, setAuth] = useState(null);
    const [keyOpen, setKeyOpen] = useState(false);
    const [keyDraft, setKeyDraft] = useState("");

    async function refreshAuth() {
        try {
            setAuth(await getAuthInfo());
        } catch {
            setAuth(null);
        }
    }

    useEffect(() => {
        const initial = setTimeout(refreshAuth, 0);
        return () => clearTimeout(initial);
    }, []);

    function saveKey(event) {
        event.preventDefault();
        setApiKey(keyDraft.trim());
        setKeyOpen(false);
        refreshAuth();
        if (onAuthChange) onAuthChange();
    }

    function clearKey() {
        setApiKey("");
        setKeyDraft("");
        setKeyOpen(false);
        refreshAuth();
        if (onAuthChange) onAuthChange();
    }

    // Fetch file count periodically to display in sidebar
    useEffect(() => {
        const fetchFileCount = async () => {
            try {
                const docs = await listDocuments();
                setFileCount(docs.length || 0);
                setStatus("online");
            } catch (err) {
                console.error("API connection failed:", err);
                setStatus("offline");
            }
        };

        fetchFileCount();
        const interval = setInterval(fetchFileCount, 10000); // refresh every 10s
        return () => clearInterval(interval);
    }, []);

    return (
        <aside className="sidebar">
            <div className="sidebar-brand" onClick={() => setActiveTab("search")}>
                <div className="sidebar-logo">✦</div>
                <div className="sidebar-brand-text">
                    <h2>Semantic AI</h2>
                    <span>Intent Search Engine</span>
                </div>
            </div>

            {activeTab === "search" && (
                <button className="new-thread-btn" onClick={onNewSearch}>
                    <span>+</span> New Search
                </button>
            )}

            <nav className="sidebar-nav">
                <button
                    className={`sidebar-nav-item ${activeTab === "search" ? "active" : ""}`}
                    onClick={() => setActiveTab("search")}
                >
                    <span className="nav-icon">🔍</span>
                    <span className="nav-label">Ask AI</span>
                </button>
                <button
                    className={`sidebar-nav-item ${activeTab === "documents" ? "active" : ""}`}
                    onClick={() => setActiveTab("documents")}
                >
                    <span className="nav-icon">📁</span>
                    <span className="nav-label">Knowledge Base</span>
                    {fileCount > 0 && (
                        <span className="sidebar-badge">{fileCount}</span>
                    )}
                </button>
                <button
                    className={`sidebar-nav-item ${activeTab === "automation" ? "active" : ""}`}
                    onClick={() => setActiveTab("automation")}
                >
                    <span className="nav-icon">✉️</span>
                    <span className="nav-label">Email Automation</span>
                </button>
            </nav>

            <div className="sidebar-history">
                <div className="history-header">
                    <span>Recent Searches</span>
                    {history.length > 0 && (
                        <button
                            className="clear-history-btn"
                            onClick={onClearHistory}
                            title="Clear all searches"
                        >
                            🗑️
                        </button>
                    )}
                </div>
                <div className="history-list">
                    {history.length === 0 ? (
                        <div className="history-empty">No recent searches</div>
                    ) : (
                        history.map((item) => (
                            <div
                                key={item.id}
                                className={`history-item ${activeHistoryId === item.id ? "active" : ""}`}
                                onClick={() => onSelectHistory && onSelectHistory(item)}
                                title={item.query}
                            >
                                <span className="history-icon">💬</span>
                                <span className="history-title">
                                    {item.title}
                                </span>
                                <button
                                    className="delete-history-item-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDeleteHistory && onDeleteHistory(item.id);
                                    }}
                                    title="Delete search"
                                >
                                    ×
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            <div className="sidebar-footer">
                <div className="auth-box">
                    <button
                        className="auth-toggle"
                        onClick={() => {
                            setKeyDraft(getApiKey());
                            setKeyOpen((open) => !open);
                        }}
                        title="Enter an agent or admin API key"
                    >
                        🔑 {auth
                            ? (auth.auth_enabled ? `Role: ${auth.role}` : "Auth disabled")
                            : "API key"}
                    </button>

                    {keyOpen && (
                        <form className="auth-form" onSubmit={saveKey}>
                            <input
                                type="password"
                                placeholder="X-API-Key"
                                value={keyDraft}
                                onChange={(e) => setKeyDraft(e.target.value)}
                                autoComplete="off"
                            />
                            <div className="auth-actions">
                                <button type="submit">Save</button>
                                <button type="button" onClick={clearKey}>Clear</button>
                            </div>
                        </form>
                    )}
                </div>

                <div className="status-indicator">
                    <span className={`status-dot ${status}`}></span>
                    <span className="status-text">
                        {status === "checking" && "Connecting..."}
                        {status === "online" && "System Online"}
                        {status === "offline" && "System Offline"}
                    </span>
                </div>

                <button
                    className="theme-toggle-btn"
                    onClick={toggleTheme}
                    title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
                    aria-label="Toggle theme"
                >
                    {darkMode ? "☀️ Light" : "🌙 Dark"}
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
