import "../styles/navbar.css";

function Navbar({
    darkMode,
    toggleTheme,
    activeTab,
    setActiveTab
}) {

    return (

        <nav className="navbar">

            <div className="navbar-container">

                <div className="navbar-brand">

                    <div className="navbar-logo">
                        ✦
                    </div>

                    <div className="navbar-title">

                        <h1>
                            Semantic AI
                        </h1>

                        <span>
                            Intent Search Engine
                        </span>

                    </div>

                </div>

                <div className="navbar-nav">
                    <button 
                        className={`nav-link ${activeTab === "search" ? "active" : ""}`}
                        onClick={() => setActiveTab("search")}
                    >
                        🔍 Search
                    </button>
                    <button 
                        className={`nav-link ${activeTab === "documents" ? "active" : ""}`}
                        onClick={() => setActiveTab("documents")}
                    >
                        📁 Knowledge Base
                    </button>
                </div>

                <div className="navbar-actions">

                    <div className="navbar-status">

                        <span className="status-dot"></span>

                        <span>
                            AI Search Engine
                        </span>

                    </div>

                    <button
                        className="theme-toggle"
                        onClick={toggleTheme}
                        aria-label={
                            darkMode
                                ? "Switch to light mode"
                                : "Switch to dark mode"
                        }
                        title={
                            darkMode
                                ? "Light mode"
                                : "Dark mode"
                        }
                    >

                        {darkMode ? "☀️" : "🌙"}

                    </button>

                </div>

            </div>

        </nav>

    );
}

export default Navbar;