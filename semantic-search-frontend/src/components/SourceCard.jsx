
import "../styles/source.css";

function SourceCard({ sources, onSelectSource }) {

    if (!sources || sources.length === 0) {
        return null;
    }

    return (

        <section className="sources-section">

            <div className="sources-header">

                <div>

                    <h2>
                        Sources
                    </h2>

                    <p>
                        Retrieved document sections used to generate answer
                    </p>

                </div>

                <div className="source-count">

                    {sources.length}
                    {" "}
                    {sources.length === 1 ? "Source" : "Sources"}

                </div>

            </div>

            <div className="sources-list">

                {sources.map((source, index) => (

                    <article
                        className="source-card"
                        key={`${source.id}-${index}`}
                        onClick={() => onSelectSource && onSelectSource(source)}
                        title="Click to view full chunk content"
                    >

                        <div className="source-top">

                            <div className="source-file-icon">
                                📄
                            </div>

                            <div className="source-file-info">

                                <h3>
                                    {source.source || "Unknown Document"}
                                </h3>

                                <span className="source-rank">
                                    #{index + 1} • Chunk {source.chunk ?? index + 1}
                                </span>

                            </div>

                        </div>

                        <p className="source-preview">
                            {source.text}
                        </p>

                    </article>

                ))}

            </div>

        </section>

    );
}

export default SourceCard;