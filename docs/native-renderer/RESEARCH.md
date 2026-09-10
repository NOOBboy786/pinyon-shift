# Native renderer research reference

This consolidates the retired discovery/replay documents at `93742f2`.
It preserves architectural findings and failed leads, not a list of current
runtime features. For shipping behavior and remaining priorities, start with
[development findings](../DEVELOPMENT.md) and the
[migration checklist](NATIVE_RESOURCE_MIGRATION_CHECKLIST.md).

The old NR-00–NR-05 and prototype Phase C labels describe historical milestones;
they are not the current resource-migration A/B/C completion gates. Many of
those title-side prototypes were removed or moved into ShiftGlue. Check source
and tool availability before reproducing an old command.

## Capture, provenance and admission

- Observe the authoritative draw/resolve path without changing guest state.
  Census observations, repeated shader signatures and static call graphs are
  discovery evidence, not permission to render or suppress a family.
- Correlate the physical PM4 header address and its generation to the actual
  backend outcome and prepared signature. Thread timing, FIFO position and equal
  addresses across reuse are insufficient. Indirect-buffer nesting, constructor,
  owner and invocation scopes add provenance; they do not supply semantic types.
- Keep fixed-capacity tables and account for overflow, stale/missing joins,
  unknown outcomes and unsupported state. Missing observations are unknown,
  not evidence of absence. Hashes and numeric metadata can be public; captured
  shaders, constants, geometry, textures and memory remain local.
- The indexed wrapper `0x8240F4D8` and immediate-index wrapper `0x829F7C70`
  supplied exact header-store boundaries at `0x82410328` and `0x829F7CB0`.
  These are supported-retail structural anchors, not terrain/vehicle labels.
- The original resolve census found 38 later consumer shader families for its
  sky/horizon output. A render target cannot be treated as presentation-only
  because it looks like a sky pass. CPU-read observations, queries, memory export,
  resolves and later consumers need independent coverage.

Keep the [census baseline](RENDER_PASS_CENSUS.md) and
[guest-visible dependency ledger](GUEST_VISIBLE_RENDER_DEPENDENCIES.md) as the
bounded evidence contracts. Their historical “Gate B” concerns census-based
suppression; it does not undo separately qualified depth/mipmap replacements.

## Immutable replay inputs and resource lifetime

Capture shader inputs at the synchronous prepared-draw boundary. Replay must
consume that immutable snapshot rather than reread mutable guest constants.
Join exact shaders/specializations, vertex layout, index bounds, topology,
textures/samplers, constants, pipeline state and attachment shape. Resource
relocation with equal content validates a content-based contract; it does not
exclude an unobserved GPU producer or establish visual identity.

The old resource model canonicalized physical-heap aliases to half-open ranges
within the 512 MiB Xenon aperture. Empty/overflowing ranges are invalid. Include
descriptor/layout and generation in cache identity, and distinguish allocation
generation from payload generation. Track writes, rebinding, GPU producers,
streaming invalidation and destruction. Known GPU-produced data without a live
compatible producer requires a bridge/fallback, never stale CPU decoding.

Finite cache budgets, generation checks and fence-delayed destruction prevent
resource reuse while in flight. A worker's metadata deduplication count is not
proof of native upload or saved GPU work. The historical title-side resource
worker and `DrainCommits` integration are absent from the current renderer.
Current geometry behavior is documented in the [Carson fix](CARSON_GEOMETRY_CACHE_FIX.md).

## Publication, visual comparison and suppression

The private replay sequence was: exact input snapshot, isolated draw, readback,
paired color/depth/stencil comparison, complete-pass retention, then output
publication and separately gated suppression. A single exact draw does not
prove complete-frame composition, and a private target does not remove work
while the original draws still execute.

Publish only complete output for the exact current source frame, committed at
the correct submission boundary. Reject stale/partial targets, unsupported
formats and failed replay. Distinguish logical image extent from padded backing
size; preserve crop, color space, gamma, scale, clear history and depth/stencil.
Early prototype work used very small logical scene extents and must not be
mistaken for a full-resolution gameplay renderer.

The historical sky/horizon experiment preserved the anchor and omitted only an
exact adjacent follower after complete native color/depth publication. Its
rollback and warm-up checks were family-specific. It does not justify omitting
arbitrary draws, resolves, queries or memory exports. An evaluator can report
admission evidence without possessing a suppression API.

Compare the same draw/frame and downstream consumers, not adjacent screenshots
from changing scenes. D3D12 timestamp spans describe the measured GPU interval;
do not add overlapping buckets or interpret them as whole-frame savings.
Keep RenderDoc/readback and profiling overhead outside clean timing windows.
Current procedures: [render automation](FH1_RENDER_TEST_AUTOMATION.md),
[manual discovery](DISCOVERY_PLAYTEST.md) and [validation rules](../DEVELOPMENT.md#validation-and-evidence).

## Procedural models, visibility and batching

RTTI, construction/destruction and generation evidence identified
`proceduralGeometry::CProceduralModels`. Its per-record helper `0x82417418`
supplied an immutable semantic extraction boundary. Visibility and render-state
stages are observed histories, not universal prerequisites: alternate dispatch
routes must remain accounted for. A typed receiver still does not establish
mesh/material meaning, streaming ownership or native admission.

Preserve title-authoritative visibility/LOD outcomes before reconstructing their
policy. A decision must join the same receiver generation, record and prepared
draw; stale, missing and future decisions cannot qualify it. Prepared-candidate
checks proved a bounded handoff without promoting a semantic world family.

Separate immutable templates, dynamic resources and batch equivalence. Global
compatibility does not permit reordering. The exact consecutive-run census
found only single-draw runs, including 2,873 eligible draws in the later batch:
zero projected command reduction. Broader material/pipeline reuse supports
state caching, not a claim of instancing or fewer draws. Coarser equivalence
needs its own side-effect and ordering proof.

## Terrain, track and static-world leads

- The title's `fasttrackrender`, `trackfardistance`, `renderroaddetailblur` and
  `notrackcommandbuffers` controls support differentials. `perfmode` also changes
  neighboring families, so it is not an isolated terrain test.
- Exact indirect track scopes reached prepared draws while the direct unified
  mesh route was dormant in the tested festival scene. Do not generalize that
  dormancy to every route or label generic direct draws as world geometry.
- Raw constants, child/descriptor windows and reference-composed matrices did
  not uniquely match the 24,025-entry authored spatial catalog. Those bounded
  transform interpretations are closed; widening tolerances is not a new proof.
  Attachment shape and exact presentation dispatch were the next leads.
- Color-producer research distinguished tile components from complete padded
  resolve assemblies. Publishing an individual component or dropping alignment
  rows cannot substitute for a full scene. The later failed scaled accumulator
  experiment remains unmergeable; see [rejected paths](../DEVELOPMENT.md#rejected-and-unqualified-paths).
- Static SimpleModel work traced presentation owner, renderer, resource,
  model/submodel/mesh and packet provenance. A live resource can replace payload
  without changing address, requiring independent payload generations.
  Prepared vertex layout is shader-derived; title mesh fields alone are not
  a complete render contract.
- Hashed asset keys and collision/gameplay spatial catalogs are category leads,
  not proof that an instance is a building or prop. The dormant SimpleModel
  population's null resource is an expected missing-resource outcome, not a
  mapped-read fault. It remains ineligible without metadata and renderer joins.

The [combined C1/C2 profile](C1_C2_BATCH_QUALIFICATION.md) retains the historical
qualification procedure and its incomplete gates. It is not current C-epic
Xenos-retirement qualification.

## Vehicles and shadow epochs

The pose boundary `0x82BC5A3C` is shared by player, traffic and other vehicles.
Identify generation, source, owner and active slot; do not call it player-only.
The local-player map-entity type was separately proved, but direct entity/ID
joins did not establish the rendered vehicle's ownership.

Thirty exact prepared color families formed 15 geometry contributions with two
variants each. They shared one material-topology group, so shader/topology hashes
could not label paint, glass, wheels, lights or livery. Unrelated draws interrupt
their order; a consecutive 30-draw replay was rejected. Frame-wide private
retention produced coherent multi-submesh geometry, but its flat diagnostic
appearance did not qualify materials, lighting or final-frame parity.

Raw constant/world-position matching and the generic CPU constant writer did
not establish the final prepared vehicle transform. The draw-atomic bridge used
authoritative shader-register state; register 254 remained outside packet-proven
semantic decisions. Player identity, typed material roles and publication were
still separate gates. A tire/wheel asset-path binding supplied a narrow static
discriminator, not runtime proof of every material contribution.

Shadow work proved a bounded 80-draw producer epoch: 64 dominant-family draws
followed by four repetitions of three secondary draws and one tertiary draw.
Private depth accumulation had exact captured parity. Sequence gaps, changed
targets, failed batches and other epochs remained inadmissible. Original draws
and consumers still executing meant no general shadow-retirement claim.
Do not confuse that prototype with the currently retained
[owned depth chain](OWNED_DEPTH_CHAIN_CONTRACT.md) or
[reflection mip replacement](REFLECTION_MIPMAP_REPLACEMENT.md).

## Recovering exact historical evidence

All 83 consolidated documents, their per-run hashes, schemas, offsets, commands
and original cross-links remain in the
[native renderer directory at 93742f2](https://github.com/arcanite24/pinyon-shift/tree/93742f2/docs/native-renderer).
Browse by topic prefix: `VEHICLE_`, `STATIC_WORLD_`, `TRACK_`, `PROCEDURAL_MODEL_`,
`VISIBILITY_`, `SEMANTIC_`, `SHADOW_` and `INDIRECT_`. Capture/replay/publication
documents use the corresponding names. Retrieve any original locally with:

```powershell
git show 93742f2:docs/native-renderer/RESOURCE_IDENTITY.md
```

Historical “next” instructions and measured FPS apply to their exact builds and
bounded scenes. They are evidence to consult when revisiting a problem, not
active work orders. New retained changes should update current findings and
one focused reproducible contract, with raw run journals kept under `.local`.
