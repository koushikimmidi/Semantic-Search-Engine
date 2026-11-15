export function initials(name) {
    return (name || "?")
        .split(/[\s._-]+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0].toUpperCase())
        .join("");
}

/** "PASSWORD_RESET" -> "Password reset" */
export function formatIntent(intent) {
    const value = typeof intent === "object" && intent ? intent.intent : intent;
    if (!value) return "Unknown";
    const words = value.toLowerCase().split("_").map((word) => (word === "faq" ? "FAQ" : word));
    return [words[0].charAt(0).toUpperCase() + words[0].slice(1), ...words.slice(1)].join(" ");
}

export function formatDateTime(iso) {
    if (!iso) return "—";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function timeAgo(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const minutes = (Date.now() - date.getTime()) / 60000;
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${Math.round(minutes)} min ago`;
    if (minutes < 48 * 60) return `${Math.round(minutes / 60)} h ago`;
    return `${Math.round(minutes / 1440)} days ago`;
}
