import { useState } from "react";
import "../styles/answer.css";

const CITATION_PATTERN = /\[(\d+(?:\s*,\s*\d+)*)\]/g;

function formatIntent(intent) {
    if (!intent) return null;
    return intent
        .toLowerCase()
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function stripCitations(text) {
    return text.replace(/\s*\[\d+(?:\s*,\s*\d+)*\]/g, "").replace(/\s+([.,;:!?])/g, "$1");
}

/**
 * Split the answer into text and citation chips. "[1]" and
 * "[1, 2]" become clickable chips when the source exists.
 */
function renderWithCitations(text, sourceCount, onCitationClick) {
    const parts = [];
    let lastIndex = 0;

    for (const match of text.matchAll(CITATION_PATTERN)) {
        if (match.index > lastIndex) {
            parts.push(text.slice(lastIndex, match.index));
        }

        const numbers = match[1].split(",").map((n) => parseInt(n.trim(), 10));

        numbers.forEach((number) => {
            const valid = number >= 1 && number <= sourceCount;
            parts.push(
                <button
                    key={`cite-${match.index}-${number}`}
                    type="button"
                    className={`citation-chip ${valid ? "" : "invalid"}`}
                    onClick={() => valid && onCitationClick && onCitationClick(number)}
                    title={valid ? `Open source ${number}` : "Source not available"}
                    disabled={!valid}
                >
                    {number}
                </button>
            );
        });

        lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
        parts.push(text.slice(lastIndex));
    }

    return parts;
}

function AnswerCard({ answer, loading, streaming, meta, sourceCount = 0, onCitationClick }) {
    const [copied, setCopied] = useState(false);

    if (loading || !answer) {
        return null;
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(stripCitations(answer));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (

        <section className="answer-section">

            <div className="answer-card">

                <div className="answer-header">

                    <div className="answer-avatar">
                        ✦
                    </div>

                    <div className="answer-header-meta">

                        <h2>
                            Answer
                        </h2>

                        <p>
                            {streaming ? "Generating…" : "Grounded AI response"}
                        </p>

                    </div>

                    <button
                        className={`copy-btn ${copied ? "copied" : ""}`}
                        onClick={handleCopy}
                        title="Copy answer"
                        disabled={streaming}
                    >
                        {copied ? "✓ Copied" : "📋 Copy"}
                    </button>

                </div>

                <div className="answer-content">

                    <p>
                        {renderWithCitations(answer, sourceCount, onCitationClick)}
                        {streaming && <span className="stream-cursor" aria-hidden="true"></span>}
                    </p>

                </div>

                {meta && !streaming && (
                    <div className="answer-meta">
                        {meta.intent?.intent && (
                            <span className="answer-chip">
                                Intent: <strong>{formatIntent(meta.intent.intent)}</strong>
                            </span>
                        )}
                        {meta.confidence?.level && (
                            <span className={`answer-chip level-${meta.confidence.level.toLowerCase()}`}>
                                Confidence: <strong>{meta.confidence.level}</strong>
                                {typeof meta.confidence.top_score === "number" && (
                                    <> · score {meta.confidence.top_score.toFixed(2)}</>
                                )}
                            </span>
                        )}
                        {meta.routing?.route && (
                            <span className={`answer-chip route-${meta.routing.route.toLowerCase()}`}>
                                {meta.routing.route === "AUTO_REPLY"
                                    ? "✓ Safe to auto-reply"
                                    : "⚑ Needs human review"}
                            </span>
                        )}
                    </div>
                )}

            </div>

        </section>

    );
}

export default AnswerCard;
