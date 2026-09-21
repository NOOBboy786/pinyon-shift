# Performance optimization backlog

Status: planned; PERF-00 is ready. No new optimization or benchmark result is
claimed by this document. All implementation tasks below are unchecked.

Source: the user-supplied ten-optimization audit of `dev` at
`8049daa12d3dd1eb1e9e71fe96366c47b8007fbb`, reconciled with local source at
`2fa804c299c723ac7758330ac1da70b258588a4a`. Both pin ShiftGlue
`a6905c39aed6353916903ada3e0c840bbc39caa2`. The local SDK contains unrelated
uncommitted changes; an implementation baseline must record or exclude those
changes rather than identifying a dirty binary solely by the submodule pin.

The objective is lower frame time at equal visual quality and correct gameplay
speed, especially in sustained difficult scenes. Recompiled CPU code and
offline shaders already exist. The remaining opportunities concern resource
preparation, transfers, command processing, and synchronization.

This is the task breakdown for performance experiments under the existing
[resource migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md).
That checklist still owns B/C milestone completion and full Xenos retirement.
Creating this backlog does not resume previously deferred experiments or change
renderer defaults. The [UI API plan](../UI_API_PLAN.md) remains separate.

## Execution order and dependencies

IDs preserve the research ranking; execution starts with the smaller experiments.
Effort describes scope, not a delivery estimate. P0 establishes evidence; P1 is
the first implementation batch; P2 is selected using the resulting profile.

| ID | Priority | Task | Effort / owner area | Prerequisite | Migration link |
| --- | --- | --- | --- | --- | --- |
| PERF-00 | P0 | Establish current baselines and correlated traces | Medium / title tooling + SDK diagnostics | None; ready | Shared qualification |
| PERF-01 | P1 | Improve geometry-cache admission and residency | Medium / SDK geometry | PERF-00 | B2 |
| PERF-02 | P2 | Keep a complete depth/render-target lifetime native | Large / SDK render targets | PERF-00 + selected lifetime contract | B1 |
| PERF-03 | P2 | Avoid redundant texture reloads and conversions | Medium–large / SDK textures | PERF-00 + reload attribution | B2 |
| PERF-04 | P1 | Upload only dirty geometry regions | Medium / SDK geometry + shared memory | PERF-00 + owner policy established in PERF-01 | B2 |
| PERF-05 | P2 | Keep reflection cubes native through sampling | Large / SDK textures + render targets | PERF-00 + cube consumer inventory | B1 |
| PERF-06 | P2 | Bypass reflection-mip command production/decoding | Medium / title hooks + SDK commands | PERF-00 + mip side-effect contract | B3 |
| PERF-07 | P2 | Reuse prepared static command streams | Large / title hooks + SDK commands | PERF-00 + immutable-stream identity | B3 |
| PERF-08 | P1 | Reuse packed constant buffers | Medium / SDK bindings | PERF-00 + recurring-layout evidence | Preparation |
| PERF-09 | P1 investigate | Reduce critical-path submission gaps and waits | Medium / SDK submission + runtime | PERF-00 correlated timeline | Preserve AUD-01 |
| PERF-10 | P2 | Keep a post-processing/output subchain native | Large / SDK output + render targets | PERF-00 + selected subchain contract | B1 |

First batch: finish PERF-00, then evaluate PERF-01, PERF-04, and PERF-08 as
separate changes. Collect the PERF-09 timeline during this batch; change
submission policy only if the trace identifies a critical-path gap. PERF-04
can proceed if PERF-01 retains the current owner policy; it does not require
a larger cache to ship. PERF-08 has no geometry dependency.

Then select the highest measured resource cost among PERF-02/03/05/10. Start
PERF-06 or PERF-07 when command processing justifies it. PERF-05 and PERF-06
address different GPU/resource and CPU costs and do not depend on one another.
Qualify combinations separately; do not add their isolated savings together.

## PERF-00 — Establish a reproducible current baseline

Completed for the current hardware and AppData state on 2026-09-20. See the
[frozen baseline and PERF-01 result](PERFORMANCE_BASELINE_2026-09-20.md).

Reuse the [discovery workflow](DISCOVERY_PLAYTEST.md),
[render-test runner](FH1_RENDER_TEST_AUTOMATION.md), and
[performance summarizer](../../tools/summarize-performance.py). Add missing
counters only where needed by the first candidate; no new benchmark framework.

- [x] Freeze main/SDK revisions and patches, actual EXE/runtime/renderer hashes,
  build flags, shader pack/catalog hashes, resolution, render scale, AA,
  post-processing, frame cap/VSync, GPU/driver, OS, and save/route identifiers.
  Use the [AppData launch procedure](../../AGENTS.md); never reset or copy saves
  to manufacture matching runs. Record changing traffic, weather, and car state.
- [x] Define fixed gameplay windows for Carson town and Hot Hatch Hustle,
  Outpost/plaza, the wooded-junction approach, and high-speed highway travel.
  Use [historical discovery findings](DISCOVERY_FINDINGS_2026-09-08.md) as route
  leads; establish exact locations and input sequences before timing. Separate
  stationary controls, moving routes, and race workloads.
- [x] Establish repeated warmed controls at 1x and 2x; measure cold-cache runs
  separately. Treat 3x and additional hardware as separate qualification, not
  coverage inherited from 1x/2x. Verify source-frame/presentation clocks and
  NPC/UI duration against real time before comparing speed.
- [x] Correlate source frames, CPU preparation, submissions/fences, GPU work,
  ready/idle gaps, and residency in diagnostic captures. Inventory existing
  counters for allocations, imported bytes, fallback reasons, reloads, and
  constant packing; mark unavailable metrics explicitly.
- [x] Run clean timing controls with corpus/per-face logging and GPU captures
  off. `tools/start-fh1-discovery.ps1 -PerformanceOnly` is an existing entry
  point; verify inherited settings and keep screenshots outside measured windows.
  Discovery's sampled pass spans cannot alone establish critical-path cost.
- [x] Before candidate runs, record the primary metric, route/window duration,
  warmup, memory ceiling, acceptable median/p95/p99 regression limits, and noise
  estimate. Use at least two alternating A/B/B/A blocks on each affected
  route/scale; retain all valid results. Set the sustained window length after a
  pilot, long enough to revisit streaming boundaries and characterize tails.
- [x] For any Xenia claim, pin its revision/configuration and match internal and
  output resolution, AA, post-processing, route, and gameplay speed. Compare
  equivalent frame measurements; window changes and FH1 source frames are
  different clocks.

Done when: a local baseline manifest, route definitions, per-run summaries, and
timeline identify candidate costs and measurement noise. Summarize findings in
this document with evidence paths. No candidate is justified solely by draw
counts or an isolated slow sample.

## PERF-01 — Geometry admission and working-set residency

Measured on 2026-09-20. The shipping 32 MiB routes showed no repeated rejected
admissions, so the tested rejection memo remains opt-in and the memory/residency
defaults are unchanged. See the
[baseline and experiment result](PERFORMANCE_BASELINE_2026-09-20.md).

Entry point: `D3D12CommandProcessor::GetFh1OwnedGeometry()` in
[command_processor.cpp](../../thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp).
The 32 MiB/512-entry cache and recent-frame protection already exist. The
[retained Carson fix](CARSON_GEOMETRY_CACHE_FIX.md) is the control, not new work.

- [x] Count repeated rejected requests, allocation-info calls, eviction scans,
  native hits, allocations, imports, fallback reasons, and peak resident bytes
  during the sustained dense-scene routes.
- [x] Test a bounded rejection cache if repeated admission work is material.
  Key it by owner/request generation and rejection reason; retry when the
  relevant frame age, completed fence, capacity, or ownership condition changes.
  Allocation failure must not permanently suppress later admission.
- [x] Sweep a small documented set of memory budgets around the current value,
  then evaluate admission by reuse/import cost saved. Compare rejection caching
  and budget changes separately before testing a combination.
- [x] Extend [geometry-cache checks](../../tools/check-fh1-geometry-cache.py)
  for rejection expiry, recent/in-flight protection, address reuse, and fallback.
  Preserve one generation across CPU snapshots and GPU bindings. Pooling and
  recycling remain deferred until admission data justifies them.

Accept when: admission/allocation work falls and dense-scene p95/p99 improves
within the predeclared memory ceiling and correctness gates. Reject a policy
that merely raises hit rate while increasing memory pressure or tail latency.

## PERF-02 — Complete native depth/render-target ownership

The post-PERF-09 scaled retry was evaluated and rejected; see the
[PERF-02/PERF-05 investigation](PERFORMANCE_02_05_RESULTS_2026-09-21.md). The
existing 1x chain remains retained, while further scaled work requires a changed
design rather than another run of the same ownership path.

Entry points: SDK D3D12 render-target preparation/transfers and
[render_target_cache.cpp](../../thirdparty/shiftglue-sdk/src/graphics/d3d12/render_target_cache.cpp).
Start from the [owned-depth contract](OWNED_DEPTH_CHAIN_CONTRACT.md) and
[A6 retention evidence](A6_OWNED_DEPTH_RETENTION.md). Native 1x clears already
exist; scaled ownership previously failed frame-tail retention.

- [x] Select one costly depth/shadow lifetime from PERF-00. Document initial
  contents, partial clears, depth/stencil writes, every reader, alias, and reuse
  boundary, including any required compatibility bridge.
- [ ] Keep its native target authoritative across that entire interval and
  remove transfers only where no compatibility consumer needs them. Count both
  eliminated and newly introduced transitions/transfers.
- [ ] Separately test conservative clear-rectangle coalescing if rectangle
  overhead is material. Compare exact coverage, including holes and uncleared
  depth/stencil regions; a bounding box is not generally equivalent.
- [ ] Extend [owned-clear checks](../../tools/check-fh1-owned-depth-clear.cpp)
  and inspect motion, stencil, shadows, partial writes, history, and alias reuse.
  Qualify each scale independently; preserve fallback outside the admitted chain.

Accept when: transfer fragments and chain GPU cost fall without worse frame
tails or output errors. Fewer clear calls with more expensive transfers fails.

## PERF-03 — Texture lifetime tracking and reload elimination

Completed as a deferred dependency on 2026-09-21. The measured recurring loads
are changed GPU-producer outputs, so immutable caching would be incorrect and
their native lifetime is owned by PERF-10. See the
[PERF-03 attribution result](PERFORMANCE_03_RESULTS_2026-09-21.md).

Entry point: `D3D12TextureCache::LoadTextureDataFromResidentMemoryImpl()` in
[texture_cache.cpp](../../thirdparty/shiftglue-sdk/src/graphics/d3d12/texture_cache.cpp).
An existing texture cache, CPU BC3 conversion, and scaled load paths are the
starting point; this task does not introduce another generic cache/converter.

- [x] Attribute each recurring load to allocation identity, payload generation,
  view, producer ownership, and invalidation reason. Measure conversion/copy
  bytes and time, scratch/descriptor allocation, and resident representations.
- [x] Choose one measured cause: unchanged streamed payload reloaded after a
  neighboring write, duplicate representations, or native-producer reimport.
  Native-producer reimport was selected; its bounded implementation is PERF-10,
  so no overlapping texture-cache change was made here.
- [x] Evaluate converted immutable retention. No recurring unchanged payload was
  found; native resource sharing requires PERF-10's verified format, visibility
  and lifetime contract.
- [x] Gate partial/neighboring writes, address reuse, eviction, view changes,
  GPU writes and streaming transitions. No cache candidate advanced to that
  matrix; the PERF-10 resource-sharing candidate must pass it instead.

Accept when: reloads and converted/copied bytes fall with measurable preparation
or frame-time benefit and no stale textures. Historical sparse 1.0–1.2 ms samples
in the supplied audit are a lead, not a current texture budget or hitch cause.

## PERF-04 — Precise dirty geometry updates

Evaluated and rejected on 2026-09-20. See the
[PERF-04/PERF-08 results](PERFORMANCE_04_08_RESULTS_2026-09-20.md). Dirty-range
uploads reduced transferred bytes, but the 2x frame-time cross-check regressed.

Entry points: `GetFh1OwnedGeometry()`, its bounds/snapshot consumers, and
[shared_memory.cpp](../../thirdparty/shiftglue-sdk/src/graphics/shared_memory.cpp).
Resident owners currently refresh whole 64 KiB-aligned windows on invalidation.

- [x] Measure import amplification: imported bytes divided by known modified
  bytes, plus snapshot copies, upload bytes, and bounds-cache invalidations.
  If only invalidated-page coverage is observable, label it as a proxy for
  changed bytes. Skip added tracking if amplification/copy cost is small.
- [x] Prototype dirty ranges within one stable owner; keep full-window import
  as fallback for unknown/GPU write coverage. Coalesce uploads only while
  preserving generation consistency and dirty writes arriving during import.
- [x] Prototype invalidating only index bounds that overlap changed bytes.
  Reduce snapshot extent only if every bounds reader can still obtain the
  matching GPU generation.
- [x] Exercise [production cache checks](../../tools/check-fh1-geometry-cache.py)
  for concurrent invalidation, overlap, GPU writes, reuse, and in-flight data;
  use [geometry replay checks](../../tools/check-fh1-owned-geometry-replay.py)
  for actual uploaded-byte parity.

Accept when: snapshot/upload bytes and copy cost decline enough to exceed
tracking overhead, without mixed-generation bounds/bindings or missing geometry.
Existing containment/recycling experiments are not prerequisites to enable.

## PERF-05 — Native reflection cubes through their consumers

The producer/consumer inventory and measured import volume are recorded in the
[PERF-02/PERF-05 investigation](PERFORMANCE_02_05_RESULTS_2026-09-21.md).
The first accepted implementation now writes the persistent consumer cube
directly, eliminating the measured scratch allocation and 54 copies per full
refresh. Producer-side ownership remains open.

Entry points: SDK D3D12 reflection face targets, texture import, mip publication,
and later sampling. Reuse the [mipmap contract](REFLECTION_MIPMAP_REPLACEMENT.md).
The current replacement has no persistent native cube mirror.

- [x] Inventory all cube producers/consumers, six-face update order, mip history,
  invalidation, aliases, format/scale requirements, and compatibility readers.
- [ ] Carry one authoritative native resource from face rendering through mip
  generation to sampling; bridge only for a proven compatibility consumer.
- [x] Count cube imports, copies, barriers, bytes, residency, and fallback.
  Check all 54 subresources for the existing six-face/nine-level contract and
  inspect later consumers over multiple changing frames.
- [ ] Qualify motion, partial face updates, reuse, streaming, and supported
  scales. Capture the reported green-glass failure before attributing it to this
  path; a clean frame does not resolve the existing report.

Accept when: imports/intermediate copies fall and whole-frame performance improves
without stale or flashing reflections. Further tuning the already small mip
kernel is outside this task unless a fresh profile identifies it as material.

## PERF-06 — Reflection-mip producer and decoder bypass

Entry points: title cached-list generation/submission and SDK command dispatch;
the [existing mip replacement](REFLECTION_MIPMAP_REPLACEMENT.md) still processes
six guest lists and 2,352 packets per cube.

- [ ] Locate the earliest verified boundary where the complete admitted mip
  operation is known; time its producer and decode work separately.
- [ ] Enumerate state restoration, events/queries, scratch clears, ownership
  transfers, dirty tracking, and ordering that must survive a bypass.
- [ ] Submit a compact native operation at that boundary, preserving every
  observable side effect and falling back for unsupported or changed input.
- [ ] Extend [mip contract checks](../../tools/check-fh1-mip-contract.cpp) for
  relocation, mutation, inherited state, and side-effect equivalence. Verify
  producer/decoder counters actually disappear, not just draw counters.

Accept when: targeted generation/decoding and CPU time decline with correct
state and frame results. The historical residual six-list CPU cost was about
0.2 ms; treat this as a bounded candidate, not a promised large FPS gain.

## PERF-07 — Prepared static command streams

Entry points: SDK command processing plus the title boundaries recorded in
[renderer research](RESEARCH.md). Previously observed eligible draws did not
form useful consecutive batches; blanket instancing is not this task.

- [ ] Select one demonstrably immutable recurring stream and measure decode /
  preparation cost, recurrence, and its dynamic inputs.
- [ ] Define identity using command generation, inherited state, resource
  generations, and dynamic patches; address alone is insufficient.
- [ ] Cache its prepared template, or submit directly from a verified title
  boundary if simpler. Preserve draw order and existing visibility/LOD decisions.
- [ ] Check mutation, relocation, inherited-state changes, invalidation,
  resource destruction, queries, and fallback. Bound entries and cache memory.
  PERF-06's side-effect audit may be reused, but its implementation is optional.

Accept when: interpreted packets and preparation CPU fall with identical order
and visible output, even if draw count stays constant. Defer if stream identity
or reuse is too weak to repay validation/cache overhead.

## PERF-08 — Packed constant-buffer reuse

Evaluated and rejected on 2026-09-20. See the
[PERF-04/PERF-08 results](PERFORMANCE_04_08_RESULTS_2026-09-20.md). Existing
packing consumed about 0.11 ms per frame; safe cache identity would cost too
much relative to that upper bound.

Entry point: `D3D12CommandProcessor::UpdateBindings()` in
[command_processor.cpp](../../thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp).
Current-binding dirty checks already avoid redundant uploads. A prior float
upload batching candidate was reverted; it is not the implementation baseline.

- [x] Measure A → B → A layout recurrence, vectors packed, upload requests, and
  packing CPU time. Establish reuse potential before adding a cache.
- [x] Evaluate whether a shader-layout gather plan is warranted. The combined
  allocation and packing cost is only 0.11 ms/frame, so it was not implemented.
- [x] Evaluate a bounded cache keyed by layout and relevant register
  generations. It was rejected before implementation because safe identity and
  frame/fence lifetime tracking target only the 0.11 ms/frame upper bound.
- [x] Check the required correctness surface: relevant and irrelevant register
  writes, layout switches, rebasing, rollover, eviction, and in-flight upload
  reuse. No candidate advanced to binding-parity testing.

Accept when: demonstrated reuse reduces packing time/upload allocation and
passes frame/memory gates. Reject if generation tracking costs more than it saves.
Whole-register hashing per draw and handwritten SIMD are not the starting point.

## PERF-09 — Submission boundaries and dependency waits

Completed on 2026-09-20. See the
[PERF-09 results](PERFORMANCE_09_RESULTS_2026-09-20.md). The measured cause was
avoidable queue gaps and full barriers at primary-buffer submission boundaries;
frame-end coalescing is now the default D3D12 policy.

Entry points: `d3d12_submit_on_primary_buffer_end`, submission/query paths, and
the existing [startup/fence correctness contract](../DEVELOPMENT.md#startup-correctness-aud-01-and-aud-02).
This is an investigation until a correlated trace establishes causality.

- [x] Correlate submission size, CPU recording, GPU start/end, fence waits,
  residency, and OS scheduling for repeatable spikes and normal frames.
- [x] Choose the observed cause: combine tiny submissions for CPU overhead,
  submit earlier for GPU starvation, or retire query results asynchronously
  where the title permits it. Test one policy change at a time.
- [x] Preserve queries, memory exports, ordering, cancellation, device failure,
  and shutdown draining. Extend [startup checks](../../tools/check-fh1-startup.py)
  where fence behavior changes and test the affected query path.
- [x] Verify smaller critical-path gaps in a diagnostic trace, then repeat clean
  route timings. Do not add overlapping wait/CPU/GPU buckets or explain a single
  long GPU span solely by the shader inside it.

Accept when: identified idle gaps and p95/p99 decline without excess latency,
memory, or altered guest behavior. If no avoidable critical-path gap appears,
record that result and defer policy changes; never bypass fences or fake results.

## PERF-10 — Native post-processing/output subchain

Entry points: SDK D3D12 full-screen replacements, render targets, resolves,
texture consumption, and output publication. The title's
[guest_output_renderer.cpp](../../src/native_renderer/guest_output_renderer.cpp)
currently installs a render-test observer, not a production scene renderer.

- [ ] Select one costly color/post-processing subchain. Enumerate intermediates,
  later readers, temporal history, aliases, and guest-visible consumers before
  treating any target as final output.
- [ ] Keep intermediate textures native through consumption; remove only proven
  unnecessary resolve/reimport cycles. Evaluate fusion separately where
  dependencies and precision allow it.
- [ ] Verify crop versus padded backing dimensions, gamma/color space,
  temporal effects, partial writes, and correct source-frame publication.
- [ ] Count full-screen copies, conversions, bytes, transitions, and end-to-end
  cost. Review moving gameplay, map, pause, photo, video/transitions, and each
  admitted scale. Preserve compatibility fallback outside the chosen contract.

Accept when: copies/conversions and whole-chain cost fall without frame/history
errors or visual regressions. The rejected scaled-accumulator presentation
experiment is not an accepted starting implementation.

## Shared completion and evidence requirements

For each implementation, follow the existing
[retention gates](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md#gates-for-every-retained-change).
Before closing a task:

- [ ] Show the targeted work removed and the clean whole-frame result, including
  per-run median/p95/p99, CPU/GPU measures with their sampling definitions,
  memory/residency, admissions/fallback, and the agreed regression limits.
- [ ] Pass the affected production-contract checks and visual/motion/lifetime
  matrix. Include streaming, reuse, partial writes, overlap, and in-flight
  ownership when the change touches resources. A normal exit alone is not proof.
- [ ] Record actual binary identities and the exact rollback switch or revert.
  Keep unsupported cases on the existing path until independently qualified.
- [ ] Land SDK implementation and title tooling separately as appropriate;
  reference the tested SDK commit before updating the title submodule pin.
  Update the linked B/C item only for the scope actually qualified.

Use `.local/native-renderer/performance/<task-id>/<run-id>/` for raw captures,
manifests, CSVs, and rejected attempts. Commit only an asset-free result summary
and reproducible instructions. The existing summarizer accepts a session CSV
and `--baseline <summary.json>`; for route windows, select and verify the same
bounded interval first rather than comparing mixed whole-session medians.

Each result records: task ID; control/candidate revisions and hashes; route /
scale / cache state; changed work counters; per-run frame statistics; memory;
correctness coverage; decision; evidence path; rollback. Allowed decisions are
retain, reject, inconclusive, or deferred. A rejected experiment does not mark
its parent optimization complete. A dependency-removal milestone may be retained
without a frame-time win only if it is faithful and has no material regression;
label it accordingly and do not publish an FPS improvement.

## Explicitly deferred

- General PGO/ThinLTO/compiler-flag sweeps, import-tracing disablement, and more
  shader prewarming without a new measured hotspot.
- Broad asynchronous I/O, audio/decompression, or scheduler rewrites based on
  warm-run aggregate totals rather than critical-path evidence.
- Generic texture caches, bindless resources, viewport caching, dirty-state
  binding checks, bulk register writes, and offline shader preparation already
  present in the renderer.
- Blanket instancing, speculative shader replacements, and enabling old
  containment/recycling/HUD/scale experiments without a revised contract.
- Lower-quality presets as evidence of equal-settings performance gains;
  those remain the separate B4 visual-profile task.

The supplied audit's re:Blue and Lost Odyssey examples are optional investigation
leads for interception placement and clear coalescing. Recheck pinned upstream
source if adopting either technique; their results do not establish an FH1 gain.
