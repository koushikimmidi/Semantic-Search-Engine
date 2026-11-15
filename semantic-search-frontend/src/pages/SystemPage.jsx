import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { getSystemInfo, reindexKnowledgeBase, startScheduler, stopScheduler, updateSettings } from "../services/api";
import { Notice } from "../components/ui";

function Health({ ok, okText, badText, warn = false }) {
    return <span className={`status ${ok ? "ok" : warn ? "warn" : "bad"}`}>{ok ? okText : badText}</span>;
}

function Switch({ checked, onChange, disabled, label }) {
    return (
        <label className="switch">
            <input type="checkbox" role="switch" aria-label={label} checked={checked} disabled={disabled}
                onChange={(e) => onChange(e.target.checked)} />
            <span />
        </label>
    );
}

function SystemPage() {
    const [info, setInfo] = useState(null);
    const [flash, setFlash] = useState(null);
    const [busy, setBusy] = useState(false);
    const [minutes, setMinutes] = useState("");

    const load = useCallback(async () => {
        try {
            const data = await getSystemInfo();
            setInfo(data);
            setMinutes(String(Math.round(data.automation.scheduler_interval_seconds / 60)));
        } catch (err) {
            setFlash({ tone: "bad", text: err.message });
        }
    }, []);

    useEffect(() => {
        const initial = setTimeout(load, 0);
        return () => clearTimeout(initial);
    }, [load]);

    async function act(action, success) {
        setBusy(true);
        setFlash(null);
        try {
            const result = await action();
            setFlash({ tone: "ok", text: typeof success === "function" ? success(result) : success });
        } catch (err) {
            setFlash({ tone: "bad", text: err.message });
        } finally {
            setBusy(false);
            load();
        }
    }

    if (!info) {
        return <div className="page">{flash ? <Notice tone={flash.tone}>{flash.text}</Notice> : <p className="empty">Loading…</p>}</div>;
    }

    const { engine, llm, confidence, automation, access } = info;
    const llmReady = llm.reachable && llm.model_available;
    const intervalChanged = Number(minutes) * 60 !== automation.scheduler_interval_seconds;

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>System</h1>
                    <p>Component health, and the settings that control how email is handled.</p>
                </div>
            </div>

            {flash && <Notice tone={flash.tone} onClose={() => setFlash(null)}>{flash.text}</Notice>}

            <div className="metrics">
                <div className="metric">
                    <div className="metric-label">Language model</div>
                    <div className="metric-value" style={{ fontSize: 17, marginTop: 8 }}>
                        <Health ok={llmReady} okText="Ready" badText={llm.reachable ? "Model missing" : "Offline"} />
                    </div>
                    <div className="metric-note mono">{llm.model}</div>
                </div>
                <div className="metric">
                    <div className="metric-label">Documents</div>
                    <div className="metric-value">{engine.documents}</div>
                    <div className="metric-note">{engine.chunks} indexed sections</div>
                </div>
                <div className="metric">
                    <div className="metric-label">Support inbox</div>
                    <div className="metric-value" style={{ fontSize: 17, marginTop: 8 }}>
                        <Health ok={automation.inbox_configured} okText="Connected" badText="Not set up" warn />
                    </div>
                    <div className="metric-note">{automation.inbox_address || "EMAIL_* in .env"}</div>
                </div>
                <div className="metric">
                    <div className="metric-label">People</div>
                    <div className="metric-value">{access.admins + access.employees}</div>
                    <div className="metric-note">{access.admins} admin · {access.employees} employee</div>
                </div>
            </div>

            <div className="grid-2">
                <section className="card">
                    <div className="card-head">
                        <div>
                            <div className="section-title">Email handling</div>
                            <div className="section-sub">Takes effect immediately and is kept after a restart.</div>
                        </div>
                    </div>
                    <div className="card-body">
                        <div className="setting">
                            <div>
                                <strong>Send automatic replies</strong>
                                <p>{automation.smtp_configured
                                    ? "Confident answers are emailed to students without review."
                                    : "Needs SMTP_USERNAME and SMTP_PASSWORD in .env."}</p>
                            </div>
                            <Switch
                                label="Send automatic replies"
                                checked={automation.auto_send_emails}
                                disabled={busy || (!automation.smtp_configured && !automation.auto_send_emails)}
                                onChange={(value) => {
                                    if (value && !window.confirm("Students will receive emails without anyone checking them first. Turn on automatic replies?")) return;
                                    act(() => updateSettings({ auto_send_emails: value }), value ? "Automatic replies are on." : "Automatic replies are off.");
                                }}
                            />
                        </div>
                        <div className="setting">
                            <div>
                                <strong>Mark handled emails as read</strong>
                                <p>Otherwise they stay unread in Gmail; duplicates are still skipped.</p>
                            </div>
                            <Switch
                                label="Mark handled emails as read"
                                checked={automation.mark_as_read}
                                disabled={busy}
                                onChange={(value) => act(() => updateSettings({ mark_as_read: value }), value ? "Handled emails will be marked as read." : "Handled emails will stay unread.")}
                            />
                        </div>
                        <div className="setting">
                            <div>
                                <strong>Scheduler</strong>
                                <p>
                                    <span className={`status ${automation.scheduler_running ? "ok" : ""}`}>
                                        {automation.scheduler_running ? "Running" : "Stopped"}
                                    </span>
                                </p>
                            </div>
                            <button
                                className="btn btn-sm"
                                disabled={busy || !automation.inbox_configured}
                                title={automation.inbox_configured ? undefined : "Set up the inbox in .env first"}
                                onClick={() => act(automation.scheduler_running ? stopScheduler : startScheduler,
                                    automation.scheduler_running ? "Scheduler stopped." : "Scheduler started.")}
                            >
                                {automation.scheduler_running ? "Stop" : "Start"}
                            </button>
                        </div>
                        <form
                            className="setting"
                            onSubmit={(e) => {
                                e.preventDefault();
                                act(() => updateSettings({ scheduler_interval_seconds: Math.round(Number(minutes) * 60) }),
                                    `The inbox will be checked every ${minutes} min.`);
                            }}
                        >
                            <div>
                                <strong>Check every</strong>
                                <p>Minutes between scheduled inbox checks.</p>
                            </div>
                            <div className="row" style={{ flexWrap: "nowrap" }}>
                                <input className="input input-sm num" style={{ width: 72 }} type="number" min="1" max="1440"
                                    value={minutes} onChange={(e) => setMinutes(e.target.value)} aria-label="Minutes between checks" />
                                <span className="small muted">min</span>
                                {intervalChanged && <button className="btn btn-sm btn-primary" type="submit" disabled={busy}>Save</button>}
                            </div>
                        </form>
                    </div>
                </section>

                <section className="card">
                    <div className="card-head">
                        <div>
                            <div className="section-title">Search engine</div>
                            <div className="section-sub">Retrieval models and the current index.</div>
                        </div>
                        <button className="btn btn-sm" disabled={busy}
                            onClick={() => act(reindexKnowledgeBase, (r) => `Re-indexed ${r.chunks} sections in ${r.seconds}s.`)}>
                            <RefreshCw size={13} className={busy ? "spin" : ""} /> Re-index
                        </button>
                    </div>
                    <div className="card-body">
                        <div className="kv">
                            <div className="kv-row"><span>Embedding model</span><span className="mono small">{engine.embedding_model}</span></div>
                            <div className="kv-row"><span>Reranker</span><span className="mono small">{engine.reranker_model.split("/").pop()}</span></div>
                            <div className="kv-row"><span>Section size</span><span>{engine.chunk_size} characters</span></div>
                            <div className="kv-row"><span>Candidates reranked</span><span>{engine.rerank_candidates}</span></div>
                            <div className="kv-row"><span>Intent detection</span><span>{engine.intent_classifier ? "Rules + classifier" : "Rules only"}</span></div>
                        </div>
                    </div>
                </section>
            </div>

            <div className="grid-3">
                <section className="card">
                    <div className="card-head"><div className="section-title">Language model</div></div>
                    <div className="card-body">
                        <div className="kv">
                            <div className="kv-row"><span>Model</span><span className="mono small">{llm.model}</span></div>
                            <div className="kv-row"><span>Server</span><span className="mono small">{llm.host.replace(/^https?:\/\//, "")}</span></div>
                            <div className="kv-row"><span>Reachable</span><Health ok={llm.reachable} okText="Yes" badText="No" /></div>
                            <div className="kv-row"><span>Model downloaded</span><Health ok={llm.model_available} okText="Yes" badText="No" /></div>
                        </div>
                    </div>
                </section>

                <section className="card">
                    <div className="card-head">
                        <div>
                            <div className="section-title">Auto-reply thresholds</div>
                            <div className="section-sub">Reranker score needed to answer without review. Set in .env.</div>
                        </div>
                    </div>
                    <div className="card-body">
                        <div className="kv">
                            <div className="kv-row"><span>Answer automatically at</span><span className="mono">≥ {confidence.very_high_threshold}</span></div>
                            <div className="kv-row"><span>…or with a clear lead</span><span className="mono">≥ {confidence.high_threshold}, gap {confidence.minimum_score_gap}</span></div>
                            <div className="kv-row"><span>Low confidence below</span><span className="mono">{confidence.medium_threshold}</span></div>
                        </div>
                    </div>
                </section>

                <section className="card">
                    <div className="card-head"><div className="section-title">Connections & access</div></div>
                    <div className="card-body">
                        <div className="kv">
                            <div className="kv-row"><span>Inbox (IMAP)</span><Health ok={automation.inbox_configured} okText="Configured" badText="Missing" warn /></div>
                            <div className="kv-row"><span>Sending (SMTP)</span><Health ok={automation.smtp_configured} okText="Configured" badText="Missing" warn /></div>
                            <div className="kv-row"><span>Sign-in required</span><Health ok={access.auth_enabled} okText="Yes" badText="No" /></div>
                            <div className="kv-row"><span>Admin API key</span><Health ok={access.api_keys.admin} okText="Set" badText="Not set" warn /></div>
                            <div className="kv-row"><span>Agent API key</span><Health ok={access.api_keys.agent} okText="Set" badText="Not set" warn /></div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}

export default SystemPage;
