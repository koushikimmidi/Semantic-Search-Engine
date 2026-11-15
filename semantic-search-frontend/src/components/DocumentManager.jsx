import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Eye, FileText, FolderUp, Search, Trash2, Upload } from "lucide-react";
import { deleteDocument, getDocumentContent, listDocuments, uploadDocuments } from "../services/api";
import { Modal, Notice } from "./ui";
import "../styles/work.css";

const SUPPORTED = [".txt", ".pdf", ".docx", ".md"];

function formatBytes(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
    return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

function formatDate(seconds) {
    return new Date(seconds * 1000).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/** Knowledge base: everyone can browse; admins can upload and delete. */
function DocumentManager({ readOnly = false }) {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("");
    const [staged, setStaged] = useState([]);
    const [dragging, setDragging] = useState(false);
    const [working, setWorking] = useState("");
    const [flash, setFlash] = useState(null);
    const [viewer, setViewer] = useState(null);

    const fileInput = useRef(null);
    const folderInput = useRef(null);

    const load = useCallback(async () => {
        try {
            setDocuments(await listDocuments());
        } catch (err) {
            setFlash({ tone: "bad", text: err.message });
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const initial = setTimeout(load, 0);
        return () => clearTimeout(initial);
    }, [load]);

    function stage(files) {
        const supported = files.filter((file) => SUPPORTED.includes(`.${file.name.split(".").pop().toLowerCase()}`));
        if (supported.length < files.length) {
            setFlash({ tone: "warn", text: `Skipped ${files.length - supported.length} unsupported file(s). Supported: PDF, Word, Markdown, text.` });
        }
        setStaged((current) => {
            const names = new Set(current.map((f) => f.webkitRelativePath || f.name));
            return [...current, ...supported.filter((f) => !names.has(f.webkitRelativePath || f.name))];
        });
    }

    function clearStaged() {
        setStaged([]);
        if (fileInput.current) fileInput.current.value = "";
        if (folderInput.current) folderInput.current.value = "";
    }

    async function upload() {
        if (!staged.length) return;
        setWorking("Uploading and re-indexing…");
        setFlash(null);

        const form = new FormData();
        staged.forEach((file) => {
            form.append("files", file);
            form.append("paths", file.webkitRelativePath || file.name);
        });

        const result = await uploadDocuments(form);
        setWorking("");

        if (result.success) {
            setFlash({ tone: "ok", text: `Added ${result.count} document${result.count === 1 ? "" : "s"}. The assistant can use them now.` });
            clearStaged();
            load();
        } else {
            setFlash({ tone: "bad", text: `Upload failed: ${result.error}` });
        }
    }

    async function remove(doc) {
        if (!window.confirm(`Delete ${doc.path}? The assistant will stop using it.`)) return;
        setWorking(`Deleting ${doc.name}…`);
        setFlash(null);
        const result = await deleteDocument(doc.path);
        setWorking("");
        if (result.success) {
            setFlash({ tone: "ok", text: `Deleted ${doc.name}.` });
            load();
        } else {
            setFlash({ tone: "bad", text: `Couldn't delete: ${result.error}` });
        }
    }

    async function view(doc) {
        setViewer({ doc, content: null });
        try {
            const result = await getDocumentContent(doc.path);
            setViewer({ doc, content: result.content || "(empty document)" });
        } catch (err) {
            setViewer({ doc, content: `Couldn't load this document: ${err.message}` });
        }
    }

    const visible = useMemo(
        () => documents
            .filter((doc) => doc.path.toLowerCase().includes(filter.toLowerCase()))
            .sort((a, b) => a.path.localeCompare(b.path)),
        [documents, filter]
    );

    const totalSize = documents.reduce((sum, doc) => sum + doc.size, 0);

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>Knowledge base</h1>
                    <p>
                        {readOnly
                            ? "The documents the assistant answers from. Ask an admin to add or remove documents."
                            : "The documents the assistant answers from. Changes are indexed straight away."}
                    </p>
                </div>
                <div className="row small muted">
                    <span className="num">{documents.length} documents</span>
                    <span className="faint">·</span>
                    <span className="num">{formatBytes(totalSize)}</span>
                </div>
            </div>

            {flash && <Notice tone={flash.tone} onClose={() => setFlash(null)}>{flash.text}</Notice>}

            {!readOnly && (
                <div className="card">
                    <div className="card-body stack">
                        <div
                            className={`dropzone ${dragging ? "active" : ""}`}
                            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={(e) => {
                                e.preventDefault();
                                setDragging(false);
                                if (e.dataTransfer.files?.length) stage(Array.from(e.dataTransfer.files));
                            }}
                            onClick={() => fileInput.current?.click()}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInput.current?.click()}
                        >
                            <Upload size={20} />
                            <div><strong style={{ color: "var(--text)", fontWeight: 500 }}>Drop files here</strong> or click to browse</div>
                            <div className="small faint">PDF, Word, Markdown or plain text</div>
                        </div>

                        <input ref={fileInput} type="file" multiple hidden accept={SUPPORTED.join(",")}
                            onChange={(e) => e.target.files?.length && stage(Array.from(e.target.files))} />
                        <input ref={folderInput} type="file" multiple hidden webkitdirectory="" directory=""
                            onChange={(e) => e.target.files?.length && stage(Array.from(e.target.files))} />

                        {staged.length > 0 && (
                            <>
                                <ul className="staged">
                                    {staged.map((file) => (
                                        <li key={file.webkitRelativePath || file.name}>
                                            <span>{file.webkitRelativePath || file.name}</span>
                                            <span className="faint num">{formatBytes(file.size)}</span>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}

                        {working && <div className="busy-bar" aria-label={working} />}

                        <div className="row" style={{ justifyContent: "space-between" }}>
                            <button className="btn btn-ghost btn-sm" onClick={() => folderInput.current?.click()} disabled={Boolean(working)}>
                                <FolderUp size={15} /> Upload a folder
                            </button>
                            {staged.length > 0 && (
                                <div className="row">
                                    <button className="btn" onClick={clearStaged} disabled={Boolean(working)}>Cancel</button>
                                    <button className="btn btn-primary" onClick={upload} disabled={Boolean(working)}>
                                        {working ? "Working…" : `Add ${staged.length} file${staged.length === 1 ? "" : "s"}`}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <div className="card">
                <div className="queue-search" style={{ borderBottom: "1px solid var(--line)" }}>
                    <Search size={15} className="faint" />
                    <input className="queue-search-input" placeholder="Filter by name or folder" value={filter}
                        onChange={(e) => setFilter(e.target.value)} aria-label="Filter documents" />
                </div>

                {loading ? (
                    <p className="empty">Loading…</p>
                ) : visible.length === 0 ? (
                    <p className="empty">{filter ? "No documents match." : "No documents yet."}</p>
                ) : (
                    <div className="table-wrap">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Folder</th>
                                    <th className="right">Size</th>
                                    <th>Updated</th>
                                    <th className="right"><span className="sr-only">Actions</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                {visible.map((doc) => {
                                    const folder = doc.path.includes("/") ? doc.path.slice(0, doc.path.lastIndexOf("/")) : "—";
                                    return (
                                        <tr key={doc.path}>
                                            <td>
                                                <span className="doc-name"><FileText size={15} />{doc.name}</span>
                                            </td>
                                            <td className="folder-tag">{folder.replace(/_/g, " ")}</td>
                                            <td className="right muted">{formatBytes(doc.size)}</td>
                                            <td className="muted">{formatDate(doc.modified)}</td>
                                            <td className="right">
                                                <div className="row" style={{ justifyContent: "flex-end", flexWrap: "nowrap", gap: 2 }}>
                                                    <button className="icon-button" onClick={() => view(doc)} aria-label={`View ${doc.name}`} title="View text">
                                                        <Eye size={15} />
                                                    </button>
                                                    {!readOnly && (
                                                        <button className="icon-button" onClick={() => remove(doc)} disabled={Boolean(working)}
                                                            aria-label={`Delete ${doc.name}`} title="Delete">
                                                            <Trash2 size={15} />
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {viewer && (
                <Modal wide title={viewer.doc.name} onClose={() => setViewer(null)}>
                    <div className="modal-body">
                        <div className="small faint">{viewer.doc.path}</div>
                        {viewer.content === null ? (
                            <div className="busy-bar" />
                        ) : (
                            <div className="doc-viewer">{viewer.content}</div>
                        )}
                    </div>
                </Modal>
            )}
        </div>
    );
}

export default DocumentManager;
