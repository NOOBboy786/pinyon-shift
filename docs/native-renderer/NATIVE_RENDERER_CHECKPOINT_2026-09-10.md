# Native renderer checkpoint — 2026-09-10 UTC

This is a source checkpoint for remote `dev`, not a new preview release or a
claim that B is complete. Continue with the active B1–B4 goal in the
[resource migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md).

**Latest handoff:** [Reflection mip producer and cached submissions](#latest-handoff-reflection-mip-producer-and-cached-submissions).
Earlier sections preserve the sequence of experiments; their resume orders and
source pins are historical. Current SDK pin: `202247a233bad7d1cbd93d5b541521f9747132eb`.

## Retained behavior and current source

- A1–A6 are complete for the bounded native depth-clear chain at symmetric 1x.
  See [A6 retention](A6_OWNED_DEPTH_RETENTION.md) and its
  [resource contract](OWNED_DEPTH_CHAIN_CONTRACT.md).
- Scaled rendering retains compatibility clears. The unchanged 2x owned-clear
  candidate failed North Carson tail retention; do not repeat it unchanged.
- Discovery now preserves shader-family coverage after the detailed key table
  fills, accounts for changing identities within a pass, and supports bounded
  long-session recording. Shader production/packaging and preparation checks
  accumulated since the previous remote checkpoint are included.
- B's tile-clear, buffer-recycling and smallest-containing geometry-window
  candidates are recorded in source but **disabled by default**. No B
  optimization has earned retention. The ordered geometry map also changes
  exact-mode lookup/eviction traversal; disabling containment alone does not
  make this source byte-for-byte equivalent to the retained DLL.
- [B execution](B_EPIC_EXECUTION.md) contains measurements, rejected experiments,
  scene coverage and limitations. [Dependency ranking](P2_DEPENDENCY_RANKING.md)
  preserves earlier qualification and attribution.

## Exact local runtime identities

Direct file hashes are authoritative; the build manifest has reported a stale
EXE identity. Both local runtime DLL paths are restored to the retained build.

| Artifact | SHA256 | Status |
| --- | --- | --- |
| Retained renderer DLL | `27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50` | Staged at both runtime paths; qualified A6 scope |
| Current EXE | `3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3` | Discovery accounting fix included |
| Stable-containment source build | `15FB392A7D16828371443A38BDBFBBD0D4C0E90DE12ADED79D51EA38340201DF` | Release build passed; unretained |
| Temporary containment capture DLL | `DAD406A16C8FE1A4524444C6111638A91E3E676B2EABBB4FCD37AADEF5C189CD` | Diagnostic only; source instrumentation removed |

The source checkpoint and the retained runtime are deliberately distinct
identities. Rebuilding this checkpoint produces the experimental source state;
it does not reproduce the archived retained DLL merely because flags are off.
Local captures, game data, saves and DLLs are not published in Git.
The source dependency is pinned to ShiftGlue commit `261dd6a4d8e27dad0cf01f1e288f602bc03e303c`.
Unrelated local kernel profiling and materialized libmspack links are excluded.

## Latest B2 evidence

The smallest-containing policy keeps a held GPU resource associated with its CPU
snapshot when a larger overlapping owner is inserted. All snapshot/bounds
lookups share that policy; watches/imports cover the full selected owner.
Budget and completion-fence protections remain. The production-body suite
passes in exact and contained modes, including partial writes, CPU/GPU import
changes, snapshot upgrades, bounds invalidation, reuse, destruction and fences.
A negative control selecting the historical largest owner fails the held-owner
snapshot assertion; it does not modify production source.

Two 1x RenderDoc frames check 13 nonzero contained owners (1,900,544 bytes) each
against fingerprints recorded at their actual CPU imports, plus 16 representative
index/vertex consumers per frame. Each frame also contains one actual 65,536-byte
copy whose upload source and GPU destination compare byte-for-byte. All checked
values match; there are no unverified contained versions. These are bounded
checks: the 13 versions do not change between captures, so this does not prove
live streamed/mutating-content coverage. The route's images show intact car,
road, crowd and HUD during short local motion.

The 2x instrumented candidate run `20260910T034013Z-p16692` fails during startup:
guest read of `0x00000004`, before its first capture trigger. No usable GPU frame
or completed route exists. The feature-off instrumented control
`20260910T035134Z-p24740` also times out at 180 seconds without captures or route
completion, but logs no corresponding access violation. These different failures
do not establish a shared cause or exonerate containment. The capture wrapper
now rejects a missing child normal-exit result even if RenderDoc itself exits 0.
Both runs are preserved; neither counts as performance or correctness evidence.

The ordinary, uninstrumented 2x candidate probe completed previously. One probe
and contained-hit counts alone do not demonstrate saved imports or faster frames.

## Resume order

1. Isolate the 2x capture/startup failures, then qualify actual contained GPU
   mutation/lifetime behavior and sustained motion. Keep failed runs in evidence.
2. Run new, preselected matched containment comparisons at 1x/2x, including
   qualified-DLL controls to account for the map change. Require reduced work,
   acceptable memory and frame-time tails before retention.
3. Continue B1's required-family/resource-chain inventory and implementation,
   B3's actual pre-packet guest producer bypass, and B4's measured visual profile
   and NPC/UI timing. None is complete; rejecting an experiment closes only it.

The last observed balance is 1,076 CR; North Carson travel costs 10,000 CR.
Use free routes until normal play replenishes credits or a free driving approach
is qualified. Follow `AGENTS.md` for the installed AppData save. Never manipulate
saves to run a test. C-epic renderer retirement and new release publication remain
outside this checkpoint.

## Checkpoint validation

The current Release candidate build and the geometry, ownership-lifetime,
texture-watch, shader-family accounting and shared-range checks pass. All 599
tooling tests, the repository boundary check and tracked Markdown link check
pass. The held-owner negative control fails at the intended snapshot assertion.
Detailed test logs and capture audits remain under `.local/native-renderer/b2/`.
The stale release-contract expectation of 256 timing slots now matches the
existing 512-slot implementation. No runtime behavior changed for this fix.


## Follow-up checkpoint: 2x evidence and B3 producer anchor

This updates the earlier resume order above. The original two failed capture
runs remain preserved and their causes are unproven. A revised diagnostic
fixture now provides usable 2x captures: it fingerprints cached CPU import
bytes instead of scanning upload memory. Production source is unchanged, and
the retained `27B486...` DLL is verified at both runtime paths. No game,
compiler or replay remains active at this checkpoint.

- The diagnostic `0D7577CB79E5B683EE9F7D266FB56EA8E31D49A53D302AACBFD3D3EF147437E3`
  session `20260910T041226Z-p10576` completes normally. Frames 2674/3032 validate
  18/19 owners, 24/25 representative IB/VS consumers, and one actual 65,536-byte
  copy each. All checked values match; zero unverified contained versions.
  The 18 common owners are unchanged, so mutation/streaming remains unqualified.
- The longer 1x containment comparison stops at B2 because the car moves
  20.03 m before planned acceleration. A2 and 2x do not run. No ABBA performance
  verdict or optimization is retained. Qualify a more stable stationary workload
  before another preselected comparison; do not repeat unchanged for better data.
- B3 now has a static CPU producer anchor: `sub_8240E130` emits the known clear
  shader from `0x820C5FD0`; copy callsite `0x8240E4A8`, direct caller callsite
  `0x824019D0`. Live cost, full side-effect tracing and an actual pre-packet
  bypass remain required. Device dirty state, clipping/scissors and buffer
  refill/flush behavior prevent simply skipping this function.

[B execution](B_EPIC_EXECUTION.md) records exact capture hashes, all control/run
identities, the incomplete-comparison report and reproducible local checks.
The cached-fixture production-body suite, capture audits, cross-frame summary
and static producer-anchor checks pass. These findings change qualification
coverage, not the retained renderer or default flags. B1-B4 stay open.

Resume with live producer attribution and remaining mutation/streaming coverage,
then matched 1x/2x retention including qualified-DLL controls. Continue the full
B1 scene/family inventory and B4 visual/timing work; the prior scope is intact.
The source checkpoint remains `6605268` with SDK `261dd6a`; this follow-up adds
documentation only. No new preview release or tag is made.


## Follow-up: producer timing and improved route tooling

The default-off `pinyon_shift_fh1_clear_producer_trace` is implemented and its
production-body tests pass. Diagnostic EXE `B3CF0B...` measures all clear
invocations together at about 0.03-0.045 ms per local gameplay frame at the
median. This is a small measured CPU opportunity in that scene; it does not
measure downstream GPU decode or implement B3's required pre-packet bypass.
[B execution](B_EPIC_EXECUTION.md) records phase tails, exact identities and
the 2x wrapper's recovered-session/unrecorded-exit-code limitation. The trace
source is present, but qualified EXE `372161...` remains staged.

The 1x handbrake C-A-B-B-A-C comparison completes all six runs. It holds the
player pose fixed but has differing passing traffic, mixed frame timings and
higher candidate import/allocation counts. **No retention; no 2x containment
performance verdict.** The free-road 2x block is deferred after workload and
work-reduction review. The failed earlier left-trigger hold is preserved: it
engages reverse from rest, so use the handbrake for stationary work.

A new retained-build Recaro Rush probe completes with an identical stationary
pose at 68/103 seconds, valid race HUD, 32 km/h motion and no nearby traffic in
the sampled race images. It is a better candidate workload for repeatability
checks, not proof of a full race or a new benchmark result. Next, establish
representative workload/cost and live mutation/streaming coverage before more
retention comparisons; do not repeat the rejected free-road block unchanged.
B1's full scene/family inventory, B3 bypass and B4 profile/timing remain open.

Current trace source snapshots/hashes are in
`.local/native-renderer/b3/producer-trace-source-manifest.json`. The trace build
used the unchanged qualified runtime DLL `955BDC...`; unrelated local kernel
profiling is preserved. SDK renderer source and candidate default flags do not
change in this follow-up. Retained DLL `27B486...` is restored at both runtime
paths. No game, build or replay remains running.


Before broad new comparisons, investigate the separate CRT configuration lead
recorded at the end of [B execution](B_EPIC_EXECUTION.md): the pre-existing
setjmp/longjmp addresses are scoped inside a hook table, so the root-only SDK
parser ignores them. No fix or renderer-crash causality is claimed. A corrected
scope needs a non-local-jump contract/regression and a newly qualified EXE;
do not merge that change silently into renderer measurements.


## Follow-up: CRT configuration correction and visual coverage gap

The CRT addresses are corrected to TOML root scope. Release code generation
now emits the existing semantic helpers at nine setjmp and eight longjmp sites.
The parsed-config regression and optimized helper/state-restoration check pass.
Replacement is at callers; retaining raw CRT definitions in generated output
does not mean the configuration is ignored. See [B execution](B_EPIC_EXECUTION.md)
for the checked contract and uncovered cases.

Corrected EXE `C24D88DCF4C3F6564BE40A4B63046BACBBFB1E0BD7329983617DEF8ED8CD4CC8`
passes bounded Recaro race entry/hold/motion smoke checks at 1x and 2x, with
retained renderer `27B486...`, runtime `955BDC...` and producer tracing off.
Both runs exit 0. Two invalid simulation-delta samples and one startup device
path error recur in the earlier retained control too; they remain explicit.
These runs do not qualify performance, full-race streaming or NPC/UI timing.

Image review adds a concrete B1 gap: corrupted car-selection thumbnails at
`event-step-1`, also visible in the earlier retained control. Race images pass
their bounded checks; menu correctness remains open. Attribute this thumbnail
resource chain instead of treating race HUD checks as whole-route visual proof.

Candidate, logs, images, source/caller audits and test results are preserved
under `.local/native-renderer/b3/crt-scope/`. Retained EXE `372161...` and both
retained renderer DLL paths are restored. No renderer defaults change, and no
new speedup, release or B-item completion is claimed. The full B1-B4 scope and
prior rejected evidence remain authoritative. Use an explicitly pinned EXE for
the next matched comparison; this correctness fix changes generated call sites.

Validation for this follow-up: Release build, generated CRT round-trip check,
all 600 tooling tests, tracked Markdown links and repository boundary check
(505 files, zero violations) pass. No game, compiler or replay remains active.

Source fix: `d36af3d`; SDK remains `261dd6a`. Unrelated local SDK kernel
profiling changes remain uncommitted and excluded from this checkpoint.


## Follow-up: B2 recurring imports and 64 KiB invalidation

SDK `75c3880` adds default-off `fh1_narrow_cpu_invalidation`. The candidate
reduces speculative invalidation around writes while preserving actual writes,
GPU-history guards and physical-heap protection. It builds and passes 1,500
range cases plus the CPU-source and texture-watch checks. Candidate DLL is
`BE32EE5D5923BA0D942C6AFA7D26E0E4C01BF8DE3BE61A124DD3D96DA38DE820`.

Two candidate-on 1x race runs reduce steady-hold imports from about 405/s in
the first off control to 183/182/s, with similar medians and lower observed
p99. **No retention:** the planned comparison stops on A2's missing early HUD;
C2 and 2x are unrun. A screenshot also falls inside the original acceleration
window. All records and limitations remain explicit in [B execution](B_EPIC_EXECUTION.md).

The separate CPU-page diagnostic found about 1.09 GB of fingerprint-equal
reimports in its exact-window run. It skips no work and is not an equality
admission rule. Fixtures and summaries remain in `b2/geometry-mutation-trace/`;
the clean candidate, comparison and unexecuted bookend-protocol draft are in
`b2/narrow-invalidation/` below `.local/native-renderer/`.

Next: verify the stronger prospective workload protocol and finish 1x/2x and
streaming qualification. Investigate the separate watch-valid CPU-snapshot
upgrade opportunity before adding data mirrors. Preserve early-HUD and menu
thumbnail defects, all failed evidence and the entire B1-B4 scope. Retained
EXE `372161...`, renderer `27B486...` at both paths and runtime `955BDC...`
remain staged. No game/compiler/replay remains active; unrelated SDK profiling
edits remain local. No new release or B-item completion is claimed.

Validation: all 600 tooling tests, tracked Markdown links and the repository
boundary check (506 files, zero violations) pass. Draft route grammar and
capture/window separation pass; its live workload checker is still pending.

## Later checkpoint: snapshot attribution and baseline HUD reproducer

The preceding goal turn made progress through the invalidation implementation
and its checkpoint. This continuation adds implementation evidence and a more
specific UI/cost reproducer; **B1-B4 remain open**.

- The CPU-only snapshot upgrade was implemented and passed production-cache
  mutation/lifetime checks and bounded 1x/2x gameplay. It avoids only about
  14.2/16.3 MB in runs observing 4.32/4.75 GB of imports. The earlier snapshot
  request count included new/dirty owners. Archive this low-value experiment;
  its production code, flag and checker extension are removed. Source, patches,
  executable checker, DLL `0CE37F...`, build and sessions remain in
  `.local/native-renderer/b2/cpu-snapshot/`.
- The revised HUD/capture-window checker is implemented and its negative test
  still rejects the original early-HUD gap even with all later bookends passing.
  Fresh 1x C1 passes; A1 again misses the early HUD, so the comparison stops
  before any B run. No revised 2x comparison or retention result exists.
- Dense half-second captures reproduce intermittent missing full HUD in both
  retained and candidate-off renderers, between passing neighboring images.
  Sessions are `20260910T070148Z-p24964` and `20260910T070529Z-p5916`.
  This predates the 64 KiB option. Whether title draws, output publication or
  capture behavior causes it remains unproven; host-visible behavior is not yet
  independently established.
- One requested 30-FPS-cap control, `20260910T070826Z-p27796`, has no sampled HUD
  gap, but the critical interval achieves only about 15 source FPS. It does not
  establish a high-FPS cause or timing fix. Every diagnostic exits 0. Preserve
  the two known invalid simulation deltas elsewhere in each session.

**Next:** attribute UI generation/drawing and the produced/published image during
the now-reproducible early-race interval. Source-CSV frame medians there are about
56..85 ms in dense and sparse capture runs, followed by substantial recovery.
The fresh control's race timer also differs by six seconds despite matching car
positions. Qualify actual workload/race stage and capture timing before further
retention comparisons; do not substitute late stationary success for this work
or for the other required scenes. Detailed measurements, identities and limits
are in [B execution](B_EPIC_EXECUTION.md). The 64 KiB candidate remains default-off.

Retained EXE SHA256 remains
`3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3`;
both staged renderer paths remain
`27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50`;
runtime remains `955BDC64AD9ABA356B162F1BD0B89E356ED45622F8F8C7D66CDB4213290F3500`.
All runs/builds/samplers are terminal. SDK stays at `75c3880`, retaining the
unrelated local profiling edits. No save manipulation, release, new retained
optimization or B-item completion is claimed.

## Latest checkpoint: early-race buffer churn and source-linked HUD gap

Diagnostic session `20260910T072547Z-p23496` exits 0 with 23 captures. Temporary
CPU/output instrumentation identifies about **22.47 ms/source frame** in geometry
allocation plus eviction during the 66..74-second early-race window, with about
45 buffers created and 45 owners evicted per frame. Import CPU cost is only
about 0.54 ms/frame there. Later stationary work largely stops the churn. These
instrumented observations prioritize work; they are not retained speedups.

Two missing-HUD images at scheduled 69.5/70.5 seconds map to source frames
4758/4770 through the actual captured output resource, with no pending-resource
conflict. Each lacks 148 calls from three shader pairs present in every passing
neighbor. This correlation does not prove they produce the HUD: two are world-lit
specializations in the catalog. Resource-chain/producer attribution and actual
host-visible behavior remain unresolved. Strict HUD gates stay.

Native GPU pass sampling still occurs every 60 source frames: only two early
and two late source frames have samples. Unsampled frames do not have zero GPU
cost. No additive GPU-cost or general performance claim follows from this run.
Exact diagnostic binary identities, measurement boundaries, validation and local
archive paths are in [B execution](B_EPIC_EXECUTION.md).

**Resume:** attribute the existing exact-size recycler under this early-race
churn. If it cannot reuse enough buffers, investigate fence-safe capacity reuse
with exact logical owner ranges and the same allocation budget. That design is
not implemented. Continue upstream HUD attribution, then strict matched 1x/2x
and changing/streamed-content qualification across the full B scene set. The
64 KiB invalidation candidate remains off; B1-B4 remain open and active.

The probe's production source edits and binaries are restored. Direct hashes
still verify EXE `372161...`, both renderer paths `27B486...` and both runtime
paths `955BDC...` (full values above). SDK remains `75c3880`, with unrelated
local kernel profiling edits preserved and excluded. No game, compiler or replay
is active. This checkpoint adds findings only; no new retained optimization,
preview release, save change or A6 2x expansion is made.

## Follow-up: matching-buffer recycler implemented and smoke-tested

SDK `acd222caa04adcc9e2ad8aabf99c09a9a8e12f0e` changes the default-off
recycler to prefer the oldest completed buffer with matching logical size and
allocation bytes anywhere in the bounded cache. It preserves the existing
imports, ownership reset, fences and 32 MiB budget. The production cache check
passes exact/contained ownership, partial writes, failed imports and lifetime
cases, including selection beyond a differently sized oldest victim.

The intermediate larger-capacity design nearly eliminates allocation cost but
increases rejected native-cache requests and late recurring imports sharply.
Its production code/field are removed and the experiment is archived. The
smaller exact-size search records about five creations and 53 recycles per
early-race frame, with no late-phase allocations, evictions or cache rejections
in its diagnostic. These separate instrumented observations do not establish
matched performance or retention. [B execution](B_EPIC_EXECUTION.md) records
every design, session, measurement boundary and failed HUD image.

Clean renderer `3A0B434AFA297315469B4A122AE72A3DE60DB2940B132057AD90B3FABACB21A1`
passes the strict six-HUD hold/motion smoke checks at 1x and 2x in sessions
`20260910T075538Z-p10180` and `20260910T075817Z-p1204`, both exit 0. Known menu
thumbnail corruption, two invalid simulation deltas and the startup device-path
error remain. There are zero GPU errors/timing drops. The preceding matching
diagnostic also passes all 19 sampled race HUD images, which does not prove the
baseline HUD defect fixed. Shader-group/HUD correlation needs actual resource-
chain attribution; two correlated pairs are named world-lit in the catalog.

**Resume:** obtain fresh actual GPU copy/consumer evidence for matching-victim
reuse, qualify race stage/capture timing and the HUD resource chain, then run
preselected matched 1x/2x comparisons with memory/tail checks. Preserve the full
ordinary/difficult-area scene set and changing/streamed-content requirements,
and continue B1 native chains, B3 pre-packet bypass and B4 visual/timing work.
No B item completes here. No new renderer setting is retained or enabled.

Clean and diagnostic archives are `.local/native-renderer/b2/matching-recycle/`
and `race-matching-profile/`; the rejected capacity variant is in
`race-capacity-profile/`. The main pin matches SDK `acd222c`. Direct hashes
verify restored EXE `372161...`, both renderer paths `27B486...` and both runtime
paths `955BDC...`. All processes are terminal; unrelated SDK profiling edits
and saves are preserved. The active goal's old EXE `882D92...` remains stale;
use the verified staged `372161...` identity above.

Validation: production geometry-cache checks, Release renderer builds, the 23
release-contract tests, tracked Markdown links and repository boundary check
(506 files) pass. Fresh GPU byte/consumer replay and matched performance gates
remain outstanding; no unavailable counter or passing smoke test substitutes
for them.

## Latest handoff: GPU reuse, HUD classification and race stage

The matching-victim recycler now has actual 2x GPU copy/consumer evidence.
Capture session `20260910T080726Z-p12416` exits 0 and passes all six strict race
HUD checks plus hold/motion. Replay checks 18 reused buffers (2,293,760 bytes),
including ten selected beyond the oldest victim. Every checked destination
changes to exactly match its nonzero upload source, and the first bound draw
consumer still sees those bytes. Sizes are 64, 128 and 320 KiB. This covers
these CPU-source lifetimes; fresh 1x, GPU-written sources, sustained streaming
and matched performance/memory/tails remain open.

The second RenderDoc capture contains no marked recycled copy. Its replay
report records that missing coverage explicitly; it is not another passing
proof. `qrenderdoc --script` returned 0 even when that script asserted, so
inspect the report result rather than relying on the process exit code.

Direct replay also classifies nine draws from the three shader pairs previously
correlated with HUD gaps. They write the map, standings, lap glyphs and
speedometer into the main R10G10B10A2 target. Catalog names such as world-lit
do not establish exclusive world use. This supports investigating the earlier
source frames' omitted HUD draws upstream; it does not identify their CPU
producer, explain the omission, establish host-visible behavior or fix timing.
Full hashes, event evidence and limits are in [B execution](B_EPIC_EXECUTION.md).

A retained-renderer single-confirmation route probe,
`20260910T082207Z-p23756`, also exits 0. All 13 captures are accounted for and
the original six HUD/pose/hold/motion checks pass unchanged. The Start Race
menu is visible at 52, 58 and 62 seconds; one final confirmation at 64 seconds
gives countdown 3 at 68 seconds and about 9.36 seconds on the race clock at
80 seconds. Matching car positions alone did not detect this stage difference
from earlier runs. All 597 existing M4 route samples have identical route and
transition states across menus and racing, so those fields cannot gate race
start. This one probe establishes a useful route adjustment, not repeatability
or a matched benchmark. Its unchanged later inputs occur at an earlier race
stage; preserve that limitation.

**Resume:** qualify a single-confirmation route on both control and candidate
using actual race-stage evidence. Include the expensive early-race phase and
capture-free measurement windows; retain every HUD failure. Then complete
fresh 1x GPU checks and preselected repeated 1x/2x cost, memory, tail and
changing/streamed-content qualification for the default-off recycler. Continue
the full B1 scene/resource inventory, B3 pre-packet bypass and B4 visual/timing
work. B1-B4 stay open; no optimization is newly retained.

Evidence is preserved locally in `.local/native-renderer/b2/matching-capture/`
and `race-stage-probe/`, including scripts, raw captures, source/binary hashes,
reports, images and the negative replay result. This documentation checkpoint
adds no production instrumentation or default change. The clean candidate
remains `3A0B434A...`; SDK `acd222c` is already pushed on `development`.
All nine staged runtime files match their retained backups: EXE `372161...`,
renderer `27B486...` and runtime `955BDC...` (full hashes above). No game,
compiler or replay is active. Unrelated SDK changes and saves are preserved.

Checkpoint validation: the single-confirmation workload check, all tracked
Markdown links, repository boundary check (506 files, zero violations) and
`git diff --check` pass. No rebuild is needed for this documentation-only
follow-up; the earlier Release and GPU results retain their exact identities.

## Latest handoff: input delivery, capture clocks and the recycler pair

The initial single-confirmation C-A comparison stops on failed event arrival:
candidate-off A1 stays in free roam, despite normal exit. Preserve it under
`.local/native-renderer/b2/matching-stage/`; no B/2x comparison followed.

Test-only instrumentation now records actual delivered input steps and capture
trigger/readback timing. `tools/check-fh1-render-test-clock.py` checks delivery
and derives bounded CSV/route clock alignment, including timestamp truncation.
It rejects missing evidence; output-trigger IDs are not captured-image source
IDs. Input scheduling and normal gameplay are unchanged. The Release build,
unit check and live timing/route checks pass.

New test EXE is
`EC2E5F097A3D513AE945B42B9E1EE01822A9E2DA7EEA08F5DD91B7E8F3243D30`;
it includes the earlier CRT configuration correction. Three 1x telemetry runs
use unchanged candidate renderer `3A0B434A...` and retained runtime `955BDC...`.
The first verifies clock alignment and all 22 input steps. The next two test
a changed approach: brake before signup, hold X for 500 ms, then confirm the
settled Start Race menu once. All 23 steps, 12 captures and seven race HUD,
grid-pose, hold and motion checks pass. Race-clock spread is at most 0.129 s.

In the single braked-entry off/on pair, early 78..86-second median falls from
46.015 to 25.222 ms and p99 from 92.396 to 30.797 ms. Last periodic allocation
counts fall from 23,707 to 4,006, with 29,284 recycles. **Still unretained:**
handbrake p99 rises 11.28%, opponents differ, and repeated 1x/2x memory/tail,
streaming and difficult-scene qualification remains open. All timing windows
exclude the actual capture-containing source-frame intervals. Detailed
identities, phase results and limitations are in [B execution](B_EPIC_EXECUTION.md).

**Resume:** use one pinned EXE and the braked-entry route for preselected
repeated control/off/on 1x/2x comparisons, including memory/process/GPU cost.
Require input delivery, actual signup/race stage, strict HUD/motion and clock
gates. Obtain fresh 1x GPU reuse proof and continue mutation/streaming and the
full B1 scene set. B3 pre-packet bypass and B4 visual/NPC/UI timing remain
required; no B item completes here. Keep recycling off pending retention.

All nine retained runtime files are restored and verified, including EXE
`372161...`, both renderer paths `27B486...` and runtime `955BDC...`. Test
archives are in `.local/native-renderer/b2/test-clock/`. No game/build/replay
remains active. Unrelated SDK edits and saves are preserved; SDK pin stays
`acd222c` and no renderer default changes.

Validation: Release build, 17 render-test tooling tests, three 1x telemetry
route/clock checks, the original missing-HUD negative control, legacy timing
evidence rejection, tracked Markdown links, repository boundary (508 files,
zero violations) and `git diff --check` pass. The staged runtime and unrelated
source backups are verified by direct SHA256 after the last run.

## Latest handoff: partial repeated comparison with memory sampling

Checkpoint requested after the first three runs of the preselected C-A-B-B-A-C
comparison at 1x. C uses the retained renderer; A/B use the same candidate with
recycling off/on. Run labels are separate from the B-epic checklist items.
The second B, second A and final C at 1x, and all six 2x runs, remain unexecuted.
This is an incomplete comparison, not a failed block or a retention decision.

C1 `20260910T090600Z-p26468`, A1 `20260910T090921Z-p8644` and B1
`20260910T091240Z-p10900` each exit 0, deliver all 23 inputs, account for all
12 captures and pass the seven HUD/pose/hold/motion checks. Reviewed race clocks
at 76/88/92 seconds differ by at most 0.079 seconds across these runs. Source
windows exclude capture-containing intervals using the measured clock bounds.
There is no concurrent compilation/replay. The known two invalid simulation
deltas and startup device-path error persist in each; GPU errors/timing drops
are zero. These checks do not close NPC/UI timing or intermittent HUD defects.

The first B run records early-race median/p95/p99 of 24.738/29.374/38.336 ms,
versus C1 51.391/112.070/119.821 and A1 68.509/88.323/91.360 ms. Later tails
are mixed, and the remaining repeats are essential. All phases, process CPU,
RAM, GPU-memory samples and measurement limits are recorded in
[B execution](B_EPIC_EXECUTION.md#repeated-recycler-comparison-with-process-and-gpu-memory-sampling).
There is no new default, retained optimization, B-item completion or release.

The local runner now samples Windows process CPU/RAM/faults and GPU Process
Memory counters equally in each condition. Each completed run has 71 GPU-memory
sample sets (355 valid counter records), with zero sampling errors. Samples
are tied to the game PID; dedicated/local and shared/nonlocal are overlapping
counter concepts, not additive memory totals. Whole-session asynchronous GPU
intervals are kept separate from source-frame and OS phase metrics.

Exact comparison identities remain test EXE `EC2E5F...`, runtime `955BDC...`,
retained renderer `27B486...` and clean candidate `3A0B434A...` (full hashes in
the preceding handoffs). SDK pin is `acd222c`; the previous main source commit
is `814d3eb`. Local evidence, plan, raw metrics and reviews are under
`.local/native-renderer/b2/matching-retention/`. Its route SHA256 is
`51e9be1cf28fc725b60873726f0cc5ac6b4e30f5915eb98165cb0681813de077`.
Local experiment scripts and runtime artifacts remain outside Git; this
checkpoint publishes their protocol, results and resume state.

**Resume:** run `run-matching-retention.ps1 -Scale 1 -Labels b2` from the local
`b2` evidence directory, then review its clock/workload/metrics and images
before A2 and C2. Preserve the preselected order and every result; stop on a
failed input, arrival, HUD or clock gate. Follow with the preselected 2x block,
fresh actual 1x GPU reuse proof, changing/streamed content and the full required
scene set. Keep the failed A6 2x clear disabled. B1 resource-chain coverage,
B3 pre-packet bypass and B4 visual/NPC/UI timing remain open; the goal is active.

All nine staged runtime files again match their retained backups, including
EXE `372161...`, both renderer paths `27B486...` and both runtime paths
`955BDC...`. No game/build/replay is running. Unrelated SDK kernel edits and
saves remain untouched. This documentation checkpoint needs no rebuild;
validation covers the three completed runs' existing gates, direct runtime
hashes, tracked Markdown links, repository boundary and `git diff --check`.

## Latest handoff: input failure, 1x GPU evidence and device-loss logging

The repeated 1x block reaches its final retained control, which exits normally
but skips the 100 ms A pulse at 12 seconds. Five preceding runs pass, including
the second recycling-on run's early median/p95/p99 of 23.895/26.442/28.388 ms.
**The preselected block fails its input gate:** keep all six runs under
`.local/native-renderer/b2/matching-retention/`; do not substitute a passing C2
or call the incomplete comparison retained. Its 2x block remains unexecuted.
Detailed results and the skipped input index are in [B execution](B_EPIC_EXECUTION.md#repeated-block-stopped-bounded-1x-gpu-proof-from-a-crashed-capture).

The prospective `wide-menu-pulses.fh1test` in that directory widens all eight
menu A pulses to 500 ms, preserving their start times, signup, captures and
motion. Its SHA256 is
`B8D8D835C2A928888C10DADCD7E599AF3A5B221A2DC757D00894C1CC6BBAEC3C`.
Two subsequent injected runs deliver every input and pass all seven HUD/pose/
motion checks. These diagnostic runs are not new clean retention comparisons.

Fresh actual 1x GPU evidence now exists, with important limits:

- First two-frame recycling-on capture `20260910T093402Z-p28600` crashes with
  graphics-device loss after one saved frame. Its replay checks 40 copies and
  first consumers, but that does not make the live run pass or explain the crash.
- Recycling-off control `20260910T093857Z-p8640` completes and writes both
  frames, but logs eight missing precompiled vertex variants during menu prewarm
  and seven invalid simulation deltas. Track those keys in B1; this is not an
  error-free renderer control. The local capture wrappers now require the child
  game's normal-exit result as well as RenderDoc's exit status.
- A diagnostic `d3d12_debug`/DRED attempt fails at DXGI factory creation before
  gameplay. Its owned capture helpers are stopped after the game exits; no OS
  setting is changed. This startup failure differs from the in-race device loss.
- With debug disabled and new presentation-error logging, session
  `20260910T095025Z-p28636` exits normally and passes all input/clock/HUD/motion
  gates. Frame 4634 verifies 12 nonzero CPU-source copies and first consumers
  (seven index, five vertex), including four matching victims beyond the oldest.
  Frame 4635 has no marked copies and adds no reuse proof. The run has six invalid
  simulation deltas and zero GPU errors/timing drops. The earlier crash remains
  unresolved; successful repetition with diagnostics is not a cause fix.

SDK `202247a` adds seven lines to the present-result path: log the Present
HRESULT and `GetDeviceRemovedReason`, then flush before returning GPU loss.
The presenter can otherwise abort before command-processor diagnostics run.
The production-path executable check passes success/other-failure classification
and both loss cases' values/log-flush order. Release runtime build passes;
the verified diagnostic DLL is
`6B97FB8B1CF15DBBB1C6A0AD762399F40F3AAFAC1E4D0CB8B818D82DFB8E24CC`
under `b2/present-loss-verified/`. No renderer default or GPU algorithm changes.
The initial archive copied the stale top-level DLL; its unchanged hash exposed
the mistake before use. The corrected build archives the actual build target.

All capture reports, exact source/binary hashes, failures and cleanup evidence
are in `b2/matching-capture/` and B execution. Captures use EXE `EC2E5F...`,
marker renderer `43E59C...` and either retained runtime `955BDC...` or the
explicitly identified diagnostic `6B97FB...`. Clean candidate `3A0B434A...`
remains the same renderer built from `acd222c`.

**Resume:** resolve the newly observed shader-pack misses and preserve the
capture-loss investigation. Use the widened-pulse route for fresh prospective
clean 1x/2x comparisons with one pinned EXE/runtime, all input/stage/HUD gates,
all phases, memory and every failed run recorded. Do not resume the failed old
block as if C2 were still pending. Continue changing/streamed/GPU-written
resource checks and the full B1 scene set. Existing motion-blur/depth-of-field
hooks now have verified static instruction/owner anchors in
`b4/post-processing-static-anchors.json`; dynamic cost and side effects still
need attribution before B4 profile work. B3 pre-packet bypass and NPC/UI timing
remain open. A6 stays restricted to symmetric 1x; B1-B4 and the goal stay active.

The retained nine-file runtime is restored: EXE `372161...`, both renderer
paths `27B486...`, both runtime paths `955BDC...`. No game/build/replay remains
active, and unrelated SDK kernel edits and saves are preserved. New validation
covers the presentation-path check, Release runtime, bounded replay reports,
live route gates, release-contract tests, Markdown links, repository boundary,
direct runtime hashes and whitespace. No preview release or B retention occurs.

## Latest handoff: corrected shader-pack staging and first v2 control

Checkpoint requested before further Epic B work. The eight apparent shader
coverage gaps from the last capture control are traced to an older AppData 1x
pack. All eight already exist in the current local offline packs. The updated
1x pack adds 25 entries while preserving all 21,987 old entries' bytecode and
bindings exactly. It is now staged with 22,012 entries, SHA256
`1636179BF8633D7406C7C3C735DD600C0C05666D8A8A8CAC188433730A38C026`.
The previous pack is preserved locally; the already-current 2x pack is unchanged.
Full hashes and validation are in [B execution](B_EPIC_EXECUTION.md#shader-misses-traced-to-stale-staging-prospective-comparison-v2).

Scripted/capture launches skip automatic pack/prewarm staging by design. The
local benchmark runner now explicitly stages the selected pack and checks
pack/catalog hashes before and after every condition. The
[automation guide](FH1_RENDER_TEST_AUTOMATION.md) records this requirement and
the direct AppData launch procedure without copying saves.

The new prospective C-A-B-B-A-C block uses the widened-pulse route (SHA256
`B8D8D835C2A928888C10DADCD7E599AF3A5B221A2DC757D00894C1CC6BBAEC3C`),
one test EXE `EC2E5F...` and diagnostic runtime `6B97FB...` throughout.
Only C1 at 1x is complete: `20260910T100454Z-p25840` exits normally, loads
22,012 precompiled shaders and passes all 23 inputs, 12 capture/clock checks
and seven HUD/pose/hold/motion checks. Manual race clocks at 76/88/92 seconds
are 5.517/17.607/21.615. GPU errors/timing drops are zero; the known two
invalid simulation deltas and startup device-path error persist.

Early-race median/p95/p99 are 62.656/112.635/120.540 ms. Other windows,
process CPU/RAM/faults and 355 valid GPU-memory counter records are in B
execution and local `b2/matching-retention-v2/race-1x-cabbac-c1/`. There is no
new off/on comparison or performance claim yet. The failed v1 block and the
unresolved capture device loss remain archived and are not superseded by this
single passing control. Experimental recycling remains off.

**Resume:** run `.local/native-renderer/b2/run-matching-retention-v2.ps1
-Scale 1 -Labels a1`, review all gates and actual race clocks, then follow
the existing B1/B2/A2/C2 order and the full 2x block. Local v2 plan and helpers
pin EXE/runtime/pack/catalog identities. Stop on any gate failure. Continue
streaming, mutation/GPU-source lifetime checks, full B1 scenes, B3 pre-packet
bypass and B4 visual/NPC/UI timing. A6 remains symmetric-1x-only. B1-B4 and
the goal are active; no new setting is retained or preview published.

All nine retained runtime files are restored and verified: EXE `372161...`,
both GPU paths `27B486...`, both runtime paths `955BDC...`. No game/build/replay
is active. Source before this documentation checkpoint is main `5b94b87`,
SDK `202247a`; the latter is already on its remote `development` branch.
Unrelated SDK kernel/libmspack dirt and saves are preserved. Shader packs,
captures and local experiment artifacts remain outside Git. Validation covers
pack payload equivalence/staging, the completed live run's gates and images,
runtime hashes, tracked Markdown links, repository boundary and whitespace.

## Latest handoff: v2 HUD failure and indirect-buffer submission evidence

The v2 comparison is **stopped**. After C1, A1/B1/B2 pass all gates; A2
`20260910T102201Z-p23016` exits normally and delivers every input but has no
HUD at 76 seconds. Its six later HUD checks pass. Final C2 and every 2x run
remain unexecuted. Preserve all v2 results and the explicit failed review;
do not replace A2 or follow the superseded resume instructions above.

Recycling-on early-race medians are 25.345/24.907 ms versus the first off
control's 65.954 ms, with fewer recorded allocations. Hold p99 is worse in
both on runs, and the full comparison is incomplete. No optimization is
retained. [B execution](B_EPIC_EXECUTION.md#v2-stops-on-an-early-hud-gap-trace-the-indirect-buffer-submission)
records every passing run's phases, CPU/RAM/fault/GPU observations and the
failed A2. Phase CPU rates now use existing OS samples; original reports are
preserved and all other fields are checked unchanged.

Two separate read-only diagnostic builds narrow the intermittent HUD defect:

- Decoder probe `20260910T103154Z-p22848` accounts for 1,307 source frames
  and reproduces five missing-HUD captures. It observes HUD shader groups
  before packet predication and distinguishes query kills/backend calls.
  The missing groups have no corresponding draw packets, but skipped parent
  command buffers still need accounting.
- IB probe `20260910T103956Z-p30256` adds copied-reader inspection of all
  indirect-buffer descriptors, including skipped ones. All 1,857,941 records
  match independent decoder counts. HUD is absent at 74.0 and 78.5 seconds.
  Visible frames reference full 2,475/4,076-word HUD lists through 23/46-word
  wrappers. In each missing capture, the 28 references to observed HUD buffer
  addresses are only 16 words; none is predicated away, and the full references
  are absent. Their contents, ordered publication and actual producer remain
  unproven; address reuse is not resource identity.

Both runs exit 0 with all 21 inputs, 32 capture/clock checks and expected race
poses. Dense capture review preserves every missing HUD. GPU errors/timing
drops are zero; two known invalid simulation deltas and the startup device-path
error persist. A first analysis assumption about the submission-frame number
was corrected against source and every output pair: closing a frame increments
that number while its source ID remains unchanged. The failed analysis log is
preserved. These are diagnostics, not clean benchmarks or a HUD fix.

Local evidence is `b2/hud-decode-profile/` and `b2/hud-ib-profile/`, with
source snapshots, hashes, routes, raw descriptors and decode/indirect reports.
The enclosing `b2` directory has the make/build/run/analyze helpers. Both use
test EXE `EC2E5F...`, runtime `0558BA...` and the pinned complete 1x pack;
GPU DLLs are `B80934...` and `81CBF6...`. Full hashes are in B execution.
The IB binary is 133,771,752 bytes, SHA256
`4B454196D100F46D10D3A5E75E49F81CD08512B16A94148CF64EEF5ECE4F126C`.

**Resume:** trace the short-list contents, ordered wrapper submission and
their CPU producer before restarting retention. Existing scene-command-buffer
observation is a lead; static IB-header candidates are recorded locally.
Do not rerun the stopped block unchanged until a favorable outcome. Keep all
B1 scenes, B2 mutation/streaming/tails, actual B3 pre-packet bypass and B4
visual/NPC/UI timing in scope. A6 stays symmetric-1x-only and recycling stays
off. The B4 motion-blur note is corrected: the last f8 load before the hook
comes from initial-image value 0.075, overwriting the earlier 500.0 load;
live values and savings remain unqualified.

All nine retained runtime files and SDK source bytes are restored and verified.
No game/build/replay is active. Source prior to this documentation checkpoint
is main `dfaf29b`, SDK `202247a`; no production algorithm/default or SDK pin
changes. Unrelated SDK kernel/libmspack edits and saves remain preserved.
Validation covers both Release diagnostic builds, geometry-cache checks,
live input/capture clocks, decoder/IB accounting, visual review, the B4 dataflow
check, runtime/source hashes, Markdown links, repository boundary and whitespace.
B1-B4 and the goal remain active; no preview release occurs.

## Latest handoff: normal-mode empty HUD lists after queue draining

The missing HUD is now traced through actual CPU submissions and the guest's
render-job dispatcher. The 16-word lists contain only four repeated scissor/
window-offset writes. Their short lengths are already present at CPU hook
`82416F18`; the full 2,475/4,076-word references appear in visible neighbors.
The submission path goes through a twelve-slot queue and callback thunk
`8249CC40`, called from dispatcher `82450160`. Producer and consumer generation
matching remains unproven.

Four diagnostic builds/runs are preserved. The first reproduces five missing
HUD captures. The second establishes queue indices/callers, while its passing
screenshots still leave source frames without HUD-group packets. The broad
dispatcher probe saturates its one-million-record limit and fails its diagnostic
gate. A narrowed three-callback probe completes, recording 28,440 decisions and
matching all 11,679 CPU queue submissions. It reproduces missing HUD at 77 s.

Most short lists come from mode-1 queue draining, and every full list comes
from normal mode 0. **The failing capture also has two empty mode-0 lists.**
Suppressing drain-mode output alone would not address this case. No HUD fix,
performance optimization or new setting is retained. See
[B execution](B_EPIC_EXECUTION.md#cpu-submission-queue-and-dispatcher-evidence)
for sessions, complete hashes, failures, decoded contents, caller proof and
validation. Local evidence/helpers are in `b2/hud-submit-profile/`,
`b2/hud-queue-profile/`, `b2/hud-dispatch-profile/` and
`b2/hud-dispatch-filtered/` under `.local/native-renderer/`.

**Resume:** trace the queue's begin/finalize operations and list generation
handoff, including nested dispatcher queues and empty normal-mode submissions.
Use the filtered probe as the starting point; preserve its failed broad sibling.
Do not restart stopped retention v2 unchanged or replay stale HUD lists as a
fix. Keep full B1 scenes, B2 mutation/streaming/tails, actual B3 pre-packet
bypass and B4 visual/NPC/UI timing in scope. All B items and the goal remain open.

The nine retained runtime files and diagnostic source bytes are restored and
directly verified: EXE `372161...`, GPU `27B486...`, runtime `955BDC...`.
The complete 1x shader pack remains staged. No game/build/replay is active.
Source before this documentation checkpoint is main `3790487`, SDK `202247a`;
no production algorithm/default or toolchain-pin changes. Unrelated SDK dirt
and saves remain preserved. A6 stays symmetric-1x-only; recycling stays off.

## Latest handoff: producer discards precede normal-mode empty HUD lists

The lifecycle probe `20260910T114031Z-p26872` reproduces missing HUD at 77
and 81 seconds. For those lists, the command cursor never advances between
begin and finalization, and no ordinary drawing jobs appear in that interval.
Closing, waiting and recorded metadata handoff succeed. The failure is already
present before finalization. 7,074 complete slot generations are checked;
26 of 27 captures have lifecycle coverage. Capture 72.0 precedes that window,
so the lifecycle report retains its full-coverage failure explicitly.

The enqueue probe `20260910T115046Z-p25232` reaches its two-million-record cap
and remains **rejected as a full diagnostic**. Its separately checked prefix
links 3,042 producer cycles by exact node/callback/owner/payload and recording
list to dispatcher/lifecycle/CPU records. In 48 cycles, drawing jobs are
discarded during recording, then begin/finalize/consume all run in normal mode
0 and submit an empty 16-word list. The observed discard condition is queue
byte 149 = 1, job flag = 0 and nesting counter 144 = 0.

**Resume:** follow the per-frame discard policy through shared enqueue
`823F4B30` (`823F4C10` admission, `823F4F08` discard, `823F4F04` linked node)
and queue publication's byte-149 assignment at `82C0D3EC`. Separate this policy
from the worker's later mode read at parent +6684. Test a correction that
preserves payload lifetime, queries/fences, ordering and guest side effects;
do not force every queued job to execute or replay old HUD lists. Reduce the
enqueue probe's redundant records before another full diagnostic. Do not
restart retention v2 unchanged.

[B execution](B_EPIC_EXECUTION.md#empty-normal-mode-lists-originate-in-producer-side-job-discards)
records exact binaries, counts, failure boundaries and checks. Local tools and
evidence are `b2/hud-lifecycle-profile/`, `b2/hud-enqueue-profile/` and their
make/build/run/analyze scripts, including the separate rejected-run prefix
analyzer. No production fix or optimization is retained.

All nine retained runtime files and diagnostic source bytes are restored and
directly verified. No game/build/replay remains active; the complete 1x pack
stays staged. Main source before this documentation checkpoint is `ab6757f`,
SDK `202247a`. Unrelated SDK dirt and saves are preserved. A6 remains 1x-only,
recycling stays off, and the complete B1-B4 goal remains active.

## Latest handoff: HUD admission prototype awaits retention

The local `hud-keep-profile` prototype postpones producer-side HUD job discards
until the existing worker's render/drain decision. It tracks a checked renderer
owner within matching begin/finalize recording markers, without changing the
dispatcher skip rules or replaying old HUD data. This is an experimental
behavior change; **the production source and staged runtime are restored**.

Session `20260910T120707Z-p30068` completes the 94-second 1x route, all 21 inputs,
32 capture-clock checks and 27 stationary Recaro HUD/pose checks. Decoder, IB,
CPU/queue, dispatcher, lifecycle and enqueue-outcome checks pass. The corrected
diagnostic covers every capture and no longer hits the enqueue trace cap.

Of 3,893 matched producer cycles, 356 render normally with no empty normal-mode
list; 3,537 still produce short lists while draining. 506,175 selected jobs
are recorded despite the old discard inputs. All 8,421 checked slot generations
close and wait successfully with matching object metadata. This supports the
proposed correction for the sampled case, not full HUD/lifetime correctness.
The run has 51 present drops and two invalid simulation deltas, so it provides
no clean performance or memory-retention claim. GPU timestamp drops and
GPU-category errors are zero; the known startup device-path error remains.

[B execution](B_EPIC_EXECUTION.md#hud-admission-prototype-passes-bounded-correctness-checks)
records the helper's exact admission policy, counts, complete hashes, checks
and next qualification. Local evidence is `b2/hud-keep-profile/`, including
`run-1x/enqueue-outcomes-report.json`, lifecycle reports, source patches,
candidate/binary manifests and the reviewed six-image contact sheet. Helpers
are in the enclosing `b2` directory. All earlier failures remain preserved.

**Resume:** use a clean candidate to measure queued payload/node lifetime,
memory pressure and frame-time tails; check other HUD/menu states and motion,
then qualify repeated 1x/2x comparisons. Reuse existing runners and OS sampling.
The stopped v2 comparison remains stopped. No production HUD fix, recycling
setting or B-item completion follows from this diagnostic.

All nine retained runtime files and nine instrumented sources are directly
verified restored. Retained EXE `372161...`, GPU `27B486...`, runtime `955BDC...`;
complete 1x pack staged. No game/build/replay is active. Source before this
checkpoint is main `9a03911`, SDK `202247a`; unrelated SDK dirt and saves remain
preserved. A6 stays symmetric-1x-only, recycling stays off, and the complete
B1-B4 goal remains active. This checkpoint does not publish a preview release.

## Latest handoff: clean HUD preflights and 1x comparison

The HUD-span helper now has a clean local build without per-job diagnostics.
EXE `20EE2F2D48BD2B83124D4812104F57631B53FB4794658CBA75B97E1419C0F319`
supports off/on through `PINYON_SHIFT_EXPERIMENT_HUD_KEEP_RECORDING=0/1`.
It uses retained GPU `27B486...` and presentation-diagnostic runtime `6B97FB...`
for every comparison, with recycling and owned clear off. The direct helper
assertion check and Release build pass. This remains a local unretained change.

Enabled preflights at 1x and 2x pass all inputs, captures/clocks, HUD/pose and
acceleration/braking/settling checks. The subsequent prospective 1x A-B-B-A
block also passes all four workload/identity gates and manual stage reviews.
Race-clock spreads are at most 0.058 seconds. Peak private-memory observations
do not show an increase. However, adoption remains **unqualified**:

- Acceleration p99 changes +28.87%, driven by a five-frame burst in B1 around
  119.34–119.48 seconds. B2 does not repeat it; existing counters do not establish
  its cause. Preserve the burst and both repetitions.
- Present drops total A1 1, B1 52, B2 42, A2 2. Every notification is within
  startup's first ten seconds, with none in the race windows. The counter means
  replacement of an unacquired presentation-mailbox image. Startup UI cadence
  and any visible timing effect need qualification before adoption.

[B execution](B_EPIC_EXECUTION.md#clean-hud-admission-both-preflights-pass-1x-comparison-remains-unqualified)
records every session, binary identity, per-run timing/memory, failures and
measurement limits. Local evidence is `b2/hud-keep-clean/`,
`b2/hud-keep-preflight/` and `b2/hud-keep-retention/`. The latter contains the
prospective plan, four 1x runs, comparison and drop/tail localization reports.

**Historical next step, superseded below:** all four matched 2x runs were
unexecuted at this checkpoint; the planned first command was
`run-hud-keep-retention.ps1 -Scale 2 -Labels a1` first, then B1/B2/A2 with
normal per-run analysis and manual stage review. Do not replace the existing
1x B1 or restart matching-recycler v2. Also qualify startup UI cadence, the
acceleration burst, queued payload lifetime and other scenes/motion. All
B1-B4 requirements remain open; the short race route cannot replace them.

All nine retained runtime files and nine instrumented sources are directly
verified restored. Retained EXE `372161...`, GPU `27B486...`, runtime `955BDC...`;
complete 1x pack staged. No game/build/replay is active. Main source before this
checkpoint is `bc2062e`, SDK `202247a`; unrelated SDK dirt and saves remain
preserved. A6 stays symmetric-1x-only, recycling stays off, and the goal is active.

## Latest handoff: stop 2x HUD qualification on prestart corruption

The clean HUD comparison now stops after 2x A1 and B1. A1 passes, while B1
(`20260910T125513Z-p8816`) shows bright green/white windshield and colored
headlight artifacts at the 62-second prestart menu. Automated HUD/pose/motion
checks passed; manual visual review fails. **B2/A2 stay unexecuted and there
is no valid 2x comparison.** Preserve B1 alongside the existing 1x +28.87%
acceleration-p99 result and startup mailbox-drop findings. No fix is retained.

A separate diagnostic (`20260910T130420Z-p22000`) captures two clean GPU frames
after its 62-second fallback; it does not reproduce the artifact. Reference
inventory and pixel-history replay complete, but reused/tiled target coordinates
are not yet mapped to the failing surface. Do not treat that capture as a
passing replacement or its transient HDR colors as failure attribution.

[B execution](B_EPIC_EXECUTION.md#clean-hud-admission-2x-comparison-stops-on-a-visual-failure)
records both sessions, timing/memory observations, failed image hashes, capture
hashes, diagnostics and limits. Local evidence is `b2/hud-keep-retention/` and
`b2/hud-glass-capture/` under `.local/native-renderer/`. The runner, summarizer
and review-writer now reject stopped/failed qualification; all three rejection
checks pass and preserve the failure. GPU captures/generated sources remain local.

**Resume:** trace whether vtable `820033FC` admits renderer instances beyond
the sampled HUD owner, and establish the windshield/headlight material and
resource history before a new correction or qualification protocol. Constructor
`82C528A0` has a direct caller in generated unit 214 near line 21994. The current
helper's predicate alone does not prove HUD-only scope. Do not continue the
stopped 2x block or restart matching-recycler v2 unchanged. Full B1 scenes,
B2 mutation/streaming/tails, actual B3 pre-packet bypass and B4 timing remain open.

All nine retained runtime files and nine instrumented sources are directly
verified restored. EXE `372161...`, GPU `27B486...`, runtime `955BDC...`;
complete 1x pack staged. No game/build/replay remains active. Source before this
checkpoint is main `ee6e20a`, SDK `202247a`; unrelated SDK dirt and saves remain
preserved. A6 stays symmetric-1x-only, recycling stays off, and the B goal stays
active. This checkpoint does not publish a preview release.

## Latest handoff: identify reference glass inputs

Static checks identify the admission predicate's object as
`CFixedFunctionRendererX360`, stored at render parent +2424 and shared by the
two observed queues. The prior 70–84-second trace contains one begin-owner;
startup/prestart scope and HUD-only behavior remain unproven. No admission
restriction or correction is made from that class identity.

Clean-reference replay now establishes three HDR scene strips and a later
180-degree UV reorientation. A closer sample in the third strip reaches the
glass pair VS `CE0FFEB0986E9971` / PS `1D38BA65C9D3C506`. Its selected inputs
are fetch slot 2, a cube at guest `1C879000` with mips at `1C9F9000`, and slot
13, a 2D texture at `1CE2D000`. The cube has no writes in this captured frame;
its contents come from earlier work. Six face exports, material constants,
shader disassembly and checked fetch decoding are available. The failed image's
GPU contents remain uncaptured, so none of this establishes its cause.

**Resume:** trace earlier cube production/publication and the slot-13 copies
using those bindings and the glass pair as anchors. Preserve the 2x visual
failure, the 1x acceleration/startup findings and both stopped comparisons.
[B execution](B_EPIC_EXECUTION.md#reference-glass-inputs-and-fixed-function-renderer-scope)
records exact events, decoded dimensions/formats, scope, local reports and the
two corrected diagnostic failures. All replays have terminated; no game run or
production behavior change occurred. Runtime/source hashes and the complete
1x pack remain retained. Main before this checkpoint is `900c9bc`, SDK
`202247a`; unrelated dirt and saves are preserved. B1-B4 remain active.

## Latest handoff: checkpoint before glass texture history capture

A local texture-history diagnostic now builds successfully. It records all
resolve publications and selected cube/2D creation, load and invalidation
events from startup, to investigate whether the glass inputs' required ranges
are available before import. CPU event order cannot establish GPU completion
or explain the failed image by itself. The earlier failed build is preserved.

Diagnostic GPU SHA256 is
`F4E08085CE577B202D383FE99139B128440246322C83BF6D989C64C2F8C00871`.
Evidence and the prospective route/plan are local under
`.local/native-renderer/b2/glass-history-profile-v2/`. **No live run has started.**
Finish the capture controller's partial-image/result checks, then use the
existing `run-hud-glass-capture.ps1 -History` runner for a separate diagnostic.
[B execution](B_EPIC_EXECUTION.md#glass-texture-history-diagnostic-built-live-capture-pending)
records the source path, event scope, exact identities, validation and resume
requirements. Both stopped comparisons and their failures remain preserved.

Checkpoint preflight verifies all nine retained runtime files and backups,
ten restored sources, the diagnostic binary/route and complete staged 1x pack.
Three PowerShell script syntax checks pass. Retained EXE `372161...`, GPU
`27B486...`, runtime `955BDC...`; no game/build/replay is active. Main before
this checkpoint is `2690045`, SDK `202247a`. Unrelated SDK dirt and saves are
preserved. No new performance setting or production fix is retained; A6 stays
symmetric-1x-only, recycling stays off, and B1-B4 remain active.

## Latest handoff: measure reflection cube GPU import cost

The startup texture-history capture completes without reproducing the green
artifact. All 722 cube loads have full preceding base/mip publication-range
coverage, but CPU call order does not prove valid GPU contents. Corrected GPU
inspection joins the glass bindings to the history through actual pipeline
commands: `GetUsage` omits shader reads here and cannot prove absent consumers.
Both stopped comparisons and their failures remain preserved.

A separate active-world capture verifies all 54 cube face/mip copies, about
8 MiB at 2x. A local extension of the existing native timestamp sampler then
measures full cube imports at both scales. Thirteen valid samples per scale
give total medians of **0.022912 ms at 1x** and **0.051200 ms at 2x**, with zero
reported timing losses. This makes the GPU conversion/copy work a low-priority
target; CPU preparation, reflection rendering and mip construction remain
unmeasured individually.
These are diagnostic operation costs, not retained FPS gains or frame-time tails.

[B execution](B_EPIC_EXECUTION.md#cube-history-and-import-cost-complete-diagnostic-low-priority)
records exact sessions, hashes, checks and preserved diagnostic failures.
Local evidence is `b2/glass-history-profile-v2/`, `b2/glass-reflection-capture/`
and final `b2/cube-timing-profile-v3/`. Earlier timing output lacked capture
metadata or unscaled query coverage and remains preserved. No production
renderer change is retained.

**Resume:** attribute CPU preparation and reflection face/mip producers using
the active-world capture and native records before changing update frequency or
choosing another chain. Do not restart the stopped comparisons unchanged or
treat another clean prestart as a fix. Eleven touched sources and all nine
runtime files/backups are verified restored; EXE `372161...`, GPU `27B486...`,
runtime `955BDC...`, complete 1x pack staged. No game/build/replay is active.
Main before this checkpoint is `8910b24`, SDK `202247a`; unrelated dirt and
saves are preserved. A6 stays symmetric-1x-only, and the B1-B4 goal stays active.

## Latest handoff: checkpoint CPU and reflection mip attribution

The new cube CPU diagnostic completes at both scales. Isolated backend-load
medians are **0.0045 ms at 1x** and **0.00595 ms at 2x**. Containing texture
requests include other textures and nested logging; their cost is not wholly
attributable to the cube. Preserve the unattributed 1x mixed-request outlier.
No renderer change or new performance setting is retained.

The stronger lead is the mip-generation pass sequence. Same-session native
records contain exactly 48 single-draw spans per sampled frame for pair
`2C53E1A563484076` / `21937679208E59A5`. Across 13 sampled frames per scale,
their summed medians are **0.892928 ms at 1x** and **1.073152 ms at 2x**.
These include preparation and resolves within the GPU spans, not just shader
execution, and do not establish removable time or retained FPS gains.

The active-world replay has now terminated successfully with descriptors,
VS/PS constants and following resolve state for all 48 draws. Its checked 2x
pattern consists of six eight-step reductions with input sides 512 through 4
and output sides 256 through 2. Full guest-range continuity, filter/quantization,
consumers/lifetime and producer-side effects remain unproven.

[B execution](B_EPIC_EXECUTION.md#cube-cpu-cost-and-reflection-mip-pass-attribution)
records sessions, exact diagnostic identity, checks and limitations. Evidence
is local under `b2/cube-timing-profile-cpu/` and
`b2/glass-reflection-capture/mip-contract/`, with runnable CPU nesting and
mip-cost/pattern checks in the enclosing `b2` folder. CPU-run capture clocks
pass; separate manual screenshot review remains pending. The prior GPU timing
runs have already received their bounded screenshot review.

**Resume:** decode the complete mip chain and trace its actual guest producer
before choosing a native replacement or reflection policy. Keep larger
depth/transfer chains in the ranking. The measured isolated cube import offers
little headroom. Preserve the green windshield/headlight failure, 1x
acceleration/startup findings and both stopped comparisons; do not resume them
unchanged. Required scenes, mutation/streaming/tails, true pre-packet bypass
and correct NPC/UI timing keep all B1-B4 items open.

Preflight verifies all nine retained runtime files/backups, eleven restored
sources and the complete staged 1x pack. Retained EXE `372161...`, GPU
`27B486...`, runtime `955BDC...`; no game/build/replay is active. Main before
this checkpoint is `a2a587a`, SDK `202247a`. Unrelated SDK dirt and saves remain
preserved. A6 remains symmetric-1x-only, recycling stays off, and the B goal
stays active. This checkpoint is for remote `dev`; no preview release is made.

## Latest handoff: reflection mip producer and cached submissions

All 48 reflection mip destinations and 42 within-face links now match the
captured guest layout. Live 1x/2x tracing identifies `823F69F8`: it generates
48 blits once, publishes six face-list handles and subsequently replays those
lists through `824167F8`. The runs check 709 / 730 complete cycles and
4,248 / 4,374 cached dispatches. Replacing only the initial builder would
leave the recurring GPU work intact.

A separate 1x command capture checks all six lists: 41,664 bytes and 2,352
packets in total, including 48 render draws, 48 resolves and 48 flush events.
All 624 sampled draw bindings match the expected face/mip sources. Incoming
predication/mode state, external loads, register effects and cache/queue
lifetime remain part of the replacement contract. Command hashes are
diagnostic identities, not lifetime proofs. No bypass or speedup is retained.

[B execution](B_EPIC_EXECUTION.md#reflection-mip-producer-and-cached-packet-contract)
records the exact sessions, binaries, guest anchors, checks, limitations and
earlier failed diagnostics. Reports and runnable checks remain local under
`b2/glass-reflection-capture/`, `b2/reflection-mip-producer-v3/` and
`b2/reflection-mip-commands/`. Only the two final producer runs' 20-second
screenshots received manual review; broader motion/timing remains unqualified.

**Resume:** link cached handles to actual submission buffers, finish the
filter/input/consumer/lifetime contract, then implement native mip production
with a safe pre-packet replacement for recurring submissions. Keep the larger
depth/transfer priorities. The earlier approximately 0.9 / 1.1 ms mip spans
are diagnostic costs including preparation/resolves, not promised savings.
Preserve both stopped comparisons and the green windshield/headlight failure.
All B1-B4 requirements remain open; A6 stays symmetric-1x-only.

Preflight verifies all nine retained runtime files and backups, twelve restored
sources and the complete staged 1x pack. Retained EXE `372161...`, GPU
`27B486...`, runtime `955BDC...`; no game/build/replay is active. Main before
this checkpoint is `ce7ae04`, SDK `202247a`; unrelated SDK dirt and saves
remain preserved. The checkpoint is for remote `dev`, with no preview release.
Resource-link, complete-producer-cycle and packet/binding checks pass, along
with tracked Markdown links, the 509-file repository boundary check and
`git diff --check`.
