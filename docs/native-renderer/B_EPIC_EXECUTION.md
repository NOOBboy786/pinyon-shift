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

### Early-race attribution: buffer churn and draws absent with the HUD

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

These 148 draws are absent from the attributed source frames, correlated with
the missing HUD. **Classification correction:** this alone does not prove they
are HUD producers. The shader catalog names the second and third pairs world-lit
specializations and the first gradient-fade. Establish the actual output/resource
chain and producer before concluding that HUD generation was omitted. The omission's
cause, animation/cadence connection and host-visible presentation remain unproven.

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

### B2: select a matching completed victim; oversized reuse archived

The next three diagnostics implement the preselected work attribution. All
reuse the 88-second Recaro route, EXE `372161...`, diagnostic runtime `411CF4...`,
1x resolution, and the CPU/draw/output probe above. Narrow invalidation,
containment and tile ownership stay off. All exit 0 and verify 19 stationary
race captures; missing HUDs are preserved, not converted into passes.

| Design / session | Early frames | Creations/frame | Recycles/frame | Rejected cache requests/frame | Allocation + eviction CPU ms/frame | Late imports/frame | Missing HUD times (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Existing oldest-victim exact-size, `20260910T073938Z-p27040` | 116 | 57.543 | 34.931 | 38.353 | 26.306 | 6.945 | 68.5, 69.5, 70, 71, 73 |
| Smallest fitting capacity, `20260910T074608Z-p18104` | 209 | 0.254 | 56.321 | 638.694 | 0.285 | 40.309 | 67.5, 68 |
| Oldest matching exact-size, `20260910T075207Z-p27464` | 209 | 5.014 | 52.967 | 48.378 | 2.939 | 5.922 | None sampled |

These are separate instrumented runs with changing race stage/draw mixes, not
matched performance results. Early/late windows use the same output clock as
the preceding table. The eviction timer excludes blocked early returns; total
`IssueDraw` CPU still includes their cost. The exact-size search records early
median draw CPU 19.493 ms and late 12.258 ms; the capacity probe records
19.384/15.331 ms. Neither comparison establishes a retained speedup. Raw means,
sample coverage and identities are in `matching-recycle/diagnostic-comparison.json`
under `.local/native-renderer/b2/`.

The capacity experiment tracks resource width separately from logical ownership,
keeps actual allocation bytes charged, and imports only the new logical window.
Its production-body checks pass, including partial writes, fence selection,
old-watch removal, failed imports and unexposed extra capacity. Nevertheless,
native-cache rejections and late recurring work rise sharply. Retaining oversized
storage is a cache-pressure suspect, not independently isolated causality.
**Archive this experiment:** its field and production changes are removed.
Source, patch, extended checker, binary and run remain in `race-capacity-profile/`.
Its renderer SHA256 is
`6D1DCB9EEA60C8EA0AA2D6F4C4967D34B42BF12280F6DE9F7F81768512D4FEEF`.

The replacement is smaller: search the existing bounded cache for the oldest
completed owner with exactly matching logical size **and** allocation bytes,
then use the existing full import and metadata reset. If no match exists, retain
the original oldest-victim eviction/allocation path. No new pool, capacity field,
budget increase or ownership broadening remains. The existing
`fh1_recycle_geometry_buffers` flag stays **false by default**.

SDK implementation: `acd222caa04adcc9e2ad8aabf99c09a9a8e12f0e`.
The extended `tools/check-fh1-geometry-cache.py` exercises this production body
in exact and contained modes: it must skip a differently sized oldest owner,
reuse the oldest matching completed buffer without calling allocation, protect
an in-flight matching owner, reset snapshots/bounds/watches, preserve the budget,
handle partial writes and recover from a failed import. The existing no-match,
all-in-flight, destruction and invalidation cases still pass. Its fake GPU
objects do not establish new actual D3D12 copy/consumer qualification.

Diagnostic renderer SHA256:
`6603C44A14C68371CE4596FE53E631E34CA9F8E9D694CDE0D4596B5FDEF00583`.
The clean Release build, with temporary instrumentation removed, is
`3A0B434AFA297315469B4A122AE72A3DE60DB2940B132057AD90B3FABACB21A1`.
Its source and binary are archived in `.local/native-renderer/b2/matching-recycle/`;
the diagnostic sources and run are in `race-matching-profile/`. The original
oldest-victim run remains under `race-cost-profile/run-1x-recycle/` on renderer
`37B02E...`. All diagnostics use the same `411CF4...` runtime hash; unrelated
kernel profiling edits were excluded and restored byte-for-byte.

The 19 passing HUD captures in the matching-victim diagnostic are encouraging,
but one run does not fix or explain the baseline HUD defect. The other two
probes still show missing-HUD frames. Gradient-fade call counts also vary with
scene state, so the preceding 148-call observation must not become a universal
HUD detector. Continue resource-chain/producer attribution and strict HUD gates.
Actual GPU reuse, sustained changing/streamed content, matched 1x/2x tails/memory
and all difficult-scene requirements remain open before retention.

Clean candidate smoke checks also pass at both scales, on retained EXE
`372161...` and runtime `955BDC...`, recycling on and the other candidates off:

| Scale / session | Moving distance | Stopped distance | Last periodic creations / recycles |
| --- | ---: | ---: | ---: |
| 1x `20260910T075538Z-p10180` | 16.852 m | 50.245 m | 3,631 / 29,445 |
| 2x `20260910T075817Z-p1204` | 17.060 m | 49.507 m | 2,860 / 29,375 |

Both complete the 130-second route and exit 0, with all six early/late race HUD
checks, stationary hold and motion passing. Sampled race images retain the car,
road, crowd and HUD (32/31 km/h in moving captures). The existing patterned
car-selection thumbnails remain at both scales. Both have zero GPU errors and
timing drops, the two known invalid simulation-delta samples and the known
startup `ResolvePath(\Device)` error. Last periodic recycling counters are not
exact session totals. These runs are bounded smoke qualification, not clean
matched performance, continuous UI timing or sustained streaming proof.

Evidence: `matching-recycle/exact-{1,2}x/`, `contact.png` and
`runtime-review.json`. Both staged renderer/runtime paths and the EXE are restored
to the qualified `27B486...` / `955BDC...` / `372161...` hashes. All build, game
and replay processes are terminal. B1-B4 remain active and open.

### Matching-victim GPU proof and direct HUD classification

Session `20260910T080726Z-p12416` runs the 130-second Recaro route at 2x,
recycling on, narrow invalidation/containment/tile ownership off. It exits 0
with ten captures and all six strict HUD/pose/hold/motion checks passing.
Temporary markers surround actual recycled `CopyBufferRegion` commands only;
admission, victim selection and copying are unchanged from SDK `acd222c`.
Production instrumentation is removed and qualified binaries are restored.
Recording perturbs execution; this is correctness evidence, not performance.

| Artifact | SHA256 |
| --- | --- |
| EXE | `3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3` |
| Runtime | `955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500` |
| Marker-only renderer | `43E59CB2EDBA3177060E58CEA90EE964A00527849DD7DDC39BB772DF6E4C71A4` |
| Production command-processor source | `7E88F0F6D8F6C6F4F3735C9094F577B8420E268B6042ACB15352E88A22B4B22B` |
| Marker source fixture | `71B6B942DBBD9410B854F4C89A2902279DD39D74374D10825C6DE3F2B7A8AE69` |
| `frame_frame3883.rdc` (567,873,360 bytes) | `D66776560139566184606AE12A9E642F8E29F97EFE283AB3C24D47A2F983E999` |
| `frame_frame3884.rdc` (524,249,907 bytes) | `1BDB326604A585A4D0C7DD790AC76E1848D465D8610042E0598C5D9368976454` |

Replay of capture 3883 passes all 18 actual copies into 18 reused buffers:
2,293,760 bytes, with seven 64 KiB, nine 128 KiB and two 320 KiB imports.
Ten choose a completed matching victim other than the oldest cache entry.
Retired submissions are 12500..12505, completed is 12507 and current is 12509.
All sources are CPU uploads with nonzero bytes; each destination changes and
equals the actual source immediately after copying. The first bound consumer
also matches the imported bytes for every buffer: 12 VS-resource and six
index-buffer checks. Later uses are inventoried, but only the first consumer
is byte-checked before rewrite. This does not cover GPU-written sources, all
sizes, sustained streaming or full lifetime qualification.

Capture 3884 has zero marked recycled copies. Preserve its report error,
`AssertionError('No actual recycled copies captured',)`, as missing coverage.
The replay launcher returns 0 despite the assertion; inspect report contents
to establish success. These adjacent RenderDoc captures do not establish
adjacent native source frames or zero total GPU work in the second capture.

The same capture provides direct output attribution for the previously
correlated shader groups. Replay maps actual command-list pipelines and checks
the first, middle and last draw in each group, exporting raw before/after
target bytes and images. All nine write `ResourceId::1915`, the main
`k_2_10_10_10` target: R10G10B10A2_UNORM, one sample, 2560x4096 backing with
2560x1440 viewport/scissor. Image review uses the active viewport.

| VS / PS | Draw count in this capture | Sampled HUD outputs |
| --- | ---: | --- |
| `ED90DA6EFF5C6BCA / 57B9400F6B398736` | 101 | Lap, standings and gear glyphs |
| `79034645B1CB882B / CAE1DB68AFFA9D3C` | 42 | Speedometer dial, tick and marking |
| `984DBF6AF14DBEBD / 6FDA0F1CDE67D12F` | 7 | Map, standings background and speed readout |

For example, event 38530 changes the map region, event 38580 the speedometer
dial and event 38610 a lap-label glyph. This now verifies HUD use for these
sampled draws, beyond shader-name correlation. It does not classify every
global use as HUD-only. Earlier source-linked gaps lacking these groups
therefore warrant upstream HUD draw-generation investigation. Their CPU
producer, omission cause, animation/cadence connection and host-visible
behavior remain unresolved. No workaround or cause fix is retained.

Local evidence: `.local/native-renderer/b2/matching-capture/`, including
`2x-audit-3883/{inventory,report}.json`, negative `2x-audit-3884/report.json`,
`2x-hud-classification-3883/{report,classified}.json`, raw bytes and
`viewport-contact.png`. Reproduction helpers remain under `b2/`:
`make-matching-capture.py`, `build-matching-capture.ps1`,
`run-matching-capture.ps1`, `audit-matching-capture.py` and
`classify-hud-capture.py`. Game/build/replay work ran sequentially.

### Race-stage probe: confirm once after the menu is ready

Retained 1x session `20260910T082207Z-p23756` removes the repeated confirmation
pulses at 52, 58, 60 and 62 seconds, keeps one at 64 seconds and adds three
pre-confirmation captures. Remaining hold/motion inputs are unchanged. The
130-second run exits 0 with 13 captures. A copy of the existing workload
checker changes only expected capture count and diagnostic scope; all six
original HUD/pose/motion thresholds and window checks pass. Moving distance
is 16.732 m and stopped distance 49.951 m, with a stable final pose.

Image review shows the pre-race cinematic at 49 seconds and the Start Race
menu at 52, 58 and 62 seconds. After the final confirmation, the 68-second
image has a three-second countdown and zero race time; the 80-second image
shows about 9.36 seconds of race time. Later motion images retain the car,
road and HUD. This demonstrates that the original pose gates alone miss
race-stage shifts. It supports testing a single confirmation after menu
readiness; one diagnostic does not establish repeatable timing or prove why
the earlier runs differed by six seconds. The later inputs now occur at an
earlier race stage, so this run is not a matched performance comparison.

Existing M4 telemetry adds 597 route-frame and 551 vehicle-pose samples.
Every route sample reports `route_state=00000001` and
`transition_active=00000000`, across menus and racing. These fields cannot
identify race start in this route. No timing hook or simulation behavior is
changed. EXE/renderer/runtime are retained `372161...`/`27B486...`/`955BDC...`;
all experimental options are off. Logs, route, images, strict checker output,
`stage-summary.json` and restored runtime verification remain under
`.local/native-renderer/b2/race-stage-probe/`.

Next, prospectively qualify race-stage alignment on retained and candidate
builds with a single final confirmation. Shift later phases consistently and
include an explicit expensive early-race window with HUD captures outside its
timed interval. Do not replace it with a later stationary phase or discard any
missing-HUD evidence. Fresh 1x GPU checks, repeated clean 1x/2x tails/memory,
sustained mutation/streaming and the full B scene set remain required. B1-B4
stay open and the matching-victim recycler remains disabled by default.

### Test-input delivery, capture clocks and a braked-entry recycler pair

The prospective single-confirmation C-A block stops at A1. Retained C1
(`20260910T083614Z-p15512`) passes all seven race HUD/pose/motion checks.
Candidate-off A1 (`20260910T083941Z-p19100`) exits normally but never enters
the event: its supposed race captures show free roam and fail the grid-pose
gate. Both use EXE `372161...`; renderers are `27B486...` and `3A0B434A...`.
No B runs or 2x block follow this failed comparison. At signup, screenshots
show different approach positions, moving cars and adjacent traffic. The
failure's exact cause is unproven; later success does not erase it.

The test driver selects the latest scheduled input state, so a short pulse
can be skipped if polling/output progress jumps over it. Test-only runtime
instrumentation now records delivered step indices, scheduled/observed frames
and skipped steps, without changing selection or input duration. Delivery to
the API does not prove menu acceptance. Capture events additionally record
their output-callback index, actual trigger time and readback/write interval
relative to the route clock. The trigger is **not** the captured image's
source-frame identity: publication may supply an earlier resource.

`tools/check-fh1-render-test-clock.py` checks input delivery and bounds the
route/CSV origin offset using synchronous D3D12 callbacks between consecutive
XE_SWAP CSV rows, including accumulated microsecond truncation. It rejects
missing timing evidence and inconsistent anchors. The executable unit check
also rejects an omitted input even when capture timing is valid. Usage:

```powershell
python tools/check-fh1-render-test-clock.py <session.jsonl> --output clock-check.json
```

Release EXE SHA256:
`EC2E5F097A3D513AE945B42B9E1EE01822A9E2DA7EEA08F5DD91B7E8F3243D30`.
It includes the already documented CRT configuration correction as well as
the new test telemetry. It is archived, not substituted for retained EXE
`372161...` after tests. The unchanged candidate renderer is `3A0B434A...`;
runtime remains `955BDC...`. Unrelated SDK kernel edits are excluded from the
build and restored byte-for-byte.

Initial timing diagnostic `20260910T084813Z-p23280` passes all 22 delivered
inputs, 12 captures and seven race HUD/pose/motion checks. Its route/CSV origin
offset is bounded to 3.073..20.207 ms. Whole capture-containing source-frame
intervals are outside every selected timing window. Early-race median is
61.497 ms; this verifies the costly phase remains present, not a speedup or
a cause fix for the earlier failed arrival.

A changed entry route adds handbraking at 14 seconds and extends the signup
X press from 100 to 500 ms. Other times are preserved, including one final
confirmation at 64 seconds. Both subsequent candidate-off/on runs show a
stopped car at signup, deliver all 23 steps, exit 0, and pass the seven HUD,
grid-pose, hold and motion checks. Their race clocks at 76/88/92 seconds differ
by at most 0.129 seconds. Opponent standings differ; this is not identical AI
behavior or continuous NPC/UI timing qualification.

| Braked-entry diagnostic | Recycling off | Recycling on |
| --- | ---: | ---: |
| Session | `20260910T085213Z-p8464` | `20260910T085529Z-p29728` |
| Early 78..86 s source frames | 144 | 316 |
| Early median / p95 / p99, ms | 46.015 / 88.927 / 92.396 | 25.222 / 29.879 / 30.797 |
| Early mean draws | 5,457.46 | 5,501.32 |
| Hold 94..114 s median / p95 / p99, ms | 16.849 / 19.868 / 22.069 | 16.799 / 19.927 / 21.243 |
| Handbrake 124..130 s p99, ms | 19.057 | 21.207 |
| Settled 134..140 s p95 / p99, ms | 18.701 / 20.350 | 19.906 / 21.197 |
| Last periodic allocations / recycles | 23,707 / 0 | 4,006 / 29,284 |

Both use the same `EC2E5F...` EXE and `3A0B434A...` renderer; only recycling
changes. Narrow invalidation, containment and tile ownership remain off.
Clock-offset bounds are 3.480..20.708 ms and 3.566..20.305 ms respectively.
Selected whole source-frame intervals stay inside each measurement window for
every allowed offset and CSV rounding bound; capture intervals stay outside.
No asynchronous GPU sample is assigned to a CPU row. Periodic allocation
records are not exact session totals or per-phase rates.

The early improvement prioritizes this candidate for repeated qualification.
**No retention:** this is one off/on pair, not the full preselected repeated
1x/2x comparison. Handbrake p99 rises 11.28% and settled p95 rises 6.44% in
this pair. Memory-pressure comparisons, fresh 1x GPU copy evidence, sustained
streaming, difficult scenes and continuous visual/timing checks remain open.
Both runs retain two known invalid simulation-delta samples and the startup
`ResolvePath(\Device)` error, with zero GPU errors/timing drops.

Evidence: `.local/native-renderer/b2/matching-stage/` preserves the failed
block and new route plans. `test-clock/` holds the build, exact sources/binary,
three telemetry runs, clock/window checks, images and
`braked-entry-comparison.json`. The local `summarize-test-clock.py` performs
conservative window selection. Continue with repeated 1x/2x controls on one
pinned EXE and the braked-entry route, collecting matched memory/process/GPU
metrics and preserving all failures. The full B1-B4 scope remains unchanged.

### Repeated recycler comparison with process and GPU memory sampling

The next comparison prospectively selects C-A-B-B-A-C at 1x, then the same
order at 2x. C is retained renderer `27B486...`; A/B are clean candidate
`3A0B434A...` with recycling off/on. Every condition uses test EXE `EC2E5F...`
and runtime `955BDC...` from the preceding entry. Narrow invalidation,
containment and tile ownership stay off. There are no per-draw CPU clocks,
corpus or M4 diagnostics. The braked-entry route is pinned to SHA256
`51e9be1cf28fc725b60873726f0cc5ac6b4e30f5915eb98165cb0681813de077`.

**Partial checkpoint:** only C1, A1 and B1 at 1x have run. The second B/A/C
and the entire 2x block remain outstanding. The user's checkpoint request
does not invalidate these runs or permit a retention decision from half a
block. Run labels do not mean completion of the B-epic checklist items.

| Completed 1x run | C1 retained | A1 recycling off | B1 recycling on |
| --- | ---: | ---: | ---: |
| Session | `20260910T090600Z-p26468` | `20260910T090921Z-p8644` | `20260910T091240Z-p10900` |
| Race clock at 76 / 88 / 92 s | 5.544 / 17.583 / 21.592 | 5.513 / 17.569 / 21.562 | 5.592 / 17.617 / 21.608 |
| Early 78..86 s source frames | 138 | 136 | 319 |
| Early median / p95 / p99, ms | 51.391 / 112.070 / 119.821 | 68.509 / 88.323 / 91.360 | 24.738 / 29.374 / 38.336 |
| Early mean draws | 5,462.23 | 5,476.00 | 5,511.54 |
| Early mean vertices | 2,136,463 | 2,134,103 | 2,143,745 |
| Hold 94..114 s median / p95 / p99, ms | 16.736 / 18.666 / 20.838 | 16.799 / 19.100 / 21.659 | 16.794 / 18.847 / 21.031 |
| Acceleration 118..120 s median / p95 / p99, ms | 16.322 / 18.319 / 18.586 | 16.431 / 18.516 / 18.843 | 16.665 / 18.815 / 20.286 |
| Handbrake 124..130 s median / p95 / p99, ms | 16.290 / 18.281 / 19.839 | 16.494 / 19.877 / 21.414 | 16.745 / 18.648 / 20.738 |
| Settled 134..140 s median / p95 / p99, ms | 16.358 / 18.128 / 18.819 | 16.765 / 19.006 / 20.825 | 16.783 / 18.859 / 20.361 |
| Last periodic allocations / recycles | Unavailable | 23,923 / 0 | 3,421 / 28,103 |
| Hold periodic imports/s | 422.71 | 298.07 | 416.42 |
| Whole-session async GPU interval mean, ms | 12.387 | 12.592 | 12.376 |
| Process CPU seconds/wall second | 3.028 | 3.009 | 3.109 |
| Process total OS faults/s | 2,854.96 | 2,795.14 | 2,799.64 |
| Sampled peak private / working memory, MiB | 2,722.53 / 2,210.92 | 2,714.73 / 2,181.76 | 2,701.26 / 2,172.95 |
| Early mean dedicated / shared GPU memory, MiB | 1,218.19 / 177.49 | 1,230.22 / 162.18 | 1,227.42 / 154.55 |
| Early mean total committed GPU memory, MiB | 1,395.68 | 1,392.40 | 1,381.97 |
| Hold mean dedicated / shared GPU memory, MiB | 1,219.86 / 189.43 | 1,230.37 / 162.18 | 1,227.44 / 154.55 |
| Hold mean total committed GPU memory, MiB | 1,409.28 | 1,392.55 | 1,381.99 |

All three runs exit normally with all 23 delivered inputs, 12 captures and
seven HUD/grid-pose/hold/motion checks passing. Manual review verifies stopped
signup, the prestart menu at 62 seconds and race-clock spread at each bookend
within the preselected 0.5-second limit (largest observed: 0.079 seconds).
Race daylight/grid match; opponent standings and pre-race free-roam lighting
vary. This does not establish identical AI behavior or continuous NPC/UI timing.
Each retains two known invalid simulation deltas and the startup
`ResolvePath(\Device)` error; GPU errors/timing drops are zero.

Measurement boundaries and limits:

- Source median/p95/p99 use complete CSV frame intervals conservatively inside
  each window for every permitted route/CSV clock offset and truncation bound.
  Capture-containing intervals are outside every timed window. Offset bounds
  for C1/A1/B1 are 3.389..19.366 / 3.415..19.358 / 3.441..19.914 ms.
- Whole-session GPU intervals are asynchronous native timestamp observations,
  not CPU-row pairs or isolated shader execution cost. They may include CPU
  starvation; changing pre-race lighting also limits whole-route comparisons.
- All runs use the same Windows process/GPU-memory sampler. GPU counters have
  71 sets per run, five valid records per set, with zero reported sampling
  errors. Roughly two-second cadence gives four early and ten hold samples.
  Counters identify the game PID and preserve per-instance paths/status/time;
  they are not adapter totals. Dedicated equals local here, and shared equals
  nonlocal: do not add these duplicate concepts. Total committed is separate.
- OS phases use wall timestamps aligned approximately through capture log
  anchors, with 100 ms excluded at phase edges. Anchor spread is below 1 ms
  in all three runs; OS samples still are not exact source-frame observations.
  Short motion phases contain only one to three OS samples. Peaks are sampled
  peaks, not a proof that memory pressure cannot rise during longer play.
- CPU and fault rates cover the sampled process interval. Faults are total
  PSAPI page faults, not specifically guest protection faults. Geometry rates
  require two timestamped periodic records: early C1/A1 have only one, so
  their import rates are unavailable. Hold rates use 12 records each. Allocation
  counters are last periodic values, not exact totals; C's DLL lacks those
  allocation/recycle counters. Recorded geometry allocation stays within 32 MiB.

The early improvement and fewer allocations remain promising. Later tails,
imports, process CPU and memory still require the complete repeated comparison;
these three runs neither retain recycling nor establish lower requirements.
Fresh 1x GPU copy proof, sustained mutation/streaming, difficult/ordinary scenes
and the full B1-B4 contract remain required.

Local evidence is `.local/native-renderer/b2/matching-retention/`, including
`plan.json`, per-run session logs/CSV, `process-samples.json`, `page-faults.json`,
`metrics.json`, clock/workload checks, images and `stage-review.json`.
Local helpers `run-matching-retention.ps1`, `summarize-retention-run.py`,
`retention-contact.py` and `record-retention-stage.py` reuse the existing launch,
clock and workload tools. Resume with label `b2` at scale 1, review its gates
and images, then A2/C2 and the planned 2x block. No processes remain active;
all nine retained runtime files are restored and verified. Defaults, saves and
unrelated SDK work are unchanged.

### Repeated block stopped; bounded 1x GPU proof from a crashed capture

The remaining 1x B2 and A2 runs complete normally and pass delivered-input,
clock, seven HUD/pose/motion and manual race-stage checks. Their race clocks
at 76/88/92 seconds are 5.575/17.608/21.599 and 5.541/17.599/21.592 seconds.
These are run labels, not completion of checklist items.

| Additional 1x run | B2 recycling on | A2 recycling off |
| --- | ---: | ---: |
| Session | `20260910T092319Z-p9692` | `20260910T092608Z-p25588` |
| Early 78..86 s frames | 340 | 138 |
| Early median / p95 / p99, ms | 23.895 / 26.442 / 28.388 | 56.534 / 104.565 / 132.827 |
| Hold median / p95 / p99, ms | 16.824 / 18.909 / 21.311 | 16.835 / 19.829 / 21.343 |
| Acceleration median / p95 / p99, ms | 16.742 / 18.757 / 20.266 | 16.758 / 18.591 / 19.858 |
| Handbrake median / p95 / p99, ms | 16.777 / 18.311 / 20.502 | 16.792 / 18.702 / 20.561 |
| Settled median / p95 / p99, ms | 16.813 / 18.714 / 20.315 | 16.828 / 20.596 / 24.195 |
| Last periodic allocations / recycles | 2,665 / 24,609 | 24,557 / 0 |
| Whole-session async GPU interval mean, ms | 12.329 | 12.624 |
| Process CPU seconds/wall second | 3.097 | 3.034 |
| Sampled peak private / working memory, MiB | 2,701.07 / 2,165.52 | 2,757.45 / 2,249.03 |

The preceding table and measurement boundaries still apply; preserve all five
passing runs. Each additional run has 355 valid GPU-memory counter records,
zero sampling errors, two known invalid simulation deltas and the startup
device-path error. There are no GPU errors/timing drops in these clean runs.

Final retained control C2 (`20260910T092856Z-p27056`) exits 0 but delivers only
22 of 23 scheduled inputs. Step 7, the A press at frame 720 (12 seconds), is
absent; the next observed step is its release at frame 726. The shared input
driver selects the latest state using `upper_bound`, so the 100 ms state is
not queued for later delivery. Telemetry establishes the skipped pulse, not
whether title polling or output-clock advancement caused that particular gap.

C2 independently passes clock alignment (3.624..18.713 ms origin bounds),
all seven HUD/pose/motion checks and manual race-stage review. Its clocks are
5.417/17.600/21.608 seconds. These do not override the preselected input gate:
**the block is stopped, no qualified six-run aggregate exists, and its 2x
block is unexecuted.** Raw C2 data and the failing check remain in
`matching-retention/race-1x-cabbac-c2/`; no passing substitute overwrites it.

A prospective route widens all eight 100 ms menu A pulses to 500 ms, retaining
their start times, the existing 500 ms signup X, braking, motion, capture and
measurement times. It is a different protocol requiring fresh qualification.
Local `matching-retention/wide-menu-pulses.fh1test` SHA256:
`B8D8D835C2A928888C10DADCD7E599AF3A5B221A2DC757D00894C1CC6BBAEC3C`.
No input-driver or production-renderer semantics change.

The first independent 1x two-frame RenderDoc probe uses that route, EXE
`EC2E5F...`, marker-only renderer `43E59C...` and runtime `955BDC...`.
Session `20260910T093402Z-p28600` reaches the race, then reports graphics-device
loss after writing one capture. The child result is a crash, exit `0xC0000409`,
ID `pscrash-v1-bcb03ba59c806a67c5bf`. It produces only six of twelve route images
and cannot pass a complete workload check. The capture wrapper is corrected
to inspect the injected game's result as well as RenderDoc's exit code; the
new check rejects this crash and accepts the archived normal 2x run.

Saved `matching-capture/1x-rdc/frame_frame4705.rdc` is 379,760,806 bytes, SHA256
`89EAE5DA93CC9A13B791768D779FE4517C13ACCDFAF5411C71ADE1B2931FCDEF`.
Its replay nevertheless completes a bounded byte/consumer audit:

- 40 actual copies, 3,866,624 bytes, 37 unique reused buffers; sizes are 64 KiB
  (22), 128 KiB (17) and 192 KiB (one). Twenty-two select a completed matching
  victim beyond the oldest cache entry.
- Every nonzero CPU upload source matches the entire destination after the
  copy, and every destination changes from its previous contents. The first
  bound draw consumer still sees those bytes: 18 index and 22 vertex reads.
- Each marker satisfies `retired <= completed < current`; observed ranges are
  15,898..15,902 retired, 15,901..15,904 completed and 15,902..15,905 current.
  These are per-copy relationships, not interchangeable range endpoints.

This is actual 1x GPU evidence for these CPU-sourced copies, **not** a passing
live session, a device-loss fix, GPU-written-source proof or streaming
qualification. The crash is not exonerated by matching bytes in its saved frame.
`matching-capture/1x-audit-4705/report.json` preserves every copy, consumer and
the successful bounded replay result.

The same-setup recycling-off control `20260910T093857Z-p8640` exits 0 and
writes both frames, 4525/4526. All 23 input steps, 12 route images and seven
HUD/pose/motion checks pass; capture-clock bounds are 2.772..22.709 ms. However,
it logs eight missing precompiled vertex-shader variants during menu prewarm
and seven invalid simulation deltas (zero GPU timing drops). It is neither an
error-free renderer qualification nor a performance control. Its normal exit
does not establish the cause of the recycling-on device loss. Preserve the
following missing keys as additional B1 coverage evidence:
`C44D26511712ACE0/7F`, `5B4289DDC7A64126/1FF`, `DAB93405F7249276/FF`,
`C4C6C4C536B7DEE7/7F`, `6F14A5029254F49D/1FF`, `B2C2DBC2FE68CD0F/7F`,
`364F8F67D6911DC7/FF` and `A1A31010058755BD/1FF`.

These control captures are `matching-capture/1x-off-rdc/frame_frame4525.rdc`
(368,788,955 bytes, SHA256
`7C0310929F29BCFF24EFA1AD7FA9E83202CE3BB0239D93FD8AB0DCB69219E72E`)
and `frame_frame4526.rdc` (325,191,416 bytes, SHA256
`DF915450B89BA87591A382642576191B6501F7796731151CEDCC4F4F66B26674`).
Neither is a recycled-copy proof. Raw results, clock/workload checks, manual
review and an explicitly preserved initial wrong-path tooling invocation are
under `matching-capture/1x-off-test/`.

Source inspection identifies a diagnostics gap: `D3D12Presenter` can return
GPU loss and trigger the fatal callback before the command processor logs
`GetDeviceRemovedReason`. Its two device-loss result paths now log both the
Present HRESULT and device-removal reason, and flush before returning. Success,
other failures and loss classification are unchanged. The executable
`tools/check-d3d12-present-loss.py` exercises those production branches,
including log/flush order and both HRESULT values; it passes.

The Release runtime build passes. Verified diagnostic runtime SHA256 is
`6B97FB8B1CF15DBBB1C6A0AD762399F40F3AAFAC1E4D0CB8B818D82DFB8E24CC`,
archived under `b2/present-loss-verified/`; source presenter SHA256 is
`4F52A5E7BF900226708DD2DB7113017340D8F4F9E906C27F68D89E539815F458`.
The first build's archive incorrectly copied the old top-level DLL; its unchanged
`955BDC...` hash exposed that error. The verified build forces recompilation and
archives the actual `rexglue-artifacts/rexruntime.dll` target before restoring
all retained runtime files. Unrelated kernel source bytes are preserved.

Initial attribution session `20260910T094848Z-p23300` enables the existing
`d3d12_debug` option, but fails DRED setup and DXGI factory creation under
injection before any gameplay or capture. It does not reproduce the earlier
in-race failure. Its two verified owned RenderDoc helper processes are stopped
after the game's terminal crash. No OS/debug-mode setting is changed. Continue
with the new error logging and debug explicitly off; capture diagnostics remain
separate from clean retention and every earlier failure stays archived.

The debug-disabled attribution probe `20260910T095025Z-p28636` then exits 0,
records all 23 delivered inputs and 12 images, and passes the seven HUD/pose/
motion checks. Capture-clock bounds are 2.816..24.798 ms; reviewed race clocks
are 5.559/17.200/21.217 seconds. It has six invalid simulation deltas, zero GPU
timing drops, no GPU errors and the known startup device-path error. The earlier
device loss does not recur; this does not prove it fixed or attribute its cause.

Replay of `matching-capture/1x-reason-rdc/frame_frame4634.rdc` checks 12 actual
recycled copies (1,179,648 bytes, 12 buffers), including four non-oldest matching
victims. All CPU sources are nonzero, destinations change to exactly match and
all first draw consumers retain those bytes (seven index, five vertex). Six
copies are 64 KiB and six are 128 KiB. This supplies bounded 1x byte/consumer
evidence from a normally completed live run. Sustained streaming, GPU-written
sources, full scenes and clean repeated performance remain outstanding.

The capture is 379,454,509 bytes, SHA256
`E6E4DE8C55B2680ABF6516DF935365752C5B30EFFE7459CFD933E10DCE053806`.
The adjacent frame 4635 is 338,631,713 bytes, SHA256
`C604E2982A8F81FE42CA79592D0B0617FEED113CDC0D39BC512CA6CD0450E023`;
it contains no marked recycled copies and its audit explicitly fails that
coverage assertion. It is not another passing proof. Reports are under
`matching-capture/1x-audit-4634/` and `1x-audit-4635/`; inspect their JSON results
because the replay process itself returns 0 even on a script assertion.

The presentation diagnostics are committed in SDK
`202247a233bad7d1cbd93d5b541521f9747132eb`. The candidate/marker GPU DLLs still
come from the preceding `acd222c` renderer source, whose bytes are unchanged.
All nine retained runtime files are restored after every probe. No B setting
is retained or enabled, no OS/debug setting changes, and all failed captures
and incomplete comparisons remain part of the evidence.

### B4 existing postprocessing hooks: static anchors

The existing default-off `disable_motion_blur` and `disable_depth_of_field`
settings already enter the generated guest code through
`config/rexglue/analysis/fh1-post-processing.toml`. An exact loaded-image check
verifies all four substituted instructions and their generated owners:

| Hook address | Original instruction | Generated owner / immediate behavior |
| --- | --- | --- |
| `82D7894C` | `D1030050`, store float f8 to r3+80 | `sub_82D78810`; motion-blur flag skips this store |
| `8245B494` | `817F18FC`, load r11 from r31+6396 | `sub_8245AEF8`; forcing zero selects the mode-not-2 branch |
| `8245846C` | `817F18FC` | `sub_82457E98`; forcing zero makes the mode-is-1 boolean false |
| `8245849C` | `817F18FC` | `sub_82457E98`; forcing zero selects the mode-not-2 branch |

The earlier f8 load from `8201F194` (500.0) is overwritten before the motion-blur
hook. Exact instruction `C11F9520` at `82D788D0` reloads f8 from `82129520`,
whose initial image value is approximately 0.075 (`3D99999A`). Generated dataflow
confirms no further f8 write before the hook at `82D7894C`. The runnable local
`b4/trace-motion-blur-store.py` checks both retail instructions and generated
dataflow; `motion-blur-store-dataflow.json` records the image/source hashes.
The initial image value still does not establish its live value or zero prior
destination contents when the store is skipped. Trace lifetime/consumers and
dynamic calls before attributing savings. Depth-of-field callers, skipped
side effects and actual GPU work also remain unqualified. Local evidence is
`b4/post-processing-static-anchors.json`, including generated-source hashes.
These anchors identify existing controls to test individually; they add no
profile/default, B3 bypass claim, B4 completion or NPC/UI timing qualification.

### Shader misses traced to stale staging; prospective comparison v2

The eight vertex variants reported by `20260910T093857Z-p8640` already exist
in the current local offline packs. The installed 1x pack had 21,987 entries;
the newer local pack has 22,012. All old entries retain identical bytecode,
bindings and metadata; the 25 additions include all eight reported keys.
All 28 entries in the existing race-misses manifest match the newer pack.
The installed 2x pack already matches its current local counterpart, which
also contains all eight keys. This resolves these observed misses as stale
test staging, not newly discovered shader-generation work. Broader B1 coverage
remains required.

`launch-preview.ps1` deliberately skips automatic pack/prewarm staging when
`RenderTestScript`, `ShaderCaptureDir` or `DiscShaderCorpusDir` is provided.
The local comparison wrappers had relied on the existing AppData pack. They
now use the existing `native-shader-pack.py stage` command and pin pack/catalog
hashes before and after each run. Public launcher semantics are unchanged;
the [automation procedure](FH1_RENDER_TEST_AUTOMATION.md) documents this setup.

| Pack | Entries | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| Previous installed 1x, preserved locally | 21,987 | 468,092,976 | `D147EE68C87D0298E0C1C394A83F68597492D4A0385BF507540EC63D9DCBA765` |
| Current 1x, now staged | 22,012 | 468,825,976 | `1636179BF8633D7406C7C3C735DD600C0C05666D8A8A8CAC188433730A38C026` |
| Current 2x, already staged | 22,012 | 473,489,272 | `D6E62162510BE0EDFC0CA4D1624B498F51024F7BC5AC2597A23C37929E030A3E` |

Both current packs use translator `20260827`, NVIDIA vendor `10DE`, flags 9.
Evidence is `.local/native-renderer/b1/shader-misses-20260910/`, including
`initial-audit.json`, `pack-delta.json` and `stage-1x.json`. No new shader source
or generated bytecode is needed, and the old failed comparison is preserved.

A new preselected C-A-B-B-A-C block at 1x, then 2x, uses the widened 500 ms
menu pulses and explicitly pinned packs. Every condition uses test EXE
`EC2E5F097A3D513AE945B42B9E1EE01822A9E2DA7EEA08F5DD91B7E8F3243D30`
and presentation-diagnostic runtime
`6B97FB8B1CF15DBBB1C6A0AD762399F40F3AAFAC1E4D0CB8B818D82DFB8E24CC`.
C uses retained renderer `27B486...`; A/B use unchanged clean `3A0B434A...`
with recycling off/on. Source checkpoint is main `5b94b87`, SDK `202247a`;
the clean candidate still comes from `acd222c`. Debug, narrow invalidation,
containment and tile ownership are off, with no per-draw/corpus/M4 profiling.

Catalog pins are `fh1-native-shaders-v2.bin`
`09F6FDC0FBD9961BA000A2B30B3839FA9D4BA0292D09F7FA436EC4B761D0613E`,
`fh1-native-pipelines-v1.bin`
`105019AD7CD33EB8F30D638FFCE891FA142553E47959615BC633144A6B618DD5`,
and `fh1-gpu-prewarm-v3.txt`
`00996D675B29B7920D5FA7C2D0402936064AF3FED0457FB7EB838D9511C5F6BA`.

Only C1, session `20260910T100454Z-p25840`, is complete at this checkpoint.
It exits 0, loads 22,012 precompiled shaders, delivers all 23 inputs and
records all 12 captures. Clock and seven HUD/pose/hold/motion checks pass.
Manual review shows a stopped signup, Start Race menu at 62 seconds and race
clocks 5.517/17.607/21.615 seconds at 76/88/92. Subsequent runs must remain
within the preselected 0.5-second spread. There is no competing build/replay,
no GPU error or timing drop; two known invalid simulation deltas and the
startup device-path error remain. This is bounded validation of correct pack
loading, not complete shader coverage or a fix for the earlier capture loss.

| Source-frame window | Frames | Median ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: | ---: |
| Early race, 78..86 s | 115 | 62.656 | 112.635 | 120.540 |
| Hold, 94..114 s | 1,193 | 16.734 | 18.830 | 20.855 |
| Acceleration, 118..120 s | 118 | 16.531 | 18.600 | 19.653 |
| Handbrake, 124..130 s | 356 | 16.604 | 19.644 | 28.445 |
| Settled, 134..140 s | 364 | 16.348 | 18.016 | 18.668 |

Clock offset is bounded to 4.349..19.928 ms; capture-containing intervals are
excluded. Whole-session asynchronous GPU mean is 12.207 ms; whole-process
CPU is 3.024 CPU-seconds/second and total OS faults average 2,873.55/second.
Sampled private/working peaks are 2,751.48/2,219.36 MiB. There are 355 valid
GPU-memory counter records and zero sampling errors. Early-race sampled
dedicated/shared/total-committed peaks are 1,228.03/194.18/1,422.21 MiB.
Local/dedicated and nonlocal/shared overlap and must not be added twice.
Acceleration has no OS samples inside its conservative window; it is unavailable,
not zero. Last periodic imports/CPU imports/hits are 52,378/51,833/18,350,080
with a 32 MiB geometry allocation budget. Retained C lacks allocation/recycle
counters. These are sampled or periodic observations, not exact session totals.

Plan, per-run hashes, raw logs, metrics and manual review are under
`.local/native-renderer/b2/matching-retention-v2/`. Resume the local
`b2/run-matching-retention-v2.ps1 -Scale 1 -Labels a1`, then B1/B2/A2/C2,
reviewing each run with `summarize-retention-v2-run.py`, contact images and
`record-retention-stage.py` before continuing. Stop the block on any failed
gate; do not mix these results with v1 or substitute a passing repeat. After
all six pass, use `summarize-retention-v2-block.py 1`; repeat the prescribed
block at 2x. No recycling retention or B-item completion is claimed.

### V2 stops on an early HUD gap; trace the indirect-buffer submission

The next four 1x runs finish, but the fourth fails its HUD gate. Preserve the
entire v2 block; final C2 and all 2x runs are unexecuted. The prior resume
instructions above are superseded. Do not substitute another A2 or relax the
early-HUD requirement.

| Run | Session | Result |
| --- | --- | --- |
| A1, recycling off | `20260910T101325Z-p2488` | All input/clock/HUD/pose/motion gates pass |
| B1, recycling on | `20260910T101615Z-p2360` | All gates pass |
| B2, recycling on | `20260910T101908Z-p4164` | All gates pass |
| A2, recycling off | `20260910T102201Z-p23016` | Normal exit, all 23 inputs and 12 capture/clock checks; no HUD at 76 s |

A2's six later HUD checks and pose/motion checks pass. Manual review confirms
the stopped signup and prestart menu, but the missing 76-second race clock
cannot be inferred from its later 17.592/21.600-second clocks. No GPU errors
occur, and the correct 22,012-entry pack loads. This is a recurrence of the
intermittent HUD defect with the updated pack and wider inputs, not another
shader miss or missed controller pulse. The full six-run summary rejects the
incomplete failed block; raw A2 logs/images remain available.

The four passing v2 runs have these source-frame results, in ms. Each cell is
median/p95/p99, with the same conservative capture/clock exclusions as before:

| Window | C1 retained | A1 off | B1 on | B2 on |
| --- | --- | --- | --- | --- |
| Early race | 62.656 / 112.635 / 120.540 | 65.954 / 101.961 / 134.789 | 25.345 / 33.317 / 36.573 | 24.907 / 32.289 / 38.088 |
| Hold | 16.734 / 18.830 / 20.855 | 16.818 / 20.297 / 21.881 | 17.006 / 21.178 / 25.725 | 16.842 / 20.721 / 25.745 |
| Acceleration | 16.531 / 18.600 / 19.653 | 16.576 / 21.001 / 25.293 | 16.783 / 18.488 / 20.070 | 16.782 / 18.732 / 21.155 |
| Handbrake | 16.604 / 19.644 / 28.445 | 16.871 / 20.606 / 21.642 | 16.818 / 20.169 / 24.033 | 16.777 / 18.836 / 20.454 |
| Settled | 16.348 / 18.016 / 18.668 | 16.780 / 18.745 / 20.951 | 16.796 / 18.680 / 20.385 | 16.731 / 19.111 / 20.498 |

The repeated early reduction is promising, but hold p99 is worse in both on
runs and the required controls/2x/full scenes remain incomplete. No optimization
is retained. A1/B1/B2 last periodic allocations are 25,367/3,962/4,223; recycles
are 0/31,541/31,639. These are periodic observations, not exact final totals.

| Whole-process/session measure | A1 off | B1 on | B2 on |
| --- | ---: | ---: | ---: |
| Async GPU mean, ms | 12.500 | 12.503 | 12.268 |
| CPU seconds/second | 3.055 | 3.115 | 3.118 |
| OS faults/second | 2,864.34 | 2,776.58 | 2,791.99 |
| Sampled private peak, MiB | 2,743.09 | 2,709.57 | 2,707.07 |
| Sampled working peak, MiB | 2,210.63 | 2,171.82 | 2,186.14 |

Each passing run has 355 valid GPU-memory counter records, zero sampling
errors, two invalid simulation deltas and zero GPU timing drops. Per-phase CPU
usage is now derived from the existing OS samples, with no added game work:
early C1/A1/B1/B2 use 2.849/2.790/3.255/3.327 CPU-seconds/second over roughly
6.1-second sampled spans; hold uses 3.135/3.206/3.174/3.211 over roughly
18.2 seconds. These are process rates on the independently aligned OS clock,
not renderer CPU durations or CPU/GPU row pairs. Short phases with fewer than
two samples remain unavailable. Earlier metric reports are preserved and an
equality check confirms only the added phase-CPU fields changed.

#### Decoder boundary and publication probe

A separate 94-second diagnostic reuses the wider startup inputs and captures
every half-second from 72 to 84 seconds, plus 88/92. All 32 captures and 21
inputs are accounted for; the 27 racing captures retain the expected pose.
Temporary SDK instrumentation counts packets before predication, query-based
draw kills and backend calls for the three sampled HUD shader groups. It also
links capture resources to completed output records. Rendering, packet skipping
and resource algorithms remain unchanged, with recycling off.

Session `20260910T103154Z-p22848` exits 0 and reproduces missing HUD at
74.5, 75.0, 76.5, 78.5 and 84.0 seconds. Accounting passes for 1,307 source
frames. The first shader group still has 12/12/4 calls in the first three
missing captures, while the other two groups have none; all three are absent
in the last two. Sampled HUD use does not make the first shader HUD-exclusive.
No observed HUD-group packet is predicated or query-killed. However, hundreds
of indirect-buffer packets are skipped elsewhere in each source, so this probe
alone cannot rule out skipping a parent buffer before parsing its HUD draws.

The first analysis incorrectly expected an unchanged submission-frame number
across `EndSubmission(true)`. Source inspection and all 6,346 output pairs
show an increment of one with an unchanged source ID. The corrected check
preserves both identities; the initial assertion log is retained. No observed
same-resource publication conflict occurs during captures. This remains
diagnostic output evidence, not proof of continuous host-visible behavior.

#### Indirect-buffer references before predication

A second probe copies the existing `RingBuffer` reader to inspect both IB
arguments without advancing the production reader. Binary records preserve
source, opcode, parent/offset, target, length, mask/select and packet header.
Every record is checked against independent decoder opcode/skip totals.

Session `20260910T103956Z-p30256` exits 0 with all input/clock/pose checks and
32 captures; HUD is missing at 74.0 and 78.5 seconds (sources 5674 and 5736).
It records 1,857,941 IB descriptors across 1,285 source frames: 133,771,752
bytes, SHA256
`4B454196D100F46D10D3A5E75E49F81CD08512B16A94148CF64EEF5ECE4F126C`.
All descriptor counts and predicate decisions match the decoder records.

Visible HUD captures include two full IB references of 2,475 and 4,076 words
to the observed UI buffer pool. In each missing capture, all 28 references
to those observed addresses are only 16 words long, and none is skipped.
The full references are absent. For example, visible source 5666 submits
`16E37620/2475` and `16E0AB60/4076` through wrappers `1317C800/23` and
`1317C880/46`, reached from primary buffer `12EA12C0`. Headers are `C0013F00`
with all lower 32 mask/select bits set. Later visible source 5679 uses other
pool entries through the same 23/46-word wrapper shapes.

This narrows the next investigation to production/submission of the full
lists and their wrappers. It does not prove what the 16-word contents mean,
that address reuse preserves contents, or that no other skipped parent could
matter. Reverse address graphs can include repeated uses within one source;
they are leads, not a substitute for ordered producer/lifetime evidence.

Both diagnostics use test EXE `EC2E5F...`, the pinned current 1x pack/catalogs,
and unchanged renderer algorithms from SDK `202247a`. First GPU SHA256 is
`B809346E65F1A297F8D6F0F3CCF42EAD92550A7E1B2B68948D6202E974BC403F`;
the IB extension is
`81CBF64F7A6584D73B638419384A2CF90EB82C2922C93F3A94B6967152CD40AB`.
Both use capture-logging runtime
`0558BADA33DB85F57C27C8404F3A0A3076A846BF22378E6E58F00282B2C7A52E`.
The diagnostic route SHA256 is
`0154B43DB9BE993C0DFD600B5B82B824722C4581310576BA44B51755C59F5E59`.
Both have two invalid simulation deltas, zero GPU errors/timing drops and the
known startup device-path error. These runs cannot establish performance gains.

Evidence and runnable local make/build/run/analyze helpers are under
`b2/hud-decode-profile/`, `b2/hud-ib-profile/` and the enclosing `b2` directory.
Reports preserve all missing images; source snapshots and hashes identify the
temporary instrumentation. Static IB-header candidates include `82416A00`,
`829E8E00`, `829EC400`, `8246FB98` and `82409398`; two other immediate-value
matches are unrelated. The existing `PinyonShiftObserveSceneCommandBuffer`
hook may help identify the live producer, but has not yet been matched to these
HUD lists. The B4 f8 dataflow correction above also remains a static lead.

### CPU submission, queue and dispatcher evidence

Four further local diagnostic builds follow the existing scene-command-buffer
hook upstream. **No production rendering change is retained.** The stopped v2
comparison remains stopped, and no B item completes here.

| Probe | Session | Result |
| --- | --- | --- |
| List heads and CPU submit | `20260910T110052Z-p27160` | Missing HUD at 73.0, 73.5, 74.0, 76.5 and 78.0 s |
| Queue/caller recovery | `20260910T110833Z-p30612` | All 27 HUD captures visible; 17 source frames in the 72–84 s diagnostic window still lack group-2 draw packets |
| All ordinary dispatcher decisions | `20260910T111433Z-p12484` | Reaches the one-million-record cap; diagnostic error rejects the decode gate; prefix evidence only |
| Three relevant dispatcher callbacks | `20260910T112214Z-p6248` | Complete diagnostic accounting; missing HUD at 77.0 s |

All four exit normally with all 21 inputs and 32 capture/clock checks. The
three complete decoder reports also verify all 27 race poses. Each run records
two invalid simulation deltas and zero GPU timestamp drops. Present-drop totals
are 3/43/69/3 respectively; these instrumented runs are not performance
comparisons. The existing startup device-path error persists. The broad probe's
additional GPU-category diagnostic error is preserved, not waived. The queue
run's passing images do not establish continuous HUD visibility or a fix.

The copied-reader heads are linked to exact per-source IB ordinals, including
repeated buffer addresses. For every known HUD-buffer reference in the first
run's 27 captures, the CPU trace matches header destination, target, word count
and packet before decoding. Its first 16 words are four identical type-0 writes
to `PA_SC_WINDOW_OFFSET` and the two window-scissor registers: offset/TL zero,
BR `0x02D00500`. **The short lists contain no draws or nested IBs.** Visible
captures have full 2,475/4,076-word lists. Each missing capture has 28 short
references and no full reference. This is evidence of CPU-submitted short lists,
not just a downstream renderer failure to issue their draws.

The checked call path is:

```text
82450160 ordinary-job dispatcher, callback return 8245032C
  -> 8249CC40 callback thunk, tail-dispatch through live vtable + 228
  -> 824726C8, consume one of twelve 60-byte queue slots
  -> 8246E8F8, wait on slot + 28 and submit slot + 20
  -> 82416A00, observed pre-store at 82416F18
```

The live queue owner is `402BBD10`, vtable `820033FC`. All 10,753 queue records
in the second run match `slot = owner + 1136 + 60 * read_index`, with indices
in 0–11, and match the original CPU trace's timestamp/object/word count. The
consumer advances `owner + 1884`; producer finalization at `823E97F8` uses
`owner + 1888`. These are sampled indices, not proof of matching generation
or completion. The wait helper reaches `NtWaitForSingleObjectEx` with an
infinite timeout; its live result has not yet been recorded.

The broad dispatcher trace covers 1,000,000 decisions in 14.989 seconds before
saturating. It is kept under `b2/hud-dispatch-profile/`, including its failed
decode analysis. A first direct-callback-address filter found no consumers:
`8249CC40` is the tail thunk, so the saved caller LR alone does not identify the
immediate callback. Corrected prefix matching associates 1,842 short submissions
with dispatcher input mode 1 at caller `8259FB14`, versus 609 full and 15 short
submissions in mode 0 at `8259FA90`. This is incomplete prefix attribution.
The dispatcher's special earlier callback is `82C09C08`, which changes the
nesting counter at dispatcher + 140; an initial metadata label `82C19C08` was
an address-arithmetic error. It was never the instrumented branch.

The narrowed trace records only checked thunks `82472A68` (vtable + 220,
begin), `823E6620` (+224, finalize), and `8249CC40` (+228, consume). It covers
28,440 decisions, 9,480 per callback, all executed. All 11,679 observed CPU
queue submissions match preceding decisions on the same thread and owner:
5,544 full submissions use mode 0; 6,093 short submissions use mode 1; 42 short
submissions also use mode 0. The dispatcher intentionally skips ordinary
callbacks when its input mode is nonzero and its computed conditional flag
is true; the three queue callbacks have node byte 16 set and remain executed
in both modes. No guest branch or queue behavior has been changed.

**The 77-second failure has 20 short known-HUD references from mode 1 and two
short references from mode 0, with no full HUD lists.** Its visible neighbors
have full mode-0 lists, sometimes after short mode-1 submissions. Therefore
simply suppressing drain-mode presentation would not resolve the evidence.
Trace command-list begin/finalize and the producer-to-consumer generation
handoff next, including the nested job queues and normal-mode empty lists.
Preserve queue completion, waits, guest side effects and presentation ordering;
do not replay old HUD commands or classify correctness from HUD visibility alone.

All diagnostics reuse the 94-second route `0154B43D...`, complete staged 1x
pack `1636179B...` and unchanged catalog pins. Runtime DLL is
`0558BADA33DB85F57C27C8404F3A0A3076A846BF22378E6E58F00282B2C7A52E`.
Exact EXE/GPU hashes, in table order:

- Submit: `4BEFBB1CFF03535E2070F25CBA4084DD184C13CF9AC2F2E01EA79A58371E43B1` /
  `E7673F38541FFB4EC2478A7995044D124B04185943A27D6D29CCFEAEC00B972C`.
- Queue: `EF6E8C7401D3772061CA70ECC09F550EC6D251B929A7D4AE0EDD4EE688CB6212` /
  `4485308ADA59B78B775619F5422492327B30175E32E8866E8023373D92DA3BC1`.
- Broad dispatcher: `D329E211F962A8C14B7E272EAE1C86FBBF5B69631070A800CB11885C8687F52A` /
  `3E0636AAD469D898BC6407FC639A3EFA1EC7C5F2C2D0036711706DE426E10FDB`.
- Filtered dispatcher: `DD61608FA54E27FBC847F048B0F8891AB6881ABF6D14700A4714214DB47B7708` /
  `FEAF57A2FCCF500F4E0CA3C8D6F0AF8DB38CF9B6946DFD611A053A28C7C6EEF6`.

The complete probes validate 1,817,979 / 1,910,720 / 2,204,837 IB records against
independent packet counts, plus 22,892 / 24,052 / 26,883 ordered list heads.
Their raw streams, source snapshots/patches, manifests and make/build/run/analyze
helpers remain under `.local/native-renderer/b2/`. The filtered dispatch stream
SHA256 is `F75E7C6E69A8B5C14D6A9BFE4149CD00403750EB5F0CA21FF19500C333AFBFF0`.
The initial preparation attempt rejected a mistaken 64-bit saved-LR assumption;
the checked guest prologue uses a 32-bit `stw`. Its failed preparation is also
preserved. Local analyzers are runnable checks, not evidence of B retention.

Four Release builds and geometry-cache checks pass. Direct hashes verify all
nine retained runtime files and every modified diagnostic source restored;
unrelated SDK kernel/libmspack edits and saves remain intact. Retained EXE is
`372161...`, GPU `27B486...`, runtime `955BDC...`. No game/build/replay remains
active. A6 remains symmetric-1x-only, recycling stays off, and the full B1-B4
scene, lifetime, producer-bypass and visual/timing qualification remains open.

**Next:** attribute the 16-word contents, ordered wrapper publication and the
actual CPU producer before changing behavior or restarting retention. Preserve
queries, fences and guest-visible side effects. The v2 block remains stopped;
the full B1 scene set, B2 streaming/lifetime/tails, B3 pre-packet bypass and B4
visual/NPC/UI timing remain required. All nine retained runtime files and
original SDK source bytes are restored, with unrelated dirt and saves preserved.

### Empty normal-mode lists originate in producer-side job discards

Two additional read-only probes follow the previous dispatcher evidence.
Neither changes rendering behavior or qualifies a performance setting.

**Lifecycle probe:** `20260910T114031Z-p26872`, local
`b2/hud-lifecycle-profile/`, exits normally with 21/21 input steps, 32/32
capture-clock checks and 27 expected stationary Recaro poses. Decoder/IB,
list-head, CPU-submit, queue and dispatcher checks pass. There are 1,291
profiled source frames and 1,837,833 IB records. HUD disappears at 77 and
81 seconds; a six-image contact sheet confirms both gaps between visible
neighbors. Present-drop deltas total 28, invalid simulation deltas 2 and
GPU timestamp drops 0; these instrumented timings are not benchmarks.

The new lifecycle stream contains 49,518 records for 7,074 complete slot
generations. Every checked generation closes successfully, waits successfully,
and preserves its recorded object metadata from close to consumer wait.
9,486 CPU submission records join those generations. The cursor does not
advance between begin and finalization for either missing capture's two
normal-mode HUD lists. No ordinary drawing jobs occur in those intervals;
visible neighbors do execute drawing jobs and advance their cursors. This
moves the investigation upstream of finalization and submission.

The broad work stream completes at 1,230,383 decisions without saturation.
The lifecycle window, however, begins later than the dispatcher window:
capture 72.0 precedes it. Its full-coverage result is explicitly **failed**;
the remaining 26 captures, including both missing HUD cases, have complete
lifecycle joins. Preserve `lifecycle-analysis-coverage-failed.log` and the
report's `passed: false`, alongside `analysis_passed: true`. Three consecutive
same-thread events share a clock sample; the earlier strict-timestamp failure
is preserved and ordering now permits equal samples without permitting reversal.
Two fixture-preparation attempts rejected non-unique source anchors before
compilation; their directories remain archived. Source and runtime restoration
ran after each attempt.

**Enqueue probe:** `20260910T115046Z-p25232`, local
`b2/hud-enqueue-profile/`, also exits normally with 21/21 input steps and
32/32 capture-clock checks. Its shared-enqueue trace reaches the two-million
record cap after 11.2064167 seconds of tracing. The decoder analyzer rejects
the GPU-category cap error; no complete decoder/capture report or retention
claim is made for this run. Present-drop deltas total 2, invalid simulation
deltas 2 and GPU timestamp drops 0. Both runs retain the known startup
`ResolvePath(\Device)` error.

The separate, explicitly failed-run prefix report validates 666,666 completed
enqueue calls and leaves the final entry/decision pair incomplete. It observes
280,353 appended nodes and 386,313 discarded jobs. All observed discards use
queue `4015A010`, byte 149 = 1, job flag = 0, nesting counter 144 = 0 and
state 172 = 0. These are the actual inputs to the guest discard branch, not
an inferred GPU rejection.

Exact node/callback/owner/payload and recording-list joins connect 3,042
complete producer cycles to dispatcher decisions, slot lifetimes and CPU
submissions. **48 cycles discard their drawing jobs but subsequently begin,
finalize and consume in normal mode 0, submitting a 16-word list.** Their
command cursors remain unchanged before finalization; none appends a traced
drawing job. The discard totals per cycle are 9 (16 cycles), 21 (16),
591 (14) or 592 (2). The observed callback families are bounded to the 21
families selected from the earlier trace. This prefix proves the producer
discard/normal-consumption mismatch; it does not waive saturation, establish
coverage of every HUD state, or prove a correction.

Static path for the next implementation:

- Shared enqueue wrapper `823F4FE8` calls `823F4B30`. The latter has 633
  wrapper call sites and other paths; preserve their contracts.
- At `823F4C10`, queue byte 149, job flag and nesting counter 144 determine
  admission. The discard path starts at `823F4F08`; successful node linkage
  ends at `823F4F04`. Payload destruction/freeing on discard matters.
- Queue publication code in `82C0D3EC` sets byte 149 when a queued tail remains
  or queue counter 128 exceeds threshold 132; the alternate branch clears it.
  Trace its frame identity and policy before deciding a correction. Do not
  force every job to execute or replay stale HUD contents.
- The worker `82472908` reads the shared mode at parent +6684 and forwards it
  through `82473DE0` to the embedded queue at parent +2816. The main dispatcher
  and this worker run on different host threads. Producer discard policy and
  later consumer mode must be treated as distinct decisions.

Binary identities (SHA256):

| Probe | EXE | GPU DLL |
| --- | --- | --- |
| Lifecycle | `18650E344AB473A2CC560FEFA9AB8C89B7E43498B88575C215DE160C964CDB6B` | `8F466021AFC643F18C74E32F51257F015FC4D7CEBC05D8EA9B690F2DC69EE86B` |
| Enqueue | `9D0867032220489070E6C8A92F18C5EC01511293A06E3CD05E3F0225645D274A` | `52AB1B32E4A440830648928633AAEC2F7132C7A0605B99A2DEA5834B5C420F81` |

Both use diagnostic runtime
`0558BADA33DB85F57C27C8404F3A0A3076A846BF22378E6E58F00282B2C7A52E`
and the same pinned complete 1x pack/catalogs and 94-second route as the previous
probe. Lifecycle stream SHA256 is
`24F480B9A9E0FC4C220B61B4C6A09019F84BF7FD2C2FF96E4568DDB4A22E9BA7`;
the saturated 384,000,000-byte enqueue stream is
`097556C3E7928DB546A2BD7BDE3FEE74D54B44BC5694A926C7D0C4631F1C2660`.
Source snapshots, diffs, binary manifests and runnable analyzers are local.

Both Release builds and geometry-cache checks pass. All diagnostic source
bytes and nine retained runtime files are restored and directly verified;
EXE `372161...`, GPU `27B486...`, runtime `955BDC...`. No game/build/replay is
active. Unrelated SDK dirt and saves remain intact. A6 remains symmetric-1x-only,
recycling remains off, retention v2 stays stopped, and every B1-B4 requirement
remains open. Next work is a correction to the producer/consumer frame policy
with bounded diagnostics, followed by the full outstanding qualification.

### HUD admission prototype passes bounded correctness checks

Local prototype `b2/hud-keep-profile/`, session `20260910T120707Z-p30068`,
changes producer admission at `823F4C10`. It retains jobs for a checked HUD
renderer between matching begin/finalize recording markers. The existing
dispatcher still decides whether to execute or drain those recorded jobs.
This is a behavior-changing experiment, not another read-only probe, and it
is **not retained in the production source or staged runtime**.

The checked policy path is queue publication `82C0D070`: a remaining tail or
counter 128 exceeding threshold 132 sets byte 149 through `82C0D3EC`; otherwise
it clears the byte. That producer policy can discard drawings before the later
worker chooses normal mode. The prototype postpones that discard opportunity
for the HUD recording span only. It preserves node flags, guest allocation,
payload ownership and dispatcher skip branches. It does not replay old HUDs.

The local helper uses one thread-local `{queue, recording_list, owner}` span:

- At begin callback `82472A68`, reset the span. Set it only for a nonzero
  recording list and an owner whose retail vtable is `820033FC`.
- At finalize callback `823E6620` for the same queue and owner, clear it.
- For intervening jobs matching all three fields, branch to normal recording
  at `823F4C3C`; all other admissions keep the original policy.
- Both boundary callbacks retain their original admission. The hook runs after
  the existing invalid-state/null/direct-execution paths. No fixed live owner
  address is used. Nested/interleaved producers, list reuse and other HUD states
  still require qualification before this can become a permanent hook.

The Release build and geometry-cache checks pass. The 94-second 1x route exits
normally with all 21 inputs and 32 capture-clock checks; origin bounds are
3,617–19,388 microseconds. All 27 stationary Recaro poses and automated HUD
checks pass. A six-image review at 72/76/77/81/84/92 seconds confirms visible
race HUDs, including the two times that failed in the earlier lifecycle probe.
This sampling does not establish continuous visibility or complete race motion.

The diagnostic chain passes decoder, IB, list-head, CPU-submit, queue,
dispatcher, lifecycle and selected enqueue-outcome checks:

| Evidence | Result |
| --- | --- |
| Profiled source frames / IB records | 1,264 / 1,795,234 |
| Ordered list heads / CPU records | 22,820 / 13,131 |
| Complete slot generations / joined queue submissions | 8,421 / 10,137 |
| Lifecycle records / ordinary work decisions | 58,947 / 1,549,312 |
| Selected enqueue outcomes | 856,366 appended; no discards or cap error |
| Complete producer cycles / fully joined cycles | 4,071 / 3,893 |
| Jobs recorded despite old discard inputs | 506,175 |
| Matched drain cycles still submitting 16 words | 3,537 |
| Matched normal cycles / empty normal cycles | 356 / 0 |

The selected enqueue stream covers 13.9581872 seconds within its 70–84 second
window. It logs one outcome per selected callback, removing redundant entry
and decision records that saturated the prior probe. Lifecycle coverage now
starts earlier and includes every capture. Exact node/callback/owner/payload,
recording-list and node-reuse checks join producer cycles to dispatcher,
slot lifetime and CPU submission. All checked closes and waits succeed, and
object metadata agrees across the handoff. The dispatcher-wide queue join has
5,769 short mode-1 submissions and 4,368 full mode-0 submissions; none is short
in mode 0. The narrower enqueue cycle counts above have a different window.

Present-drop deltas total **51**, invalid simulation deltas 2 and GPU timestamp
drops 0. The existing startup `ResolvePath(\Device)` error persists, with no
GPU-category errors. These heavily instrumented results cannot establish a
performance improvement or acceptable queue/memory pressure. Longer payload
and node lifetime is the main new risk; no clean tail or memory claim is made.

Exact SHA256 identities:

- EXE: `AFBFBE9977E36D30E95394962F461FDAEEB6038DAA54D11B9E734DF76DB61B2D`.
- GPU DLL: `E02CBB8579D2F58F15E22CD735F6066E40D3D33938759955EE68DFD220DE0C0D`.
- Runtime: `0558BADA33DB85F57C27C8404F3A0A3076A846BF22378E6E58F00282B2C7A52E`.
- Enqueue stream, 164,422,272 bytes:
  `42044D017E37EF6E0E72388946F7DAD857539A5E36CBF1596369F4F802F6657B`.
- Lifecycle stream, 16,976,736 bytes:
  `7C04F3930666D2EB7BC783423E320243A98A9C0563BA201E0151CB1BC8310886`.
- IB stream, 129,256,848 bytes:
  `4852BEFDA6C3279812C93362D1D060B2E3263B3E55E57E46328634DC0E68BAE8`.

The route remains `0154B43D...`, complete 1x pack `1636179B...`, with the same
catalog pins. Local `make/build/run-hud-keep-profile` scripts preserve source
snapshots, patches, manifests and binary evidence. Run the existing
`analyze-hud-{decode,indirect,submit,queue,dispatch,lifecycle}.py` stages in that
order, followed by `analyze-hud-enqueue-prefix.py <run-directory> --outcomes`.
The latter mode requires complete lifecycle/HUD coverage and an unsaturated
stream; the older rejected-prefix mode and its failed evidence remain intact.
The lifecycle report's inherited read-only description was corrected, with
all evidence and qualification fields verified unchanged. These local tools
and generated/binary artifacts remain outside the public repository boundary.

**Resume:** qualify a clean version of this admission change for queue/payload
lifetime and memory, other HUD/menu states, representative motion and repeated
1x/2x comparisons. Reuse the existing OS memory/CPU sampling and route gates.
Keep retention v2 stopped; this new design needs its own prospective protocol.
No optimization, B item or production HUD fix is retained by this one run.

All nine retained runtime files and nine instrumented source files are restored
and directly hash-verified. EXE remains `372161...`, GPU `27B486...`, runtime
`955BDC...`; the complete 1x pack is staged. No game/build/replay remains active.
Source before this checkpoint is main `9a03911`, SDK `202247a`. SDK kernel and
libmspack dirt and saves remain preserved. A6 stays symmetric-1x-only; recycling
stays off. Full B1 scenes, B2 mutation/streaming/tails, B3 actual pre-packet
bypass and B4 measured visual/NPC/UI timing remain open.

### Clean HUD admission: both preflights pass, 1x comparison remains unqualified

`b2/hud-keep-clean/` contains the exact previously traced HUD-span helper,
without per-job logging. Its single EXE switches admission off/on with
`PINYON_SHIFT_EXPERIMENT_HUD_KEEP_RECORDING=0/1` and logs that choice once.
The generated-source edit remains local; the production hook is not retained.
An executable assertion check compiles that helper directly and exercises
begin/end boundaries, wrong owner/list/queue, absent list, wrong vtable,
replacement begin and thread isolation. It and the Release build pass.

Exact EXE SHA256 is
`20EE2F2D48BD2B83124D4812104F57631B53FB4794658CBA75B97E1419C0F319`.
All following runs use retained GPU
`27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50`
and presentation-diagnostic runtime
`6B97FB8B1CF15DBBB1C6A0AD762399F40F3AAFAC1E4D0CB8B818D82DFB8E24CC`.
Recycling, narrow invalidation, containment, owned clear and D3D12 debug are
off. The complete 1x/2x packs, catalogs and widened-pulse route `B8D8D835...`
are pinned. Existing OS CPU/private/working/fault/GPU-memory sampling is reused;
no per-job traces or competing compilation are active during gameplay.

Two enabled preflights under `b2/hud-keep-preflight/` pass normal exit, all
23 inputs, 12 captures/clock checks, seven HUD/pose checks and the acceleration,
braking and settling gates. Manual contacts confirm signup/prestart state,
visible race HUDs and matching race clocks. These have no matched controls:

| Scale / session | Early median / p95 / p99 ms | Hold median / p95 / p99 ms | Peak private / working MiB | Whole-session GPU ms |
| --- | --- | --- | --- | --- |
| 1x / `20260910T122310Z-p21644` | 50.342 / 109.044 / 117.828 | 16.539 / 18.536 / 21.211 | 2726.86 / 2210.96 | 12.136 |
| 2x / `20260910T122642Z-p26996` | 79.785 / 110.241 / 113.604 | 16.842 / 20.460 / 23.708 | 4973.66 / 2238.46 | 14.281 |

Each preflight has two invalid simulation deltas, zero GPU timing drops and
only the known startup device-path error. Present-drop totals are 21/9.
The 1x GPU-memory sampler preserves one error and 350 valid counter records;
2x has no errors and 355 valid records. These are bounded motion/pressure
observations, not a leak test or proof of acceptable overhead.

A new prospective **A-B-B-A** comparison under `b2/hud-keep-retention/` isolates
HUD admission: A off, B on, identical EXE/GPU/runtime and sampling. It is separate
from the stopped matching-recycler v2 block, which remains stopped. All four
1x runs pass the same input/capture/HUD/motion, identity and contention gates:

| Run | Session | Peak private / working MiB | Whole-session GPU ms | Process CPU seconds / wall second |
| --- | --- | --- | --- | --- |
| A1 | `20260910T123100Z-p7224` | 2719.04 / 2193.63 | 12.171 | 3.0233 |
| B1 | `20260910T123403Z-p30152` | 2716.96 / 2202.55 | 12.557 | 3.0317 |
| B2 | `20260910T123716Z-p3280` | 2679.02 / 2179.13 | 12.304 | 3.0450 |
| A2 | `20260910T124020Z-p21684` | 2737.93 / 2220.75 | 12.337 | 3.0262 |

Every timing cell below is median / p95 / p99 in milliseconds. Percentages
compare equally weighted run statistics, keeping both repetitions rather than
pooling their frames or selecting the better run.

| Phase | A1 | B1 | B2 | A2 | B vs A p99 |
| --- | --- | --- | --- | --- | --- |
| Early race | 85.191 / 113.377 / 122.034 | 60.335 / 108.380 / 113.073 | 62.080 / 122.309 / 126.473 | 54.407 / 110.105 / 113.001 | +1.92% |
| Hold | 16.802 / 20.825 / 21.906 | 16.771 / 18.559 / 20.332 | 16.683 / 18.791 / 21.262 | 16.617 / 18.603 / 20.735 | -2.46% |
| Acceleration | 16.446 / 18.284 / 18.985 | 16.747 / 21.348 / 30.026 | 16.483 / 17.846 / 18.324 | 16.283 / 18.065 / 18.534 | **+28.87%** |
| Handbrake | 16.296 / 18.290 / 19.427 | 16.407 / 18.242 / 18.719 | 16.335 / 18.623 / 20.853 | 16.283 / 18.620 / 21.005 | -2.13% |
| Settled | 16.312 / 17.941 / 18.798 | 16.727 / 18.424 / 19.840 | 16.352 / 18.242 / 18.732 | 16.351 / 18.276 / 19.867 | -0.24% |

Early median changes -12.31%, but the two controls themselves differ widely.
Whole-session GPU changes +1.44%, process CPU +0.45%, peak private -1.12%
and peak working -0.74%. These observations do not establish retention.
GPU times remain asynchronous whole-session statistics, not CPU-row timings.
Per-phase draws/vertices differ by less than 0.2% in these aggregate comparisons.
Race-clock spreads at 76/88/92 seconds are 0.058/0.043/0.037 seconds.
All four runs have two invalid simulation deltas and zero GPU timing drops.
A1 preserves one GPU-memory sampling error; every run has 355 valid counter
records and valid samples in each measured phase. Per-phase memory, faults,
geometry counters, exact clocks and every run's statistics remain in the reports.

Two unresolved findings prevent adoption:

- Present-drop totals are A1 **1**, B1 **52**, B2 **42**, A2 **2**. Localization
  puts every notification within the first ten seconds of startup, with none
  in the race windows. `Presenter::RefreshGuestOutput` increments this counter
  when a newly published image replaces an unacquired mailbox image. It is not
  a device-loss counter. Why admission changes startup output cadence, and
  whether that affects visible UI timing, still require qualification. CSV
  notification intervals are not exact identities of the discarded images.
- B1's acceleration tail includes five consecutive 28.975–37.763 ms frames
  around 119.34–119.48 seconds. B2 does not repeat that burst. The recorded
  cache-miss, command-stall, memexport-wait and resolve/query-wait counters do
  not identify a cause. Disabled texture CPU timing cannot be read as zero
  actual cost, and coarse OS samples cannot attribute a five-frame burst.
  Preserve the +28.87% aggregate p99 result and investigate it; do not replace
  B1 with another unchanged run.

Local checks/helpers are `make/build-hud-keep-clean`, `check-hud-span.cpp`,
`run/summarize-hud-keep-preflight`, `run/summarize-hud-keep-retention` and
`summarize-hud-keep-block.py`, plus `localize-hud-keep-tails.py`. Evidence includes `comparison-1x.json`,
`present-drop-localization.json`, `acceleration-tail-localization.json`,
per-run metrics, manual stage reviews and source/binary manifests.

**Historical next step, superseded below:** the preplanned matched 2x
A1/B1/B2/A2 runs were all unexecuted at this checkpoint. Also
qualify the startup UI cadence and acceleration burst, queued payload/node
lifetime, other HUD/menu states and broader scene/motion coverage. The two
preflights cannot replace either control or either matched repetition.
No HUD fix, optimization or B item is retained. A6 remains 1x-only and
recycling remains off. Every B1-B4 requirement remains in scope.

All nine retained runtime files and nine previously instrumented sources are
restored and directly verified. EXE `372161...`, GPU `27B486...`, runtime
`955BDC...`; complete 1x pack staged. No game/build/replay remains active.
Source before this checkpoint is main `bc2062e`, SDK `202247a`. Unrelated SDK
kernel/libmspack edits and saves remain preserved.

## Clean HUD admission: 2x comparison stops on a visual failure

The prospective 2x block runs A1 and B1 only, using the same clean EXE
`20EE2F2D48BD2B83124D4812104F57631B53FB4794658CBA75B97E1419C0F319`,
retained GPU `27B486...` and presentation-diagnostic runtime `6B97FB...`
identified above. The 2x pack/catalogs, route, sampling and disabled renderer
experiments are unchanged. A1 has admission off; B1 has it on.

Both runs exit normally and pass automated input/capture-clock, HUD/pose,
motion, identity and contention checks. A1 passes manual review. **B1 fails
the prestart visual check at 62 seconds:** bright green/white glow appears
along the windshield and reflective headlight parts have colored artifacts.
The corresponding A1 image is clean. Cause and relation to the admission
change remain unproven. Automated checks do not override this visual failure.

| Run | Session | Manual stage review | Race clocks at 76 / 88 / 92 s | Peak private / working MiB | Whole-session GPU ms / process CPU cores |
| --- | --- | --- | --- | --- | --- |
| A1 | `20260910T125200Z-p7224` | Pass | 5.458 / 17.610 / 21.607 | 4998.68 / 2243.36 | 14.421 / 3.1101 |
| B1 | `20260910T125513Z-p8816` | **Fail: prestart artifact** | 5.516 / 17.608 / 21.625 | 5037.45 / 2244.42 | 14.225 / 3.0923 |

Preserved observations below are median / p95 / p99 milliseconds. They are
not a qualified comparison: the second repetitions are intentionally absent.

| Phase | A1 | B1 |
| --- | --- | --- |
| Early race | 79.943 / 112.340 / 113.507 | 83.404 / 113.564 / 120.673 |
| Hold | 16.896 / 20.840 / 21.736 | 17.076 / 20.929 / 22.314 |
| Acceleration | 16.872 / 20.136 / 20.405 | 16.590 / 18.436 / 20.018 |
| Handbrake | 17.165 / 20.616 / 21.892 | 16.758 / 19.028 / 20.541 |
| Settled | 16.947 / 20.917 / 21.761 | 16.789 / 20.206 / 20.990 |

Both have zero GPU timing drops and only the known startup device-path error.
All individual metrics and failed manual review remain in
`b2/hud-keep-retention/race-2x-abba-{a1,b1}/`. The `before-confirm-62.ppm`
SHA256 values are A1
`A9E2A5AFB5103BF56F4891DE858DF2CD960238C7C73B68DDCFDD786FC9BC2D25`
and B1 `E3E64E1A42894D5E57117D2C3865BAD403675FC213D8EF4E8F8302C2CF646135`.
An archive screen ranks all 37 existing prestart images using one normalized
windshield region. Only this B1 exceeds its green-pixel criterion. That aids
review; it does not prove correctness of the other images or identify a cause.

**The block is stopped. Do not run 2x B2/A2 or replace failed B1.** Local
guards reject a stopped plan, reject failed manual review in the block summary
and prevent overwriting that review. `check-hud-retention-stop.py` runs all
three rejection paths successfully, preserves the review bytes, verifies the
unexecuted outputs remain absent, and checks all nine retained runtime files
and nine previously instrumented source hashes. Results are in
`b2/hud-keep-retention/stop-guard-check.json`.

A separate diagnostic holds the prestart menu and adds dense screenshots from
52 to 65 seconds, with RenderDoc triggered by a green-region match or a
62-second fallback. Session `20260910T130420Z-p22000` exits normally and passes
its input/capture-clock checks. All ten inspected region samples are clear;
the fallback captures two frames. **It does not reproduce the failure and
cannot qualify or replace the failed benchmark.** Diagnostic route SHA256 is
`6E8DBADF6E66C008C4D1E6A9955CEB054A819591835AEE22824BD2316C53C0E9`.

Local evidence under `b2/hud-glass-capture/` includes controller results,
screenshots, runtime logs, the route/plan and these clean reference captures:

- `rdc/frame_frame3883.rdc`: 528,404,280 bytes, SHA256
  `0BBFEC6AC0FE8F097E127F8D68B00C3EBD0217B21B1E8256C31E339546BA8907`.
- `rdc/frame_frame3884.rdc`: 489,288,411 bytes, SHA256
  `9F7D2256CC69270444B65BA8C584569CBB7743296937127F88301532BC6DF752`.

Reference replay inventories 3,203 actions, 2,628 draws and 14 unique output
targets. Target exports and pixel histories complete successfully. Some HDR
targets are later cleared/resolved or reused, so a physical texture coordinate
does not yet identify the windshield pixel across passes. A transient green
HDR history value in the clean frame is not evidence of the failure's cause.
Reports remain in `reference-inventory/` and `reference-pixel/`.

**Resume:** establish the admission predicate's actual renderer-instance scope
and trace the corrupted material/resource chain before changing the design.
Vtable `820033FC` is initialized by `82C528A0`; its direct caller is in local
generated unit 214 near line 21994. The sampled HUD owner does not establish
that every matching instance is HUD-only. Map viewport/resolve coordinates
before attributing the clean reference's pixel history, and capture the actual
failure's GPU contents if needed. Preserve the stopped block, 1x acceleration
tail, startup cadence findings and all earlier rejected experiments.

No production correction or performance setting is retained. All nine runtime
files and nine instrumented sources are directly verified restored: EXE
`372161...`, GPU `27B486...`, runtime `955BDC...`. The complete 1x pack is staged;
no game/build/replay remains active. Source before this documentation checkpoint
is main `ee6e20a`, SDK `202247a`. Unrelated SDK dirt and saves are preserved.
A6 remains symmetric-1x-only, recycling stays off, and B1-B4 remain active.

### Reference glass inputs and fixed-function renderer scope

Follow-up static checks identify the admission predicate's object as the
fixed-function renderer. Its initializer uses declaration names
`CFixedFunctionRendererX360Decl` and `CFixedFunctionRendererX360DeclCB`.
The checked constructor chain is `8259C7D8:8259D000` -> `82C537A8:82C537D8`
-> `82C528A0`; `8259D004` stores the object at parent +2424. The renderer is
shared by the main and worker queue wrappers. `check-hud-renderer-scope.py`
checks retail branch/store instructions, declaration strings and vtable slots.
It also rechecks the earlier selected-callback trace: 855,009 records and all
4,071 begins use owner `402BBD10` through queues `40159EE8` and `4015A010`.
The other 1,357 records have no begin callback. This establishes the observed
owner scope during 70–84 seconds, not all startup/prestart uses or HUD-only
behavior. It does not justify narrowing the helper or identify the corruption.

The clean reference frame renders the HDR scene in three strips. Sampled
viewports have heights 1440, 928 and 416; scissors cover 512, 512 and 416 rows.
Later postprocess draws `16873`/`16882` cover the two screen halves and their
captured vertex UVs confirm a 180-degree reorientation. Consequently, the
earlier physical `(1600,210)` history must not be treated as one persistent
windshield pixel. Filter offsets and strip placement matter.

Near the observed glow, sample-0 history at physical `(1059,115)` in the third
scene strip includes a surviving draw at event `15372`, primitive 65, using
VS `CE0FFEB0986E9971` / PS `1D38BA65C9D3C506`. This reference glass draw reads
two resources. Decoded guest fetch constants and shader branches identify them:

| Fetch slot | Guest base / mip base | Guest dimensions and format | Captured resource | Writes in this frame |
| --- | --- | --- | --- | --- |
| 2 | `1C879000` / `1C9F9000` | 256x256 cube, six faces, format 54 (`k_2_10_10_10_AS_16_16_16_16`), exponent adjustment 4 | `8027`, 512x512x6, R10G10B10A2 | None |
| 13 | `1CE2D000` / zero | 1280x720 2D, format 6 (`k_8_8_8_8`) | `9757`, 2560x1440, RGBA8 | Copies at 4466 / 4889 |

Both fetches have the resolution-scaled bit set. The captured shader Boolean
word is 529: its branch selects the slot-2 cube and skips the slot-1 scene
sample. `check-hud-glass-bindings.py` verifies the six-dword SDK fetch layout,
dimensions, formats, scaled dimensions, branches and resource-use records.
The cube's contents predate this frame; six face exports and the full material
constants/disassembly are preserved. These are diagnostic targets, not proof
of which input caused the failed image. Exact final-pixel filter attribution
and failed-frame GPU contents remain unavailable.

Local evidence is under `b2/hud-glass-capture/`: `renderer-scope.json`,
`glass-bindings.json`, `reference-surfaces-v2/`, `reference-final-pixel/`,
`reference-final-pixel-1059-115/` and `reference-glass-material/`. Replays pass
their report checks. The first surface audit's unmapped-barrier failure is
preserved in `reference-surfaces/`; the corrected report explicitly marks
barriers lacking draw-action metadata. A malformed replay invocation produced
no report and was terminated after verifying its own live process identity;
its failure is preserved in `replay-invocation-failure.json`. The corrected
invocation uses a scoped environment variable and completes. No game runs or
candidate behavior changes occur in this follow-up.

**Next:** trace the cube's earlier production/publication and the slot-13
copies, using the glass shader pair and fetch identities as diagnostic anchors.
Obtain actual artifact contents before changing resource history or claiming a
correction. Keep both stopped comparisons stopped and every B requirement open.
The retained runtime, source hashes and complete 1x pack remain unchanged.

### Glass texture history diagnostic built; live capture pending

The next attribution question is whether the glass inputs have the required
resolved face/mip contents before import. The shared texture cache marks
overlapping 4 KiB pages as scaled-resolved and selects a scaled texture key
when either its base or mip range overlaps. The D3D12 load then uses the full
requested base/mip ranges, including cube slices. This is a path to inspect,
not evidence that partial publication caused the failed 2x image.

A local one-file diagnostic in `src/graphics/pipeline/texture/cache.cpp`
records resolve publications from startup and creation, load, retry and watch
invalidation events for canonical-format-7 256x256 cubes and format-6 1280x720
2D textures. It selects all matching addresses and scales, rather than relying
on the earlier session's guest addresses. Each 160-byte `<20Q` record includes
resource/range identity, base/mip load flags, scaled state, sequence and source
frame. Watch callbacks use submission zero to avoid reading GPU-thread state
on a CPU callback. These observations establish CPU call order, not GPU
completion or valid texture contents. A write failure or the one-million-record
limit rejects the trace; pointer reuse requires a new creation generation.

The corrected Release GPU build succeeds with SHA256
`F4E08085CE577B202D383FE99139B128440246322C83BF6D989C64C2F8C00871`.
The first build failed because a free helper named the protected nested
`Texture` type; the corrected helper deduces its argument type. Both build
outputs remain preserved. All modified source and runtime files were restored.
No diagnostic gameplay run has started, so there is no new session, texture
history, captured failure, performance result or retained renderer change.

Local evidence under `.local/native-renderer/b2/glass-history-profile-v2/`
contains the build log, source snapshot/patch, binary/source manifests, record
format, plan, route and `checkpoint-preflight.json`. The failed build remains
in `glass-history-profile/`. The existing capture runner and child/controller
now accept the separate history output. Their PowerShell syntax checks pass;
the controller's partial-image handling and result checks still need validation
before the first launch. Reusable helpers are `make-glass-history-profile.py`,
`build-glass-history-profile.ps1`, `run-hud-glass-capture.ps1` and
`hud-glass-capture-{launch.ps1,control.py}` in the enclosing `b2` directory.
Generated sources, binaries and capture evidence remain local.

**Resume:** finish those controller checks, then run the separate diagnostic
with `run-hud-glass-capture.ps1 -History`. Use its pinned 66-second route
(`6E8DBADF6E66C008C4D1E6A9955CEB054A819591835AEE22824BD2316C53C0E9`),
HUD-admission EXE `20EE2F...`, runtime `6B97FB...` and the new diagnostic GPU.
Require terminal launch/controller results, normal game exit, input/clock
checks and an uncapped complete history before analysis. Correlate range
publication and selected texture generations with captured glass bindings;
a clean reference still cannot replace the failed benchmark. Restore the
retained runtime and stage the complete 1x pack after the diagnostic.

At this checkpoint all nine retained runtime files and their backups, ten
previously instrumented sources, the new diagnostic binary/route and the staged
complete 1x pack pass direct identity checks. No game, build or replay is
active. Main before this checkpoint is `2690045`, SDK `202247a`; unrelated SDK
dirt and saves remain preserved. Both comparisons stay stopped, A6 remains
symmetric-1x-only, and B1-B4 remain open. No preview release is published.

### Cube history and import cost: complete diagnostic, low priority

The startup history run `20260910T135620Z-p30568` exits normally and passes
all 18 input steps and 14 capture-clock checks. The controller finishes and
captures two frames at its 62-second fallback. All ten green-region samples
are clear, and manual prestart review shows no green windshield artifact.
This is another clean reference, not a replacement for failed 2x B1.

The complete history has 171,821 records: 151,839 resolve API observations,
six selected texture creations, 6,419 paired load beginnings/completions and
7,138 watch invalidations. There are no trace-cap/write errors, retries,
unfinished load pairs or sequence gaps. History SHA256 is
`C8C3DA07D19841B7A432067783C71144BED531E01058DBBA3BE0D8AB8093276F`.
Creation generations, stable keys and base/mip flags are checked explicitly.

The glass cube at base `1C879000`, mips `1C9F9000`, loads 722 times over source
frames 1199–3207. All requested base and mip ranges have full union coverage
from preceding resolve calls: before the first load, and since the previous
load began thereafter. Its 721 base and 721 mip invalidations are GPU-originated.
Slot-13 texture `1CE2D000` has 4,148 loads, also with full publication coverage
in those windows. This does **not** prove GPU completion, unchanged allocation
lifetime, valid padding or valid contents after intervening CPU writes.
The clean run does not support a missing-publication explanation for the cube.
Another selected 2D texture has 539 partial-publication windows; partial writes
are not themselves corruption, since untouched contents may remain valid.

Pipeline-command mapping verifies all 2,628 draws in the first capture and
finds six draws using the known glass pair. At event 15372, decoded fetches
and shader Boolean word 529 join the cube and slot-13 resource to this run's
history. **`GetUsage` reports no cube accesses despite the bound descriptor
and selected shader branch.** Both captured frames show this limitation.
Missing usage entries cannot establish that a consumer is absent. Two failed
inspectors that selected draws through that usage list remain preserved;
the corrected inspector follows actual command-list pipeline bindings.

Local history evidence is `b2/glass-history-profile-v2/`: `history-report.json`,
`glass-bindings.json`, `frame-workloads/`, `reference-glass-material-v3/`,
the two earlier failed material reports and `test/`. Its captures are:

- `frame_frame3901.rdc`, 532,132,851 bytes, SHA256
  `CD04B30587121037D4709CEF1BED87E934E81C98964D617C1A93F37825AE744C`.
- `frame_frame3902.rdc`, 487,085,398 bytes, SHA256
  `972B50EB364BA131CDFA5918A2C2AC2086039ED4C752F9E7565F0962BABC87EE`.

A separate prospective 25-second world-view route captures active reflection
production at 20 seconds. Session `20260910T140940Z-p4000` exits normally,
passes all ten inputs and three capture-clock checks, and visibly reaches the
stopped car by the Recaro Rush signup. It uses clean EXE `20EE2F...`, runtime
`6B97FB...`, retained GPU `27B486...` and enabled local HUD admission. This
metadata diagnostic is not a retention benchmark. Route SHA256 is
`19A53072C258EDFC2B05F5ECA3F263656A9D335C3EBB272B89B25ECAA00BA3E5`.

Frame 1506 contains 5,224 actions. Its actual cube copy commands at events
9528–9581 cover every one of the 54 face/mip subresources exactly once, from
scratch buffer 1905 into cube 8097. Checked source footprints do not overlap:
8,388,576 logical bytes, with padding extending to byte 8,451,072. Evidence
is `b2/glass-reflection-capture/chain/` and `copy-chain-check.json`. Rendering,
resolves and mip construction precede these imports and are separate costs.

The existing native timestamp heap now has a local diagnostic extension for
full scaled **and unscaled** 256x256 format-7 cube loads. Query allocation,
completion and retirement guards are unchanged; interrupted/invalid samples
remain rejected. The conversion interval includes later scaled mip-source
setup, and the copy interval covers all face/mip copies. Dimension, slice,
mip and scale fields identify each sample without relying on guest addresses.
No RenderDoc duration-counter retry or OS setting change is needed.

The corrected diagnostic GPU is
`F615DFF6C5FC259DB0F98BEBD28D40750E2D282961D7FE97D3ACE874FA79946A`.
Both runs use EXE `20EE2F...`, runtime `6B97FB...`, explicit complete packs,
the same 25-second route and **disabled HUD admission**. Both exit normally,
pass input/capture-clock and identity checks, have zero reported timing losses
and corpus overflows/collisions, and produce 13 cube samples at source frames
1260–1980 in steps of 60. Manual review of all six world screenshots confirms
the stopped car and visible scene/HUD. Camera framing, traffic and NPC poses
vary; these images do not establish correct animation timing.

| Scale / session | Median conversion / copy ms | Total median / p95 / p99 ms |
| --- | --- | --- |
| 1x / `20260910T142302Z-p17484` | 0.010240 / 0.012032 | 0.022912 / 0.024205 / 0.024911 |
| 2x / `20260910T142350Z-p11296` | 0.025600 / 0.025056 | 0.051200 / 0.053050 / 0.053925 |

These are small sampled-operation distributions from one diagnostic run per
scale, **not gameplay frame-time percentiles, retained savings or total
reflection cost**. The GPU conversion/copy work is now a low-priority target.
Removing it would address little of the observed GPU budget; CPU preparation
has not been isolated. Earlier face rendering/mip generation and larger
depth/transfer chains remain unqualified opportunities. No quality setting or
mirror shortcut is adopted.

Preserve two earlier timing limitations: `cube-timing-profile/run-2x/` exits
normally but fails clock verification because retained EXE `372161...` lacks
`trigger_output_frame`; `cube-timing-profile-v2/` has valid 2x samples but no
unscaled cube queries at 1x. Neither verifier is weakened. The final run/report
is in `b2/cube-timing-profile-v3/`, including `timing-report.json`, per-run
`texture-ranking.json`, source/binary manifests, `world-review.json` and
`restoration-check.json`. Helpers `check-cube-timing.py`,
`check-reflection-copy-chain.py`, `check-glass-history-bindings.py` and
`analyze-glass-history.py` provide runnable checks in the enclosing `b2` folder.
The builder/launcher reuse existing helpers; all diagnostics remain local.

**Next:** attribute CPU preparation and the earlier reflection face-rendering
and mip-generation work from the active-world capture and native records before
changing its update policy. Mip draw pair `2C53E1A563484076` /
`21937679208E59A5` and the small float-color targets are anchors, not yet a
complete producer contract. Preserve the unresolved green artifact, the
stopped comparisons and 1x tail/startup findings. Another clean prestart does
not establish a correction. All nine retained runtime files/backups and eleven
touched source files are directly verified restored, with the complete 1x pack
staged and no active game/build/replay. Main before this checkpoint is `8910b24`,
SDK `202247a`; unrelated SDK dirt and saves remain preserved. B1-B4 stay open.

### Cube CPU cost and reflection mip pass attribution

A local CPU probe now isolates the backend cube load and its containing
`RequestTextures` call. It reuses the existing cube GPU diagnostic and
one-in-60 source-frame sampler. Every backend return records success and
elapsed time; the checker requires a unique same-thread, same-submission,
same-internal-frame containing request, then joins the corresponding GPU
sample by source frame and base. Missing, duplicate and wrong-thread parents
are rejected by runnable negative checks. Nested intervals are not added.

Diagnostic GPU SHA256 is
`08C3F5EA8E1FFB4917B7CF8FD10C88E841A6821676999B33D048F204FDB7C157`.
Both scales use EXE `20EE2F...`, runtime `6B97FB...`, the same pinned 25-second
world route as the prior GPU probe, complete matching shader packs and disabled
HUD admission. Both launch handles terminate normally, including restoration;
all ten inputs, three capture clocks, binary/route identities and timing/corpus
checks pass. These runs have not received a separate manual screenshot review
and do not qualify representative motion or a performance setting.

| Scale / session | Backend samples | Backend CPU median / p95 / p99 / max ms |
| --- | --- | --- |
| 1x / `20260910T143729Z-p1512` | 14 | 0.004500 / 0.005230 / 0.006166 / 0.006400 |
| 2x / `20260910T143829Z-p5428` | 12 | 0.005950 / 0.006690 / 0.006778 / 0.006800 |

The backend excludes its own reporting overhead. Its containing requests have
medians of 0.0588 / 0.0551 ms, but include other requested textures and the
nested backend log. They cannot be attributed entirely to cube preparation.
Summing all cube-bound requests in a sampled frame gives median/max
0.14345 / 1.9895 ms at 1x and 0.25595 / 0.3394 ms at 2x. The 1x outlier remains
unattributed; these mixed requests must not be presented as removable cube cost.
Together with the previous GPU import result, the isolated backend work is a
low-priority target. The scope excludes full cache lookup and earlier producers.

The prior native GPU sessions provide a stronger mip-generation lead. Joining
pass `first_draw` identities to their same-session corpus selects pair
VS `2C53E1A563484076` / PS `21937679208E59A5`. At each scale, all 13 sampled
frames from 1260 through 1980 contain exactly 48 selected spans, each with one
draw: 624 records across 16 families. All first-draw identities resolve, and
the existing session, duplicate-record and zero-loss checks remain in force.

| Scale / session | Sum of selected pass spans per sampled frame: median / max ms |
| --- | --- |
| 1x / `20260910T142302Z-p17484` | 0.892928 / 1.116160 |
| 2x / `20260910T142350Z-p11296` | 1.073152 / 1.293312 |

These GPU spans include work such as incoming texture preparation and the
following resolve. They are not shader-only durations, fully removable time,
retained FPS gains or gameplay frame-time percentiles. Do not add overlapping
cube-load timings to these spans.

The active-world frame-1506 replay completes all 48 matching draws and their
following resolves. The checked 2x pattern has six groups of eight reductions:
single-mip R10G10B10A2 inputs decrease from 512x512 to 4x4; viewport/scissor
outputs decrease from 256x256 to 2x2. Each draw uses 24 indices, one instance
and float target 7984, followed by `Resolve Copy Full 32bpp`. Descriptors,
VS/PS constants, resolve constants and shader disassembly are exported. This
pattern is consistent with six face mip chains, but guest-range continuity,
filter/quantization behavior, all consumers, lifetime and producer side effects
still require proof. Resource bindings alone do not authorize skipping work.

Local evidence is `b2/cube-timing-profile-cpu/` (`cpu-report.json`,
`timing-report.json`, per-run logs/clocks, source/binary manifests and
`restoration-check.json`) and `b2/glass-reflection-capture/`
(`mip-contract/report.json`, shader exports and `mip-cost-check.json`). Helpers
`make-cube-cpu-profile.py`, `check-cube-cpu.py`, `inspect-reflection-mips.py`
and `check-reflection-mip-cost.py` reuse the existing build/run/ranking tools.
All diagnostics and GPU captures remain local.

**Resume:** decode the complete mip resource chain and trace the actual guest
producer before designing a native replacement or changing reflection policy.
Prioritize this measured lead alongside the larger depth/transfer chains;
avoid spending more unchanged experiments on the small cube import itself.
Keep the green windshield failure and both stopped comparisons preserved.
No production renderer change is retained and no B item is complete.

Checkpoint preflight directly verifies all nine retained runtime files and
backups, eleven restored source files and the complete staged 1x pack. EXE
`372161...`, GPU `27B486...`, runtime `955BDC...`; no game/build/replay is active.
Main before this checkpoint is `a2a587a`, SDK `202247a`; unrelated SDK dirt and
saves remain preserved. A6 stays symmetric-1x-only, recycling stays off, and
B1-B4 remain active. This checkpoint publishes no preview release.

## Reflection mip producer and cached packet contract

The complete frame-1506 resource check now joins all 48 mip destinations and
all 42 within-face output-to-next-input links. Face order is `0,4,2,1,3,5`;
cube base is `1C879000`, with unpacked mips at `1C9F9000`. Base faces occupy
256x256x4 bytes each. Each following level has six face strides of
`max(32, 256 >> level)^2 * 4` bytes. At 2x, resolve buffer offsets scale by
four. These are checked bindings and address relationships, not GPU-content
or allocation-lifetime equivalence.

The mip pair is VS `2C53E1A563484076` / PS `21937679208E59A5`. Sampling uses
explicit LOD zero, linear minification/magnification, sample exponent +4 and
BGRA swizzle; resolves use exponent -4 and red/blue swap. The intermediate
floating target and R10G10B10A2 publication require a quantization contract.
The draws have 24 indices; their actual vertex coverage is still unproved.
A generic native mip filter must not be assumed equivalent. The PS's 84-byte
guest microcode uniquely matches image address `821ABC7C`, near the
`srcMipLevel` parameter string. The loaded image SHA256 is
`5CE77D34952A8C65B432D84E5EB9B321F2CBB9F8C0377567DECD77AFBF93927C`.

Static call tracing and live producer probes establish this bounded path:

- Parent `823F40D8` calls `823F69F8` at `823F43D4` with caching enabled.
  The alternate parent path goes through `82DC92E8` and remains untraced.
- `823F69F8` builds eight reductions per face through `82C3CE58`, called
  at `823F6E88`, using the helper at parent+8336. The shared blit reaches
  `824426B8` at `82C3CFFC`.
- Finished face lists are published at `823F6EF0` into the six handle slots
  at parent+7844+face*4. Later calls reuse those handles through `824167F8`
  at `823F6BA8`; **the 48 blits are generated once in each observed run**.
- The wrapper can queue work through `82D842F8` or call `82416A00` directly
  at `82416894`. The latter follows the object's list at +116 to emit
  indirect-buffer packets; the existing observation hook is at `82416F18`.
- Successful parent completion sets parent+8252 bit 64. Cache publication,
  queueing, references and this guest-visible completion state must survive
  any replacement. Neither cached dispatch nor initial generation is bypassed.

Final producer fixture EXE SHA256 is
`7EA8294116970A817CA3112E5E5229D5DE1249F124F054FA11E721ACF359D70E`.
It uses retained GPU `27B486...`, runtime `955BDC...`, disabled local HUD
admission, explicit complete packs and the existing 25-second route SHA256
`19A53072C258EDFC2B05F5ECA3F263656A9D335C3EBB272B89B25ECAA00BA3E5`.

| Scale / session | Complete cycles / frames | Initial blits / handles | Later cached dispatches |
| --- | --- | --- | --- |
| 1x / `20260910T150838Z-p20084` | 709 / 1202–1910 | 48 / 6 at frame 1202 | 4,248 across 708 cycles |
| 2x / `20260910T150940Z-p18104` | 730 / 1197–1926 | 48 / 6 at frame 1197 | 4,374 across 729 cycles |

Both runs exit normally, pass ten input and three capture-clock checks, and
have complete, balanced, single-thread producer records below the cap.
Every reused face handle matches its earlier publication; all calls return
success and no regeneration is observed. The same-session native corpus
still contains 48 mip spans in every sampled world frame, without reported
overflow/collision. Manual review of each 20-second image shows the stopped
car by Recaro with visible scene/HUD. Other saved images, motion, NPC/UI
timing and broader scene/lifetime coverage are not qualified. Trace timings
include instrumentation and establish no CPU saving.

A separate 1x packet diagnostic, `20260910T151726Z-p21680`, combines that
EXE with GPU SHA256
`0A290CD3E96BC70D7807D8E24A98271698667EEBE4DD4F71BA559748210DCFF9`.
It also exits normally and passes inputs/clocks. Reusing the existing scene
decoder and its negative checks, the new local checker verifies six snapshots
of 6,944 bytes / 392 packets each and all 624 observed draw bindings over
13 sampled frames. Each face list has eight predicated render draws, eight
resolve draws and eight single-word `CACHE_FLUSH` events. The six templates
total **41,664 bytes / 2,352 packets**, excluding wrapper work. These are
observed packet volumes, not measured decoding time or eliminated work.

Each list also includes 303 type-0 writes, 14 padding packets, eight external
PS loads, nine external constant loads, 17 invalidations and 17 immediate
shader loads. No scratch writeback is present inside these six snapshots.
The first render draw inherits mode state, and all render predicates depend
on incoming bin state. The SDK's single-word event handler writes
`VGT_EVENT_INITIATOR`; preserve that state and event ordering. Stable observed
command hashes do not prove lifetime identity or stable external data.
An exact same-session CPU cached-handle-to-GPU-buffer join remains pending.
Only 1x packet contents were captured; this run's producer trace is archived
but has not received the separate full-cycle checker or manual image review.

Evidence remains local under `.local/native-renderer/b2/`:
`glass-reflection-capture/{mip-cost-check.json,guest-producer/}`,
`reflection-mip-producer-v3/{producer-check.json,run-1x/,run-2x/}` and
`reflection-mip-commands/{command-check.json,run-1x/,restoration-check.json}`.
Runnable checks are `check-reflection-mip-cost.py`, `check-mip-producer.py`
and `check-mip-commands.py`; all pass. Source/binary manifests and build logs
identify each local fixture. Preserve the first producer build's musttail
failure and v2's sampled-frame coverage gap: v2 missed initial generation,
so zero observed blits there did not mean no producer. The command diagnostic's
builder omitted its source from automatic restoration; exact source bytes
were explicitly restored and verified before launching and at checkpoint.

**Resume:** join cached handles to submission buffers, establish filtering,
external inputs, all consumers and mutation/lifetime behavior, then design
native mip production and suppression of the six recurring submissions before
packet emission. Replacing only initial list construction leaves the measured
recurring GPU work intact. The earlier 0.892928 / 1.073152 ms span medians
include preparation/resolves and remain diagnostic, not removable savings.
Keep larger depth/transfer priorities, both stopped comparisons and the full
B1-B4 scene/timing/retention requirements. No new behavior is retained.

## Native reflection mip kernel: bounded GPU proof

The existing scene-producer observer now joins each published face handle to
the actual submitted GPU buffer at both scales. No new game build was needed:
the prior read-only EXE `7EA829...` and GPU `0A290C...` run with
`pinyon_shift_fh1_scene_dump=true`, HUD admission disabled and explicit packs.

| Scale / session | Producer cycles / frames | Cached dispatches | Unique producer records |
| --- | --- | --- | --- |
| 1x / `20260910T153317Z-p27320` | 786 / 1225–2010 | 4,710 | 1,027 |
| 2x / `20260910T153427Z-p22900` | 773 / 1198–1970 | 4,632 | 717 |

Both normal exits pass all inputs/clocks and complete producer checks. At
each scale, the six published handles uniquely join six submitted 1,736-word
buffers. All six packet snapshots and 624 live mip bindings pass the existing
decoder checks, including source levels, incoming predicates and external
loads. The observer stays below its 4,096-record cap. Manual review of both
20-second images confirms the stopped Recaro view and visible HUD without
the previous green-glass artifact. This bounded identity join does not prove
cache destruction, streamed reuse, wrapper side effects or performance.
Local evidence: `b2/reflection-mip-join/`, with `producer-check.json`,
`command-check-{1,2}x.json`, source trace files, logs and binary/route plan.

The active-world frame-1506 replay then exports all 48 mip inputs and
post-vertex-shader outputs, plus all 54 final cube subresources. **Every
draw input is byte-identical to its corresponding published previous mip**.
All vertex outputs match each other: 24 nonindexed vertices form eight
vertical rectangle inputs. The backend's rectangle geometry expansion must
be accounted for; post-VS triangles alone are not full raster coverage.
The first inspector incorrectly required an index buffer and failed before
exporting a draw. Its script/report are preserved; v2 handles the observed
nonindexed path and completes. See `glass-reflection-capture/mip-geometry-v2/`.

A simple integer 2x2 box filter is now a concrete native quality candidate.
The CPU check compares both individual reductions and a fully recursive
eight-level chain against the captured cube. Across all 524,280 generated
pixels, recursive RGB error is at most **2/1,023**, with mean absolute error
**0.118223/1,023 per RGB channel**; 377,687 pixels match exactly. This is
one captured frame's quantized mip error, not a percentage of visual accuracy
or motion qualification. It supports testing a small intentional filtering
difference without reproducing every intermediate conversion.

`b2/native-mip-kernel/mip-box.hlsl` implements the filter with packed
R10G10B10A2 integer loads/stores and ties-to-even rounding. One dispatch per
level covers all six faces, with UAV barriers between levels. A standalone
D3D12 check, adapted from the existing owned-geometry harness, generates
2,097,120 mip bytes from 6,291,456 captured base bytes. The complete 8,388,576
bytes match the CPU reference exactly; input and trailing guards remain intact.
An input-mutation control changes four generated bytes and passes the expected
negative comparison. The CPU rounding check covers every sum from 0 to 4,092.

On the local **RTX 4080**, sixteen warmed timestamp intervals for eight
dispatches plus barriers measure median **0.020480 ms**, range
0.019456–0.021504 ms. This is an isolated, repeatedly reused buffer with
diagnostic debug-layer setup. It excludes input extraction/upload, texture
publication, guest state, CPU submission and gameplay contention. Do not
subtract it from the earlier approximately 0.9/1.1 ms pass spans or claim
an in-game speedup, memory reduction or lower hardware requirement.

Kernel source SHA256:
`BDDB6097F6FCDF946504B6EA4B907F1025B9C6CD6BE43E336BD9217663F35E2C`.
Standalone checker EXE SHA256:
`95648DE370043C3FEA1EFD30C24F9E1E4799A04F17240B1964A34006702AC963`.
CPU/GPU output SHA256:
`A33D6933AE19D55E4744BC8048C0760E1B7F8ED741DEA992B2E174A3F204AE92`.
`manifest.json`, build log, positive/negative logs and outputs remain beside
the kernel. `check-mip-filter.py` reproduces the content comparison and CPU
fixture; `check-gpu.exe INPUT_DIR [--poison]` runs the GPU checks.

**Resume:** integrate the kernel with actual base-cube access and publication
under the existing resource/fence rules, then replace recurring submissions
at the guest boundary. A generic `CallInThread` callback is not sufficient
ordering: the processor services pending callbacks before queued ring work.
Keep the original packet-order position and guest-visible state/queue effects.
Full consumers/lifetime, changing content, 1x GPU contents, broader motion,
NPC/UI timing, clean tail/memory comparisons and all B1-B4 gates remain open.
The game still uses the retained renderer; the native kernel is local and
standalone, and no new renderer behavior or quality setting is retained.

## Tiled reflection mips and publication contract

The native candidate now uses the actual 2x scaled/tiled resolve layout,
reusing addressing from the existing `fh1_scaled_32bpp_2x.cs.hlsl` and
`texture_util::GetTiledOffset2D`. The active-world frame-1506 replay exports
resource 1925 before the mip sequence (event 7575) and after its final resolve
(event 9236). The guest interval is `1C879000` through exclusive `1CA95000`,
with mip base `1C9F9000`: 2,211,840 unscaled bytes / 8,847,360 scaled bytes.
Its layout includes minimum-32-texel mip storage and byte-swapped 32-bit words;
simple per-pixel scalar expansion would address it incorrectly.

`b2/check-mip-tiled.py` verifies all **2,097,144 logical pixels** in the 54
cube subresources against actual resolve memory. All 524,280 generated mip
destinations are unique. The original sequence changes no base or padding
words outside these destinations. The CPU native fixture replaces only active
mip words, retaining the existing base and padding. Every aligned 2x2 source
block has checked relative byte offsets **0, 4, 16, 20** in this 2x layout.
Evidence is local under `glass-reflection-capture/mip-tiled/` and
`native-mip-tiled/layout-check.json`; the exporter is `export-mip-tiled-memory.py`.

The first optimized HLSL recomputed each neighboring sample's tiled address
and **failed with 214,797 differing generated bytes**. The same source with
optimization disabled passes. Optimized disassembly loses a required low-X
offset in neighboring loads; this is an optimizer-dependent failure in the
observed shader, not evidence that the original output was acceptable.
Preserve `native-mip-tiled/` and `native-mip-tiled-noopt/` as failure/control.
The corrected `native-mip-tiled-v2/` computes one source address and uses the
four checked offsets. It passes at normal optimization, without broadening
the admitted layout or disabling optimization globally.

The standalone D3D12 v2 check matches the **entire 8,847,360-byte** CPU fixture.
Base, mip padding and trailing guards remain intact. The input-mutation
control produces four differing generated bytes and passes its expected
negative comparison. Actual generated pixels occupy 2,097,120 bytes; the
checker's `generated_bytes=2555904` is the mip storage span including padding,
not the number of active pixel bytes written. Sixteen warmed intervals give
median **0.023040 ms**, range 0.022528–0.023552 ms, on the RTX 4080. These
exclude in-game publication, guest/CPU work and contention. The earlier
approximately 0.9/1.1 ms mip spans still cannot be treated as removable savings.

V2 kernel SHA256:
`E7DAFFEF330EB9860FA12747A8A91DBC472FA7FC7213D1BEFA6EDB216A0121A6`.
Standalone checker EXE SHA256:
`AB74C06B08DAF25D2DDBAD4A7C64DFA49D6E14EB66737ABB7861DB8D6FB68B06`.
Full tiled CPU/GPU output SHA256:
`67CB7B8741D1E296BB480AE71FCF2BB52E1F0E50A1589CFEAA33C1C773AACB6E`.
`native-mip-tiled-v2/manifest.json` also identifies source, compiled header,
input and mutated output. Runnable checks are `check-mip-tiled.py` and the
v2 `check-gpu.exe INPUT_DIR [--poison]`. Their inputs and GPU captures remain
local; this documentation checkpoint does not publish captured game data.

The resolve contract has a newly identified required side effect:
`RB_COPY_CONTROL=00100100` sets **color_clear_enable, bit 8**. The SDK resolves
the copy and then clears color through its common resolve-clear path. All 48
mip resolves carry this state. A replacement must preserve both canonical
mip output and the required EDRAM/host render-target clear history. Existing
`MarkRangeAsResolved` publishes scaled ranges and invalidates shared-memory
watches. Publishing inside a pending cube import would invalidate that load's
own watch; it is not a safe integration point.

`make-mip-publication-profile.py` prepares a bounded diagnostic that runs the
native kernel **after the final original resolve and its clear**, before the
later cube import. It uses the existing scaled buffer, adds ordered UAV work
and marks the mip range resolved. All original draws, resolves and clears
remain enabled. Its environment flag, fixed captured address and frame window
are local diagnostic triggers, not a production admission contract or B3 bypass.
Even a successful live run would prove output/publication only and retain
duplicate work.

The initial integration **build failed**: the derived D3D12 texture cache calls
private base-class `IsRangeScaledResolved`. No candidate DLL or live run was
produced. Preserve `reflection-mip-publication/{build.log,source-manifest.json}`
and its source snapshots/patches. The builder's terminal failure executes its
restoration path; `restoration-check.json` independently verifies all nine
retained runtime files/backups, thirteen source baselines and the staged
complete 1x pack, with no active game/build/replay. This does not affect the
standalone v2 GPU result. Retained identities remain EXE `372161...`, GPU
`27B486...`, runtime `955BDC...`, main `2825e9d` before checkpoint and SDK `202247a`.

**Resume:** fix access to the required range-validation query in a separate
diagnostic version, retaining its guard, and build with every changed source
listed for restoration. Extend the existing profile runner with explicit
candidate hashes; use the verified AppData save and 2x pack, then restore 1x.
Check actual native output/publication and subsequent cube consumers in a GPU
capture, rather than inferring correctness from admission logs. Then establish
safe production identity/lifetime and clear/state preservation before replacing
the recurring guest submissions. 1x native contents, changing/streamed content,
motion, NPC/UI timing, clean tails/memory and all B1-B4 gates remain open.
No new renderer behavior is retained; the stopped comparisons stay stopped.

## Native mip publication reaches the in-game cube

The revised local diagnostic **builds and runs**. The existing scaled-range
query is made protected, preserving its implementation and existing callers.
Inspection showed that it means *any page in the range*, so this diagnostic
queries each of the 384 aligned base pages before dispatching. Per-page locking
is diagnostic overhead, not a retained production design or lifetime proof.
The kernel uses the existing scaled buffer, ordered UAV barriers and existing
publication/invalidation path after the final original resolve and color clear.
Every original mip draw, resolve and clear remains enabled.

Local candidate: `b2/reflection-mip-publication-v2/`, generated by
`make-mip-publication-profile-v2.py`; source snapshots and the four-file manifest
cover both texture-cache headers, D3D12 texture-cache implementation and command
processor. GPU SHA256:
`2A200172C4ED84EBDCD02B7C9D9BC1DE2C3A608D0CB032A5DEB5A6B8F771DA31`.
Read-only producer EXE `7EA829...`, retained runtime `955BDC...`, route
`19A530...`, main `dfd82b2` before checkpoint and SDK `202247a`. Exact identities,
packs and catalogs are in `plan.json`. The native-publication environment flag
is enabled only for these diagnostics; HUD admission and other B experiments
are disabled.

Normal 2x session **`20260910T163235Z-p27636`** exits normally and passes all
10 inputs and three capture-clock checks. It records **761 successful native
publications**, frames 1299–2059, with no rejected admission. The complete
producer checker passes 762 cycles, frames 1297–2058, initial 48-blit/six-list
construction and 4,566 cached face dispatches. Thirteen sampled frames still
contain all 48 legacy mip spans, explicitly demonstrating duplicate work.
CPU producer and GPU observation frame numbers are different scopes and must
not be treated as synchronous per-frame timings. Producer trace SHA256:
`A366E4677CBAD69BB6EA2E5EF58DF0C1EF4C47C62052C9337A19A0E6E75CCCB8`.

The first capture setup rejects an older runtime DLL before game launch; its
failure and restoration remain in `reflection-mip-publication-capture-v2/`.
The corrected runner stages the candidate's planned runtime. Separate capture
session **`20260910T163514Z-p20540`** exits normally, passes inputs/clocks and
records 367 successful publications, frames 1200–1566. Evidence is in
`reflection-mip-publication-capture-v3/`. Manual review of the normal and
captured runs' 20-second images shows the stopped Recaro car/HUD scene without
an obvious new artifact; other images and motion have not been qualified.

The first GPU capture, **frame 1504**, proves the actual output path:

- Eight native dispatches at events 10449–10470 address scaled buffer 1925
  at byte offset 1,914,585,088, corresponding to guest base `1C879000` at 2x.
- The complete **8,847,360-byte** output matches an independent recursive CPU
  box-filter calculation from the captured base. No base or padding word
  outside the 524,280 active mip pixels changes. Legacy output differs by
  190,743 bytes, so an unchanged legacy buffer would fail this comparison.
- All **54 imported subresources / 2,097,144 logical pixels** in cube 8034
  match the native buffer exactly. Copies occur at events 10726–10779.
- The next checked draw, event 10811, binds that cube as all six faces and
  nine mips, `R10G10B10A2_UNORM`, for VS `C34795A841E7DEFF` /
  PS `21B70A5E4C9CFD11`. This checks a subsequent bound consumer, not the full
  set of consumers or resource lifetime.

Actual native output SHA256:
`9B0536A92A6EEDE3C510B83C80F1D5BD80438C0686CFDCB2DE21BD24CB2ABB3B`.
Compared with the preceding legacy mip result in this frame, RGB error is
zero for 1,386,755 channels, one for 185,876, two for 208 and **three for one**.
Mean absolute error is 0.118445/1,023. Thus the earlier one-frame maximum of
2/1,023 is not a universal bound. Visual/motion qualification remains required.

The adjacent **frame 1505** capture has four actions, one presentation draw,
zero native dispatches and zero cube copies. The copy checker rejects it;
`adjacent-frame-coverage.json` preserves this coverage gap. It does not provide
changing-input or second-publication evidence, and no favorable rerun replaces it.

Runnable checks: `check-mip-producer.py ROOT 2`, `check-reflection-copy-chain.py
ROOT`, and `check-native-mip-publication.py`. Replay export is
`inspect-native-mip-publication.py`; `native-publication/{report,content-check}.json`
contains event/descriptor and content checks. The shared `mip_layout.py` reuses
the previously checked address math; the original tiled-layout regression also
passes after extraction. Admission counts and direct restoration checks are
recorded in the candidate directory. All nine runtime files/backups and fourteen
source baselines are restored, the complete 1x pack is staged and all processes
are terminal. Unrelated SDK dirt and saves are preserved.

**Resume:** obtain a second active workload capture with changed base contents
using a separated trigger; adjacent presentation captures cannot qualify reuse.
Then establish 1x native contents, production identity/lifetime admission and
resolve-clear preservation before suppressing the obsolete work. The measured
opportunity remains removing the recurring mip sequence, including safe guest
submission bypass; this duplicate-work publication diagnostic retains no speedup.
Broader scenes, streaming/partial writes/reuse/destruction, motion/NPC timing,
matched tails/memory and every B1-B4 completion gate remain open. Both failed
retention comparisons remain stopped, and A6 stays symmetric-1x-only.

## Native mip work replacement and unresolved scratch history

The separated-trigger publication session `20260910T165110Z-p18048` completes
normally, with all ten inputs and three capture clocks passing. The unchanged
publication candidate still runs the original mip work. Its two scheduled
triggers, `glass-18.ppm,glass-22.ppm`, produce four captures, all inventoried:

| Capture / index | Actions | Native dispatches | Cube copies | Checked scope |
| --- | ---: | ---: | ---: | --- |
| 1479 / 0 | 5,610 | 8 | 54 | Native buffer, imported cube and bound consumer |
| 1480 / 1 | 5 | 0 | 0 | Presentation only |
| 1481 / 2 | 4 | 0 | 0 | Presentation only |
| 1482 / 3 | 1,077 | 8 | 0 | Native writes; capture ends before cube import |

Between the two active captures, **727,644 base bytes and 241,086 mip-storage
bytes change**. Both complete 8,847,360-byte outputs match an independent CPU
reference. This is bounded changing-input evidence in one process, not proof
of streaming, partial writes, allocation reuse/destruction or a second consumer.
The observed maximum RGB difference from current legacy output is 3/1,023 in
the first active capture and 2/1,023 in the later one. Full output SHA256 values:

- `2D57B5FCF32E53905232DC7459106EEEA305C122896ECC39D7A67CAD261E307D`.
- `B4B78478E65637289285A66D9E521F8699463E02621416746C939B9ED5848D84`.

Evidence: `b2/reflection-mip-publication-capture-v4/`, including
`capture-inventory.json`, `changing-input-check.json`, `chain/`, `chain-3/`,
`native-publication/` and `native-publication-3/`. The native-only export/check
explicitly requires that scope; presentation-only captures are not discarded.

The new local `make-mip-replacement-profile.py` builds on the previous
publication fixture. It admits only six exact captured 6,944-byte face lists,
at 2x during frames 1200–2100, with bounded addresses, supported incoming
mode/predicate/query state and no nested replacement. Each list is snapshotted
before comparison/execution. The six templates match across the earlier 1x/2x
join captures; a changed-byte control is rejected. This does **not** establish
production allocation identity, external-data contents or lifetime admission.
The captured arrays contain game-derived bytes and remain local.

For an admitted face, eight native dispatches generate its mips. The original
state, shader/external-load, invalidation and event packets still execute.
Render draws and the resolve-copy branch are suppressed; the shared resolve
clear/ownership-transfer path still executes. Native writes use existing
resources, publication ranges, residency and barriers. Each list logs exactly
eight removed draws/copies and checks its final mode. All six guest lists and
their **2,352 packets per cube still reach decoding**. This is downstream work
replacement, not B3's required pre-packet bypass or complete Xenos retirement.

Candidate GPU SHA256:
`FD91E36E1BA2EFA2F01C4F0AC263C02D057655499DA09275432DA1985221A649`.
Producer EXE:
`7EA8294116970A817CA3112E5E5229D5DE1249F124F054FA11E721ACF359D70E`.
Runtime:
`955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500`.
Main/SDK inputs are `3c9b713` / `202247a`; the route hash is
`19A53072C258EDFC2B05F5ECA3F263656A9D335C3EBB272B89B25ECAA00BA3E5`.
Exact plans, source snapshots/patches, template check, binaries and build log
remain under `b2/reflection-mip-replacement-v1/`. No production change is retained.

Normal 2x session **`20260910T171101Z-p29060`** exits normally and passes all
ten inputs/three clocks. The producer check records 729 cycles, frames
1201–1929, with 728 cached cycles and 4,368 face submissions. Native replacement
counters cover 728 complete frames, 1203–1930: **34,944 mip draws and 34,944
resolve copies suppressed**, with no sampled legacy mip spans in that interval.
These source/GPU frame ranges differ; do not join them by row position.
The reviewed 20-second still shows the stopped Recaro car/HUD without an
obvious artifact. This is not motion or performance qualification.

Separate capture session **`20260910T171350Z-p3420`** also exits normally and
passes inputs/clocks. Frame 1538 contains **48 native dispatches and zero draws
of VS `2C53E1A563484076` / PS `21937679208E59A5`**. Native work starts at event
7541; copies 8019–8072 populate cube 8018. The complete 8,847,360-byte native
buffer equals the CPU reference, with zero changes outside active mip pixels.
All 54 imported subresources / 2,097,144 logical pixels match. Event 8104 binds
all six faces/nine mips as `R10G10B10A2_UNORM`, with VS `C34795A841E7DEFF` /
PS `21B70A5E4C9CFD11`. Actual native output SHA256:
`1E66E8D368263AA354792B18501468CF0DDB909C8B00C58A4FC86EA6CAA759D8`.
The replacement's before snapshot contains previous contents, not this frame's
legacy result; its previous-content differences establish no legacy error bound.
Adjacent frame 1539 and this run's 20-second still have not been reviewed.
Evidence: `b2/reflection-mip-replacement-capture-v1/`.

The scratch-history comparison is **incomplete**. Its first inspector grouped
by floating-point format and accidentally included an unrelated world clear,
finding 49 versus 48. That failed inspector/report remain under
`reflection-mip-clear-history-v1/`. The revised inspector uses the actual scratch
resource identity, excludes that separate target and checks all 48 clear calls:
identical order, zero colors, and rectangles repeating sides 256, 128, 64, 32,
16, 16, 16, 16 per face. All checked cleared pixels are zero in both captures.

However, the complete 320×16384 `R16G16B16A16_FLOAT` scratch resources differ:
**8,192 pixels at x=256–319, y=32–255**, entirely outside the cleared rectangle
union. Control resource 7966 and replacement resource 7965 come from different
runs, so this establishes neither a regression nor harmless unused padding.
`reflection-mip-clear-history-v2/{report,difference-regions}.json` explicitly
records `full_scratch_bytes_equal=false`. Trace partial-tile ownership,
preservation transfers and later reads before claiming history equivalence;
do not zero the differences to make the comparison pass. The common
`RenderTargetCache::PrepareHostRenderTargetsResolveClear` implementation is in
`src/graphics/pipeline/render_target/cache.cpp`, and calls `ChangeOwnership`
with the clear rectangle.

Local runnable checks reuse `check-mip-producer.py ROOT 2`,
`check-reflection-copy-chain.py ROOT [INDEX]` and
`check-native-mip-publication.py OUTPUT_ROOT [--native-only]`. Replay export
uses the existing inspectors, with `PINYON_SHIFT_MIP_REPLACEMENT_INSPECT=1`
for the replacement and `inspect-mip-clear-history-v2.py` for scratch history.
The capture wrapper selects `-NativeMipProof -NativeMipProfile
reflection-mip-replacement-v1`; diagnostic runtime and pack restoration remain
mandatory. No diagnostic result is a clean benchmark or retained FPS gain.

**Resume:** resolve scratch history, then prove semantic/external-data/lifetime
admission, 1x contents and safe upstream generation/decoding removal. Continue
the complete B1 scene inventory, streaming/partial-write/reuse/destruction,
motion/NPC/UI timing and matched tail/memory gates. The unchanged failed
comparisons remain stopped. Preflight verifies nine retained runtime files and
backups, eighteen restored source baselines and the complete staged 1x pack;
all game/build/replay handles are terminal. All B1-B4 items remain open.

## Mip scratch history proven and live work cost measured

The outside-clear difference reported above is resolved for the two captured
frames. `inspect-mip-scratch-usage.py` enumerates actual resource uses, not stale
graphics output bindings attached to compute actions. Control scratch 7966 has
one incoming transfer, 48 mip draws, 48 clears, 48 compute reads for resolves
and one later scene transfer. Replacement scratch 7965 has one incoming transfer,
48 clears and one later scene transfer. There are no further uses of either
scratch resource within its captured frame. The later read means the differing
columns cannot simply be dismissed as unused padding.

`export-mip-scratch-transfers.py` exports actual post-VS rectangles, constants,
source sample planes and destination samples for those four transfer draws.
The incoming shaders/constant word 4098 match between captures, as do the
outgoing shaders/constant word 2080. The CPU check follows their integer address
mapping and verifies **every fragment in all four captured transfer rectangles**:

| Run / event | Transfer rectangle | Checked samples | Byte mismatches |
| --- | --- | ---: | ---: |
| Control / 8973 | Source → scratch, x=0–319, y=0–255 | 81,920 | 0 |
| Replacement / 7574 | Source → scratch, x=256–319, y=0–255 | 16,384 | 0 |
| Control / 10780 | Scratch → 4x-MSAA scene target, 1280×16 | 81,920 | 0 |
| Replacement / 7815 | Scratch → 4x-MSAA scene target, 1280×16 | 81,920 | 0 |

All **8,192 cross-run differing pixels already differ in the checked incoming
source transfers**. Their values remain unchanged through mip generation,
every clear, the checked outgoing transfer and the final scratch snapshot.
The replacement's clear path correctly preserves the 64 columns outside the
256-wide clear. A changed transferred byte fails the padding comparison.
No source fix or padding overwrite was required. This proves the captured
ownership transitions; it does not establish general reuse/destruction,
streaming, arbitrary partial writes, other consumers or 1x contents.

Evidence: `b2/reflection-mip-scratch-usage-v1/` and
`b2/reflection-mip-scratch-transfers-v1/{report,content-check}.json` plus exported
blobs/shaders. Reproduce with `check-mip-scratch-transfers.py`; it validates
blob/shader hashes, actual triangle rectangles and all sample address bounds.
The earlier failed format-only inspector and cross-run scratch mismatch remain
preserved; this later source/consumer proof explains rather than deletes them.

The next diagnostic reuses the existing GPU timestamp heap and completion
checks to time entire exact face lists. The same binary executes either all
legacy operations or the native replacement. Three timestamp positions delimit
native generation and original packet execution/clears, while CPU intervals
measure the corresponding recording work. The CPU interval starts after exact
list recognition and `BeginSubmission`; it includes native preparation, but
excludes the common admission comparison and outer submission setup. Every
original state/event packet remains decoded in both modes.

Timing GPU SHA256:
`990D6BF937CB936BB1419CD6465DE3714305B8C2B40B727D2404CB8AD9D7494B`.
EXE `7EA8294116970A817CA3112E5E5229D5DE1249F124F054FA11E721ACF359D70E`,
runtime `955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500`,
route `19A53072C258EDFC2B05F5ECA3F263656A9D335C3EBB272B89B25ECAA00BA3E5`.
Main before the fixture is `b63723a`, SDK `202247a`. The existing 2x pack/catalog
pins are unchanged. `reflection-mip-replacement-timing-v1/plan.json` preselects
legacy control followed by native; neither run replaces a failed comparison.

| Mode / session | Complete list frames | Sampled frames | Face lists / sampled |
| --- | --- | --- | ---: |
| Legacy / `20260910T174447Z-p28976` | 745, frames 1200–1944 | 13, frames 1200–1920 | 4,470 / 78 |
| Native / `20260910T174555Z-p26692` | 785, frames 1206–1990 | 13, frames 1260–1980 | 4,710 / 78 |

Both sessions exit normally, with all ten inputs and three capture clocks
passing. Each sampled frame contains all six faces in order. All 78 CPU samples
join 78 completed GPU samples per mode by observation-frame/record identity;
CPU submission means the starting submission, while GPU retirement reports the
frame slot's final submission. These are distinct values, not a row-position
or equal-submission join. No face timing is lost in the checked sets.

Per-frame sums over six lists, in milliseconds; **all complete samples included**:

| Interval | Legacy median | Native median | Legacy p95 / p99 | Native p95 / p99 |
| --- | ---: | ---: | ---: | ---: |
| CPU total | 0.4011 | 0.1980 | 0.6998 / 0.6998 | 0.3326 / 0.3326 |
| GPU total | 1.075200 | 0.100352 | 1.334272 / 1.334272 | 0.100352 / 0.100352 |
| Native generation, CPU | — | 0.0638 | — | 0.2002 / 0.2002 |
| Native generation, GPU | — | 0.084992 | — | 0.086016 / 0.086016 |

The median measured work reduction is **0.2031 ms CPU / 0.974848 ms GPU**.
These intervals must not be added into a total frame-time saving. Percentiles
use nearest rank; with only 13 samples, p95 and p99 are the maximum. Sampling
one frame in 60 also misses unsampled first-use compilation and other frames.
Native packet/clear medians are 0.1307 ms CPU and 0.015360 ms GPU. Separate
component medians need not sum to the median total. Native counters record
37,680 removed draws and 37,680 removed resolve copies; control removes zero.

The first timing checker rejected a shared startup filesystem error:
`ResolvePath(\Device) failed - device not found`. Both runs contain precisely
that same non-renderer message. Its failed checker/result remain preserved.
The corrected check records the message explicitly and still rejects renderer
or native contract errors. Both timing checks now pass. Manual review of both
20-second stills and the earlier replacement-capture still shows the stopped
Recaro entry, car, road and HUD without an obvious new artifact. NPC/traffic
phases differ, so these are neither pixel-parity nor motion/timing qualification.

Local reproduction: `make-mip-replacement-timing-profile.py` through the existing
restoring build helper; `run-mip-replacement-timing.ps1 -Case control|native`;
`check-mip-replacement-timing.py`. Source snapshots, patches, all logs and
producer traces, `timing-check.json`, `world-review.json` and restoration checks
remain in `b2/reflection-mip-replacement-timing-v1/`. Exact captured game-command
arrays remain local. The retained nine runtime files/backups, eighteen source
baselines and complete 1x shader pack are verified restored; no process is live.

**Resume:** prove 1x native contents/publication and replace fixed-list admission
with production semantic/external-data/lifetime validation. Then bypass the
actual obsolete producer work before packet emission. All 2,352 original packets
per cube still decode, so B3 remains open. This diagnostic reduction supports
continued development, not retention or lower hardware claims. The full B1-B4
scene, mutation/streaming, motion/NPC/UI timing and clean matched tail/memory
requirements remain unchanged, as do both stopped comparisons and A6's 1x scope.

## 1x native mip publication and failed dual-scale admission

Legacy control session **`20260910T175539Z-p732`** uses timing GPU `990D6BF9...`
with replacement disabled at symmetric 1x. It exits normally and passes all
ten inputs/three clocks. Frame 1507 contains 48 legacy mip draws. Cube 8181
is 256-square with six faces/nine mips; its resource is
`R10G10B10A2_TYPELESS`, sampled through a `R10G10B10A2_UNORM` view. Copies
8534–8587 import its 54 subresources, followed by consumer 8619 using
VS `C34795A841E7DEFF` / PS `21B70A5E4C9CFD11`. The two unrelated one-mip BC1
cubes remain in the report and are excluded from the reflection chain.

All 48 resolve destinations and 524,286 logical cube pixels match the actual
shared buffer over guest interval `1C879000`–`1CA95000`, or 2,211,840 bytes.
A recursive integer box-filter generates 131,070 mip pixels while preserving
the 1,572,864-byte base region and padding. This frame's maximum RGB difference
from legacy is 2/1,023, with mean 0.142351415/1,023; it is not a universal bound.
The first memory exporter incorrectly required a UNORM resource and failed.
Its inspector/report remain in `reflection-mip-control-capture-1x-v1/mip-memory/`;
the corrected `mip-memory-v2/` verifies the typeless resource and actual UNORM
consumer view. Adjacent frame 1508 has not been inspected.

The standalone 1x kernel reuses the checked tiled addressing and fixed
2x2-neighbor offsets from the 2x kernel. The optimized D3D12 result matches
every byte of the CPU fixture, including base and guard preservation. A changed
input byte changes six generated bytes while guards remain intact. Sixteen
warmed eight-dispatch measurements give a **0.014336 ms median**, range
0.014336–0.016384 ms, on RTX 4080. These are isolated kernel measurements,
not gameplay or whole-frame savings. Evidence and runnable checks remain under
`b2/native-mip-unscaled-v1/`, with `check-mip-memory-1x.py` and
`make-mip-unscaled-kernel.py` in its parent directory.

| 1x artifact | SHA256 |
| --- | --- |
| HLSL | `473C416009BE9E0406C8FD52386395F7FF97E131B8226EB5F65927EBBD448AA4` |
| Compiled shader header | `C46C0E4BF302D34E190A81C87822CCD760564BD9FBF96B44853B6D7D5DD4859B` |
| Standalone checker EXE | `F5C9E47CA624BE14151438BE05C6235158C01739B35493E70B33295850409D05` |
| CPU reference / actual standalone GPU output | `D65B4D5490E258AC2CB624818CBA9F521E363D1038F7D12E03CA8673EF60AAEA` |

The combined diagnostic reuses the existing exact-list replacement and
restoring build/run helpers. At 1x it requests the complete shared-memory
interval, transitions that buffer for writing, dispatches the 1x shader and
marks UAV writes/publication through the existing helpers. At 2x it selects
the previous scaled-buffer path and shader, including the base-page checks.
Both retain original state/event packets and resolve-clear processing. This
is still fixed-address, captured-list admission, without production lifetime
or external-data validation and without upstream generation/decoding removal.

Candidate GPU:
`62B7F109B99A8838F57F86A1B446CECF103DE842599A2B3E9ECAF06756521FC0`.
EXE `7EA8294116970A817CA3112E5E5229D5DE1249F124F054FA11E721ACF359D70E`,
runtime `955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500`.
Main/SDK inputs: `89ff2cb` / `202247a`. The route remains
`19A53072C258EDFC2B05F5ECA3F263656A9D335C3EBB272B89B25ECAA00BA3E5`;
complete 22,012-entry pack/catalog identities are in the diagnostic plan.

Normal 1x session **`20260910T180734Z-p32316`** checks 634 consecutive complete
frames, 1252–1885, each with faces 0,4,2,1,3,5. The 3,804 face lists suppress
**30,432 mip draws and 30,432 resolve copies**. Separate capture session
**`20260910T180849Z-p30408`**, frame 1493, proves 48 native dispatches and zero
draws of the legacy mip shader pair. The native root UAV references shared
buffer 317 at guest base `1C879000`. Every byte of its 2,211,840-byte output
equals the CPU reference; no byte outside active mip pixels changes.

Copies 7839–7892 populate cube 8130. All **54 imported subresources / 524,286
pixels** match the native output. Event 7924 binds all six faces/nine mips
through UNORM with the same C347/21B70 consumer pair. Native output SHA256:
`4FA038E3A16A82D3A435B95AD284CCCA1FD5F465C7A9ED240B47676853D6BBC3`.
Its before snapshot contains previous native contents; the 316 changed bytes
do not establish current-frame legacy error or broader mutation coverage.
Adjacent frame 1494 and the new 1x runs' 20-second stills remain unreviewed.
The earlier 2x scratch-history proof does not qualify 1x scratch preservation.

**The same candidate fails its first normal 2x admission check.** Session
**`20260910T181130Z-p27232`** exits normally and passes ten inputs/three clocks,
as do both 1x runs. The reviewed 2x 20-second still shows the stopped Recaro
entry, intact car/road/HUD and passing traffic, but its log contains **zero
native admissions** and retains legacy mip work. The 2,211,840-byte producer
trace and full log are preserved. Both normal runs record the same known
startup filesystem error, with no GPU or native-contract error. A normal exit
and correct scene do not turn zero admissions into a passing replacement test.

The planned 2x capture was rejected by the admission gate before launch and
before creating `reflection-mip-replacement-capture-2x-v2/`; no such capture
exists at checkpoint. The failure's cause remains unknown. Inspect actual
submitted list contents and rejection guards using the existing scene-dump
observer or bounded rejection diagnostics. Do not assume a particular guard
or a shader error, weaken admission to get a pass, or repeat unchanged tests
until favorable. Rechecking the old 2x capture with generalized content/copy
checkers passes, but that validates the checkers, not this candidate's 2x path.

Local evidence: `b2/reflection-mip-replacement-dual-scale-v1/` includes plans,
eight source snapshots, binaries, build log, normal runs, producer traces,
`checkpoint-run-check.json` and `checkpoint-preflight.json`.
The new 1x captures are `reflection-mip-control-capture-1x-v1/` and
`reflection-mip-replacement-capture-1x-v1/`. Reproduction reuses
`make-mip-replacement-dual-scale-profile.py`, `run-mip-replacement-timing.ps1`
with explicit `-Profile`, `-Scale` and `-Case`, and the scale-aware
`run-hud-glass-capture.ps1`. `check-mip-dual-scale-checkpoint.py` audits the
normal-run identities, complete face counters and preserved 2x failure;
`check-native-mip-publication.py OUTPUT` rechecks actual 1x GPU/cube bytes.
Captured command arrays, shaders/blobs and diagnostic source remain local.

**Resume:** diagnose 2x rejection, qualify 1x scratch history, then establish
production semantic/external-data/lifetime admission and actual pre-packet
bypass. All 2,352 original packets per cube still decode. All B1-B4 scene,
streaming/partial-write/reuse/destruction, motion/NPC/UI timing and clean
matched tails/memory gates remain open. No B setting is retained, neither
stopped comparison is restarted and A6 remains symmetric-1x-only. Fresh
preflight verifies nine retained runtime files/backups, eighteen restored
source baselines and the complete staged 1x pack; all handles are terminal.
