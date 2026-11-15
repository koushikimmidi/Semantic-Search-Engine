import { useCallback, useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getAnalytics } from "../services/api";
import { Notice } from "../components/ui";
import { formatIntent } from "../utils/format";

// Categorical slots 1-4 (validated for light and dark surfaces).
const OUTCOMES = [
    { key: "auto_reply", label: "Answered automatically", color: "var(--series-1)" },
    { key: "human_review", label: "Sent to review", color: "var(--series-2)" },
    { key: "skipped", label: "Skipped", color: "var(--series-3)" },
    { key: "failed", label: "Failed", color: "var(--series-4)" }
];

const RANGES = [[7, "7 days"], [30, "30 days"], [90, "90 days"]];

const shortDate = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });

function formatMs(ms) {
    if (!ms) return "—";
    return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

function formatHours(hours) {
    if (hours === null || hours === undefined) return "—";
    if (hours < 1) return `${Math.max(1, Math.round(hours * 60))}m`;
    if (hours < 48) return `${hours.toFixed(1)}h`;
    return `${(hours / 24).toFixed(1)}d`;
}

function OutcomeTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    const total = payload.reduce((sum, p) => sum + (p.value || 0), 0);
    return (
        <div className="tooltip">
            <strong>{shortDate(label)} · {total} email{total === 1 ? "" : "s"}</strong>
            {OUTCOMES.map((o) => (
                <div className="line" key={o.key}>
                    <span><i style={{ background: o.color }} />{o.label}</span>
                    <b>{payload.find((p) => p.dataKey === o.key)?.value ?? 0}</b>
                </div>
            ))}
        </div>
    );
}

function QuestionTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="tooltip">
            <strong>{shortDate(label)}</strong>
            <div className="line"><span>Questions</span><b>{payload[0].value}</b></div>
        </div>
    );
}

function Bars({ rows, empty }) {
    if (!rows.length) return <p className="empty" style={{ padding: "12px 0" }}>{empty}</p>;
    const max = Math.max(1, ...rows.map((r) => r.value));
    return (
        <div className="bars">
            {rows.map((row) => (
                <div className="bars-row" key={row.label} title={`${row.label}: ${row.value}`}>
                    <span>{row.label}</span>
                    <div className="bars-track"><div className="bars-fill" style={{ width: `${(row.value / max) * 100}%` }} /></div>
                    <span className="right">{row.value}</span>
                </div>
            ))}
        </div>
    );
}

const axis = { tick: { fill: "var(--text-3)", fontSize: 12 }, axisLine: false, tickLine: false };

function Card({ title, sub, action, children, flush = false }) {
    return (
        <section className="card">
            <div className="card-head">
                <div>
                    <div className="section-title">{title}</div>
                    {sub && <div className="section-sub">{sub}</div>}
                </div>
                {action}
            </div>
            <div className="card-body" style={flush ? { padding: "8px 4px 4px" } : undefined}>{children}</div>
        </section>
    );
}

function AnalyticsPage({ isAdmin }) {
    const [days, setDays] = useState(30);
    const [data, setData] = useState(null);
    const [error, setError] = useState("");
    const [view, setView] = useState("chart");

    const load = useCallback(async () => {
        try {
            setData((await getAnalytics(days)).overview);
            setError("");
        } catch (err) {
            setError(err.message);
        }
    }, [days]);

    useEffect(() => {
        const initial = setTimeout(load, 0);
        const interval = setInterval(load, 60000);
        return () => {
            clearTimeout(initial);
            clearInterval(interval);
        };
    }, [load]);

    const timeline = data?.timeline || [];
    const activeDays = timeline.filter((d) => d.auto_reply + d.human_review + d.skipped + d.failed > 0);
    const hasQuestions = timeline.some((d) => d.searches > 0);

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>{isAdmin ? "Analytics" : "Overview"}</h1>
                    <p>How emails and questions were handled, by the assistant and by the team.</p>
                </div>
                <div className="segmented" role="tablist" aria-label="Date range">
                    {RANGES.map(([value, label]) => (
                        <button key={value} role="tab" aria-selected={days === value}
                            className={days === value ? "active" : ""} onClick={() => setDays(value)}>
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {error && <Notice tone="bad">{error}</Notice>}

            {!data ? (
                <p className="empty">Loading…</p>
            ) : (
                <>
                    <div className="metrics">
                        <div className="metric">
                            <div className="metric-label">Emails handled</div>
                            <div className="metric-value">{data.emails.total}</div>
                            <div className="metric-note">{data.emails.by_channel.inbox || 0} inbox · {data.emails.by_channel.test || 0} test</div>
                        </div>
                        <div className="metric">
                            <div className="metric-label">Answered automatically</div>
                            <div className="metric-value">{data.emails.auto_reply_rate}%</div>
                            <div className="metric-note">{data.emails.auto_reply} of {data.emails.auto_reply + data.emails.human_review}</div>
                        </div>
                        <div className={`metric ${data.review.pending ? "attention" : ""}`}>
                            <div className="metric-label">Waiting for review</div>
                            <div className="metric-value">{data.review.pending}</div>
                            <div className="metric-note">oldest {formatHours(data.review.oldest_pending_hours)}</div>
                        </div>
                        <div className="metric">
                            <div className="metric-label">Time to resolve</div>
                            <div className="metric-value">{formatHours(data.review.avg_resolution_hours)}</div>
                            <div className="metric-note">{data.review.resolved} resolved · {data.review.replied} replied</div>
                        </div>
                        <div className="metric">
                            <div className="metric-label">Questions asked</div>
                            <div className="metric-value">{data.searches.total}</div>
                            <div className="metric-note">{data.searches.confident_rate}% confident</div>
                        </div>
                        <div className="metric">
                            <div className="metric-label">Answer time</div>
                            <div className="metric-value">{formatMs(data.searches.avg_response_ms)}</div>
                            <div className="metric-note">emails {formatMs(data.emails.avg_processing_ms)}</div>
                        </div>
                    </div>

                    <Card
                        title="Email outcomes"
                        sub="What happened to each email the assistant processed, per day."
                        action={
                            <div className="segmented" aria-label="Chart or table">
                                <button className={view === "chart" ? "active" : ""} onClick={() => setView("chart")}>Chart</button>
                                <button className={view === "table" ? "active" : ""} onClick={() => setView("table")}>Table</button>
                            </div>
                        }
                    >
                        {activeDays.length === 0 ? (
                            <p className="empty">No emails in this period yet.</p>
                        ) : view === "chart" ? (
                            <div className="stack">
                                <div className="legend">
                                    {OUTCOMES.map((o) => <span key={o.key}><i style={{ background: o.color }} />{o.label}</span>)}
                                </div>
                                <div className="chart">
                                    <ResponsiveContainer>
                                        <BarChart data={timeline} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
                                            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                                            <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={28} {...axis} />
                                            <YAxis allowDecimals={false} {...axis} />
                                            <Tooltip content={<OutcomeTooltip />} cursor={{ fill: "var(--surface-2)" }} />
                                            {OUTCOMES.map((o, i) => (
                                                <Bar key={o.key} dataKey={o.key} stackId="e" fill={o.color}
                                                    stroke="var(--chart-surface)" strokeWidth={1} maxBarSize={22}
                                                    radius={i === OUTCOMES.length - 1 ? [3, 3, 0, 0] : 0} isAnimationActive={false} />
                                            ))}
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        ) : (
                            <div className="table-wrap">
                                <table className="table">
                                    <thead>
                                        <tr><th>Day</th>{OUTCOMES.map((o) => <th key={o.key} className="right">{o.label}</th>)}</tr>
                                    </thead>
                                    <tbody>
                                        {activeDays.map((d) => (
                                            <tr key={d.date}>
                                                <td>{shortDate(d.date)}</td>
                                                {OUTCOMES.map((o) => <td key={o.key} className="right">{d[o.key]}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </Card>

                    <div className="grid-2">
                        <Card title="Questions asked" sub="Questions typed into Ask, per day.">
                            {!hasQuestions ? (
                                <p className="empty">No questions in this period yet.</p>
                            ) : (
                                <div className="chart short">
                                    <ResponsiveContainer>
                                        <AreaChart data={timeline} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
                                            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                                            <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={28} {...axis} />
                                            <YAxis allowDecimals={false} {...axis} />
                                            <Tooltip content={<QuestionTooltip />} cursor={{ stroke: "var(--line-strong)" }} />
                                            <Area type="monotone" dataKey="searches" stroke="var(--series-1)" strokeWidth={2}
                                                fill="var(--series-1)" fillOpacity={0.08} dot={false}
                                                activeDot={{ r: 4, stroke: "var(--chart-surface)", strokeWidth: 2 }} isAnimationActive={false} />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                        </Card>

                        <Card title="Topics" sub="Detected intent of emails and questions.">
                            <Bars rows={(data.intents || []).slice(0, 7).map((i) => ({ label: formatIntent(i.intent), value: i.count }))} empty="No activity yet." />
                        </Card>
                    </div>

                    <div className={isAdmin ? "grid-3" : "grid-2"}>
                        <Card title="Answer confidence">
                            <Bars
                                rows={[["High", "HIGH"], ["Medium", "MEDIUM"], ["Low", "LOW"]]
                                    .map(([label, key]) => ({ label, value: data.confidence[key] }))
                                    .filter((r) => r.value > 0)}
                                empty="No answers yet."
                            />
                        </Card>

                        <Card title="Waiting by topic">
                            <Bars
                                rows={Object.entries(data.review.pending_by_intent || {}).sort((a, b) => b[1] - a[1])
                                    .map(([intent, value]) => ({ label: formatIntent(intent), value }))}
                                empty="Nothing waiting."
                            />
                        </Card>

                        {isAdmin && (
                            <Card title="Inbox automation">
                                <div className="kv">
                                    <div className="kv-row"><span>Inbox checks</span><span className="num">{data.runs.total}</span></div>
                                    <div className="kv-row"><span>Emails read</span><span className="num">{data.runs.fetched}</span></div>
                                    <div className="kv-row"><span>Replies sent</span><span className="num">{data.emails.emails_sent}</span></div>
                                    <div className="kv-row"><span>Failures</span><span className="num">{data.runs.failed}</span></div>
                                    <div className="kv-row">
                                        <span>Last check</span>
                                        <span>{data.runs.last_run ? new Date(data.runs.last_run).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "—"}</span>
                                    </div>
                                </div>
                            </Card>
                        )}
                    </div>

                    <div className={isAdmin ? "grid-2" : ""}>
                        <Card title="Knowledge gaps" sub="Questions the assistant couldn't answer. Adding documents for these helps most." flush>
                            {data.knowledge_gaps.length === 0 ? (
                                <p className="empty">No gaps in this period.</p>
                            ) : (
                                <div className="table-wrap">
                                    <table className="table">
                                        <thead><tr><th>Question</th><th>Topic</th><th className="right">Asked</th></tr></thead>
                                        <tbody>
                                            {data.knowledge_gaps.map((gap) => (
                                                <tr key={gap.text}>
                                                    <td>{gap.text}</td>
                                                    <td className="muted" style={{ whiteSpace: "nowrap" }}>{formatIntent(gap.intent)}</td>
                                                    <td className="right">{gap.count}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </Card>

                        {isAdmin && (
                            <Card title="Team" sub="Activity per person in this period." flush>
                                {data.agents.length === 0 ? (
                                    <p className="empty">No team activity yet.</p>
                                ) : (
                                    <div className="table-wrap">
                                        <table className="table">
                                            <thead>
                                                <tr><th>Person</th><th className="right">Replied</th><th className="right">Resolved</th><th className="right">Questions</th></tr>
                                            </thead>
                                            <tbody>
                                                {data.agents.map((a) => (
                                                    <tr key={a.user}>
                                                        <td>{a.user}</td>
                                                        <td className="right">{a.replied}</td>
                                                        <td className="right">{a.resolved}</td>
                                                        <td className="right">{a.searches}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </Card>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

export default AnalyticsPage;
