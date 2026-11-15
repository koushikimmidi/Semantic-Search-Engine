import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { getAuditLog } from "../services/api";
import { Notice } from "../components/ui";

const PAGE_SIZE = 50;

const ACTIONS = {
    login: "Signed in",
    login_failed: "Failed sign-in",
    setup_admin_created: "Set up admin account",
    setup_failed: "Failed setup attempt",
    password_changed: "Changed password",
    user_created: "Created user",
    user_updated: "Updated user",
    user_deleted: "Deleted user",
    documents_uploaded: "Added documents",
    document_deleted: "Deleted document",
    reindex: "Re-indexed documents",
    settings_changed: "Changed settings",
    scheduler_started: "Started scheduler",
    scheduler_stopped: "Stopped scheduler",
    inbox_run: "Checked inbox",
    test_message: "Tried a message",
    escalation_resolved: "Resolved review item",
    escalation_replied: "Replied to student"
};

const WARN_ACTIONS = new Set(["login_failed", "setup_failed", "user_deleted", "document_deleted"]);

const label = (action) => ACTIONS[action] || action.replace(/_/g, " ");

function describe(details) {
    if (!details || typeof details !== "object") return details || "";
    return Object.entries(details)
        .map(([key, value]) => `${key.replace(/_/g, " ")} ${typeof value === "object" ? JSON.stringify(value) : value}`)
        .join(" · ");
}

function AuditLogPage() {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [actions, setActions] = useState([]);
    const [action, setAction] = useState("");
    const [actor, setActor] = useState("");
    const [offset, setOffset] = useState(0);
    const [error, setError] = useState("");

    const load = useCallback(async () => {
        try {
            const data = await getAuditLog({ limit: PAGE_SIZE, offset, action, actor: actor.trim() });
            setItems(data.items || []);
            setTotal(data.total || 0);
            setActions(data.actions || []);
            setError("");
        } catch (err) {
            setError(err.message);
        }
    }, [offset, action, actor]);

    useEffect(() => {
        const id = setTimeout(load, 250);
        return () => clearTimeout(id);
    }, [load]);

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>Audit log</h1>
                    <p>Sign-ins, setting changes, document changes and review actions, with who did them.</p>
                </div>
                <div className="row">
                    <select className="input" style={{ width: 200 }} value={action} aria-label="Action"
                        onChange={(e) => { setOffset(0); setAction(e.target.value); }}>
                        <option value="">All actions</option>
                        {actions.map((value) => <option key={value} value={value}>{label(value)}</option>)}
                    </select>
                    <input className="input" style={{ width: 160 }} placeholder="Username" value={actor} aria-label="Username"
                        onChange={(e) => { setOffset(0); setActor(e.target.value); }} />
                </div>
            </div>

            {error && <Notice tone="bad">{error}</Notice>}

            <div className="card">
                {items.length === 0 ? (
                    <p className="empty">No events match.</p>
                ) : (
                    <div className="table-wrap">
                        <table className="table">
                            <thead>
                                <tr><th>Time</th><th>Who</th><th>What</th><th>Details</th></tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id}>
                                        <td className="muted mono small" style={{ whiteSpace: "nowrap" }}>
                                            {new Date(item.timestamp).toLocaleString(undefined, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                                        </td>
                                        <td style={{ whiteSpace: "nowrap" }}>
                                            {item.actor}
                                            <span className="cell-sub">{item.role}</span>
                                        </td>
                                        <td>
                                            <span className={WARN_ACTIONS.has(item.action) ? "status warn" : ""}>{label(item.action)}</span>
                                            {item.target && <span className="cell-sub">{item.target}</span>}
                                        </td>
                                        <td className="muted small">{describe(item.details)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
                <div className="card-foot small">
                    <span className="faint num">
                        {total === 0 ? "0 events" : `${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}`}
                    </span>
                    <div className="row">
                        <button className="btn btn-sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
                            <ChevronLeft size={14} /> Newer
                        </button>
                        <button className="btn btn-sm" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>
                            Older <ChevronRight size={14} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AuditLogPage;
