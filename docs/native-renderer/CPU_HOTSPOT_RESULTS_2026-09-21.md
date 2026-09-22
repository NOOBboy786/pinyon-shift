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

The captured `consumed_swap` IDs were one ahead of their intended ordinal.
The source code now emits the ordinal directly. The earlier phase join also
mistook D3D12 submission IDs for source-frame IDs, so its phase latencies are
superseded by the corrected post-fix trace below.

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

## Shader-catalog repair and saved-race replay

The installed cache's `4D5309C9.xsh` and legacy PSO file contain shaders
encountered in the saved race that the clean-state offline producer missed.
Preparation now copies those two **cache files only** into its isolated
producer state and includes their hashes in the preparation key. It does not
copy or alter the save. The resulting catalog grew from 12,507 to 12,590
analyzed shaders and covered all 37 distinct missing vertex hashes retained
in the rolling logs. Four more exact specializations observed on the first
replay were added to the producer; the final pack contains 24,763 variants.

The final `fh1-race-sustained.fh1test` replay exited normally with seven
captures and no catalog misses, shader-pack misses, or failed GPU draws.
The only ERROR in its session's runtime log was an unrelated `ResolvePath`
device lookup. The moving window had 1,577 consumed swaps over 30.015 s,
30.017 s of title simulation, and 378.7 m of vehicle travel. Its frame-time
median was 18.825 ms and p95 was 27.479 ms.

The earlier no-WPR, INFO-batching-off run with nearly identical starting
position (-1743.6 m versus -1743.5 m) measured 33.991 ms median and
58.210 ms p95. This matched-scene comparison is 44.6% lower at the median
and 52.8% lower at p95. An intermediate replay starting near -1799 m also
measured 16.635 ms median and 24.550 ms p95, versus 24.619 and 52.950 ms
for the earlier no-WPR run starting near -1798 m; that intermediate pack
still missed four specializations. These are observed end-to-end changes,
not a CPU attribution: no post-fix WPR trace was collected because this
session lacked elevation. Repeat the [capture procedure](CPU_HOTSPOT_PROFILING.md)
from elevated PowerShell to measure the new thread-level hotspots.

An installation without a prior legacy shader cache cannot gain these
save-specific shaders from this seeding path. The retail-disc corpus remains
the clean-install baseline; any newly encountered missing hash still needs a
separate producer source or specialization.

## Post-fix elevated CPU trace — 2026-09-22

The same sustained route completed normally with seven captures and a valid
ETL at `.local/cpu-profile/20260921-212706/`: 395,079 CPU samples, 1,151,404
waits, only 210 samples lacking stacks (0.05%), and zero lost events. The
saved race started at X = -1743.19 m and travelled 380.1 m between the
`race-moving` and `race-sustained` captures. Its 1,621 consumed swaps over
30.028 s had an 18.922 ms median and 26.074 ms p95, consistent with the
earlier repaired no-WPR run from X = -1743.50 m (18.825/27.479 ms). This
supports the observed improvement without assuming that WPR caused it.
The session's runtime log had no GPU ERRORs; one unrelated filesystem device
lookup ERROR remained.

The moving window spans source frames 5,626–7,247. Source-frame intervals
have an 18.734 ms median and 26.017 ms p95. For 1,621 complete ordinal
pairs, source boundary to consumed swap is 19.826 ms median (p95 27.509 ms),
consumed swap to closing D3D12 submission begin is 0.060 ms, submission is
2.525 ms, and submission end to present is 0.480 ms. Source to present is
22.889 ms median (p95 31.090 ms). The closing submission ID is the consumed
swap ordinal plus one; the `source_frame` field on asynchronous submission
events is only a snapshot. These spans are elapsed latency, not additive CPU
work or proof of a single critical function.

The title frame thread used 27.884 s of sampled CPU in this roughly 30 s
window; the GPU command thread used 25.730 s. On the title thread,
`sub_829F04A8` accounts for 9.320 s of leaf samples and appears in 10.867 s
of stacks. Its caller `sub_823E91F0` appears in 19.012 s of stacks; these
inclusive amounts overlap. The generated code shows a loop polling a guest
counter with repeated `db16cyc` delay hints, which currently recompile to
no-ops. This looks like a busy wait, but its synchronization role and effect
on frame pacing need a controlled test before changing it.

On the GPU command thread, `DeferredCommandList::Execute` appears in 3.774 s
of stacks, `UpdateBindings` in 2.395 s, and shared-memory `UploadRanges` in
2.157 s; these stacks may overlap. Only 0.002 s of that thread's samples
contain `spdlog`, confirming that the prior logging hotspot is gone. The
command thread is still busy, so the title wait-loop experiment should be
compared with a GPU submission timeline before treating reduced title CPU as
a frame-time win. Do not add another logging or shader-cache optimization
based on the pre-fix trace.

## Follow-up: visible race traffic

After the shader repair, the player reports roughly 10 FPS more in open world,
but the race remains difficult to play. With other cars visible, race FPS is
about 40% below open world; in first place with no cars visible, it is about
10% below open world. These are observations, not matched measurements, and
race position also changes scene and simulation state.

Capture repeated traffic-heavy and clear-road windows at the same resolution,
route, weather, and vehicle state. Record visible car count, per-frame draw and
geometry/texture upload counts, source/present intervals, and title/GPU thread
stacks. Compare equivalent windows before deciding whether car rendering,
simulation, submission, or GPU execution causes the gap. Keep the current game
session available for manual testing; collect traces in a later run.

## Counter-poll pacing trial and stationary traffic replay — 2026-09-22

A temporary, default-off hook at `0x829F04BC` tested a 1 ms sleep after each
2 ms spent in the title counter poll. The same RelWithDebInfo binary ran the
30-second moving race window with pacing off and on. Whole-process CPU usage
fell from 105.8 to 91.5 CPU seconds, but the consumed-swap median rose from
21.14 to 22.76 ms (p95 29.11 versus 29.21 ms). The player was already about
39 m apart at the `race-moving` captures, so the FPS comparison is not a
matched-scene effect estimate. The trial showed no frame-time win and the hook
was removed; the preview was rebuilt without it. Lower CPU use alone does not
justify changing the guest's synchronization loop.

The static SNR-M02 counter map is recorded below; the pacing trial did not
establish a safe replacement for this wait.

### Static counter contract for SNR-M02 — 2026-09-22

Generated title code narrows the wait's contract but does not yet establish
its host synchronization guarantee. `sub_823E91F0` compares a requested
position with `device+11036` minus the word at `*(device+11024)`, calls
`sub_829F03B0` to snapshot that word, then repeatedly calls
`sub_829F04A8` while the published position remains behind the requested
position. `sub_829F03B0` also snapshots `r13+256+88` and the guest timebase.
Within `sub_829F04A8`, the published word is re-read, a system counter from
`r13+256+88` is compared with the snapshot, and a threshold is loaded from
`0x8328CDF8`. The verified base image stores `0x1388` (5000) there. The
counter's units and the precise meaning of expiry are not yet proved; the
expiry branch calls `sub_82A007E0`.

`sub_82457D50` is a concrete writer path: it reads `device+11036`, emits
command words beginning with `0xC0003B00`, and, under its `device+21940`
and `device+11069` conditions, stores that position at
`*(device+11024)` and an associated value at the next word. It then advances
`device+11036` by two. Initialization in `sub_829EE7B8` also writes the
published-position word; `sub_82A007E0` has a recovery write. These title
stores do **not** by themselves prove whether the command processor or GPU
also writes the memory, nor when that write becomes visible relative to
submission and fences.

SNR-M02 therefore remained open at this static stage. A later runtime join is
recorded in [SNR-M02 counter evidence](SCENE_NATIVE_SNRM02_EVIDENCE_2026-09-22.md).
Any sleep/yield trial must preserve the observed ordering and compare
consumed-swap latency, tail behavior and route position against controls,
not only CPU use.

The moving route also sent the scripted car into barriers, invalidating its
late clear-road window as a traffic-only comparison. The new
[`fh1-race-traffic-stationary.fh1test`](../../config/render-tests/fh1-race-traffic-stationary.fh1test)
keeps the player stopped at the race start, captures opponents leaving every
second, then samples the same view after they have gone. In two independent
unpaced replays, the player's start-to-end pose drift was under 0.001 m.

| Replay | Window | Median frame | p95 frame | Median draws | Median guest GPU |
|---|---|---:|---:|---:|---:|
| First stationary | 0–8 s, opponents departing | 20.64 ms | 25.01 ms | 4,801 | 11.34 ms |
| First stationary | 13–18 s, clear view | 14.70 ms | 18.24 ms | 3,340 | 8.18 ms |
| Restored build | 0–8 s, opponents departing | 21.04 ms | 28.20 ms | 4,808 | 11.28 ms |
| Restored build | 13–18 s, clear view | 15.16 ms | 18.32 ms | 3,341 | 8.19 ms |

The early window costs about 39–40% more frame time in both replays, with
roughly 1,460 extra draws and 3.1 ms more measured guest GPU time. The
one-second images show several opponents at the start and progressively fewer
through seconds 1–7. None is obvious at second 8, yet draw count remains above
4,000 until about second 13. This supports a race-traffic workload cost, but
does not identify which draw passes, shadow work, AI, or submission costs are
responsible; off-screen opponents may still contribute. The stationary scene
also continues to animate, so it is a controlled comparison rather than an
exact car-only ablation.

The reproducible next profile is an elevated WPR capture of the stationary
fixture, splitting CPU samples at `race-ready`/`race-08` and
`race-13`/`race-18`:

```powershell
.\tools\capture-cpu-profile.ps1 -SkipBuild `
  -RenderTestScript config/render-tests/fh1-race-traffic-stationary.fh1test
```

Attribute the extra draws by pass and vehicle/shadow
ownership, then test a targeted change against this fixture and its images.
GPU time increases by about 3 ms, so a GPU pass capture is useful after the
draw owners are identified. Clean-install shader coverage remains separate.

## Stationary traffic pass attribution — 2026-09-22

The unmodified RelWithDebInfo preview replayed the same stationary script with
the existing critical-path trace and GPU corpus/timestamp diagnostics. These
diagnostic runs are for attribution; the uninstrumented medians above remain
the performance baseline. The scene and player pose stay fixed, but crowd,
effects, lighting, and opponent state continue to change.

Between `race-ready` and `race-08`, the traced source-frame interval had a
21.52 ms median, versus 14.24 ms between `race-13` and `race-18`. Command-tape
replay medians were 2.56/1.94 ms, and closing submission recording medians
were 2.70/2.07 ms. The title emitter took only 0.13/0.07 ms. The observed
submit-to-completion interval includes queueing and polling; it is not pure
GPU execution time. Trace logging changes absolute frame time.

Subtracting successive corpus checkpoints over 189 early and 210 clear source
frames yielded about 5,015 versus 3,423 prepared draws per frame. About 560
early draws per frame use depth-only vertex shader `5A28C7FAFD86F112` and
disappear entirely in the clear window. They span four attachment states and
many tiny index buffers (common index counts include 4, 9, and 7). This shader
uses the terrain-depth path in the D3D12 backend. The historically identified
80-draw dynamic-vehicle shadow epoch instead uses `4E1DA281CC3D7EDB` plus
two tail shaders. These are distinct; the disappearing terrain-depth draws
must not be removed or relabeled as vehicle shadows based on timing alone.

The existing GPU pass timestamps sampled four early and four clear frames.
Early frames had 4,723–5,242 draws and 10.63–11.30 ms of summed pass GPU time;
clear frames had 3,363–3,368 draws and 7.52–7.98 ms. A depth-only pass family
absent from the clear frames averaged 652 draws and 1.71 ms GPU in the early
samples. Another large family averaged 694 early versus 117 clear draws and
2.52 versus 0.10 ms GPU. Pass families group by attachment and use their first
draw as a label; the latter family's first draw is a post-chain shader, so
these aggregates do not identify all enclosed draw owners. GPU pass deltas
must not be added as independent traffic costs because other scene work also
changes. Checkpoint JSON serialization produced a recording-time outlier;
those wall times are not an FPS benchmark.

The `race-07` and `race-18` images show the same stopped camera with no obvious
nearby opponents in either image. Off-screen or effects work may continue
after visible cars leave. No production optimization follows safely from a
shader hash or pass label alone. The remaining steps are:

A temporary focused binding dump at source frame 5000 recorded 710 of the
`5A28C7FAFD86F112` depth draws. It found two prepared pipelines, four
attachment states, eight dynamic-state hashes, 444 distinct index-buffer
bases, and 103 distinct vertex-fetch sets. The draws form several contiguous
state groups, including one with 332 draws, rather than repeated copies of a
single identical operation. The data strengthens the case for repeated
terrain-depth work in multiple views, but does not identify the title owner or
prove which output each later consumer needs. The diagnostic edit was removed,
and the normal RelWithDebInfo preview rebuilt successfully.

The historical vehicle-shadow shader `4E1DA281CC3D7EDB` remains at about 70
draws per frame in both windows on attachment `152BC4D46BC006B2`; it is not
the disappearing family. The largest color attachment
(`84241CB4C5BD3DC8`) rises from about 880 to 1,700 draws per frame. Its
stable road/scene shader `B8489164D5A86043/68150A8E959006CD` stays near
385 draws in both windows; the additional color work is distributed across
many other shader pairs. This supports a multi-material scene workload rather
than a single repeated draw, but the corpus cannot assign those pairs to
individual vehicles without a title-object or binding join.

1. Run the stationary fixture through elevated CPU sampling to compare title
   and GPU-command stacks in the marked early and clear windows:

   ```powershell
   .\tools\capture-cpu-profile.ps1 -SkipBuild `
     -RenderTestScript config/render-tests/fh1-race-traffic-stationary.fh1test
   ```

2. Establish source/owner and producer-to-consumer bindings for the extra
   terrain-depth and color draws, using a focused race-frame pass capture if
   necessary. Optimize the proved hot owner at its shared boundary, then
   repeat uninstrumented stationary runs and compare simulation time, pass
   timings, and images. Do not trade away traffic rendering or shadows merely
   to reduce the draw counter.

## Elevated stationary CPU capture and depth ablation — 2026-09-22

The user supplied a valid, zero-dropped-event WPR capture at
`.local/cpu-profile/20260921-224902` for the stationary script. Symbolized
export had 8,411 source markers, 372,519 CPU samples, and 174 samples without
stacks. Split at the exact `race-ready`/`race-08` and `race-13`/`race-18`
output-frame markers, the traffic and clear windows had 343 frames in 8.003 s
and 328 frames in 4.992 s respectively:

| ETW metric | Traffic | Clear |
|---|---:|---:|
| Source interval median | 21.30 ms | 14.86 ms |
| Title emitter median | 0.175 ms | 0.062 ms |
| Command-tape replay median | 2.547 ms | 1.934 ms |
| Closing submission recording median | 2.651 ms | 2.066 ms |
| Guest vblank lateness median | 0.725 ms | 0.735 ms |

The title source thread used 931/959 sampled CPU ms per wall second in the
traffic/clear windows; the GPU-command thread used 833/839. Both stay busy as
frame throughput changes. On the GPU thread, `UpdateBindings` leaf samples
rose from 43.9 to 53.7 ms per second, `ExecutePacket` from 28.4 to 36.6,
and `RegisterFile::GetRegisterInfo` from 20.0 to 29.6. These are sampling
rates, not additive frame latencies. `DeferredCommandList::Execute` project
caller samples were lower in traffic (115.5 versus 133.6 ms per second), so
it is not supported as the incremental hotspot. The title counter poll still
dominates absolute samples but was already tested with pacing; reducing its
CPU did not improve FPS. Queueing and guest synchronization can make saturated
thread CPU a consequence of slower frames.

A temporary, default-off backend probe omitted only depth-only shader
`5A28C7FAFD86F112` draws without memexport or an active query. The same
RelWithDebInfo binary ran the stationary route once with the probe off and
once on; both exited normally. In the traffic window, median draws fell from
4,810 to 4,303 and median frame time from 21.01 to 20.40 ms. Median guest GPU
time was unchanged at 11.22/11.24 ms. The clear window, which has none of
these draws, also improved from 14.01 to 13.23 ms, so the single-run frame
difference is not a qualified effect. Amplified race-start image differences
cluster around vehicles, lights, and shadows, but ordinary repeat runs also
differ there. The probe deliberately removes guest depth writes, and final
image parity was not proved; it must not ship for this unproven gain. The probe
was removed and the normal RelWithDebInfo preview rebuilt.

The depth family is therefore not a viable traffic fix by deletion. The
multi-material color workload and title-side render preparation remain the
substantial candidates. A race-frame render-target/consumer capture is needed
to classify which color draws are genuinely visible, reflected, shadowed, or
otherwise consumed before changing title culling or native batching.

## RenderDoc race-frame producer and consumer join — 2026-09-22

A signed, portable RenderDoc 1.46 capture triggered just after `race-ready`
produced `.local/cpu-profile/traffic-attribution/race-start-capture_frame4709.rdc`
(SHA-256 `2cccd83b0adebb6e9e96cd0c846986fb6036d415340b93267260f4ca92f59cb7`).
The frame has 5,439 draw actions. The repository's payload-free pass exporter
and resource-usage exporter recorded these ordered producer phases:

| Event range | Draws | Output | Relevant observation |
|---|---:|---|---|
| 214–7,110 | 1,079 | D24S8 depth target `ResourceId::8655` | 448 draws use `5A28C7FAFD86F112` |
| 7,201–13,418 | 1,094 | D32S8 depth target `ResourceId::6980` | 262 draws use the same shader |
| 14,106–15,442 | 197 | Separate 2× MSAA color/depth targets | Material ownership unclassified |
| 15,880–32,745 | 2,579 | 4× MSAA color `ResourceId::2487` and depth `2488` | Main multi-material scene phase |

RenderDoc reports the first depth target as a compute input at events 3,060,
4,474, 6,830, 7,119 and a pixel input in 12 later draws. The second depth
target is a compute input at event 13,380 and a pixel input in 32 draws.
These resource reads prove both depth outputs have downstream consumers; a shader-only skip
cannot establish that the removed geometry is invisible to those consumers.
The main color target is read by 10 later pixel draws after its producer phase.
This is direct evidence that the large traffic color phase feeds later scene
work, rather than a disposable diagnostic pass. Resource usage is a dependency
join, not proof that every individual producer draw changes final pixels.

The capture does not yet identify traffic object ownership, material roles,
blend/order constraints, or the minimum draw set that preserves the final
image. RenderDoc listed `EventGPUDuration`, but returned no per-action results
for this capture, so the in-game pass timestamps remain the GPU timing source.
The next experiment needs a bounded title owner → prepared draw → RenderDoc
event join for the same stationary frames, followed by a paired run of a
semantically safe draw or binding optimization. The depth-skip probe is not
such a candidate. The temporary capture trigger and launcher wrapper were
removed; the normal RelWithDebInfo preview rebuilt.
