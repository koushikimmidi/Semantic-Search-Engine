import { useState } from "react";
import "../styles/answer.css";

function formatIntent(intent) {
    if (!intent) return null;
    return intent
        .toLowerCase()
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function AnswerCard({ answer, loading, meta }) {
    const [copied, setCopied] = useState(false);

    if (loading || !answer) {
        return null;
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(answer);
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
                            Grounded AI response
                        </p>

                    </div>

                    <button 
                        className={`copy-btn ${copied ? "copied" : ""}`}
                        onClick={handleCopy}
                        title="Copy answer"
                    >
                        {copied ? "✓ Copied" : "📋 Copy"}
                    </button>

                </div>

                <div className="answer-content">

                    <p>
                        {answer}
                    </p>

                </div>

                {meta && (
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