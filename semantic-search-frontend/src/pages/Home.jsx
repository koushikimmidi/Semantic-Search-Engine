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

import { searchDocumentsStream } from "../services/api";

import "../styles/home.css";

function Home({
    activeTab,
    newSearchTrigger,
    selectedHistoryItem,
    onSaveToHistory,
    onStartNewSearch,
    authVersion = 0
}) {

    const [query, setQuery] = useState("");

    // loading: waiting for the first answer token.
    // streaming: answer text is arriving.
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);

    const [answer, setAnswer] = useState("");

    const [sources, setSources] = useState([]);
    const [activeSource, setActiveSource] = useState(null);
    const [meta, setMeta] = useState(null);

    const [loadedHistoryId, setLoadedHistoryId] = useState(null);


    // Clear state on new search trigger from sidebar
    useEffect(() => {
        if (newSearchTrigger > 0) {
            handleClear();
        }
    }, [newSearchTrigger]);

    // Load the selected history item into the workspace (state is
    // adjusted during render when the selection changes).
    if (selectedHistoryItem && selectedHistoryItem.id !== loadedHistoryId) {
        setLoadedHistoryId(selectedHistoryItem.id);
        setQuery(selectedHistoryItem.query || "");
        setAnswer(selectedHistoryItem.answer || "");
        setSources(selectedHistoryItem.sources || []);
        setMeta(selectedHistoryItem.meta || null);
        setActiveSource(null);
    } else if (!selectedHistoryItem && loadedHistoryId !== null) {
        setLoadedHistoryId(null);
    }

    const busy = loading || streaming;


    async function handleSearch(forcedQuery) {
        const searchQuery = typeof forcedQuery === "string" ? forcedQuery : query;
        if (!searchQuery.trim() || busy) {
            return;
        }

        setLoading(true);
        setStreaming(false);
        setAnswer("");
        setSources([]);
        setMeta(null);
        setActiveSource(null);

        if (onStartNewSearch) {
            onStartNewSearch();
        }

        let streamedText = "";

        try {

            const result = await searchDocumentsStream(searchQuery, (event) => {

                if (event.type === "sources") {
                    setSources(event.sources || []);
                    setMeta({ intent: event.intent || null, confidence: null, routing: null });
                }

                if (event.type === "token") {
                    streamedText += event.text;
                    setLoading(false);
                    setStreaming(true);
                    setAnswer(streamedText);
                }
            });

            const receivedAnswer = result.answer || streamedText;
            const receivedSources = result.sources || [];

            const receivedMeta = {
                intent: result.intent || null,
                confidence: result.confidence || null,
                routing: result.routing || null
            };

            setAnswer(receivedAnswer);
            setSources(receivedSources);
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
            setStreaming(false);

        }
    }

    function handleCitation(number) {
        const source = sources[number - 1];
        if (source) {
            setActiveSource({ ...source, citation: number });
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
                    {(answer || busy) && (
                        <SearchBox
                            query={query}
                            setQuery={setQuery}
                            handleSearch={handleSearch}
                            loading={busy}
                            hasResults={
                                Boolean(answer)
                            }
                            onClear={handleClear}
                        />
                    )}


                    {!answer && !busy && (

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
                        streaming={streaming}
                        meta={meta}
                        sourceCount={sources.length}
                        onCitationClick={handleCitation}
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
                <AutomationDashboard key={`automation-${authVersion}`} />
            ) : (
                <DocumentManager key={`documents-${authVersion}`} />
            )}


            <Footer />

            {/* Source Details Modal - Rendered at root level to prevent sibling stacking context issues */}
            {activeSource && (
                <div className="source-modal-overlay" onClick={() => setActiveSource(null)}>
                    <div className="source-modal-content card" onClick={(e) => e.stopPropagation()}>
                        <div className="source-modal-header">
                            <div>
                                <h3>
                                    {activeSource.citation ? `[${activeSource.citation}] ` : ""}
                                    {activeSource.source}
                                </h3>
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