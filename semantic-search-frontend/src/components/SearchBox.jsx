import "../styles/search.css";

function SearchBox({
    query,
    setQuery,
    handleSearch,
    loading,
    hasResults,
    onClear
}) {


    function handleKeyDown(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            handleSearch();

        }

    }


    return (

        <section className="search-section">

            <div className="search-container">





                <div className="search-wrapper">

                    <div className="search-icon">
                        🔍
                    </div>


                    <input
                        type="text"
                        value={query}
                        placeholder="What would you like to know?"
                        onChange={(event) =>
                            setQuery(event.target.value)
                        }
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                        aria-label="Search query"
                    />


                    {hasResults && !loading && (

                        <button
                            className="clear-button"
                            type="button"
                            onClick={onClear}
                            aria-label="Clear search"
                            title="Clear search"
                        >
                            ×
                        </button>

                    )}


                    <button
                        className="search-button"
                        type="button"
                        onClick={handleSearch}
                        disabled={
                            loading ||
                            !query.trim()
                        }
                    >

                        {loading ? (

                            <>
                                <span className="button-spinner"></span>

                                Searching
                            </>

                        ) : (

                            <>
                                Search

                                <span className="search-arrow">
                                    →
                                </span>
                            </>

                        )}

                    </button>

                </div>


                <div className="search-hint">

                    <span>
                        ✨
                    </span>

                    <span>
                        Semantic search
                    </span>

                    <span>
                        •
                    </span>

                    <span>
                        AI-powered answers
                    </span>

                    <span>
                        •
                    </span>

                    <span>
                        Source-backed results
                    </span>

                </div>

            </div>

        </section>

    );
}

export default SearchBox;