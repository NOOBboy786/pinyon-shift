# Non-renderer optimization results

Branch: `codex/non-renderer-optimization-experiments`.
Plan: [optimization research](NON_RENDERER_OPTIMIZATION_RESEARCH.md).

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
| CPU-03 ThinLTO | Pending | Qualified isolated build and matched results |
| CPU-04 PGO | Pending | Broad multi-module profiles and held-out validation |
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

These are not a qualified performance pair. Cumulative CSV durations were 32.01 s
and 46.68 s despite using the same script; a naive 27–30 s CSV window is therefore
not sufficient to establish matched gameplay. `tracing-smoke-summary.json`
records this limitation. Explicit scene/script-clock alignment and repeated runs
are needed before interpreting differences. No tracing performance gain is claimed.

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
