# CPU critical-path performance follow-up

Status: **closed historical follow-up**; architectural priority is superseded
by the [scene-native renderer backlog](SCENE_NATIVE_RENDERER_BACKLOG.md).
This plan followed the completed PERF-00–10 measurements at root `0c274cd` and
ShiftGlue `35d0b99`. Instrumentation and conditional experiment gates remain
useful; consult the [post-fix CPU findings](CPU_HOTSPOT_RESULTS_2026-09-21.md)
for the newer sustained capture and hotspot attribution.

## Decision change

The retained frame-end submission policy exposed a large separation between
source-frame duration and measured GPU execution. The Recaro moving-race result
was 67.557 ms median per source frame with a 16.406 ms mean GPU timestamp span.
The values use different statistics and asynchronous domains, so their
difference is not CPU time. They do establish that small GPU copy, clear, and
resolve savings should not be the next default investment.

The capture requested by this plan was intended to identify delays among
title execution, command publication, SDK preparation/recording, vblank and
interrupt delivery, GPU submission/completion, and presentation.

## Instrumentation

Set `perf_critical_path_trace=true` for diagnostic runs. The default remains
false and requires restart. Each `CRITICAL_PATH` log record contains a monotonic
timestamp, thread identity, source-frame identity, and three event-specific
integer values.

The title adds read-only hooks at:

- `0x8240F4D8`: indexed draw-emitter entry.
- `0x82410328`: exact `PM4_DRAW_INDX_2` header publication.
- `0x82410620`: the wrapper's common epilogue.

The SDK records deferred-tape replay duration/bytes/command count, submission
begin/end and fence completion identities, guest-vblank lateness and interrupt
dispatch duration, and successful presentation. Analyze a log with:

```powershell
python tools/summarize-critical-path-trace.py <log-or-rotated-logs...> --output <summary.json>
```

Title-emitter timing is inclusive wall time. Deferred-tape replay is an upper
bound because it contains required D3D12 calls. Use optimized-build sampling to
separate serialization/dispatch from driver work and to inspect VMX lowering.

## Conditional implementations

1. If the indexed emitter passes its gate, replace one fully understood path
   with native C++ that produces byte-equivalent PM4 and guest-visible state.
   Unsupported inputs must fall back before any side effect.
2. If avoidable command-tape overhead passes its gate, add a direct recording
   sink while retaining the existing submission policy and a fence-safe
   deferred suffix for unavailable PSOs.
3. If vblank delivery is late on the critical path, replace only the polling
   wait with cancellation-aware deadline delivery. Preserve cadence, catch-up,
   simulation, pause/resume, and the polling fallback.
4. If generated assembly and samples prove the VMX byte shifts hot, replace
   only `simde_mm_vslo`/`simde_mm_vsro` with bit-exact register operations for
   the existing minimum CPU target.

These are conditional maintenance experiments, not prerequisites for the new
scene-native renderer. Follow current sampled evidence when considering one;
do not revive a rejected PERF-00–10 candidate unchanged. The new backlog replaces
this plan's earlier restriction against a semantic renderer direction.
