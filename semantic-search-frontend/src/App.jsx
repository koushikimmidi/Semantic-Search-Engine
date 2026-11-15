import { useCallback, useEffect, useState } from "react";
import {
    FolderOpen,
    Inbox,
    LayoutDashboard,
    Mail,
    MessageSquareText,
    ScrollText,
    Settings2,
    Users
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import PortalHeader from "./components/PortalHeader";
import { ChangePasswordModal } from "./components/ui";
import Home from "./pages/Home";
import LoginPage from "./pages/LoginPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ReviewQueuePage from "./pages/ReviewQueuePage";
import UsersPage from "./pages/UsersPage";
import AuditLogPage from "./pages/AuditLogPage";
import SystemPage from "./pages/SystemPage";
import AutomationDashboard from "./components/AutomationDashboard";
import DocumentManager from "./components/DocumentManager";

import { getAuthStatus, getEscalations, getMe, getSession, saveSession } from "./services/api";

const NAV = {
    admin: [
        {
            label: "Workspace",
            items: [
                { id: "overview", label: "Analytics", icon: LayoutDashboard },
                { id: "search", label: "Ask", icon: MessageSquareText },
                { id: "queue", label: "Review queue", icon: Inbox, badge: true },
                { id: "automation", label: "Email automation", icon: Mail }
            ]
        },
        {
            label: "Content",
            items: [{ id: "documents", label: "Knowledge base", icon: FolderOpen }]
        },
        {
            label: "Administration",
            items: [
                { id: "users", label: "Users", icon: Users },
                { id: "audit", label: "Audit log", icon: ScrollText },
                { id: "system", label: "System", icon: Settings2 }
            ]
        }
    ],
    employee: [
        {
            label: "Workspace",
            items: [
                { id: "overview", label: "Overview", icon: LayoutDashboard },
                { id: "search", label: "Ask", icon: MessageSquareText },
                { id: "queue", label: "Review queue", icon: Inbox, badge: true },
                { id: "automation", label: "Test a message", icon: Mail }
            ]
        },
        {
            label: "Content",
            items: [{ id: "documents", label: "Knowledge base", icon: FolderOpen }]
        }
    ]
};

function readJson(key, fallback) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch {
        return fallback;
    }
}

function writeJson(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {
        // Storage unavailable: keep in memory only.
    }
}

function App() {

    // ---------------- Theme ----------------

    const [darkMode, setDarkMode] = useState(() => readJson("semantic-ai-theme-dark", false));

    useEffect(() => {
        document.documentElement.classList.toggle("theme-dark", darkMode);
    }, [darkMode]);

    function toggleTheme() {
        setDarkMode((mode) => {
            writeJson("semantic-ai-theme-dark", !mode);
            return !mode;
        });
    }

    // ---------------- Session ----------------

    const [authState, setAuthState] = useState("loading");   // loading | signed-out | signed-in | offline
    const [authStatus, setAuthStatus] = useState(null);
    const [session, setSession] = useState(null);
    const [notice, setNotice] = useState("");
    const [passwordOpen, setPasswordOpen] = useState(false);
    const [navOpen, setNavOpen] = useState(false);

    const signOut = useCallback((message = "") => {
        saveSession(null);
        setSession(null);
        setNotice(message);
        setAuthState("signed-out");
        getAuthStatus().then(setAuthStatus).catch(() => {});
    }, []);

    const checkSession = useCallback(async () => {
        try {
            const status = await getAuthStatus();
            setAuthStatus(status);

            const stored = getSession();

            if (!stored) {
                setAuthState("signed-out");
                return;
            }

            const me = await getMe();

            if (me.role === "viewer") {
                saveSession(null);
                setNotice("Your session has expired. Please sign in again.");
                setAuthState("signed-out");
                return;
            }

            const role = me.role === "agent" ? "employee" : me.role;
            const refreshed = {
                ...stored,
                portal: role === "admin" ? (stored.portal || "admin") : "employee",
                user: { ...stored.user, role, username: me.username, full_name: me.full_name || stored.user?.full_name }
            };

            saveSession(refreshed);
            setSession(refreshed);
            setAuthState("signed-in");
        } catch {
            setAuthState("offline");
        }
    }, []);

    useEffect(() => {
        const initial = setTimeout(checkSession, 0);
        return () => clearTimeout(initial);
    }, [checkSession]);

    useEffect(() => {
        const onExpired = (event) => signOut(event.detail || "Your session has expired. Please sign in again.");
        window.addEventListener("auth:expired", onExpired);
        return () => window.removeEventListener("auth:expired", onExpired);
    }, [signOut]);

    function handleSignedIn(newSession) {
        saveSession(newSession);
        setSession(newSession);
        setNotice("");
        setActiveTab(newSession.portal === "admin" ? "overview" : "queue");
        setAuthState("signed-in");
    }

    function switchPortal() {
        const next = { ...session, portal: session.portal === "admin" ? "employee" : "admin" };
        saveSession(next);
        setSession(next);
        setActiveTab("overview");
    }

    // ---------------- Navigation ----------------

    // The current page lives in the URL hash (#queue, #users…) so a
    // refresh keeps you where you were and pages can be linked to.
    const [activeTab, setActiveTabState] = useState(
        () => window.location.hash.replace("#", "") || (getSession()?.portal === "employee" ? "queue" : "overview")
    );

    function setActiveTab(id) {
        setActiveTabState(id);
        if (window.location.hash !== `#${id}`) {
            window.history.replaceState(null, "", `#${id}`);
        }
    }

    useEffect(() => {
        const onHash = () => {
            const id = window.location.hash.replace("#", "");
            if (id) setActiveTabState(id);
        };
        window.addEventListener("hashchange", onHash);
        return () => window.removeEventListener("hashchange", onHash);
    }, []);
    const [newSearchTrigger, setNewSearchTrigger] = useState(0);
    const [pendingCount, setPendingCount] = useState(0);

    const portal = session?.portal === "admin" ? "admin" : "employee";
    const isAdminPortal = portal === "admin";

    const refreshPending = useCallback(async () => {
        try {
            const data = await getEscalations("PENDING");
            setPendingCount(data.count || 0);
        } catch {
            // Ignore: the badge simply stays as it was.
        }
    }, []);

    useEffect(() => {
        if (authState !== "signed-in") return undefined;
        const initial = setTimeout(refreshPending, 0);
        const interval = setInterval(refreshPending, 30000);
        return () => {
            clearTimeout(initial);
            clearInterval(interval);
        };
    }, [authState, refreshPending]);

    function navigate(id) {
        setActiveTab(id);
        setNavOpen(false);
    }

    // ---------------- Search history ----------------

    const historyKey = `semantic-ai-history-${session?.user?.username || "anon"}`;
    const [historyState, setHistoryState] = useState({ key: null, items: [] });
    const history = historyState.key === historyKey ? historyState.items : readJson(historyKey, []);

    function setHistory(items) {
        setHistoryState({ key: historyKey, items });
        writeJson(historyKey, items);
    }

    const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

    function handleSaveToHistory({ query, answer, sources, meta }) {
        if (!query.trim() || !answer.trim()) return;

        const rest = history.filter((item) => item.query.toLowerCase() !== query.trim().toLowerCase());
        const item = {
            id: Date.now().toString(),
            query: query.trim(),
            answer,
            sources,
            meta,
            timestamp: new Date().toISOString()
        };

        setHistory([item, ...rest].slice(0, 30));
    }

    // ---------------- Render ----------------

    if (authState === "loading") {
        return <div className="empty" style={{ paddingTop: "30vh" }}>Connecting…</div>;
    }

    if (authState === "offline") {
        return (
            <div className="page" style={{ maxWidth: 520, paddingTop: "18vh" }}>
                <div className="card card-body stack">
                    <h1 className="section-title" style={{ fontSize: 16 }}>Can't reach the backend</h1>
                    <p className="muted small">
                        Start the API on port 8000, then try again:
                    </p>
                    <code className="tag" style={{ height: "auto", padding: "6px 8px", whiteSpace: "normal" }}>
                        venv\Scripts\python -m uvicorn backend.api.app:app --port 8000
                    </code>
                    <div>
                        <button className="btn btn-primary" onClick={() => { setAuthState("loading"); checkSession(); }}>
                            Try again
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (authState !== "signed-in" || !session) {
        return <LoginPage status={authStatus} onSignedIn={handleSignedIn} notice={notice} />;
    }

    const groups = NAV[portal];
    const allItems = groups.flatMap((group) => group.items);
    const tab = allItems.some((item) => item.id === activeTab) ? activeTab : allItems[0].id;
    const title = allItems.find((item) => item.id === tab)?.label;

    function renderPage() {
        switch (tab) {
            case "overview":
                return <AnalyticsPage isAdmin={isAdminPortal} />;
            case "queue":
                return <ReviewQueuePage onChange={refreshPending} />;
            case "automation":
                return <AutomationDashboard isAdmin={isAdminPortal} onChange={refreshPending} />;
            case "documents":
                return <DocumentManager readOnly={!isAdminPortal} />;
            case "users":
                return <UsersPage currentUser={session.user} />;
            case "audit":
                return <AuditLogPage />;
            case "system":
                return <SystemPage />;
            default:
                return (
                    <Home
                        newSearchTrigger={newSearchTrigger}
                        selectedHistoryItem={selectedHistoryItem}
                        history={history}
                        onSaveToHistory={handleSaveToHistory}
                        onSelectHistory={setSelectedHistoryItem}
                        onClearHistory={() => setHistory([])}
                        onStartNewSearch={() => setSelectedHistoryItem(null)}
                    />
                );
        }
    }

    return (
        <div className={`shell ${navOpen ? "nav-open" : ""}`} data-portal={portal}>
            <Sidebar
                portal={portal}
                groups={groups}
                activeTab={tab}
                onNavigate={navigate}
                pendingCount={pendingCount}
                user={session.user}
                method={session.method}
                darkMode={darkMode}
                onToggleTheme={toggleTheme}
                onChangePassword={() => setPasswordOpen(true)}
                onSwitchPortal={session.user.role === "admin" ? switchPortal : null}
                onSignOut={() => signOut("")}
            />
            {navOpen && <div className="side-scrim" onClick={() => setNavOpen(false)} />}

            <main className="shell-main">
                <PortalHeader portal={portal} title={title} onOpenNav={() => setNavOpen(true)}>
                    {tab === "search" && (
                        <button
                            className="btn btn-sm"
                            onClick={() => {
                                setSelectedHistoryItem(null);
                                setNewSearchTrigger((value) => value + 1);
                            }}
                        >
                            New question
                        </button>
                    )}
                </PortalHeader>
                {renderPage()}
            </main>

            {passwordOpen && <ChangePasswordModal onClose={() => setPasswordOpen(false)} />}
        </div>
    );
}

export default App;
