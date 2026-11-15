import json
from datetime import datetime


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _intent_name(intent):

    if isinstance(intent, dict):
        return intent.get("intent") or "UNKNOWN"

    return intent or "UNKNOWN"


def _confidence(confidence):

    confidence = confidence or {}

    return confidence.get("level", "") or "", confidence.get("top_score")


class EventStore:
    """
    Records what the system does, for analytics and the audit log:

        email_events   every processed email (inbox or test)
        search_events  every question asked in the UI / API
        audit_log      every administrative or agent action

    Logging must never break the request that triggered it, so all
    writes swallow their own errors.
    """

    def __init__(self, db):

        self.db = db

    # ========================================================
    # WRITE
    # ========================================================

    def log_email(self, channel, message, result, duration_ms):

        try:

            route = result.get("route") or ("FAILED" if not result.get("success") else "")
            level, top_score = _confidence(result.get("confidence"))
            email = result.get("email") or {}

            self.db.execute(
                "INSERT INTO email_events (timestamp, channel, sender, subject, query, intent, "
                "route, confidence_level, top_score, email_sent, duration_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _now(),
                    channel,
                    (message.get("sender_email") or message.get("sender") or "")[:200],
                    (message.get("subject") or "")[:300],
                    (message.get("body") or "")[:500],
                    _intent_name(result.get("intent")),
                    route or "FAILED",
                    level,
                    top_score,
                    1 if email.get("sent") else 0,
                    int(duration_ms)
                )
            )

        except Exception as e:
            print("Could not log email event:", str(e))

    def log_search(self, actor, query, response, duration_ms):

        try:

            level, top_score = _confidence(response.get("confidence"))

            self.db.execute(
                "INSERT INTO search_events (timestamp, actor, query, intent, route, "
                "confidence_level, top_score, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _now(),
                    actor or "",
                    (query or "")[:500],
                    _intent_name(response.get("intent")),
                    (response.get("routing") or {}).get("route", ""),
                    level,
                    top_score,
                    int(duration_ms)
                )
            )

        except Exception as e:
            print("Could not log search event:", str(e))

    def audit(self, principal, action, target="", details=None):

        try:

            principal = principal or {}

            self.db.execute(
                "INSERT INTO audit_log (timestamp, actor, role, action, target, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    _now(),
                    principal.get("username", "system"),
                    principal.get("role", "system"),
                    action,
                    str(target or "")[:300],
                    json.dumps(details, default=str)[:2000] if details else ""
                )
            )

        except Exception as e:
            print("Could not write audit log:", str(e))

    # ========================================================
    # READ
    # ========================================================

    def list_audit(self, limit=100, offset=0, action=None, actor=None):

        sql = "SELECT * FROM audit_log"
        clauses, params = [], []

        if action:
            clauses.append("action = ?")
            params.append(action)

        if actor:
            clauses.append("actor = ?")
            params.append(actor)

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        total = self.db.query(sql.replace("SELECT *", "SELECT COUNT(*) AS n", 1), params)[0]["n"]

        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"

        rows = self.db.query(sql, params + [max(1, min(limit, 500)), max(0, offset)])

        for row in rows:
            try:
                row["details"] = json.loads(row["details"]) if row["details"] else None
            except json.JSONDecodeError:
                pass

        return {"total": total, "items": rows}

    def list_actions(self):

        return [r["action"] for r in self.db.query("SELECT DISTINCT action FROM audit_log ORDER BY action")]

    def email_events_since(self, since):

        return self.db.query(
            "SELECT * FROM email_events WHERE timestamp >= ? ORDER BY timestamp", (since,)
        )

    def search_events_since(self, since):

        return self.db.query(
            "SELECT * FROM search_events WHERE timestamp >= ? ORDER BY timestamp", (since,)
        )

    def audit_since(self, since):

        return self.db.query(
            "SELECT * FROM audit_log WHERE timestamp >= ? ORDER BY timestamp", (since,)
        )
