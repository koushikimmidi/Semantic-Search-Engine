import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";

function App() {

  const [darkMode, setDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem("semantic-ai-theme");
    return savedTheme === "dark";
  });

  const [activeTab, setActiveTab] = useState("search");
  const [newSearchTrigger, setNewSearchTrigger] = useState(0);
  // Bumped when the API key changes so data views reload.
  const [authVersion, setAuthVersion] = useState(0);

  // Search History States
  const [history, setHistory] = useState(() => {
    const savedHistory = localStorage.getItem("semantic-ai-history");
    return savedHistory ? JSON.parse(savedHistory) : [];
  });
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  function toggleTheme() {
    setDarkMode((currentMode) => {
      const newMode = !currentMode;
      localStorage.setItem(
        "semantic-ai-theme",
        newMode ? "dark" : "light"
      );
      return newMode;
    });
  }

  function generateTitle(query) {
    if (!query) return "New Search";
    
    // Clean question patterns or filler phrases at the beginning of the query
    let cleanQuery = query
      .trim()
      .replace(/^(what\s+is\s+a\s+|what\s+is\s+|how\s+does\s+|how\s+do\s+i\s+|explain\s+the\s+|explain\s+|describe\s+the\s+|describe\s+|tell\s+me\s+about\s+|show\s+me\s+|search\s+for\s+)/i, "");
    
    // Clean special characters at end
    cleanQuery = cleanQuery.replace(/[?.,!/\\-]+$/, "").trim();
    
    if (!cleanQuery) return query.trim().substring(0, 24);
    
    // Capitalize first letter of words
    const capitalized = cleanQuery
      .split(/\s+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
    
    // Truncate to a reasonable title length
    if (capitalized.length > 25) {
      return capitalized.substring(0, 24) + "...";
    }
    return capitalized;
  }

  function handleSaveToHistory({ query, answer, sources, meta }) {
    // Avoid saving if answer or query is blank
    if (!query.trim() || !answer.trim()) return;

    // Check if query already exists in recent history to prevent duplicates
    const duplicateIndex = history.findIndex(
      (item) => item.query.toLowerCase() === query.trim().toLowerCase()
    );

    let updatedHistory = [...history];

    if (duplicateIndex !== -1) {
      // Remove duplicate from its old position so we can prepend it
      const [duplicateItem] = updatedHistory.splice(duplicateIndex, 1);
      // Update its contents (in case LLM answer or sources changed)
      const updatedItem = {
        ...duplicateItem,
        answer,
        sources,
        meta,
        timestamp: new Date().toISOString()
      };
      updatedHistory.unshift(updatedItem);
      setHistory(updatedHistory);
      localStorage.setItem("semantic-ai-history", JSON.stringify(updatedHistory));
      setActiveHistoryId(updatedItem.id);
    } else {
      // Create new history item
      const newItem = {
        id: Date.now().toString(),
        title: generateTitle(query),
        query: query.trim(),
        answer,
        sources,
        meta,
        timestamp: new Date().toISOString()
      };
      updatedHistory.unshift(newItem);
      setHistory(updatedHistory);
      localStorage.setItem("semantic-ai-history", JSON.stringify(updatedHistory));
      setActiveHistoryId(newItem.id);
    }
  }

  function handleSelectHistory(item) {
    setActiveHistoryId(item.id);
    setSelectedHistoryItem(item);
    setActiveTab("search");
  }

  function handleDeleteHistory(id) {
    const updatedHistory = history.filter((item) => item.id !== id);
    setHistory(updatedHistory);
    localStorage.setItem("semantic-ai-history", JSON.stringify(updatedHistory));

    if (activeHistoryId === id) {
      setActiveHistoryId(null);
      setSelectedHistoryItem(null);
      setNewSearchTrigger(prev => prev + 1); // trigger a reset
    }
  }

  function handleClearHistory() {
    setHistory([]);
    localStorage.removeItem("semantic-ai-history");
    setActiveHistoryId(null);
    setSelectedHistoryItem(null);
    setNewSearchTrigger(prev => prev + 1); // trigger a reset
  }

  function handleNewSearch() {
    setActiveHistoryId(null);
    setSelectedHistoryItem(null);
    setNewSearchTrigger(prev => prev + 1);
    setActiveTab("search");
  }

  function handleStartNewSearch() {
    setActiveHistoryId(null);
    setSelectedHistoryItem(null);
  }

  return (
    <div className={darkMode ? "app dark-mode app-container" : "app app-container"}>
      <Sidebar
        darkMode={darkMode}
        toggleTheme={toggleTheme}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewSearch={handleNewSearch}
        history={history}
        activeHistoryId={activeHistoryId}
        onSelectHistory={handleSelectHistory}
        onDeleteHistory={handleDeleteHistory}
        onClearHistory={handleClearHistory}
        onAuthChange={() => setAuthVersion((v) => v + 1)}
      />

      <main className="main-content">
        <Home
          authVersion={authVersion}
          activeTab={activeTab}
          newSearchTrigger={newSearchTrigger}
          selectedHistoryItem={selectedHistoryItem}
          onSaveToHistory={handleSaveToHistory}
          onStartNewSearch={handleStartNewSearch}
        />
      </main>
    </div>
  );
}

export default App;