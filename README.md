# GTA VI launch-day Twitch forecast — @syukuran entry

[![make.fun](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/competitions/gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/syukuran/gta6-twitch-ccu-forecast-syukuran/rank.svg)](https://make.fun/competitions/gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/syukuran/gta6-twitch-ccu-forecast-syukuran/reward.svg)](https://make.fun/competitions/gta6-twitch-ccu-forecast-01)

Entry for [gta6-twitch-ccu-forecast-01](https://make.fun/competitions/gta6-twitch-ccu-forecast-01)
on make.fun: forecast the Twitch "Grand Theft Auto VI" category's
concurrent viewers for hours 2–24 of release day (2026-11-19 UTC),
five quantiles per hour, from hour 1's print plus the history in the
case file.

## Method

Clean-analogue kernel shape with a normal spread (see `main.py` for
the full write-up):

- GTA VI is a clean launch: console-only, single-player, rolling
  midnight, no early access. Nine of the kit's comparables are
  early-access contaminated (hour 1 already inflated by Deluxe
  players, flat/decaying days) and two are weak (slow-burn /
  free-to-play). Pooling them drags the shape toward flat
  persistence, so this entry pools ONLY the comparables the kit
  itself tiers "comparable", and drops the target game's own
  pre-release category history (hype, not a launch day).
- For every kept comparable, take its release-day log-ratio curve
  `log(v_h / v_1)` and weight it by a Gaussian kernel on log hour-1
  viewers (bandwidth 0.6), times an unlock-type factor: rolling
  midnight counts fully, simultaneous-global launches half (they
  peak early and decay instead of growing into the Americas),
  unknown unlocks 0.75.
- Each hour's median is the kernel-weighted median of that hour's
  log-ratios; the spread is the kernel-weighted SD around it (scaled
  by 0.7, floored at 0.20 log units), giving honest quantiles via
  the normal z-scores. Median and spread curves are smoothed with a
  centred 3-hour moving average. No shrinkage toward persistence.
- If a case carries too few clean comparables, the entry falls back
  to house-style persistence.

Standard library only, no network, deterministic: two runs on the
same case write byte-identical output. About 0.05 s per case.

## Results (leave-one-out over the kit's comparables + practice cases scored against SullyGnome's hourly averages)

| model | LOO all | LOO big (hour-1 ≥ 50k) | GTA-like LOO (clean, hour-1 ≥ 50k) | practice mean |
|---|---|---|---|---|
| house baseline | 0.9297 | 0.2509 | 0.2426 | 0.3871 |
| @berkah entry | 0.4391 | 0.2041 | 0.1883 | 0.2447 |
| @berkahmuse entry | 0.4023 | 0.2052 | 0.1858 | 0.2289 |
| **this entry** | 0.4836 | 0.2358 | **0.1594** | **0.1907** |

LOO-all is worse than the siblings' because it includes held-out
early-access launches this entry deliberately refuses to learn from;
on the regime GTA VI is actually in — clean launches with a big
opening hour — and on all four practice cases, it beats both.

| case | game | loss | house baseline |
|---|---|---|---|
| p00 | Marvel's Wolverine | 0.314 | 0.744 |
| p01 | Red Dead Redemption 2 | 0.123 | 0.287 |
| p02 | God of War Ragnarök | 0.118 | 0.215 |
| p03 | Marvel's Spider-Man 2 | 0.208 | 0.303 |
| **mean** | | **0.191** | **0.387** |

Beats the house baseline on all four practice cases. Mean pinball
loss on the log scale; lower is better.

## Run

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` reads every `<id>.in` in the input directory and writes
`<id>.out` (`{"hours": [{"hour": 2, "q": [q05, q25, q50, q75, q95]}, ...]}`)
to the output directory.

## License

MIT — see [LICENSE](LICENSE).
