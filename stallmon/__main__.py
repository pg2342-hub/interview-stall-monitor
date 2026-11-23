"""CLI: python -m stallmon report THREADS USERS --as-of ISO [--out DIR] [--account NAME]"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .model import load_threads, load_users, parse_time
from .render import to_html, to_markdown
from .report import build_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="stallmon")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("report", help="write the weekly report")
    rp.add_argument("threads")
    rp.add_argument("users")
    rp.add_argument("--as-of", required=True)
    rp.add_argument("--out", default="reports")
    rp.add_argument("--account", default="Example Search Partners")
    a = ap.parse_args(argv)

    report = build_report(load_threads(a.threads), load_users(a.users), parse_time(a.as_of), account=a.account)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(to_markdown(report))
    (out / "report.html").write_text(to_html(report))
    (out / "report.json").write_text(json.dumps(report, default=str, indent=2))
    with open(out / "stalls.csv", "w", newline="") as fh:
        cols = ["flag", "thread", "practice", "owner", "reason", "waiting_on", "waiting_hours", "rounds", "next_step"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(report["flagged"])
    print(f"{report['account']}: {report['week']['booked']} booked, {report['week']['hours_returned']}h handed back, "
          f"{report['stalled']} stalled, {report['at_risk']} at risk -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
