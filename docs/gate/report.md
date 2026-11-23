# Stall monitor go-live gate: GO

Agent `agent:monitor`, 28 cases, 1 run(s).

- every rule held on all 1 run(s), no critical failures

## Pass counts by run

| Run | Passed | Critical failures |
|---|---|---|
| 1 | 28 of 28 | 0 |

Agent cost 0.0000 USD, judge cost 0.0000 USD, mean latency 0.0 ms per case.

## Cases

| Case | Group | Result | Failed checks |
|---|---|---|---|
| Candidate silent after two nudges | stalled | 1 of 1 runs |  |
| Client silent after three nudges | stalled | 1 of 1 runs |  |
| Client answered, partner has not confirmed for a day | stalled | 1 of 1 runs |  |
| Reschedule needs the partner, three days waiting | stalled | 1 of 1 runs |  |
| Candidate waiting 31h and no nudge went out | stalled | 1 of 1 runs |  |
| Client waiting 50h and no nudge went out | stalled | 1 of 1 runs |  |
| Just past the 48h line with two nudges | stalled | 1 of 1 runs |  |
| Booked, candidate moved it, then went silent | stalled | 1 of 1 runs |  |
| Candidate quiet 30h, one nudge out | at_risk | 1 of 1 runs |  |
| Two nudges but still under 48h | at_risk | 1 of 1 runs |  |
| One nudge, then 36h of silence from the agent | stalled | 1 of 1 runs |  |
| Request came in 3h ago and the agent never picked it up | stalled | 1 of 1 runs |  |
| Candidate replied 5h ago and the agent has not answered | stalled | 1 of 1 runs |  |
| Candidate quiet 40h, nudged 16h ago | at_risk | 1 of 1 runs |  |
| Thirteen rounds and still open | at_risk | 1 of 1 runs |  |
| Client moved the interview twice | at_risk | 1 of 1 runs |  |
| Client moved it three times | at_risk | 1 of 1 runs |  |
| Twenty-one rounds of panel juggling | at_risk | 1 of 1 runs |  |
| Client quiet 25h, one nudge | at_risk | 1 of 1 runs |  |
| Booked in one exchange | ok | 1 of 1 runs |  |
| Booked after fourteen rounds (closed, so no flag) | ok | 1 of 1 runs |  |
| Client cancelled the meeting | ok | 1 of 1 runs |  |
| Fresh proposal, candidate has had 3h | ok | 1 of 1 runs |  |
| Candidate has had 23h, no nudge due yet | ok | 1 of 1 runs |  |
| Partner has had the client's reply for 10h | ok | 1 of 1 runs |  |
| Candidate moved it once, new times out 2h | ok | 1 of 1 runs |  |
| Reply just came in, the agent's turn | ok | 1 of 1 runs |  |
| Ghosted, then the owner closed it | ok | 1 of 1 runs |  |

## Checks

| Check | Critical | Text |
|---|---|---|
| flag |  | The monitor gives the expected flag (stalled, at risk or ok). |
| reason |  | For a flagged thread, the main reason is the expected one. |
| catches_stalled | yes | Every stalled thread is flagged as stalled. |
| next_step |  | Every flagged thread comes with a next step a person can act on. |
| no_false_alarm |  | A thread that needs nothing is not raised. |
