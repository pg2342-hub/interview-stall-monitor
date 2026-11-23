"""Stall rules: which open threads need a person, and what to do next.

Thresholds are plain constants so a CS lead can tune them per customer.
The 12-round line comes from a public Executive Search Scheduling
Benchmark, tryvela.ai/benchmark (cancellations 3.9% when settled in one exchange vs 16.4% past
twelve rounds); the 24-hour line matches a 24-hour follow-up cadence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .model import EXTERNAL, Thread

LONG_THREAD_ROUNDS = 12        # past this, treat as at risk
NO_REPLY_HOURS = 48            # external silence that counts as stalled ...
NO_REPLY_FOLLOWUPS = 2         # ... once this many nudges went unanswered
SLOW_REPLY_HOURS = 24          # external silence worth watching
MISSED_CADENCE_HOURS = 30      # waiting on someone outside and nothing sent for this long (24h cadence missed)
AGENT_IDLE_HOURS = 1           # the agent itself has not acted on its turn
INTERNAL_WAIT_HOURS = 24       # the firm's own person holding the thread
CLIENT_MOVES = 2               # client rescheduled this many times

STALLED, AT_RISK, OK = "stalled", "at_risk", "ok"
RANK = {STALLED: 0, AT_RISK: 1, OK: 2}


@dataclass
class Flag:
    flag: str
    reasons: List[str] = field(default_factory=list)
    next_step: str = ""
    waiting_on: str = ""
    waiting_hours: float = 0.0

    @property
    def reason(self) -> str:
        return self.reasons[0] if self.reasons else "none"

    def as_dict(self) -> dict:
        return {"flag": self.flag, "reason": self.reason, "reasons": self.reasons,
                "next_step": self.next_step, "waiting_on": self.waiting_on,
                "waiting_hours": round(self.waiting_hours, 1)}


def _hours(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600


def classify(thread: Thread, as_of: datetime) -> Flag:
    """Flag one thread as of a moment. Closed threads (booked or cancelled) are never flagged."""
    if thread.state(as_of) != "open":
        return Flag(OK)

    found = []  # (severity, reason, next step)
    wait = thread.waiting(as_of)
    party, hours = "", 0.0
    if wait:
        party, since, nudges = wait
        hours = _hours(since, as_of)
        who = "client" if party == "client" else party
        if party in EXTERNAL:
            quiet = _hours(thread.last_touch(as_of), as_of)
            if nudges >= NO_REPLY_FOLLOWUPS and hours >= NO_REPLY_HOURS:
                found.append((STALLED, "no_reply",
                              f"{nudges} follow-ups to the {who} are unanswered after {hours:.0f}h. "
                              f"Ask {thread.owner or 'the owner'} to call or text the {who} directly."))
            elif quiet >= MISSED_CADENCE_HOURS:
                found.append((STALLED, "missed_followup",
                              f"Nothing has gone to the {who} in {quiet:.0f}h, so the follow-up cadence was missed. "
                              "Check the thread for a parsing or channel issue, reproduce it, and send engineering the thread id."))
            elif hours >= SLOW_REPLY_HOURS:
                found.append((AT_RISK, "slow_reply",
                              f"Waiting {hours:.0f}h on the {who}. Watch it; the next follow-up is due."))
        elif party == "agent" and hours >= AGENT_IDLE_HOURS:
            found.append((STALLED, "agent_idle",
                          f"The scheduling agent has not acted on this thread in {hours:.0f}h. "
                          "Reproduce it, send engineering the thread id, and tell the owner a person is on it."))
        elif party == "internal" and hours >= INTERNAL_WAIT_HOURS:
            found.append((STALLED, "internal_wait",
                          f"Waiting {hours:.0f}h on {thread.owner or 'someone at the firm'}. "
                          "Nudge them and offer to confirm the slot already proposed."))

    rounds = thread.rounds(as_of)
    if rounds > LONG_THREAD_ROUNDS:
        found.append((AT_RISK, "long_thread",
                      f"{rounds} rounds and still open; cancellations run about 4x higher past 12 in "
                      "a public search-scheduling benchmark. Suggest a quick call to lock a time."))
    moves = thread.client_moves(as_of)
    if moves >= CLIENT_MOVES:
        found.append((AT_RISK, "client_moving",
                      f"The client has moved this {moves} times. Give the candidate two firm backup "
                      "slots so the next move does not restart the thread."))

    if not found:
        return Flag(OK, waiting_on=party, waiting_hours=hours)
    found.sort(key=lambda f: RANK[f[0]])
    return Flag(found[0][0], [r for _, r, _ in found], found[0][2], party, hours)
