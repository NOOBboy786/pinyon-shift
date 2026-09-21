# PERF-04 and PERF-08 results — 2026-09-20

Both candidates were measured against the frozen PERF-00 setup and rejected.
Neither experimental implementation is part of the final tree.

## PERF-04 — precise dirty geometry updates

The experiment extended shared-memory watch notifications with their invalidated
address range. `GetFh1OwnedGeometry()` accumulated CPU-dirty ranges, retained a
full-owner fallback for GPU writes and missing snapshots, uploaded only the
dirty span, and invalidated only overlapping depth and terrain bounds.

The unmodified full-window path showed 111,869,952 upload bytes for 62,275,584
bytes of observed invalidated-page coverage: 1.80x amplification. The page
coverage is a lower-bound proxy because each watch is one-shot and does not
observe additional writes before the next import.

The 1x race A/B/B/A final-window results were:

| Run | Partial upload | Median ms | P95 ms | GPU ms |
| --- | --- | ---: | ---: | ---: |
| A1 | Off | 65.437 | 92.538 | 59.280 |
| B1 | On | 63.077 | 92.112 | 56.221 |
| B2 | On | 66.347 | 100.000 | 62.431 |
| A2 | Off | 71.533 | 98.638 | 67.518 |

The candidate average improved median and GPU time by about 5.5% and 6.4%, but
p95 was flat and the run order showed substantial drift. A 2x cross-check did
not confirm the improvement:

| Run | Partial upload | Median ms | P95 ms | GPU ms | Upload bytes | Snapshot bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| B | On | 69.021 | 89.063 | 62.740 | 106,487,808 | 61,145,088 |
| A | Off | 67.907 | 90.788 | 60.796 | 126,025,728 | 66,125,824 |

The candidate reduced uploads by 15.5% and snapshot copies by 7.5% in that pair,
but regressed median and GPU time by 1.6% and 3.2%. It therefore fails the frame
and copy-cost acceptance gate. The implementation and temporary telemetry were
removed. The synthetic cache harness covered CPU and GPU invalidation, writes
during import, overlap, retained snapshots, address reuse, and in-flight owners.
An uploaded-byte RenderDoc parity replay was not run because the performance
gate had already rejected the candidate.

Artifacts are under `.local/native-renderer/perf-04-08/` and are intentionally
not versioned.

## PERF-08 — packed constant-buffer reuse

Temporary telemetry measured the existing `UpdateBindings()` path during the
1x race:

| Metric | Result |
| --- | ---: |
| Layout switches | 1,671,255 |
| Immediate A → B → A layout recurrences | 758,606 (45.4%) |
| Float upload requests | 4,260,001 |
| Vectors packed | 119,092,511 |
| Bytes packed | 1,905,885,168 |
| Measured allocation and packing CPU | 410.1 ms total |

The combined allocation and packing work was about 0.11 ms per rendered frame
over the run. Layout recurrence does not prove that the referenced register
values also recur. Proving safe reuse would require relevant-register generation
tracking or hashing and comparison, plus frame/fence lifetime handling. That
bookkeeping would target only the measured 0.11 ms/frame upper bound.

No gather-plan or constant-buffer cache was added. Current-binding dirty checks
already remove the cheapest redundant case, and the remaining measured cost is
too small to justify the required identity and lifetime machinery. The temporary
telemetry was removed after measurement.

## Validation

- One release preview build completed with the experiments applied.
- The focused geometry-cache harness passed with contained and exact ownership.
- CPU snapshot and texture-watch checks passed after the shared-memory callback
  experiment.
- Eight scripted race runs completed normally and produced all six expected
  captures per run.
- The final source tree contains only this documentation and backlog updates;
  runtime experiments remain rejected.
