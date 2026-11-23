"""Weekly account report: value delivered, adoption by practice and person, and the stall list."""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from .model import Thread, parse_time
from .rules import AT_RISK, RANK, STALLED, classify

# From a public time-saved calculator's defaults (tryvela.ai): 15 minutes of
# coordination per interview. Reschedules handled are counted at the same 15 minutes.
MINUTES_PER_BOOKING = 15
MINUTES_PER_RESCHEDULE = 15


def _in(t: datetime, start: datetime, end: datetime) -> bool:
    return start < t <= end


def _booked_at(th: Thread, as_of: datetime):
    """Time of the last confirm, if the thread is booked as of as_of."""
    if th.state(as_of) != "booked":
        return None
    return max(e.t for e in th.upto(as_of) if e.kind == "confirm")


def week_stats(threads: List[Thread], users: List[dict], start: datetime, end: datetime) -> dict:
    started = [t for t in threads if _in(t.started(), start, end)]
    booked = [t for t in threads if (b := _booked_at(t, end)) and _in(b, start, end)]
    resched = sum(1 for t in threads for e in t.upto(end) if e.kind == "reschedule" and _in(e.t, start, end))
    cancelled = [t for t in threads if t.state(end) == "cancelled"
                 and _in(max(e.t for e in t.upto(end)), start, end)]
    hours_to_book = [(_booked_at(t, end) - t.started()).total_seconds() / 3600 for t in booked]
    active = {t.owner for t in started}
    live = [u for u in users if parse_time(u["live_from"]) <= end]
    minutes = len(booked) * MINUTES_PER_BOOKING + resched * MINUTES_PER_RESCHEDULE
    return {
        "start": start, "end": end,
        "threads_started": len(started), "booked": len(booked), "reschedules": resched,
        "cancelled": len(cancelled),
        "median_hours_to_book": round(statistics.median(hours_to_book), 1) if hours_to_book else None,
        "booked_within_24h": sum(1 for h in hours_to_book if h <= 24),
        "active_users": len(active & {u["name"] for u in live}), "live_seats": len(live),
        "hours_returned": round(minutes / 60, 1),
    }


def build_report(threads: List[Thread], users: List[dict], as_of: datetime, weeks: int = 4,
                 account: str = "Example Search Partners") -> dict:
    week_start = as_of - timedelta(days=7)
    this_week = week_stats(threads, users, week_start, as_of)
    trend = [week_stats(threads, users, as_of - timedelta(days=7 * (i + 1)), as_of - timedelta(days=7 * i))
             for i in reversed(range(weeks))]

    # Stall list over every open thread.
    flagged, open_count = [], 0
    wait_hours = defaultdict(float)
    for th in threads:
        if th.started() > as_of or th.state(as_of) != "open":
            continue
        open_count += 1
        f = classify(th, as_of)
        if f.waiting_on:
            side = {"internal": "inside the firm", "agent": "on the agent"}.get(f.waiting_on, "outside the firm")
            wait_hours[side] += f.waiting_hours
        if f.flag in (STALLED, AT_RISK):
            flagged.append({"thread": th.id, "search": th.search_id, "practice": th.practice,
                            "owner": th.owner, "meeting": th.meeting, "rounds": th.rounds(as_of), **f.as_dict()})
    flagged.sort(key=lambda r: (RANK[r["flag"]], -r["waiting_hours"]))

    # Adoption by practice and by person.
    by_practice: Dict[str, dict] = {}
    people = []
    for u in users:
        live_from = parse_time(u["live_from"])
        if live_from > as_of:
            continue
        mine = [t for t in threads if t.owner == u["name"] and t.started() <= as_of]
        this = [t for t in mine if _in(t.started(), week_start, as_of)]
        last = max((t.started() for t in mine), default=None)
        status = "active" if this else ("never started" if last is None else "gone quiet")
        people.append({"name": u["name"], "practice": u["practice"], "live_from": u["live_from"][:10],
                       "threads_this_week": len(this), "last_thread": last.date().isoformat() if last else "",
                       "status": status})
        p = by_practice.setdefault(u["practice"], {"practice": u["practice"], "seats": 0, "active": 0,
                                                   "threads": 0, "open": 0, "flagged": 0, "stalled": 0})
        p["seats"] += 1
        p["active"] += status == "active"
        p["threads"] += len(this)
    for th in threads:
        if th.practice in by_practice and th.started() <= as_of and th.state(as_of) == "open":
            by_practice[th.practice]["open"] += 1
    for r in flagged:
        if r["practice"] in by_practice:
            by_practice[r["practice"]]["flagged"] += 1
            by_practice[r["practice"]]["stalled"] += r["flag"] == STALLED
    for p in by_practice.values():
        p["active_share"] = round(p["active"] / p["seats"], 2) if p["seats"] else 0.0
        # Stalled threads as a share of the week's volume, so a busy practice is not punished for size.
        stalled_share = p["stalled"] / max(p["threads"], 1)
        if p["active_share"] >= 0.7 and stalled_share <= 0.10:
            p["health"] = "green"
        elif p["active_share"] >= 0.4 and stalled_share <= 0.25:
            p["health"] = "yellow"
        else:
            p["health"] = "red"

    total_wait = sum(wait_hours.values())
    return {
        "account": account, "as_of": as_of.isoformat(), "week": this_week, "trend": trend,
        "open_threads": open_count, "flagged": flagged,
        "stalled": sum(1 for r in flagged if r["flag"] == STALLED),
        "at_risk": sum(1 for r in flagged if r["flag"] == AT_RISK),
        "waiting_split": {k: round(v / total_wait, 2) for k, v in wait_hours.items()} if total_wait else {},
        "practices": sorted(by_practice.values(), key=lambda p: p["practice"]),
        "people": sorted(people, key=lambda p: ({"never started": 0, "gone quiet": 1, "active": 2}[p["status"]],
                                                 p["practice"], p["name"])),
        "assumptions": {"minutes_per_booking": MINUTES_PER_BOOKING,
                        "minutes_per_reschedule": MINUTES_PER_RESCHEDULE},
    }
