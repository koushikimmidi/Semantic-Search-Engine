import { FileText } from "lucide-react";

function SourceCard({ sources, loading, onSelectSource }) {
    return (
        <aside className="sources" aria-label="Sources">
            <div className="sources-head">
                <h2>Sources</h2>
                {!loading && <span className="faint small">{sources.length}</span>}
            </div>

            {loading ? (
                <div className="skeleton"><span /><span /><span style={{ width: "60%" }} /></div>
            ) : sources.length === 0 ? (
                <p className="faint small">No matching documents.</p>
            ) : (
                <ol className="source-list">
                    {sources.map((source, index) => (
                        <li key={`${source.id}-${index}`}>
                            <button onClick={() => onSelectSource(source, index)}>
                                <span className="source-num">{index + 1}</span>
                                <span className="source-body">
                                    <span className="source-name">
                                        <FileText size={13} />
                                        {source.source?.split("/").pop() || "Document"}
                                        <span className="faint">· p. {source.page ?? 1}</span>
                                    </span>
                                    <span className="source-snippet">{source.text}</span>
                                </span>
                            </button>
                        </li>
                    ))}
                </ol>
            )}
        </aside>
    );
}

export default SourceCard;
