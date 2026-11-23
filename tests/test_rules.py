from datetime import datetime, timedelta, timezone

import pytest

from stallmon import Thread, classify
from stallmon.rules import AT_RISK, OK, STALLED

AS_OF = datetime(2026, 11, 20, 17, 0, tzinfo=timezone.utc)


def thread(*events, owner="Avery Ellis"):
    return Thread.from_dict({"id": "t", "owner": owner, "events": [
        {"t": (AS_OF - timedelta(hours=h)).isoformat(), "by": by, "kind": kind, "waiting_on": w}
        for h, by, kind, w in events]})


def test_booked_thread_is_never_flagged_even_after_many_rounds():
    evs = [(100, "internal", "request", "agent")]
    evs += [(99 - k, "agent" if k % 2 == 0 else "client", "propose" if k % 2 == 0 else "reply",
             "client" if k % 2 == 0 else "agent") for k in range(20)]
    evs += [(50, "agent", "confirm", None)]
    assert classify(thread(*evs), AS_OF).flag == OK


def test_wait_clock_starts_at_the_handoff_not_the_last_nudge():
    t = thread((60, "internal", "request", "agent"), (59, "agent", "propose", "candidate"),
               (35, "agent", "followup", "candidate"), (11, "agent", "followup", "candidate"))
    party, since, nudges = t.waiting(AS_OF)
    assert (party, nudges) == ("candidate", 2)
    assert since == AS_OF - timedelta(hours=59)


@pytest.mark.parametrize("hours,nudges,expected", [
    (49, 2, STALLED),   # past 48h with two nudges
    (47, 2, AT_RISK),   # under the line
    (40, 1, AT_RISK),   # one nudge 16h ago: watch, do not escalate
    (60, 1, STALLED),   # one nudge 36h ago and nothing since: the cadence was missed
])
def test_no_reply_line(hours, nudges, expected):
    evs = [(hours + 0.1, "internal", "request", "agent"), (hours, "agent", "propose", "candidate")]
    evs += [(hours - 24 * (k + 1), "agent", "followup", "candidate") for k in range(nudges)]
    assert classify(thread(*evs), AS_OF).flag == expected


def test_missing_followup_is_flagged_for_engineering():
    f = classify(thread((32, "internal", "request", "agent"), (31, "agent", "propose", "candidate")), AS_OF)
    assert (f.flag, f.reason) == (STALLED, "missed_followup")
    assert "engineering" in f.next_step


def test_silence_after_one_nudge_is_a_missed_cadence():
    f = classify(thread((61, "internal", "request", "agent"), (60, "agent", "propose", "client"),
                        (36, "agent", "followup", "client")), AS_OF)
    assert (f.flag, f.reason) == (STALLED, "missed_followup")


def test_agent_that_never_acts_is_flagged():
    f = classify(thread((3, "internal", "request", "agent")), AS_OF)
    assert (f.flag, f.reason) == (STALLED, "agent_idle")


def test_internal_wait_names_the_owner():
    f = classify(thread((40, "internal", "request", "agent"), (39, "agent", "propose", "client"),
                        (25, "client", "reply", "internal"), owner="Quinn Shaw"), AS_OF)
    assert (f.flag, f.reason) == (STALLED, "internal_wait")
    assert "Quinn Shaw" in f.next_step


def test_candidate_reschedules_do_not_count_as_client_moves():
    t = thread((100, "internal", "request", "agent"), (99, "agent", "propose", "candidate"),
               (98, "candidate", "reply", "agent"), (97.9, "agent", "confirm", None),
               (50, "candidate", "reschedule", "agent"), (49.9, "agent", "propose", "candidate"),
               (49, "candidate", "reply", "agent"), (48.9, "agent", "confirm", None),
               (3, "candidate", "reschedule", "agent"), (2.9, "agent", "propose", "candidate"))
    assert t.client_moves(AS_OF) == 0
    assert classify(t, AS_OF).flag == OK


def test_stalled_outranks_at_risk_and_keeps_both_reasons():
    evs = [(200, "internal", "request", "agent")]
    evs += [(199 - k, "agent" if k % 2 == 0 else "client", "propose" if k % 2 == 0 else "reply",
             "client" if k % 2 == 0 else "agent") for k in range(15)]
    evs += [(150, "agent", "followup", "client"), (126, "agent", "followup", "client")]
    f = classify(thread(*evs), AS_OF)
    assert f.flag == STALLED
    assert f.reasons[:2] == ["no_reply", "long_thread"]


def test_events_after_the_report_time_are_ignored():
    t = thread((10, "internal", "request", "agent"), (9, "agent", "propose", "candidate"), (-5, "candidate", "reply", "agent"))
    assert t.waiting(AS_OF)[0] == "candidate"


def test_bad_input_is_rejected():
    with pytest.raises(ValueError):
        thread((5, "agent", "propose", "candidate"))  # no request first
    with pytest.raises(ValueError):
        thread((5, "internal", "request", "agent"), (4, "robot", "propose", "candidate"))
