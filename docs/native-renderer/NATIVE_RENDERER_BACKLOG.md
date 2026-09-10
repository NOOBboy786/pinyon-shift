# Native renderer: prioritized backlog

Updated: 2026-09-08. Baseline: **0.1.2-preview.3**, highly experimental.
Goal: lower hardware requirements and fully retire the Xenos renderer while
preserving gameplay and timing with visually faithful rendering. Small, stable
visual differences are acceptable when they measurably reduce cost; numerical
"95% accuracy" is not a target. This is the current priority order;
V5/V6 documents remain implementation references, not completion evidence.

Architecture reference: [Xbox 360 native-renderer research](XBOX360_NATIVE_RENDERER_RESEARCH.md)
compares Unleashed, re:Blue, Skate 3 and Marathon with FH1, including resource
ownership techniques and proposed experiments. Its recommendations do not mark
the items below complete or establish new hardware requirements.

Current P2/P3 execution order: [native resource migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md).
Start with A1–A6: one qualified native resource chain. This supersedes older
next-step ordering below; retain the P0–P4 outcomes, acceptance rules and evidence.

## P0 - Stabilize the reported gameplay experience

Deferred at the user's request on 2026-09-07; P2 is now the working priority.

- [ ] **Reproduce and fix the area-specific performance collapse.** Locate the
  screenshot area; record approach, stationary/camera changes and exit. Compare
  CPU/GPU frame times, draw workload and resource activity; fix the measured
  bottleneck. Done: repeatable before/after runs show the collapse resolved
  without visual regressions or slower ordinary driving.
- [ ] **Verify and fix animation timing.** Check NPC animations first, then
  title-screen transitions, at different render rates. Done: animation duration
  follows real time and simulation, physics, input and audio remain correct.

Evidence: [manual playtest feedback and screenshot](PLAYTEST_FEEDBACK_2026-09-07.md).
Around 70 FPS in ordinary driving and around 15 FPS in the affected area are
user observations, not controlled benchmarks. Causes remain unconfirmed.

P0 status (2026-09-07): investigated, neither item fixed. Manual logs correlate
slow areas with geometry-cache import spikes at the 32 MiB limit. A containing-
window reuse candidate passed cache checks but lacked performance/parity proof
and was restored out. NPC clip timing was inconclusive. See the checkpoint's
P0 investigation for evidence and the next reproduction steps.

## P1 - Make the preview reproducible outside the development machine

- [ ] **Qualify a clean launcher setup.** Verify the released source produces and
  stages every required shader pack/catalog without developer-local caches.
  Complete missing launcher-side production, resume/reuse and invalidation paths.
- [ ] **Qualify supported configurations.** Exercise resolution changes and
  NVIDIA/AMD/Intel setups; document what is tested and what remains unsupported.
  Done: supported configurations start and play with valid artifacts and no
  unexplained shader/pipeline misses.

Implementation reference: [V6 backlog](NATIVE_RENDERER_V6_BACKLOG.md).

P1 status: [clean artifact production and qualification record](P1_ARTIFACT_PRODUCTION.md).
Two empty-cache NVIDIA 1x startup runs passed. Packaging/SDK paths and the Python
dependency are fixed; complete gameplay artifacts, setup integration, reuse,
scale changes and other vendors remain open.

## P2 - Reduce measured renderer cost and expand native coverage

Status: [first race baseline and dependency ranking](P2_DEPENDENCY_RANKING.md).
Race coverage is recorded and the ranking is reproducible. B848's native vertex
specialization is retained at 2x after parity, live binding and regression
checks. Shader-specific cost, the remaining scene set, broader shader/pass
coverage and resource replacement remain open. The two-UV candidate stays disabled.
The 31511D video pixel stage is also retained for its exact 2x variant after
captured output parity, live binding verification and a passing title comparison.
The B848 geometry-ownership experiment passed captured input/output checks but
failed the controlled performance gate; ownership admission is disabled. Its
validated native vertex specialization remains enabled on shared bindings.

Work in the following order. Performance gains and dependency retirement are
separate outcomes: record both, and do not count native coverage as a speedup.

- [ ] **P2.1 - Establish the gameplay cost ranking and 1x baseline.** Reuse the
  existing captures and timing tools for a repeatable driving/race window, with
  screenshots outside measurement. Rank actual per-frame GPU pass cost, CPU
  imports/copies and memory pressure, including already-native passes. Record
  median/p95/p99, coverage and fallback reasons; draw counts, static instruction
  counts and a pass's first shader are not cost attribution. Keep title/menu
  measurements separate. The slowdown town remains unidentified and deferred;
  it does not block independent work. Qualify the retained B848/video stages at
  1x before broadening their current 2x gates; leave other configurations explicit.
- [x] **P2.2 - Test a cheaper gameplay post-process pass.** Start with the captured
  20A41D/614588 contract and measure its complete per-frame contribution; do not
  substitute the title's 9AAEF9 variant or credit it with an entire mixed span.
  Isolate one costly visual operation, then test fewer samples or a lower-resolution
  intermediate where valid. Preserve live constants, depth-sensitive behavior
  and required outputs. Retain a simplification only after motion/image review
  and a repeatable benefit; move to the next measured bottleneck if cost is small.
  Result: center-sample experiment rejected after stationary ABBA showed median
  +0.99%, p95 +10.99% and p99 +16.42% with mean draws +0.063%. It remains disabled;
  this completes the bounded experiment, not post-process retirement or broad
  visual/input-mode qualification.
- [ ] **P2.3 - Reduce resource transfer and cache overhead.** Video CPU upload is
  retained for the exact movie shader pair at symmetric 1x/2x. Each scale passed
  three changing-frame upload comparisons (4,147,200 bytes), visual review and
  title checks. The latest 1x ABBA had no material regression; no general gameplay
  speedup is claimed. Other scales remain unqualified. Now target measured
  redundant geometry/texture uploads, copies, render-target resolves and readbacks
  through existing caches. B848 ownership stays disabled after its +15.32%
  median-frame regression; diagnose import/cache cost before retrying it.
- [ ] **P2.4 - Simplify expensive scene effects where measurements justify it.**
  Investigate shadows, reflections or distant shading only if the cost ranking
  identifies them. Document each specific quality tradeoff and compare motion,
  frame-time tails and memory. These are hypotheses, not established bottlenecks.
- [ ] **P2.5 - Complete remaining native shader/pass and resource coverage.**
  Replace the highest-value remaining families and supported geometry, textures,
  render targets, resolves and readbacks, including their bindings and side
  effects. Use the simplest faithful implementation. C347/21B70 and two-UV stay
  disabled until deliberately qualified under the acceptance rules below;
  relaxed visual tolerance alone is not evidence to enable them.

### Acceptance rules

- **Strict correctness:** simulation/animation timing, geometry placement,
  guest-visible writes, resource validity, queries and synchronization remain
  correct. Resource byte checks and mutation/fallback checks remain necessary;
  visual tolerance does not relax memory correctness.
- **Visual tolerance:** small, stable shading/effect differences may be accepted
  for repeatable performance or memory savings. Describe the difference before
  evaluating it; compare the same scene in screenshots and motion. Missing
  objects, flicker, broken transparency and severe popping fail qualification.
  Exact pixel parity is a diagnostic tool, not a universal release gate.
- **Evidence:** compare matched workloads/settings against the retained build,
  record median/p95/p99, CPU/GPU time and memory, and confirm the intended native
  path actually runs. Repeat enough to distinguish gains from run variation.
  Record tested scenes/scales and limitations; no whole-game claim from one frame.
- **Retention:** a visual compromise needs a repeatable benefit worth its visible
  cost. A faithful dependency replacement may be retained without a speedup when
  it removes a demonstrated dependency without material regression. Otherwise
  leave it disabled. Xenos remains a temporary reference until P3 can retire it.

Next bounded tasks: qualify retained shader stages at 1x and continue P2.1
CPU/resource attribution. Detailed census is now opt-in via
`--pinyon_shift_fh1_scene_dump=true`; two default corpus runs confirmed no scene
dumps and reduced the diagnostic spike. Remaining preparation cost is unresolved.
1x race reference smoke passed; the RenderDoc attempt lost the device at capture
and produced no RDC. Video pixel stage now accepts symmetric 1x/2x after exact replay, live binding
verification and ABBA with no material regression (median -0.60%, p95 +0.26%,
p99 +2.01%). B848 and CPU video upload remain 2x-only.
B848 1x replay now passes with corpus-disabled capture: 489 exact vertex outputs
and six exact attachments; live binding also passed. Retention was rejected after
ABBA showed median +2.36%, p95 +8.51%, p99 +16.17% (draws +0.81%). Keep B848
2x-only and diagnose cost before revising the 1x candidate. Corpus-enabled 1x race
capture still loses the device.
A grouped-load B848 prototype now passes the same 489 vertex outputs and six
attachments at 1x; boundary/SRV/UAV helper checks pass. Benchmark it in isolation
before reconsidering the rejected 1x extension. Superseding result: live binding
passed but ABBA showed median +1.63%, p99 +9.36% (draws +1.73%); keep it isolated.
Return to broader resource attribution before another B848 revision.
Six recorded gameplay windows have zero readbacks/strict-query waits/memexport;
D3D12 texture-cache counters measure SRV descriptor reuse, not uploads. Next
measure actual texture request/load and GPU render-target transfer cost. Two new
2x probes now measure 2.46/2.22 ms texture-request CPU per sampled frame and
86/89 dirty-load attempts/frame. Trace classification now finds 97.626% of successful load messages are scaled resolves. An unused packed-tail key normalization passed layout checks but failed live retention; it remains isolated. Direct samples now measure 1.13/1.14 ms GPU conversion+copy per sampled frame. The captured 0x1C4E1000 chain has three writes from a reused 4xMSAA RGBA16F target, with loads before and during assembly; direct aliasing is unsafe. E17 now has a faithful native 2x pixel replacement: exact captured output, confirmed live binding and neutral ABBA frame times. Next preserve region/history state in a native resolve output; RMS 1x and any reduced-tap filter remain unqualified; session isolation now revalidates prior CPU preparation figures; prioritize larger scene spans/C347 coverage over reduced-tap RMS work;
request totals include cache/transition work and are not upload-only cost. No production
change; 1x B848 retention remains open. Video-upload qualification is complete for the retained 2x scope. The first P2.2
experiment is concluded without retention; prioritize larger measured costs.

P2.1 progress: four 1x/2x/2x/1x driving runs completed on the retained build.
1x reduced mean median frame time by 5.31% and process private memory by 46.51%
in the short probe; traffic varied. See the ranking's resolution-baseline record.
New shader gates remain 2x-only. Frame-specific diagnostics now rank three sampled
gameplay frames: spans beginning with 20A41D/614588 average 0.355 ms per sampled
frame, below several other spans. Next inspect the larger spans' captured work
and keep the post-process experiment bounded. This is provisional GPU span
attribution; broader sampling, CPU cost ranking and 1x shader qualification remain.

P2.2 progress: an offline center-sample 614588 prototype renders close to the
original in one race capture (active-image mean channel error 0.005-0.010/255).
It is not admitted at runtime. A full-sampling control still needs correction;
motion, supported live inputs and performance remain unqualified. The attempted
RenderDoc counter measurement failed and supplies no speedup evidence.
The zero-offset control now narrows the large control discrepancy to neighboring
sampling; captured unsigned views and the true 3D LUT are verified. Next qualify
the center candidate's live input contract and benchmark it in isolation; keep
the full-sampling control out of production.
The integrated candidate now handles signed fetches and array LUTs, with admission
still disabled. Native binding is verified in a live race capture. The first
driving ABBA comparison is confounded by traffic/draw-count changes; the last
baseline was fastest. Next use a steadier workload and broader visual/input-mode
coverage before deciding whether to retain the simplification. Superseding result:
the stationary comparison failed the retention gate; the experiment is concluded
and the shader stays disabled. Remaining signed/array/motion qualification is
unclaimed and unnecessary unless a new reason to retry emerges.

## P3 - Remove the Xenos renderer dependency

- [ ] Replace remaining command/register interpretation and fallback execution
  with the necessary FH1-native submission paths.
- [ ] Remove remaining renderer reliance on the shared guest-memory GPU buffer.
- [ ] Delete superseded Xenos renderer paths, translation dependencies and build
  inputs only after their replacements cover all required behavior.

Done: an FH1 build runs the qualification scenes without the Xenos renderer or
hidden renderer fallbacks. A permanent compatibility renderer does not satisfy
this goal; retain required behavior through native implementations.

## P4 - Establish lower hardware requirements

- [ ] Run the qualification set on lower-end CPU/GPU configurations and measure
  memory use, frame-time tails and sustained performance.
- [ ] Publish supported settings and revised minimum requirements only when
  repeatable results support them. Expand beyond highly experimental status only
  after the stability and coverage gates above pass.

## Working rule

Continue P2 while unfinished P0/P1 work is deferred. Finish one bounded change and its check
before expanding scope. Update this list as work lands; detailed evidence stays
in the [performance checkpoint](NATIVE_RENDERER_PERFORMANCE_CHECKPOINT_2026-09-04.md)
and [V5 implementation record](NATIVE_RENDERER_V5_BACKLOG.md).


Manual discovery tooling: [playtest recording guide](DISCOVERY_PLAYTEST.md). Sampled coverage, problem markers, periodic checkpoints and session reports are implemented; longer playtests will supply new P2.1/P2.5 evidence.

Manual playtest evidence: [2026-09-08 discovery findings](DISCOVERY_FINDINGS_2026-09-08.md). Six markers identify town/outpost, plaza, highway and canyon-junction reproductions. Next targeted comparisons: markers 3/4 and 6. Fix bounded coverage exhaustion before another long discovery run; no root cause or renderer fix claimed.

Discovery coverage follow-up completed: independent bounded shader-family inventory survives detailed-key saturation; current/incomplete rankings are explicit. Saturation/ranking checks, release build and live checkpoint smoke passed. Existing playtest markers remain the next reproduction inputs.

RMS 1x qualification completed: exact captured output, verified native live binding and neutral stationary ABBA; exact RMS pixel stage is now retained at symmetric 1x and 2x. This expands native coverage without a speedup claim. See the latest ranking section for evidence. P2 remains incomplete.

Video CPU upload at 1x qualification completed: three changing live movie frames preserve all 4,147,200 active plane bytes; clean ABBA shows no material regression. Existing upload path is retained at symmetric 1x/2x. Detailed evidence is in the latest ranking section. Broader P2 resource coverage and marked-stall attribution remain unfinished.

Single-range request preparation experiment concluded without retention: 1x ABBA median -0.639%, p99 +3.607%, CPU -0.750%, with workload drift and fastest final baseline. Source/binaries restored; production range-validation/page-coverage checker added. Prioritize scaled-resolve conversion/region ownership next.

Scaled 32-bit 2x conversion prototype: CPU reference and offline GPU replacement reproduce 44,236,800 active texture bytes across old/partial/full resolve states. Shader source and address/endian checker added; no runtime admission or performance claim yet. Next qualify exact live admission and benchmark before retention; resource ownership and scratch-copy removal remain open.

Scaled 32-bit 2x conversion retained for the narrow 1280x720 format-7 contract: live binding, independent input/output byte checks and ABBA/BAAB with no consistent regression. No repeatable speedup claimed. Replay history limitation and results are documented in the ranking. Next target native texture output/scratch-copy removal; P2 stays incomplete.

Direct texture output experiment rejected: captured writes are byte-exact and remove the copy, but ABBA p99 regressed 15.128% with fewer draws. Runtime implementation restored; only the unbound prototype/checks remain. Diagnose GPU write/sampling cost before another attempt. P2 transfer/resource work remains open.

Direct-output diagnosis: sampled conversion cost rose from about 28 to 47 microseconds/load, largely offsetting the removed ~22-microsecond copy. Sample losses limit per-frame conclusions. Retention rejection stands; prioritize broader coverage or a cheaper write kernel, not copy elimination alone. See ranking for four probe sessions and count-matched subset.


Terrain queue correction: the C347/21B70 material shader already exists and the full pair failed earlier retention tests. Current retained-renderer capture audits 45 draws but supplies no new performance evidence. Do not reimplement or rebenchmark the unchanged pair; require a materially changed candidate or newly measured workload. See the latest ranking section.


RGBA8 scaled-conversion extension: four captured loads pass exact replay and independent CPU checks; clean ABBA is roughly neutral with workload drift. Live capture failed at trigger, so native binding remains unverified. Candidate preserved locally, production restored. Next resolve live qualification before retention; no speedup or expanded production coverage claimed.


RGBA8 extension follow-up: native live binding and exact output now verified. Reversed BAAB p99 +6.59%; combined eight-run p99 +3.95%, CPU +2.57%, draws -2.54%. Extension not retained; production stays format-7-only. Before revisiting, require matched per-dispatch cost evidence or a materially cheaper kernel, not another unchanged stationary batch.


P2.1 timing coverage fix retained: explicit loss reasons identify capacity exhaustion; bounded record capacity raised256 to512. Live probe reached record267 with zero reported losses; invalid pass timestamps now count as losses and texture rankings expose loss metadata. New retained DLL2FD4B204. No FPS claim; use these improved diagnostics for further matched attribution.


Current1x/2x diagnostic comparison: zero reported losses; two single-clear spans scale roughly4x while the811-draw geometry span barely changes. Pass boundaries include following attachment transfers, so this is not clear/shader attribution. Next isolate PerformTransfersAndResolveClears GPU cost at both callers before any clear-cutout or effects simplification. See latest ranking table; no renderer change in this comparison.


P2.1 direct transfer timing retained, DLL87B79AAB: ordinary ownership-transfer intervals average1.435ms/frame1x versus5.683ms/frame2x, near-equal call counts and zero reported losses. Resolve-clear calls are much smaller. Next map dominant transfer source/target contracts before cutout/replacement; do not attribute old single-clear spans to clear API cost or reduce effects quality on that basis.


Dominant transfer contract identified: D24S8 base720/pitch13,1xMSAA->4xMSAA, full wrapped EDRAM range, four calls/frame (~1.57ms/frame in verbose audit). Next inspect its actual shader/sample mapping and existing native stencil-output selection before replacement; preserve depth AND stencil. Verbose audit restored out; retained87B79AAB unchanged.

P2 transfer follow-up: D24S8 1xMSAA->4xMSAA confirmed one depth plus eight stencil-bit draws; RTX4080 reports native stencil-reference output unsupported. Exact address shortcut passed378.6MB replay parity but failed eight-run retention (p99+9.61%); restored87B79AAB renderer. Next investigate actual transfer work/ownership; do not repeat unchanged address-only candidate. See latest ranking section. Original area slowdown unresolved.

Stencil audit: dominant four copies have zero stencil in captured source; positive-control replay confirms readback includes stencil. However174 guest PSOs/2,916 draws enable stencil, including nonzero references. Next establish per-range clear/write provenance; no global stencil skip or capture-based whitelist. Production unchanged.

Transfer provenance:374 guest draws on the two dominant D24 resources leave stencil disabled, but incoming color/depth transfers repopulate stencil after clears. Clear-only/per-resource flags are insufficient. Next test GPU-side source-stencil detection with original-copy fallback; preserve all sample/tile contracts. See provenance evidence in ranking.

Stencil query experiment implemented, disabled (`fh1_stencil_predication=false`). Reuses existing shader for one read-only query, predicates eight copies, bypasses active guest queries. Build/command guard checks and captured zero plus synthetic nonzero GPU controls pass. Performance/1x/broader fidelity gates remain; staged87B79AAB unchanged. Next qualify candidate B709E04B before enabling.

Stencil predication not retained: eight runs show opposing order/draw-count drift, combined GPU-0.17%/p99+3.83%; no repeatable benefit. Removed disabled runtime experiment and rebuilt exact87B79AAB. Source/check archived locally. Strengthen isolated attribution before another transfer experiment; do not repeat unchanged runs. Baseline a3 rear-window red artifact recorded, P0/P1 still deferred.

P2.1 replay timing cause identified: RenderDoc requires Windows Developer Mode (currently off); FetchCounters empties follow fatal replay-device error. Preflight now fails before opening device. User preference pending; native timestamp profiling remains available. Do not read empty counters as zero cost or reuse the failed replay controller.

P2.1 native ranking tool added: rank-fh1-transfer-contracts.py validates complete ordered contracts, frame denominator, session isolation and losses. Self-test passed; reproduces archived35 groups/418 records/11 frames exactly. No performance gain claimed; renderer unchanged.

Resource-migration A epic complete (2026-09-09): [A6 retention report](A6_OWNED_DEPTH_RETENTION.md).
The owned-depth chain is retained and enabled at symmetric 1x draw resolution;
2x keeps compatibility clears after failed North Carson tail qualification.
The exact retained build passes 1x native and 2x fallback race-start checks.
Continue with B1 in the [migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md);
scaled owned-clear admission requires new attribution or a changed design.
This does not close P0/P1, broader resource migration or Xenos retirement.