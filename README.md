# interview-stall-monitor

[![CI](https://github.com/pg2342-hub/interview-stall-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/pg2342-hub/interview-stall-monitor/actions/workflows/ci.yml)

Demo page: https://pg2342-hub.github.io/interview-stall-monitor/ (a sample weekly report and the go-live gate results, no install needed)

When an AI agent schedules interviews for a search firm, most threads book themselves. The job of the person who owns the account is the rest: knowing which searches are quietly stalling, who on the customer's team has stopped using the agent, and how much time the firm actually got back this week.

`stallmon` reads the scheduling threads for one account and writes that weekly report:

- **Needs a person**: every open thread that is stalled or at risk, with the reason and a next step someone can act on today
- **Adoption**: active users per practice, seats that never started, people who went quiet
- **Value**: meetings booked, reschedules handled, hours of coordination handed back, time from request to booked
- **Trend**: the same numbers for the last four weeks

## Run it

```
pip install -e .
python -m stallmon report data/threads.jsonl data/users.json --as-of 2026-11-20T17:00:00Z --out reports
```

It writes `report.md` (for an email or a check-in doc), `report.html`, `report.json` and `stalls.csv`. Python 3.10+, no dependencies.

The sample in `data/` is a made-up search firm: 18 seats in two practices (one live from week one, the second from week three) and 168 synthetic threads. `scripts/make_sample.py` regenerates it. The reply-time mix is loosely shaped like a public executive-search scheduling benchmark, and a few hand-written threads make sure every flag type shows up. None of it is real customer data.

## How a thread gets flagged

| Flag | Rule | Constant in `stallmon/rules.py` |
|---|---|---|
| Stalled | Someone outside the firm has not answered 2 follow-ups in 48 hours | `NO_REPLY_HOURS`, `NO_REPLY_FOLLOWUPS` |
| Stalled | Waiting on the firm's own partner or recruiter for 24 hours | `INTERNAL_WAIT_HOURS` |
| Stalled | Waiting on someone outside the firm and nothing sent to them for 30 hours (a missed 24-hour follow-up cadence, so a product issue to reproduce) | `MISSED_CADENCE_HOURS` |
| Stalled | The scheduling agent itself has not acted on its turn for an hour | `AGENT_IDLE_HOURS` |
| At risk | More than 12 rounds and still open | `LONG_THREAD_ROUNDS` |
| At risk | The client has moved the meeting twice | `CLIENT_MOVES` |
| At risk | Waiting 24 hours on someone outside the firm | `SLOW_REPLY_HOURS` |

Booked and cancelled threads are never flagged. The wait clock starts when the turn passed to that person, not at the last nudge.

Hours handed back counts 15 minutes per booked meeting and 15 per reschedule handled. That is the default of a public time-saved calculator, and the first thing to replace with the customer's own number.

## Input format

One JSON object per line:

```json
{"id": "T-0001", "search_id": "S-120", "practice": "Consumer", "owner": "Avery Ellis", "meeting": "candidate_interview",
 "events": [
   {"t": "2026-11-18T15:00:00Z", "by": "internal", "kind": "request", "waiting_on": "agent"},
   {"t": "2026-11-18T15:02:00Z", "by": "agent", "kind": "propose", "waiting_on": "candidate"},
   {"t": "2026-11-19T15:02:00Z", "by": "agent", "kind": "followup", "waiting_on": "candidate"}]}
```

`by` is one of `agent` (the scheduling agent), `internal`, `client`, `candidate`. `kind` is one of `request`, `propose`, `reply`, `followup`, `reschedule`, `confirm`, `cancel`. `waiting_on` is who must act next, or null once settled. Seats live in `users.json` as `{name, practice, live_from}`.

## Tests and the go-live gate

```
pytest -q                                          # 21 unit tests
cd evals && PYTHONPATH=.. golive run golive.yml    # 28 labeled threads
```

The rules are graded against 28 hand-labeled threads (11 stalled, 8 at risk, 9 that need nothing) with [golive-gate](https://github.com/pg2342-hub/golive-gate). The gate in `evals/gate.yml`:

- every stalled thread caught (a miss is a critical failure and blocks go-live)
- at most 1 false alarm among the 9 threads that need nothing
- 7 of 8 at-risk threads (a miss holds at partial)
- 27 of 28 overall

CI runs ruff, the tests on Python 3.10 and 3.12, the sample report, and the gate on every push. It also checks that the gate blocks a monitor that never flags anything. Current result: GO, 28 of 28.

## License

MIT
