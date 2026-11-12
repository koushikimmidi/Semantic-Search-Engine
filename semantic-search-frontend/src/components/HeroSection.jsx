import "../styles/hero.css";

function HeroSection({ onSelectQuery, searchBox }) {

    const suggestions = [
        {
            icon: "🧠",
            title: "Attention Mechanism",
            desc: "Explain the attention mechanism in transformers.",
            query: "Explain the attention mechanism in transformers"
        },
        {
            icon: "🧩",
            title: "Semantic Search",
            desc: "How does dense semantic retrieval work?",
            query: "How does dense semantic retrieval work"
        },
        {
            icon: "⚡",
            title: "Hybrid RRF",
            desc: "How does Reciprocal Rank Fusion work?",
            query: "How does Reciprocal Rank Fusion work"
        },
        {
            icon: "🤖",
            title: "Gemma Models",
            desc: "What are Google Gemma language models?",
            query: "What are Google Gemma language models"
        }
    ];

    return (

        <section className="hero-section">

            <div className="hero-icon">
                ✦
            </div>

            <h1>
                What would you like to know?
            </h1>

            <p className="hero-description">
                Ask natural-language questions about your local documents and get instant AI-grounded responses.
            </p>

            <div className="hero-search-container">
                {searchBox}
            </div>

            <div className="suggestions-grid">

                {suggestions.map((s, idx) => (
                    <button 
                        key={idx}
                        className="suggestion-card"
                        onClick={() => onSelectQuery && onSelectQuery(s.query)}
                    >
                        <span className="suggestion-card-icon">{s.icon}</span>
                        <div className="suggestion-card-content">
                            <h4>{s.title}</h4>
                            <p>{s.desc}</p>
                        </div>
                        <span className="suggestion-card-arrow">→</span>
                    </button>
                ))}

            </div>

        </section>

    );
}

export default HeroSection;