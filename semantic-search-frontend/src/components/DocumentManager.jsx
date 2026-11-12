import { useState, useEffect, useRef } from "react";
import {
    listDocuments,
    uploadDocuments,
    deleteDocument,
    getDocumentContent
} from "../services/api";
import "../styles/document-manager.css";

function DocumentManager() {
    const [documents, setDocuments] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState("");
    const [stagedFiles, setStagedFiles] = useState([]);
    const [isDragActive, setIsDragActive] = useState(false);
    
    // Viewer states
    const [viewerOpen, setViewerOpen] = useState(false);
    const [viewerDoc, setViewerDoc] = useState(null);
    const [viewerContent, setViewerContent] = useState("");
    const [viewerLoading, setViewerLoading] = useState(false);

    const fileInputRef = useRef(null);
    const folderInputRef = useRef(null);

    // Fetch documents on load
    useEffect(() => {
        fetchDocs();
    }, []);

    async function fetchDocs() {
        setLoading(true);
        try {
            const data = await listDocuments();
            setDocuments(data || []);
        } catch (error) {
            console.error("Failed to load documents:", error);
        } finally {
            setLoading(false);
        }
    }

    // Format file sizes
    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    // Format epoch timestamps
    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    // Handle Drag & Drop
    function handleDrag(e) {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setIsDragActive(true);
        } else if (e.type === "dragleave") {
            setIsDragActive(false);
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            stageFiles(Array.from(e.dataTransfer.files));
        }
    }

    // Staging files
    function stageFiles(files) {
        // Filter out unsupported files
        const supportedExtensions = [".txt", ".pdf", ".docx", ".md"];
        const filtered = files.filter(file => {
            const ext = "." + file.name.split(".").pop().toLowerCase();
            return supportedExtensions.includes(ext);
        });

        if (filtered.length === 0) {
            alert("No supported files selected. Supported types: .txt, .pdf, .docx, .md");
            return;
        }

        setStagedFiles(prev => {
            // Avoid duplicate filenames in staged files
            const existingNames = new Set(prev.map(f => f.name));
            const newFiles = filtered.filter(f => !existingNames.has(f.name));
            return [...prev, ...newFiles];
        });
    }

    // Handle standard inputs
    function handleFileChange(e) {
        if (e.target.files && e.target.files.length > 0) {
            stageFiles(Array.from(e.target.files));
        }
    }

    function handleFolderChange(e) {
        if (e.target.files && e.target.files.length > 0) {
            stageFiles(Array.from(e.target.files));
        }
    }

    // Clear Staging
    function clearStaging() {
        setStagedFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = "";
        if (folderInputRef.current) folderInputRef.current.value = "";
    }

    // Upload files to backend
    async function handleUpload() {
        if (stagedFiles.length === 0) return;

        setUploading(true);
        setUploadStatus("Uploading files...");

        const formData = new FormData();
        stagedFiles.forEach(file => {
            formData.append("files", file);
            // Reconstruct webkitRelativePath for folder structure, fallback to name
            const path = file.webkitRelativePath || file.name;
            formData.append("paths", path);
        });

        try {
            setUploadStatus("Indexing & building vector database...");
            const res = await uploadDocuments(formData);
            if (res.success) {
                clearStaging();
                await fetchDocs();
            } else {
                alert("Upload failed: " + res.error);
            }
        } catch (error) {
            console.error("Upload error:", error);
            alert("Upload failed. Make sure the backend server is running.");
        } finally {
            setUploading(false);
            setUploadStatus("");
        }
    }

    // Delete document
    async function handleDelete(path) {
        if (!confirm(`Are you sure you want to delete ${path}? This will remove it from the index.`)) {
            return;
        }

        setUploading(true);
        setUploadStatus(`Deleting ${path} & re-indexing...`);

        try {
            const res = await deleteDocument(path);
            if (res.success) {
                await fetchDocs();
            } else {
                alert("Deletion failed: " + res.error);
            }
        } catch (error) {
            console.error("Deletion error:", error);
            alert("Deletion failed. Make sure the backend server is running.");
        } finally {
            setUploading(false);
            setUploadStatus("");
        }
    }

    // Open Document in Viewer Modal
    async function handleView(doc) {
        setViewerDoc(doc);
        setViewerOpen(true);
        setViewerLoading(true);
        setViewerContent("");

        try {
            const res = await getDocumentContent(doc.path);
            if (res.success) {
                setViewerContent(res.content);
            } else {
                setViewerContent("Error loading content: " + res.error);
            }
        } catch (error) {
            console.error("Fetch content error:", error);
            setViewerContent("Failed to load document content. Make sure backend is running.");
        } finally {
            setViewerLoading(false);
        }
    }

    // Filter documents based on local search
    const filteredDocs = documents.filter(doc =>
        doc.path.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <section className="doc-manager-section">
            <div className="doc-manager-header">
                <h2>Knowledge Base Manager</h2>
                <p>Manage documents inside <code>data/documents</code>. Uploaded documents are parsed, chunked, embedded, and re-indexed automatically.</p>
            </div>

            {uploading && (
                <div className="status-overlay">
                    <div className="status-spinner"></div>
                    <h3>Processing Knowledge Base</h3>
                    <p>{uploadStatus}</p>
                </div>
            )}

            <div className="doc-manager-grid">
                {/* Upload Panel */}
                <div className="upload-panel card">
                    <h3>Add New Documents</h3>
                    <p className="subtitle">Supported: .txt, .pdf, .docx, .md</p>

                    <div 
                        className={`dropzone ${isDragActive ? "active" : ""}`}
                        onDragEnter={handleDrag}
                        onDragOver={handleDrag}
                        onDragLeave={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current && fileInputRef.current.click()}
                    >
                        <div className="dropzone-icon">📥</div>
                        <p>Drag & drop files here, or <span>browse files</span></p>
                    </div>

                    <div className="input-group">
                        <button 
                            className="btn btn-secondary" 
                            onClick={() => fileInputRef.current && fileInputRef.current.click()}
                            disabled={uploading}
                        >
                            📄 Select Files
                        </button>
                        <button 
                            className="btn btn-secondary" 
                            onClick={() => folderInputRef.current && folderInputRef.current.click()}
                            disabled={uploading}
                        >
                            📁 Select Folder
                        </button>
                    </div>

                    {/* Hidden Inputs */}
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        multiple 
                        style={{ display: "none" }} 
                        onChange={handleFileChange} 
                    />
                    <input 
                        type="file" 
                        ref={folderInputRef} 
                        webkitdirectory="" 
                        directory="" 
                        multiple 
                        style={{ display: "none" }} 
                        onChange={handleFolderChange} 
                    />

                    {/* Staged Files List */}
                    {stagedFiles.length > 0 && (
                        <div className="staged-container">
                            <h4>Selected Files ({stagedFiles.length})</h4>
                            <div className="staged-list">
                                {stagedFiles.map((file, idx) => (
                                    <div key={idx} className="staged-item">
                                        <span className="file-icon">📄</span>
                                        <span className="file-name" title={file.webkitRelativePath || file.name}>
                                            {file.webkitRelativePath || file.name}
                                        </span>
                                        <span className="file-size">{formatBytes(file.size)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="action-buttons">
                                <button className="btn btn-danger" onClick={clearStaging} disabled={uploading}>
                                    Cancel
                                </button>
                                <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
                                    Upload & Index
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Documents List */}
                <div className="docs-list-panel card">
                    <div className="docs-list-header">
                        <h3>Indexed Documents</h3>
                        <span className="doc-count">{documents.length} Files</span>
                    </div>

                    <div className="search-bar-wrapper">
                        <span className="search-icon">🔍</span>
                        <input 
                            type="text" 
                            placeholder="Filter files by name or path..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="docs-grid-container">
                        {loading ? (
                            <div className="list-loading">
                                <div className="spinner"></div>
                                <p>Loading documents...</p>
                            </div>
                        ) : filteredDocs.length === 0 ? (
                            <div className="empty-docs">
                                <h3>📂 No Documents Found</h3>
                                <p>{searchQuery ? "No matches for search query." : "No documents indexed. Upload files to get started."}</p>
                            </div>
                        ) : (
                            <div className="docs-grid">
                                {filteredDocs.map((doc, idx) => (
                                    <div key={idx} className="doc-item-card">
                                        <div className="doc-item-top">
                                            <div className="doc-item-icon">📄</div>
                                            <div className="doc-item-info">
                                                <h4 className="doc-item-name" title={doc.name}>
                                                    {doc.name}
                                                </h4>
                                                <p className="doc-item-path" title={doc.path}>
                                                    {doc.path}
                                                </p>
                                            </div>
                                        </div>
                                        
                                        <div className="doc-item-meta">
                                            <span>⚖️ {formatBytes(doc.size)}</span>
                                            <span>📅 {formatDate(doc.modified)}</span>
                                        </div>
                                        
                                        <div className="doc-item-actions">
                                            <button 
                                                className="btn-action view" 
                                                title="View parsed text"
                                                onClick={() => handleView(doc)}
                                            >
                                                👁️ View
                                            </button>
                                            <button 
                                                className="btn-action delete" 
                                                title="Remove from index"
                                                onClick={() => handleDelete(doc.path)}
                                            >
                                                🗑️ Delete
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Document Viewer Modal */}
            {viewerOpen && (
                <div className="viewer-modal">
                    <div className="viewer-content card">
                        <div className="viewer-header">
                            <div>
                                <h3>{viewerDoc?.name}</h3>
                                <p className="subtitle">{viewerDoc?.path}</p>
                            </div>
                            <button className="close-btn" onClick={() => setViewerOpen(false)}>×</button>
                        </div>
                        <div className="viewer-body">
                            {viewerLoading ? (
                                <div className="viewer-loader">
                                    <div className="spinner"></div>
                                    <p>Extracting & loading parsed text...</p>
                                </div>
                            ) : (
                                <pre className="parsed-text">
                                    {viewerContent || "This document is empty."}
                                </pre>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}

export default DocumentManager;
