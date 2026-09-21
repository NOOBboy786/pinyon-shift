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
| Runtime `spdlog::details::file_helper::flush` stack | 1,576 ms inclusive | 4.03 ms | Identify the log level and failing draw path. |
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
configuration and 768 to failed draws. Both paths emit ERROR, so INFO batching
cannot address them. Kernel samples outside those stacks need public Microsoft
symbols before assigning them to a specific subsystem.

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
starting scene shifted materially between pairs. The second pair gained only
0.8% at p95. The symbolized moving trace below shows that the hot flushes
are ERROR, not INFO, so these A/B differences do not establish a benefit from
INFO batching. The experimental switch was removed.

The moving route also exposes a larger problem. The last 31 s of the fourth
run alone generated about 735,560 ERROR records, including 367,780 failed
draws. The paired error reports say that FH1 vertex shaders are absent from
the offline analysis catalog, so the backend rejects those draws. This
overwrites the 500 MB rolling runtime log within about half a minute and
makes INFO-only flushing a questionable primary target. The graphics catalog
needs coverage for the save-backed sustained route before treating its frame
times as a representative rendering benchmark. Do not suppress these errors
to manufacture a speedup.

## Symbolized moving-race trace

An elevated run of the sustained route produced a valid ETL at
`.local/cpu-profile/20260921-165652/`: 384,724 CPU samples, 1,051,998 waits,
and zero lost events. The `race-moving` to `race-sustained` captures bracket
source frames 4,930–6,136, 29.88 s and about 313.5 m of vehicle travel.
There were 1,210 consumed swaps in 30.05 s, with a 24.870 ms median and
45.778 ms p95 wall interval. Source-frame intervals had a 24.193 ms median
and 45.639 ms p95. These are the same moving phase, not a stationary menu.

The captured `consumed_swap` IDs were one ahead of the corresponding
`SourceFrame` IDs. Subtracting one for this ETL yields 1,207 ordered pairs
with no negative producer-to-consumer latencies. The source code now emits
the source ordinal directly. For 1,206 fully paired frames (4,930–6,135),
the median source-to-submission-begin latency is 25.133 ms (p95 39.323 ms),
submission takes 2.097 ms (p95 2.869 ms), and source-to-present is 27.781 ms
(p95 42.499 ms). Submission-end to consumed swap is 0.038 ms median, and
consumed swap to present is 0.446 ms median. Most measured latency precedes
submission; these spans are elapsed time, not proof that a particular task
blocks the frame.

In that 29.99 s window the GPU command thread used 26.175 s of sampled CPU.
Its logging stacks account for 5.404 s in `file_helper::flush` and 2.296 s
in `fwrite_bytes`, with no sample overlap. The 5.404 s of flush samples divide
between `PipelineCache::ConfigurePipeline` (2.739 s) and failed draws in
`CommandProcessor::ExecutePacketType3Draw` (2.665 s). Both are ERROR paths.
The rolling log's last 22 s alone contain 364,437 missing-vertex-shader
ERRORs and the same number of paired failed-draw ERRORs; only 53 INFO lines
remain. These errors involve 17 distinct vertex shader hashes. The most
frequent, `B8489164D5A86043`, appears 122,596 times. The 500 MB rolling log
was already overwritten by this volume, so its counts understate the run.

Across consumed-swap intervals, sampled logging CPU totals 7.681 s and
correlates with interval duration (Pearson r = 0.784). This is a strong
triage signal, not a predicted frame-time gain: making the missing shaders
available will also cause the currently rejected draws to execute. The
generated title thread also used 25.856 s of sampled CPU, with hot symbols
`sub_829F04A8` and `sub_823E91F0`; their call stacks overlap and neither
has yet been shown to be on the frame-critical path.

The next rendering task is to cover the save-backed sustained scene in the
offline vertex shader catalog, then repeat this capture and compare draw
success, ERROR volume, and frame timings. Do not hide the ERROR reports as a
performance fix. The [capture procedure](CPU_HOTSPOT_PROFILING.md) describes
the repeatable WPR command.
