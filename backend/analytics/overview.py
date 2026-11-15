from collections import Counter, defaultdict
from datetime import datetime, timedelta


ROUTES = ("AUTO_REPLY", "HUMAN_REVIEW", "SKIPPED", "FAILED")


def _parse(timestamp):

    try:
        return datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None


def _rate(part, whole):

    return round(100.0 * part / whole, 1) if whole else 0.0


def build_overview(event_store, escalations, run_history, days=30, now=None):
    """
    Aggregate everything the analytics page shows for the last `days`
    days: email and search activity, intents, confidence, the review
    queue, inbox runs, agent activity and knowledge gaps.
    """

    days = max(1, min(int(days), 365))
    now = now or datetime.now()
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    since = start.isoformat(timespec="seconds")

    day_keys = [(start + timedelta(days=i)).date().isoformat() for i in range(days)]

    emails = event_store.email_events_since(since)
    searches = event_store.search_events_since(since)
    audit = event_store.audit_since(since)

    # ---------------- Emails ----------------

    route_counts = Counter(e["route"] for e in emails)
    emails_by_day = {day: {route: 0 for route in ROUTES} for day in day_keys}

    for event in emails:
        day = event["timestamp"][:10]
        if day in emails_by_day:
            emails_by_day[day][event["route"] if event["route"] in ROUTES else "FAILED"] += 1

    answered = route_counts["AUTO_REPLY"] + route_counts["HUMAN_REVIEW"]

    email_totals = {
        "total": len(emails),
        "auto_reply": route_counts["AUTO_REPLY"],
        "human_review": route_counts["HUMAN_REVIEW"],
        "skipped": route_counts["SKIPPED"],
        "failed": route_counts["FAILED"],
        "emails_sent": sum(e["email_sent"] for e in emails),
        "auto_reply_rate": _rate(route_counts["AUTO_REPLY"], answered),
        "avg_processing_ms": round(
            sum(e["duration_ms"] for e in emails) / len(emails)
        ) if emails else 0,
        "by_channel": dict(Counter(e["channel"] for e in emails))
    }

    # ---------------- Searches ----------------

    searches_by_day = {day: 0 for day in day_keys}

    for event in searches:
        day = event["timestamp"][:10]
        if day in searches_by_day:
            searches_by_day[day] += 1

    search_totals = {
        "total": len(searches),
        "confident": sum(1 for s in searches if s["route"] == "AUTO_REPLY"),
        "confident_rate": _rate(sum(1 for s in searches if s["route"] == "AUTO_REPLY"), len(searches)),
        "avg_response_ms": round(
            sum(s["duration_ms"] for s in searches) / len(searches)
        ) if searches else 0,
        "unique_users": len({s["actor"] for s in searches if s["actor"]})
    }

    # ---------------- Intents & confidence ----------------

    intents = Counter()
    for event in emails:
        if event["route"] != "SKIPPED":
            intents[event["intent"]] += 1
    for event in searches:
        intents[event["intent"]] += 1

    confidence = Counter(
        (e["confidence_level"] or "NONE")
        for e in list(emails) + list(searches)
        if e["route"] != "SKIPPED"
    )

    # ---------------- Knowledge gaps ----------------
    # Questions the system could not answer confidently: these show
    # which documents are missing from the knowledge base.

    gaps = Counter()
    gap_examples = {}

    for event in list(searches) + [e for e in emails if e["route"] == "HUMAN_REVIEW"]:
        if event.get("route") == "AUTO_REPLY":
            continue
        if event.get("confidence_level") not in ("LOW", "", None):
            continue
        text = (event.get("query") or event.get("subject") or "").strip()
        if not text:
            continue
        key = text.lower()[:120]
        gaps[key] += 1
        gap_examples.setdefault(key, {"text": text[:160], "intent": event.get("intent", "UNKNOWN")})

    knowledge_gaps = [
        {**gap_examples[key], "count": count}
        for key, count in gaps.most_common(8)
    ]

    # ---------------- Review queue ----------------

    pending = [e for e in escalations if e.get("status") == "PENDING"]
    resolved_recent = []
    resolution_hours = []

    for item in escalations:
        if item.get("status") != "RESOLVED":
            continue
        resolved_at = _parse(item.get("resolved_at"))
        created_at = _parse(item.get("timestamp"))
        if resolved_at and resolved_at >= start:
            resolved_recent.append(item)
            if created_at:
                resolution_hours.append((resolved_at - created_at).total_seconds() / 3600)

    oldest_pending = min((_parse(e.get("timestamp")) for e in pending if _parse(e.get("timestamp"))), default=None)

    review = {
        "pending": len(pending),
        "resolved": len(resolved_recent),
        "replied": sum(1 for e in resolved_recent if e.get("reply")),
        "avg_resolution_hours": round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else None,
        "oldest_pending_hours": round((now - oldest_pending).total_seconds() / 3600, 1) if oldest_pending else None,
        "pending_by_intent": dict(Counter(
            ((e.get("intent") or {}).get("intent") if isinstance(e.get("intent"), dict) else e.get("intent")) or "UNKNOWN"
            for e in pending
        ))
    }

    # ---------------- Inbox runs ----------------

    runs = [r for r in run_history if (r.get("timestamp") or "") >= since]
    runs_by_day = defaultdict(lambda: {"runs": 0, "fetched": 0, "processed": 0})

    for run in runs:
        bucket = runs_by_day[run["timestamp"][:10]]
        bucket["runs"] += 1
        bucket["fetched"] += run.get("fetched", 0)
        bucket["processed"] += run.get("processed", 0)

    run_totals = {
        "total": len(runs),
        "fetched": sum(r.get("fetched", 0) for r in runs),
        "processed": sum(r.get("processed", 0) for r in runs),
        "auto_reply": sum(r.get("auto_reply", 0) for r in runs),
        "human_review": sum(r.get("human_review", 0) for r in runs),
        "failed": sum(r.get("failed", 0) for r in runs),
        "last_run": runs[-1]["timestamp"] if runs else (run_history[-1]["timestamp"] if run_history else None)
    }

    # ---------------- People ----------------

    agent_actions = defaultdict(lambda: {"replied": 0, "resolved": 0, "searches": 0})

    for entry in audit:
        if entry["action"] == "escalation_replied":
            agent_actions[entry["actor"]]["replied"] += 1
        elif entry["action"] == "escalation_resolved":
            agent_actions[entry["actor"]]["resolved"] += 1

    for event in searches:
        if event["actor"]:
            agent_actions[event["actor"]]["searches"] += 1

    agents = sorted(
        ({"user": user, **counts} for user, counts in agent_actions.items()),
        key=lambda item: -(item["replied"] + item["resolved"] + item["searches"])
    )

    # ---------------- Timeline ----------------

    timeline = [
        {
            "date": day,
            "auto_reply": emails_by_day[day]["AUTO_REPLY"],
            "human_review": emails_by_day[day]["HUMAN_REVIEW"],
            "skipped": emails_by_day[day]["SKIPPED"],
            "failed": emails_by_day[day]["FAILED"],
            "searches": searches_by_day[day],
            "inbox_fetched": runs_by_day[day]["fetched"] if day in runs_by_day else 0
        }
        for day in day_keys
    ]

    return {
        "range": {"days": days, "since": since, "until": now.isoformat(timespec="seconds")},
        "emails": email_totals,
        "searches": search_totals,
        "intents": [{"intent": k, "count": v} for k, v in intents.most_common()],
        "confidence": {level: confidence.get(level, 0) for level in ("HIGH", "MEDIUM", "LOW", "NONE")},
        "review": review,
        "runs": run_totals,
        "agents": agents[:10],
        "knowledge_gaps": knowledge_gaps,
        "timeline": timeline
    }
