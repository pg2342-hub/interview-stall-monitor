from golive_gate import NA, CheckSet


def verdict(ok, reason=""):
    return ("pass" if ok else "fail", reason)

checks = CheckSet()


@checks.check("flag", text="The monitor gives the expected flag (stalled, at risk or ok).")
def flag(case, out):
    return verdict(out["flag"] == case.expected["flag"], f"got {out['flag']}")


@checks.check("reason", text="For a flagged thread, the main reason is the expected one.")
def reason(case, out):
    if case.expected["flag"] == "ok":
        return NA
    return verdict(out["reason"] == case.expected["reason"], f"got {out['reason']}")


@checks.check("catches_stalled", text="Every stalled thread is flagged as stalled.", critical=True)
def catches_stalled(case, out):
    if case.expected["flag"] != "stalled":
        return NA
    return out["flag"] == "stalled"


@checks.check("next_step", text="Every flagged thread comes with a next step a person can act on.")
def next_step(case, out):
    if out["flag"] == "ok":
        return NA
    return len(out.get("next_step", "")) > 20


@checks.check("no_false_alarm", text="A thread that needs nothing is not raised.")
def no_false_alarm(case, out):
    if case.expected["flag"] != "ok":
        return NA
    return verdict(out["flag"] == "ok", f"raised as {out['flag']}")
