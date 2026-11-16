import { useState } from "react";
import { BarChart3, BookOpenCheck, ShieldCheck } from "lucide-react";
import { login, loginWithApiKey, setupAdmin } from "../services/api";
import { Notice } from "../components/ui";
import "../styles/login.css";

/**
 * Sign-in with two portals (admin console / employee workspace).
 * On first run it shows the one-time admin setup, protected by
 * ADMIN_API_KEY from the backend .env file.
 */
function LoginPage({ status, onSignedIn, notice }) {
    const setupRequired = Boolean(status?.setup_required);

    const [portal, setPortal] = useState("admin");
    const [useApiKey, setUseApiKey] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [form, setForm] = useState({
        username: "",
        password: "",
        confirm: "",
        fullName: "",
        apiKey: "",
        setupKey: ""
    });

    const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });
    const settingUp = setupRequired && !useApiKey;

    function finish(session) {
        if (portal === "admin" && session.user.role !== "admin") {
            throw new Error("This account doesn't have admin access. Sign in as an employee instead.");
        }
        onSignedIn({ ...session, portal: session.user.role === "admin" ? portal : "employee" });
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");
        setBusy(true);

        try {
            if (settingUp) {
                if (form.password !== form.confirm) throw new Error("The passwords don't match.");
                const session = await setupAdmin({
                    setupKey: form.setupKey.trim(),
                    username: form.username.trim(),
                    password: form.password,
                    fullName: form.fullName.trim()
                });
                onSignedIn({ ...session, portal: "admin" });
            } else if (useApiKey) {
                finish(await loginWithApiKey(form.apiKey.trim()));
            } else {
                finish(await login(form.username.trim(), form.password));
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    function switchPortal(value) {
        setPortal(value);
        setError("");
        if (value === "employee") setUseApiKey(false);
    }

    return (
        <div className="login">
            <aside className="login-brand">
                <div className="login-brand-name">
                    <div className="brand-mark" aria-hidden="true">S</div>
                    <span>Semantic Search</span>
                </div>

                <div className="login-brand-body">
                    <h2>Answers from your own documents, checked before they're sent.</h2>
                    <ul>
                        <li><BookOpenCheck size={18} /><span>Every answer cites the policy or guide it came from.</span></li>
                        <li><ShieldCheck size={18} /><span>Only confident answers go out automatically; the rest come to your team.</span></li>
                        <li><BarChart3 size={18} /><span>See what people ask and which documents are missing.</span></li>
                    </ul>
                </div>

                <div className="login-brand-foot">Runs on your own servers. Questions and documents stay private.</div>
            </aside>

            <div className="login-pane">
            <main className="login-main">
                <form className="login-form" onSubmit={handleSubmit}>
                    <div>
                        <h1>{settingUp ? "Set up your workspace" : "Sign in"}</h1>
                        <p>
                            {settingUp
                                ? "Create the first admin account. You'll add the rest of your team afterwards."
                                : "Use the account your administrator created for you."}
                        </p>
                    </div>

                    {!settingUp && (
                        <div className="segmented login-switch" role="tablist" aria-label="Portal">
                            <button type="button" role="tab" aria-selected={portal === "admin"}
                                className={portal === "admin" ? "active" : ""} onClick={() => switchPortal("admin")}>
                                Admin
                            </button>
                            <button type="button" role="tab" aria-selected={portal === "employee"}
                                className={portal === "employee" ? "active" : ""} onClick={() => switchPortal("employee")}>
                                Employee
                            </button>
                        </div>
                    )}

                    {notice && <Notice tone="warn">{notice}</Notice>}
                    {error && <Notice tone="bad">{error}</Notice>}
                    {settingUp && !status?.setup_available && (
                        <Notice tone="warn">
                            Add <code>ADMIN_API_KEY</code> to the backend <code>.env</code> file and restart the backend first.
                        </Notice>
                    )}

                    {settingUp && (
                        <>
                            <label className="field">
                                <span>Setup key</span>
                                <input type="password" value={form.setupKey} onChange={update("setupKey")} autoComplete="off" required />
                                <small>The value of <code>ADMIN_API_KEY</code> in the backend <code>.env</code> file.</small>
                            </label>
                            <label className="field">
                                <span>Full name</span>
                                <input value={form.fullName} onChange={update("fullName")} autoComplete="name" />
                            </label>
                        </>
                    )}

                    {useApiKey ? (
                        <label className="field">
                            <span>API key</span>
                            <input type="password" value={form.apiKey} onChange={update("apiKey")} autoComplete="off" required autoFocus />
                        </label>
                    ) : (
                        <>
                            <label className="field">
                                <span>Username</span>
                                <input value={form.username} onChange={update("username")} autoComplete="username" required />
                            </label>
                            <label className="field">
                                <span>Password</span>
                                <input type="password" value={form.password} onChange={update("password")}
                                    autoComplete={settingUp ? "new-password" : "current-password"} required minLength={settingUp ? 8 : undefined} />
                                {settingUp && <small>At least 8 characters.</small>}
                            </label>
                            {settingUp && (
                                <label className="field">
                                    <span>Confirm password</span>
                                    <input type="password" value={form.confirm} onChange={update("confirm")} autoComplete="new-password" required />
                                </label>
                            )}
                        </>
                    )}

                    <button className="btn btn-primary btn-lg btn-block" type="submit" disabled={busy}>
                        {busy ? "Please wait…" : settingUp ? "Create admin account" : "Sign in"}
                    </button>

                    {(portal === "admin" || setupRequired) && (
                        <button type="button" className="login-link" onClick={() => { setUseApiKey(!useApiKey); setError(""); }}>
                            {useApiKey
                                ? (setupRequired ? "Back to account setup" : "Sign in with username and password")
                                : "Sign in with an API key instead"}
                        </button>
                    )}
                </form>
            </main>

            <footer className="login-foot">
                Admins manage the engine, documents and team. Employees answer the review queue.
            </footer>
            </div>
        </div>
    );
}

export default LoginPage;
