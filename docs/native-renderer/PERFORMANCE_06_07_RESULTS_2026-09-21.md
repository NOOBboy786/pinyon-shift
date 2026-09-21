# PERF-06 / PERF-07 reflection command-stream result — 2026-09-21

Status: **decoder/stream bypass rejected; no production behavior changed.**

The existing native reflection-mip replacement intercepts each 6,944-byte
indirect list in `D3D12CommandProcessor::ExecuteIndirectBuffer`. This is the
earliest verified boundary in the current title and SDK: the title has already
built and submitted the list before the SDK sees it. No title-side cached-list
construction or submission hook exists in the current source tree, so an SDK
change cannot remove producer work that has already happened.

## Current cost

A default-off probe split the admitted path into contract/input validation,
native command recording, and required guest-packet replay. The fixed 1x
open-world route exited normally with 6,378 native faces and no fallback lists.

| Work | Cumulative ns | µs / face | µs / six-face cube |
| --- | ---: | ---: | ---: |
| Snapshot, parse and external-input checks | 50,121,800 | 7.859 | 47.151 |
| Native mip command recording | 19,368,100 | 3.037 | 18.220 |
| Required packet replay | 95,634,900 | 14.994 | 89.967 |
| Total | 165,124,800 | 25.890 | 155.338 |

The replay is the largest remaining part, but it is not dead decoding. Each
face list contains eight resolve commands whose copy work is skipped while the
existing resolve path still performs compatibility clears and render-target
ownership transfers. The signed command contract also preserves register
writes, inline shader and constant loads, invalidation, and cache-flush packets.
Query, predication, inherited state, render-target path, physical ranges,
relocation, external allocations, mutation, and CPU ownership all gate entry.

Skipping the list after `GenerateFh1ReflectionMips` would therefore remove
observable clear/ownership/cache behavior. Replacing it correctly would require
a second handwritten executor for the same signed packet sequence. That would
save at most the measured 0.090 ms per complete cube while duplicating the
existing packet implementation, so the candidate was rejected before a
behavior-changing build.

## Prepared-stream decision

The mip list is the strongest immutable-stream candidate: six recurring face
lists share an address-independent non-address signature. It still cannot use
an address-only or one-time prepared template. Cube, shader, constant, vertex,
and resolve-vertex allocations may relocate; every current allocation and
external payload is re-snapshotted to reject mutation, concurrent writes and
GPU-owned input. The required replay also consumes current inherited state and
updates ordinary command-processor state.

Caching the parsed template could remove only the 0.047 ms per-cube validation
bucket, and safely validating its identity would repeat the snapshots and hash
work that bucket measures. The existing parse-and-fallback path is the smaller
implementation. Previously observed general draw streams did not form useful
consecutive immutable batches, so no broader prepared-stream cache was added.

## Evidence and rollback

- SDK probe commit: `35d0b99`.
- Staged `rexgpu-fh1.dll` SHA-256:
  `63AA779E95813832FD1F1CEC228F03EC6434F815511C9E775172A84EC4F5DB75`.
- Route: `config/render-tests/fh1-open-world-performance.fh1test`, symmetric 1x,
  AppData preview state, `--fh1_mip_decode_probe=true`.
- Final probe event: 6,378 faces, 50,121,800 / 19,368,100 / 95,634,900 ns.
- Local evidence: `.local/native-renderer/performance/perf-06/decode-probe-1x/`.
- Existing `tools/check-fh1-mip-contract.cpp` covers six faces, relocation,
  external mutation/ownership rejection, malformed commands, truncation and
  inherited-state rejection.
- Rollback/normal operation: `--fh1_mip_decode_probe=false` (the default), or
  revert SDK commit `35d0b99` to remove the timing counters.

The diagnostic route is not a clean frame-time comparison. The rejection is
based on measured removable CPU bounds and missing side-effect equivalence; no
runtime candidate advanced to visual or performance retention testing.
