"""Write evals/cases.yml from the hand-labeled cases below.

Each event is (hours before the check time, sender, kind, who must act next).
The expected flag and reason on every case were written by hand, before the rules
were run, from what a CS lead would want surfaced.
"""
from pathlib import Path

import yaml

AS_OF = "2026-11-20T17:00:00Z"
V, IN, CL, CA = "agent", "internal", "client", "candidate"


def ping_pong(n, start, step, ext):
    """n back-and-forth messages between the agent and the external party, oldest first."""
    out = []
    for k in range(n):
        h = start - step * k
        out.append((h, V, "propose", ext) if k % 2 == 0 else (h, ext, "reply", V))
    return out


CASES = [
    # --- stalled: a person must step in now ---
    ("s01", "stalled", "no_reply", "Candidate silent after two nudges",
     [(60, IN, "request", V), (59.9, V, "propose", CA), (35.9, V, "followup", CA), (11.9, V, "followup", CA)]),
    ("s02", "stalled", "no_reply", "Client silent after three nudges",
     [(100, IN, "request", V), (99.9, V, "propose", CL), (75.9, V, "followup", CL), (51.9, V, "followup", CL), (27.9, V, "followup", CL)]),
    ("s03", "stalled", "internal_wait", "Client answered, partner has not confirmed for a day",
     [(40, IN, "request", V), (39.9, V, "propose", CL), (26, CL, "reply", IN)]),
    ("s04", "stalled", "internal_wait", "Reschedule needs the partner, three days waiting",
     [(200, IN, "request", V), (199.9, V, "propose", CA), (199, CA, "reply", V), (198.9, V, "confirm", None),
      (72, CA, "reschedule", V), (71.9, V, "propose", CA), (70, CA, "reply", IN)]),
    ("s05", "stalled", "missed_followup", "Candidate waiting 31h and no nudge went out",
     [(32, IN, "request", V), (31, V, "propose", CA)]),
    ("s06", "stalled", "missed_followup", "Client waiting 50h and no nudge went out",
     [(51, IN, "request", V), (50, V, "propose", CL)]),
    ("s07", "stalled", "no_reply", "Just past the 48h line with two nudges",
     [(48.6, IN, "request", V), (48.5, V, "propose", CA), (24.5, V, "followup", CA), (0.5, V, "followup", CA)]),
    ("s08", "stalled", "no_reply", "Booked, candidate moved it, then went silent",
     [(150, IN, "request", V), (149.9, V, "propose", CA), (149, CA, "reply", V), (148.9, V, "confirm", None),
      (56, CA, "reschedule", V), (55.9, V, "propose", CA), (31.9, V, "followup", CA), (7.9, V, "followup", CA)]),
    # --- at risk: watch, no action yet ---
    ("r01", "at_risk", "slow_reply", "Candidate quiet 30h, one nudge out",
     [(31, IN, "request", V), (30, V, "propose", CA), (6, V, "followup", CA)]),
    ("r02", "at_risk", "slow_reply", "Two nudges but still under 48h",
     [(47.5, IN, "request", V), (47, V, "propose", CA), (23, V, "followup", CA), (0.2, V, "followup", CA)]),
    ("s11", "stalled", "missed_followup", "One nudge, then 36h of silence from the agent",
     [(61, IN, "request", V), (60, V, "propose", CL), (36, V, "followup", CL)]),
    ("s09", "stalled", "agent_idle", "Request came in 3h ago and the agent never picked it up",
     [(3, IN, "request", V)]),
    ("s10", "stalled", "agent_idle", "Candidate replied 5h ago and the agent has not answered",
     [(30, IN, "request", V), (29.9, V, "propose", CA), (5, CA, "reply", V)]),
    ("r09", "at_risk", "slow_reply", "Candidate quiet 40h, nudged 16h ago",
     [(41, IN, "request", V), (40, V, "propose", CA), (16, V, "followup", CA)]),
    ("r04", "at_risk", "long_thread", "Thirteen rounds and still open",
     [(80, IN, "request", V)] + ping_pong(13, 79, 6, CL)),
    ("r05", "at_risk", "client_moving", "Client moved the interview twice",
     [(130, IN, "request", V), (129.9, V, "propose", CA), (129, CA, "reply", V), (128.9, V, "confirm", None),
      (90, CL, "reschedule", V), (89.9, V, "propose", CA), (89, CA, "reply", V), (88.9, V, "confirm", None),
      (3.1, CL, "reschedule", V), (3, V, "propose", CA)]),
    ("r06", "at_risk", "client_moving", "Client moved it three times",
     [(200, IN, "request", V), (199.9, V, "propose", CA), (199, CA, "reply", V), (198.9, V, "confirm", None),
      (150, CL, "reschedule", V), (149.9, V, "propose", CA), (149, CA, "reply", V), (148.9, V, "confirm", None),
      (100, CL, "reschedule", V), (99.9, V, "propose", CA), (99, CA, "reply", V), (98.9, V, "confirm", None),
      (5.1, CL, "reschedule", V), (5, V, "propose", CA)]),
    ("r07", "at_risk", "long_thread", "Twenty-one rounds of panel juggling",
     [(110, IN, "request", V)] + ping_pong(21, 109, 5, CL)),
    ("r08", "at_risk", "slow_reply", "Client quiet 25h, one nudge",
     [(26, IN, "request", V), (25, V, "propose", CL), (1, V, "followup", CL)]),
    # --- ok: nothing to do ---
    ("o01", "ok", "none", "Booked in one exchange",
     [(10, IN, "request", V), (9.9, V, "propose", CA), (9, CA, "reply", V), (8.9, V, "confirm", None)]),
    ("o02", "ok", "none", "Booked after fourteen rounds (closed, so no flag)",
     [(90, IN, "request", V)] + ping_pong(14, 89, 5, CL) + [(18.9, V, "confirm", None)]),
    ("o03", "ok", "none", "Client cancelled the meeting",
     [(50, IN, "request", V), (49.9, V, "propose", CL), (40, CL, "cancel", None)]),
    ("o04", "ok", "none", "Fresh proposal, candidate has had 3h",
     [(3.1, IN, "request", V), (3, V, "propose", CA)]),
    ("o05", "ok", "none", "Candidate has had 23h, no nudge due yet",
     [(23.1, IN, "request", V), (23, V, "propose", CA)]),
    ("o06", "ok", "none", "Partner has had the client's reply for 10h",
     [(20, IN, "request", V), (19.9, V, "propose", CL), (10, CL, "reply", IN)]),
    ("o07", "ok", "none", "Candidate moved it once, new times out 2h",
     [(60, IN, "request", V), (59.9, V, "propose", CA), (59, CA, "reply", V), (58.9, V, "confirm", None),
      (2.1, CA, "reschedule", V), (2, V, "propose", CA)]),
    ("o08", "ok", "none", "Reply just came in, the agent's turn",
     [(5, IN, "request", V), (4.9, V, "propose", CA), (0.1, CA, "reply", V)]),
    ("o09", "ok", "none", "Ghosted, then the owner closed it",
     [(150, IN, "request", V), (149.9, V, "propose", CA), (125.9, V, "followup", CA), (101.9, V, "followup", CA),
      (77.9, V, "followup", CA), (30, IN, "cancel", None)]),
]


def main():
    cases = []
    for cid, flag, reason, title, events in CASES:
        cases.append({
            "id": cid, "group": flag, "title": title,
            "input": {"as_of": AS_OF, "owner": "Owner", "events": [
                {"h_ago": h, "by": by, "kind": kind, "waiting_on": w} for h, by, kind, w in events]},
            "expected": {"flag": flag, "reason": reason},
        })
    out = Path(__file__).with_name("cases.yml")
    out.write_text("# Generated by build_cases.py from hand-labeled cases. Edit there, not here.\n"
                   + yaml.safe_dump({"cases": cases}, sort_keys=False, width=200))
    print(f"{len(cases)} cases -> {out}")


if __name__ == "__main__":
    main()
