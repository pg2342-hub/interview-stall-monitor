import json
from pathlib import Path

from stallmon import build_report, load_threads, load_users
from stallmon.__main__ import main
from stallmon.model import parse_time
from stallmon.report import MINUTES_PER_BOOKING

ROOT = Path(__file__).resolve().parent.parent
AS_OF = parse_time("2026-11-20T17:00:00Z")


def sample():
    return build_report(load_threads(ROOT / "data/threads.jsonl"), load_users(ROOT / "data/users.json"), AS_OF)


def test_calculator_default_matches_public_calculator():
    # public calculator (tryvela.ai): 30 interviews/week, 15 minutes each, 35% reschedule rate -> 43.5h/month
    weekly_minutes = 30 * MINUTES_PER_BOOKING * (1 + 0.35)
    assert round(weekly_minutes) == 608
    assert round(weekly_minutes / 60 * 4.3, 1) == 43.5


def test_hours_returned_follows_the_stated_assumption():
    w = sample()["week"]
    assert w["hours_returned"] == round((w["booked"] + w["reschedules"]) * 15 / 60, 1)


def test_every_flag_type_appears_in_the_sample():
    reasons = {f["reason"] for f in sample()["flagged"]}
    assert {"no_reply", "missed_followup", "internal_wait", "slow_reply", "long_thread", "client_moving"} <= reasons


def test_flag_list_puts_stalled_first():
    flags = [f["flag"] for f in sample()["flagged"]]
    assert flags == sorted(flags, key=lambda f: 0 if f == "stalled" else 1)


def test_adoption_catches_seats_that_never_started():
    people = sample()["people"]
    assert any(p["status"] == "never started" for p in people)
    assert people[0]["status"] != "active"


def test_seats_not_live_yet_are_left_out():
    r = build_report(load_threads(ROOT / "data/threads.jsonl"), load_users(ROOT / "data/users.json"),
                     parse_time("2026-10-28T17:00:00Z"))
    assert {p["practice"] for p in r["practices"]} == {"Consumer"}


def test_cli_writes_all_outputs(tmp_path):
    assert main(["report", str(ROOT / "data/threads.jsonl"), str(ROOT / "data/users.json"),
                 "--as-of", "2026-11-20T17:00:00Z", "--out", str(tmp_path)]) == 0
    for name in ("report.md", "report.html", "report.json", "stalls.csv"):
        assert (tmp_path / name).stat().st_size > 0
    assert json.loads((tmp_path / "report.json").read_text())["stalled"] >= 1
