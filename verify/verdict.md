# Independent verification verdict — make.fun gta6-twitch-ccu-forecast-01, @syukuran entry

**Verdict: PASS**

Verifier did not build this entry. All numbers below were recomputed with the
verifier's own code (no import/copy of the builder's `main.py`); the builder's
program was only executed as a black box. Builder files were not modified
(`git status` clean after verification).

- Repo: `/home/hatch/workspace/makefun-gta6/engine-syukuran/`
- Commit verified: `1252c8b754c022e123b7ee79805c90fdd5fa5ed3`
  (`Clean-analogue kernel shape forecast for gta6-twitch-ccu-forecast-01 (@syukuran)`)
- Entrypoint: `main.py`; kit:
  `/home/hatch/workspace/makefun-watch/kits/gta6-twitch-ccu-forecast-01/gta6-twitch-ccu-forecast-01-kit/`
- Verification date: 2026-11-17 (WIB). Local Python was 3.12.3 (task states 3.13);
  the code uses only stdlib features present in both.

## 1. Reruns (determinism + runtime)

`MAKEFUN_INPUT_DIR=<kit>/input`, two separate output dirs, all four practice cases:

| run | wall time (all 4 cases) | p00 sha256 | p01 sha256 | p02 sha256 | p03 sha256 |
|---|---|---|---|---|---|
| 1 | 0.263 s | 917fc58c…875a908 | 0bf50612…e8c33 | 2295fe67…952660dd | a400c244…f16963 |
| 2 | 0.160 s | identical | identical | identical | identical |

- Two runs byte-identical on all four outputs (`diff -r` clean). **Determinism: PASS.**
- ~0.04–0.07 s per case, far under the 8 s/case limit. **Runtime: PASS.**

## 2. Practice cases — independently recomputed pinball loss

Practice answers taken from the builder-fetched SullyGnome one-month JSONs
(`/tmp/wolv.json`, `/tmp/p01.json`, `/tmp/p02.json`, `/tmp/p03.json` — reused as
instructed, no new download): "Average viewers" dataset, point at `HH:00` =
hour `HH+1` of the release day. Cross-check: SullyGnome hour-1 equals each
case file's `known` hour-1 print exactly (p00 23357, p01 116550, p02 269517,
p03 119087), and all 23 hours 2–24 are present for every case.
Scoring per RULES.txt: `2*max(tau*d, (tau-1)*d)`, `d = ln(y) - ln(q)`,
mean over 23 hours × 5 levels.

| case | game | recomputed | claimed | diff |
|---|---|---|---|---|
| p00 | Marvel's Wolverine | 0.3136 (exact 0.313557) | 0.3136 | 0.0000 |
| p01 | Red Dead Redemption 2 | 0.1234 (exact 0.123429) | 0.1234 | 0.0000 |
| p02 | God of War Ragnarök | 0.1178 (exact 0.117790) | 0.1178 | 0.0000 |
| p03 | Marvel's Spider-Man 2 | 0.2078 (exact 0.207836) | 0.2078 | 0.0000 |
| **mean** | | **0.1907 (exact 0.190653)** | **0.1907** | **0.0000** |

Tolerance was 0.001. **Practice: MATCH.**
Sanity check of the scorer: house baseline recomputed with the same code gives
0.7437 / 0.2868 / 0.2146 / 0.3033, mean 0.3871 — exactly the claimed 0.744 /
0.287 / 0.215 / 0.303 / 0.3871.

## 3. Leave-one-out — independently recomputed

Method (verifier's own code): from `p00.in`, the 37 usable comparables are
those with a release-day hour-1 print and ≥ 12 scored hours 2–24 (the 38th,
the GTA VI target-history comparable, has no hour-1 and only 7 scored hours,
so it is excluded — matching the claimed n = 37). For each, a case was built
from `p00.in` with that launch as target (its own hour-1 as `known`, its own
day as `day_start`, the other 37 comparables as pool) and the committed
`main.py` was run on it in its own input/output directory (37 runs, 6.39 s
total wall). Scored against the held-out launch's actual hours 2–24 (all 37
have all 23 hours, so per-launch mean = pooled mean). Tier read from the
kit's own `Tier: …` note in each comparable's `unlock` field.

| metric | n | recomputed | claimed | diff |
|---|---|---|---|---|
| LOO all | 37 | 0.4836 (exact 0.483627) | 0.4836 | 0.0000 |
| LOO big (hour-1 ≥ 50k) | 20 | 0.2358 (exact 0.235808) | 0.2358 | 0.0000 |
| GTA-like LOO (Tier comparable, hour-1 ≥ 50k) | 13 | 0.1594 (exact 0.159444) | 0.1594 | 0.0000 |

Tolerance was 0.002. **LOO: MATCH on all three.**
Subset counts confirmed: big n = 20, GTA-like n = 13 (ELDEN RING, Cyberpunk 2077,
Monster Hunter Wilds, Black Ops 6, Modern Warfare III, Black Ops 7, Modern
Warfare 4, Zelda: Tears of the Kingdom, Borderlands 4, Elden Ring Nightreign,
FF VII Rebirth, The Last of Us Part II, Ghost of Tsushima).
Note: LOO-all is dominated by small-opening launches the entry does not target
(worst: Black Myth: Wukong 2.1130, Marathon 2.0424, ARC Raiders 1.5953) — this
is consistent with the builder's stated design, not a scoring error.

## 4. Output format (RULES.txt) — all four practice outputs, both runs

Checked per file: valid JSON, exactly one top-level key `hours`, exactly 23
rows, hours 2–24 each exactly once, each row exactly `{"hour": h, "q": [...]}`
with 5 quantiles, each finite, `0 < q <= 1e9`, non-decreasing, size ≤ 65536 bytes.

| case | size | rows | hours | quantiles | result |
|---|---|---|---|---|---|
| p00.out | 1455 B | 23 | 2–24 once each | 5, non-decreasing, in (0, 1e9] | PASS |
| p01.out | 1529 B | 23 | 2–24 once each | 5, non-decreasing, in (0, 1e9] | PASS |
| p02.out | 1555 B | 23 | 2–24 once each | 5, non-decreasing, in (0, 1e9] | PASS |
| p03.out | 1534 B | 23 | 2–24 once each | 5, non-decreasing, in (0, 1e9] | PASS |

Same result for run 2 (byte-identical files). All 37 LOO outputs also checked:
23 rows, hours 2–24 each once. **Format: PASS.**

## 5. Code audit (read-only)

- Imports only: `json`, `math`, `os`, `sys`, `datetime.datetime`, `pathlib.Path`
  — **stdlib only**.
- No network: no `socket`/`urllib`/`requests`/`http` references; no file/network
  access beyond reading `$MAKEFUN_INPUT_DIR/*.in` and writing `$MAKEFUN_OUTPUT_DIR/*.out`.
- No randomness or wall-clock: no `random`, no `time` module, `datetime` used
  only via `fromisoformat` to parse timestamps from the case file; no `now()`.
- Deterministic ordering: comparables sorted by name, cases processed in name
  order, fixed JSON separators. Consistent with the byte-identical reruns above.

## Mismatches

None. Every claimed number reproduced to 4 decimal places, within tolerance,
with zero discrepancies in format, determinism, runtime, or code audit.

## Artifacts (verifier's own, outside the builder repo except this verdict)

- This verdict: `/home/hatch/workspace/makefun-gta6/engine-syukuran/verify/verdict.md`
- Rerun outputs: `/tmp/verify-syukuran/run1/`, `/tmp/verify-syukuran/run2/`
- Verifier scripts: `/tmp/verify-syukuran/score_practice.py`,
  `/tmp/verify-syukuran/enumerate_loo.py`, `/tmp/verify-syukuran/run_loo.py`,
  `/tmp/verify-syukuran/format_check.py`; LOO cases/outputs/results:
  `/tmp/verify-syukuran/loo/`
