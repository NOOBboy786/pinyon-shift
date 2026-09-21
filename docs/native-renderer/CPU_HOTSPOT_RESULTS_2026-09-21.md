# First symbolized CPU hotspot capture — 2026-09-21

The Recaro route now has a valid sampled CPU and context-switch trace. Two
generated title regions and runtime file logging dominate this selected CPU
window, but it is mostly **before** sustained race movement. This is a ranking
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
  The route takes its `race-moving` capture at frame 4,560 and stops at 4,590,
  leaving only 31 moving frames (about 0.67 s). This window must not be used
  as a sustained moving-race benchmark. Rows outside it are excluded, not lost.

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
| Runtime `spdlog::details::file_helper::flush` stack | 1,576 ms inclusive | 4.03 ms | Locate who flushes during the moving race and whether logging can be reduced. |
| Runtime `spin_wait_strategy::wait_until_published` | 553 ms | 1.41 ms | Correlate the spin with frame-boundary timing and producer progress. |
| GPU module `rexgpu-fh1rd` (all leaves) | 3,006 ms | 7.69 ms | Inspect packet/binding stacks only after the larger title and logging costs. |

The two title symbols are generated names shown as `__imp__sub_*` by the PDB.
They identify hot regions; they do not reveal gameplay semantics on their own.
For the logging row, 1,073 of its 1,576 samples have kernel leaves, so an
ordinary leaf-function ranking hides much of that cost. The per-frame module
totals are title 37.26 ms, Windows kernel 8.91 ms, GPU module 7.69 ms, and
runtime module 3.84 ms. Kernel samples need public Microsoft symbols or stack
inspection before assigning them to a specific subsystem. The 31-frame moving
slice also ranks the two title regions highest among named leaves, but is too
short to establish a stable race-specific cost or a whole-frame improvement.

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

The [capture procedure](CPU_HOTSPOT_PROFILING.md) covers repeat runs and when
to use PIX for CPU/GPU overlap. Before a race-specific optimization, extend
the route past frame 4,590 and repeat this capture over a sustained moving
segment. Any change then needs a before/after trace on that same segment, plus
the existing visual and gameplay checks.
