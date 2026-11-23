"""Generate the synthetic sample account in data/ (deterministic).

Every thread, name and number here is made up. The reply-time mix is loosely shaped
like a public Executive Search Scheduling Benchmark (tryvela.ai/benchmark) (about half of replies inside
an hour, most inside a day, clients moving meetings more often than candidates), so the
report has realistic texture. It is not data from that benchmark or from any firm.
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 7
AS_OF = datetime(2026, 11, 20, 17, 0, tzinfo=timezone.utc)
START = AS_OF - timedelta(days=28)
OUT = Path(__file__).resolve().parent.parent / "data"

FIRST = ["Avery", "Blake", "Casey", "Devon", "Emery", "Finley", "Harper", "Jordan", "Kendall", "Logan",
         "Morgan", "Parker", "Quinn", "Reese", "Riley", "Rowan", "Sage", "Skyler", "Taylor", "Wren"]
LAST = ["Abbott", "Bishop", "Carver", "Doyle", "Ellis", "Foster", "Grant", "Hayes", "Irving", "Keane",
        "Lowe", "Marsh", "Nolan", "Ortiz", "Pryce", "Reid", "Shaw", "Tate", "Vance", "Wells"]

# Practice -> (seats, go-live date, threads per active user per week)
PRACTICES = {
    "Consumer": (8, START + timedelta(days=2), 5.0),        # pilot practice, live from week 1
    "Enterprise": (10, START + timedelta(days=16), 4.0),    # second practice, live from week 3
}


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def reply_delay(rng, party):
    """Hours until a counterparty replies, or None if they go silent."""
    if rng.random() < (0.13 if party == "candidate" else 0.10):
        return None
    if rng.random() < 0.49:
        return rng.uniform(0.05, 1.0)
    if rng.random() < 0.80:
        return rng.uniform(1.0, 20.0)
    return rng.uniform(20.0, 70.0)


def simulate(rng, tid, owner, practice, t0):
    meeting = rng.choices(["candidate_interview", "client_panel", "debrief"], [0.6, 0.3, 0.1])[0]
    ext = "candidate" if meeting == "candidate_interview" else "client"
    ev = [{"t": t0, "by": "internal", "kind": "request", "waiting_on": "agent"}]
    t = t0 + timedelta(minutes=rng.uniform(1, 6))
    ev.append({"t": t, "by": "agent", "kind": "propose", "waiting_on": ext})
    missed_cadence = rng.random() < 0.01
    moves = 0
    for _ in range(40):
        if t > AS_OF + timedelta(days=3):
            break
        last = ev[-1]
        if last["waiting_on"] == ext:
            d = reply_delay(rng, ext)
            nudges = 0
            while d is None or d > 24 * (nudges + 1):
                if missed_cadence or nudges >= 3:
                    d = None
                    break
                nudges += 1
                ev.append({"t": last["t"] + timedelta(hours=24 * nudges), "by": "agent", "kind": "followup", "waiting_on": ext})
                if d is None and rng.random() < 0.35:
                    d = 24 * nudges + rng.uniform(0.2, 6)
            if d is None:
                if nudges >= 3 and rng.random() < 0.75:
                    # The owner gives up on the thread and closes it a few days later.
                    ev.append({"t": ev[-1]["t"] + timedelta(hours=rng.uniform(24, 96)), "by": "internal",
                               "kind": "cancel", "waiting_on": None})
                break
            t = last["t"] + timedelta(hours=d)
            roll = rng.random()
            if roll < 0.55:
                ev.append({"t": t, "by": ext, "kind": "reply", "waiting_on": "agent"})
                t += timedelta(minutes=rng.uniform(1, 5))
                ev.append({"t": t, "by": "agent", "kind": "confirm", "waiting_on": None})
            elif roll < 0.85:
                ev.append({"t": t, "by": ext, "kind": "reply", "waiting_on": "agent"})
                t += timedelta(minutes=rng.uniform(1, 5))
                ev.append({"t": t, "by": "agent", "kind": "propose", "waiting_on": ext})
            else:
                ev.append({"t": t, "by": ext, "kind": "reply", "waiting_on": "internal"})
                t += timedelta(hours=rng.choice([0.5, 1, 2, 4, 6, 30, 40]))
                ev.append({"t": t, "by": "internal", "kind": "reply", "waiting_on": "agent"})
                t += timedelta(minutes=rng.uniform(1, 5))
                ev.append({"t": t, "by": "agent", "kind": "propose", "waiting_on": ext})
        elif last["kind"] == "confirm":
            p_move = 0.18 if moves == 0 else 0.30
            if ext == "client" or rng.random() < 0.5:
                mover = "client"
            else:
                mover = "candidate"
            if rng.random() < p_move:
                moves += 1
                t = last["t"] + timedelta(hours=rng.uniform(4, 60))
                ev.append({"t": t, "by": mover, "kind": "reschedule", "waiting_on": "agent"})
                t += timedelta(minutes=rng.uniform(1, 5))
                ev.append({"t": t, "by": "agent", "kind": "propose", "waiting_on": ext})
            elif rng.random() < 0.04:
                ev.append({"t": last["t"] + timedelta(hours=rng.uniform(4, 48)), "by": ext, "kind": "cancel", "waiting_on": None})
                break
            else:
                break
        else:
            break
    ev = [dict(e, t=iso(e["t"])) for e in ev if e["t"] <= AS_OF]
    return {"id": tid, "search_id": f"S-{rng.randint(101, 140)}", "practice": practice, "owner": owner,
            "meeting": meeting, "events": ev}


def scenario_threads(names):
    """A few hand-written threads near the report date so every flag type appears in the demo."""
    def h(hours):
        return iso(AS_OF - timedelta(hours=hours))

    return [
        {"id": "T-9001", "search_id": "S-120", "practice": "Consumer", "owner": names[1], "meeting": "client_panel",
         "events": [{"t": h(52), "by": "internal", "kind": "request", "waiting_on": "agent"},
                    {"t": h(51.9), "by": "agent", "kind": "propose", "waiting_on": "client"},
                    {"t": h(31), "by": "client", "kind": "reply", "waiting_on": "internal"}]},
        {"id": "T-9002", "search_id": "S-131", "practice": "Enterprise", "owner": names[10], "meeting": "candidate_interview",
         "events": [{"t": h(40), "by": "internal", "kind": "request", "waiting_on": "agent"},
                    {"t": h(39.9), "by": "agent", "kind": "propose", "waiting_on": "candidate"}]},
        {"id": "T-9003", "search_id": "S-108", "practice": "Consumer", "owner": names[3], "meeting": "client_panel",
         "events": [{"t": h(150), "by": "internal", "kind": "request", "waiting_on": "agent"}]
                   + [{"t": h(149 - 9 * k), "by": ("agent" if k % 2 == 0 else "client"),
                       "kind": ("propose" if k % 2 == 0 else "reply"),
                       "waiting_on": ("client" if k % 2 == 0 else "agent")} for k in range(15)]},
        {"id": "T-9004", "search_id": "S-115", "practice": "Enterprise", "owner": names[12], "meeting": "candidate_interview",
         "events": [{"t": h(120), "by": "internal", "kind": "request", "waiting_on": "agent"},
                    {"t": h(119.9), "by": "agent", "kind": "propose", "waiting_on": "candidate"},
                    {"t": h(118), "by": "candidate", "kind": "reply", "waiting_on": "agent"},
                    {"t": h(117.9), "by": "agent", "kind": "confirm", "waiting_on": None},
                    {"t": h(80), "by": "client", "kind": "reschedule", "waiting_on": "agent"},
                    {"t": h(79.9), "by": "agent", "kind": "propose", "waiting_on": "candidate"},
                    {"t": h(79), "by": "candidate", "kind": "reply", "waiting_on": "agent"},
                    {"t": h(78.9), "by": "agent", "kind": "confirm", "waiting_on": None},
                    {"t": h(20), "by": "client", "kind": "reschedule", "waiting_on": "agent"},
                    {"t": h(19.9), "by": "agent", "kind": "propose", "waiting_on": "candidate"}]},
    ]


def main():
    rng = random.Random(SEED)
    names = rng.sample([f"{first} {last}" for first in FIRST for last in LAST], 18)
    users, threads, n = [], [], 0
    i = 0
    for practice, (seats, live, rate) in PRACTICES.items():
        for k in range(seats):
            name = names[i]
            i += 1
            users.append({"name": name, "practice": practice, "live_from": iso(live)})
            # Two seats never start, one goes quiet after its first week.
            if (practice, k) in {("Consumer", 7), ("Enterprise", 9)}:
                continue
            stop = live + timedelta(days=8) if (practice, k) == ("Consumer", 6) else AS_OF
            t = live
            while True:
                t += timedelta(hours=rng.expovariate(rate / (5 * 10)))   # working hours only, roughly
                if t > stop:
                    break
                if t.weekday() >= 5 or not (14 <= t.hour <= 23):
                    continue
                n += 1
                threads.append(simulate(rng, f"T-{n:04d}", name, practice, t))
    threads += scenario_threads(names)
    OUT.mkdir(exist_ok=True)
    (OUT / "threads.jsonl").write_text("".join(json.dumps(t) + "\n" for t in threads))
    (OUT / "users.json").write_text(json.dumps({"users": users}, indent=1) + "\n")
    print(f"{len(users)} seats, {len(threads)} threads -> {OUT}")


if __name__ == "__main__":
    main()
