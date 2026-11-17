"""gta6-twitch-ccu-forecast-01 entry for @syukuran (Python 3.13, standard library only).

Approach: clean-analogue kernel shape with normal spread.

GTA VI is a clean launch: a console-only, single-player game with a
rolling-midnight unlock and no early access. Most past launches are not
clean analogues -- nine of the kit's comparables are early-access
contaminated (their hour 1 is already inflated by Deluxe-edition
players, so their release days sit flat or decay) and two are weak
(slow-burn / free-to-play). Pooling them in drags the shape toward flat
persistence and costs real accuracy on launches like this one, so this
entry pools ONLY the comparables the kit itself tiers "comparable",
and drops the target game's own pre-release category history (hype,
not a launch day).

For every kept comparable, take its release-day hourly viewers and
form the log-ratio curve log(v_h / v_1), h = 2..24. Weight each launch
by a Gaussian kernel on log hour-1 viewers (bandwidth 0.6), so launches
whose opening hour looked like this game's opening hour dominate the
shape, times an unlock-type factor: rolling-midnight launches count
fully (GTA VI unlocks rolling midnight), simultaneous-global launches
half (their day peaks early and decays instead of growing into the
Americas), unknown unlocks 0.75.

Per hour, the forecast median is the kernel-weighted median of that
hour's log-ratios and the spread is the kernel-weighted standard
deviation of the same ratios around that median, scaled by 0.7 and
floored at 0.20 log units; quantiles come from the normal z-scores.
Both the median curve and the spread curve are smoothed with a centred
3-hour moving average, because a launch day's true shape is smooth
while per-hour estimates from ~26 launches are noisy. No shrinkage
toward persistence: on clean big launches the unshrunk shape scores
best (shrinking to 0.9 cost ~0.01 of practice loss).

Everything is computed from the case file at run time: no network, no
randomness, no wall-clock use, so two runs on the same case produce
byte-identical output.

Validation (leave-one-out over the kit's comparables, contest pinball
loss on the log scale; practice cases scored against SullyGnome's
hourly averages, the same source the kit is built from):
  - house baseline:  LOO all 0.9297, LOO big 0.2509, practice 0.3871
  - @berkah entry:   LOO all 0.4391, LOO big 0.2041, practice 0.2447
  - @berkahmuse:     LOO all 0.4023, LOO big 0.2052, practice 0.2289
  - this entry:      LOO all 0.4836, LOO big 0.2358,
                     GTA-like LOO (clean, hour-1 >= 50k) 0.1594 vs
                     0.1883 (@berkah) and 0.1858 (@berkahmuse),
                     practice 0.1907 vs 0.2447 / 0.2289
  LOO-all is worse than the siblings' because it includes held-out
  early-access launches this entry deliberately refuses to learn from;
  on the regime GTA VI is actually in -- clean launches with a big
  opening hour, and on all four practice cases -- it beats both.

Input:  every <id>.in in $MAKEFUN_INPUT_DIR (else /input).
Output: <id>.out in $MAKEFUN_OUTPUT_DIR (else /output):
        {"hours": [{"hour": 2, "q": [q05, q25, q50, q75, q95]}, ...]},
        23 rows, hours 2..24, quantiles non-decreasing, each in (0, 1e9].
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so a
# module shipped beside this file imports.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# Gaussian kernel bandwidth on log hour-1 viewers (log units).
BANDWIDTH = 0.6
# Unlock-type weight: rolling-midnight launches are the true analogue
# for GTA VI; simultaneous-global launches peak early and decay.
UTYPE_WEIGHT = {"rolling": 1.0, "simul": 0.5, "unk": 0.75}
# Spread = max(SPREAD_FLOOR, SPREAD_SCALE * weighted SD of log-ratios).
SPREAD_SCALE = 0.7
SPREAD_FLOOR = 0.20
# Persistence fallback spread (the house baseline's sigma).
FALLBACK_SIGMA = 0.15
# A comparable needs hour 1 plus at least this many scored hours.
MIN_DAY_HOURS = 12
# Usable clean shape curves needed, else fall back to the baseline.
MIN_CURVES = 3


def round2(x):
    """Round to 2 decimals, half up (matches the house baseline's rule).

    Whole numbers come back as ints so json.dumps writes 1240, not 1240.0.
    """
    scaled = x * 100.0
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100.0
    return int(value) if value == int(value) else value


def clamp_q(x):
    """Keep a quantile inside the format's (0, 1e9] range."""
    if x <= 0 or x != x:  # also guards NaN
        return 1
    if x > 1_000_000_000:
        return 1_000_000_000
    return x


def parse_time(text):
    """ISO 8601 UTC timestamp -> datetime (handles trailing Z)."""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def release_day_series(comp):
    """A comparable's release-day hourly viewers as {hour: viewers}.

    `day_start` is the release day's 00:00 UTC; hour h covers
    [day_start + (h-1)h, day_start + h h). Rows with no viewers, or
    with viewers <= 0, are skipped.
    """
    try:
        day_start = parse_time(comp["day_start"])
    except (KeyError, TypeError, ValueError):
        return {}
    series = {}
    for row in comp.get("hourly") or []:
        try:
            hour = (parse_time(row["from"]) - day_start).total_seconds() / 3600
            viewers = row["viewers"]
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= hour < 24 and abs(hour - round(hour)) < 1e-9 and viewers and viewers > 0:
            series[int(hour) + 1] = float(viewers)
    return series


def tier_of(comp):
    """The kit's own tier for a comparable, read from its unlock note."""
    unlock = comp.get("unlock") or ""
    if "Tier: early-access-contaminated" in unlock:
        return "eac"
    if "Tier: weak" in unlock:
        return "weak"
    if "Tier: target-history" in unlock:
        return "target"
    if "Tier: comparable" in unlock:
        return "comp"
    return "unknown"


def unlock_type(comp):
    """rolling: midnight-local rolling unlock; simul: one global unlock
    time; unk: the note does not say."""
    unlock = (comp.get("unlock") or "").lower()
    if "rolling" in unlock or "midnight local" in unlock:
        return "rolling"
    if "simultaneous" in unlock or "single global" in unlock:
        return "simul"
    return "unk"


def usable_comparables(case):
    """Clean-analogue release-day series: (hour-1 viewers, series).

    Keeps only Tier "comparable" launches: early-access-contaminated
    launches have an inflated hour 1 and a flat/decaying day, weak
    launches are slow-burn or free-to-play, and the target game's own
    category history is pre-release hype, not a launch. Needs hour 1
    and at least MIN_DAY_HOURS scored hours.
    """
    target_name = (case.get("game") or {}).get("name", "")
    target_day = (case.get("day_start", "") or "")[:10]
    out = []
    for comp in sorted(case.get("comparables") or [], key=lambda c: c.get("name", "")):
        if tier_of(comp) != "comp":
            continue
        if target_name and target_name in (comp.get("name") or ""):
            continue
        if (comp.get("day_start", "") or "")[:10] == target_day:
            continue
        series = release_day_series(comp)
        scored = sum(1 for h in range(2, 25) if h in series)
        if 1 in series and scored >= MIN_DAY_HOURS:
            out.append((series[1], series, unlock_type(comp)))
    return out


def weighted_median(pairs):
    """Weighted median of (weight, value) pairs; deterministic."""
    ordered = sorted(pairs, key=lambda p: p[1])
    total = sum(w for w, _ in ordered)
    if total <= 0:
        return ordered[len(ordered) // 2][1]
    acc = 0.0
    for weight, value in ordered:
        acc += weight
        if acc >= total / 2.0:
            return value
    return ordered[-1][1]


def weighted_sd(pairs, centre):
    """Weighted population SD of the values around `centre`."""
    total = sum(w for w, _ in pairs)
    if total <= 0 or len(pairs) < 2:
        return 0.0
    var = sum(w * (v - centre) ** 2 for w, v in pairs) / total
    return math.sqrt(var) if var > 0 else 0.0


def smooth3(values):
    """Centred 3-hour moving average over {hour: value} (edge-truncated)."""
    out = {}
    for hour in sorted(values):
        near = [values[h] for h in (hour - 1, hour, hour + 1) if h in values]
        out[hour] = sum(near) / len(near)
    return out


def kernel_shape(p1, comps):
    """Per-hour (median log-ratio, spread) from kernel-weighted clean
    comparables, both curves smoothed over neighbouring hours.

    A comparable's weight is a Gaussian kernel on log hour-1 viewers
    (bandwidth BANDWIDTH) times its unlock-type factor, so launches
    whose opening hour looked like this game's opening hour -- and
    whose unlock rolled midnight like GTA VI's -- dominate the shape.
    """
    log_p1 = math.log(p1)
    median = {}
    spread = {}
    for hour in range(2, 25):
        pairs = []
        for v1, series, utype in comps:
            if hour in series:
                w = math.exp(-0.5 * ((math.log(v1) - log_p1) / BANDWIDTH) ** 2)
                w *= UTYPE_WEIGHT.get(utype, 1.0)
                pairs.append((w, math.log(series[hour] / v1)))
        if not pairs:
            continue
        med = weighted_median(pairs)
        median[hour] = med
        spread[hour] = max(SPREAD_FLOOR, SPREAD_SCALE * weighted_sd(pairs, med))
    if not median:
        return {}
    median = smooth3(median)
    spread = smooth3(spread)
    return {h: (median[h], spread[h]) for h in median}


def baseline_quantiles(p1, hour):
    """House baseline quantiles for one hour (flat persistence + spread)."""
    return [round2(p1 * math.exp(z * FALLBACK_SIGMA * math.sqrt(hour - 1))) for z in Z]


def forecast_case(case, name):
    if case.get("levels") != LEVELS:
        raise ValueError("%s asks for levels %s, not %s" % (name, case.get("levels"), LEVELS))
    first = next((k for k in case.get("known") or [] if k.get("hour") == 1), None)
    if first is None:
        raise ValueError("%s has no hour-1 print" % name)
    p1 = max(1.0, float(first["viewers"]))

    comps = usable_comparables(case)
    shape = kernel_shape(p1, comps) if len(comps) >= MIN_CURVES else {}

    hours = []
    for row in case.get("forecast") or []:
        hour = row["hour"]
        if hour in shape:
            med, sd = shape[hour]
            qs = [p1 * math.exp(med + z * sd) for z in Z]
        else:
            # No clean shape for this hour: house-style persistence.
            qs = [p1 * math.exp(z * FALLBACK_SIGMA * math.sqrt(hour - 1)) for z in Z]
        qs = [round2(clamp_q(q)) for q in qs]
        # Guard the non-decreasing rule against rounding ties.
        for i in range(1, 5):
            if qs[i] < qs[i - 1]:
                qs[i] = qs[i - 1]
        hours.append({"hour": hour, "q": qs})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / (path.stem + ".out")).write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
