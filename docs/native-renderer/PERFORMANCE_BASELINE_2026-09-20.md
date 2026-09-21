# Native-renderer performance baseline — 2026-09-20

Status: **PERF-00 complete; PERF-01 measured, with no default policy change.**

## Reproduction contract

The committed fixed controls are:

| ID | Script and measured window | Workload |
| --- | --- | --- |
| `open-world-1x/2x` | `fh1-open-world-performance.fh1test`, wall seconds 20–46.7 after a 20-second warmup | menu transition, stationary open world, changing traffic |
| `recaro-race-1x` | `fh1-race.fh1test`, wall seconds 40–76.5; race motion begins at second 70 | event entry, stationary grid, then moving race |
| `timing-straight` | `fh1-timing-straight.fh1test`, wall seconds 29–33 | short moving control before the first bend |

North Carson and Hot Hatch Hustle retain the qualified windows in
[A6 owned-depth retention](A6_OWNED_DEPTH_RETENTION.md) and the
[Carson geometry fix](CARSON_GEOMETRY_CACHE_FIX.md). The Outpost, plaza,
divided-highway and wooded-junction leads remain the elapsed-time markers in
[the 2026-09-08 discovery](DISCOVERY_FINDINGS_2026-09-08.md); they are useful
manual capture targets but are excluded from automated A/B claims until an
input script reaches each location.

Every new discovery run now records the main and SDK revisions and dirty state,
actual executable/runtime/renderer hashes, route and settings hashes, exact game
arguments, OS, GPU and driver, and staged shader/pipeline/prewarm hashes in its
local `build.json`. Runs use the installed AppData state directly and never copy,
reset or replace its save.

The pilot set the next comparison gate: use the fixed 20–46.7-second open-world
window, two warmed A/B/B/A blocks per affected scale, a 32 MiB geometry ceiling,
and reject a candidate that regresses median or p95 by more than 3% or p99 by
more than 5%. Treat a single p99 outlier as noise requiring another block, not as
evidence. Captures, pass inventory and corpus logging stay outside clean timing.
No Xenia comparison is claimed.

## PERF-00 baseline

The local evidence root is `.local/native-renderer/perf-00-01/`. Its manifests,
reports, captures and sampled logs are local-only because they contain machine
and game-derived data. Values below are means of the per-run 20–46.7-second
window statistics; A disables and B enables the experimental rejection memo.

| Scale / order | Control median / p95 / p99 ms | Candidate median / p95 / p99 ms | Mean GPU ms, control / candidate |
| --- | ---: | ---: | ---: |
| 1x A/B/B/A | 33.985 / 55.785 / 72.425 | 34.485 / 56.215 / 73.325 | 33.895 / 33.150 |
| 2x A/B/B/A | 34.975 / 58.305 / 97.220 | 35.345 / 57.315 / 70.390 | 33.845 / 34.490 |

Traffic and scene state dominate the small median/p95 differences. The 2x
control p99 contains one large outlier, so the block does not establish a p99
win. The Recaro race reaches 68.20 ms median, 92.98 ms p95 and 102.41 ms p99 in
the moving 70–76.5-second window, with 58.26 ms mean measured GPU time. This
identifies GPU work as the main cost in that window; admission is not the tail
cause shown by this capture.

## PERF-01 result

Instrumentation now reports admission attempts, allocation-info calls, eviction
scans, in-flight/recent rejection reasons and peak resident bytes. The cache
budget is temporarily sweepable through `fh1_geometry_cache_mb` (8–128 MiB,
32 MiB default). A fixed 64-slot rejection memo was tested separately behind
`fh1_cache_geometry_rejections`; it remains disabled by default.

| 1x budget | Attempts | Allocation queries | Eviction scans | Memo hits | Peak bytes | Mean p95 ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 MiB | 867 | 344 | 181 | 523 | 16,777,216 | 56.05 |
| 32 MiB | 188 | 188 | 0 | 0 | 19,070,976 | 56.44 |
| 48 MiB | 184 | 184 | 0 | 0 | 18,481,152 | 61.00 |

At the shipping 32 MiB budget, both 1x/2x open-world controls report zero
rejections and zero eviction scans. The denser Recaro route reaches exactly
32 MiB and performs 81 successful eviction scans, but reports zero rejected or
repeated requests. The memo removes 523 repeated queries only under artificial
16 MiB pressure; that single run does not establish a tail improvement. The
48 MiB result is slower and its lower peak proves that extra capacity was unused.

The accepted result is therefore the counters, reproducible budget sweep, and
expiry/correctness check. The 32 MiB default and recent-frame residency policy
stay unchanged, and the rejection memo stays opt-in. Pooling and recycling remain
deferred until a route shows rejected admission work at the shipping budget.

Validation: production geometry extraction check, recorder self-check, Release
preview build, 1x/2x A/B/B/A open-world runs, 16/32/48 MiB sweep, and the 1x
Recaro race all completed normally.
