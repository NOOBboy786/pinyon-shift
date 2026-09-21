# PERF-09 submission-boundary results — 2026-09-20

PERF-09 is complete. D3D12 now keeps each frame in one command-list submission
by default instead of submitting whenever a PM4 primary buffer ends. The
`d3d12_submit_on_primary_buffer_end` hot-reload cvar remains available to restore
the previous behavior for diagnostics.

## Cause and policy

The PERF-00 race trace showed no command-buffer stalls, ZPD strict waits,
memexport waits, resolve-readback waits, or GPU timing drops. Its moving frame
was GPU-bound, with 58.26 ms mean GPU time inside a 68.20 ms median frame. This
ruled out a fence-policy change or earlier submission for GPU starvation.

The remaining test disabled `d3d12_submit_on_primary_buffer_end`. A primary
buffer boundary otherwise closes and executes the deferred command list when
safe. D3D12 treats each `ExecuteCommandLists` boundary as a full UAV and aliasing
barrier, so multiple boundaries split one guest frame into separate queue
submissions. Coalescing removes those internal boundaries while preserving the
existing frame-end submission and every explicit submission required by waits,
queries, memory exports, shutdown, or device failure.

## Fixed-route results

The open-world numbers are means of four runs from two warmed A/B/B/A blocks at
each scale. Each run uses the fixed 20.0–46.7 second window.

| Scale | Policy | Median ms | P95 ms | P99 ms | GPU span ms |
| --- | --- | ---: | ---: | ---: | ---: |
| 1x | Submit on primary end | 34.722 | 57.840 | 79.305 | 33.627 |
| 1x | Coalesce to frame end | 33.527 | 55.679 | 68.536 | 11.199 |
| 2x | Submit on primary end | 36.603 | 61.745 | 81.883 | 34.961 |
| 2x | Coalesce to frame end | 34.019 | 56.742 | 69.201 | 11.814 |

Coalescing improved 1x median/p95/p99 by 3.4%/3.7%/13.6% and 2x by
7.1%/8.1%/15.5%. The GPU span is the timestamp distance from the frame's first
to last GPU marker. With multiple submissions it includes queue gaps between
command lists, so the large reduction is evidence that those gaps disappeared;
it is not presented as shader execution time saved.

The Recaro race was repeated after one candidate p99 outlier. The table averages
four control and four candidate runs in the moving 70.0–76.6 second window.

| Policy | Median ms | P95 ms | P99 ms | GPU span ms |
| --- | ---: | ---: | ---: | ---: |
| Submit on primary end | 68.205 | 95.394 | 113.153 | 59.462 |
| Coalesce to frame end | 67.557 | 93.777 | 110.859 | 16.406 |

The race improved by 0.9%/1.7%/2.0%. Across all measured windows there were zero
command-buffer stalls, ZPD strict waits/timeouts/stale results, memexport waits,
resolve-readback waits, and GPU timing drops. Warmed process samples showed no
systematic memory increase: candidate working-set peaks stayed within the
control range, and 2x private-memory peaks were slightly lower.

## Correctness and validation

- All 1x/2x open-world and race A/B/B/A runs exited normally.
- The race route passed required native-family coverage, presentation,
  simulation-time, HUD progression, and capture-difference assertions.
- End-of-route open-world captures were byte-identical. Other capture
  differences stayed within normal control-to-control scene variation.
- Production fence failure, stale-wake, cancellation, device-loss, and shutdown
  draining checks passed.
- The constant no-output query guard passed.
- The release preview built successfully, then completed an open-world run with
  no cvar override; its GPU span matched the coalesced candidate.

Local evidence is under `.local/native-renderer/perf-09/` and is intentionally
not versioned.
