# Pinyon Shift native renderer V3 backlog

Status: active north star, 2026-09-01

This document is the execution order for finishing the native renderer. It
supersedes `REPRIORITIZED_PLAN.md` for prioritization and day-to-day decisions,
but it does not replace the evidence and architecture recorded there or in
`PINYON_SHIFT_NATIVE_RENDERER_INVESTIGATION_AND_EXECUTION_PLAN.md`.

V3 is organized around one correction: isolated native draws and isolated
targets are not a scene. The shortest route to visible progress is to retain a
proved camera-correct gameplay scene, add only the families it is actually
missing, and compose them before publication.

The final scope is unchanged. The early milestone is deliberately smaller so
that a camera-correct, drivable hybrid renderer is available before completing
every effect and retiring Xenos.

## Current truth

The following foundations are merged or substantially qualified on `dev`:

- native D3D12 draw replay into private render targets;
- shader, resource, material, pass, camera, draw, and ownership provenance;
- resource identity, caching, invalidation, deferred destruction, and GPU
  lifetime handling;
- continuous replay worksets and exact procedural-color replay;
- private resolve assembly and presentation ingress;
- exact native replay of a bounded dynamic-shadow epoch;
- Xenos fallback, fail-closed publication, renderer selection, and independent
  suppression controls;
- capture, comparison, report, and AppData-backed qualification tooling; and
- direct renderer-backend iteration in the in-tree ShiftGlue fork.

The following are not complete:

- a coherent native open-world frame;
- camera-consistent composition of terrain, road, static world, sky, and
  vehicles;
- a drivable native or hybrid prototype with acceptable frame pacing;
- complete lighting, reflections, transparency, post-processing, frontend,
  and special-mode coverage;
- production pass suppression and material Xenos workload reduction;
- independent low-requirement quality profiles; and
- a no-Xenos build.

The current supported path keeps Xenos authoritative. Native worksets remain
private because publishing the last isolated target produced the wrong view
and an incomplete world. The old procedural-only scaled accumulator is not a
complete-scene source. The qualified 1x combined producer lifecycle is
different: reseeding its retained target at each exact resolve boundary
produces the camera-correct gameplay base and is the V3 prototype source.

## Rejected approaches and retained lessons

These paths produced useful evidence and infrastructure, but they did not
produce a coherent gameplay scene. Do not restart them as prototype leads
without satisfying the stated revisit condition. Detailed chronology and
runtime evidence remain in the earlier plans and their linked reports.

| Approach | Observed result | V3 decision | Reusable work | Revisit condition |
| --- | --- | --- | --- | --- |
| Publish the last completed isolated target | Displayed whichever scene family finished last, producing the wrong camera, repeated fragments, and a missing open world | Rejected as a scene architecture; [PR #308](https://github.com/arcanite24/pinyon-shift/pull/308) restored Xenos-authoritative output | Isolated replay, target identity, invalidation, and publication safety gates | Do not revisit; replace it with camera-consistent multi-target composition |
| Treat the procedural scaled accumulator as a complete scene | Correctly assembled regions from one procedural producer, but could not supply terrain, static world, vehicles, and background as one frame | Retain as diagnostic and producer evidence only | Resolve topology, source-region contracts, exact copies, and private accumulation | May feed one compositor slot after V3-01, but must never define scene completeness |
| Present the accumulator at 2x draw scale | Produced incomplete output and triggered `DEVICE_HUNG`/TDR GPU resets during qualification | Deferred; 1x composition is the only supported prototype target | Scaled-layout contracts, source-row calculations, failure evidence, and fail-closed gates | Reconsider only after V3-04 is stable at 1x and a GPU capture identifies and removes the unsafe path |
| Run broad census, hashing, and observers continuously | Improved provenance knowledge but processed very large draw volumes and materially harmed prototype CPU cost | Discovery features default off; enable only a bounded observer for a named blocker | Capture tools, semantic classifiers, counters, and provenance reports | Enable temporarily when a V3 exit gate cannot be answered by existing evidence or focused tests |
| Split one capability into topology, counter, request, result, and qualification PRs | Kept individual diffs small but multiplied CI, clean-build, review, documentation, and integration overhead while delaying visible results | Use vertical capability PRs with their minimum instrumentation and tests included | Focused tests and narrowly scoped commits remain useful inside a larger PR | Split only across a genuine safety boundary or when a single capability cannot be reviewed independently |
| Fully qualify every small change with an AppData run | Repeated expensive builds and gameplay sessions often reconfirmed unchanged behavior | Batch runtime qualification at V3 batch exits or true runtime-only blockers | AppData launch procedure, capture scripts, reports, and crash bundles | Run early only when synthetic tests cannot establish safety or a runtime observation determines the next implementation step |

General lesson: instrumentation is valuable when it closes a decision. A V3
change should primarily create a compositor capability, integrate a required
producer, make the scene visible, or remove measured prototype cost. Evidence
collection is supporting work rather than a milestone by itself.

## North-star milestones

### Milestone 1 — Drivable hybrid prototype

At one fixed reference configuration, the player can drive through the open
world while the native renderer supplies the essential gameplay scene and
Xenos supplies unsupported presentation work.

Required native scene content, either in one proved base or exact overlays:

- sky or horizon clear/background;
- opaque terrain and road;
- opaque static world geometry; and
- the player vehicle.

Allowed Xenos work:

- UI and HUD;
- unsupported transparent effects;
- post-processing;
- traffic, crowds, and nonessential decoration; and
- any family that fails closed without corrupting the native scene.

Prototype acceptance gate:

- use 1x draw scale and the established 1280x720 logical reference path;
- use the installed AppData save and a repeatable festival-to-open-world route;
- the native view matches the Xenos camera, projection, and player position;
- the minimum native family set comes from one agreed frame and camera;
- missing, stale, or ambiguous families atomically yield to Xenos;
- driving does not expose repeated, stacked, frozen, or last-target output;
- the reference route sustains the 30 fps target without severe recurring
  frame-time stalls;
- no device removal, TDR, crash, guest-memory mutation, or save mutation;
- Xenos remains available as an immediate comparison and fallback; and
- paired screenshots and a frame-time report are attached to the milestone.

### Milestone 2 — Complete production hybrid

All normal gameplay and frontend scenes have native coverage, and qualified
native families can suppress equivalent Xenos visual work. Unsupported or
failed work still falls back independently.

### Milestone 3 — Native-only release candidate

All guest-visible rendering dependencies have native implementations or
proved native no-op replacements. A no-Xenos build passes the full scene,
stability, performance, and recovery matrix.

## Prototype critical path

The first four batches form one vertical slice. Avoid side work that does not
remove a listed exit-gate blocker.

### V3-01 — Scene-frame compositor contract

Build the structure that the previous accumulator path was missing.

- Define retained slots for a proved gameplay-scene base and later optional
  overlays.
- Attach exact guest frame, camera, projection, viewport, resolution, sample
  topology, and attachment identity to every candidate.
- Define a minimum-family coverage mask and deterministic composition order.
- Reject mixed-frame, mixed-camera, stale, duplicate, or ambiguous candidates.
- Keep targets private until the complete minimum set passes the agreement
  gate.
- Preserve Xenos output and all guest-visible side effects.
- Add bounded compositor state reporting without broad per-draw census.

Exit gate:

- tests prove retention, replacement, invalidation, ordering, agreement, and
  atomic fallback;
- a synthetic complete frame composes deterministically;
- an incomplete frame never publishes; and
- no application gameplay run is required unless a contract cannot be proved
  synthetically.

### V3-02 — Opaque open-world producers

Feed the compositor with the largest visible part of the scene.

- Prefer the natural producer boundary when one qualified producer already
  contains terrain, road, buildings, large static props, and usable depth.
- Split that base only if a missing or independently invalidated family proves
  the split is necessary.
- Bind producer output to the exact scene-frame contract from V3-01.
- Prefer already proved render paths; add instrumentation only for a specific
  unresolved producer boundary.
- Do not publish partial world targets.

Exit gate:

- a private capture contains camera-correct terrain, road, and representative
  static geometry together;
- target ownership survives ordinary streaming and attachment reuse;
- incomplete coverage yields cleanly; and
- focused tests plus one batched AppData capture qualify the producer set.

### V3-03 — Background and player vehicle

Complete the minimum gameplay family set.

- Retain the qualified sky, horizon, or background-clear family.
- Route player-vehicle opaque color and required depth into its own slot.
- Use exact camera and player ownership; do not admit hash-only correlations.
- Compose vehicle and world depth deterministically.
- Keep traffic, glass, particles, shadows, and reflections optional for this
  milestone.

Exit gate:

- a private composed frame contains background, world, static geometry, and
  the correctly positioned player vehicle;
- the view matches a paired Xenos capture at the same frame and camera;
- missing vehicle or background work causes fallback instead of a partial
  native frame; and
- focused tests plus one batched AppData capture pass.

### V3-04 — Hybrid publication and prototype performance

Make the minimum scene visible, drivable, and affordable.

- Publish only complete, camera-agreed scene frames.
- Compose Xenos UI and unsupported effects over or with the native scene.
- Provide immediate Xenos, hybrid, and comparison selections.
- Disable discovery census, broad hashing, verbose observers, readback, and
  captures by default.
- Cache semantic classification and avoid replaying rejected work.
- Bound retained targets, command lists, uploads, and deferred destruction.
- Measure CPU time, GPU time, memory, frame pacing, and fallback frequency.
- Optimize the reference route before adding resolution scaling.

Exit gate:

- all Milestone 1 acceptance criteria pass in one complete qualification run;
- paired Xenos and hybrid screenshots demonstrate camera and scene agreement;
- logs contain no device removal, GPU validation error, native publication
  rejection loop, or unbounded resource growth; and
- the prototype is merged behind an explicit nondefault selector.

## Completion backlog after the prototype

These batches remain mandatory. Their order prioritizes gameplay coverage and
performance before removing the fallback.

### V3-05 — Gameplay-scene breadth

- traffic and non-player vehicles;
- vegetation, crowds, repeated instances, and LOD/culling behavior;
- transparent world and vehicle materials;
- particles, weather, lens effects, and gameplay overlays;
- rewind, streaming transitions, races, and representative open-world routes;
- semantic batching that replaces diagnostic draw-by-draw replay where safe.

Exit gate: the normal gameplay matrix has camera-correct native coverage with
family-local fallback and no material visual omissions.

### V3-06 — Lighting, shadows, reflections, and presentation

- complete shadow ownership, cascades, filtering, and dynamic casters;
- local, global, vehicle, and environment lighting;
- planar, cubemap, vehicle, and road reflections;
- exposure, tonemapping, anti-aliasing, bloom, depth of field, motion blur,
  color grading, and final presentation;
- native UI composition boundaries where required.

Exit gate: paired captures pass the agreed visual comparison thresholds across
day, night, weather, tunnel, race, and festival scenes.

### V3-07 — Frontend and special modes

- boot, loading, menus, garage, paint, upgrade, photo mode, replay, and FMV;
- livery and user-generated texture paths;
- resize, fullscreen, focus, suspend, resume, and device-recovery behavior;
- frontend-specific render targets, queries, resolves, and synchronization.

Exit gate: the complete scene matrix works without relying on unclassified
Xenos presentation behavior.

### V3-08 — Production hybrid and low-requirement profiles

- close the renderer census by family rather than by isolated draw;
- enable measured, independently reversible Xenos suppression;
- harden streaming, resource budgets, deferred GPU lifetime, and recovery;
- add independent scene resolution, geometry, world-density, shadow,
  reflection, material, and effect controls;
- qualify representative low-end CPU and GPU configurations;
- verify that each profile materially reduces cost rather than only changing
  launcher state.

Exit gate: native mode is the qualified default, materially reduces Xenos
work, and has stable rollback at family granularity.

### V3-09 — Xenos retirement

- enumerate and close every remaining Xenos dependency;
- preserve required guest side effects without executing Xenos visual work;
- produce and qualify a no-Xenos build;
- run the full gameplay, frontend, visual, performance, soak, and recovery
  matrix;
- document release rollback and retained diagnostic builds.

Exit gate: the native-only release candidate passes the full matrix and Xenos
is no longer required for supported execution.

## Work that is explicitly deferred

Until Milestone 1 passes, do not prioritize:

- scaled or supersampled accumulator presentation;
- 2x draw-scale qualification;
- full shadows, reflections, transparency, or post-processing;
- traffic, crowds, vegetation quality, or special modes;
- broad census expansion without a named compositor blocker;
- pass suppression or Xenos retirement;
- low-requirement profile UI; or
- visual polish on isolated targets that cannot contribute to a complete
  scene frame.

Deferred means later, not removed from the final scope.

## Development and validation cadence

### Every commit

- Run only affected focused tests.
- Keep commits independently reviewable and use Conventional Commits.
- Record new evidence only when it changes an implementation decision.

### Every pull request

- Prefer one vertical capability over one observer, counter, or field.
- Include supporting instrumentation in the capability PR.
- Run the relevant automated suite and an incremental Release build.
- Confirm Xenos fallback and guest-memory invariants synthetically when
  possible.

### End of a V3 batch

- Rebase or merge the latest `dev` before final qualification.
- Run a clean ShiftGlue build and the full automated suite once.
- Run a clean Release build once.
- Perform one AppData-backed run only when the batch has a runtime exit gate.
- Review logs, crash artifacts, GPU messages, and bounded resource counters.
- Merge only after the batch exit gate is satisfied.

### Visual milestones

- Use the same save, reference route, resolution, draw scale, and camera points.
- Capture paired Xenos and native/hybrid frames.
- Retain frame-time summaries and fallback counts.
- Do not repeat a full qualification run for documentation-only changes.

## Decision rules

- No evidence-only PR unless it resolves a binary blocker for the active batch.
- Stop tracing once the minimum safe implementation boundary is known.
- If one targeted runtime capture disproves an architectural hypothesis, record
  it and leave that path rather than adding increasingly broad observers.
- Never publish a last-writer or best-effort partial scene.
- Never mix targets from different frames, cameras, projections, or unresolved
  attachment lifetimes.
- Optimize the coherent 1x prototype before revisiting scaling.
- Measure performance with discovery and capture features disabled.
- Treat fallback frequency as a product metric, not just a debug counter.
- Keep renderer selection, native publication, and Xenos suppression as
  separate gates.
- Unknown or failed work always yields to Xenos until V3-09 is complete.

## Pull-request sizing

The preferred unit is a vertical capability with tests and the minimum
instrumentation required to prove it. A batch may use more than one PR when
risk or reviewability requires it, but avoid splitting a single capability
into a sequence of topology, counter, request, and result PRs.

For the prototype, the expected shape is three to five substantial PRs:

1. compositor contract and retained scene-frame state;
2. opaque world and static-world producers;
3. background and player-vehicle producers;
4. hybrid publication and fallback; and
5. an optional focused performance/hardening PR if V3-04 cannot contain it.

## Status reporting

Keep this section short. Update it only when a V3 batch changes state.

| Batch | State | Visible result | Primary blocker |
| --- | --- | --- | --- |
| V3-01 | complete | deterministic private complete-frame plan | none |
| V3-02 | complete | coherent camera-correct opaque open world | none |
| V3-03 | complete | camera-agreed background and player vehicle | none |
| V3-04 | in progress | drivable native gameplay base | prototype observer performance |
| V3-05 | pending | broad gameplay coverage | prototype exit gate |
| V3-06 | pending | complete lighting and presentation | gameplay-scene breadth |
| V3-07 | pending | frontend and special modes | presentation coverage |
| V3-08 | pending | production hybrid and profiles | complete native coverage |
| V3-09 | pending | native-only release candidate | all Xenos dependencies |

V3-01 is complete synthetically: the host contract rejects stale, mixed,
duplicate, ambiguous, or invalidated candidates and only emits a complete
minimum plan. Optional family slots remain available, but the minimum is now
the proved precomposed gameplay base rather than four artificial subdivisions.
ShiftGlue reports private resource identities and generations and never exposes
them to presentation. V3-02 has exact 1x producers: unowned main-view context
`824365B0` and procedural context `82417BC0` feed one retained accumulator. A
17-frame AppData run recorded 171 main-view and 354 procedural requests, reused
the target 508 times, completed every frame without failure, reported coverage
`02` as a complete private plan, and kept Xenos authoritative. A later paired
selector run proved that the apparent private preview was Xenos fallback:
enabling the committed native accumulator repeated one vehicle-bearing source
tile vertically instead of presenting the world. V3-02 therefore remains open
on correct full-frame tile assembly, and publication remains disabled. A
follow-up main-view-only run (`20260901T213848Z-p44396`) removed the repeated
vehicle but exposed only one road-texture block with the rest of the frame
black. It recorded 234 main-view requests, zero procedural requests, and 24
structurally committed frames. This disproves both producer subsets as a
complete base and narrows the blocker to the missing pass boundary or private
tile mapping rather than compositor retention. The old track and SimpleModel
leads remain rejected. A rejection census (`20260901T214651Z-p1628`) then
proved that every missing selected draw was excluded only by the snapshot-era
texture-count or texture-layout gate. The prepared-replay path now ignores
those two observation-only restrictions while preserving the remaining safety
checks. The bounded quota was raised from 64 to 128 after the first corrected
run exposed 438 otherwise-valid yields. The follow-up
`20260901T215424Z-p5596` run replayed all 1,334 main-view and 414 procedural
candidates (1,748/1,748), with zero mechanical rejections, quota yields,
backend failures, or failed frames across 22 complete private frames. Xenos
remained authoritative; the next gate is visual proof of the complete private
assembly before publication is restored.
The first temporary publication capture (`20260901T215814Z-p46092`) was
inconclusive because the title transition had not finished. A paired Xenos run
established the repeatable route: `Return` at Press Start, `Space` at Single
Player, then about 45 seconds to the festival. The corrected direct-native
probe `20260901T220852Z-p45552` replayed all 1,226 main-view and 416 procedural
candidates across 21 complete frames, with zero rejection, quota yield,
backend failure, or failed frame. It displayed three stacked copies of the
same upside-down 256-line vehicle/ground tile. Inspection then proved that the
old planner had mistaken the conservative tiled guest-memory modification
range for linear destination rows. Routing the retained target through the
normal ShiftGlue resolve fixed orientation, but `20260901T222510Z-p43036`
still repeated one temporal source region across all three resolves. The
minimum working lifecycle now reseeds the private target after each exact
resolve and lets the existing resolve path perform every copy. The bounded
AppData qualification `20260901T223221Z-p38192` recorded all 1,377 main-view
and 478 procedural requests across 23 complete frames with no failed frame.
Its direct-native probe displayed one coherent, correctly oriented 1280x720
festival scene containing terrain, road, representative static structures,
background, crowd, and the player vehicle. V3-02 is complete. V3-03 then added
an atomic same-frame producer-set gate: both the exact main-view and procedural
families must record successfully before the retained resolve can replace
Xenos. Either family missing keeps the normal Xenos resolve. A paired Xenos
capture (`20260901T223833Z-p42460`) from the same save matched the native
camera, Audi placement, road, festival towers, garage sign, and horizon. Xenos
supplied the expected HUD and brighter final presentation. V3-03 is complete;
V3-04 is active on hybrid UI composition and prototype performance. Both runs
were closed normally and the installed renderer remains Xenos at 2x.
The first V3-04 `hybrid_prototype` probe
(`20260901T224144Z-p29472`) reproduced the coherent native base but did not
retain the HUD. Its guest-output callback never claimed a retained frame: the
qualified resolve had already replaced the guest framebuffer, so the later
hybrid compositor had no independent Xenos UI source. The existing
post-presentation pixel-agreement compositor is therefore not the publication
boundary. A second probe (`20260901T225323Z-p43460`) tested composition before
the qualified resolve, while both inputs were linear render targets. It stayed
stable and recorded all 1,387 requests across 17 complete observed frames, but
still produced the native world without HUD: the Xenos render target at that
point does not yet contain the UI-bearing presentation. That experiment and
its extra resolve resources were removed. V3-04 now requires two independently
preserved final sources at presentation: the qualified native resolve and the
complete Xenos guest output. Composition failure must continue to present the
normal Xenos output. A third bounded probe
(`20260901T232058Z-p31000`) kept the qualified pre-resolve render target alive
until presentation. The callback claimed it, but direct sampling produced an
upside-down, cropped vehicle target rather than the composed scene. That raw
target lifetime change was removed. The native presentation input must be the
post-resolve product; retaining the source render target is not equivalent to
retaining the qualified resolve.
The V2 shadow-depth publication is no longer auto-enabled by the V3 prototype:
two runs reproduced access violation `pscrash-v1-2d1ed55709da7bc08fc2`
immediately after its first 80-draw atlas publication. Its explicit diagnostic
controls remain available. With that V2 auto-publication removed, the same
AppData scene remained stable for 30 seconds past the prior crash point and
exited normally.
The missing-menu regression in the minimal prototype graph was isolated from
retained publication. `diagnostic_retained_pass` and Xenos with census enabled
kept the complete menu, while `hybrid_prototype` without census lost it. The
minimal graph had installed a second shortened copy observer; routing every
mode through the existing safe `ObserveCopy` ingress removed that duplicate
path. Qualification `20260902T000303Z-p46716` then preserved `SINGLE PLAYER`,
`MULTIPLAYER`, `A SELECT`, and `B BACK`, loaded the AppData festival save, and
exited normally. It recorded all 1,294 replay requests across 17 complete
frames with no failed frame, but correctly remained on Xenos because no
retained presentation frame was available.
A subsequent V3-04 probe retained the native post-resolve product without
depending on texture-fetch slot 0: ShiftGlue now derives the texture identity
from the exact resolve destination and restores the ordinary guest resolve
before presentation. Qualification `20260902T001347Z-p47776` compiled and ran
normally and again preserved the complete menu and gameplay fallback, but the
guest-output callback still reported `retained_pass_unavailable`. The remaining
blocker is therefore before snapshot publication, at the retained resolve
selector or its source handoff, rather than producer replay, menu composition,
or fetch-slot identity. V3-04 remains in progress. The installed renderer was
restored to Xenos at 2x after both probes.

Qualification `20260902T002000Z-p46056` made the selector observable: 72
retained-family resolves qualified while all 1,062 replay requests recorded
across 15 complete frames, yet no retained frame reached presentation. This
excluded the producer set and selector predicate. The ShiftGlue resolve
snapshot also emitted neither copy nor texture failure, which exposed a
lifetime bug: every unrelated `BeginIsolatedReplayTarget` cleared the retained
source frame identity even though the source resource remained valid. The
reset is now scoped to activation of a new accumulator-source target. A second
normal-exit run, `20260902T003029Z-p43308`, recorded all 1,256 requests across
17 complete frames and 81 qualified resolves, but still reported
`retained_pass_unavailable`; a narrowly gated ShiftGlue warning now records
the required, preview, resolve, and source frame identities for the next probe.
Both runs preserved the Xenos fallback and save, and the installed renderer is
restored to Xenos at 2x. V3-04 remains in progress at the final snapshot
publication gate.

The remaining publication invalidation was then removed at its owner:
`EndIsolatedReplayTarget` no longer clears the exact-frame resolve snapshot
when an unrelated private replay target ends. Shutdown and failed snapshot
creation still invalidate it, and the presentation gate still requires an
exact frame-sequence match. The ShiftGlue build, 15 focused Python checks, and
the resolve-accumulator, scene-compositor, and render-target bridge checks
pass. AppData runs `20260902T004407Z-p34340` and
`20260902T004746Z-p42660` exited normally and preserved the save, but their
bounded traces ended before the gameplay workset activated (zero replay
requests), so they are not publication qualification evidence. The installed
renderer is restored to Xenos at 2x; V3-04 remains in progress pending one
workset-bearing qualification of the retained snapshot.

Workset-bearing qualification `20260902T005701Z-p47236` then isolated the
presentation handoff: all 1,149 producer requests recorded across 14 complete
frames, 72 resolves qualified, and the retained snapshot survived with frame
identity 6899. The host callback ran after the guest swap increment at frame
6900, so requesting the current in-progress frame rejected the valid completed
snapshot as stale and preserved Xenos. ShiftGlue presentation now requests
`observation_frame_sequence_ - 1`; the cache continues to require an exact
match to that completed frame. The build and 16 focused Python checks pass.
Post-fix run `20260902T010413Z-p22444` exited normally and preserved the save,
but its trace stopped at the idle festival scene before a producer workset
activated, so it is not publication proof. The installed renderer is restored
to Xenos at 2x. V3-04 remains in progress pending one workset-bearing post-fix
qualification and Xenos UI composition.

Post-fix AppData run `20260902T011212Z-p44700` exercised the complete title
flow, selected `SINGLE PLAYER`, loaded the festival save, and exited normally.
Across 48 checkpoints it produced zero replay requests, zero qualified
retained-family resolves, and zero completed workset frames, so it neither
validates nor refutes the completed-frame handoff. The strict producer selector
and exact retained-frame match remain unchanged. The save was preserved and
the installed renderer was restored to Xenos at 2x. V3-04 still requires a
workset-bearing post-fix qualification before publication can be accepted.

The presentation callback now identifies the same previous completed guest
frame that ShiftGlue requests from the retained snapshot; previously its
context still named the incremented swap frame and the host rejected a valid
snapshot before drawing it. Seventeen focused checks and the Release build
pass. AppData run `20260902T012434Z-p36656` confirmed the corrected telemetry
pair through callback 8700/frame 8699, but its 29 checkpoints again contained
zero replay requests, qualified resolves, or completed workset frames and no
native output was claimed. Transient title-flow frames therefore remained
Xenos and are not publication evidence. The run exited normally, preserved the
save, and the installed renderer was restored to Xenos at 2x. V3-04 remains in
progress pending a workset-bearing qualification.

Workset-bearing runs `20260902T013503Z-p39372` and
`20260902T013902Z-p18368` first appeared to stop at producer activation while
the process remained CPU-active at roughly 1.55 GiB. Focused replay tracing in
`20260902T014447Z-p33660` and `20260902T014845Z-p39116` then proved that every
selected replay completed; the latter recorded all 1,144 requests across 15
complete frames with no failure. The apparent hang was extreme observer and
replay latency, not a blocked replay callback. The temporary trace was removed
after closing that decision.

A narrower ShiftGlue binding-restore shortcut did not improve runtime and was
removed. Run `20260902T015845Z-p47132` still recorded all 1,184 requests across
16 complete frames, but its final summary exposed 275,473 prepared-draw
observations for those requests. An aggressive accumulator-only early return
made producer frames visibly faster but caused guest access violation
`pscrash-v1-1a4926e5a2bc9d1a37e6` in `20260902T020630Z-p1616`; it was rejected
and reverted. The safer follow-up only bypasses resolved-dependency census when
the continuous workset has no explicit static- or track-world request.

Qualification `20260902T021113Z-p30472` selected `SINGLE PLAYER`, reached the
AppData gameplay scene, published a retained hybrid frame, and exited normally.
It recorded all 1,143 requests across 14 complete frames with no failed frame,
but processed 644,623 prepared observations and the published image remained
dark and fragmented without usable Xenos UI composition. The save remained
51,208 bytes and the installed renderer was restored to Xenos at 2x. This is
publication-path proof, not V3-04 completion: broad prototype observers must
still be disabled and the final native/Xenos composition corrected.

A follow-up attempt to omit the lineage and semantic aggregation while keeping
only accumulator classification was rejected. Run
`20260902T021925Z-p45768` emitted no dependency-census or command-lineage
entries, but selected zero producer requests and stopped advancing with the
process still CPU-active. It exited normally, the change was reverted, the
save remained 51,208 bytes, and Xenos 2x was restored. Producer classification
therefore still depends on state maintained by those paths; the next
optimization must cache or narrow that state without bypassing its updates.

The fragmented hybrid image was a ShiftGlue descriptor-binding bug, not a
missing UI source. The hybrid compute root signature declared native `t0` and
Xenos `t1` as one two-descriptor table, but
`RequestOneUseSingleViewDescriptors` explicitly returns independently
allocated bindless descriptors. Binding only the first descriptor therefore
made `t1` sample an unrelated slot. ShiftGlue now exposes separate one-SRV
root tables for `t0` and `t1`, using the same existing allocator. The 18
focused checks and Release build pass. AppData run
`20260902T022906Z-p43980` then rendered the complete title screen and complete
main menu in `hybrid_prototype`, including `SINGLE PLAYER`, `MULTIPLAYER`,
`A SELECT`, and `B BACK`. Those frames remained Xenos fallback, so the change
fixes the descriptor contract but does not yet qualify retained hybrid
composition. Gameplay activation stalled on a black transition while
CPU-active at about 1.41 GiB: the bounded trace reached 148 resolve-target
observations, 76 dependency observations, and nine three-chunk accumulator
sequences, but no selected producer replay or retained publication before
normal exit. The save remained 51,208 bytes and Xenos 2x was restored.

The V3 prototype no longer implicitly enables the rejected V2 static- and
track-world families. Their explicit diagnostic controls remain available.
AppData run `20260902T023705Z-p40024` reached the visible festival scene and
exited normally. It recorded all 1,302 requests across 17 complete frames,
including 988 exact main-view and 314 procedural requests, with 81 qualified
resolves and no dependency-census events. Prepared observations fell from
644,623 to 280,995. The run ended before a retained output frame was claimed,
so it is performance evidence rather than composition proof.

A still narrower command-lineage ledger early return was rejected. Run
`20260902T024411Z-p27360` reached the festival but produced 634,442 prepared
observations, zero producer candidates, zero requests, and no retained output.
The shortcut was reverted because exact producer classification still depends
on state maintained by the full lineage path. The run exited normally, the
save remained 51,208 bytes, and Xenos 2x was restored. V3-04 remains in
progress on both observer cost and a retained-output composition
qualification.

A ShiftGlue pre-observation gate based only on the active indirect-buffer
context was also rejected. Run `20260902T025639Z-p40904` reached gameplay
loading, but through frame 4,800 it admitted zero prepared observations and
therefore selected zero producer requests. The gate was removed: the producer
identity is not available early enough in that callback context to replace the
existing classification state. The run exited normally, the save remained
51,208 bytes, and Xenos 2x was restored.
