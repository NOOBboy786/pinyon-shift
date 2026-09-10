# Native renderer: resource migration checklist

Execution checklist derived from the [renderer research](XBOX360_NATIVE_RENDERER_RESEARCH.md).
This defines the next work order within P2/P3 of the [main backlog](NATIVE_RENDERER_BACKLOG.md).
Existing correctness and retention rules still apply; P0/P1 remain open and deferred.

## Objective

Reduce rendering cost and hardware requirements by moving complete FH1 resource
lifetimes and their producing/consuming passes under native ownership. Reuse
suitable translated shaders. Ultimately run without Xenos command processing,
resource management, or hidden renderer fallback.

Track performance gains and dependency removal separately. A shader replacement,
a correct screenshot, or a completed experiment alone does not establish either.

## Starting point

- Existing shader packs, native specializations, video upload, discovery tools,
  timing, and test routes remain the foundation.
- Ordinary transfer intervals measured approximately 5.7 ms per sampled frame
  at 2x resolution. This is diagnostic attribution, not fully removable frame time.
- Both the depth-address shortcut and GPU stencil-predication experiment failed
  retention. Predication was removed from production. Do not repeat either
  unchanged, or reopen rejected RGBA8/direct-output/geometry candidates without
  new evidence or a materially different design.
- `tools/rank-fh1-transfer-contracts.py` now reproduces complete transfer-list
  rankings. Native timestamps remain usable without Windows Developer Mode;
  unavailable replay counters must not block independent work.

Source of current status: the latest sections of [P2 dependency ranking](P2_DEPENDENCY_RANKING.md).
Recheck those sections before implementation; this checklist is not a binary manifest.

## A — First complete native resource chain

A1-A6 complete for the retained 1x owned depth-clear chain. 2x uses the
qualified compatibility path; see [A6 retention](A6_OWNED_DEPTH_RETENTION.md).

- [x] **A1 — Establish a matched chain-cost baseline.** Reuse complete transfer
  contracts and existing source-frame/session timing. Select one expensive chain,
  starting with the dominant D24S8 chain unless another has a stronger opportunity.
  Record 1x/2x workload, actual transfers, preparation, and measurement losses.
  **Done:** reproducible evidence attributes cost to the complete chain and
  distinguishes GPU intervals from total frame time; no descriptor-count grouping.
- [x] **A2 — Prove the resource lifetime and game boundary.** Trace creation,
  clears, draw writes, partial regions, resolves, reads, reuse and destruction.
  Identify the actual game producer and every required consumer, including
  depth/stencil, aliasing, queries and guest-visible writes.
  **Done:** a documented contract explains what survives each transition and
  identifies the earliest usable hook; unknown consumers remain explicit.
- [x] **A3 — Implement native ownership for the selected chain.** Reuse existing
  D3D12 resources and suitable shaders; give the chain explicit resource identity,
  generation and lifetime. Choose a boundary that removes measured work.
  **Done:** the native producer and consumers execute on owned resources, with
  observable admission and correct fallback for unsupported inputs during migration.
- [x] **A4 — Preserve history without unconditional copies.** Allow direct
  sampling or deferred copies only where the contract permits. Materialize old
  contents before conflicting writes, reuse or destruction; preserve partial regions.
  **Done:** changing-content, overwrite, partial-write and lifetime checks pass,
  including nonzero stencil where relevant; captured zeros are never an admission rule.
- [x] **A5 — Remove the replaced work.** Suppress only transfers/passes whose
  required outputs are now supplied natively. Count retained compatibility work
  and any new publication copies, conversions or synchronization.
  **Done:** captures/counters prove the intended operations no longer execute,
  with required side effects preserved and no duplicate rendering behind native output.
- [x] **A6 — Qualify and retain the chain.** Compare against the qualified build
  with repeated matched runs at 1x/2x, screenshots and motion. Include ordinary
  driving/racing and a recorded difficult area relevant to the chain.
  **Done:** a retained implementation demonstrates useful performance/memory
  savings, or a real dependency removal without material regression. Document
  scope, median/p95/p99, CPU/GPU cost, memory and remaining fallback.

Implementation status, 2026-09-09 UTC: **A epic complete for the bounded 1x chain.**
The native owned depth clear is retained and enabled by default only at symmetric
1x resolution. Its longer ordinary-scene and North Carson comparisons support
retention; 2x tail tests fail, so scaled rendering keeps compatibility clears.
Final default-setting 1x/2x race-start checks pass on the retained DLL, with native
admissions at 1x and zero owned clears at 2x. See [A6 retention](A6_OWNED_DEPTH_RETENTION.md)
for exact identities, measurements, validation and limits, and the
[chain contract](OWNED_DEPTH_CHAIN_CONTRACT.md) for resource correctness.
A2 identifies the game GPU clear producer and verified draw boundary; upstream
CPU packet-emitter bypass remains B3. This is useful retained native ownership at
1x, not completion by merely rejecting the 2x experiment.

If a candidate fails, archive the evidence, restore the qualified path and select
a different design or measured chain. A rejected candidate closes that experiment;
it does not complete A3–A6. Do not expand a failing design merely to increase coverage.

## B — Expand the demonstrated approach

Start after A6. Each item needs its own bounded implementation and evidence.
The B1-B4 goal is active; see [B execution and coverage](B_EPIC_EXECUTION.md)
for the fixed scene set, discovery accounting correction and opt-in tile-clear
candidate. GPU clear/publication and live eviction checks now pass, but no new
optimization is retained: 1x triage is unfavorable and the 2x long comparison
has a HUD workload mismatch. B2 now has measured allocation-churn attribution,
opt-in buffer recycling and a bounded GPU copy proof, but the mixed Outpost/local
comparisons do not establish retention. Paid Outpost travel is unavailable until
normal play replenishes credits; free routes remain usable. Stable containment
has bounded 1x/2x GPU validation, but live mutation/streaming and retention remain
open. A completed 1x handbrake comparison has mixed timings, more imported bytes
and differing traffic; 2x performance remains unqualified. B3 now has
live clear-producer attribution (about 0.03-0.045 ms/frame median in the local
scene); downstream decode attribution and actual pre-packet bypass remain open.
See the [current checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md).
All B items remain open.
B1 also tracks corrupted car-selection thumbnails, present in the retained
control and corrected-CRT probes. The separate CRT configuration correction
passes bounded 1x/2x race smoke checks; it completes no B item.
B2 now has a default-off 64 KiB invalidation candidate with lower import rates
in two bounded runs. An incomplete HUD-gated comparison prevents retention;
see the checkpoint for the revised, unexecuted workload protocol.
Later update: the revised protocol is exercised with strict early/late HUD gates,
but its comparison also stops on a missing early HUD. Dense captures reproduce
intermittent HUD absence on both the retained renderer and candidate flag-off;
UI/output attribution is now required. The separate CPU-only snapshot shortcut
was implemented and archived after its bounded avoided bytes measured below
0.4%. Neither experiment completes or retains a B item; see B execution.
Latest source-linked diagnostic attributes about 22.47 ms/frame of early-race
CPU work to geometry allocation/eviction and maps two HUD gaps to frames with
148 absent draws. Their correlation with the HUD gap does not yet establish HUD
production. Measure recycler work and trace the actual HUD resource chain next;
no cause fix or speedup is retained.
Broader scene coverage, mutation/streaming, clean comparisons and timing remain
required. GPU sampling is sparse and unsampled cost remains unavailable.
Follow-up: the recycler now searches for a completed exact-size victim beyond
the oldest entry. Production-cache checks and strict 1x/2x HUD/hold/motion smoke
runs pass. A larger-capacity experiment is archived after increased cache
rejections and late recurring work. The matching-victim option remains off;
actual GPU copy/consumer checks, matched tails/memory, sustained streaming and
the full scene set remain required before retention. See B execution for all
identities and the unresolved HUD/thumbnail defects.
Latest GPU evidence checks 18 actual 2x recycled copies and their first draw
consumers, including ten matching victims beyond the oldest entry. A second
capture has no marked copies and remains an explicit coverage gap. Direct
replay also verifies HUD outputs from nine draws of the three correlated shader
pairs; their CPU producer and omission cause remain open. A retained single-
confirmation route passes the original HUD/hold/motion gates, but still needs
race-stage repeatability before matched comparisons. These bounded results
retain no new setting; see the latest checkpoint and B execution.
The first stage-comparison block then fails event arrival. New test-input and
capture-clock telemetry plus a braked-entry route pass bounded validation.
One same-binary recycler off/on pair improves early median 46.015→25.222 ms,
but later tails rise and memory/repeated 1x/2x/streaming gates remain open.
This prioritizes repeated qualification; it does not retain the option.
The repeated C-A-B-B-A-C comparison now has its first C/A/B runs at 1x,
with passing input/race-stage/HUD gates and valid process/GPU-memory samples.
The remaining 1x repeats and all 2x runs are pending at the requested checkpoint.
Early recycling results remain promising, but later tails and the incomplete
comparison prevent retention. See the latest checkpoint for exact resume state.
Follow-up: the final 1x control skips a 100 ms menu pulse, stopping that block.
A widened-pulse route passes bounded injected checks; one normal 1x capture
now verifies 12 recycled GPU copies and first consumers. Earlier capture
device loss remains unresolved, and its control exposes eight precompiled
shader-variant gaps. Presentation-loss HRESULT logging is added; no renderer
setting is retained. B execution/checkpoint preserve all failures, new B4 static
postprocessing anchors and the unchanged full B1-B4 requirements.

Latest correction: those eight variants already exist in the current offline
packs; the control used a stale staged 1x pack. Explicit staging and immutable
pack/catalog pins now precede the new widened-pulse comparison. Its first 1x
control passes input/clock/HUD/motion gates with zero GPU errors; the remaining
five 1x and all six 2x runs are pending. See the latest checkpoint for the next
run. This resolves the observed staging gap, retains no optimization and leaves
the full B1-B4 scope open.

- [ ] **B1 — Migrate the next highest-value chains.** Rank remaining resource
  dependencies, then repeat the A2–A6 contract and retention checks.
  **Done:** required pass families have native producers/consumers and an explicit
  inventory accounts for every remaining compatibility dependency in the scene set.
- [ ] **B2 — Reduce geometry/texture preparation where measured.** Use proven
  allocation identity and mutation/lifetime hooks for persistent buffers and texture
  mirrors. Move conversion earlier only when it improves measured first-use cost.
  **Done:** imports, allocations or conversion recurrence fall without stale data,
  missing streamed content, higher memory pressure or worse frame-time tails.
- [ ] **B3 — Bypass obsolete guest command generation.** For covered chains,
  replace the producer path before packet emission where its contract permits.
  **Done:** less command generation/decoding is measured, and queries, fences,
  memory export and other guest-visible behavior remain correct.
- [ ] **B4 — Qualify a lower-cost visual profile.** Test individually measured
  AA, shadow/reflection, scene-scale or postprocessing changes; combine only retained
  settings. Mark an effect inapplicable if attribution shows no worthwhile opportunity.
  **Done:** the profile has documented visual differences and repeatable savings
  in representative motion, including correct NPC/UI timing at supported frame rates.

B1 follow-up: the 2x owned-clear optimization failed North Carson tail retention
(short p99 +24.46%, longer p99 +90.09%). Keep the 1x-only guard until actual
attribution or a changed design earns fresh scaled qualification. Do not repeat
the unchanged 2x candidate. Other measured chains may offer better next work.

Research references: Unleashed's lifetime/copy handling, re:Blue's history and
resource mirrors, Skate's complete-pass suppression, and Marathon's producer-side
tiling removal. Their game-specific assumptions are examples to investigate,
not FH1 contracts to copy.

## C — Retire Xenos and qualify lower requirements

- [ ] **C1 — Close remaining rendering dependencies.** Cover required geometry,
  textures, render targets, resolves, presentation, readbacks and guest side effects.
  **Done:** qualification routes report no renderer fallback or unhandled dependency,
  including menus, video, race transitions and streaming; coverage limits are explicit.
- [ ] **C2 — Run without the Xenos renderer.** Remove superseded command/resource
  paths and renderer build dependencies after their replacements are qualified.
  **Done:** a clean build runs the scene set without the Xenos renderer linked or
  invoked. Keep required offline shader production separate from runtime retirement.
- [ ] **C3 — Validate lower hardware requirements.** Reuse P1/P4 qualification;
  test lower-end discrete and integrated/UMA hardware with stated settings and
  sustained difficult scenes. Identify hardware still unavailable for testing.
  **Done:** publish only demonstrated FPS/frame-time and memory targets, with
  adapter/API/driver and quality settings. Compare pinned Canary separately where
  available; another game's claims cannot establish FH1 requirements.

## Completion and evidence rules

For each checked item, append its result and evidence link here; keep detailed
logs in the existing ranking/checkpoint rather than duplicating them. Record the
qualified source/binary identity, removed work, remaining dependencies, and limitations.

Preserve simulation, geometry, resource contents, ordering and guest-visible side
effects. Small stable visual differences require an explicit benefit and motion
review. Measure profiling and clean benchmarks separately. A newly introduced
timing defect must be fixed before retaining the change; existing P0 issues remain
tracked independently and must be resolved before broader release qualification.

## Suggested next goal

Proceed to B1: rank the next valuable resource chain against the retained 1x
owned-depth implementation, then qualify one bounded migration. Keep the failed
2x clear optimization disabled unless new attribution supports a changed design.
B/C expansion, broader town stalls and full Xenos retirement remain open; do not
claim new hardware requirements from this first-chain result.

## Earlier evidence (historical, superseded by A6 retention)

Progress, 2026-09-09 UTC: an opt-in early owned-depth clear candidate now builds
and runs at 2x with thousands of admissions. CPU mapping checks pass; a single
probe shows fewer ordinary transfer intervals. GPU content/history equivalence,
matched repeated performance and motion remain unqualified. See the latest
[dependency-ranking entry](P2_DEPENDENCY_RANKING.md). A1–A6 remain unchecked.

Earlier evidence: A1/A2 remain incomplete. A full-frame resource-use
audit confirms the dominant 4x D24S8 target has 36 transfer draws and no guest
geometry draws; its other writes are clears. Reads feed transfers and EDRAM
resolve dumps, including later mixed floating-depth preservation. Inspect native
rectangle-clear admission before render-target Update as the next ownership
experiment; this is not permission to skip a clear or its downstream history.
Evidence: `p2/native-chain-usage/{report,summary}.json`, local audit/check scripts,
and the latest [dependency-ranking entry](P2_DEPENDENCY_RANKING.md).

> Complete A1–A6: qualify and retain one complete FH1 resource chain under native
> ownership, removing its measured redundant transfer/pass work while preserving
> required resource history and guest-visible behavior. Reuse existing shaders,
> tools and D3D12 facilities. Verify 1x/2x performance, frame-time tails and motion,
> record remaining dependencies, and continue to another measured chain if the
> first candidate fails retention. Do not claim completion from a rejected experiment.

The full migration objective remains A–C. The focused goal provides a concrete
architectural milestone without making complete Xenos retirement a prerequisite
for the first useful result.
