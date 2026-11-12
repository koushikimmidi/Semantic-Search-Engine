import { useState, useEffect, useCallback } from "react";
import {
    getAutomationDashboard,
    getAutomationHistory,
    runAutomation,
    startScheduler,
    stopScheduler,
    processTestMessage,
    getEscalations,
    resolveEscalation
} from "../services/api";
import "../styles/document-manager.css";
import "../styles/automation.css";

function formatIntent(intent) {
    if (!intent) return "—";
    return intent
        .toLowerCase()
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function formatTime(iso) {
    if (!iso) return "—";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function RouteBadge({ route }) {
    if (!route) return null;
    const isAuto = route === "AUTO_REPLY";
    return (
        <span className={`auto-badge ${isAuto ? "auto" : "review"}`}>
            {isAuto ? "Auto reply" : "Human review"}
        </span>
    );
}

function AutomationDashboard() {
    const [dashboard, setDashboard] = useState(null);
    const [history, setHistory] = useState([]);
    const [escalations, setEscalations] = useState([]);
    const [showResolved, setShowResolved] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [running, setRunning] = useState(false);
    const [runMessage, setRunMessage] = useState("");
    const [schedulerBusy, setSchedulerBusy] = useState(false);

    const [testMessage, setTestMessage] = useState({
        sender: "student@example.com",
        subject: "Refund request",
        body: "What is the refund period for my course?"
    });
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState(null);

    const [notes, setNotes] = useState({});

    const refresh = useCallback(async () => {
        try {
            const [dashboardData, historyData, escalationData] = await Promise.all([
                getAutomationDashboard(),
                getAutomationHistory(),
                getEscalations(showResolved ? null : "PENDING")
            ]);
            setDashboard(dashboardData.dashboard);
            setHistory((historyData.history || []).slice().reverse());
            setEscalations(escalationData.escalations || []);
            setError("");
        } catch (err) {
            console.error(err);
            setError(err.message || "Could not reach the automation API.");
        } finally {
            setLoading(false);
        }
    }, [showResolved]);

    useEffect(() => {
        const initial = setTimeout(refresh, 0);
        const interval = setInterval(refresh, 15000);
        return () => {
            clearTimeout(initial);
            clearInterval(interval);
        };
    }, [refresh]);

    async function handleRun() {
        setRunning(true);
        setRunMessage("");
        try {
            const data = await runAutomation();
            const s = data.summary || {};
            setRunMessage(
                `Fetched ${s.fetched ?? 0}, processed ${s.processed ?? 0}, ` +
                `skipped ${s.skipped ?? 0} · ${s.auto_reply ?? 0} auto reply, ` +
                `${s.human_review ?? 0} human review, ${s.failed ?? 0} failed.`
            );
        } catch (err) {
            setRunMessage(`Run failed: ${err.message}`);
        } finally {
            setRunning(false);
            refresh();
        }
    }

    async function handleScheduler() {
        setSchedulerBusy(true);
        try {
            if (dashboard?.scheduler?.running) {
                await stopScheduler();
            } else {
                await startScheduler();
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setSchedulerBusy(false);
            refresh();
        }
    }

    async function handleTest(event) {
        event.preventDefault();
        if (!testMessage.body.trim()) return;
        setTesting(true);
        setTestResult(null);
        try {
            const data = await processTestMessage(testMessage);
            setTestResult(data);
        } catch (err) {
            setTestResult({ error: err.message });
        } finally {
            setTesting(false);
            refresh();
        }
    }

    async function handleResolve(id) {
        try {
            await resolveEscalation(id, notes[id]);
            setNotes((current) => {
                const next = { ...current };
                delete next[id];
                return next;
            });
        } catch (err) {
            setError(err.message);
        } finally {
            refresh();
        }
    }

    const stats = dashboard
        ? [
            { label: "Runs", value: dashboard.total_executions },
            { label: "Emails fetched", value: dashboard.total_fetched },
            { label: "Processed", value: dashboard.total_processed },
            { label: "Auto replies", value: dashboard.total_auto_reply },
            { label: "Human review", value: dashboard.total_human_review },
            { label: "Pending reviews", value: dashboard.pending_reviews ?? 0, highlight: true },
            { label: "Success rate", value: `${dashboard.success_rate}%` }
        ]
        : [];

    const schedulerRunning = Boolean(dashboard?.scheduler?.running);

    return (
        <section className="doc-manager-section automation-section">
            <div className="doc-manager-header">
                <h2>Email Automation</h2>
                <p>
                    Reads unread support emails, answers them from the knowledge base, and
                    routes low-confidence messages to a human review queue.
                </p>
            </div>

            {error && <div className="auto-error">{error}</div>}

            {loading ? (
                <div className="card auto-empty">Loading automation status…</div>
            ) : (
                <>
                    <div className="auto-stats">
                        {stats.map((stat) => (
                            <div
                                key={stat.label}
                                className={`card auto-stat ${stat.highlight && stat.value > 0 ? "highlight" : ""}`}
                            >
                                <span className="auto-stat-label">{stat.label}</span>
                                <strong className="auto-stat-value">{stat.value}</strong>
                            </div>
                        ))}
                    </div>

                    <div className="auto-grid">
                        <div className="card">
                            <h3>Inbox controls</h3>
                            <p className="subtitle">
                                Email sending is{" "}
                                <strong>{dashboard?.email_sending ? "ON" : "OFF (safe mode)"}</strong>.
                                {!dashboard?.email_sending && " Answers are generated but not sent."}
                            </p>

                            <div className="auto-controls">
                                <button
                                    className="auto-btn primary"
                                    onClick={handleRun}
                                    disabled={running}
                                >
                                    {running ? "Checking inbox…" : "Check inbox now"}
                                </button>

                                <button
                                    className={`auto-btn ${schedulerRunning ? "danger" : ""}`}
                                    onClick={handleScheduler}
                                    disabled={schedulerBusy}
                                >
                                    {schedulerRunning ? "Stop scheduler" : "Start scheduler"}
                                </button>
                            </div>

                            <div className="auto-scheduler-status">
                                <span className={`status-dot ${schedulerRunning ? "online" : "offline"}`}></span>
                                Scheduler {schedulerRunning ? "running" : "stopped"} · every{" "}
                                {dashboard?.scheduler?.interval_seconds ?? "—"}s
                            </div>

                            {runMessage && <p className="auto-run-message">{runMessage}</p>}
                        </div>

                        <form className="card" onSubmit={handleTest}>
                            <h3>Test a message</h3>
                            <p className="subtitle">
                                Runs one email through the pipeline without touching Gmail.
                            </p>

                            <label className="auto-field">
                                <span>From</span>
                                <input
                                    value={testMessage.sender}
                                    onChange={(e) => setTestMessage({ ...testMessage, sender: e.target.value })}
                                />
                            </label>
                            <label className="auto-field">
                                <span>Subject</span>
                                <input
                                    value={testMessage.subject}
                                    onChange={(e) => setTestMessage({ ...testMessage, subject: e.target.value })}
                                />
                            </label>
                            <label className="auto-field">
                                <span>Message</span>
                                <textarea
                                    rows={3}
                                    value={testMessage.body}
                                    onChange={(e) => setTestMessage({ ...testMessage, body: e.target.value })}
                                />
                            </label>

                            <button className="auto-btn primary" type="submit" disabled={testing}>
                                {testing ? "Processing…" : "Process message"}
                            </button>

                            {testResult && (
                                <div className="auto-test-result">
                                    {testResult.error ? (
                                        <p className="auto-error-text">{testResult.error}</p>
                                    ) : (
                                        <>
                                            <div className="auto-test-row">
                                                <RouteBadge route={testResult.route} />
                                                <span>Intent: {formatIntent(testResult.intent?.intent)}</span>
                                                <span>Confidence: {testResult.confidence?.level ?? "—"}</span>
                                            </div>
                                            <p className="auto-answer">{testResult.answer}</p>
                                            {testResult.confidence?.reason && (
                                                <p className="auto-reason">{testResult.confidence.reason}</p>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}
                        </form>
                    </div>

                    <div className="card auto-queue">
                        <div className="auto-queue-header">
                            <div>
                                <h3>Human review queue</h3>
                                <p className="subtitle">
                                    Messages the system was not confident enough to answer automatically.
                                </p>
                            </div>
                            <label className="auto-toggle">
                                <input
                                    type="checkbox"
                                    checked={showResolved}
                                    onChange={(e) => setShowResolved(e.target.checked)}
                                />
                                Show resolved
                            </label>
                        </div>

                        {escalations.length === 0 ? (
                            <div className="auto-empty">No messages waiting for review.</div>
                        ) : (
                            <div className="auto-queue-list">
                                {escalations.map((item) => (
                                    <article key={item.id} className="auto-queue-item">
                                        <header>
                                            <div>
                                                <strong>{item.subject || "(no subject)"}</strong>
                                                <span className="auto-meta">
                                                    {item.sender} · {formatTime(item.timestamp)} ·{" "}
                                                    {formatIntent(item.intent?.intent)}
                                                </span>
                                            </div>
                                            <span className={`auto-badge ${item.status === "PENDING" ? "review" : "auto"}`}>
                                                {item.status === "PENDING" ? "Pending" : "Resolved"}
                                            </span>
                                        </header>

                                        <p className="auto-body">{item.body}</p>

                                        {item.suggested_answer && (
                                            <p className="auto-suggested">
                                                <span>Suggested answer:</span> {item.suggested_answer}
                                            </p>
                                        )}

                                        <p className="auto-reason">{item.confidence?.reason || item.reason}</p>

                                        {item.status === "PENDING" ? (
                                            <div className="auto-resolve">
                                                <input
                                                    placeholder="Resolution note (optional)"
                                                    value={notes[item.id] || ""}
                                                    onChange={(e) => setNotes({ ...notes, [item.id]: e.target.value })}
                                                />
                                                <button className="auto-btn" onClick={() => handleResolve(item.id)}>
                                                    Mark resolved
                                                </button>
                                            </div>
                                        ) : (
                                            item.resolution_note && (
                                                <p className="auto-reason">Note: {item.resolution_note}</p>
                                            )
                                        )}
                                    </article>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="card">
                        <h3>Run history</h3>
                        <p className="subtitle">The 15 most recent inbox checks.</p>

                        {history.length === 0 ? (
                            <div className="auto-empty">No runs yet.</div>
                        ) : (
                            <div className="auto-table-wrap">
                                <table className="auto-table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Fetched</th>
                                            <th>Processed</th>
                                            <th>Skipped</th>
                                            <th>Auto reply</th>
                                            <th>Review</th>
                                            <th>Failed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history.slice(0, 15).map((row) => (
                                            <tr key={row.timestamp}>
                                                <td>{formatTime(row.timestamp)}</td>
                                                <td>{row.fetched}</td>
                                                <td>{row.processed}</td>
                                                <td>{row.skipped}</td>
                                                <td>{row.auto_reply}</td>
                                                <td>{row.human_review}</td>
                                                <td>{row.failed}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </section>
    );
}

export default AutomationDashboard;
