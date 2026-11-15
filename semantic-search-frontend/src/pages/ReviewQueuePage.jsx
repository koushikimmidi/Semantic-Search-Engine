import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, Inbox, Search, Send } from "lucide-react";
import { getEscalations, replyToEscalation, resolveEscalation } from "../services/api";
import { Notice } from "../components/ui";
import { formatDateTime, formatIntent, timeAgo } from "../utils/format";
import "../styles/work.css";

/**
 * Emails the assistant was not confident enough to answer.
 * Employees reply in the student's email thread or mark them resolved.
 */
function ReviewQueuePage({ onChange }) {
    const [status, setStatus] = useState("PENDING");
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [flash, setFlash] = useState(null);
    const [filter, setFilter] = useState("");
    const [selectedId, setSelectedId] = useState(null);
    const [drafts, setDrafts] = useState({});
    const [notes, setNotes] = useState({});
    const [busy, setBusy] = useState(false);

    const load = useCallback(async () => {
        try {
            const data = await getEscalations(status === "ALL" ? null : status);
            setItems(data.escalations || []);
            setError("");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [status]);

    useEffect(() => {
        const initial = setTimeout(load, 0);
        const interval = setInterval(load, 20000);
        return () => {
            clearTimeout(initial);
            clearInterval(interval);
        };
    }, [load]);

    const visible = useMemo(() => {
        const needle = filter.trim().toLowerCase();
        if (!needle) return items;
        return items.filter((item) =>
            [item.subject, item.body, item.sender, formatIntent(item.intent)].join(" ").toLowerCase().includes(needle)
        );
    }, [items, filter]);

    const selected = visible.find((item) => item.id === selectedId) || visible[0] || null;
    const draft = selected ? (drafts[selected.id] ?? selected.suggested_answer ?? "") : "";

    async function act(kind) {
        if (!selected) return;
        setBusy(true);
        setFlash(null);
        try {
            if (kind === "reply") {
                await replyToEscalation(selected.id, draft, notes[selected.id]);
                setFlash({ tone: "ok", text: `Reply sent to ${selected.sender_email || selected.sender}.` });
            } else {
                await resolveEscalation(selected.id, notes[selected.id]);
                setFlash({ tone: "ok", text: "Marked as resolved." });
            }
            setSelectedId(null);
        } catch (err) {
            setFlash({ tone: "bad", text: kind === "reply" ? `Reply not sent: ${err.message}` : err.message });
        } finally {
            setBusy(false);
            load();
            onChange && onChange();
        }
    }

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>Review queue</h1>
                    <p>Emails the assistant wasn't confident enough to answer on its own.</p>
                </div>
                <div className="segmented" role="tablist" aria-label="Status">
                    {[["PENDING", "Open"], ["RESOLVED", "Resolved"], ["ALL", "All"]].map(([value, label]) => (
                        <button key={value} role="tab" aria-selected={status === value}
                            className={status === value ? "active" : ""}
                            onClick={() => { setLoading(true); setSelectedId(null); setStatus(value); }}>
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {error && <Notice tone="bad">{error}</Notice>}
            {flash && <Notice tone={flash.tone} onClose={() => setFlash(null)}>{flash.text}</Notice>}

            <div className="card queue">
                <div className="queue-list">
                    <div className="queue-search">
                        <Search size={15} className="faint" />
                        <input className="queue-search-input" placeholder="Filter" value={filter}
                            onChange={(e) => setFilter(e.target.value)} aria-label="Filter messages" />
                    </div>

                    {loading ? (
                        <p className="empty">Loading…</p>
                    ) : visible.length === 0 ? (
                        <div className="empty">
                            <Inbox size={20} style={{ marginBottom: 6 }} />
                            <div>{status === "PENDING" ? "Nothing waiting for review." : "No messages."}</div>
                        </div>
                    ) : (
                        <ul>
                            {visible.map((item) => (
                                <li key={item.id}>
                                    <button
                                        className={`queue-item ${selected?.id === item.id ? "active" : ""}`}
                                        onClick={() => setSelectedId(item.id)}
                                    >
                                        <span className="queue-item-top">
                                            <strong>{item.subject || "(no subject)"}</strong>
                                            <span className="faint small">{timeAgo(item.timestamp)}</span>
                                        </span>
                                        <span className="queue-item-from">{item.sender_email || item.sender}</span>
                                        <span className="queue-item-preview">{item.body}</span>
                                        <span className="row" style={{ marginTop: 4 }}>
                                            <span className="tag">{formatIntent(item.intent)}</span>
                                            {item.status === "RESOLVED" && <span className="status ok">Resolved</span>}
                                        </span>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="queue-detail">
                    {!selected ? (
                        <p className="empty">Select a message to read it.</p>
                    ) : (
                        <>
                            <div className="queue-detail-head">
                                <h2>{selected.subject || "(no subject)"}</h2>
                                <div className="row small muted">
                                    <span>{selected.sender}</span>
                                    <span className="faint">·</span>
                                    <span>{formatDateTime(selected.timestamp)}</span>
                                    <span className="faint">·</span>
                                    <span className="tag">{formatIntent(selected.intent)}</span>
                                </div>
                            </div>

                            <div className="queue-message">{selected.body}</div>

                            <div className="queue-why small">
                                <span className="faint">Why it's here: </span>
                                {selected.confidence?.reason || selected.reason}
                            </div>

                            {selected.status === "PENDING" ? (
                                <div className="queue-reply">
                                    <label className="field">
                                        <span>Reply</span>
                                        <textarea
                                            rows={6}
                                            value={draft}
                                            placeholder="Write a reply to the student…"
                                            onChange={(e) => setDrafts({ ...drafts, [selected.id]: e.target.value })}
                                        />
                                        <small>
                                            {selected.suggested_answer
                                                ? "Pre-filled with the assistant's draft. Edit before sending."
                                                : "The assistant had no draft for this one."}
                                            {" "}Sent in the same email thread.
                                        </small>
                                    </label>
                                    <label className="field">
                                        <span>Internal note <span className="faint" style={{ fontWeight: 400 }}>(optional)</span></span>
                                        <input value={notes[selected.id] || ""} onChange={(e) => setNotes({ ...notes, [selected.id]: e.target.value })} />
                                    </label>
                                    <div className="row" style={{ justifyContent: "flex-end" }}>
                                        <button className="btn" onClick={() => act("resolve")} disabled={busy}>
                                            <Check size={15} /> Resolve without reply
                                        </button>
                                        <button className="btn btn-primary" onClick={() => act("reply")} disabled={busy || !draft.trim()}>
                                            <Send size={14} /> {busy ? "Sending…" : "Send reply"}
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="queue-resolved">
                                    {selected.reply && (
                                        <>
                                            <div className="faint small">Reply sent</div>
                                            <div className="queue-message">{selected.reply}</div>
                                        </>
                                    )}
                                    <div className="small muted">
                                        Resolved {formatDateTime(selected.resolved_at)}
                                        {selected.resolved_by && <> by <strong>{selected.resolved_by}</strong></>}
                                        {selected.resolution_note && <> · {selected.resolution_note}</>}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ReviewQueuePage;
