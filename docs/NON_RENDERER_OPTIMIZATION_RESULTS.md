# Non-renderer optimization results

Branch: `codex/non-renderer-optimization-experiments`.
Plan: [optimization research](NON_RENDERER_OPTIMIZATION_RESEARCH.md).

## Current decision status

No runtime optimization is recommended for merge yet. Build/profile collection
controls have working smoke evidence; hardware requirements and broad gameplay
correctness are not qualified. The following table is a scope audit, not a
replacement for the experiments below.

| Item | Evidence now | Required next decision |
| --- | --- | --- |
| CPU-01 | Frozen identities/flags; repeated CPU/frame/I/O samples; thread CPU attribution | Useful baseline established; scheduling wait durations and instruction stacks remain unavailable |
| CPU-02 | Six stationary runs, runtime-only change, matched settings/poses | Retain tracing ON; no consistent runtime benefit from OFF |
| CPU-03 | Six stationary runs; smaller code; variable results | Keep IPO OFF; no reliable runtime win in this experiment |
| CPU-04 | Three-scene training; map check; six held-out race runs | Keep PGO OFF; 2.02% smaller executable, no consistent runtime win |
| CPU-05 | Unused main registration excluded; normal/PGO builds, map and repeated race checks | Recommend the narrow build exclusion; defer O2/O3 sweeps without hot-path evidence |
| CPU-06 | Frequent small helpers plus measured guest-thread CPU use | Explicitly defer register/native-function changes: counts and thread totals do not identify instruction cost |
| IO-01 | Warm town synchronous-read durations measured; process I/O samples | Timed reads do not explain large warm-run stalls; open/stat and cold-storage latency unresolved |
| IO-02 | Warm gameplay sample: 161 reads take 2.471 ms total | Explicitly defer async/coalescing rewrite; current evidence does not justify its semantic risk |
| RT-01 | Frequent polling candidate; command and guest threads both consume CPU | Explicitly defer scheduling/polling changes until the polling function's time and wait behavior are measured |
| RT-02 | No recorded XMA stalls/recoveries in analyzed windows; no timed decompression hotspot | Explicitly defer audio/decompression changes; absence of counters is not broad audio qualification |
| QUAL-01 | Normal exits, exact sessions, simulation counters, held-out map/race and matched poses | No broad runtime optimization is qualified; cold storage, lower-spec, long-play audio/NPC timing remain limitations |

The matched baseline build's 332 generated compile commands were compared with
the staged PGO USE commands and differ only by `-fprofile-use`; both retain the
same source list (without unused main registration), SSE4.1 and exception flags.
See `matched-compile-check.txt`. Completion of that build and binary/runtime
verification are separate gates, not implied by this command comparison.

## Starting state — 2026-09-09 UTC

The initial branch switch preserved the existing uncommitted renderer/runtime
work. No experiment has yet demonstrated a performance improvement.

Before editing, the project and SDK binary diffs, changed/untracked source files,
configured Release commands, and existing executable/DLL files were saved under
`.local/non-renderer-optimization/baseline-20260909T050809Z/`. Its `baseline.json`
records source file hashes and binary hashes. It contains no save-file copies.
This private snapshot distinguishes pre-existing changes from experiment changes;
it is not a clean source revision or proof that the binaries match current source.

| Component | Starting identity |
| --- | --- |
| Project HEAD | `f4c39de29fb456a0a258fb18d04c45347d573e06` (Git commit, not SHA-256) |
| SDK HEAD | `6db74f6de0230727358d93f8a221f40fbba6a792` (Git commit, not SHA-256) |
| Executable | `882d9247f23b97b0121a0d7f15f3efb4569728777a26f03ef2b676d8a9dbcb52` |
| Runtime DLL | `2dbc82dd92b1af47115242fb818213280921d69e946dc7e41358d1d3158fe0c8` |
| Renderer DLL | `87b79aabec3f06326df616dc02ccc3588e1cffefee3a4e2b3590a17655ea23b5` |
| Speech DLL | `0e5369e0c30803a159c0cdd35eaf993d4e9f7042f05fe586c53fc8c68f612406` |
| XMedia DLL | `b27a5562dbc4f74716a5a5df497c825bba0a9425e341044bc36967a8e9329324` |

## Measurement availability

- No `pinyon_shift` process was running at initial inspection.
- Existing fixed-time driving and town-approach scripts are available under
  `.local/native-renderer/`; their scene coverage must be revalidated against the
  current save before matched comparisons.
- `wpr.exe -status` confirmed no existing recording. A short CPU capture capability
  check failed with `0xc5585011`: unable to enable the system-performance profiling
  policy. No policy was changed and no user recording was stopped. Scheduling
  attribution via WPR remains unavailable in this session; do not report it as
  measured. Existing recorder process CPU and frame counters remain candidates
  for lower-overhead comparisons, with narrower attribution.
- The research document was ignored by the repository's `/docs/*` rule. Explicit
  exceptions now allow the research and this results ledger to be tracked.

## Experiment ledger

| Item | State | Evidence still required |
| --- | --- | --- |
| CPU-01 baseline and effective flags | In progress: starting snapshot saved; isolated baseline configured successfully | Matched workload measurements, symbols and compiler semantics audit |
| CPU-02 tracing/counters | Both import-tracing variants built; 95 runtime commands compared | Independent baseline/candidate timing and retained diagnostics |
| CPU-03 ThinLTO | Built; four open-world runs show substantial variance, no consistent timing gain | Broader qualification and CPU attribution; default remains OFF |
| CPU-04 PGO | Instrumented game build in progress, IPO OFF | Verified profile writing, broad multi-module profiles and held-out validation |
| CPU-05 optimization level/code size | Pending attribution | Hot-code evidence |
| CPU-06 guest code/dispatch | Pending attribution | Hot-path and state-preservation evidence |
| IO-01 streaming attribution | Pending; WPR capability check failed | Alternative attribution or an available capture session |
| IO-02 asynchronous/lookup changes | Conditional on IO-01 | Correct completion and measured benefit |
| RT-01 waits/allocations | Pending attribution | Critical-path evidence |
| RT-02 audio/decompression | Pending attribution | Hotspot and latency/correctness evidence |
| QUAL-01 qualification | Pending | Paired runs, held-out scenes, simulation/audio/save correctness |

## Merge recommendation

None yet. Documentation establishes the experiment plan; no runtime or compiler
change is qualified for merging. Keep the goal active.

## Build preparation

`out/build/non-renderer-baseline` configured successfully with the existing
Release preset and `CMAKE_EXPORT_COMPILE_COMMANDS=ON` (Clang 20.1.8, SSE4.1,
Tracy off, performance counters on). Configuration took approximately 111 s.
The source-built SDK artifact directory resolves inside this isolated build.
Configuration output is in `.local/non-renderer-optimization/configure-baseline.log`.

The first compilation targets `rexruntime` with eight build workers and the
release wrapper's `SOURCE_DATE_EPOCH=1784764800`. It does not invoke the game
codegen target or replace preview binaries. Output is in
`.local/non-renderer-optimization/build-baseline-runtime.log`; compilation and
runtime qualification are still pending. This baseline is preparation for
CPU-02, not a timing result.

## CPU-02: import-reach tracing isolation

Both `rexruntime` compilations completed successfully. The default tracing build
is staged in `.local/non-renderer-optimization/trace-on`; the candidate is staged
in `trace-off`. Each package contains the same saved executable, renderer and
facade DLLs. Their binary manifests confirm only the runtime DLL differs:

- Trace on: `f081e42d97b3a39f5b8f0b6877f8b8d904f7bc58c0d213bc194d4b0b3773ad3e`.
- Trace off: `b06f8acae05497c630ea2201a6593f773455dfe807857bb2fbe53924f7df5413`.

All 95 runtime compile commands were compared against the saved baseline. They
differ only by removal of `-DREXGLUE_TRACE_IMPORTS=1`; source paths and remaining
options match. The candidate retains performance counters. Build logs and
`trace-command-check.txt` are stored beside the packages.

The experimental CMake option `PINYON_SHIFT_TRACE_IMPORTS` defaults to ON, preserving
preview behavior. The existing launcher now accepts optional `-BuildDirectory`
and resolves both the game executable and shader producer within it. PowerShell
syntax validation passed. The launcher already had unrelated renderer changes;
only the new parameter and build-path substitutions belong to this experiment.

A smoke-test attempt was stopped by the pre-launch process check: the regular
preview was running as PID 53164 from `out/build/win-amd64-release`, starting at
2026-09-08 23:12:52 local time. It was not stopped or replaced. Runtime smoke tests,
matched CPU/frame measurements, and any performance conclusion remain pending.

## CPU-03/04: compiler capability probe

A two-function, non-game executable/DLL probe passed with the installed LLVM
20.1.8 toolchain: `-O3 -msse4.1 -flto=thin -fuse-ld=lld-link`, IR instrumentation
via `-fprofile-generate -fprofile-update=atomic`, per-module/process profile
filenames, `llvm-profdata merge`, and a separately linked profile-use build.
The merged data contained both `main` and the exported DLL function `probe`;
the profile-use executable returned success with the optimized DLL.

Sources, profile data, summary and success marker are under
`.local/non-renderer-optimization/compiler-probe/`. The profile runtime library
and `llvm-profdata.exe` are present in the pinned toolchain. Initial PowerShell
argument-parsing attempts failed before compilation and were corrected using
quoted argument arrays; the final compiler and execution checks passed.

This establishes toolchain capability only. It does not validate PPC exception
semantics, game profile coverage, or performance. CPU-03 and CPU-04 remain pending
on actual game builds and qualification.

## Gameplay smoke and frozen compiler baseline

The existing preview subsequently exited. Trace-on (PID 27784) and trace-off
(PID 4804) each completed the existing `driving-clean.fh1test` route and returned
exit code 0. The trace-on image was inspected and shows open-road driving at the
end of the route. Both produced frame CSVs and captures. Settings-file SHA-256
was identical: `e267dcac701a0e14a92df00aa059c2fb639d5a0b32b7d3dc279a00a5c974afc7`.

These are not a qualified performance pair. Initial CSV selection by PID alone
incorrectly selected an older run with reused PID 4804, creating an apparent
46.68 s duration. The incorrect file is retained as `misattributed-perf.csv` and
excluded. Exact sessions `20260909T051759Z-p27784` and `20260909T051930Z-p4804`
were verified through their configured output paths in the event logs. Correct
CSV durations are 32.013 s and 32.005 s. Endpoint positions differ by about 0.12
world units. Approximate 27–30 s CSV medians are 16.607 ms and 17.107 ms;
one smoke pair does not establish a tracing benefit or regression.
`tracing-smoke-summary.json` records corrected session identities and captures.
Use complete session IDs, never PID alone, for future collection. Explicit
scene/script-clock alignment and repeated runs remain necessary.

For compiler experiments, all 680 existing generated files were copied into
`.local/non-renderer-optimization/generated` and hashed in `generated-sha256.json`.
Experimental frozen-codegen mode bypasses generator invocation; normal builds
retain dependency-tracked generation. Recomp IPO defaults off and applies only
to the host and generated object/facade targets when explicitly enabled.

CMake IPO capability checking passed. Effective commands confirmed ThinLTO,
SSE4.1 and asynchronous exceptions on all 333 generated C++ files; all 95 runtime
commands remained non-LTO. The ThinLTO commands were saved separately. A full
non-IPO build from that same frozen snapshot is now underway, to establish a
matched compiler baseline before building the IPO variant. Its log is
`.local/non-renderer-optimization/build-frozen-baseline.log`. Neither compiler
variant is qualified yet.

### Corrected baseline configuration

The first full baseline build was stopped after inspection found that reapplying
the standard preset had reset the generated-source paths to `.local/generated`.
Frozen mode still prevented codegen writes, but those objects cannot establish
the intended snapshot baseline. No preview files were replaced.

Reconfiguration now uses `cmake -S . -B out/build/non-renderer-baseline` with
explicit snapshot paths, frozen mode ON and IPO OFF. Effective-command assertions
verified all 326 translated shards use the copied tree and no codegen invocation
exists. The initial assertion also matched the generated target's PCH filename;
it was corrected to check source basenames. The corrected build is running;
use `build-frozen-baseline-corrected.log`, not the interrupted build log.

### Full baseline completed; ThinLTO build started

The corrected full baseline completed successfully and is staged under
`.local/non-renderer-optimization/compiler-baseline/`, including binary hashes,
effective commands and CMake cache. All 680 copied generated files still match
the snapshot manifest. This compiler baseline is distinct from the earlier
trace-on package; do not mix their results or binaries.

| Baseline module | SHA-256 |
| --- | --- |
| Executable | `38e1f94756a100f32c777345e6ff0cc9c12611eff80c71b2e23b1be4c53f3bfa` |
| Runtime | `c6bb0619dd042e1362ea811989d646aa95ab864cd48d164375df4a0f32113dc3` |
| Renderer | `38f56643340179e9b078f9f4aac1975686d3c1b53efbd658f6364d7ca2a1f4d0` |

ThinLTO is now compiling from the same snapshot after reconfiguration without
reapplying the preset. `tools/check-recomp-experiment.py` verified all 326
translated shards retain snapshot paths, SSE4.1 and asynchronous exceptions,
with ThinLTO enabled and no runtime LTO or codegen invocation. Its regression
test rejects preset path resets, unexpected IPO state and enabled codegen.

Validation: `python tools/tests/test_recomp_experiment.py` passed;
`python tools/check-recomp-experiment.py out/build/non-renderer-baseline
.local/non-renderer-optimization/generated --ipo` passed. Candidate compilation
is recorded in `build-thinlto.log`. Full baseline and candidate runtime
qualification and matched performance measurements remain pending.

### Session collection and code footprint

`tools/collect-recomp-session.py` now requires a full session ID and verifies
that the event log names the expected test output, reports completion, and has
no render-test failure before copying its matching CSV. Its reused-PID regression
passed and both real tracing smoke sessions were collected successfully.

Baseline PE `.text` virtual sizes are 96,754,310 bytes for the executable,
9,485,062 for SpeechFacade, and 12,831,910 for XMediaFacade. These are executable
code-section sizes, not resident RAM or measured hot-code working sets. Details
are in `compiler-baseline/sections.json`.

ThinLTO reached its final executable link. A partial observation of linker PID
52464 recorded a peak working set of 1,913,028,608 bytes at that point; this is
neither the complete build peak nor necessarily the final link peak. The raw
observation is in `thinlto-link-observation.json`. Link completion and runtime
results remain pending.

ThinLTO subsequently linked successfully. Its package is staged in
`compiler-thinlto/`. Initial manifest validation caught a changed runtime hash
despite the intended generated-only IPO scope. The candidate package therefore
explicitly reuses the preserved compiler-baseline runtime and renderer DLLs;
their hashes are verified equal. Only the executable and generated facade DLLs
come from the ThinLTO build. The unexpected rebuilt runtime is not used to infer
an IPO benefit. Candidate binary manifests, sections and effective commands are
stored in that package. Runtime smoke and matched benchmarks are still pending.

## Initial compiler gameplay comparisons

The frozen baseline and ThinLTO packages both completed the stationary open-world
script with normal exit and matching settings. Captures were inspected side by
side: both show the same roadside event scene and parked car, without an obvious
large visual difference. This is a smoke check, not full visual or semantic
qualification. Test hardware is Ryzen 7 5800X, RTX 4080, approximately 128 GiB
RAM; device/driver details are saved in `hardware.json`.

Initial 32–43 s cumulative-CSV windows, excluding the capture boundaries:

| Run | Variant | Median frame ms | p95 frame ms |
| --- | --- | --- | --- |
| compiler-a1 | Baseline | 16.610 | 20.518 |
| compiler-b1 | ThinLTO | 19.945 | 25.682 |
| compiler-b2-retry | ThinLTO | 16.989 | 21.115 |
| compiler-a2 | Baseline | 18.401 | 24.887 |

The second ThinLTO run materially differs from the first; no consistent benefit
or regression is established. The reverse-order baseline also varied notably.
All four completed sessions and identical settings hashes are recorded in
`compiler-abba-summary.json`. More attribution and workload coverage are needed;
these results do not justify enabling IPO by default.
The first pair accumulated approximately 11 s of simulation time in each 11 s
window, but this does not establish NPC/UI timing correctness.

An attempted `compiler-b2` exited before gameplay because the wrapper had
pre-created the output folder, which the render-test API rejects. That attempt
is excluded and retained for provenance. The successful retry was initially
misclassified by a wrapper checking PowerShell's stale `$LASTEXITCODE`; its
normal-exit JSON and completed session verify success. Subsequent wrappers
check the launch result and session completion explicitly. Neither issue is
evidence of a ThinLTO game crash.

## PGO collection build

Recomp PGO now has explicit OFF (default), GENERATE and USE build modes. USE
requires an existing merged profile; unsupported compilers and invalid modes
are rejected. GENERATE uses IR instrumentation and atomic counters on the host
and generated game modules, including their final links. Runtime and renderer
are not instrumented in this experiment. IPO is OFF to evaluate PGO separately.

Configuration and effective-command checks passed: all 333 generated C++ files
have generation/atomic-update flags, and all 326 translated shards retain the
frozen source path, SSE4.1 and asynchronous exceptions. The runtime has no PGO
flags. `check-recomp-experiment.py --pgo generate` and its mode-mismatch
regression passed. The actual game collection build is still running; see
`configure-pgo-generate.log` and `build-pgo-generate.log`.

Before longer training, verify nonempty per-module raw profiles on a normal
game exit. Planned collection covers opening video/title, stationary gameplay,
driving and town approach. Reserve different routes/events for validation.
An instrumented run is training evidence, not a performance result. Broad
coverage, profile-use compilation and qualification remain incomplete.

The collection build reached 362/365 completed steps. The remaining main
registration translation unit (`pinyon_shift_register.cpp`) is expensive under
instrumentation: compiler PID 43860 was observed using about 6.12 GB of working
set while its CPU time continued increasing. `pgo-compile-observation.json`
contains a partial process observation, not a complete build peak. The build
remains active and has not been restarted or classified as failed.

Existing scenario contracts were inspected for training selection. Title/video
runs require `RenderTestIncludeOpeningMovies`; skipping movies can leave an
unrepresentative flat title background. The race and map scripts have distinct
scene checks and can provide held-out validation if excluded from training.
Their comments alone do not prove those scenarios executed in a new run.

## Broader process measurements

The pre-existing discovery wrapper has local extensions for `-BuildDirectory`
and `-PerformanceOnly`, allowing its existing CPU/private-memory sampling to
run against isolated packages without enabling renderer corpus discovery.
It fingerprints both facade DLLs as well as the executable/runtime/renderer.
PowerShell parsing and the existing recorder self-test passed; a live isolated
performance-only recording is still required.

The recorder also now samples `GetProcessIoCounters`. Its Windows self-test
verified readable counters and at least 4096 additional write bytes after a
4096-byte file write. Failure is represented as unavailable rather than zero.
These counters account for process I/O operations and transferred bytes, not
physical-disk latency or critical-path wait time. They supplement but do not
replace missing WPR scheduling/I/O attribution. See Microsoft's
[GetProcessIoCounters contract](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getprocessiocounters)
and [counter definitions](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-io_counters).

These extensions are in pre-existing untracked discovery files. They remain
uncommitted to avoid silently including the earlier renderer tooling as new
work in an optimization commit; the starting snapshots distinguish the changes.

## Registration code generation: concrete build-cost candidate

The frozen main registration file is 21,898,245 bytes and contains 419,524
straight-line `SetFunction` calls, including continuation aliases. During the
PGO collection build its compiler process accumulated over 841 seconds of CPU
time and remained active at roughly 6.12 GB working set. This identifies an
expensive translation unit, not a measured LLVM pass-level root cause.

A private probe replaced only that call sequence with a static array of
`{uint32_t address, PPCFunc* function}` entries and a loop. An assertion compared
every address/function pair in order, retaining duplicates and aliases. Using
the actual main registration compile command, PCH and atomic PGO options, the
candidate compiled successfully in 6.746 seconds elapsed; its object is
13,535,116 bytes. The first probe accidentally selected the speech registration
command by basename and failed; the successful probe selects the exact main
source path. See `.local/non-renderer-optimization/probe-registration.py`,
`registration-table-command.txt`, and `registration-table-result.json`.

These are different timing measures under concurrent compilation, so do not
report their ratio as a controlled speedup. Nevertheless, the candidate
completed while the original was still compiling. The baseline snapshot and
active build source were not modified. Runtime implementation inspection shows
that preserving call order retains dispatcher writes and recording order; both
forms ignore the boolean return. Linking, startup correctness, final image
size/relocations and representative timing remain untested. This is a CPU-05
build-cost candidate, not evidence of higher gameplay FPS. Any emitter change
must also preserve DLL exports, below-code-base import filtering, empty-module
behavior and continuation aliases, with the existing registration template
test updated before proposing it for merge.

Follow-up inspection found that `init_cpp.inja` already emits `PPCFuncMappings`
with the same filtering and aliases, terminated by `{0, nullptr}`. The probe's
`--reuse` mode asserts exact equality of all 419,524 entries against that existing
table, then emits only a loop over it. This smaller candidate compiled with the
same main PGO command in 2.380 seconds and reduces registration source to 543
bytes without another table. Prefer this reuse approach if module symbol
ownership and table immutability checks pass. It is still a private compile
probe, not a linked or gameplay-qualified change.

### Main registration exclusion and first actual PGO run

Further caller inspection found no consumer of the main executable's generated
`pinyon_shift_RegisterFunctions`: `Runtime::Setup` already uses the image's
`PPCFuncMappings`. The smaller project-level candidate excludes only the main
registration translation unit from CMake. Both facade registration units and
the main init/table unit remain in the actual compile database. No SDK emitter
change is needed for this candidate. The original compiler was deliberately
stopped after confirming its command/source identity, because this work was
unnecessary, not because an observation timed out. The reconfigured PGO build
linked successfully; the 326-shard isolation check passed.

The staged `compiler-pgo-generate` package pins runtime and renderer to the saved
compiler baseline. Driving session `20260909T060018Z-p39664` completed its capture
and exited with code zero. The exact-session collector passed. This is startup
and short driving evidence for omitting the unused unit; broad qualification
and normal-build checks remain required before recommending merge.

Only two raw profiles were emitted, merging to 9,595 functions and 418,904
blocks. Do not treat this as complete main-plus-facade training. Inspection
found `ReXApp::OnClosing` calls `std::_Exit(0)`, skipping the executable's atexit
profile writer. A PGO-GENERATE-only host hook now calls `__llvm_profile_dump`
at the existing accepted window-close boundary and records its return code.
This API is documented in the [Clang profiling runtime interface](https://clang.llvm.org/docs/UsersManual.html).
It takes a training snapshot before title termination; it does not promise a
globally synchronized final count across still-running guest threads. Counters
are instrumented atomically. The rebuild and a new run must verify the main
profile is emitted before collecting broader training. Initial incomplete
profiles remain separate and are not yet used for optimization.

Verification run `20260909T060316Z-p36708` completed the same driving script and
exited zero. Its exact-session collection passed, and `pgo.profile.dump`
reported result zero. Three nonempty raw files now merge successfully to
87,123 functions and 2,328,110 blocks. Artifacts are in
`compiler-pgo-dump`, `pgo-driving-smoke-02`, and `pgo-training-driving-02`.
This verifies the explicit executable dump fixes the observed missing-profile
problem. It does not establish representative coverage; title/video, town and
held-out validation still remain. No profile-use build has been qualified.

### Expanded training and profile-use build

Title/video session `20260909T060455Z-p28612` and town-approach session
`20260909T060624Z-p50240` both completed and exited zero. Exact-session
collection passed for each. Capture inspection confirmed the Dolby opening
video and the real Ferrari title background; driving/town captures show the
car and HUD on the road. The private `town-training.fh1test` ends before the
original route's map input, preserving map and race as held-out scenarios.
The town endpoint is close to the roadside barrier, so future comparisons
must inspect position/state rather than assume an unobstructed route.

Eight raw profiles from driving-02, title-01 and town-01 merge successfully
into `training-v1.profdata` (87,123 function records, 2,328,110 blocks).
Function records include unexecuted functions; this is not a claim that every
function ran. Title loads only two instrumented modules, while driving/town
produce three profiles. The initial incomplete driving-01 profiles are excluded.
The profile-use build is configured with IPO still OFF, preserving the isolated
PGO experiment. Its 326-shard scope check passed; compilation and held-out
qualification remain pending (`build-pgo-use.log`).

The town run also verified the existing discovery wrapper's isolated
`-PerformanceOnly` mode in a live run. It produced process CPU/private-memory
and I/O samples with the staged package fingerprints and settings preserved.
Final samples can include process teardown (near-zero resident/private memory)
and must be excluded from steady-state analysis. Instrumented training counters
are not an uninstrumented CPU/I/O baseline or a PGO speedup measurement.

### Evidence for the next CPU/runtime investigation

`llvm-profdata show --topn=20 training-v1.profdata` identifies frequent block
execution, not sampled CPU cost. The highest entry is `sub_829F04A8` (maximum
block count 1,348,070,352). Its frozen generated body contains four iterations
of eight `db16cyc` instructions emitted as comments, followed by guest state and
thread-related checks. `sub_82441690`, another frequent function, reads two
guest words through r13. Register-save/restore helpers also occur frequently.
This narrows RT-01/CPU-06 investigation to guest delay/polling behavior and
small cross-shard helpers; it does not justify changing scheduling or declaring
these functions CPU bottlenecks without timing evidence. Preserve continuation
entry semantics and guest state when considering any replacement.

The private `summarize-run.py` reports frame and process windows separately
because cumulative CSV frame time is not exact process-sample alignment.
In the instrumented town 32–42 second window, nine process samples span
32.61–41.05 seconds and average 5.28 CPU core equivalents; median private memory
is 5.01 GB. I/O deltas include 18.43 MB read and 22.20 MB written. The CSV window
has zero recorded XMA stall/recovery and critical-region-contention counts and
10.002 seconds of simulation time. These values validate usable measurements;
they are not baseline requirements, physical disk traffic, proof of no audio
problem, or a reason to skip uninstrumented paired runs. See the run's
`measurement-summary.json` for all fields and clock caveat.

The profile-use build completed successfully and is staged as `compiler-pgo-use`
with the baseline runtime/renderer hashes. Its executable is 99,198,976 bytes
(SHA256 `1082b56bb21abf396b07d1cbd55e29f37f818a418ab1ea49b994ef44f3440778`).
Do not attribute the entire size difference to PGO: the old compiler baseline
still compiled the unused main registration unit. A final matched non-PGO
rebuild should include its removal too.

The build reports one profile hash mismatch for `OnWindowCloseRequested`, whose
training-only explicit dump intentionally changes its control flow (up to nine
counts discarded). No guest-function profile mismatch appeared in the checked
log. This shutdown-only mismatch is recorded rather than hidden or suppressed.
Held-out map comparison has started using the performance-only recorder.

Baseline map session `20260909T061152Z-p47992` exited normally and passed
exact-session collection; the map capture visibly shows the map rather than
free roam. The script holds it only briefly: the 16.8–18.8 second process
window contains two samples spanning 1.06 seconds. Treat this as a scene and
measurement smoke check, not a stable CPU benchmark. `map-summary.json`
preserves the limited measurements.

The first PGO map launch was refused because a separate regular-preview game
(PID 14028, original Release path) was running. No second game was started and
the existing process was left alone. Meanwhile a matched non-PGO build, with
the unused main registration unit excluded just like the candidate, is running
with four compiler jobs (`build-matched-baseline.log`). The actual compile
database passes the 326-shard OFF-mode isolation check. The saved original
baseline and PGO packages remain available independently of this build tree.

The matched non-PGO build completed successfully and is staged independently as
`compiler-matched-baseline`. Both packages have identical runtime and renderer
hashes. Matched executable sizes are 101,242,368 bytes OFF and 99,198,976 bytes
USE: approximately 2.02% smaller with PGO. The old baseline was 108,432,896
bytes, so its combined reduction must not be attributed entirely to PGO.
The matched baseline map run `20260909T061856Z-p41396` exited normally; PGO's
matching map run is now underway. Scene and performance qualification remain
separate from this verified build-size comparison.

Matched PGO map session `20260909T061944Z-p48828` exited normally. Both map
sessions passed exact-session collection and used byte-identical settings.
The map image's mean absolute channel difference is 0.997 on the 0–255 scale.
Free-roam/return differences are 10.71/17.46 with differing vehicle positions;
do not mislabel those moving-scene differences as a compiler rendering defect
or treat the images as pixel-equivalent correctness proof.

Matched baseline race session `20260909T062031Z-p2304` exited normally. The
existing `first_race_hud_summary` check passed on `race-moving`, and visual
inspection confirms the car on track with lap 1/2, place 8/8 and the standings
HUD. The event-menu capture also identifies Recaro Rush. This verifies the
held-out scenario actually entered a race. The matching PGO race is running;
paired performance conclusions remain pending.

PGO race session `20260909T062220Z-p50776` exited normally, passed exact-session
collection and the existing race HUD check, and visually reached the track.
Settings match baseline byte-for-byte. Vehicle-position differences are below
0.05 world units through race-ready and 0.237 at race-moving. NPC animation and
the standings highlight differ between captures; these short stills do not
qualify animation timing or audio.

First matched race pair, cumulative CSV window 70–75 seconds:

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| OFF a1 | 26.030 | 110.526 | 119.631 | 3.031 |
| USE b1 | 22.705 | 118.849 | 124.957 | 3.014 |

Both process estimates use only five samples over roughly 4.15 seconds and
their clock is separate from cumulative CSV time. Both CSV windows report zero
invalid simulation deltas/XMA stall recoveries and about 5.05 seconds of
simulation. This pair shows mixed frame metrics and nearly unchanged process
CPU, not a reproducible PGO win. The high tails recur in both variants. Reverse
order repetition has started (`matched-race-b2`); retain per-run results and
do not pool frames to conceal run-level uncertainty.

The reverse-order pair completed normally and passed exact-session collection
and race HUD checks: USE b2 `20260909T062400Z-p46712`, then OFF a2
`20260909T062534Z-p51312`. Same 70–75 second summary:

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| USE b2 | 22.296 | 107.667 | 124.629 | 2.911 |
| OFF a2 | 23.634 | 119.138 | 135.263 | 2.887 |

Across the first four runs PGO has lower medians, inconsistent tail improvement
and no consistent process CPU reduction. A third pair is underway. Retain the
short five-sample CPU-window limitation when interpreting small differences.
Inspection of the first three CSVs groups 20–25 frames above 80 ms per window;
their GPU timing samples average roughly 40–44 ms. Recorded command-buffer
stalls, readback wait time and memexport fence waits are zero in those groups.
This shows substantial concurrent GPU cost, not complete CPU/GPU critical-path
attribution, and zero specific counters do not prove absence of other waits.
Raw grouped evidence is in `race-tail-counters.json`.

Third pair completed normally: OFF a3 `20260909T062718Z-p53052`, USE b3
`20260909T062852Z-p2656`. All six runs pass exact-session collection, race HUD
checks and byte-identical settings comparison. Final pair:

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| OFF a3 | 23.790 | 108.524 | 137.264 | 2.988 |
| USE b3 | 23.859 | 122.669 | 149.849 | 3.168 |

**PGO disposition for this training corpus and configuration: leave OFF by
default.** Two lower medians followed by a slight regression, inconsistent
tails and no consistent CPU reduction do not establish a runtime benefit.
The roughly 2% executable-size reduction is real but does not establish lower
RAM/GPU requirements. `matched-race-six-runs.json` retains all run-level metrics.
This is a bounded negative result for the current experiment, not a claim that
PGO cannot help another corpus, CPU-bound setting or combined LTO build.
Do not broaden into a flag sweep without new attribution evidence.

CPU-02 repeated evaluation has started with `trace-stationary-a1`. Before
launch, hashes confirmed the tracing packages differ only in `rexruntime.dll`
among the five game modules (`trace-pair-module-check.json`). These packages
are a separate comparison from the compiler packages and must not be mixed
into their performance results.

First tracing stationary pair completed normally with exact-session collection:
ON a1 `20260909T063042Z-p52704`, OFF b1 `20260909T063150Z-p52612`.
The ON endpoint capture shows the stationary car at the Recaro Rush event.
The 32–43 second CSV/process summaries are:

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| Trace ON a1 | 17.145 | 21.502 | 23.896 | 3.267 |
| Trace OFF b1 | 16.688 | 21.547 | 25.319 | 3.234 |

Each process estimate has 11 samples over about 10.48 seconds. Both windows
report approximately 11 seconds of simulation and zero recorded invalid
simulation deltas/XMA stalls/recoveries. This first pair is mixed and cannot
justify disabling import reachability diagnostics. Reverse-order repetition
is underway (`trace-stationary-b2`).

Reverse tracing pair completed normally with exact-session collection: OFF b2
`20260909T063255Z-p48520`, ON a2 `20260909T063359Z-p24608`.

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| Trace OFF b2 | 16.777 | 21.556 | 29.510 | 3.248 |
| Trace ON a2 | 16.642 | 20.784 | 24.179 | 3.202 |

The first three runs have byte-identical settings and endpoint coordinates
within 0.001 world units, with no vehicle motion between their captures. The
reverse pair does not reproduce an advantage for tracing OFF; ON a2 is better
on all four listed metrics. A third pair is underway. Do not choose a default
from the first favorable pair or discard this negative replication.

Final tracing pair: ON a3 `20260909T063506Z-p38620`, OFF b3
`20260909T063609Z-p32252`; both exited normally and passed exact-session
collection. All six settings files are byte-identical.

| Run | Median ms | p95 ms | p99 ms | Process CPU core equivalents |
| --- | ---: | ---: | ---: | ---: |
| Trace ON a3 | 17.140 | 22.471 | 25.382 | 3.218 |
| Trace OFF b3 | 16.536 | 20.784 | 24.843 | 3.449 |

**CPU-02 disposition: retain tracing ON by default.** OFF has small median wins
in two pairs, loses the reverse pair, and has no consistent CPU or tail benefit.
Keep the OFF build control for controlled diagnostics experiments, not as a
qualified performance preset. Full run-level results are `trace-six-runs.json`.

A private `thread-snapshot.ps1` probe uses .NET thread CPU totals and Win32
thread descriptions with query-only handles; thread/process creation timestamps
allow rejection of ID reuse. Its live own-process check returned thread times
without errors. It does not suspend threads or modify scheduling. A separate
game attribution run is still required. These totals identify CPU consumption
by thread, not instruction stacks, wait duration or critical-path causality.
See [Microsoft's thread timing contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getthreadtimes).

### Live thread CPU attribution

Separate stationary baseline session `20260909T063808Z-p37796` exited normally
and passed exact-session collection. Two query-only snapshots during gameplay
span 10.052 seconds. The matched thread CPU deltas sum to 33.75 CPU-seconds,
equal to the process delta, with creation timestamps checked against ID reuse.

| Thread description | CPU seconds | Share of process CPU |
| --- | ---: | ---: |
| XThread9D5C (F8001174) | 9.516 | 28.2% |
| GPU Commands (F8000018) | 8.875 | 26.3% |
| XThreadCC50 (F8000054) | 5.969 | 17.7% |
| XThread3BE0 (F80012D0) | 2.516 | 7.5% |
| XThread76EC (F8001338) | 1.281 | 3.8% |
| rex::thread::TimerQueue | 0.906 | 2.7% |

Artifacts: `thread-attribution-01/threads-before.json`, `threads-after.json`,
and `thread-deltas.json`. Thread descriptions identify objects, not guest
entry-point addresses. Existing logs associate the highest CPU guest thread
with the opening-movie path and another with a cleanup event, but those isolated
events do not identify what those threads execute during this measurement.
Do not equate their CPU totals with the frequent polling function's cost.
Two instantaneous thread states also cannot establish wait duration.

This narrows CPU-01: command processing and guest execution both matter in this
stationary scene. I/O critical-path attribution is still missing; the next
useful measurement is synchronous read duration by thread, not more compiler
flag combinations. The snapshot overhead belongs to this separate attribution
run and is excluded from the six-run performance comparisons.

### Synchronous-read duration probe

An opt-in `profile_guest_file_reads` cvar (default false) times the actual
`XFile::Read` call inside `NtReadFile_entry`, logging after the timer ends.
It preserves the existing result, byte count, APC and event handling. The
isolated runtime built successfully. The discovery wrapper can now append
JSON-specified game arguments, and its log archive recognizes `IO_PROFILE`.
These are diagnostic edits, not a faster I/O implementation.

Town session `20260909T064157Z-p37956` completed and exited normally; exact-session
collection passed. The first recorder process predated the new archive filter,
so its complete runtime log was copied immediately after exit and parsed only
inside the matching `logging.ready` PID boundary. Artifacts are in
`io-attribution-town-01/runtime-capture.log` and `read-duration-summary.json`.

- Whole run: 4,538 reads, 189,552,853 returned bytes, 91.103 ms total measured
  duration across threads; maximum 6.586 ms, three reads above 1 ms, none above
  10 ms.
- Local logger interval 00:42:29–00:42:39 (approximately run seconds 32–42):
  161 reads, 4,395,347 returned bytes, 2.471 ms total, maximum 98 microseconds.

**IO-02 disposition: defer asynchronous/coalesced read changes.** This
warm-cache town sample does not support synchronous read duration as the cause
of large frame stalls. It does not qualify cold disks or exclude costs outside
the timed call (object lookup, file open/stat, decompression, other read paths).
Per-read logging adds overhead outside the measured interval, so this run must
not be used as a performance baseline. The default-off branch and full
save/APC behavior still require normal-build regression review before retaining
the diagnostic as a mergeable change; the probe alone justifies no runtime
I/O rewrite. Recorder self-test and diff whitespace checks passed.

The diagnostic's default-off session `20260909T064407Z-p46380` completed
normally and passed exact-session collection. Parsing its matching runtime-log
session found no `IO_PROFILE` lines. This verifies the off path and command-line
opt-in behavior in actual gameplay, not broad save/APC correctness under every
error condition. Reviewable patches for the diagnostic and inherited tooling
are preserved under `tools/experiments/`, with prerequisite identities and
application instructions. They passed reverse-application checks against the
tested working files; unrelated renderer/SDK edits remain separate.

### ThinLTO final repetition

The third original-baseline/ThinLTO pair completed normally and passed exact
session collection: OFF `20260909T064540Z-p5936`, ThinLTO
`20260909T064645Z-p44508`. The config hash still matches the earlier four runs
(`e267dcac701a0e14a92df00aa059c2fb639d5a0b32b7d3dc279a00a5c974afc7`).
The original direct-launch/performance-CSV method was retained, without the
additional discovery recorder. In the same 32–43 second CSV window:

| Run | Median ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: |
| OFF a3 | 17.019 | 21.220 | 25.063 |
| ThinLTO b3 | 16.361 | 20.896 | 26.140 |

**CPU-03 disposition: leave IPO OFF by default.** This final modest median win
does not resolve the earlier inconsistent pairs or establish stable tail/CPU
improvement. The code-footprint reduction remains valid; it is not evidence of
lower hardware requirements. `compiler-third-pair.json` retains this pair.

## Merge recommendation and remaining audit gaps

Recommend the narrow exclusion of the unused main registration translation
unit in `cmake/PinyonShiftRexGlue.cmake`. It removes a verified expensive compile
and about 7.19 MB from the non-PGO executable in these builds; the entrypoint
still registers through `PPCFuncMappings`, and facade registration is retained.
Normal builds, map checks and repeated races exercised the resulting package.
This is a build/footprint improvement, not a demonstrated gameplay FPS gain.
It is currently part of `bd79dea` alongside the training-profile exit fix;
reviewers wanting only the exclusion should take just that CMake hunk.

The default-off IPO/PGO controls, exact-session collector and frozen-build
checker are useful experiment infrastructure, not production optimization
presets. Keep trace logging ON, IPO OFF and PGO OFF. Do not merge the diagnostic
patches as performance fixes; their README records prerequisite work and their
on/off smoke checks. No SDK pointer update, remote merge or release was made.

Final checks so far: both compiler package isolation checks and collector/
checker regression tests pass; both saved diagnostic patches pass reverse
application checks; committed patch bytes match the checked files; all 680
frozen generated files match their initial hashes. Existing dirty renderer work
was neither reverted nor swept into the experiment commits.

The objective remains open at this audit. Thread CPU totals and two state
snapshots do not establish scheduling wait durations, and the warm read-call
probe does not cover open/stat latency or cold storage. Those are explicitly
weaker than complete scheduling/I/O attribution. The runtime flag experiments
have measured dispositions; their negative results do not fill these remaining
measurement gaps or qualify broad animation/audio correctness. No lower
hardware requirement is claimed.

### Open/create and failed lookup duration

The same default-off I/O flag now also times the shared VFS `OpenFile` call in
`NtCreateFile_entry` (also used by `NtOpenFile_entry`). The timer includes VFS
resolution/open work but excludes the later guest handle allocation. Both
success and failure durations are logged after measurement. The isolated
runtime rebuilt and town session `20260909T065216Z-p52436` completed normally,
passed exact-session collection and was archived with the new recorder filter.

- Whole run: 1,203 open/create calls, 108.276 ms summed duration, maximum
  438 microseconds. Ten failures total 543 microseconds; only one failed path
  repeats, twice.
- Run seconds 32–42: 47 calls, 5.496 ms total, maximum 227 microseconds,
  no failures.

`io-open-town-01/open-duration-summary.json` preserves the counts, longest calls
and repeated failures. This warm sample does not support repeated VFS misses
or open latency as a large-stall cause. Together with the read probe it supports
deferring an asynchronous/coalescing/cache rewrite; it does not characterize
cold media or unrelated metadata syscalls. The diagnostic patch was refreshed
and passed reverse-application validation. Scheduler wait duration remains an
open attribution requirement; this I/O result does not close it.

### Guest-object wait timing coverage and observer overhead

An opt-in `profile_guest_object_waits` wrapper now times the shared single,
signal-and-wait, wait-any and wait-all host calls in `XObject`, preserving their
existing callbacks, timeout conversions, termination checks and return mapping.
The initial exact helper check verified one callback invocation, scalar/pair
results and exception propagation with profiling enabled and disabled. The
isolated runtime built and town session `20260909T065454Z-p25040` completed
normally with exact-session collection.

All four wait types appeared. However, the initial per-call logger emitted
696,443 single-wait records alone, making this unsuitable as a low-overhead
scheduling baseline. Its sums include concurrent waits and long idle waits
completing at shutdown; they are not CPU time or frame stall duration. Preserve
`wait-town-01/wait-duration-summary.json` as coverage/observer-cost evidence,
not a timing recommendation.

The probe now aggregates per thread and call site, reporting after 1,024
completions or one second observed at a completion. The aggregate version built;
its updated helper check and gameplay repetition remain pending. Partial
buckets at hard exit and waits that never return are unreported and must be
acknowledged in analysis. This is instrumentation, not a scheduler optimization.

The updated exact-helper check passed scalar/pair return, single invocation,
exception propagation, both flag modes and the 1,024-completion aggregation
threshold. Town session `20260909T065802Z-p51336` completed normally and passed
exact-session collection. It reports 938,963 completed calls in 1,608 aggregate
records rather than roughly one line per call. All four wait types remain
represented. Artifacts: `wait-town-02/wait-aggregate-summary.json`.

Buckets reported during run seconds 32–42 contain 286,353 single waits with
163.004 seconds summed duration across threads, 3,766 wait-any calls with
10.041 seconds, three signal-and-wait calls with 1.166 seconds, and 62 wait-all
calls totaling 247 microseconds. These are **completion-bucket totals**, not
wait time confined to the interval: calls can start earlier and many threads
wait concurrently. Long idle waits complete at shutdown. Do not add these
durations to CPU time or claim that eliminating them would improve frame time.

This supplies a bounded guest-object wait baseline alongside the thread CPU
and I/O measurements. It does not replace an OS ready-time/context-switch trace
or determine which producer a wait depends on. No scheduler change is justified
from these totals; RT-01 remains explicitly deferred. The profile is archived
as a separate SDK patch and the recorder patch recognizes its aggregate lines.
Default-off gameplay verification is running before final review.
