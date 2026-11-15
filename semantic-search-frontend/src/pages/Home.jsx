import { useEffect, useRef, useState } from "react";
import { ArrowUp, LoaderCircle } from "lucide-react";

import AnswerCard from "../components/AnswerCard";
import SourceCard from "../components/SourceCard";
import { Modal, Notice } from "../components/ui";
import { timeAgo } from "../utils/format";
import { searchDocumentsStream } from "../services/api";
import "../styles/ask.css";

const SUGGESTIONS = [
    "How many days do I have to ask for a refund?",
    "The password reset email never arrived",
    "Can I get my certificate reissued?",
    "What will I build in the Python Basics course?"
];

function QuestionBox({ value, onChange, onSubmit, busy, compact = false }) {
    const ref = useRef(null);

    useEffect(() => {
        if (!compact) ref.current?.focus();
    }, [compact]);

    return (
        <form
            className={`ask-box ${compact ? "compact" : ""}`}
            onSubmit={(e) => { e.preventDefault(); onSubmit(); }}
        >
            <label htmlFor="question" className="sr-only">Question</label>
            <input
                id="question"
                ref={ref}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Ask about policies, payments, courses, access…"
                autoComplete="off"
                disabled={busy}
            />
            <button type="submit" className="ask-submit" disabled={busy || !value.trim()} aria-label="Ask">
                {busy ? <LoaderCircle size={16} className="spin" /> : <ArrowUp size={16} strokeWidth={2.2} />}
            </button>
        </form>
    );
}

function Home({
    newSearchTrigger,
    selectedHistoryItem,
    history = [],
    onSaveToHistory,
    onSelectHistory,
    onClearHistory,
    onStartNewSearch
}) {
    const [query, setQuery] = useState("");
    const [asked, setAsked] = useState("");
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState([]);
    const [meta, setMeta] = useState(null);
    const [error, setError] = useState("");
    const [activeSource, setActiveSource] = useState(null);
    const [loadedHistoryId, setLoadedHistoryId] = useState(null);

    function reset() {
        setQuery("");
        setAsked("");
        setAnswer("");
        setSources([]);
        setMeta(null);
        setError("");
        setActiveSource(null);
    }

    useEffect(() => {
        if (newSearchTrigger > 0) {
            const id = setTimeout(reset, 0);
            return () => clearTimeout(id);
        }
        return undefined;
    }, [newSearchTrigger]);

    // Show a past question when it is picked from the list.
    if (selectedHistoryItem && selectedHistoryItem.id !== loadedHistoryId) {
        setLoadedHistoryId(selectedHistoryItem.id);
        setQuery(selectedHistoryItem.query);
        setAsked(selectedHistoryItem.query);
        setAnswer(selectedHistoryItem.answer);
        setSources(selectedHistoryItem.sources || []);
        setMeta(selectedHistoryItem.meta || null);
        setError("");
    } else if (!selectedHistoryItem && loadedHistoryId !== null) {
        setLoadedHistoryId(null);
    }

    const busy = loading || streaming;
    const hasResult = Boolean(asked);

    async function ask(text = query) {
        const question = text.trim();
        if (!question || busy) return;

        setQuery(question);
        setAsked(question);
        setLoading(true);
        setStreaming(false);
        setAnswer("");
        setSources([]);
        setMeta(null);
        setError("");
        onStartNewSearch && onStartNewSearch();

        let streamed = "";

        try {
            const result = await searchDocumentsStream(question, (event) => {
                if (event.type === "sources") {
                    setSources(event.sources || []);
                    setMeta({ intent: event.intent || null, confidence: null, routing: null });
                }
                if (event.type === "token") {
                    streamed += event.text;
                    setLoading(false);
                    setStreaming(true);
                    setAnswer(streamed);
                }
            });

            const finalMeta = {
                intent: result.intent || null,
                confidence: result.confidence || null,
                routing: result.routing || null
            };

            setAnswer(result.answer || streamed);
            setSources(result.sources || []);
            setMeta(finalMeta);

            onSaveToHistory && onSaveToHistory({
                query: question,
                answer: result.answer || streamed,
                sources: result.sources || [],
                meta: finalMeta
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
            setStreaming(false);
        }
    }

    function openCitation(number) {
        const source = sources[number - 1];
        if (source) setActiveSource({ ...source, number });
    }

    if (!hasResult) {
        return (
            <div className="page ask-start">
                <div className="ask-intro">
                    <h1>Ask the knowledge base</h1>
                    <p>Answers are written only from your documents, with the sources they came from.</p>
                </div>

                <QuestionBox value={query} onChange={setQuery} onSubmit={() => ask()} busy={busy} />

                <div className="ask-lists">
                    <section>
                        <h2>Try asking</h2>
                        <ul className="ask-list">
                            {SUGGESTIONS.map((text) => (
                                <li key={text}>
                                    <button onClick={() => ask(text)}>{text}</button>
                                </li>
                            ))}
                        </ul>
                    </section>

                    {history.length > 0 && (
                        <section>
                            <div className="ask-list-head">
                                <h2>Recent</h2>
                                <button className="btn btn-ghost btn-sm" onClick={onClearHistory}>Clear</button>
                            </div>
                            <ul className="ask-list">
                                {history.slice(0, 6).map((item) => (
                                    <li key={item.id}>
                                        <button onClick={() => onSelectHistory(item)}>
                                            <span>{item.query}</span>
                                            <span className="faint small">{timeAgo(item.timestamp)}</span>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="page">
            <QuestionBox value={query} onChange={setQuery} onSubmit={() => ask()} busy={busy} compact />

            {error && <Notice tone="bad">{error}</Notice>}

            <div className="ask-result">
                <AnswerCard
                    question={asked}
                    answer={answer}
                    loading={loading}
                    streaming={streaming}
                    meta={meta}
                    sourceCount={sources.length}
                    onCitationClick={openCitation}
                />
                <SourceCard sources={sources} loading={loading} onSelectSource={(source, index) => setActiveSource({ ...source, number: index + 1 })} />
            </div>

            {activeSource && (
                <Modal
                    wide
                    title={`[${activeSource.number}] ${activeSource.source}`}
                    onClose={() => setActiveSource(null)}
                >
                    <div className="modal-body">
                        <div className="row small faint">
                            <span>Page {activeSource.page ?? 1}</span>
                            <span>·</span>
                            <span>Section {activeSource.chunk ?? "—"}</span>
                            {typeof activeSource.cross_score === "number" && (
                                <>
                                    <span>·</span>
                                    <span className="mono">relevance {activeSource.cross_score.toFixed(2)}</span>
                                </>
                            )}
                        </div>
                        <p className="source-full">{activeSource.text}</p>
                    </div>
                </Modal>
            )}
        </div>
    );
}

export default Home;
