"""Thread and event model for scheduling conversations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

PARTIES = ("agent", "internal", "client", "candidate")
KINDS = ("request", "propose", "reply", "followup", "reschedule", "confirm", "cancel")
EXTERNAL = ("client", "candidate")


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class Event:
    t: datetime
    by: str            # who sent it: agent, internal, client, candidate
    kind: str          # request, propose, reply, followup, reschedule, confirm, cancel
    waiting_on: Optional[str] = None  # who must act next after this message (None once settled)

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        if d["by"] not in PARTIES:
            raise ValueError(f"unknown party {d['by']!r}")
        if d["kind"] not in KINDS:
            raise ValueError(f"unknown event kind {d['kind']!r}")
        return cls(parse_time(d["t"]), d["by"], d["kind"], d.get("waiting_on"))


@dataclass
class Thread:
    id: str
    search_id: str
    practice: str
    owner: str
    meeting: str                 # candidate_interview, client_panel, debrief
    events: List[Event] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Thread":
        events = sorted((Event.from_dict(e) for e in d["events"]), key=lambda e: e.t)
        if not events or events[0].kind != "request":
            raise ValueError(f"thread {d.get('id')} must start with a request")
        return cls(d["id"], d.get("search_id", d["id"]), d.get("practice", ""), d.get("owner", ""),
                   d.get("meeting", "candidate_interview"), events)

    def upto(self, as_of: datetime) -> List[Event]:
        return [e for e in self.events if e.t <= as_of]

    def started(self) -> datetime:
        return self.events[0].t

    def state(self, as_of: datetime) -> str:
        """open, booked or cancelled as of a moment."""
        state = "open"
        for e in self.upto(as_of):
            if e.kind == "confirm":
                state = "booked"
            elif e.kind == "reschedule":
                state = "open"
            elif e.kind == "cancel":
                state = "cancelled"
        return state

    def rounds(self, as_of: datetime) -> int:
        """Back-and-forth messages after the request, not counting follow-up nudges or the final confirm."""
        return sum(1 for e in self.upto(as_of)[1:] if e.kind in ("propose", "reply", "reschedule"))

    def client_moves(self, as_of: datetime) -> int:
        return sum(1 for e in self.upto(as_of) if e.kind == "reschedule" and e.by == "client")

    def reschedules(self, as_of: datetime) -> int:
        return sum(1 for e in self.upto(as_of) if e.kind == "reschedule")

    def waiting(self, as_of: datetime):
        """(party, since, unanswered_followups) for an open thread, or None.

        The wait starts at the last message that handed the turn to that party;
        the agent's follow-ups while waiting do not restart the clock.
        """
        evs = self.upto(as_of)
        if not evs or self.state(as_of) != "open":
            return None
        party = evs[-1].waiting_on
        if party is None:
            return None
        since, nudges = evs[-1].t, 0
        for e in reversed(evs):
            if e.kind == "followup" and e.waiting_on == party:
                nudges += 1
                since = e.t
                continue
            since = e.t
            break
        return party, since, nudges

    def last_touch(self, as_of: datetime) -> Optional[datetime]:
        """Time of the most recent message of any kind, including follow-ups."""
        evs = self.upto(as_of)
        return evs[-1].t if evs else None


def _read(path: Path) -> Iterable[dict]:
    text = Path(path).read_text()
    if str(path).endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    return data["threads"] if isinstance(data, dict) else data


def load_threads(path) -> List[Thread]:
    return [Thread.from_dict(d) for d in _read(Path(path))]


def load_users(path) -> List[dict]:
    """Seats: [{name, practice, live_from}]"""
    data = json.loads(Path(path).read_text())
    return data["users"] if isinstance(data, dict) else data
