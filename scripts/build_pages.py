"""Write docs/index.html: the sample weekly report with a short explainer around it."""
import re
from pathlib import Path

from stallmon import build_report, load_threads, load_users
from stallmon.model import parse_time
from stallmon.render import to_html, to_markdown

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/pg2342-hub/interview-stall-monitor"

# The demo page swaps the report's own stylesheet for one on top of the portfolio's demo kit (scripts/demo_chrome.py).
DEMO_CSS = """
main{padding-bottom:24px}
h1{margin-top:40px}
.sub{font:400 13px/1.4 var(--mono);letter-spacing:.02em;color:var(--ink-2)}
.lead{font-size:18px;color:var(--ink);max-width:42em;margin:16px 0 0}
.note{color:var(--ink-2);font-size:14px;max-width:46em}
.demo-note{background:var(--tint-2);border-radius:12px;padding:14px 18px;margin-top:40px;font-size:15px;color:var(--ink-2)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-top:32px}
.tile{border:1px solid var(--rule);border-radius:16px;padding:16px 18px}
.tile b{display:block;font:400 32px/1.15 var(--serif);font-weight:400;font-variant-numeric:tabular-nums}
.tile span{color:var(--ink-2);font-size:14px}
.wrap{overflow-x:auto;margin:16px 0}
td .pill{display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;border:1px solid var(--ink);
font:500 12px/1 var(--mono);letter-spacing:.03em}
td .pill.stalled,td .pill.red{background:var(--ink);color:var(--paper)}
td .pill.green{background:var(--green-wash);border-color:var(--green-wash);color:var(--green)}
td .pill.yellow{border-style:dashed}
.bar{height:10px;background:var(--tint-1);border-radius:999px;overflow:hidden;min-width:80px;margin-top:6px}
.bar i{display:block;height:100%;background:var(--green);border-radius:999px}
"""


def demo_page(page: str) -> str:
    page = re.sub(r"<style>.*?</style>", lambda m: f"<style>{DEMO_CSS}</style>", page, count=1, flags=re.S)
    return re.sub(r"<link[^>]+fonts\.(googleapis|gstatic)[^>]*>", "", page)


BANNER = f"""
<p class='note demo-note'>
<b>Demo.</b> This is the weekly report <code>stallmon</code> writes for one customer account, run on a made-up
search firm (18 seats in two practices, 168 synthetic scheduling threads over four weeks). Nothing here is real
customer data. <a href='gate/index.html'>Go-live gate report (28 labeled threads)</a></p>
"""

FOOTER = """
<h2>How it decides</h2>
<div class='wrap'><table>
<tr><th>Flag</th><th>Rule</th><th>Why it matters</th></tr>
<tr><td>Stalled</td><td>Someone outside the firm has not answered two follow-ups in 48 hours</td><td>More than half of the waiting in a search is follow-ups nobody answered, so a person should call or text</td></tr>
<tr><td>Stalled</td><td>Waiting on the firm's own partner or recruiter for 24 hours</td><td>Internal waits are the easiest to fix and the most embarrassing to leave</td></tr>
<tr><td>Stalled</td><td>Nothing sent to someone outside the firm for 30 hours while waiting on them</td><td>The 24-hour cadence was missed, which points at a product issue to reproduce and send to engineering</td></tr>
<tr><td>Stalled</td><td>The scheduling agent has not acted on its turn for an hour</td><td>Something is stuck in the product, not with a person</td></tr>
<tr><td>At risk</td><td>More than 12 rounds and still open</td><td>A public search-scheduling benchmark shows cancellations rising from 3.9% to 16.4% past twelve rounds</td></tr>
<tr><td>At risk</td><td>The client has moved the meeting twice</td><td>Each move restarts the negotiation; firm backup slots stop the loop</td></tr>
<tr><td>At risk</td><td>Waiting 24 hours on someone outside the firm</td><td>Worth watching before it becomes a stall</td></tr>
</table></div>
<p class='note'>Every threshold is a constant in <code>stallmon/rules.py</code> so it can be tuned per customer. The rules are
checked in CI against 28 hand-labeled threads with <a href='https://github.com/pg2342-hub/golive-gate'>golive-gate</a>:
every stalled thread must be caught, with at most one false alarm.</p>
<p class='note'>Run it: <code>python -m stallmon report data/threads.jsonl data/users.json --as-of 2026-11-20T17:00:00Z</code></p>
"""


def main():
    r = build_report(load_threads(ROOT / "data/threads.jsonl"), load_users(ROOT / "data/users.json"),
                     parse_time("2026-11-20T17:00:00Z"))
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(demo_page(to_html(r, title="Interview stall monitor", banner=BANNER, footer=FOOTER)))
    (docs / "sample_report.md").write_text(to_markdown(r))
    (docs / ".nojekyll").write_text("")
    print("docs/index.html written")


if __name__ == "__main__":
    main()
