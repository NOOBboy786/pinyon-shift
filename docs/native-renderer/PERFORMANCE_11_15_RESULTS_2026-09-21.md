# PERF-11–15 critical-path results

Date: 2026-09-21

## Decision

Retain the opt-in correlated trace and the deadline-driven guest-vblank wait.
Reject the native title-emitter replacement. Defer direct D3D12 recording and
VMX byte-shift lowering until a privileged, symbolized CPU sample proves their
avoidable cost meets the existing entry gates.

The retained vblank change defaults on and can be rolled back with
`pinyon_shift_fh1_vblank_deadline_wait=false`. The diagnostic trace defaults
off and is enabled with `perf_critical_path_trace=true`.

## Tested build

- Title base: `0c274cdd08eec3f2f3800395ac09df3c8d705188` plus the PERF-11 hooks and tools.
- SDK implementation: `59451e4848d0ef117b4a904b66f8e041f73007d4`.
- `pinyon_shift.exe` SHA-256: `7BB481FE77399F049C7FD89ED0BC79E914952A81B83D30A0C21B164BA3414B91`.
- `rexgpu-fh1.dll` SHA-256: `E7E318907ED5E8600745F735A1C25CEEA3D96D15F34D6B4FF5A776D7EFF5DCB1`.
- Guest executable SHA-256: `DB40DF605ADE49A612B35A7A24C38F6004BCB17A88ED6B48288DE16DF9E3987C`.
- Patch-set SHA-256: `95C7A898D76AC8ED2B3F0D4CDDB4CC3D4823D085788959DB1A0040314BD9551D`.

The same candidate binary produced both clean PERF-14 arms; only the rollback
cvar changed. Runs used the installed `0.1.0` AppData preview state and its
existing Forza profile. The SDK worktree also contained pre-existing,
uncommitted `xboxkrnl_io.cpp`, `xobject.cpp`, and `libmspack` changes; they were
preserved and excluded from the PERF-11/14 commit.

## Critical-path measurements

Times are milliseconds. The open-world control used the legacy 1 ms polling
wait. Candidate captures used the retained deadline wait. The Recaro summary
covers the final rotated-log window, source frames 4618–5040, which includes
the moving-race segment.

| Route / wait | Source frames | Frame median | Title emitter median / p95 | Tape replay median / p95 | Vblank late p95 | Vblanks at least 1 ms late |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Open world / polling | 4,200 | 9.040 | 0.035 / 0.249 | 0.420 / 2.431 | 1.860 | 37.85% |
| Open world / deadline | 4,281 | 8.824 | 0.043 / 0.261 | 0.409 / 2.203 | 1.462 | 24.20% |
| Recaro moving window / deadline | 422 | 31.660 | 0.056 / 0.215 | 2.132 / 5.994 | 1.525 | 26.62% |

The first ordinary `sleep_for` deadline experiment was rejected: its share of
vblanks at least 1 ms late rose to 73.13%. The retained implementation reuses
the presenter's sleep-then-yield policy and preserves the old polling path for
VSync-off operation and rollback.

## Clean PERF-14 A/B

Three control and three candidate runs alternated on
`fh1-open-world-performance.fh1test`, with critical-path tracing disabled.
Values below are medians across the three per-run summaries.

| Arm | Frame median | p95 | p99 | Source cadence | Present cadence | Dropped presents | Simulation/wall ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Polling control | 9.180 ms | 18.370 ms | 22.371 ms | 90.263 Hz | 89.728 Hz | 29 | 1.003076 |
| Deadline candidate | 8.886 ms | 17.341 ms | 21.658 ms | 92.679 Hz | 92.636 Hz | 11 | 1.003195 |
| Change | -3.20% | -5.60% | -3.19% | +2.68% | +3.24% | -62.07% | +0.01% |

This exceeds the 2% median retention gate and stays within all regression
ceilings. Every run exited normally and produced the route captures.

## Candidate disposition

- **PERF-11 — retained.** Events correlate title emission and PM4 publication
  with deferred replay, submission/fence completion, guest vblank and present.
  The analyzer accepts rotated logs and sorts them by monotonic timestamp.
- **PERF-12 — rejected.** The indexed emitter costs 0.035–0.056 ms median,
  far below `max(2 ms, 8% of frame time)` on both routes.
- **PERF-13 — deferred.** Open-world total tape replay is only 0.420 ms median,
  below the 1 ms gate. Recaro reaches 2.132 ms, but this upper bound includes
  required D3D12 driver calls. Windows Performance Recorder could not enable
  the CPU sampling policy (`0xc5585011`) in the current session, and no WPA
  exporter is installed, so avoidable serialization/dispatch is unproven.
- **PERF-14 — retained.** The entry and clean retention gates pass. The old
  polling behavior remains available through the rollback cvar.
- **PERF-15 — deferred.** Generated source contains 141 `vslo`/`vsro` sites in
  nine partitions. Optimized assembly still contains stack-backed SIMD work,
  but the required symbolized samples are unavailable, so hot-path cost has
  not met `max(1 ms, 5% of frame time)`.

## Reproduction

Build with `tools/build-preview.ps1`, launch the fixed routes through
`tools/launch-preview.ps1` with the AppData state root, and add
`--perf_critical_path_trace=true` for diagnostic captures. Pass every rotated
log to:

```powershell
python tools/summarize-critical-path-trace.py <logs...> --output summary.json
```

Raw local evidence is under
`.local/native-renderer/performance/PERF-14/20260921-011330` and the matching
`.local/critical-path` capture directories. These large logs and screenshots
remain uncommitted.
