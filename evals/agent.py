"""Adapter: run the stall rules on one eval case."""
from datetime import timedelta

from stallmon import Thread, classify
from stallmon.model import parse_time


def monitor(case_input):
    as_of = parse_time(case_input["as_of"])
    events = [{"t": (as_of - timedelta(hours=e["h_ago"])).isoformat(), "by": e["by"], "kind": e["kind"],
               "waiting_on": e.get("waiting_on")} for e in case_input["events"]]
    th = Thread.from_dict({"id": "case", "owner": case_input.get("owner", ""), "events": events})
    return classify(th, as_of).as_dict()


def flag_everything(case_input):
    """A deliberately bad monitor for the CI self-test: it raises every open thread."""
    out = monitor(case_input)
    return dict(out, flag="stalled", reason="no_reply")


def flag_nothing(case_input):
    """The other bad monitor: it never raises anything."""
    return {"flag": "ok", "reason": "none", "reasons": [], "next_step": "", "waiting_on": "", "waiting_hours": 0}
