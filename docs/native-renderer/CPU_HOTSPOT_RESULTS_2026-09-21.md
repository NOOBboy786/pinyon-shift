# First symbolized CPU hotspot capture — 2026-09-21

The Recaro route now has a valid sampled CPU and context-switch trace. Two
generated title regions and runtime file logging dominate this selected CPU
  window, but it is **before** race movement. This is a ranking
of CPU execution, not proof that each item delays presentation; confirm the
relevant thread and stack in the ETL before editing.

## Capture quality and scope

- Route: `config/render-tests/fh1-race.fh1test` with the installed AppData save.
- Local capture: `.local/cpu-profile/20260921-155143/`; the 1.7 GB ETL and
  derived CSV/JSON reports are local artifacts, not checked into Git.
- WPR and TraceEvent both report zero lost events. The game exited normally.
- 5,031 source-frame markers, 249,088 game CPU samples, and 667,699 completed
  blocked intervals were exported. Only 120 samples (0.05%) lack stacks.
- Matching PDBs resolved for the title, both generated guest facades,
  `rexruntimerd`, and `rexgpu-fh1rd`. Windows kernel and display-driver frames
  are not fully symbolized by the bundled project symbols.
- The ranked window is source frames 4,200–4,590: 391 frames across 8.408 s.
  These are title `SourceFrame` IDs, while the route's 4,200/4,560/4,590
  numbers are 60 Hz wall-clock script ticks. The captured input log puts the
  throttle press after this source-frame window. This is a pre-driving sample,
  not a moving-race benchmark. Rows outside it are excluded, not lost.
- Source-frame intervals have a 21.601 ms median and 27.223 ms p95. The same
  session's consumed-swap `frame_time_us` has a 21.416 ms median and 27.547 ms
  p95 across the corresponding 391 rows; the totals differ by less than 1 ms
  across the 8.408 s window. These clocks agree in aggregate, but individual
  source frames are not yet joined to consumed swaps or presented refreshes.

Across these frames, sampled CPU time summed over all game threads has a
65 ms/frame median and 80 ms/frame p95. These are **not** frame wall times:
multiple threads execute concurrently. Blocked-time totals likewise sum
across idle and active threads; the 1,744 ms/frame median does not imply a
1.7-second stall. Use the ETL's CPU Usage (Precise) timeline to identify waits
on the actual frame-critical thread.

## Ranked CPU work in the race window

| Region | Sampled CPU | Per source frame | Next check |
|---|---:|---:|---|
| Generated title `sub_829F04A8` | 3,076 ms | 7.87 ms | Inspect its guest loop, callers, and role on the hot title thread. |
| Generated title `sub_823E91F0` | 2,123 ms | 5.43 ms | Identify the guest operation and whether its work is frame-critical. |
| Runtime `spdlog::details::file_helper::flush` stack | 1,576 ms inclusive | 4.03 ms | A/B INFO batching; ERROR flushes remain immediate. |
| Runtime `spin_wait_strategy::wait_until_published` | 553 ms | 1.41 ms | Correlate the spin with frame-boundary timing and producer progress. |
| GPU module `rexgpu-fh1rd` (all leaves) | 3,006 ms | 7.69 ms | Inspect packet/binding stacks only after the larger title and logging costs. |

The two title symbols are generated names shown as `__imp__sub_*` by the PDB.
They run on the same title thread, and `sub_829F04A8` is often called from
`sub_823E91F0`; their inclusive stack costs must not be added together. They
identify hot regions; they do not reveal gameplay semantics on their own.
For the logging row, 1,073 of its 1,576 samples have kernel leaves, so an
ordinary leaf-function ranking hides much of that cost. The per-frame module
totals are title 37.26 ms, Windows kernel 8.91 ms, GPU module 7.69 ms, and
runtime module 3.84 ms. Full stacks attribute 808 flush samples to pipeline
configuration INFO logging and 768 to failed-draw ERROR logging. INFO batching
can only affect the first part. Kernel samples outside those stacks need public
Microsoft symbols before assigning them to a specific subsystem.

The local `race-hotspots.md` in that capture directory contains the function,
module, thread, and wait rankings; its JSON companion
contains every selected frame's CPU and blocked-time totals. To reproduce it:

```powershell
dotnet run --project tools/profile-etl-export -- .local/cpu-profile/20260921-155143
python tools/summarize-cpu-hotspots.py `
  .local/cpu-profile/20260921-155143/markers.csv `
  .local/cpu-profile/20260921-155143/samples.csv `
  --waits .local/cpu-profile/20260921-155143/waits.csv `
  --start-frame 4200 --end-frame 4590 `
  --output .local/cpu-profile/20260921-155143/race-hotspots.json
```

## Sustained route and INFO-flush A/B

The separate `config/render-tests/fh1-race-sustained.fh1test` route holds
throttle for 45 s after script tick 4,200. Four normal-exit runs measured the
30 s between its `race-moving` and `race-sustained` captures with
`tools/summarize-drive-window.py`. All four had seven captures, no render-test
failures, matching 244-event diagnostic sequences, and about 30 s of title
simulation in that interval.

| Run | INFO batching | Start position X | Consumed swaps | Median | P95 |
|---|---|---:|---:|---:|---:|
| 1 | off | -1743.6 | 811 | 33.991 ms | 58.210 ms |
| 2 | on | -1743.3 | 989 | 30.070 ms | 55.695 ms |
| 3 | off | -1797.9 | 1152 | 24.619 ms | 52.950 ms |
| 4 | on | -1799.2 | 1203 | 22.970 ms | 52.523 ms |

The matched pairs show 11.5% and 6.7% lower median with batching, but the
starting scene shifted materially between pairs and the source of the gain is
not established. The second pair gained only 0.8% at p95. The switch remains
**off by default**. It only changes the flush threshold to WARN and adds a
one-second periodic flush; messages, levels, and sinks are unchanged, and
`--log_batch_info_flush=false` is the rollback setting.

The moving route also exposes a larger problem. The last 31 s of the fourth
run alone generated about 735,560 ERROR records, including 367,780 failed
draws. The paired error reports say that FH1 vertex shaders are absent from
the offline analysis catalog, so the backend rejects those draws. This
overwrites the 500 MB rolling runtime log within about half a minute and
makes INFO-only flushing a questionable primary target. The graphics catalog
needs coverage for the save-backed sustained route before treating its frame
times as a representative rendering benchmark. Do not suppress these errors
to manufacture a speedup.

The [capture procedure](CPU_HOTSPOT_PROFILING.md) has the ready-to-run elevated
WPR command for the sustained route and the optional batching variant. A new
sampled ETL is needed to verify moving-race flush stacks and correlate them
with producer, consumed-swap, submission, and present events. WPR denied the
non-elevated session, so this trace remains uncollected.
