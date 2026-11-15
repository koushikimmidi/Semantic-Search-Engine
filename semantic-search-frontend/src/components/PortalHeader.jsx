import { ChevronRight, Menu } from "lucide-react";

/** Slim top bar: where you are, plus the mobile menu button. */
function PortalHeader({ portal, title, onOpenNav, children }) {
    return (
        <header className="topbar">
            <button className="icon-button menu-toggle" onClick={onOpenNav} aria-label="Open navigation">
                <Menu size={18} />
            </button>
            <div className="topbar-crumbs">
                <span>{portal === "admin" ? "Admin console" : "Workspace"}</span>
                <ChevronRight size={14} />
                <strong>{title}</strong>
            </div>
            <div className="topbar-actions">{children}</div>
        </header>
    );
}

export default PortalHeader;
