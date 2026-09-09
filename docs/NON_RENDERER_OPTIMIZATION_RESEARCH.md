# Optimization research beyond the native renderer

Research date: 2026-09-08 (Mexico City). Scope: the current Windows x64 recomp, its generated CPU code, compiler/linker pipeline, and host runtime.

## Recommendation

Start with a short CPU attribution pass, then test diagnostic overhead, ThinLTO, and profile-guided optimization (PGO). These are concrete opportunities in the current build. Investigate streaming stalls alongside them: the guest file-read implementation currently performs reads synchronously even for asynchronous guest requests.

The larger CPU opportunity is reducing the work performed by generated PPC code and its runtime boundaries. Pursue that through measured hot functions, existing codegen options, and narrowly verified native replacements. A compiler flag alone will not remove guest synchronization, redundant copies, or unnecessary work.

Keep this work separate from the [native resource migration checklist](native-renderer/NATIVE_RESOURCE_MIGRATION_CHECKLIST.md). Both programs can lower requirements, but they address different bottlenecks. Rendering approximations are not a license to approximate physics, timing, file completion, or save behavior.

**No optimization was implemented or benchmarked for this report.** The findings below combine local source/build inspection with primary documentation. Priorities are engineering judgments, not measured speedup estimates.

## 1. Evidence and current baseline

The inspected checkout is based on project commit `f4c39de29fb456a0a258fb18d04c45347d573e06` and ShiftGlue commit `6db74f6de0230727358d93f8a221f40fbba6a792`, with substantial local changes. These hashes alone do not reproduce the working tree. Effective commands were inspected in `out/build/win-amd64-release/build.ninja` and configuration in its `CMakeCache.txt`; they describe that configured build, not proof of the exact binary used in every prior playtest.

The [August performance assessment](PERFORMANCE_RENDERER_ASSESSMENT.md) remains historical evidence. Its renderer state and FPS discussion should not be treated as the September baseline. The more recent [discovery findings](native-renderer/DISCOVERY_FINDINGS_2026-09-08.md) and marked routes are better starting points for matching workloads.

| Area | Verified current state | Consequence |
| --- | --- | --- |
| Toolchain | Release tooling pins LLVM 20.1.8; the configured consumer uses `clang++.exe` and `lld-link`. | Use Clang/COFF experiments, not a recipe assuming MSVC `cl.exe` or ELF. |
| Optimization | Effective Release flags already contain `-O3 -DNDEBUG`. | “Enable release optimizations” is already done. |
| CPU baseline | SSE4.1 is explicit in presets and enforced by integration. | Global AVX2 or `-march=native` would change the supported hardware contract. |
| LTO/PGO | No `-flto`, `-fprofile`, or `/LTCG` markers in the inspected Ninja build. | These are available experiments, not existing gains. |
| Target boundaries | Main generated code is an object library linked into the executable; SpeechFacade and XMediaFacade are separate DLLs, alongside the shared runtime. | Optimization scope must follow actual final link units. |
| Generated code | Main: 263 top-level C++ files, 292.49 MiB; speech: 28, 28.21 MiB; xmedia: 42, 41.01 MiB. | Build scalability and generated code quality matter. Source bytes are not executable size or resident memory. |
| Exceptions/debug data | Generated targets use asynchronous exceptions and line-table debug information, with target PCHs. | Preserve exception semantics and match PCH options when changing flags. |
| Diagnostics | Tracy is forced off; performance counters are enabled; `rexruntime` defines `REXGLUE_TRACE_IMPORTS=1`. | Audit actual remaining instrumentation instead of proposing to disable Tracy. |
| Dispatch | Generated indirect calls already have a module-local table path and a global fallback. Direct tail calls and module-local thunk reuse are already ported. | A new generic dispatch cache would duplicate existing work unless profiling identifies a missing case. |
| Host filesystem | Entries are cached in a tree; missing entries try an exact stat before a directory scan. | The older advice to avoid enumerating directories on every successful open is partly implemented. |
| Scheduling | Guest affinity and priority restrictions are ignored by default. | “Unpin the guest threads” is not automatically a new optimization. |

Local build evidence: [root CMake](../CMakeLists.txt), [presets](../CMakePresets.json), [integration](../cmake/PinyonShiftRexGlue.cmake), [toolchain pin](../config/release-toolchain.json), [module manifest](../config/rexglue/pinyon_shift_manifest.toml), [SDK CMake](../thirdparty/shiftglue-sdk/CMakeLists.txt), and [historical patch dispositions](../config/rexglue/PATCH_DISPOSITIONS.md).

### A compiler-semantics discrepancy to resolve first

The effective SDK runtime and core compile commands include `-fno-strict-aliasing -ffp-model=strict`. The inspected main generated-code command does **not** include those flags; it has `-O3`, SSE4.1, asynchronous exceptions, and line tables. Directory-scoped SDK options do not automatically apply to the parent project's targets.

This is a reason to audit the effective floating-point and aliasing contract, not a demonstrated bug or an instruction to copy flags everywhere. Generated code uses PPC context helpers and explicit SIMD operations; their semantics, included pragmas, and compiler IR also matter. Establish which operations require dynamic rounding, exception behavior, and alias-safe access before changing their compilation. Clang documents that its floating-point modes govern these assumptions. [Clang 20 floating-point behavior](https://releases.llvm.org/20.1.0/tools/clang/docs/UsersManual.html#controlling-floating-point-behavior).

## 2. Measure the limiting work, not only FPS

For this project, the useful question is: **what delayed the next useful game frame in this marked interval?** A thread can be executing expensive instructions, ready but unscheduled, waiting for another thread, waiting for disk, or waiting for the GPU. Those require different fixes.

Use existing discovery markers and frame-time output as the timeline. Add a short CPU sampling capture and, where available, context-switch/wait and file-I/O attribution. Windows Performance Analyzer distinguishes sampled CPU analysis from scheduling analysis using precise CPU events; use both when diagnosing waits. Verify symbols resolve to this build before interpreting stacks. [Microsoft CPU analysis](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/cpu-analysis).

Capture these scenes separately:

1. Title screen and transitions, including NPC/UI timing checks.
2. Stable general driving, where the user reported approximately 70 FPS.
3. The marked town/outpost and other slowdown routes, including entering and leaving the area.
4. A race with traffic and audio activity, plus menus and transitions back to gameplay.
5. A cold launch/load and a repeated warm traversal. Label cache state rather than combining them.

Record CPU time by module/thread, useful-frame intervals, p50/p95/p99 frame time, stalls above 33/50/100 ms, GPU duration, process commit and working set, file-read latency, and existing audio/deadline counters where available. Some of these require a short diagnostic capture rather than the default recorder. Keep resolution, render scale, presentation cap, save, route, and scene settings fixed.

For changes to instrumentation, retain an independent frame observer: counters that disappear in the candidate cannot be used as proof that the candidate does less work. For compiler changes, retain symbols separately and identify every loaded executable/DLL by hash. Do not compare a newly compiled executable with an accidentally stale runtime DLL.

The initial output should be a one-page attribution table: subsystem, critical-path time, evidence, and next experiment. If GPU time still sets the frame interval, CPU improvements may reduce power or improve headroom without increasing FPS.

## 3. First inexpensive experiment: diagnostic overhead

There are two specific costs to test.

**Import reach tracing.** `REX_TRACE_IMPORT_REACH` uses a function-local atomic flag. It logs only the first arrival, but executes `test_and_set(memory_order_relaxed)` on every invocation. The Release runtime enables it. Relaxed ordering does not remove the read-modify-write operation. [Import hook implementation](../thirdparty/shiftglue-sdk/include/rex/hook.h), [runtime target configuration](../thirdparty/shiftglue-sdk/src/system/CMakeLists.txt).

**Counters.** `IncrementCounter` performs two atomic `fetch_add` operations, for current and total counts. The counters live in shared arrays. Contention or cache-line sharing is plausible when hot counters are updated by multiple threads, but has not been measured here. Generated indirect-dispatch instrumentation also has a separate profiling guard, so do not assume every guest function call increments these counters in the current build. [Counter implementation](../thirdparty/shiftglue-sdk/src/core/perf/counter.cpp), [counter definitions](../thirdparty/shiftglue-sdk/include/rex/perf/counter.h).

Experiment order:

- Compare the current build with import-reach tracing compiled out, retaining useful frame measurements.
- If that matters, make expensive reachability tracing a discovery option; preserve actionable crash/error reporting.
- Separately test hot counter categories. Batch or make a counter thread-local only if it has measurable cost and its aggregation semantics permit it.
- Check optional route/save tracing and log formatting at actual call sites. Several project hooks already have environment gates; their existence is not evidence that they are active.

This is a high-priority experiment because it is small and attributable. It could return no meaningful gain. Avoid building a replacement telemetry framework before that comparison.

## 4. ThinLTO: the first compiler experiment

ThinLTO allows cross-translation-unit analysis and selective importing while avoiding monolithic full-LTO processing of all code at once. LLVM documents Windows `lld-link` support, backend job controls, and an incremental cache. Relevant knobs include `-flto=thin`, `/opt:lldltojobs=N`, and `/lldltocache:<path>`. [LLVM 20 ThinLTO](https://releases.llvm.org/20.1.0/tools/clang/docs/ThinLTO.html).

For this project, begin with the main generated object target and its final executable link. Then evaluate the runtime and facade DLLs as separate link units. Compiling only the launcher with LTO would miss most translated code; adding the flag only at link time cannot recover LLVM IR from every existing native object.

Use an isolated build directory and preserve the known-good package. Keep existing exception, CPU-baseline, CRT, debug, and PCH settings. Bound linker concurrency because the generated source inventory is large. Record clean and incremental build times, peak build memory, executable `.text` size, and runtime results separately.

CMake can check IPO support before enabling target properties, but the result still needs effective-command inspection: a successful capability check does not establish the intended ThinLTO scope for this project. [CMake CheckIPOSupported](https://cmake.org/cmake/help/latest/module/CheckIPOSupported.html).

Limitations matter here. DLL boundaries remain; exported/address-taken functions and the generated weak/noinline entry scheme can constrain optimization. The PCH's tail-call implementation and context synchronization must survive the transformation. LLD supports Windows exception handling, but that is not a substitute for this project's continuation and module-lifecycle tests. [LLD Windows support](https://releases.llvm.org/20.1.0/tools/lld/docs/windows_support.html).

**Keep criterion:** reproducible improvement in CPU time, tail latency, memory, or another declared objective, with no behavioral regression. A smaller binary or faster link alone is not evidence of a faster game.

## 5. PGO: use broad playtesting to optimize CPU code

PGO is particularly interesting because generated code contains many branches and functions whose actual execution frequency is game-dependent. Clang's IR instrumentation route uses `-fprofile-generate` during collection and `-fprofile-use` when building the optimized candidate. Collection is instrumented; the final candidate should be measured separately. Multi-threaded collection can use `-fprofile-update=atomic`, with additional training overhead. [Clang 20 PGO](https://releases.llvm.org/20.1.0/tools/clang/docs/UsersManual.html#profile-guided-optimization).

This would complement the user's discovery sessions, but the existing GPU corpus and frame CSVs are **not compiler profiles**. A dedicated instrumented build must collect `.profraw` data first.

### Proposed project workflow

1. Select a stable codegen/runtime revision and a qualified compiler baseline, preferably after the diagnostic experiment.
2. Instrument the relevant executable and DLL targets, including their final links and profile runtime support. Check that each module produces nonempty data and distinguish its output using a binary-signature/process pattern such as `%m-%p` in `LLVM_PROFILE_FILE`. The profiling runtime's filename substitutions are documented in [Clang's profile collection guidance](https://releases.llvm.org/20.1.0/tools/clang/docs/SourceBasedCodeCoverage.html#running-the-instrumented-program).
3. Collect explicit sessions for startup, ordinary driving, slowdown towns, races, menus, speech/video, and loading. Check profile writing on a normal exit before asking the user for hours of play.
4. Merge profiles with the matching LLVM toolchain, inspect coverage and mismatch warnings, then compile a separate profile-use build.
5. Validate on routes and events held out from training. Keep the startup and facade paths in the qualification set even if they are not dominant in driving.

`llvm-profdata merge` combines execution counts; a long session naturally outweighs a short one. Weighted inputs can adjust the mixture. Therefore, document the actual training mix instead of claiming that one startup run and two hours of driving have equal influence. [LLVM 20 llvm-profdata](https://releases.llvm.org/20.1.0/docs/CommandGuide/llvm-profdata.html).

A minimal experiment matrix is baseline, ThinLTO alone, PGO alone, then their combination if each deserves further investigation. Do not immediately multiply it by every optimization level and CPU architecture. Profiles should be retrained after significant regenerated-code or runtime changes; successful compilation with stale profile warnings is not a release qualification.

**Expected type of benefit:** potentially lower CPU instruction cost and better hot-code decisions, particularly on CPU-limited scenes. No project-specific percentage is defensible yet. Training success and performance success are separate gates.

## 6. Generated CPU code and code size

### Test `-O2` against `-O3` where code is actually hot

There are approximately 362 MiB of generated C++ across the three modules. That makes instruction footprint a reasonable hypothesis, but source size does not establish an instruction-cache bottleneck. Compare `.text` size, hot-function disassembly, CPU samples, and instruction-cache/front-end counters where the hardware profiler provides them.

An `-O2` experiment on generated code can be worthwhile if `-O3` produces excessive expansion or unrolling. Keep runtime settings otherwise identical. An isolated `-Os` experiment belongs on measured cold or oversized code, not as the initial global setting. Do not remove line tables merely to shrink a download and report that as a runtime optimization.

### Use compiler remarks before rewriting SIMD

Clang already has loop and SLP vectorizers. Optimization remarks such as `-Rpass-missed=loop-vectorize`, `-Rpass-analysis=loop-vectorize`, and `-fsave-optimization-record` can identify blocked transformations. Apply them to sampled hot translation units so the output remains usable. [LLVM 20 vectorization documentation](https://releases.llvm.org/20.1.0/docs/Vectorizers.html).

A useful result is an identified helper whose repeated loads, byte swaps, or aliasing prevent optimization, supported by emitted assembly. “Enable vectorization” is not a specific project change. Prefer an existing native primitive or a better emitter pattern over handwritten assembly.

### Register localization and narrower guest boundaries

The SDK exposes `ctr_as_local`, `xer_as_local`, `cr_as_local`, non-argument/nonvolatile localization, and LR/MSR options. The inspected configuration defaults are conservative, and the project's TOML files do not explicitly enable the searched localization options. Confirm the merged configuration and generated output before treating any option as newly available.

XenonRecomp describes similar options and recommends deferring them until a recompilation runs successfully. This demonstrates a relevant technique, not that every option is safe for FH1. [XenonRecomp optimization configuration](https://github.com/hedge-dev/XenonRecomp#optimizations).

FH1 has specific constraints: setjmp/longjmp hooks, restored continuations, reentry, and SEH funclets sharing nonvolatile state. The SDK already suppresses nonvolatile localization for shared-register functions, and prior direct-tail-call work preserves publication to those funclets. [Codegen configuration](../thirdparty/shiftglue-sdk/include/rex/codegen/config.h), [register access generation](../thirdparty/shiftglue-sdk/src/codegen/builders/context.cpp), [main analysis](../config/rexglue/analysis/main-xex.toml), [patch dispositions](../config/rexglue/PATCH_DISPOSITIONS.md).

Start with a sampled hot function or register class, inspect context load/store traffic, and verify normal calls, indirect callbacks, tail branches, and unwind/reentry behavior. Add the smallest focused codegen regression that demonstrates the preserved state. Do not globally skip LR updates or remove asynchronous exceptions to obtain a flattering benchmark.

### Native replacements and indirect calls

The runtime already supplies native CRT memory hooks using `std::memcpy`, `std::memmove`, and `std::memset`. Verify which hot guest implementations are actually recognized and routed to them; the existence of a hook is not proof of coverage. [Native memory hooks](../thirdparty/shiftglue-sdk/src/kernel/crt/memory.cpp).

Good candidates for additional replacements are proven bulk operations with clear input/output semantics. Verify overlap, alignment, endian representation, return values, guest register effects, faults, and memory-write notifications. Prefer byte-identical output for non-renderer processing. A guest allocator or decompressor replacement is a substantially larger contract than a memcpy mapping.

For indirect calls, measure local table hits versus fallback resolution first. The generated fast path already performs a table lookup. Global fallback improvements matter only if misses/cross-module calls are frequent and costly. Preserve caller-module ownership, dynamic module unload, and interior-PC continuation behavior. [Function dispatcher](../thirdparty/shiftglue-sdk/src/system/function_dispatcher.cpp).

## 7. Streaming and filesystem work

### Verified limitation: asynchronous guest reads block in the host path

The inspected `NtReadFile_entry` explicitly takes `if (true || file->is_synchronous())`, invokes `XFile::Read`, and can subsequently report pending status for an asynchronous file. `XFile` holds a per-file mutex around the synchronous read. The Windows file handle is opened without `FILE_FLAG_OVERLAPPED`; its `OVERLAPPED` argument supplies an offset but does not make the handle asynchronous. [Guest read entry](../thirdparty/shiftglue-sdk/src/kernel/xboxkrnl/xboxkrnl_io.cpp), [XFile read path](../thirdparty/shiftglue-sdk/src/system/xfile.cpp), [Windows file handle](../thirdparty/shiftglue-sdk/src/core/filesystem_win.cpp), [Microsoft I/O semantics](https://learn.microsoft.com/en-us/windows/win32/fileio/synchronous-and-asynchronous-i-o).

This is a real architectural opportunity, **not a diagnosis of the marked town slowdown**. Reads may already occur on a guest worker, data may be cached, or graphics work may dominate those frames. Correlate blocked read stacks, disk latency, file-lock contention, and useful-frame gaps first.

If confirmed, choose the smallest asynchronous implementation that preserves the guest contract. Existing host workers may suffice; a new I/O framework is not the starting requirement. Completion must retain the file and destination lifetime, update status/byte counts before signaling, deliver APCs on the correct guest mechanism, preserve offsets and error behavior, and handle shutdown safely.

The read path also explicitly handles physical guest memory and triggers invalidation callbacks after writes. Moving a read to another thread must preserve that ordering. Changing just the Win32 open flag or returning pending earlier would be incomplete.

### Smaller filesystem candidates

The host device already uses an entry tree and an exact-name stat before its case-insensitive fallback scan. A genuine missing path can still scan a directory, and VFS resolution holds a global critical region. Count repeated misses, directory enumerations, path-normalization work, and lock hold times before adding a cache. [Host device lookup](../thirdparty/shiftglue-sdk/src/filesystem/devices/host_path_device.cpp), [VFS implementation](../thirdparty/shiftglue-sdk/src/filesystem/virtual_file_system.cpp).

A bounded negative cache could help immutable game-content mounts if the same misses recur. It needs invalidation for mount changes and must not hide newly created save/cache files. Coalescing nearby small reads or reusing decompression scratch buffers is similarly conditional on a trace showing that cost. Do not change saves or preload the entire game merely to improve a warm benchmark.

### Why DirectStorage is a later experiment

Microsoft's guidance describes request batching, asset layout/compression constraints, GPU decompression, and custom CPU decompression. It is not a transparent acceleration switch for arbitrary guest archive reads. [DirectStorage developer guidance](https://github.com/microsoft/DirectStorage/blob/main/Docs/DeveloperGuidance.md).

For FH1, first determine the actual hot archive/decompression format, request sizes, and destination ownership. Only then compare a native asynchronous path with an asset-conditioning/DirectStorage prototype. Account for disk cache size, install/conversion time, RAM, GPU competition, and additional supported-platform requirements. That larger pipeline may be justified eventually; it is premature before basic I/O attribution.

## 8. Scheduling, waits, and animation timing

The SDK defaults `ignore_thread_affinities` and `ignore_thread_priorities` to true. Its guest CPU bookkeeping remains, while optional host pinning applies when affinity ignoring is disabled. Verify effective session configuration before diagnosing inherited Xbox core pinning. [Thread implementation](../thirdparty/shiftglue-sdk/src/system/xthread.cpp).

Use scheduling traces to identify the limiting pattern: a long-running critical thread, a producer blocked behind a consumer, a ready thread losing CPU time, or a busy polling loop. Fix the specific dependency or contention. Blanket real-time priority, disabling SMT, or pinning every thread to a selected core can trade one symptom for another and does not establish lower hardware requirements.

Where a host-owned loop waits for a value and all producers can signal, an existing event/condition variable or standard atomic wait may suffice. Windows `WaitOnAddress` is another native option, but waking must be explicit and the predicate rechecked. It cannot simply replace an arbitrary guest-memory spin loop whose writers do not notify. [Microsoft WaitOnAddress](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitonaddress).

The user reported accelerated NPC animation and possibly title transitions. Treat that as a correctness gate for throughput changes. The project already observes simulation delta and the runtime has guest clock scaling; neither proves every animation uses the same clock. Compare animation/event duration against wall time at different rendering rates, including a supported lower cap. [Simulation observer](../src/pinyon_shift_runtime_hooks.cpp), [guest clock](../thirdparty/shiftglue-sdk/src/core/clock.cpp).

Do not count faster simulated time, dropped useful updates, or more duplicated presents as an optimization. Stable capped operation with lower CPU use may be a valuable result even when the FPS number stays fixed.

## 9. Memory, allocation, audio, and startup

**Memory:** distinguish reserved guest address space, committed pages, resident working set, host allocations, and GPU memory. Reserving an address range does not itself mean the same amount of physical RAM is consumed. [Microsoft virtual memory functions](https://learn.microsoft.com/en-us/windows/win32/memory/virtual-memory-functions).

The runtime manages guest heaps, physical aliases, page access, and callbacks. A general host allocator replacement does not replace that memory architecture. Profile allocation stacks and hard faults; then target a measured temporary allocation/copy, excessive retained cache, or repeated scratch-buffer growth. Avoid global allocator replacement, large pages, or removal of protection callbacks as first moves. [Guest memory implementation](../thirdparty/shiftglue-sdk/src/system/xmemory.cpp).

**Audio:** the XMA implementation already has a worker and performs immediate work for kicked contexts. Its comments document why waiting for a worker sweep previously hurt latency. “Move audio to a worker” therefore misses existing design and could regress responsiveness. Measure decoder time, queue depth, no-progress/recovery counters, and underruns during busy scenes. Optimize a demonstrated decoder/conversion/copy hotspot while retaining context ownership and synchronization. [XMA decoder](../thirdparty/shiftglue-sdk/src/audio/xma_decoder.cpp), [performance counters](../thirdparty/shiftglue-sdk/include/rex/perf/counter.h).

**Startup and packaging:** native source generation, PCHs, build parallelism, and linker caching can improve iteration without improving gameplay. Measure these separately. For user-facing startup, distinguish process loading, module registration, file-tree population, content reads, video, and cache warm-up. Avoid removing required registration merely because a training route never exercised it.

Linker dead stripping and identical-code folding deserve an audit rather than a claimed missing optimization: defaults and emitted sections determine what is already effective. Folding can affect distinct function addresses, which are relevant to generated dispatch identities. [Microsoft `/OPT` documentation](https://learn.microsoft.com/en-us/cpp/build/reference/opt-optimizations?view=msvc-170).

## 10. Approaches to defer or reject

| Proposal | Decision for this project |
| --- | --- |
| Global `-Ofast`/fast math | Reject as a general CPU strategy. Preserve simulation and PPC numerical semantics; any local relaxation needs a separate proven contract. |
| Global `-march=native` or AVX2 baseline | Do not put in the general preview. It raises ISA requirements and can hide missing fallbacks. Consider a narrow dispatched helper only after a hotspot and compatibility test exist. |
| Turn on every register-localization flag | Defer broad rollout. Qualify shared registers, continuation and unwind behavior first. |
| Remove exception support, bounds checks, invalidation, or save synchronization | Reject as a performance shortcut. These protect observed runtime contracts. |
| BOLT on the Windows preview | Defer: LLVM 20's BOLT documents x86-64/AArch64 **ELF** inputs, not this PE/COFF executable/DLL set. [BOLT 20.1.8 requirements](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/bolt/README.md#input-binary-requirements). |
| Copy ELF linker flags into the Windows build | Reject. Use the actual Clang driver/COFF linker syntax and inspect commands. |
| Upgrade compiler and change flags simultaneously | Separate experiments. A newer compiler may help or regress; first preserve a reproducible LLVM 20.1.8 baseline. |
| Install an allocator, task system, or DirectStorage immediately | Defer until attribution shows the existing standard/native solution is the limit. |
| More caches everywhere | Defer. Lower requirements include RAM and cold-start behavior, not just warm-route FPS. |

Clang's command-line reference distinguishes target/optimization options; use documentation matching the pinned compiler rather than assuming GCC, MSVC, and current development Clang accept equivalent recipes. [Clang 20 option reference](https://releases.llvm.org/20.1.0/tools/clang/docs/ClangCommandLineReference.html).

## 11. Ranked experiments and completion criteria

The ranking balances evidence, scope, and reversibility. It is not an estimate of absolute savings. Promote streaming immediately if a capture shows it dominates the marked hitches.

| ID | Priority | Experiment | Prerequisite / completion evidence |
| --- | --- | --- | --- |
| CPU-01 | First | Attribute matched ordinary and slowdown intervals; audit effective flags/symbols/module hashes. | Distinguish running, ready, waiting, disk and GPU time; document FP/alias assumptions. |
| CPU-02 | First | Remove import-reach tracing from one candidate; separately audit hot counters. | Independent frame measurement; keep only reproducible savings with useful diagnostics retained. |
| CPU-03 | First compiler pass | ThinLTO on the relevant generated-code/final-link targets. | Qualified gameplay and continuation paths; runtime, `.text`, link time and peak build RAM comparison. |
| CPU-04 | First compiler pass | Broad IR PGO collection and profile-use candidate. | Verified per-module profiles, documented training mix, held-out gameplay improvement and clean qualification. |
| CPU-05 | Next if CPU-bound | `-O2`/`-O3`, hot-function remarks, targeted code-size/vectorization work. | Assembly and CPU evidence identify a specific improvement; do not run an unbounded flag sweep. |
| CPU-06 | Next if guest code dominates | Localized registers, native bulk-operation coverage, expensive fallback dispatch. | One measured hot path and focused semantic regression coverage before wider rollout. |
| IO-01 | Investigate early | Attribute synchronous reads, repeated VFS misses and lock time in marked areas. | Establish whether I/O is actually on the useful-frame critical path. |
| IO-02 | Conditional | Smallest correct asynchronous/coalesced read or immutable-content lookup fix. | IO-01 evidence; completion/APC/error/write-notification and save/load qualification. |
| RT-01 | Conditional | Remove demonstrated polling, lock contention, or redundant host allocations/copies. | Producer/consumer or allocation evidence; preserve deadlines and bounded memory. |
| RT-02 | Conditional | Optimize a measured audio/decompression hotspot. | Verify no underruns, corruption or latency regression under busy gameplay. |
| QUAL-01 | Required for any retained change | Timing, stability, held-out routes, cold/warm and lower-spec validation. | No accelerated simulation; retain reproducible gains and record failures as well as wins. |

Suggested bounded follow-up goal: **complete CPU-01 through CPU-04 and IO-01, then retain only qualified improvements and rank the next implementation work from their measurements.** This does not require a compiler flag to win; a documented negative result completes its experiment. It does not claim to finish every possible recomp optimization.

For each candidate, alternate baseline/candidate runs on the same scenes; use at least several paired runs and extend only when variance leaves the decision unclear. Preserve original capture files and report run-level results instead of pooling every frame into a misleadingly large sample. Define the objective before testing: steady CPU time, tail latency, memory, startup, or power.

## 12. How much performance might remain?

The source establishes plausible opportunities, not a percentage. A doubling from compiler flags is not a defensible expectation. A meaningful CPU improvement is more plausible when profiling reveals a broad generated-code hotspot, instrumentation tax, blocking read, or repeated work that can be removed. These effects can overlap, so their percentages must not be added together.

For a **hypothetical serial critical path**, if an affected subsystem occupies fraction `f` and becomes `s` times faster:

`overall speedup = 1 / ((1 - f) + f / s)`

| Hypothetical affected share | Local improvement | Overall speedup |
| --- | --- | --- |
| 20% | 20% faster (`s = 1.2`) | Approximately 1.034x |
| 50% | 20% faster (`s = 1.2`) | Approximately 1.091x |
| 50% | Twice as fast | Approximately 1.333x |

These are arithmetic examples, **not predictions for FH1**. Real CPU/GPU overlap and frame caps further limit direct conversion into FPS. Removing a rare 100 ms stall may be more noticeable than improving average throughput by a few percent.

Lower requirements must ultimately be demonstrated on lower-spec machines: sustained useful-frame rate, stable frame times, correct game speed, acceptable CPU use, and bounded RAM/VRAM. Improving this development PC is evidence of progress, but it does not by itself justify a new minimum-spec claim.

## Source and validation notes

External sources are primary LLVM/Clang/CMake, Microsoft, and XenonRecomp documentation, linked beside the claims they support. LLVM references intentionally use version 20 documentation or the `llvmorg-20.1.8` tag; live Microsoft/CMake/XenonRecomp pages were consulted on the research date. The proposals and rankings are project-specific analysis.

Local inspection covered effective Release commands, target topology, generated headers/file inventory, codegen configuration, import tracing, counter updates, dispatch, VFS/read completion, thread defaults, memory management, audio kicks, and the simulation observer. Private generated game source is not reproduced here.

No compiler experiment, game run, new timing capture, hardware minimum qualification, or release change was performed for this research. The next evidence to collect is CPU-01, not another round of speculative optimization settings.
