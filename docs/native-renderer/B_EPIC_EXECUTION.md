# B epic execution and coverage

Started 2026-09-10 UTC. **B1-B4 remain open.** The retained resource baseline is
[A6](A6_OWNED_DEPTH_RETENTION.md): owned depth clears only at symmetric 1x;
2x uses compatibility. This document fixes the required coverage before choosing
more migrations. A sampled shader inventory is not native resource ownership.

## Required scene set

| Scene | Existing evidence / reproduction | Remaining qualification |
| --- | --- | --- |
| Startup, title and navigation UI | Recaro scripted startup, fresh B1 inventories | Opening movie run, title/UI transition duration and native resource accounting |
| Ordinary open-world driving | Recaro save and A6 fixed stationary/reverse routes | Fresh inventory at both scales; streaming traversal rather than stationary-only proof |
| Recaro Rush entry and racing | Existing owned-depth race route; B1 1x survey | Both-scale inventory; full race, start/end transitions and resource ownership qualification |
| North Carson Outpost / marker 3 | Verified fast-travel route, entrance stationary/reverse views; B1 2x survey | Both-scale inventory, camera turns, sustained candidate comparisons |
| Town plaza / marker 4 | Screenshot and old sampled logs | Exact approach/arrival route and fresh retained-build inventory; Outpost is not a substitute |
| Downtown/residential / markers 1-2 | Screenshots and old sampled logs | Reproduce both urban views and record current dependencies |
| Divided highway / marker 5 | Screenshot and old sampled logs | Repeat high-speed approach, traffic and streaming at both scales |
| Gladstone Canyon junction / marker 6 | Screenshot/sign and old sampled logs | Reproduce approach and turn, inventory and clean tail tests at both scales |

Each scene needs a verified location and motion/camera state, actual binary/settings
identity and retained session evidence. The old 21.8-minute discovery had detailed
inventory overflow; its earlier snapshot cannot stand in for the later locations.
One-in-60-frame surveys miss brief effects; targeted runs must cover those gaps.

## Required pass/resource families

These categories define B1 coverage, independent of which candidate is easiest.
Every observed shader pair must remain in the inventory, including unclassified
pairs, and be joined to a real pass/resource contract before claiming ownership.

| Family | Required producer/consumer contract | Current limitation |
| --- | --- | --- |
| Static world, terrain/road and alpha geometry | Title mesh/stream generation, geometry/material lifetime, scene and depth consumers | Existing native shaders/prepared metadata retain guest bindings and command decoding |
| Skinned/dynamic geometry, vehicles and crowds | All vertex/transform streams, changing constants and materials, depth/color/velocity consumers | Shader parity is not ownership; resource mutation and streaming remain required |
| Shadow/depth/stencil and mixed depth history | Clears, partial writes, aliasing, format/sample changes, queries and depth readers | A6 owns only one 1x clear chain; scaled and other chains remain compatibility |
| Scene color, reflection and render-to-texture | All writers/regions, MSAA changes, resolves, texture sampling and publication | Reused aliased surfaces and partial resolves prohibit pointer-only aliasing |
| Postprocessing, velocity, downsample and final composition | Input versions, filtering/format contract, output ownership and presentation | Native shaders often retain EDRAM publication and texture conversion |
| UI, text and title transitions | Changing geometry/atlases, blend/composition and timing | Must qualify separately from racing screenshots |
| Video | Changing plane uploads, conversion/composition and lifetime | Existing qualified upload/shader work is retained; opening/movie transitions need scene coverage |
| Cross-cutting guest side effects | Queries, fences, memory export, CPU-visible writes, synchronization and resets | Must be inventoried even if absent from one sampled scene; no silent suppression |

B2 investigates measured recurrent imports/conversions using title allocation and
mutation identity. B3 must find actual pre-packet producers; post-decode replacement
alone does not count. B4 compares individual quality controls, then combines only
retained settings and verifies NPC/UI timing. None is closed by this inventory work.

## Resource priorities from existing complete contracts

The following are discovery leads from archived A6 diagnostic captures, not new
retention benchmarks. Costs are whole ordered transfer-list intervals, not first
entries, shader cost, or additive frame-time savings. Refresh them on the retained
build in the required scenes before implementation/retention claims.

| Priority | Chain | Archived ordinary-transfer cost / sampled frame | Next evidence |
| --- | --- | --- | --- |
| 1 | Base-0, pitch-16, 4-sample D24S8 clear intermediate, key `00308000` | Two incoming lists: 0.193434 ms at 1x; 0.777421 ms at 2x, excluding outgoing work/clears | Native zero-clear ownership across color/depth aliases, untouched contents, float-depth history and final publication |
| 2 | Mixed floating-depth consumer, key `00708000` | 0.107622 ms at 1x with A6; 0.421581 ms at 2x compatibility | Independent host-depth history and every per-tile source; cannot flatten into a same-format copy |
| 3 | Scaled resolve texture assembly/conversion | Earlier selected windows about 1.0-1.2 ms GPU conversion/copy | Preserve each partial region and content version at producer/consumer boundary; rejected direct-output/RGBA8 experiments remain rejected |
| Hold | A6 2x owned-clear variant | Failed longer North Carson p99 by 90.09% | New attribution or materially different design required; retain 1x-only guard |

Historical `scaled-rgba-stationary-rdc/frame_frame3055.rdc` now has a complete
metadata usage audit for its active render targets under
`.local/native-renderer/b1/historical-target-usage/`. This is inspection material,
not a capture of the current retained binary.

The base-0 D24S8 target has **45 verified transfer-helper attachment draws**, no
guest geometry draw, four API clears, six unique pixel-stage read events and one
EDRAM dump dispatch. Shader reflection verifies all 45 attachment draws use only
`xe_transfer_*` inputs. Two stencil clears belong to transfer preparation; two
title rectangle clears write **both depth and stencil to zero**, over 160x96 and
80x64 rectangles in the captured 2x target. They do not overwrite the full target.
Evidence: `b1/base0-depth-chain/report.json` and its replay script.

This distinguishes it from A6's depth-only D24S8 owner. It cannot reuse that
admission gate: incoming data includes RGB10 float and independent floating-depth
owners. A native replacement must preserve untouched guest values and explain
host color quantization/history behavior before skipping those transfers. A black
screenshot or captured zero values are not admission rules.

## Discovery pass-count correction

Pass signatures hash attachment state, the ordered draw-family sequence and the
terminal copy state. The recorder incorrectly rejected repeated passes when the
first draw's buffer identity changed, although that identity is outside the pass
signature. This dropped counts and preparation time in otherwise valid families.

`RecordPassLocked` now retains the first identity as a representative and exports
`first_draw_identity_varies`. It still rejects conflicting attachment, first
family, terminal-copy or draw-count metadata. Variant groups are not evidence
that all their bindings or resources are identical.

`tools/check-fh1-family-coverage.py` compiles the production recording functions
and pass-summary definition. The new repeated-pass case fails on the old code;
with the fix it checks accumulated counts/time, explicit identity variation,
real conflict rejection and both inventory capacities. Release build passes.
The renderer DLL remains A6's `27B486...`; the bookkeeping build's actual EXE is
`3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3`.
No renderer performance improvement is claimed from this correction.

Fresh live inventories reconcile after the fix:

| Scene / scale | Before: observed / recorded pass draws | Before collisions | After: observed = pass draws | After collisions |
| --- | --- | --- | --- | --- |
| Recaro race / 1x | 178,366 / 152,147 | 3,671 | 173,972 | 0 |
| North Carson Outpost / 2x | 262,927 / 234,943 | 7,167 | 264,725 | 0 |

Every run exited normally; both Outpost runs pass arrival, stationary and reverse
motion checks. Counts compare accounting *within* each session, not workload or
performance between runs. Instrumented surveys are not clean benchmarks.
Corrected race/Outpost sessions are `20260910T010017Z-p2624` and
`20260910T010348Z-p25812`. Their 305 distinct shader pairs are all retained in
`.local/native-renderer/b1/required-family-inventory.json`, with per-scene counts,
binary hashes and unclassified resource contracts. All other scene gaps remain.
Raw corpus/session/performance data and checks accompany each survey in `b1/`.

## Current-build base-0 contract and tile candidate

Fresh retained-build capture `b1/retained-resource-1x-rdc/frame_frame2812.rdc`
has SHA256 `A1ABDA4D1FA1080429E72649B8AC2A1EA29867DA94A8A0A6BF3AAE1835F859F4`.
It confirms the historical transfer-only pattern: 45 attachment transfer draws,
two transfer stencil-preparation clears, two title clears and seven unique reads.
At 1x, the title clears at events 27794/27948 overwrite depth and stencil with
zero in 80x48/40x32 rectangles. Six outgoing pixel transfers read depth/stencil
into the base-0, pitch-16, single-sample RGB10-float target; event 28003 dumps
the D24S8 data into EDRAM. Immediate dependencies, pipelines, shader reflection,
constants and clear commands are in `b1/retained-base0-depth-chain/` and
`b1/retained-base0-values/`. The candidate publication audit is recorded below.

Both inspected color round trips were unchanged but their sampled color buffers
were entirely zero. Separate source-color and owned-depth positive controls have
nonzero readbacks, confirming readback operation; the zero cases are **not**
value-preservation or admission proof. Do not infer canonical HDR precision or
discard independent history from these values.

The next implementation therefore uses the clear's actual write contract:
`fh1_owned_depth_tile_clear` (default **false**) claims only fully overwritten
tiles before render-target Update. For this base-0/pitch-16 D24S8 chain, the two
rectangles cover 12 and 4 tiles at either symmetric scale. It creates/reuses the
existing D24S8 resource, uses the shared ownership range tracker for those rows,
retains both independent depth histories and every other current owner, then
issues the depth/stencil zero clear. It requests no incoming copies for the
overwritten tiles. Consumers still use existing transfers/dumps for the owned
regions; their actual work reduction remains to be audited.

Admission requires the validated clear shader/pipeline, CPU-authoritative
rectangle vertices, no pixel shader or color writes, both depth/stencil writes,
zero depth and stencil reference, no queries/memexport, exact full-tile coverage,
and symmetric 1x/2x. Partial tiles, other keys, unsupported states and allocation
failure fall back before any ownership change. This is a different design from
A6's rejected 2x depth-only owner redirect; A6's guard stays at 1x.

Production mapping and preparation checks pass, including partial-edge rejection,
wrap/overflow checks, validating all rectangles before any claim, exact disjoint
row claims and allocation failure. Existing ownership lifetime tests still pass.
The preparation check executes the production ownership tracker and compares all
2,048 tiles with an independent flat model, including claims across mixed owners,
padding and both independent history keys. This checks ownership metadata, not
GPU value/history and publication equivalence.

Release candidate DLL SHA256:
`5ED43C5070350557F552413E69BE8D7AA69324EF6C6F764D4F11621D0E45B861`.
Archived as `b1/tile-clear-candidate.dll`, with original touched source snapshots
under `b1/before-tile-clear/`. First 1x gameplay probe
`20260910T013107Z-p9592` exits normally and logs at least 5,120 tile-clear
admissions; its stationary images show the expected scene. The first replay
capture attempt produced no RDC despite the trigger acknowledgment; rerun uses
an absolute capture path. No performance gain or retention is claimed yet.

Remaining candidate gates: complete consumer/value/history/partial-region and
lifetime validation, actual removed-work counts, 1x/2x motion and clean repeated
ordinary/race/Outpost comparisons. Keep the qualified `27B486...` DLL staged
between experiments. B1-B4 remain unchecked.

### Initial capture and 2x triage

The corrected absolute-path capture succeeded:
`b1/tile-clear-1x-rdc2/frame_frame2838.rdc`, session
`20260910T013324Z-p29060`, capture SHA256
`09FD14AC133B7236BC90C239580ACB7ED48A574384D8224E93CDC82BF49A886D`.
The candidate resource audit (`b1/tile-clear-1x-chain/report.json`) confirms:

| Base-0 D24S8 work in captured frame | Retained | Tile candidate |
| --- | ---: | ---: |
| Incoming transfer attachment draws | 45 | 0 |
| Stencil-preparation clears | 2 | 0 |
| Title/native full-tile clears | 2 | 2 |
| Outgoing pixel transfer draws | 6 | 2 |
| EDRAM dump consumer dispatches | 1 | 1 |

The title rectangles and depth/stencil zero values match. Fewer transfers alone
do not prove final output/history equivalence. The D24S8 resource, two outgoing
conversions and dump remain dependencies; this has not retired the entire chain.

Initial four-run 2x ABBA uses current EXE `372161...`, retained DLL `27B486...`
and opt-in candidate `5ED43C...`, ordinary stationary Recaro view. All sessions
exit normally, confirm the same parked vehicle location and expected captures,
have no recorded GPU errors, no competing compiler and zero GPU timing drops.
Only candidate runs record tile admissions. Evidence:
`b1/tile-clear-2x-probe-abba-{a1,b1,b2,a2}/` and its summary/check script.

| Short steady window, 32..44 seconds | Baseline | Candidate | Change |
| --- | ---: | ---: | ---: |
| Median frame time | 17.106 ms | 16.796 ms | -1.81% |
| p95 frame time | 21.377 ms | 19.757 ms | -7.58% |
| p99 frame time | 23.805 ms | 21.730 ms | -8.72% |
| CPU seconds / second, process 34..46 s | 3.185 | 3.141 | -1.38% |
| Private memory | 4722.7 MiB | 4746.0 MiB | +23.3 MiB |

Whole-session GPU averages are 9.218/8.902 ms, explicitly **not** attributed to
the steady frame window: delayed GPU results are not joined to CPU rows.
Recorded draw-call averages also differ by -7.07%; this counter is not a complete
native/compatibility dependency inventory. Short stationary timing and changing
traffic/crowds cannot establish retention or explain every workload difference.
These promising triage results justify the remaining value, motion, 1x and
sustained North Carson tests; they do not qualify the candidate or close B1.

### Nonzero GPU clear and publication audit

The opt-in candidate now passes GPU value checks at symmetric 1x and 2x.
A temporary diagnostic DLL initialized the newly allocated base-0 D24S8 target,
and each intended rectangle before its real clear, to depth 0.25 / stencil A5.
This makes both overwritten samples and untouched guard data observable. It is
capture-only instrumentation, excluded from performance comparisons.

For each of two clears at each scale, all four sample planes were read before
and after the actual clear. Every interior sample starts at packed `A5400000`
and ends at zero. Every outside byte remains identical, with nonzero outside
guard values verified. Each complete plane covers 2,621,440 bytes at 1x or
10,485,760 bytes at 2x; all eight checks per scale pass.

The independent consumer model uses actual transfer vertices, viewport/scissor,
tile/sample addressing and depth/color half-row exchange. Both outgoing pixel
transfers read only cleared values, write the expected colors and preserve every
other output byte. The dump model independently reproduces all 1,280 / 5,120
sample writes to EDRAM at 1x / 2x and checks the entire before/after buffer.
No differences remain in either scale's consumer check.

Final texture publication also passes: the subsequent RGB7e3A2 EDRAM-to-RGB10A2
resolve uses exponent bias -2, endian conversion and Xbox tiled addressing.
The model checks all 6,144 / 24,576 destination pixels, including 3,840 / 15,360
nonzero source pixels, plus unchanged bytes outside the modeled writes. The 2x
shader binds a relative destination UAV window; the exporter checks that actual
descriptor offset/range rather than assuming the 1x constant-buffer layout.
No intermediate EDRAM writer occurs between the audited dump and final resolve.

Evidence under `.local/native-renderer/b1/`:

- `tile-clear-seeded-{1x,2x}-audit/`: raw sample planes, consumer before/after
  buffers, pipeline inventory, shader disassembly, constants and checks.
- `check-tile-clear-consumers.py`: independent pixel-transfer and dump check.
- `tile-clear-seeded-{1x,2x}-publication/`,
  `check-tile-clear-publication.py`, `tile-clear-publication-check.json`:
  independent final publication check, both scales passing.
- 1x capture `tile-clear-seeded-1x-rdc/frame_frame2743.rdc`, session
  `20260910T015003Z-p17920`, SHA256
  `185748F2B3B2CBCD12B9DE896A90F40C17B6BC24BFB1504BAFF741A7D0E78475`.
- 2x capture `tile-clear-seeded-2x-rdc/frame_frame2778.rdc`, session
  `20260910T015054Z-p2380`, SHA256
  `AB912679F2ED34D930B35EA64708305A41254ABC55F7ABEC874CA38A3B334C8D`.
- Diagnostic DLL `81988EF1DE7C4DEE7F9214C68673C0BFD45314BEA835C9EF338EF49707362867`,
  archived source/patch and build log. Both runs exit normally. The exact
  unseeded production source was restored before captures; its SHA256 is
  `94DC2518AFA5B460C77F771F854D8C8214368C59CF91ABA38FBA0467D1DA56DA`.

This establishes the clear and immediate publication chain with nonzero guards;
it does not establish every other mixed floating-depth history, scene, streaming
or reset case. Production remains default-off. Clean sustained motion/tail tests
and candidate lifetime qualification remain required before retention. Qualified
DLL `27B486...` was restored to both runtime paths after the diagnostic runs.

### Sustained 2x Outpost comparison: invalid workload match, do not retain

Four clean runs of the 170-second North Carson route completed using EXE
`372161...`, retained DLL `27B486...` and unseeded candidate `5ED43C...` with
only the tile-clear flag enabled in B. Every run verifies arrival at the same
Outpost pose, no movement before the measurement and subsequent reverse motion.
No competing compiler/capture process, GPU error or GPU timing drop was recorded.
Subsequent image review found A2 had hidden its HUD/prompt by the stationary
capture; the other three retained them. The block is therefore unsuitable for
a matched performance claim. Pose checks alone were insufficient.
Both B runs reach 18,432 native tile clears; both A runs have zero.

| Run / session | Median ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: |
| A1 / `20260910T020457Z-p30264` | 21.381 | 34.085 | 90.985 |
| B1 / `20260910T020817Z-p27116` | 21.407 | 37.671 | 59.923 |
| B2 / `20260910T021139Z-p18484` | 21.358 | 37.103 | 59.728 |
| A2 / `20260910T021501Z-p28208` | 20.920 | 25.156 | 30.195 |

The preselected 62..148-second frame window averages per-run median/p95/p99:
21.151/29.621/60.590 ms baseline versus 21.383/37.387/59.826 ms candidate.
Changes are **+1.10% median, +26.22% p95, -1.26% p99**. Process CPU is
3.428/3.431 CPU seconds per second (+0.075%); private memory is
4971.2/4969.1 MiB (-2.2 MiB). Whole-session GPU time is 14.836/14.527 ms
(-2.08%), not attributed to that steady CPU window. Texture CPU timing was
disabled for clean runs and is reported unavailable, not zero cost.

Steady simulation-time/wall ratios are 0.99996..1.00007 with zero invalid
simulation deltas. This does not prove NPC clip or UI-transition timing.
Recorded draw averages differ by +2.02%; changing crowd/traffic work and baseline
tail variability limit causal attribution. Both candidate p95 values exceed both
baselines, but the HUD mismatch invalidates interpreting +26.22% as a proven
renderer regression. **Do not retain or enable the candidate from this block.**
Preserve the raw result; first control and validate HUD/activity state before
another comparison. A changed route must qualify its scene/motion again.
Simply repeating the unchanged route to obtain favorable timing is not valid.
Separate 1x qualification remains open.

Evidence: `.local/native-renderer/b1/tile-clear-2x-outpost-long-abba-{a1,b1,b2,a2}/`,
`tile-clear-outpost-long-abba.ps1`, `summarize-tile-clear-outpost-long.py` and
`tile-clear-2x-outpost-long-abba-summary.json`. Raw/scoped logs, CSV, direct hashes,
process samples and arrival checks accompany each run. Qualified DLL `27B486...`
was restored to both runtime paths. B1-B4 remain open.

The HUD is present in A2's arrival and reverse-motion images and absent in its
stationary image. This is consistent with inactivity hiding, but its cause and
rate dependence remain unproved. `tools/check-fh1-outpost-workload.py` now checks
pose/motion plus the speedometer's pink region in all three captures. It passes
A1/B1/B2 and rejects A2 (stationary pink fraction 0 versus approximately 0.057).
The check is intentionally limited to this known route and complements visual
review; it does not prove the HUD was continuously visible between captures.
`tile-clear-outpost-hud-contact.png` preserves the four-image comparison. The
numerical table above is retained as rejected comparison evidence, not a gain or
regression attributed to the renderer. A6's existing retention rules are unchanged.

### Tile ownership lifetime and race-start checks

`tools/check-fh1-owned-lifetime.py` now additionally runs the production ClearCache
and full-tile preparation against mixed ownership/history, checks that live tile
owners survive eviction, then destroys all targets and prepares the same key
again with empty surrounding ownership and histories. The production-body test
passes. Updated test SHA256:
`a437643ecead63e5e049c6aa48be5ffce5c3077fcb7b3a7e995c9da2e7cd47d0`.

A temporary diagnostic build requests the supported live ClearCaches path at tile
clear counts 1,024 and 2,048, waits through the normal queue-completion boundary,
and logs eviction completion. Both requests occur before `event-ready`; native
admissions then continue through the race start and driving portion. The runs
cover eviction followed by race transitions, not an arbitrary device reset.

| Scale / session | Completed eviction frames | Later tile-clear count | Simulation / active wall |
| --- | --- | ---: | ---: |
| 1x / `20260910T021939Z-p6920` | 1076, 1588 | 7168 | 1.001367 |
| 2x / `20260910T022100Z-p29660` | 1010, 1522 | 7168 | 0.999764 |

Both exit normally, pass request/completion ordering, race HUD and motion checks,
and record no GPU error. Moving images show the race at 85 km/h with track,
vehicles, crowd, shadows and HUD intact. These instrumented runs are correctness
probes, not clean performance measurements or full-race completion evidence.

Fixture DLL `7646373297C5BB037BEBDB478C4DAD8F5C27BB89DBB8ACED4CEE52AFF16303AE`;
source/patch/build/launch/check scripts and outputs are under
`.local/native-renderer/b1/tile-clear-*eviction*`. Both modified production source
files were restored byte-for-byte before launch and every production candidate
source hash still matches `tile-clear-source-manifest.json`. Qualified DLL
`27B486...` was restored to both runtime paths afterward.

### Initial 1x triage: not retained

The separate unseeded 1x ABBA also exits normally with the expected Recaro pose
and visible HUD in the inspected end images. Current EXE `372161...`, A DLL
`27B486...`, B DLL `5ED43C...` plus tile-clear flag. No GPU error, timing loss or
competing compiler; admissions occur only in B. Per-run medians are
13.121/16.273/16.653/15.685 ms in ABBA order. Their averaged comparison is:

- Median 14.403 -> 16.463 ms (+14.30%); p95 +5.65%; p99 +4.02%.
- CPU 3.166 -> 3.065 seconds/second (-3.20%); private memory +10.9 MiB.
- Recorded draws 3251.7 -> 3679.3 (+13.15%); whole-session GPU +1.00%.

The draw-workload difference and short sample prevent attributing that entire
frame-time difference to the clear. Nevertheless the result does not support
retention. Preserve it and investigate the changed work/cost before expanding
this design or retrying it. Tile clear remains default-off at both scales.
Evidence: `tile-clear-1x-probe-abba-{a1,b1,b2,a2}/`, its summary and
`tile-clear-1x-probe-contact.png`. Remaining B1 chains/scene inventory and B2-B4
still require implementation and qualification; this candidate's audits and
rejected comparisons do not close those items.

### B2: geometry allocation churn and bounded storage recycling

Status, 2026-09-10 UTC: **implemented and tested, default-off, not retained**.
The diagnostic Outpost run `20260910T023652Z-p10212` reaches 17,000 creations,
16,644 evictions and 3,462 budget/fence rejections at its last periodic record.
It imports 1,883,766,784 bytes. CPU allocation/preparation records 8.061 seconds
and import recording 2.766 seconds across startup, travel and driving. These
instrumented totals are attribution, not clean benchmark or GPU execution time.
Allocation timing includes eviction and destruction. The 32 MiB cache then holds
20,840,448 unique guest bytes and 14,352,384 snapshot bytes. Only 175 of 11,375
snapshot imports match their previous snapshot, accounting for 12,320,768 bytes;
unchanged-snapshot suppression is therefore not the first opportunity.

The candidate reuses an evicted D3D12 buffer only when the existing oldest-victim
policy selects it, its last submission has completed, and its byte extent and
allocation size exactly match the new guest window. It preserves the resource
state, discards the old watch/snapshot/bounds, and executes the ordinary complete
window import and binding path. The same 32 MiB / 512-entry limits apply. There
is no additional pool, larger budget, containment lookup or new eviction order.
`fh1_recycle_geometry_buffers` defaults to false; tile clear also stays disabled.

`tools/check-fh1-geometry-cache.py` passes production-body checks for in-flight
exclusion, both feature settings, full nonzero byte replacement, partial writes,
old-watch removal, new-watch notification, stale-bound removal, prior-state
transition, mismatched sizes, allocation failure, budget and destruction. The
Release DLL builds. Candidate SHA256:
`8AF0207FE28A2D5FC26F2E45205B9DB13F55FA7EA79DCAEA854027D67C41011F`.
EXE remains `3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3`.

The 2x ABBA uses that same DLL with recycling off/on. All runs exit normally,
reach the Outpost, retain the HUD in all three checked images and pass basic
pose/movement checks. No GPU errors, timing losses or competing builds occur.
CPU frame-clock windows exclude captures; asynchronous GPU totals span the
entire session. Counts below stop at the last periodic log, not shutdown.

| Run / session | Actual allocations | Recycles | Stationary p99 ms | Reverse p99 ms |
| --- | ---: | ---: | ---: | ---: |
| A1 / `20260910T024727Z-p21072` | 13,378 | 0 | 83.304 | 39.222 |
| B1 / `20260910T024926Z-p27116` | 4,873 | 3,373 | 36.110 | 88.725 |
| B2 / `20260910T025126Z-p1616` | 10,170 | 6,895 | 75.417 | 109.218 |
| A2 / `20260910T025326Z-p18660` | 9,504 | 0 | 72.062 | 117.761 |

Candidate recycles directly avoid 40.90% / 40.40% of observed new-window
allocations. Different total requests prohibit attributing the raw A/B allocation
count difference entirely to recycling. Averaged stationary (62..83 s) median,
p95 and p99 change -4.62%, -18.39% and -28.22%; draws differ -2.78%. Reverse
(91..98 s) changes +3.69%, +32.81% and +26.09%; draws differ +0.35%. Whole-session
GPU changes +0.77%, process CPU -0.35%, steady private memory -2.06 MiB and peak
private memory -2.98 MiB. Simulation/wall ratios are 0.99941..1.00107 with no
invalid deltas; this does not establish NPC/UI timing.

**This block does not establish retention.** Reverse tails are unfavorable and
variable. Visual review also finds the car/camera contacting roadside objects
after the long reverse; the stopped B1 view differs substantially and A2 shows
a bright respawn-like effect. Braking-window timing is not a matched-workload
claim. Basic endpoint-distance/HUD checks cannot certify collisions, camera
state or continuous motion. Preserve the raw block, validate actual recycled
GPU contents and attribute the spikes before another performance comparison.
A revised route must avoid the obstruction and qualify its motion explicitly;
do not repeat unchanged tests to seek a favorable result.

Evidence under `.local/native-renderer/b2/`: `geometry-profile-*`,
`before-recycling/`, `geometry-recycling-candidate.dll`,
`geometry-recycling-{2x-abba-a1,2x-abba-b1,2x-abba-b2,2x-abba-a2}/`,
`geometry-recycling-2x-abba-summary.json`, `summarize-recycling.py`,
`geometry-recycling-2x-abba-contact.png` and the build/launch scripts.
Qualified A6 DLL `27B486...` is restored after the comparison. B1-B4 remain open.

#### GPU copy and cost attribution follow-up

Diagnostic DLL `C51CDA81BD1EEE56232A2F4A6E3B5AE31016DDF2C36FCAEC8A9C3905868FBDE4`
adds a marker only around actual recycled-buffer imports. The normal 2x run
PID 27880 records `recycling-capture-2x-rdc/frame_frame5995.rdc` (SHA256
`9DB23D700919A7AEEDDC22A8379376C9572B2AF5C46C82E2FC7F9E32C48388D3`).
Its one recycled copy replaces every byte of a 131,072-byte resource from a
nonzero CPU upload; destination bytes differ before the copy and match the
actual upload source afterward. The recorded retired/completed/current
submissions are 19405/19407/19409. At the first VS consumer, event 941, the
bound resource still contains exactly those imported bytes. Resource identity,
copy arguments, hashes and both subsequent VS usage events are inventoried in
`recycling-capture-2x-audit/report.json`; value readback covers the first consumer.
This is a bounded 128 KiB GPU proof, not coverage of every size or source type.
Production source is restored byte-for-byte after building the diagnostic.

The separate per-frame CPU diagnostic DLL
`C6C2259F10CA4716C591FF047DEB6F470F6236F253E29E0C566279E4D86B9153`
times resource creation, eviction and import recording independently. Baseline
session `20260910T030426Z-p27104` reaches the Outpost. Its stationary window
creates 2,346 buffers; creation/eviction/import consume 0.733/0.464/0.046 seconds
over 20.931 seconds of recorded geometry-frame intervals. The slowest 80.009 ms
interval spends 26.633/14.052/0.944 ms in those operations, with 93 creations.
The reverse window accounts for 0.538/0.328/0.028 seconds over 6.973 seconds;
one 75.778 ms interval spends 33.917 ms in the three operations. This establishes
substantial synchronous CPU cost in observed spikes. These are instrumented
geometry-first-call intervals, not clean frame/GPU measurements. Capture-clock
anchors have 10 ms spread; no asynchronous GPU/CSV pairing is used.

The intended paired candidate session `20260910T030626Z-p26504` **fails arrival**:
the game refuses the 10,000 CR fare because only 1,076 CR remain. Its images show
the insufficient-credits dialog and map; it is excluded from phase attribution.
`summarize-recycling-cost.py` explicitly records this rejection and an incomplete
pair. Do not repeat paid Outpost launches until normal gameplay replenishes the
balance, or a free driving approach is established. Saves are not manipulated.
Free local driving and race work remain available; this does not block all B work.

The shortened Outpost reverse route and probe are prepared but **not run**;
they must qualify arrival, motion, camera and obstruction avoidance after travel
becomes available. Current production source/test hashes and minimal diffs are
in `geometry-recycling-source-manifest.json` and `geometry-recycling-source/`.

#### Free local 1x/2x comparison: no retention

`geometry-recycling-local.fh1test` starts at Recaro, holds the initial view,
accelerates for six seconds and brakes on the clear road. Both ABBA blocks use
DLL `8AF020...`, recycling off/on, tile ownership off and the existing A6 defaults.
All eight runs exit normally, pass arrival/movement/HUD checks, and have zero GPU
errors, timing drops or invalid simulation deltas. Image review shows intact
road, car, crowd and HUD with the car moving at 36 km/h. Cross-run moving-pose
spread is at most 0.64 m (1x) / 0.23 m (2x), stopped spread 1.07 m / 0.80 m.
Traffic/crowd state and draw counts still vary; matching endpoints does not make
every frame identical. The route covers short ordinary motion, not sustained
streaming, a full race or a replacement for North Carson pressure tests.

| Scale / CPU frame-clock phase | Median change | p95 change | p99 change | Draw-count change |
| --- | ---: | ---: | ---: | ---: |
| 1x stationary, 32..41 s | +0.82% | +1.51% | +3.08% | +1.60% |
| 1x accelerating, 46..48 s | -11.97% | -17.45% | -25.40% | -4.86% |
| 1x braking, 52..57 s | -6.70% | -2.78% | -0.99% | -2.17% |
| 2x stationary, 32..41 s | -1.85% | -3.32% | -16.13% | -6.25% |
| 2x accelerating, 46..48 s | -1.33% | -4.56% | -4.95% | -2.79% |
| 2x braking, 52..57 s | +3.16% | +9.01% | +13.28% | +5.36% |

At 1x, candidate runs record only 13/10 recycles (3.33%/2.56% of observed
new-window requests). At 2x they record 31/26 (7.13%/6.47%). Whole-session GPU
changes -0.41%/-0.86% at 1x/2x and process CPU +0.37%/-0.24%. Steady private
memory changes +1.74/-28.82 MiB, peak private +7.92/-15.05 MiB. These low-churn,
short windows and varying workload do not support attributing the large positive
or negative tail percentages to recycling. In particular, the 2x braking result
does not pass a straightforward no-regression gate. **Keep recycling off.**
Do not repeat the same short blocks to seek a favorable outcome; first measure
activation and cost in representative sustained motion or improve the design.

Sessions in ABBA order: 1x `20260910T031734Z-p18940`, `20260910T031843Z-p19212`,
`20260910T031952Z-p2328`, `20260910T032101Z-p29744`; 2x
`20260910T031147Z-p26860`, `20260910T031405Z-p14672`, `20260910T031515Z-p7536`,
`20260910T031624Z-p28140`. Raw files, summaries and contact sheets are under
`.local/native-renderer/b2/geometry-recycling-local-*`; the summarizer preserves
per-run timings, workloads, memory and measurement scope. Qualified `27B486...`
is restored to both runtime paths afterward; no game remains running.

#### A concrete constraint on the next geometry design

The older same-base containment experiment selected the **largest** containing
window. A new production-body probe reproduces a held-owner inconsistency:
import a small index window containing byte 7, retain its GPU address, modify
guest byte 64 to 9, then import a larger same-base window. The held GPU buffer
still contains 7, but the historical largest-window CPU lookup returns 9 from
the new buffer. This violates the intended association between a held geometry
address and its immutable CPU snapshot. It does not by itself demonstrate a
particular visible game defect or invalidate the unrelated recycling candidate.

The current exact-key implementation preserves that association. An isolated
smallest-containing lookup (`lower_bound` at requested base/size) also preserves
it in this probe: inserting a larger window cannot displace the selected smaller
owner. A bound owner cannot be evicted before its submission completes. This is
a materially different selection rule to investigate if overlapping windows are
addressed next; do not re-enable the historical largest-window implementation.
No containment change is made to production in this step. Full lookup/lifetime,
aliased import/bounds, live GPU and performance validation remain required.

Reproduce the three-policy identity probe with
`.local/toolchain/python-3.13.15/python.exe .local/native-renderer/b2/check-containment-owner-stability.py`.
It reuses the existing fake-GPU shell and actual production/historical cache
methods; only the injected held-owner scenario runs. `containment-owner-stability.json`
records the expected mismatch for the historical policy and matching results for
exact/smallest. This is not a claim that the full cache suite or GPU qualification
has passed for smallest containment. B1-B4 remain open and the goal stays active.

### B2 stable containment candidate (2026-09-10 UTC)

`fh1_contain_geometry_windows` is a new **default-off, restart-required** candidate.
An ordered map selects the smallest existing window at the same 64 KiB guest
base that contains the request. Exact mode uses exact-key lookup in the same
map. A later larger insertion cannot displace the selected owner; smaller
requests already reuse it, and its submission tag prevents premature eviction.
Every CPU snapshot/bounds helper uses this same lookup. Watches, imports and
snapshots cover the entire selected owner, including bytes outside a nested
request. The 32 MiB / 512-entry budget, normal imports, shared fallback and
completion-fence rules remain. Recycling and tile ownership stay independently
disabled during this candidate's runs. Changing the map also changes exact-mode
lookup/tie traversal costs; eventual retention must compare with the qualified
build as well as same-binary containment off/on.

The full `tools/check-fh1-geometry-cache.py` suite passes in both exact and
contained modes. Added cases cover held GPU/CPU owner identity after a larger
import, snapshot upgrade, writes outside a nested request, GPU-source fallback,
CPU re-import, bounds invalidation, different-base exclusion, nested-use fence
protection, eviction and same-range recreation. Existing depth/terrain/skinned
binding, partial-write, import failure, recycling and budget checks run in both
modes. Release DLL builds with SHA256
`15FB392A7D16828371443A38BDBFBBD0D4C0E90DE12ADED79D51EA38340201DF`;
EXE remains `372161...`. Source/test snapshots and minimal diffs are in
`.local/native-renderer/b2/stable-containment-source/` and its manifest.

The first free local 2x probe (`20260910T033336Z-p27864`) exits normally,
passes route/HUD checks and shows
intact stationary/driving/stopped images. At its last periodic record it has
328 allocations, 3,008 imports, 220,004,352 imported bytes, 504,031 contained
uses and 31,457,280 allocated bytes. A contained use is **not** an avoided import;
many calls would have been hits on separate exact-key windows. This single probe
does not establish a performance or memory reduction. It is not an ABBA block.

GPU qualification is underway using a temporary fixture that labels allocation
generations and fingerprints each actual CPU import without changing snapshot
admission. Contained-use markers carry that immutable import fingerprint, so
checks can compare captured GPU data with its actual import even when current
guest shared memory is stale. Actual GPU-source copies are checked against their
copy source; unknown pre-capture GPU-only versions must remain explicit.
The fixture is diagnostic and must not supply clean performance measurements.
Candidate containment remains disabled pending live/GPU/lifetime and retention
qualification. All B items remain open.


#### Stable containment GPU checks and startup control

The source checkpoint is [2026-09-10](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md).
The 1x diagnostic session `20260910T033738Z-p27296` completes the free local
route with intact stationary/moving/stopped images. Frames 2563/2905 each
validate 13 nonzero owners (1,900,544 bytes), 16 representative index/VS
consumers, and one actual 65,536-byte copy. Owner/consumer validation uses the
fingerprint of the actual CPU import; actual copy source/destination bytes are
also compared directly. All match, with zero unverified contained versions.
The 13 owner versions are unchanged between frames: live mutation/streaming
qualification is still required. Raw audits are
`b2/containment-capture-1x-frame{2563,2905}-audit/report.json`; frame SHA256s are
`66D6E41AC0E2F9417BDAE1AC6F468409EDD5672B14C6211DBEC64F4491BA2969`
and `80E084A03A479DFE1160F27063BA2F31C246D198D9957BDB366A798CC1A19994`.

The 2x diagnostic candidate session `20260910T034013Z-p16692` times out after
an unhandled guest null read at `0x00000004`, before the first capture trigger.
The subsequent instrumented feature-off control `20260910T035134Z-p24740`
also times out at 180 seconds without captures or route completion, but has no
corresponding logged access violation. Preserve both failures; neither proves
2x correctness, and their different symptoms do not establish the same cause.
The local control wrapper correctly rejects the missing child normal-exit
result despite RenderDoc's exit 0. Both runtime paths are restored to `27B486...`.

The actual production-body cache suite passes again. An isolated negative
control replaces the smallest-owner lookup with the historical largest-owner
selection and fails precisely at the held-owner CPU snapshot assertion.
Production source stays unchanged; see `b2/check-stable-containment-negative.*`.
The earlier `check-containment-owner-stability.py` is historical evidence tied
to the earlier harness layout; use the current production cache suite when
resuming. No B experiment is retained. All B1-B4 requirements remain open.


#### Revised 2x capture fixture and incomplete retention block

The original `DAD406...` instrumentation completes the 2x free local route
without RenderDoc injection, containment off (`20260910T040450Z-p12616`).
The retained `27B486...` DLL also completes a 2x RenderDoc control with two
captures (`20260910T040638Z-p29364`). These controls narrow the investigation;
they do not establish the cause of the original null read or separate timeout.
Thread-stack sampling is diagnostic, so these runs are not clean benchmarks.

A revised capture-only fixture fingerprints cached CPU bytes instead of reading
mapped upload memory byte by byte. It uses the existing CPU snapshot when
available; otherwise it copies guest bytes through a temporary CPU vector before
upload. It does not force persistent CPU snapshots or change cache admission.
The actual production-body suite also passes with this fixture. The diagnostic
DLL is `0D7577CB79E5B683EE9F7D266FB56EA8E31D49A53D302AACBFD3D3EF147437E3`.
Instrumentation is removed afterward; production source still matches the
`15FB392...` candidate. This is no measured performance gain or proven root-cause
fix for the earlier startup failures.

The revised 2x session `20260910T041226Z-p10576` completes normally with intact
car, road, crowd and HUD during short local driving. No access violation is
logged. Both GPU audits pass:

| Frame | Checked owners / bytes | Representative IB/VS consumers | Actual copies |
| --- | --- | ---: | --- |
| 2674 | 18 / 2,686,976 | 24 | 1 / 65,536 bytes |
| 3032 | 19 / 2,883,584 | 25 | 1 / 65,536 bytes |

All checked values match, with zero unverified contained versions. Owners and
representative consumers match import fingerprints; actual copy source and
destination bytes compare directly. The 18 shared owners have unchanged size
and fingerprint; frame 3032 adds owner serial 318. This is bounded GPU evidence,
not live mutation/streaming or every-consumer qualification. Frame SHA256s are
`9435ECBC34732C294F6CB2848D394A64424D364AA3284D2C8B5B0255872876FC`
and `2FBAAF5EA710519BF1B4D0407FEC503A16B62B3F756DCF8C0F9B99D63510ACAC`.
Audits, cross-frame comparison, screenshots and controls remain under
`.local/native-renderer/b2/containment-cached-capture-2x-*` and
`retained-capture-2x-startup-control-rdc/`. Reproduce the evidence summary with
`b2/summarize-containment-checkpoint.py` under the local native-renderer directory.

The preselected longer clean comparison uses the same `15FB392...` DLL with
containment off/on, recycling/tile ownership off, and stationary, accelerating,
braking and settled windows. **The 1x ABBA block is rejected and incomplete.**
A1 (`20260910T041653Z-p30028`) and B1 (`20260910T041828Z-p24996`) pass the
route checks. B2 (`20260910T042002Z-p23720`) exits normally but moves 20.03 m
between its 30-second start image and 63-second stationary image, before planned
acceleration at 65 seconds. The images also show this displacement; its cause
is unproven. All three runs have no recorded compiler/replay contention.

The runner stops at that failed workload gate. A2 and the entire 2x block are
not run; no matched ABBA performance percentages or retention verdict are
published. Preserve `b2/stable-containment-long-local-incomplete.json`, the plan,
scoped logs, images and process samples. Do not repeat the unchanged route until
favorable: first qualify a stationary brake hold or a clear parked position.
This proposed route adjustment has not yet been tested. Qualified `27B486...`
is restored at both paths, with no game or replay running.

### B3 static guest producer anchor (2026-09-10 UTC)

The exact 108-byte vertex microcode for the known clear shader
`1E6883FCCDE1F688` has a unique word-endian-adjusted match at guest address
`0x820C5FD0`. The local `default-image.bin` is a loaded-image extraction:
addresses use `0x82000000 + offset`, not PE raw-section relocation. An initial
raw-PE address guess is discarded; the instruction bytes and generated code
confirm the addresses below.

`sub_8240E130` constructs the clear command stream. At `0x8240E480..0x8240E4A4`
it selects the shader blob at `0x820C5FA8`, vertex code at +40, and byte count
108, then prepares `IM_LOAD_IMMEDIATE` (`0xC01C2B00`, 27 shader dwords).
The call at `0x8240E4A8` copies those exact bytes through `sub_82A7D730` into
the guest command buffer. A direct caller is `sub_824018B0`, with its call at
`0x824019D0`. The producer has a common epilogue at `0x8240E7A4` and calls
`sub_82407C08` for rectangle work, which in turn calls `sub_82460C50`.
The latter helper still needs a complete packet/side-effect trace.

This is an actual upstream producer anchor, but **no bypass or measured CPU
saving exists yet**. The function clips rectangles, handles colour/depth paths,
refills/flushes the command buffer, updates device dirty state and restores
scissors. Device cursor +48 and end +56 may change through refill/flush;
subtracting entry/exit cursor values is not a valid general emitted-byte count.
Do not skip the function based solely on the shader match. Next, use read-only
producer observation to establish live call frequency/cost and the full contract,
then bypass only proven obsolete emission while preserving state, ordering,
queries, fences, memory export and guest-visible behavior.

Local reproducible evidence is `b3/check-clear-producer-anchor.py` and its JSON
report; it checks the unique shader match, loaded-image instructions and both
relative branch targets. Guest image/generated-code excerpts remain local.
All B1-B4 completion criteria remain open; neither this anchor nor a rejected
B2 comparison completes an item.


### B3 live clear-producer attribution (2026-09-10 UTC)

Default-off, restart-required `pinyon_shift_fh1_clear_producer_trace` observes
entry `0x8240E130`, common epilogue `0x8240E7A4`, the two shader copy callsites
`0x8240E4A8` / `0x8240E4F4`, and command-buffer refill entry `0x8240CF68`.
It reads registers without changing guest state or emitting/suppressing packets.
Elapsed wall time excludes entry setup and the final log write; inner hook cost,
scheduling and refill work remain included. Nesting, mismatched pairs and the
100,000-record cap are explicit. This is diagnostic attribution, not a clean
benchmark, CPU-cycle measurement or a downstream GPU-decode measurement.

Release trace EXE SHA256 is
`B3CF0B7AFE63FB8FE50FF0DF9131712AC8B3080F69835566D82E229C47D0AACE`.
It runs with retained renderer `27B486...` and unchanged runtime DLL
`955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500`.
The original EXE `372161...` and all staged DLLs are backed up and restored.
The production-body trace check passes disabled observation, register
non-mutation, nested accounting, thread isolation, mismatches and record limits:
`tools/check-fh1-clear-producer-trace.py --compiler <clang++>`.

The 1x session `20260910T044707Z-p12388` exits normally. The 2x session
`20260910T044922Z-p29968` completes the route and logs process shutdown, but its
wrapper initially matches an older session with reused PID 29968 and throws
before preserving the launcher result. The exact current session is recovered
from its capture output path. Its OS exit code remains **unrecorded**, not
assumed zero. The wrapper now saves launch results before archiving and excludes
pre-existing session files. No repeat run is used to replace this evidence.
Both runs pass arrival/pose/HUD checks; contact-sheet review shows intact car,
road, crowd and HUD while driving at 36 km/h.

| Scale / phase | Source frames | Total producer median / p95 / p99 per frame (ms) |
| --- | ---: | --- |
| 1x stationary, 32..41 s | 425 | 0.03580 / 0.17578 / 0.26738 |
| 1x accelerating, 46..48 s | 123 | 0.02990 / 0.04246 / 0.04985 |
| 1x braking, 52..57 s | 252 | 0.03795 / 0.05077 / 0.13555 |
| 2x stationary, 32..41 s | 449 | 0.03460 / 0.05126 / 0.08689 |
| 2x accelerating, 46..48 s | 89 | 0.03940 / 0.05458 / 0.23095 |
| 2x braking, 52..57 s | 192 | 0.04505 / 0.06761 / 0.27842 |

There are 45,103 / 42,350 complete records, one observed producer thread and
60 / 47 refill calls at 1x/2x. No unmatched/nested records or cap exhaustion
occur. Each producer invocation copies 108 + 36 shader bytes; gameplay has
15 invocations per source frame at the median. Complete groups inside each
phase have no missing source-frame IDs. Capture-clock anchor spread is 17 / 54
ms; phase summaries use whole groups within the boundaries and do not join
asynchronous GPU samples. Raw logs, images, identities, the recovered-exit
limitation and summary are under `.local/native-renderer/b3/producer-trace-*`;
reproduce the summary with `b3/summarize-producer-trace.py`.

The typical measured producer contribution is small in this free local scene.
Do not prioritize a complex clear-producer rewrite on the assumption that it
will remove milliseconds of CPU work. GPU decoding is still unmeasured here,
and this does not close B3: an actual safe pre-packet bypass is still required.
A pointer-based shader load cannot directly reference `0x820C5FD0`, because the
image uses a virtual XEX heap whereas `PM4_IM_LOAD` reads physical memory.
Do not substitute a masked image address. Any such design needs a proven mirror
and lifetime contract; return first to higher measured preparation costs.


### B2 handbrake workload and first qualified-DLL controls (2026-09-10 UTC)

The first stationary-route adjustment held the left trigger from rest. Retained
control `20260910T045723Z-p7324` completes but fails every position gate:
screenshots show reverse gear at 54/59 km/h. Holding that trigger engages reverse;
it is not a stationary brake hold. The wrapper stops before candidate runs.
Keep the failed route/results under `b2/stable-containment-braked-local-*`.

A changed route holds A (handbrake) from 27 seconds until the planned 65-second
acceleration. The preselected 1x C-A-B-B-A-C block completes with all six normal
exits and automated arrival/stationary/motion/HUD checks. C uses qualified
`27B486...`; A/B use `15FB392...` with containment off/on, recycling and tile
ownership off. All use EXE `372161...`. No compiler/replay contention, GPU errors
or timing drops are recorded. The selected CPU phases have zero invalid
simulation deltas. Start/stationary pose spread is below 0.001 m, moving spread
0.61 m, stopped spread 1.28 m. Images show intact car/road/crowd and 34-35 km/h
motion, but **passing traffic differs**: A1 has nearby vehicles in stationary,
moving and stopped images, including partial HUD occlusion in the last image.
Thus matching the player pose does not establish a matched traffic workload.

| 1x phase / CPU frame clock | B vs A median / p95 / p99 | B vs C median / p95 / p99 | B vs A draw-count change |
| --- | --- | --- | ---: |
| Stationary, 32..61 s | +1.25% / +0.91% / +1.17% | +4.24% / -0.30% / -0.67% | +1.65% |
| Accelerating, 66..68 s | -4.38% / -4.44% / -5.02% | +9.77% / +1.51% / +0.55% | -6.00% |
| Braking, 72..77 s | +0.45% / +0.02% / +0.06% | +0.16% / -0.22% / -11.71% | +1.25% |
| Settled, 80..88 s | +8.02% / +4.63% / +8.64% | -0.79% / +1.27% / -3.06% | +2.52% |

These are descriptive results, not isolated causal gains/regressions. Compared
with A, B whole-session GPU time rises 2.02%, process CPU falls 1.47%, steady
private memory rises 14.21 MiB and peak private memory rises 18.37 MiB.
At the last periodic record (all A/B runs have 14,155,776 cache hits), mean
allocations rise from 397 to 447.5, imports from 4,934.5 to 5,430, and imported
bytes from 340,328,448 to 402,128,896. Stationary import rates are approximately
69.4/s for A and 70.3/s for B. Candidate contained-use counts 714,780/829,423
are not avoided imports. This does not demonstrate reduced recurring work.
Memory/CPU clocks and whole-session asynchronous GPU totals retain separate
scope; no GPU sample is paired naively with a CPU row.

**No retention.** The ordered-map exact path also has mixed differences against
C; flag-off source has not earned equivalence to the retained DLL. The planned
2x free-road block is deferred after this workload/work-reduction review;
there is no 2x containment performance verdict. Preserve all six runs and do
not repeat the same free-road block for a more favorable result. The handbrake
fix remains useful route tooling. A closed-course race hold/motion probe is the
next workload investigation, not yet a qualified comparison or full race proof.

Sessions in C-A-B-B-A-C order: `20260910T050003Z-p9796`,
`20260910T050137Z-p27808`, `20260910T050312Z-p7120`,
`20260910T050446Z-p7076`, `20260910T050620Z-p29068`,
`20260910T050754Z-p25844`. Source-of-truth identities remain each run's metadata;
results, contact sheet, plan and explicit visual review are under
`.local/native-renderer/b2/stable-containment-handbrake-local-*`. Reproduce the
summary using `b2/summarize-handbrake-containment.py 1`. Its `complete` flag
means all six runs were collected, not retention qualification. The separate
review records `retention_qualified: false`. All B items stay open.


#### Closed-course route probe

Retained-build session `20260910T051524Z-p27136` exits normally after the new
130-second Recaro Rush hold/motion probe. The race starts at
(-1296.251587, 47.215019, -3550.364990); the 68- and 103-second captures have
identical player coordinates. Four seconds after releasing the handbrake, the
car has moved 16.74 m at a visible 32 km/h; the stopped sample is 49.96 m from
the start. All four race images pass the existing race-HUD checks and show
8/8 position, intact scenery/car and no nearby traffic. This establishes one
usable 1x route probe, **not** repeatability, matched performance, streaming or
a full race. Reproduce its checks with `b2/check-closed-course-handbrake.py`;
script, logs, images, hashes and contact sheet are in
`b2/closed-course-handbrake-probe*`. Both runtime paths remain retained.


#### Separate correctness lead found while adding producer hooks

The existing `setjmp_address` / `longjmp_address` entries in `main-xex.toml`
parse inside the scene-observer `[[midasm_hook]]`, rather than at the TOML root.
The SDK parser reads these scalar keys only at the root. Before the correction
below, generated direct callers still invoke the raw CRT functions instead of
the semantic helpers. Replacement happens at call sites; the original CRT
definitions may remain in generated output. Parsed data at `f613ed0` and
the current source confirm this predates the clear trace; new hook blocks were
placed after the old metadata to preserve its existing scope during the probe.
Evidence: `b3/crt-config-scope-observation.json`.

This is a concrete configuration correctness lead, **not an established cause**
of the earlier renderer null read or timeout. It is not fixed in the trace
experiment. Before broad new qualification, verify the target contract and add
a parsed-config/non-local-jump round-trip regression, then qualify any rebuilt
EXE. Preserve the existing renderer evidence and exact binary identities.


#### CRT scope correction and bounded runtime checks

The two CRT addresses now precede all tables in `main-xex.toml`, enabling the
existing SDK implementation. This changes nine direct setjmp sites and eight
longjmp sites in six caller functions. Each observed setjmp caller has one
site. No new jump implementation or renderer setting is introduced.

`tools/tests/test_nonlocal_jump_config.py` fails on the old table scope and
passes on the corrected root scope. After Release code generation,
`tools/check-nonlocal-jumps.py --compiler <clang++>` checks all 17 transformed
sites and compiles their actual emitted sequences and generated SDK helpers
against the SDK PPCContext at `-O2`. It passes initial/nonzero returns,
zero-to-one normalization, negative values, stack/nonvolatile GPR, FPR, vector,
CR/XER/LR/CTR restoration, nested frames, guest-memory side effects, key reuse
and thread isolation. This bounded contract does not establish indirect raw
CRT entry, guest jump-buffer byte compatibility, every unwind path or host
profiling-scope unwinding. The normal build has guest-function Tracy zones off.

Candidate EXE SHA256:
`C24D88DCF4C3F6564BE40A4B63046BACBBFB1E0BD7329983617DEF8ED8CD4CC8`.
The Release build succeeds; source hashes and generated caller audit are in
`.local/native-renderer/b3/crt-scope/`. Both live runs use retained renderer
`27B486...` and runtime `955BDC...`, with clear-producer tracing explicitly off.
They complete the 130-second Recaro race entry/hold/motion route and exit 0:

| Scale | Session | Stationary drift | Moving distance | Stopped distance |
| --- | --- | ---: | ---: | ---: |
| 1x | `20260910T054251Z-p20300` | 0.000122 m | 16.73 m | 49.97 m |
| 2x | `20260910T054530Z-p25316` | 0 m | 16.99 m | 49.32 m |

All race HUD checks pass. Sampled race scenery, car and HUD are intact; moving
images show 32/31 km/h. This is bounded smoke qualification, not a completed
race, sustained streaming test, matched performance result or NPC/UI timing
qualification. Both sessions have zero GPU errors and timing drops, but two
invalid simulation-delta samples and a startup `ResolvePath(\Device)` error.
Retained control `20260910T051524Z-p27136` has the same counts/message; invalid
samples occur at approximately 7.14/43.69 seconds of summed frame time in all
three runs. Preserve these observations; do not report wholly clean timing.

**B1 visual defect:** car-selection thumbnails show patterned corruption in
`event-step-1` at both scales. The earlier retained 1x control has the same
defect, confirmed in `crt-scope/car-select-control.png`; it predates this CRT
scope correction. Track the thumbnail producer/upload/consumer chain explicitly.
Passing race HUD checks do not establish menu visual correctness.

The corrected EXE is archived; baseline EXE `372161...` and retained renderer
remain staged for continuity with existing performance evidence. The CRT
correction has no established connection to earlier renderer crashes and earns
no rendering speedup or B-item completion. Continue B1's full chain inventory,
B2 mutation/streaming and work reduction, B3 producer bypass, and B4 profile/
timing qualification. Before using the corrected EXE for performance claims,
preselect and record it as a distinct baseline.


## B2: page mutation attribution and narrower invalidation candidate

The temporary CPU-page fingerprint diagnostic runs on corrected CRT EXE
`C24D88...`, with renderer
`C1DC16ABAFB0AEDEE010EB8B2E9C3D3141D879FC51B5FB6CC4722ECAA6BBA8E4`.
It reads ordinary cached CPU memory, never write-combined upload memory, and
keeps every original import. Per-owner versions and 4 KiB fingerprints identify
repeat work; matching fingerprints are not a byte-equality admission rule.
The production-body cache checks also exercise unchanged pages, partial changes,
snapshot upgrades and the transition through GPU-owned/unknown data.

Two separate 1x Recaro probes exit 0 and pass arrival/HUD/motion checks:

| Mode | Session | Imports | Imported bytes | Comparable CPU versions | Fingerprint-equal versions / bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| Exact | `20260910T055718Z-p28404` | 48,170 | 4,573,560,832 | 24,374 | 11,508 / 1,087,045,632 |
| Contained | `20260910T060006Z-p25844` | 26,406 | 2,590,507,008 | 16,961 | 10,654 / 1,220,476,928 |

These are instrumented work observations, not a performance comparison or
retention of containment. The exact run has 12,451 snapshot upgrades. Most
fingerprint-equal recurring race imports do not retain CPU snapshots, so merely
comparing existing snapshots would cover little of this repeated race work.
Evidence and source snapshots: `.local/native-renderer/b2/geometry-mutation-trace/`;
reproduce summaries with `b2/summarize-geometry-mutation.py <run-directory>`.

The existing shared-memory invalidation callback may widen a CPU write to a
256 KiB block at 4 KiB host pages. New default-off, restart-required
`fh1_narrow_cpu_invalidation` limits that speculative excess to 64 KiB windows.
It preserves the actual write range and existing GPU-written-page guards, fires
watches over the resulting range, and returns that same range to the physical
heap. The heap intersects callback ranges before unprotecting memory. No hash,
new mirror, allocation budget increase, packet suppression or OS setting is used.

SDK source commit: `75c3880`. Clean candidate DLL:
`BE32EE5D5923BA0D942C6AFA7D26E0E4C01BF8DE3BE61A124DD3D96DA38DE820`.
Release build, 1,500 production-function cases at 4/16/64 KiB host pages,
CPU-source ownership and texture-watch tests pass. The range test checks
exact/speculative modes, cross-window writes, GPU-history guards, validity bits,
watch notifications and returned ranges against a separate per-page model.

### Incomplete clean 1x comparison: no retention

The preselected C-A-B-B-A-C plan uses EXE `372161...` throughout: C is retained
DLL `27B486...`; A/B use `BE32EE...` with the limit off/on. Containment, recycling
and tile ownership remain off. No fingerprint trace, compiler or replay runs
alongside the benchmark. Process CPU/memory and all-cause page faults are sampled;
the latter do not isolate guest write-protection exceptions.

The 82..102-second hold observations from the first four valid route runs are:

| Run | Geometry imports/s | Median ms | p95 ms | p99 ms | Steady private MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1 | 424.24 | 16.741 | 18.766 | 21.093 | 2699.82 |
| A1 | 404.56 | 16.9155 | 21.050 | 22.261 | 2693.74 |
| B1 | 182.90 | 16.739 | 18.539 | 20.748 | 2688.95 |
| B2 | 182.02 | 16.703 | 18.529 | 20.809 | 2690.20 |

This is a repeatable work-reduction lead in two B runs, **not a completed
retention result**. A2 exits 0 but fails the HUD check at the 68-second
`race-ready` capture. Its scene/car are intact and later race captures have
the HUD; the cause is unproven. The driver stops there: C2 and 2x do not run.
Separately, the original 106..110-second acceleration window includes the
109-second screenshot and cannot support clean tail claims. Do not repair
either limitation by omitting data or declaring this block retained.

Sessions C1/A1/B1/B2/A2: `20260910T061100Z-p28252`,
`20260910T061314Z-p19156`, `20260910T061529Z-p8728`,
`20260910T061744Z-p30608`, `20260910T061959Z-p27244`.
An earlier setup attempt, `20260910T061007Z-p23172`, was rejected before gameplay
because the driver precreated the output directory. That setup defect is fixed
and its record preserved; it supplies no benchmark data.

The complete raw record, explicit failed-HUD report, partial summary, plan and
review are under `b2/narrow-invalidation/`. A prospective, unexecuted protocol
draft adds HUD bookends at 80/129 seconds and moves acceleration measurement
to 106..108 seconds. Implement and verify its checks before fresh comparisons;
keep the early HUD observation explicit, and do not equate bookends with
continuous UI/timing correctness. Broader 1x/2x ordinary, difficult-area and
streaming/mutation qualification remain required. The candidate stays off.

Another bounded B2 lead is the clean snapshot upgrade: the current cache
reimports GPU bytes when adding a CPU snapshot even if its existing watch
still proves the previous owner unchanged. Investigate a CPU-only upgrade
using that watch and authoritative CPU copy, with invalidation-during-copy
fallback; no implementation or saving from this separate lead is claimed.

### CPU-only snapshot experiment: implemented, then archived

The watch-valid upgrade lead was implemented behind a default-off flag, built
and exercised at 1x/2x. An existing owner watch must remain valid through the
authoritative CPU copy and final import decision. Otherwise the original full
import runs. The successful path avoids the upload allocation, GPU copy and
barriers; it adds only the CPU snapshot already required by the consumer.
Full-owner coverage, immutable index snapshots, alias revalidation, eviction
fences, allocation budgets and destruction retain the existing cache rules.

The production-body cache check passes with exact and contained owners, partial
writes, CPU/GPU invalidation during the copy, upload failure, failed prior imports,
snapshot/GPU bytes, counters and fences. Candidate renderer SHA256:
`0CE37F6CC49865B1D160C3232C4E2BE2E58D6E28197C56E7CC8F220921FAF3FC`.
Both probes use corrected CRT EXE `C24D88...`, narrow invalidation/containment/
recycling/tile clear off, and the revised 130-second race route. Both exit 0 and
pass all six race HUD checks, arrival, hold and motion. Sampled race images are
intact; the existing car-selection thumbnail corruption remains. Both have zero
GPU errors/timing drops and the same two invalid simulation-delta observations.

| Scale / session | CPU-only upgrades | Avoided upload bytes | Imported bytes |
| --- | ---: | ---: | ---: |
| 1x `20260910T064709Z-p3992` | 216 | 14,155,776 | 4,319,412,224 |
| 2x `20260910T064943Z-p26616` | 249 | 16,318,464 | 4,749,000,704 |

These are **last periodic counters**, not exact whole-session totals or a
performance comparison. Avoided bytes are only 0.327%/0.342% of observed
imported-plus-avoided bytes. The earlier 12,451 `add_snapshot` observations
included new/dirty owners; they were not 12,451 clean-owner opportunities.
This corrects the attribution behind that lead.

**Do not retain this experiment.** Its bounded work reduction is too small to
prioritize over speculative invalidation. The production change, flag and test
extension are removed after archiving source, patches, executable checker, build,
binary, sessions and review under `.local/native-renderer/b2/cpu-snapshot/`.
No GPU-content or performance qualification is claimed, and rejection does not
complete B2. SDK source returns to `75c3880` plus the pre-existing unrelated edits.

### Revised comparison stops; dense captures reproduce a baseline HUD gap

The prospective route adds captures at 80 and 129 seconds and restricts the
acceleration window to 106..108 seconds. All scheduled captures lie outside the
82..102, 106..108, 112..118 and 122..128 windows. Its checker separately records
early and later HUD outcomes, but **either failure still rejects the route**.
A negative check using the previously missing-HUD image confirms this; passing
later bookends cannot mask the early failure. Endpoint checks still do not prove
continuous activity, capture/CSV clock identity or transition timing.

Fresh 1x C-A-B-B-A-C comparison uses the original EXE `372161...`, retained C
renderer `27B486...` and candidate A/B renderer `BE32EE...`, narrow invalidation
off/on. C1 (`20260910T065334Z-p11964`) passes. A1
(`20260910T065549Z-p14316`) exits 0 but again has no HUD at 68 seconds; all five
later HUD checks pass. The driver stops before B1/B2/A2/C2. The revised 2x block
is not run. Both incomplete comparison blocks and all failed images remain.
Neither supports retention. At 80 seconds the race clocks read 15.592 seconds
in C1 and 21.592 in A1 despite matching positions, exposing a six-second race
entry offset that pose checks alone miss.

Two separate 82-second diagnostic runs capture every half-second from 66.5 to
74 seconds and once at 80. Both exit 0 and retain the expected stationary race
pose. They use EXE `372161...`; all candidate options are off:

| Renderer / session | Missing HUD at scheduled seconds | Remaining race captures |
| --- | --- | --- |
| Candidate `BE32EE...`, `20260910T070148Z-p24964` | 68, 69 | 15 pass |
| Retained `27B486...`, `20260910T070529Z-p5916` | 67.5, 69 | 15 pass |

The full HUD disappears in individual captured images between passing neighbors,
including on the retained path. This predates the 64 KiB option and is not a
sustained missing-HUD transition. It does **not** yet distinguish title draw
omission from output/publication/capture behavior, or establish what the user
sees in host presentation. Do not dismiss it as a screenshot artifact or claim a
renderer root cause. Dense captures are diagnostic, never clean benchmarks.
Evidence and scripts: `b2/hud-gap-diagnostic/`, `hud-gap-diagnostic-plan.json`,
`check-hud-gap-diagnostic.py`, `check-race-bookends.py` and its negative check.

Next attribute the missing UI at producer, draw and published-image boundaries,
including cadence. The 64 KiB candidate remains off pending this issue and the
full 1x/2x ordinary/difficult streaming and mutation checks. All B1-B4 requirements
remain open; no A6 2x retest or expansion is authorized by these observations.

A follow-up retained-renderer run with requested source cap 30,
`20260910T070826Z-p27796`, exits 0 and has no missing HUD among its 17 race
captures. This is **inconclusive cadence attribution**: the 66..74-second
interval produces only about 15 source frames/s, versus about 14/16 in the
uncapped candidate/control diagnostics. It does not demonstrate a 30-versus-high
FPS comparison, an animation fix or complete UI timing. All three diagnostics
have zero GPU errors/timing drops, two invalid deltas elsewhere in the session,
and approximately 1.00 simulation/wall ratio with zero invalid deltas in 66..74.

The early racing workload deserves separate cost attribution. Source-CSV median
intervals in 66..74 seconds are about 56..85 ms across these diagnostics and the
sparsely captured controls; later intervals often recover to about 16.7..17.3 ms.
The late-starting control remains slow longer. These are descriptive observations
with captures, not clean benchmark estimates or proof of a capture-induced stall.
They expose an important gap in judging this scene only after the opponents have
left: static pose/HUD endpoints alone do not match race stage or the costly work.
Use this reproducible early-race interval for UI/geometry/pass attribution while
preserving the separate Outpost, town, junction and highway requirements.
See `hud-gap-diagnostic/{cadence-observations,early-phase-context,runtime-review}.json`.

### Early-race attribution: buffer churn and absent UI-associated draws

Session `20260910T072547Z-p23496` completes the 88-second stationary Recaro
diagnostic and exits 0. It records 23 captures, including 19 race captures with
the expected stationary pose. Two race images lack the HUD: scheduled 69.5
and 70.5 seconds (`hud-4170`, `hud-4230`). Preserve both failures.

This uses temporary instrumentation on SDK `75c3880`, with narrow invalidation,
contained windows, buffer recycling and tile ownership explicitly off. Corpus
recording is on and discovery sampling is off. Exact binary SHA256 identities:

- EXE: `3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3`.
- Diagnostic renderer: `37B02E7F925FBC5E2A6DAE301A5D68CE0D0EFB9F1B0F43B2CB4CAA3D374B6A94`.
- Diagnostic runtime: `411CF48B0D81A0C630A10C0F6F31C4B29A2593C3376CAD66640E66B38A40E75C`.

The renderer includes the current SDK's exact-window map implementation, so
candidate flags off does **not** make it the retained `27B486...` binary/source.
Per-draw clocks, logging and captures perturb timing. These observations rank
work within this diagnostic; they are not a retained-build benchmark, a matched
early/late comparison or an estimate of fully removable frame time.

The existing geometry-cost probe measures allocation, eviction and import CPU
time. Source-labelled `IssueDraw` totals are joined through native output and
geometry frame identities. Windows below use seconds since the first native
output callback, not an assumed alignment with asynchronous CSV/GPU rows:

| Measurement | Early (66..74 s, 122 frames) | Late (82.1..84.8 s, 118 frames) |
| --- | ---: | ---: |
| Median total `IssueDraw` CPU ms/frame | 42.023 | 12.145 |
| Mean geometry buffers created/frame | 45.254 | 0.025 |
| Mean geometry owners evicted/frame | 45.131 | 0.034 |
| Mean allocation CPU ms/frame | 14.088 | 0.008 |
| Mean eviction CPU ms/frame | 8.383 | 0.010 |
| Mean import CPU ms/frame | 0.540 | 0.051 |
| Mean geometry imports/frame | 46.541 | 4.975 |
| Mean imported bytes/frame | 4,719,129 | 455,975 |

Allocation covers `CreateCommittedResource`; eviction includes victim selection,
watch removal and resource/map release. Import measures CPU preparation and
copy-command recording, not GPU copy duration. These timers are contained within
the draw path and must not be added again to total draw CPU. The approximately
22.47 ms/frame allocation-plus-eviction cost makes **buffer churn during active
early racing** the next B2 lead. The 32 MiB cache budget is unchanged. A later
stationary scene largely stops this churn and does not qualify the early workload.

The largest early CPU draw groups are depth-mode VS hashes `5A28C7FAFD86F112`,
`C8C39E5AE1B08DE6` and `9BF2991815B941B9`, at about 6.45, 6.01 and 4.53
ms/source frame respectively. These are draw-processing CPU costs, not measured
shader execution time or independently removable passes.

For capture attribution, the probe logs the output resource before native
rendering and after submission, then logs the resource actually consumed by
`CaptureGuestOutput`. Every race capture maps to a preceding completed submission
with no same-resource pending-output conflict. The existing capture queue/fence
path is unchanged. Submission completion here means commands submitted before
publication, not GPU execution completed at that log entry.

Missing captures map to source frames **4758 and 4770**. Both have 5,492
`IssueDraw` calls, 5,326 issued draws and zero failed calls. Across the 14 passing
neighboring captures through 74 seconds, the following three mode-4 shader pairs
issue 99, 42 and 7 draws per frame; both missing captures have no recorded calls
for any of these pairs:

| Vertex / pixel shader hashes | Issued in each passing neighbor | Missing frames |
| --- | ---: | ---: |
| `ED90DA6EFF5C6BCA / 57B9400F6B398736` | 99 | 0 |
| `79034645B1CB882B / CAE1DB68AFFA9D3C` | 42 | 0 |
| `984DBF6AF14DBEBD / 6FDA0F1CDE67D12F` | 7 | 0 |

Thus these 148 UI-associated draws are absent from the attributed source frames;
the evidence does not show normally issued HUD draws simply disappearing during
capture. It still does not identify why the guest producer omits them, prove an
animation/cadence cause, or independently establish host-visible presentation.
Trace that producer/packet boundary before claiming the HUD defect fixed.

GPU timing retains `IsFh1GpuWorkTimingSampleFrame`'s every-60-source-frame gate.
Only two early sources (4740/4800, 190/184 records) and two late sources
(5340/5400, 139 records each) have pass samples. Missing samples mean unavailable
cost, never zero. Another 26 sampled source identities fall outside the logged
output window. Intervals can overlap, nest or include CPU starvation; no GPU
ranking or sum of independently removable GPU costs is claimed. The final pass
timing report records zero dropped samples.

**Next:** measure the existing exact-size buffer recycler in this specific
early-race diagnostic before designing a new cache. This would attribute work
removed under the newly identified churn, not reopen an old failed retention
comparison unchanged. If size mismatch still forces creation, investigate
fence-safe reuse of a larger buffer's capacity while retaining the new owner's
exact logical range, full import and actual allocation budget. That revised
design is not implemented or qualified. Continue the HUD producer investigation
and retain the strict early/late correctness gates before clean comparisons.

Local evidence lives in `.local/native-renderer/b2/race-cost-profile/`: source
snapshots/patches and hashes, Release build, passing production-cache check,
diagnostic DLLs, route, raw log, corpus, CSV, images, capture identities and
`run-1x/profile-summary.json`. The existing local `make-race-cost-profile.py`,
`build-race-cost-profile.ps1`, `run-race-cost-profile.ps1` and
`summarize-race-cost-profile.py` reproduce the probe and identity joins. These
raw diagnostic archives remain local; this checkpoint publishes the findings
and exact identities. No diagnostic instrumentation remains in production.

Both renderer/runtime paths and the EXE are restored to their qualified hashes
in the [checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md). Unrelated SDK
kernel profiling edits remain byte-preserved and excluded from this build and
commit. No game/compiler/replay is active. B1-B4 remain open with the full scene,
mutation/streaming, producer-bypass and visual/timing scope; no new optimization,
release or higher-resolution A6 admission is retained.
