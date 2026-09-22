# Scene-native baseline and first ownership join

Status: SNR-00 and SNR-01 **in progress**. This records a reproducible
compatibility control and a bounded title/GPU evidence map. It authorizes no
scene admission, draw suppression or claim of native-renderer speedup.

## Qualified local control

The current source is Pinyon `a9ed5d5cda4cf19cd8bb5c3a9c83e6869c023115`
on `dev`, with ShiftGlue `bf7df82c6322d98b099e19909a8cfc657cfbea36`.
The RelWithDebInfo build completed on 2026-09-22. The SDK build used
`tools/prepare-rexglue.ps1` to materialize `libmspack` symlink targets on
Windows; this leaves only generated vendor-file differences in the nested
checkout. The earlier uncommitted SDK profiling probes remained stashed and
were not part of the binary. The build profile labels the root dirty because
of the materialized nested checkout; hashes below identify the actual binary.

| Input | SHA-256 |
| --- | --- |
| `pinyon_shift.exe` | `F6B01AC3696417A4138288E0212ADF1E7C5412A3189F0F6CD1E869BAB5F82E32` |
| `rexgpu-fh1rd.dll` | `B98AFE02B10B101A10FF78DBF0AACC6403BAE945C61DFEF48D025509A9256DF7` |
| `rexruntimerd.dll` | `C5076E5C1152A31294FD6944BAB20D8F4330A98801C77D1E0A5C97E038CB54D2` |
| Installed native shader catalog v2 | `3C77C669F68F645B5F2B27351D1BB1054B98EE92A3AADE5057D5B2F428CAA5C2` |
| Installed native pipeline catalog v1 | `1FDE4F6EE2D727BA98459560668A1BADAF619B00C0FD49B63D485DFD50141D56` |
| Installed `pinyon_shift.toml` before control | `1684B2F632B04AEAC0DDF76C52E9453F6E9A43EBA0B0D81A356B6A22F2D5E8A4` |
| `fh1-race-sustained.fh1test` | `298C69DCD4A7A10DF05C8084258F61AE67147D1C166313DCF9056B67ACE85D19` |

The installed AppData preview profile is under
`%LOCALAPPDATA%/PinyonShift/source/0.1.0/.local/preview/user` and the verified
guest executable hash is `DB40DF605ADE49A612B35A7A24C38F6004BCB17A88ED6B48288DE16DF9E3987C`.
The installed host settings were D3D12, 1× scale, legacy occlusion queries,
vsync on, variable refresh/tearing off, no host FPS cap, source presentation
on, motion blur and depth of field off, anisotropy 3 and no swap post effect.
The display capture was 1280×720. Hardware: Ryzen 7 5800X, RTX 4080,
NVIDIA driver `32.0.15.8108`. These settings are part of the reference image
quality; changing them creates another baseline.

Launch with the checked AppData save and no existing `pinyon_shift` process:

```powershell
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
.\tools\launch-preview.ps1 -Configuration RelWithDebInfo `
  -StateRoot $stateRoot `
  -RenderTestScript config/render-tests/fh1-race-sustained.fh1test `
  -RenderTestOutput .local/native-renderer/snr00/<run-id> `
  -RenderTestTimeoutSeconds 240 -Hidden `
  -GameArgumentsJson '["--pinyon_shift_capture_performance=true"]' -Json
python tools/summarize-drive-window.py `
  .local/native-renderer/snr00/<run-id>/frames.perf.csv `
  .local/native-renderer/snr00/<run-id>/events.jsonl `
  --start race-moving --end race-sustained
```

The first and third controls were uncontended normal exits with seven valid
captures, no error event and 1280×720 output. Raw output images, event logs,
frame CSVs and summaries are local under `.local/native-renderer/snr00/`.
The second control followed the same route, but an unrelated static source
scan overlapped its timing window; it is retained for route evidence and
excluded from the timing-noise estimate.

| Control | Samples / wall | Start X,Z | End X,Z | Travel | Median | p95 | p99 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| A1 | 1,538 / 29.999 s | −1412.506, 2808.671 | −1747.420, 2644.752 | 372.9 m | 20.066 ms | 26.179 ms | 29.166 ms |
| A2, source scan overlapped | 1,519 / 30.018 s | −1412.961, 2808.890 | −1747.369, 2644.780 | 372.6 m | 20.239 ms | 27.029 ms | 30.146 ms |
| A3 | 1,544 / 30.019 s | −1412.948, 2808.877 | −1747.375, 2644.792 | 372.6 m | 20.060 ms | 25.638 ms | 29.114 ms |

A1 and A3 differ by 0.488 m at the start and 0.060 m at the end. Their
median, p95 and p99 differences are 0.030%, 2.088% and 0.178% of the pair
centres. These are **two pilot controls**, not the final control variation
for Gate B. The older 18.922 ms post-fix trace began around X = −1743 m,
so it is hotspot evidence, not a matched performance baseline for this route.

## Predeclared Gate B comparison

- Use the same 1× installed settings and source route, with compatibility
  control A and native candidate B. Run at least two warmed ABBA blocks with
  per-run source-aligned `race-moving` → `race-sustained` summaries. Keep
  diagnostic traces, RenderDoc and screenshot readbacks off in timing runs.
  Run cold startup and 3–5 minute streaming checks separately.
- Reject a pair whose starting pose differs by more than 2 m, ending pose by
  more than 5 m, simulation time by more than 1%, or whose route shows a
  collision/scene transition absent from its partner. Record exclusions rather
  than silently pairing different race positions. Compare one second of
  stationary traffic separately because moving-route car placement can vary.
- Let `A` be the median of the four per-run control medians and `B` the median
  of the four candidate medians. Define control variation as the range of the
  four A run medians divided by `A`. Gate B needs `(A−B)/A ≥ 15%` and greater
  than twice that observed variation. Candidate per-run p95 and p99 medians
  may rise by at most 3% and 5% versus controls, respectively. If control
  variation itself exceeds a tail limit, repeat controls; do not loosen the
  limit after seeing candidate results.
- Require complete scene content and current resource/pose generations. Check
  full-resolution reference crops covering road and grass edges, foliage
  alpha, player/traffic body and glass, shadow boundaries, sky/exposure, HUD
  and menus. Same-frame native and compatibility images are needed before
  judging shader parity; race screenshots from different runs are context,
  not pixel-perfect references. Count admission, unsupported full-frame
  fallback, repeated/dropped presents and simulation time.
- Record host commit and dedicated GPU memory across warm and 3–5 minute
  windows. Provisionally cap incremental committed/resident memory at 512 MiB
  each and steady-state growth after warmup at 64 MiB. Measure the actual
  control footprint before Gate B; a larger need must be justified and frozen
  before the candidate comparison, never after observing its performance.

The proposed first slice remains the full main-view opaque/alpha-tested
contribution and its color/depth interfaces. **SNR-00 is not closed:** exact
title view/pass membership and an image comparison set spanning all required
materials need SNR-01/02. The observed RenderDoc scene target below is a
candidate boundary, not a substitute for that proof.

## SNR-01 title-to-GPU evidence map

The source-frame hook at `0x829EFEB8` observes FH1's sole `VdSwap`. The
read-only title hooks at `0x8240F4D8` and `0x82410328` observe the indexed
emitter and exact PM4 draw-header publication. The current SDK
`GraphicsPreparedDrawObservation` carries frame sequence, shader hashes,
index buffer/range and prepared state, but no title owner/view identity.
The current GPU census is therefore structural and cannot label a material
or connect a RenderDoc event to a title object by itself.

The freshly regenerated static dispatch inventory at
`.local/native-renderer/snr01/dispatch-static-with-image.json` (SHA-256
`640D9B643806F12705DFA5B680663FA1DC9EC0A12D83772263E008899DBDD1EF`)
identifies `proceduralGeometry::CProceduralModels` through RTTI and verifies
the `0x82417418` per-record helper. Candidate read-only boundaries are helper
entry `0x8241741C`, final return `0x82417B80`, render-state entry/return
`0x824170DC`/`0x82417410`, and geometry submission `0x82417B60` leading
through `0x82415CE0` to emitter `0x82415F68`. The inventory explicitly says
mesh/material ownership, LOD meaning, runtime view join and graphics target
join remain unproved. The separate `0x82BC5A3C` vehicle pose hook is shared
by player and traffic and does not identify the player render owner.

The local RenderDoc race frame at
`.local/cpu-profile/traffic-attribution/race-start-capture_frame4709.rdc`
has 5,439 draw actions. Its payload-free trace shows two preceding depth
producer ranges (1,079 draws on D24S8 `ResourceId::8655`, 1,094 on D32S8
`ResourceId::6980`) and a 2,579-draw 4×MSAA scene-color phase on color/depth
`ResourceId::2487/2488`. Both depth resources have later compute/pixel readers;
the color output has ten later pixel readers. These are resource dependencies,
not proof of camera identity or which individual draw is visible. See the
[race-frame attribution](CPU_HOTSPOT_RESULTS_2026-09-21.md#renderdoc-race-frame-producer-and-consumer-join--2026-09-22).

The next runtime capture must carry a bounded title owner/generation, view,
record and selected LOD through final draw preparation and join those exact
submissions to prepared draw sequence and RenderDoc phase. Capture helper
entry **and post-original state** so transforms/palettes are not read before
the title finishes them. Distinguish main, shadow and reflection dispatch by
owner/view relationships. Record unmatched title entries and GPU draws on
both sides of the join. Until this is demonstrated, SNR-01 and Gate A stay
open and no shader/attachment heuristic authorizes suppression.
