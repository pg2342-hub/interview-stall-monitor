"""Write docs/index.html: the sample weekly report, laid out as the demo page.

The report data comes from stallmon; the layout lives in scripts/page_template.html.
Run scripts/demo_chrome.py afterwards (build_demo.sh does) to add the portfolio header and footer.
"""

import json
from pathlib import Path

from stallmon import build_report, load_threads, load_users
from stallmon.model import parse_time
from stallmon.render import MEETING_LABEL, REASON_LABEL, _d, headline, to_markdown

ROOT = Path(__file__).resolve().parent.parent
AS_OF = "2026-11-20T17:00:00Z"


def payload(r: dict) -> dict:
    trend = [{"end": t["end"].date().isoformat(), "label": t["end"].strftime("%b %-d"),
              **{k: t[k] for k in ("threads_started", "booked", "hours_returned", "active_users", "live_seats")}}
             for t in r["trend"]]
    flagged = [{**f, "reason_label": REASON_LABEL.get(f["reason"], f["reason"]),
                "meeting_label": MEETING_LABEL.get(f["meeting"], f["meeting"])} for f in r["flagged"]]
    split = sorted(r["waiting_split"].items(), key=lambda kv: -kv[1])
    return {
        "account": r["account"], "week_ending": _d(r["as_of"]), "headline": headline(r),
        "week": {k: v for k, v in r["week"].items() if k not in ("start", "end")},
        "trend": trend, "flagged": flagged, "stalled": r["stalled"], "at_risk": r["at_risk"],
        "open_threads": r["open_threads"], "waiting_split": [[k, int(v * 100)] for k, v in split],
        "practices": r["practices"], "people": r["people"], "assumptions": r["assumptions"],
        "reasons": REASON_LABEL, "as_of": AS_OF,
    }


def main():
    r = build_report(load_threads(ROOT / "data/threads.jsonl"), load_users(ROOT / "data/users.json"), parse_time(AS_OF))
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    template = (ROOT / "scripts" / "page_template.html").read_text()
    (docs / "index.html").write_text(template.replace("/*DATA*/null", json.dumps(payload(r))))
    (docs / "sample_report.md").write_text(to_markdown(r))
    (docs / ".nojekyll").write_text("")
    print("docs/index.html written")


if __name__ == "__main__":
    main()
