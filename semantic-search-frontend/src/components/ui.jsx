import { useEffect, useState } from "react";
import { CircleAlert, CircleCheck, TriangleAlert, X } from "lucide-react";
import { changePassword } from "../services/api";

export function Notice({ tone = "info", children, onClose }) {
    const Icon = tone === "ok" ? CircleCheck : tone === "warn" ? TriangleAlert : CircleAlert;
    return (
        <div className={`notice ${tone}`} role={tone === "bad" ? "alert" : "status"}>
            <Icon size={16} strokeWidth={2} />
            <div style={{ flex: 1 }}>{children}</div>
            {onClose && (
                <button className="icon-button" style={{ width: 22, height: 22, margin: "-2px -4px 0 0" }} onClick={onClose} aria-label="Dismiss">
                    <X size={14} />
                </button>
            )}
        </div>
    );
}

export function Modal({ title, onClose, children, footer, wide = false }) {
    useEffect(() => {
        const onKey = (event) => event.key === "Escape" && onClose();
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [onClose]);

    return (
        <div className="overlay" onMouseDown={onClose}>
            <div
                className={`modal ${wide ? "wide" : ""}`}
                role="dialog"
                aria-modal="true"
                aria-label={title}
                onMouseDown={(e) => e.stopPropagation()}
            >
                <div className="modal-head">
                    <h2>{title}</h2>
                    <button className="icon-button" onClick={onClose} aria-label="Close" style={{ margin: "-6px -8px 0 0" }}>
                        <X size={16} />
                    </button>
                </div>
                {children}
                {footer && <div className="modal-foot">{footer}</div>}
            </div>
        </div>
    );
}

export function ChangePasswordModal({ onClose }) {
    const [form, setForm] = useState({ current: "", next: "", confirm: "" });
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [done, setDone] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");
        if (form.next !== form.confirm) {
            setError("The new passwords do not match.");
            return;
        }
        setBusy(true);
        try {
            await changePassword(form.current, form.next);
            setDone(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <Modal
            title="Change password"
            onClose={onClose}
            footer={done ? (
                <button className="btn btn-primary" onClick={onClose}>Done</button>
            ) : (
                <>
                    <button className="btn" onClick={onClose}>Cancel</button>
                    <button className="btn btn-primary" form="change-password" type="submit" disabled={busy}>
                        {busy ? "Saving…" : "Change password"}
                    </button>
                </>
            )}
        >
            <form id="change-password" className="modal-body" onSubmit={handleSubmit}>
                {done ? (
                    <Notice tone="ok">Your password has been changed.</Notice>
                ) : (
                    <>
                        {error && <Notice tone="bad">{error}</Notice>}
                        <label className="field">
                            <span>Current password</span>
                            <input type="password" autoComplete="current-password" required autoFocus
                                value={form.current} onChange={(e) => setForm({ ...form, current: e.target.value })} />
                        </label>
                        <label className="field">
                            <span>New password</span>
                            <input type="password" autoComplete="new-password" required minLength={8}
                                value={form.next} onChange={(e) => setForm({ ...form, next: e.target.value })} />
                            <small>At least 8 characters.</small>
                        </label>
                        <label className="field">
                            <span>Confirm new password</span>
                            <input type="password" autoComplete="new-password" required
                                value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
                        </label>
                    </>
                )}
            </form>
        </Modal>
    );
}
