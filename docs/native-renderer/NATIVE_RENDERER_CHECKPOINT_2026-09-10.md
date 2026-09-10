# Native renderer checkpoint — 2026-09-10 UTC

This is a source checkpoint for remote `dev`, not a new preview release or a
claim that B is complete. Continue with the active B1–B4 goal in the
[resource migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md).

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
