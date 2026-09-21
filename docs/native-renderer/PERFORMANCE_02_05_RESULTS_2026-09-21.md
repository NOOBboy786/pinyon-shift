# PERF-02 / PERF-05 investigation — 2026-09-21

Status: **PERF-02 scaled retry rejected; PERF-05 direct consumer import accepted.**

## PERF-02: owned depth at 2x after PERF-09

The selected lifetime is the existing audited base-720, pitch-13 D24S8 chain in
[the owned-depth contract](OWNED_DEPTH_CHAIN_CONTRACT.md). It covers initial
ownership, partial depth-only clears, unchanged stencil and exterior pixels,
mixed floating-depth history, EDRAM dumps, resolve publication, aliases, cache
reuse and destruction. The retained implementation remains symmetric-1x-only.

PERF-09 changed the default submission boundary after the original 2x rejection,
so a separate default-off admission switch was used for one fresh A/B/B/A check.
The switch reused the checked 2x mapping and ownership implementation; it changed
no clear, transfer or consumer logic. The fixed open-world window was seconds
20–46.7 at symmetric 2x. All four runs exited normally, and candidate runs each
reported at least 5,120 native owned clears.

| Mode / run | Median ms | p95 ms | p99 ms | Mean measured GPU ms |
| --- | ---: | ---: | ---: | ---: |
| Control A1 | 12.652 | 17.118 | 23.451 | 10.431 |
| Candidate B1 | 12.349 | 16.105 | 22.674 | 7.507 |
| Candidate B2 | 13.539 | 19.540 | 28.903 | 7.856 |
| Control A2 | 12.545 | 16.950 | 23.752 | 10.610 |
| Control mean | 12.598 | 17.034 | 23.601 | 10.520 |
| Candidate mean | 12.944 | 17.822 | 25.788 | 7.682 |

The candidate reduced measured GPU time by 26.98%, but median/p95/p99 regressed
2.74%/4.63%/9.27%. The p95 and p99 changes exceed the PERF-00 retention limits.
The experimental admission switch was removed. Repeating the same ownership path
is closed; further PERF-02 work needs attribution and a changed lifetime or CPU
design. The qualified 1x default and scaled fallback are unchanged.

## PERF-05: reflection-cube lifetime inventory

The existing producer contract writes a 256×256, six-face, nine-level
R10G10B10A2 cube. Each face runs eight native mip dispatches, publishes each mip
range through `MarkRangeAsResolved`, invalidates overlapping texture watches via
`RangeWrittenByGpu`, and preserves the compatibility clear and ownership work.
The observed face order is `0, 4, 2, 1, 3, 5`; two consecutive complete updates
used the same allocation at `0x1C879000`. The address is evidence, not identity.

The later consumers use the cube through VS `C34795A841E7DEFF` and PS
`21B70A5E4C9CFD11`. The generic texture cache retains the host cube object, but
every changed cube is still untiled into a scratch buffer and copied into all 54
host subresources before sampling. Unsupported command/input state falls back to
the original mip draws and resolves. Symmetric 1x/2x/3x generation and scaled
storage requirements remain those in
[the mipmap contract](REFLECTION_MIPMAP_REPLACEMENT.md).

New cumulative counters are recorded only after a successful matching cube load:
load count, copied subresources, guest bytes and scratch-upload bytes. On the
fixed 1x open-world route, the final periodic sample reported:

| Native faces | Complete cube imports | Subresource copies | Guest bytes | Scratch-upload bytes |
| ---: | ---: | ---: | ---: | ---: |
| 10,050 | 1,671 | 90,234 | 3,695,984,640 | 3,613,851,648 |

This is 54 copies and about 2.16 MiB of scratch traffic per imported cube. The
four-cube difference between generated and imported totals is expected because
the periodic sample can end before the last produced cubes are consumed. This
proves the next implementation target: write the persistent consumer cube
directly and retire the scratch conversion/copy path, while preserving the
compatibility bridge until face rendering itself can publish to that resource.

## PERF-05: direct persistent-cube import

The accepted implementation adds one contract-specific compute importer for
the measured cube. It writes all six faces of each mip directly from shared or
scaled resolve memory into the existing persistent `Texture2DArray` resource.
The resource receives UAV capability only for the exact 256×256, six-face,
nine-level, tiled R10G10B10A2 contract. Other textures and incomplete base/mip
loads continue through the generic importer. A default-on runtime switch,
`fh1_direct_reflection_cube_import`, preserves an immediate fallback and made
the comparison use identical binaries.

Each complete refresh now issues nine compute dispatches and one tracked
destination transition instead of allocating about 2.16 MiB of scratch space
and issuing 54 `CopyTextureRegion` calls. The later transition to the ordinary
UNORM SRV makes the UAV writes visible to the existing consumers. On the 1x
smoke route, the final sample recorded 1,067 direct imports, zero subresource
copies and zero scratch-upload bytes. The captured frame was coherent. A 2x
run recorded 1,663 direct imports and also eliminated every copy and scratch
byte; its black-world capture matches the pre-existing 2x route output rather
than establishing a new visual regression. The 3x route exited normally but
did not request a matching consumer cube, so it did not exercise this path.

The fixed 1x open-world window was seconds 20–46.7. All four A/B/B/A runs used
the same staged Release build; A disabled the new runtime switch and B enabled
it.

| Mode / run | Median ms | p95 ms | p99 ms | Mean measured GPU ms |
| --- | ---: | ---: | ---: | ---: |
| Control A1 | 15.520 | 19.540 | 25.631 | 6.537 |
| Candidate B1 | 14.957 | 18.664 | 23.994 | 6.227 |
| Candidate B2 | 14.982 | 20.027 | 24.092 | 6.651 |
| Control A2 | 15.555 | 19.709 | 25.658 | 6.597 |
| Control mean | 15.538 | 19.625 | 25.645 | 6.567 |
| Candidate mean | 14.970 | 19.346 | 24.043 | 6.439 |

The candidate improved median/p95/p99 by 3.66%/1.42%/6.25% and measured GPU
time by 1.95%. It therefore remains enabled by default. This completes the
measured consumer-side copy retirement. A future producer-side phase may bind
face rendering and mip generation to the same texture and remove the remaining
compatibility-memory read; that larger ownership change is not claimed here.

## Validation and evidence

- Release `rexgpu-fh1` and staged preview builds pass.
- `tools/check-fh1-owned-lifetime.py` passes production ownership lifetime and
  atomic full-tile row admission.
- `tools/check-fh1-owned-depth-clear.cpp` passes 7,204,228 sample mappings,
  partial-region guards and wrap rejection.
- All seven new direct-import smoke/comparison runs exited normally, including
  the 1x A/B/B/A block and separate 1x/2x/3x smoke routes.
- Local run evidence is under `.local/native-renderer/perf-02-05/` and is not
  committed because it contains game-derived data and machine-specific captures.
