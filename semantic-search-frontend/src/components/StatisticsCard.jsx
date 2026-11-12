import "../styles/statistics.css";

function StatisticsCard({
    model,
    reranker,
    llm,
    totalSources
}) {

    if (totalSources === 0) {
        return null;
    }

    const statistics = [
        {
            icon: "🧠",
            label: "Embedding Model",
            value: model
        },
        {
            icon: "🎯",
            label: "Reranker",
            value: reranker
        },
        {
            icon: "✦",
            label: "Language Model",
            value: llm
        },
        {
            icon: "📚",
            label: "Retrieved Sources",
            value: totalSources
        }
    ];

    return (

        <section className="statistics-section">

            <div className="statistics-header">

                <div>

                    <h2>
                        Search System Overview
                    </h2>

                    <p>
                        Models and retrieval information used for this answer
                    </p>

                </div>

                <div className="statistics-status">

                    <span className="statistics-status-dot"></span>

                    Search Complete

                </div>

            </div>

            <div className="statistics-grid">

                {statistics.map((stat) => (

                    <div
                        className="stat-box"
                        key={stat.label}
                    >

                        <div className="stat-icon">

                            {stat.icon}

                        </div>

                        <div className="stat-content">

                            <span className="stat-label">

                                {stat.label}

                            </span>

                            <strong className="stat-value">

                                {stat.value}

                            </strong>

                        </div>

                    </div>

                ))}

            </div>

        </section>

    );
}

export default StatisticsCard;