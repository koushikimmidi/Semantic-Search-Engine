import { useCallback, useEffect, useState } from "react";
import { MoreHorizontal, Plus } from "lucide-react";
import { createUser, deleteUser, listUsers, updateUser } from "../services/api";
import { Modal, Notice } from "../components/ui";
import { initials, timeAgo } from "../utils/format";

const EMPTY = { username: "", full_name: "", password: "", role: "employee" };

function RowMenu({ user, isSelf, onReset, onToggle, onDelete }) {
    const [open, setOpen] = useState(false);

    useEffect(() => {
        if (!open) return undefined;
        const close = () => setOpen(false);
        const id = setTimeout(() => document.addEventListener("click", close), 0);
        return () => {
            clearTimeout(id);
            document.removeEventListener("click", close);
        };
    }, [open]);

    return (
        <div style={{ position: "relative", display: "inline-block" }}>
            <button className="icon-button" onClick={() => setOpen(!open)} aria-label={`Actions for ${user.username}`} aria-haspopup="menu">
                <MoreHorizontal size={16} />
            </button>
            {open && (
                <div className="menu" role="menu" style={{ top: "calc(100% + 4px)", bottom: "auto", left: "auto", right: 0, width: 190 }}>
                    <button role="menuitem" onClick={onReset}>Reset password</button>
                    {!isSelf && <button role="menuitem" onClick={onToggle}>{user.active ? "Disable account" : "Enable account"}</button>}
                    {!isSelf && <><hr /><button role="menuitem" onClick={onDelete} style={{ color: "var(--bad)" }}>Delete account</button></>}
                </div>
            )}
        </div>
    );
}

function UsersPage({ currentUser }) {
    const [users, setUsers] = useState([]);
    const [flash, setFlash] = useState(null);
    const [busy, setBusy] = useState(false);
    const [creating, setCreating] = useState(false);
    const [form, setForm] = useState(EMPTY);
    const [formError, setFormError] = useState("");
    const [resetFor, setResetFor] = useState(null);
    const [resetPassword, setResetPassword] = useState("");

    const load = useCallback(async () => {
        try {
            setUsers((await listUsers()).users || []);
        } catch (err) {
            setFlash({ tone: "bad", text: err.message });
        }
    }, []);

    useEffect(() => {
        const initial = setTimeout(load, 0);
        return () => clearTimeout(initial);
    }, [load]);

    async function run(action, success) {
        setBusy(true);
        setFlash(null);
        try {
            await action();
            setFlash({ tone: "ok", text: success });
            await load();
            return true;
        } catch (err) {
            setFlash({ tone: "bad", text: err.message });
            return false;
        } finally {
            setBusy(false);
        }
    }

    async function create(event) {
        event.preventDefault();
        setFormError("");
        setBusy(true);
        try {
            await createUser({ ...form, username: form.username.trim(), full_name: form.full_name.trim() });
            setFlash({ tone: "ok", text: `Created ${form.username.trim()}. Share the password with them privately.` });
            setCreating(false);
            setForm(EMPTY);
            await load();
        } catch (err) {
            setFormError(err.message);
        } finally {
            setBusy(false);
        }
    }

    async function reset(event) {
        event.preventDefault();
        const ok = await run(() => updateUser(resetFor.id, { password: resetPassword }), `Password reset for ${resetFor.username}.`);
        if (ok) setResetFor(null);
    }

    const isSelf = (user) => user.username === currentUser?.username;
    const admins = users.filter((u) => u.role === "admin").length;

    return (
        <div className="page">
            <div className="page-head">
                <div>
                    <h1>Users</h1>
                    <p>Who can sign in. Admins use the admin console; employees use the workspace and review queue.</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setCreating(true); setFormError(""); }}>
                    <Plus size={15} /> Add user
                </button>
            </div>

            {flash && <Notice tone={flash.tone} onClose={() => setFlash(null)}>{flash.text}</Notice>}

            <div className="card">
                <div className="table-wrap">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Last sign-in</th>
                                <th className="right"><span className="sr-only">Actions</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user) => (
                                <tr key={user.id}>
                                    <td>
                                        <div className="row" style={{ flexWrap: "nowrap", gap: 10 }}>
                                            <span className="avatar">{initials(user.full_name || user.username)}</span>
                                            <div style={{ minWidth: 0 }}>
                                                <div style={{ fontWeight: 500 }}>
                                                    {user.full_name || user.username}
                                                    {isSelf(user) && <span className="faint" style={{ fontWeight: 400 }}> (you)</span>}
                                                </div>
                                                <span className="cell-sub mono">{user.username}</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <select
                                            className="input input-sm"
                                            style={{ width: 128 }}
                                            value={user.role}
                                            disabled={busy || isSelf(user)}
                                            onChange={(e) => run(() => updateUser(user.id, { role: e.target.value }), `${user.username} is now ${e.target.value === "admin" ? "an admin" : "an employee"}.`)}
                                            aria-label={`Role for ${user.username}`}
                                        >
                                            <option value="employee">Employee</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </td>
                                    <td><span className={`status ${user.active ? "ok" : "bad"}`}>{user.active ? "Active" : "Disabled"}</span></td>
                                    <td className="muted">{user.last_login ? timeAgo(user.last_login) : "Never"}</td>
                                    <td className="right">
                                        <RowMenu
                                            user={user}
                                            isSelf={isSelf(user)}
                                            onReset={() => { setResetFor(user); setResetPassword(""); }}
                                            onToggle={() => run(() => updateUser(user.id, { active: !user.active }), `${user.username} ${user.active ? "disabled" : "enabled"}.`)}
                                            onDelete={() => window.confirm(`Delete ${user.username}? This can't be undone.`) && run(() => deleteUser(user.id), `Deleted ${user.username}.`)}
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="card-foot small faint">
                    <span>{users.length} account{users.length === 1 ? "" : "s"} · {admins} admin{admins === 1 ? "" : "s"}</span>
                    <span>Disabling an account signs that person out immediately.</span>
                </div>
            </div>

            <div className="card">
                <div className="card-head">
                    <div>
                        <div className="section-title">Permissions</div>
                        <div className="section-sub">Checked by the server on every request.</div>
                    </div>
                </div>
                <div className="card-body" style={{ padding: "8px 4px 4px" }}>
                    <div className="table-wrap">
                        <table className="table">
                            <thead><tr><th>Can…</th><th>Employee</th><th>Admin</th></tr></thead>
                            <tbody>
                                {[
                                    ["Ask questions and browse documents", true, true],
                                    ["Reply to and resolve the review queue", true, true],
                                    ["Try messages and see the overview", true, true],
                                    ["Add or delete documents, re-index", false, true],
                                    ["Check the inbox, run the scheduler, change settings", false, true],
                                    ["Manage users and read the audit log", false, true]
                                ].map(([label, emp, adm]) => (
                                    <tr key={label}>
                                        <td>{label}</td>
                                        <td>{emp ? <span className="status ok">Yes</span> : <span className="faint">No</span>}</td>
                                        <td>{adm ? <span className="status ok">Yes</span> : <span className="faint">No</span>}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {creating && (
                <Modal
                    title="Add user"
                    onClose={() => setCreating(false)}
                    footer={<>
                        <button className="btn" onClick={() => setCreating(false)}>Cancel</button>
                        <button className="btn btn-primary" type="submit" form="create-user" disabled={busy}>Create account</button>
                    </>}
                >
                    <form id="create-user" className="modal-body" onSubmit={create}>
                        {formError && <Notice tone="bad">{formError}</Notice>}
                        <label className="field">
                            <span>Full name</span>
                            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} autoFocus />
                        </label>
                        <label className="field">
                            <span>Username</span>
                            <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="off" required />
                            <small>Letters, numbers, dots, dashes. Used to sign in.</small>
                        </label>
                        <label className="field">
                            <span>Temporary password</span>
                            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" required minLength={8} />
                            <small>At least 8 characters. They can change it after signing in.</small>
                        </label>
                        <label className="field">
                            <span>Role</span>
                            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                                <option value="employee">Employee</option>
                                <option value="admin">Admin</option>
                            </select>
                        </label>
                    </form>
                </Modal>
            )}

            {resetFor && (
                <Modal
                    title={`Reset password for ${resetFor.username}`}
                    onClose={() => setResetFor(null)}
                    footer={<>
                        <button className="btn" onClick={() => setResetFor(null)}>Cancel</button>
                        <button className="btn btn-primary" type="submit" form="reset-password" disabled={busy}>Reset password</button>
                    </>}
                >
                    <form id="reset-password" className="modal-body" onSubmit={reset}>
                        <label className="field">
                            <span>New password</span>
                            <input type="password" autoComplete="new-password" required minLength={8} autoFocus
                                value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} />
                            <small>At least 8 characters.</small>
                        </label>
                    </form>
                </Modal>
            )}
        </div>
    );
}

export default UsersPage;
