import { useState, useEffect } from "react";

import SearchBox from "../components/SearchBox";
import LoadingSpinner from "../components/LoadingSpinner";
import AnswerCard from "../components/AnswerCard";
import SourceCard from "../components/SourceCard";
import StatisticsCard from "../components/StatisticsCard";
import HeroSection from "../components/HeroSection";
import Footer from "../components/Footer";
import DocumentManager from "../components/DocumentManager";
import AutomationDashboard from "../components/AutomationDashboard";

import { searchDocuments } from "../services/api";

import "../styles/home.css";

function Home({
    activeTab,
    newSearchTrigger,
    selectedHistoryItem,
    onSaveToHistory,
    onStartNewSearch
}) {

    const [query, setQuery] = useState("");

    const [loading, setLoading] = useState(false);

    const [answer, setAnswer] = useState("");

    const [sources, setSources] = useState([]);
    const [activeSource, setActiveSource] = useState(null);
    const [meta, setMeta] = useState(null);


    // Clear state on new search trigger from sidebar
    useEffect(() => {
        if (newSearchTrigger > 0) {
            handleClear();
        }
    }, [newSearchTrigger]);

    // Load active history item details into workspace
    useEffect(() => {
        if (selectedHistoryItem) {
            setQuery(selectedHistoryItem.query || "");
            setAnswer(selectedHistoryItem.answer || "");
            setSources(selectedHistoryItem.sources || []);
            setMeta(selectedHistoryItem.meta || null);
            setActiveSource(null);
        }
    }, [selectedHistoryItem]);


    async function handleSearch(forcedQuery) {
        const searchQuery = typeof forcedQuery === "string" ? forcedQuery : query;
        if (!searchQuery.trim() || loading) {
            return;
        }

        setLoading(true);
        setAnswer("");
        setSources([]);
        setMeta(null);

        if (onStartNewSearch) {
            onStartNewSearch();
        }

        try {

            const result =
                await searchDocuments(searchQuery);

            const receivedAnswer = result.answer || "";
            const receivedSources = result.sources || [];

            setAnswer(receivedAnswer);
            setSources(receivedSources);

            const receivedMeta = {
                intent: result.intent || null,
                confidence: result.confidence || null,
                routing: result.routing || null
            };

            setMeta(receivedMeta);

            if (receivedAnswer && onSaveToHistory) {
                onSaveToHistory({
                    query: searchQuery,
                    answer: receivedAnswer,
                    sources: receivedSources,
                    meta: receivedMeta
                });
            }

        } catch (error) {

            console.error(error);

            alert(
                `Search failed: ${error.message}. Please make sure the backend is running.`
            );

        } finally {

            setLoading(false);

        }
    }


    function handleClear() {

        setQuery("");

        setAnswer("");

        setSources([]);
        setActiveSource(null);
        setMeta(null);

    }


    return (

        <div className="home-container">

            {activeTab === "search" ? (
                <div className="search-workspace">
                    {(answer || loading) && (
                        <SearchBox
                            query={query}
                            setQuery={setQuery}
                            handleSearch={handleSearch}
                            loading={loading}
                            hasResults={
                                Boolean(answer)
                            }
                            onClear={handleClear}
                        />
                    )}


                    {!answer && !loading && (

                        <HeroSection 
                            onSelectQuery={(q) => {
                                setQuery(q);
                                handleSearch(q);
                            }}
                            searchBox={
                                <SearchBox
                                    query={query}
                                    setQuery={setQuery}
                                    handleSearch={handleSearch}
                                    loading={loading}
                                    hasResults={
                                        Boolean(answer)
                                    }
                                    onClear={handleClear}
                                />
                            }
                        />

                    )}


                    <LoadingSpinner
                        loading={loading}
                    />


                    <AnswerCard
                        answer={answer}
                        loading={loading}
                        meta={meta}
                    />


                    <SourceCard
                        sources={sources}
                        onSelectSource={setActiveSource}
                    />


                    <StatisticsCard
                        model="all-MiniLM-L6-v2"
                        reranker="ms-marco-MiniLM-L-6-v2"
                        llm="Gemma 4"
                        totalSources={
                            sources.length
                        }
                    />
                </div>
            ) : activeTab === "automation" ? (
                <AutomationDashboard />
            ) : (
                <DocumentManager />
            )}


            <Footer />

            {/* Source Details Modal - Rendered at root level to prevent sibling stacking context issues */}
            {activeSource && (
                <div className="source-modal-overlay" onClick={() => setActiveSource(null)}>
                    <div className="source-modal-content card" onClick={(e) => e.stopPropagation()}>
                        <div className="source-modal-header">
                            <div>
                                <h3>{activeSource.source}</h3>
                                <p className="subtitle">Page {activeSource.page ?? 1} • Chunk {activeSource.chunk ?? "-"}</p>
                            </div>
                            <button className="source-modal-close" onClick={() => setActiveSource(null)}>×</button>
                        </div>
                        <div className="source-modal-body">
                            <p className="source-modal-text">
                                {activeSource.text}
                            </p>
                        </div>
                    </div>
                </div>
            )}

        </div>

    );
}

export default Home;