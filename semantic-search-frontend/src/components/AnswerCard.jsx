import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { formatIntent } from "../utils/format";

const CITATION_PATTERN = /\[(\d+(?:\s*,\s*\d+)*)\]/g;

function stripCitations(text) {
    return text.replace(/\s*\[\d+(?:\s*,\s*\d+)*\]/g, "").replace(/\s+([.,;:!?])/g, "$1");
}

/** Turn "[1]" / "[1, 2]" into small clickable citation markers. */
function renderWithCitations(text, sourceCount, onCitationClick) {
    const parts = [];
    let lastIndex = 0;

    for (const match of text.matchAll(CITATION_PATTERN)) {
        if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));

        match[1].split(",").map((n) => parseInt(n.trim(), 10)).forEach((number) => {
            const valid = number >= 1 && number <= sourceCount;
            parts.push(
                <button
                    key={`c-${match.index}-${number}`}
                    type="button"
                    className="cite"
                    disabled={!valid}
                    onClick={() => onCitationClick(number)}
                    title={valid ? `Show source ${number}` : "Source not available"}
                >
                    {number}
                </button>
            );
        });

        lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) parts.push(text.slice(lastIndex));

    return parts;
}

const LEVEL_TONE = { HIGH: "ok", MEDIUM: "warn", LOW: "bad" };

function AnswerCard({ question, answer, loading, streaming, meta, sourceCount = 0, onCitationClick }) {
    const [copied, setCopied] = useState(false);

    function copy() {
        navigator.clipboard.writeText(stripCitations(answer));
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
    }

    const level = meta?.confidence?.level;
    const route = meta?.routing?.route;

    return (
        <section className="card answer" aria-live="polite">
            <div className="answer-question">{question}</div>

            <div className="answer-text">
                {loading ? (
                    <div className="skeleton" aria-label="Searching documents">
                        <span style={{ width: "92%" }} />
                        <span style={{ width: "78%" }} />
                        <span style={{ width: "55%" }} />
                    </div>
                ) : (
                    <p>
                        {renderWithCitations(answer, sourceCount, onCitationClick)}
                        {streaming && <span className="caret" aria-hidden="true" />}
                    </p>
                )}
            </div>

            <div className="answer-foot">
                <div className="row">
                    {meta?.intent?.intent && <span className="tag">{formatIntent(meta.intent.intent)}</span>}
                    {level && (
                        <span className={`status ${LEVEL_TONE[level] || ""}`}>
                            {level.charAt(0) + level.slice(1).toLowerCase()} confidence
                            {typeof meta.confidence.top_score === "number" && (
                                <span className="mono faint" style={{ fontWeight: 400 }}>&nbsp;{meta.confidence.top_score.toFixed(2)}</span>
                            )}
                        </span>
                    )}
                    {route && (
                        <span className={`status ${route === "AUTO_REPLY" ? "ok" : "warn"}`}>
                            {route === "AUTO_REPLY" ? "Safe to send automatically" : "Needs a person to review"}
                        </span>
                    )}
                </div>

                {!loading && !streaming && answer && (
                    <button className="btn btn-ghost btn-sm" onClick={copy}>
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                        {copied ? "Copied" : "Copy"}
                    </button>
                )}
            </div>
        </section>
    );
}

export default AnswerCard;
