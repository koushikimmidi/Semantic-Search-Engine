import { useEffect, useRef, useState } from "react";
import { ArrowLeftRight, ChevronsUpDown, KeyRound, LogOut, Moon, Sun } from "lucide-react";
import { initials } from "../utils/format";

function Sidebar({
    portal,
    groups,
    activeTab,
    onNavigate,
    pendingCount = 0,
    user,
    method,
    darkMode,
    onToggleTheme,
    onChangePassword,
    onSwitchPortal,
    onSignOut
}) {
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        if (!menuOpen) return undefined;
        const close = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false);
        };
        document.addEventListener("mousedown", close);
        return () => document.removeEventListener("mousedown", close);
    }, [menuOpen]);

    const name = user?.full_name || user?.username || "User";
    const roleLabel = user?.role === "admin" ? "Administrator" : "Employee";

    return (
        <aside className="side" aria-label="Sidebar">
            <div className="side-brand">
                <div className="brand-mark" aria-hidden="true">S</div>
                <div>
                    <strong>Semantic Search</strong>
                    <span>{portal === "admin" ? "Admin console" : "Employee workspace"}</span>
                </div>
            </div>

            {groups.map((group) => (
                <nav className="side-group" key={group.label} aria-label={group.label}>
                    <div className="side-label">{group.label}</div>
                    {group.items.map(({ id, label, icon: Icon, badge }) => (
                        <button
                            key={id}
                            className={`side-link ${activeTab === id ? "active" : ""}`}
                            onClick={() => onNavigate(id)}
                            aria-current={activeTab === id ? "page" : undefined}
                        >
                            <Icon size={16} strokeWidth={1.8} />
                            <span>{label}</span>
                            {badge && pendingCount > 0 && (
                                <span className="side-count" aria-label={`${pendingCount} waiting`}>{pendingCount}</span>
                            )}
                        </button>
                    ))}
                </nav>
            ))}

            <div className="side-spacer" />

            <div className="side-user" ref={menuRef}>
                {menuOpen && (
                    <div className="menu" role="menu">
                        {method === "account" && (
                            <button role="menuitem" onClick={() => { setMenuOpen(false); onChangePassword(); }}>
                                <KeyRound size={15} /> Change password
                            </button>
                        )}
                        <button role="menuitem" onClick={() => { onToggleTheme(); }}>
                            {darkMode ? <Sun size={15} /> : <Moon size={15} />}
                            {darkMode ? "Light theme" : "Dark theme"}
                        </button>
                        {onSwitchPortal && (
                            <button role="menuitem" onClick={() => { setMenuOpen(false); onSwitchPortal(); }}>
                                <ArrowLeftRight size={15} />
                                {portal === "admin" ? "View as employee" : "Back to admin console"}
                            </button>
                        )}
                        <hr />
                        <button role="menuitem" onClick={onSignOut}>
                            <LogOut size={15} /> Sign out
                        </button>
                    </div>
                )}

                <button
                    className="side-user-button"
                    onClick={() => setMenuOpen((open) => !open)}
                    aria-haspopup="menu"
                    aria-expanded={menuOpen}
                >
                    <span className="avatar" aria-hidden="true">{initials(name)}</span>
                    <span className="side-user-meta">
                        <strong>{name}</strong>
                        <span>{roleLabel}{method === "api_key" ? " · API key" : ""}</span>
                    </span>
                    <ChevronsUpDown size={15} className="faint" />
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
