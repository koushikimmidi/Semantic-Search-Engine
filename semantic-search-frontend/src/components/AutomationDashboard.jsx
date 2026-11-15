import { useCallback, useEffect, useState } from "react";
import { Play, RefreshCw, Square } from "lucide-react";
import {
    getAutomationDashboard,
    getAutomationHistory,
    processTestMessage,
    runAutomation,
    startScheduler,
    stopScheduler
} from "../services/api";
import { Notice } from "./ui";
import { formatDateTime, formatIntent } from "../utils/format";
import "../styles/work.css";

const ROUTE_LABEL = {
    AUTO_REPLY: ["ok", "Would be answered automatically"],
    HUMAN_REVIEW: ["warn", "Sent to the review queue"],
    SKIPPED: ["", "Skipped (automated email)"]
};

/**
 * Admins: inbox controls, scheduler, test messages, run history.
 * Employees: test messages and run history.
 */
function AutomationDashboard({ isAdmin = false, onChange }) {
    const [dashboard, setDashboard] = useState(null);
    const [history, setHistory] = useState([]);
    const [error, setError] = useState("");
    const [running, setRunning] = useState(false);
    const [runResult, setRunResult] = useState(null);
    const [schedulerBusy, setSchedulerBusy] = useState(false);

    const [test, setTest] = useState({
        sender: "student@example.com",
        subject: "Refund request",
        body: "How many days do I have to ask for a refund?"
    });
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState(null);

    const refresh = useCallback(async () => {
        try {
            const [d, h] = await Promise.all([getAutomationDashboard(), getAutomationHistory()]);
            setDashboard(d.dashboard);
            setHistory((h.history || []).slice().reverse());
            setError("");
        } catch (err) {
            setError(err.message);
        }
    }, []);

    useEffect(() => {
        const initial = setTimeout(refresh, 0);
        const interval = setInterval(refresh, 15000);
        return () => {
            clearTimeout(initial);
            clearInterval(interval);
        };
    }, [refresh]);

    async function checkInbox() {
        setRunning(true);
        setRunResult(null);
        try {
            const { summary } = await runAutomation();
            setRunResult({ tone: "ok", summary });
        } catch (err) {
            setRunResult({ tone: "bad", text: err.message });
        } finally {
            setRunning(false);
            refresh();
            onChange && onChange();
        }
    }

    async function toggleScheduler() {
        setSchedulerBusy(true);
        try {
            if (dashboard?.scheduler?.running) await stopScheduler();
            else await startScheduler();
        } catch (err) {
            setError(err.message);
        } finally {
            setSchedulerBusy(false);
            refresh();
        }
    }

    async function runTest(event) {
        event.preventDefault();
        if (!test.body.trim()) return;
        setTesting(true);
        setTestResult(null);
        try {
            setTestResult(await processTestMessage(test));
        } catch (err) {
            setTestResult({ error: err.message });
        } finally {
            setTesting(false);
            refresh();
            onChange && onChange();
        }
    }

    const schedulerOn = Boolean(dashboard?.scheduler?.running);
    const [routeTone, routeText] = ROUTE_LABEL[testResult?.route] || ["", testResult?.route];

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>{isAdmin ? "Email automation" : "Test a message"}</h1>
                    <p>
                        {isAdmin
                            ? "Check the support inbox, run it on a schedule, and see how messages would be handled."
                            : "See how the assistant would handle an email. Nothing is sent."}
                    </p>
                </div>
            </div>

            {error && <Notice tone="bad">{error}</Notice>}

            {isAdmin && dashboard && (
                <div className="metrics">
                    <div className="metric">
                        <div className="metric-label">Inbox checks</div>
                        <div className="metric-value">{dashboard.total_executions}</div>
                    </div>
                    <div className="metric">
                        <div className="metric-label">Emails read</div>
                        <div className="metric-value">{dashboard.total_fetched}</div>
                    </div>
                    <div className="metric">
                        <div className="metric-label">Answered automatically</div>
                        <div className="metric-value">{dashboard.total_auto_reply}</div>
                    </div>
                    <div className="metric">
                        <div className="metric-label">Sent to people</div>
                        <div className="metric-value">{dashboard.total_human_review}</div>
                    </div>
                    <div className={`metric ${dashboard.pending_reviews ? "attention" : ""}`}>
                        <div className="metric-label">Waiting for review</div>
                        <div className="metric-value">{dashboard.pending_reviews ?? 0}</div>
                    </div>
                </div>
            )}

            <div className={isAdmin ? "grid-2" : ""} style={isAdmin ? undefined : { maxWidth: 680 }}>
                {isAdmin && (
                    <div className="card">
                        <div className="card-head">
                            <div>
                                <div className="section-title">Inbox</div>
                                <div className="section-sub">
                                    Automatic replies are {dashboard?.email_sending ? <strong>on</strong> : <strong>off</strong>}.
                                    {!dashboard?.email_sending && " Answers are written but not sent. Change this in System."}
                                </div>
                            </div>
                        </div>
                        <div className="card-body stack">
                            <div className="setting">
                                <div>
                                    <strong>Check now</strong>
                                    <p>Read unread emails and handle them once.</p>
                                </div>
                                <button className="btn btn-primary" onClick={checkInbox} disabled={running}>
                                    <RefreshCw size={14} className={running ? "spin" : ""} />
                                    {running ? "Checking…" : "Check inbox"}
                                </button>
                            </div>
                            <div className="setting">
                                <div>
                                    <strong>Scheduler</strong>
                                    <p>
                                        <span className={`status ${schedulerOn ? "ok" : ""}`}>{schedulerOn ? "Running" : "Stopped"}</span>
                                        <span className="faint"> · every {Math.round((dashboard?.scheduler?.interval_seconds || 0) / 60)} min</span>
                                    </p>
                                </div>
                                <button className="btn" onClick={toggleScheduler} disabled={schedulerBusy}>
                                    {schedulerOn ? <Square size={13} /> : <Play size={13} />}
                                    {schedulerOn ? "Stop" : "Start"}
                                </button>
                            </div>
                            {runResult && (
                                runResult.tone === "bad" ? (
                                    <Notice tone="bad">{runResult.text}</Notice>
                                ) : (
                                    <Notice tone="ok">
                                        Read {runResult.summary.fetched} · handled {runResult.summary.processed} ·
                                        skipped {runResult.summary.skipped} — {runResult.summary.auto_reply} automatic,
                                        {" "}{runResult.summary.human_review} to review, {runResult.summary.failed} failed.
                                    </Notice>
                                )
                            )}
                        </div>
                    </div>
                )}

                <form className="card" onSubmit={runTest}>
                    <div className="card-head">
                        <div>
                            <div className="section-title">Try a message</div>
                            <div className="section-sub">Runs the full pipeline without touching Gmail.</div>
                        </div>
                    </div>
                    <div className="card-body stack">
                        <div className="grid-2" style={{ gap: 12 }}>
                            <label className="field">
                                <span>From</span>
                                <input value={test.sender} onChange={(e) => setTest({ ...test, sender: e.target.value })} />
                            </label>
                            <label className="field">
                                <span>Subject</span>
                                <input value={test.subject} onChange={(e) => setTest({ ...test, subject: e.target.value })} />
                            </label>
                        </div>
                        <label className="field">
                            <span>Message</span>
                            <textarea rows={3} value={test.body} onChange={(e) => setTest({ ...test, body: e.target.value })} />
                        </label>
                        <div>
                            <button className="btn btn-primary" type="submit" disabled={testing}>
                                {testing ? "Processing…" : "Run"}
                            </button>
                        </div>

                        {testResult && (
                            testResult.error ? (
                                <Notice tone="bad">{testResult.error}</Notice>
                            ) : (
                                <div className="result-block">
                                    <div className="row">
                                        <span className={`status ${routeTone}`}>{routeText}</span>
                                        <span className="tag">{formatIntent(testResult.intent?.intent)}</span>
                                        {testResult.confidence?.level && (
                                            <span className="faint small">{testResult.confidence.level.toLowerCase()} confidence</span>
                                        )}
                                    </div>
                                    <p>{testResult.email_body || testResult.answer}</p>
                                    {testResult.confidence?.reason && <div className="small faint">{testResult.confidence.reason}</div>}
                                </div>
                            )
                        )}
                    </div>
                </form>
            </div>

            <div className="card">
                <div className="card-head">
                    <div>
                        <div className="section-title">Recent inbox checks</div>
                        <div className="section-sub">Scheduled and manual runs.</div>
                    </div>
                </div>
                <div className="card-body" style={{ padding: "8px 4px 4px" }}>
                    {history.length === 0 ? (
                        <p className="empty">No inbox checks yet.</p>
                    ) : (
                        <div className="table-wrap">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>When</th>
                                        <th className="right">Read</th>
                                        <th className="right">Handled</th>
                                        <th className="right">Skipped</th>
                                        <th className="right">Automatic</th>
                                        <th className="right">To review</th>
                                        <th className="right">Failed</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.slice(0, 12).map((row) => (
                                        <tr key={row.timestamp}>
                                            <td>{formatDateTime(row.timestamp)}</td>
                                            <td className="right">{row.fetched}</td>
                                            <td className="right">{row.processed}</td>
                                            <td className="right">{row.skipped}</td>
                                            <td className="right">{row.auto_reply}</td>
                                            <td className="right">{row.human_review}</td>
                                            <td className="right">{row.failed}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AutomationDashboard;
