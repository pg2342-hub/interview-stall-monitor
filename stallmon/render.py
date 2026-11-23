"""Render a report dict as markdown (for email or a PR) and as one self-contained HTML page."""
from __future__ import annotations

import html
from datetime import datetime

REASON_LABEL = {
    "no_reply": "No reply after follow-ups",
    "missed_followup": "Follow-up cadence missed",
    "agent_idle": "Agent has not acted",
    "internal_wait": "Waiting on the firm",
    "slow_reply": "Slow reply",
    "long_thread": "Long thread",
    "client_moving": "Client keeps moving it",
}
MEETING_LABEL = {"candidate_interview": "Candidate interview", "client_panel": "Client panel", "debrief": "Debrief"}


def _d(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%b %-d, %Y")


def headline(r: dict) -> str:
    w = r["week"]
    return (f"{w['booked']} meetings booked and {w['hours_returned']} hours of coordination handed back this week; "
            f"{r['stalled']} stalled and {r['at_risk']} at-risk threads need a person.")


def to_markdown(r: dict) -> str:
    w = r["week"]
    lines = [f"# Weekly scheduling report: {r['account']}", f"Week ending {_d(r['as_of'])}", "", headline(r), "",
             "## This week", "",
             "| Measure | Value |", "|---|---|",
             f"| Meetings booked | {w['booked']} |",
             f"| Reschedules handled | {w['reschedules']} |",
             f"| Hours handed back | {w['hours_returned']} |",
             f"| Median hours from request to booked | {w['median_hours_to_book']} |",
             f"| Booked within 24 hours | {w['booked_within_24h']} of {w['booked']} |",
             f"| Active users | {w['active_users']} of {w['live_seats']} live seats |",
             f"| Cancelled | {w['cancelled']} |", "",
             "## Needs a person", ""]
    if r["flagged"]:
        lines += ["| Thread | Practice | Owner | Flag | Why | Next step |", "|---|---|---|---|---|---|"]
        for f in r["flagged"]:
            lines.append(f"| {f['thread']} | {f['practice']} | {f['owner']} | {f['flag'].replace('_', ' ')} | "
                         f"{REASON_LABEL.get(f['reason'], f['reason'])} | {f['next_step']} |")
    else:
        lines.append("Nothing stalled.")
    lines += ["", "## Adoption by practice", "", "| Practice | Live seats | Active | Threads this week | Open | Stalled | Health |",
              "|---|---|---|---|---|---|---|"]
    for p in r["practices"]:
        lines.append(f"| {p['practice']} | {p['seats']} | {p['active']} | {p['threads']} | {p['open']} | {p['stalled']} | {p['health']} |")
    quiet = [p for p in r["people"] if p["status"] != "active"]
    lines += ["", "## People to check in with", ""]
    lines += [f"- {p['name']} ({p['practice']}): {p['status']}" + (f", last thread {p['last_thread']}" if p["last_thread"] else "")
              for p in quiet] or ["Everyone with a seat used the agent this week."]
    lines += ["", "## Four-week trend", "", "| Week ending | Threads | Booked | Hours handed back | Active users |", "|---|---|---|---|---|"]
    for t in r["trend"]:
        lines.append(f"| {t['end'].date().isoformat()} | {t['threads_started']} | {t['booked']} | {t['hours_returned']} | {t['active_users']} of {t['live_seats']} |")
    a = r["assumptions"]
    lines += ["", f"Hours handed back counts {a['minutes_per_booking']} minutes per booked meeting and "
              f"{a['minutes_per_reschedule']} per reschedule handled, the default in a public time-saved calculator for search firms. "
              "Replace them with the customer's own numbers after the first week."]
    return "\n".join(lines) + "\n"


CSS = """
:root{--ink:#111;--mute:#666;--line:#ddd;--bg:#fff;--soft:#f5f5f5}
@media (prefers-color-scheme:dark){:root{--ink:#eee;--mute:#999;--line:#333;--bg:#111;--soft:#1b1b1b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,system-ui,-apple-system,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 16px 64px}h1{font-size:26px;margin:0 0 4px}h2{font-size:17px;margin:36px 0 10px}
.sub{color:var(--mute)}.lead{font-size:17px;margin:16px 0 0}.note{color:var(--mute);font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:20px}
.tile{border:1px solid var(--line);border-radius:8px;padding:12px}.tile b{display:block;font-size:24px}.tile span{color:var(--mute);font-size:13px}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--mute);font-size:12px;text-transform:uppercase;letter-spacing:.03em}
.pill{display:inline-block;border:1px solid var(--ink);border-radius:99px;padding:0 8px;font-size:12px;white-space:nowrap}
.stalled{background:var(--ink);color:var(--bg)}.red{background:var(--ink);color:var(--bg)}.green{border-style:dotted}
.bar{height:8px;background:var(--soft);border-radius:4px;overflow:hidden;min-width:80px}.bar i{display:block;height:100%;background:var(--ink)}
a{color:inherit}
"""


def _e(s) -> str:
    return html.escape(str(s))


def to_html(r: dict, title: str = "Weekly scheduling report", banner: str = "", footer: str = "") -> str:
    w = r["week"]
    tiles = [("Meetings booked", w["booked"]), ("Hours handed back", w["hours_returned"]),
             ("Median hours to book", w["median_hours_to_book"]), ("Active users", f"{w['active_users']}/{w['live_seats']}"),
             ("Stalled", r["stalled"]), ("At risk", r["at_risk"])]
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{_e(title)}</title><link rel='preconnect' href='https://fonts.googleapis.com'>"
           "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap' rel='stylesheet'>"
           f"<style>{CSS}</style></head><body><main>", banner,
           f"<h1>Weekly scheduling report: {_e(r['account'])}</h1><div class='sub'>Week ending {_e(_d(r['as_of']))}</div>",
           f"<p class='lead'>{_e(headline(r))}</p><div class='tiles'>"]
    out += [f"<div class='tile'><b>{_e(v)}</b><span>{_e(k)}</span></div>" for k, v in tiles]
    out.append("</div><h2>Needs a person</h2>")
    if r["flagged"]:
        out.append("<div class='wrap'><table><tr><th>Flag</th><th>Thread</th><th>Owner</th><th>Why</th><th>Waiting</th><th>Next step</th></tr>")
        for f in r["flagged"]:
            cls = "pill stalled" if f["flag"] == "stalled" else "pill"
            wait = f"{f['waiting_hours']:.0f}h on {f['waiting_on']}" if f["waiting_on"] else f"{f['rounds']} rounds"
            out.append(f"<tr><td><span class='{cls}'>{_e(f['flag'].replace('_', ' '))}</span></td>"
                       f"<td>{_e(f['thread'])}<br><span class='note'>{_e(MEETING_LABEL.get(f['meeting'], f['meeting']))}, {_e(f['practice'])}</span></td>"
                       f"<td>{_e(f['owner'])}</td><td>{_e(REASON_LABEL.get(f['reason'], f['reason']))}</td>"
                       f"<td>{_e(wait)}</td><td>{_e(f['next_step'])}</td></tr>")
        out.append("</table></div>")
    else:
        out.append("<p>Nothing stalled.</p>")
    if r["waiting_split"]:
        parts = ", ".join(f"{int(v * 100)}% {k}" for k, v in sorted(r["waiting_split"].items(), key=lambda kv: -kv[1]))
        out.append(f"<p class='note'>Of the hours open threads have spent waiting: {_e(parts)}.</p>")
    out.append("<h2>Adoption by practice</h2><div class='wrap'><table><tr><th>Practice</th><th>Active users</th><th></th>"
               "<th>Threads this week</th><th>Open</th><th>Stalled</th><th>Health</th></tr>")
    for p in r["practices"]:
        out.append(f"<tr><td>{_e(p['practice'])}</td><td>{p['active']} of {p['seats']}</td>"
                   f"<td><div class='bar'><i style='width:{int(p['active_share'] * 100)}%'></i></div></td>"
                   f"<td>{p['threads']}</td><td>{p['open']}</td><td>{p['stalled']}</td>"
                   f"<td><span class='pill {p['health']}'>{_e(p['health'])}</span></td></tr>")
    out.append("</table></div><h2>People to check in with</h2>")
    quiet = [p for p in r["people"] if p["status"] != "active"]
    if quiet:
        out.append("<div class='wrap'><table><tr><th>Name</th><th>Practice</th><th>Status</th><th>Live since</th><th>Last thread</th></tr>")
        out += [f"<tr><td>{_e(p['name'])}</td><td>{_e(p['practice'])}</td><td>{_e(p['status'])}</td>"
                f"<td>{_e(p['live_from'])}</td><td>{_e(p['last_thread'] or '-')}</td></tr>" for p in quiet]
        out.append("</table></div>")
    else:
        out.append("<p>Everyone with a seat used the agent this week.</p>")
    out.append("<h2>Four-week trend</h2><div class='wrap'><table><tr><th>Week ending</th><th>Threads</th><th>Booked</th>"
               "<th>Hours handed back</th><th>Active users</th></tr>")
    out += [f"<tr><td>{t['end'].date().isoformat()}</td><td>{t['threads_started']}</td><td>{t['booked']}</td>"
            f"<td>{t['hours_returned']}</td><td>{t['active_users']} of {t['live_seats']}</td></tr>" for t in r["trend"]]
    a = r["assumptions"]
    out.append(f"</table></div><p class='note'>Hours handed back counts {a['minutes_per_booking']} minutes per booked meeting and "
               f"{a['minutes_per_reschedule']} per reschedule handled, the default in a public time-saved calculator for search firms. "
               "Swap in the customer's own numbers after week one.</p>")
    out += [footer, "</main></body></html>"]
    return "".join(out)
