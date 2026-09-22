# Native resource migration checklist

Original milestone status: 2026-09-10. Start with the [development findings](../DEVELOPMENT.md)
for retained behavior, rejected experiments, installation work and user reports.
This remains the acceptance ledger for resource migration and full Xenos retirement.
The [scene-native renderer backlog](SCENE_NATIVE_RENDERER_BACKLOG.md) now owns
implementation order. Its new architecture does not mark any B/C item complete
or reopen previously deferred experiments unchanged.

## A — First complete resource chain

- [x] A1: establish a matched chain-cost baseline.
- [x] A2: identify producer, consumers, history and lifetime boundaries.
- [x] A3: implement native ownership with validated admission and fallback.
- [x] A4: preserve changing contents, partial regions and history.
- [x] A5: remove the replaced work and count remaining compatibility work.
- [x] A6: qualify and retain the bounded chain.

A1–A6 are complete **only for the symmetric 1x owned depth-clear chain**.
Scaled rendering retains compatibility clears: the unchanged 2x candidate failed
North Carson frame-tail retention. Upstream CPU packet-emitter bypass remains B3.
See the [resource contract](OWNED_DEPTH_CHAIN_CONTRACT.md) and
[retention result](A6_OWNED_DEPTH_RETENTION.md).

## B — Expand native ownership

The focused [reflection-mipmap replacement](REFLECTION_MIPMAP_REPLACEMENT.md)
is implemented and enabled for validated symmetric 1x/2x inputs. It removes 48
original draws and 48 resolve copies per cube, with current-input validation and
fallback. It retains six guest lists and all 2,352 packet decodes per cube.
Clean whole-frame comparisons show small/mixed changes, not a large FPS gain.

The [Carson cache fix](CARSON_GEOMETRY_CACHE_FIX.md) reduces allocation churn
without raising the 32 MiB/512-entry budget. Its short race comparison and 1x/2x
smoke pass; sustained town/race acceptance and green-glass reproduction remain open.

**Previous incremental B experiments remain deferred.** New work proceeds under
the scene-native backlog above. Neither focused change completes B1–B4.
Keep containment, recycling, tile-clear and HUD admission
experiments unretained; stopped comparisons require new attribution and a revised
protocol before resuming. See [rejected paths](../DEVELOPMENT.md#rejected-and-unqualified-paths).

- [ ] **B1 — Migrate the next highest-value chains.** Rank actual resource and
  pass costs; repeat A2–A6 for each selected chain. Complete when required pass
  families have native producers/consumers and the scene inventory accounts for
  every remaining compatibility dependency. Draw counts, first-shader labels
  and isolated kernel timings are not complete cost attribution.
- [ ] **B2 — Reduce geometry/texture preparation.** Use proven allocation
  identity, mutation and lifetime hooks for persistent buffers/texture mirrors.
  Complete when imports, allocations or conversions fall without stale content,
  missing streamed geometry, higher memory pressure or worse frame-time tails.
  Bounded GPU copy/consumer proofs do not establish changing-content coverage.
- [ ] **B3 — Bypass obsolete guest command generation.** Replace covered producer
  work before packet emission while preserving queries, fences, memory exports,
  dirty state, clipping, refill/flush and other side effects. Complete only when
  less generation/decoding is measured. The clear producer anchor is
  `sub_8240E130` (shader `0x820C5FD0`, copy callsite `0x8240E4A8`, caller
  `0x824019D0`); measured aggregate CPU cost was only about 0.03–0.045 ms/frame
  in one scene. This does not justify skipping it or measure downstream GPU work.
  Mip cached-list construction/submission is another explicit remaining dependency.
- [ ] **B4 — Qualify a lower-cost visual profile.** Measure AA, shadow/reflection,
  scene scale or postprocessing settings individually and combine only retained
  changes. Complete with documented visual differences and repeatable savings
  during motion, including correct NPC/UI timing. Mark effects inapplicable when
  attribution shows no useful opportunity.

## C — Retire Xenos and qualify lower requirements

- [ ] **C1 — Close remaining dependencies.** Cover geometry, textures, render
  targets, resolves, presentation, readbacks and guest side effects. Qualification
  routes must report no fallback or unhandled dependency, including menus, video,
  transitions and streaming; state coverage limits explicitly.
- [ ] **C2 — Run without Xenos.** Remove superseded command/resource paths and
  runtime build dependencies only after their replacements are qualified. A clean
  build must pass the scene matrix without Xenos linked or invoked. Keep offline
  shader production separate and preserve a rollback release.
- [ ] **C3 — Measure lower hardware requirements.** Test lower-end discrete and
  integrated/UMA hardware with stated quality, API, adapter and driver settings
  during sustained difficult scenes. Publish only measured frame-time and memory
  targets. Compare pinned Canary separately with matched workloads; another
  game's renderer cannot establish FH1 requirements.

## Gates for every retained change

1. Freeze actual source, SDK, binary, settings and artifact identities. Separate
   the source checkpoint from any previously staged runtime; old embedded hashes
   and successful compilation do not prove a binary is the qualified one.
2. Validate exact session, input delivery, clocks, scene/HUD state, motion and
   candidate admissions. Keep failed captures and incomplete comparisons; a
   normal exit or correct screenshot does not prove native work executed.
3. Check resource contents, mutation, partial writes, aliasing, history, reuse,
   destruction and GPU completion. Preserve simulation, ordering and guest-visible
   side effects. Missing geometry, flicker, broken transparency and timing errors
   fail qualification; small stable shading changes need explicit benefit.
4. Use repeated matched controls at relevant scales. Report median/p95/p99,
   CPU/GPU cost, memory, removed work and fallback. Keep profiling and readback
   outside clean benchmarks. Cover frontend, garage, day/night driving, traffic,
   race, rewind, map, pause, photo, FMV and streaming as the changed chain requires.
5. Retain only a useful measured improvement or faithful dependency removal
   without material regression. A rejected candidate closes its experiment,
   not the checklist item. Full release coverage is broader than bounded smoke.

Record one concise result and its evidence link against the relevant item.
Keep detailed run logs under `.local` and follow [AGENTS.md](../../AGENTS.md)
for the AppData save. Do not manipulate saves for tests or automatically resume
previously deferred work merely because an old journal says a goal is active.
