# Scene-native baseline and first ownership join

Status: SNR-00 and SNR-01 **in progress**. This records a reproducible
compatibility control and a bounded title/GPU evidence map. It authorizes no
scene admission, draw suppression or claim of native-renderer speedup.

## Qualified local control

The compatibility control used Pinyon
`a9ed5d5cda4cf19cd8bb5c3a9c83e6869c023115` on `dev`, with ShiftGlue
`bf7df82c6322d98b099e19909a8cfc657cfbea36`.
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

### Bounded source-frame packet probe

The default-off `pinyon_shift_snr01_trace_source_frame` probe observes one
source frame without changing guest state. The saved sustained-race route ran
to normal exit with target frame 6000 and executable SHA-256
`E932A4A6BB0F203CC901CDC8A3ABE2D19682A790262ADDC6D84ECB224EF3F388`.
The raw title packet log is local at
`.local/native-renderer/snr01/semantic-frame-6000/title-packets.log` (SHA-256
`03CCB835A58927FC27CB18724042CB39FE5648F36345AC8E55A6B91D632859A0`).
Its source-frame summary reports 42 generic indexed packets, 392 packets at
the two verified procedural emitter stores, 231 procedural item calls, zero
unmatched returns and zero unfinished scopes. Neither bound was hit (8192
packets, 4096 items). The probe is diagnostic, not a timing baseline.

The generic indexed wrapper produced **zero** packets within item scopes.
The procedural emitter instead produced 197 packets within 197 item calls:
186 at `0x82416260` and 11 at `0x824162F4`, across 36 observed receiver
addresses. Thirty-four calls produced no packet. The remaining 195
procedural-emitter packets occurred outside those item scopes; this may be
other callers or work stages and is not yet classified by view. All 392
packets used one observed command-owner register value, which identifies a
shared command context, not a render owner. Guest packet addresses and
header words are recorded for the later backend join. Counts from this run
are not a draw census for every view or route position.

### Exact packet address to prepared-draw join

The next default-off diagnostic adds the PM4 draw-header physical address,
command-buffer base, capacity and draw-end offset to ShiftGlue's prepared-draw
observation. The saved route again exited normally, using executable SHA-256
`1E165D50D34E4528F1B60C6214874419ACA9A45F8AE4AFAD93AACE93ED6511E8`.
The final SDK GPU DLL SHA-256 was
`1A41505285B1E8172DA5D71424A9D3F2350330C9CA8002FADC61E4FCB453AC09`.
The local combined log at
`.local/native-renderer/snr01/backend-join-final-frame-6000/title-backend-packets.log`
has SHA-256
`3B770AF21DC6780F0710C6E671578C770FA37585BCB9D6273B431042C1C9794E`.
This instrumented run saw 441 distinct procedural-emitter header addresses,
290 inside item scopes. Every one appeared in a prepared-draw callback in
backend frame 6001, while the title hook labelled its source frame 6000.
Every matched callback also satisfied
`(command_buffer + draw_end_offset - packet_physical) % command_bytes == 12`,
the three-word draw packet length. The match used the physical address and
buffer position, not a shader, attachment or image size. Backend frame 6000
preceded the title submissions and is not joined to them.

The 441 headers yielded 593 prepared-draw callbacks: 329 headers appeared
once, 72 twice and 40 three times. This shows repeated execution of packet
addresses; the exact replay/bin cause remains to be proved. Matched callbacks
span 26 shader pairs and render-target bit values 1, 2 and 3, so these
packets cannot be assumed to be one pass. Forty-five generic indexed-wrapper
headers did **not** match a prepared draw in frame 6001, and 4,285 of that
frame's 4,878 prepared draws matched neither observed title header class.
They remain unclassified; some may use other title emitters. The join proves
packet identity for this source frame, not view, material, resource generation,
visibility or complete coverage. This capture is diagnostic and must not be
used as a timing comparison.

### Receiver phases and emitter callers

An additional default-off source-frame 6000 capture ran to normal exit with
executable SHA-256
`146B63C46CE4936B32F0E018CA898D30647FAFA7D133AD3BEE110316A25F2562`.
The combined title/backend log is
`.local/native-renderer/snr01/emitter-caller-frame-6000/title-backend-emitter.log`
(SHA-256
`E89040F6801C2848DAC756511D5E7B90E790F4BCBC6349C88C72EE26B59644EF`).
The source `runtime.1.log` and `runtime.log` were both required because the
diagnostic output rotated at 5 MiB. Its summary reports 100 balanced
`CProceduralModels` slot-41 dispatch calls, nine balanced slot-40
render-state calls, 296 balanced item calls and 386 balanced emitter calls,
with no unfinished scope or trace cap hit.

The 100 slot-41 calls and 296 item calls share 44 distinct receiver
addresses and one observed graphics-context address, but **no item call or
draw packet is nested inside slot 41**. The nine slot-40 calls use one
aggregate receiver and contain all 296 item calls. The item path emits 235
packets; 61 items emit none. The other 151 procedural packets occur outside
slot 40. This separates two title phases and avoids treating the slot-41
receiver as the direct draw owner. The argument values on either path are
still unlabelled; a value such as 1 or 2 is not yet a view identity.

The original caller return address at `0x82415F6C` partitions all 386
emitter invocations and packet stores. Each packet passed the exact
physical-address and ring-buffer-position join in backend frame 6001:

| Caller LR / static function | Title packets | Prepared-draw callbacks | Item/render-state overlap | Distinct shader pairs | Observed target bits |
| --- | ---: | ---: | --- | ---: | --- |
| `0x82415D1C` / `sub_82415CE0` | 235 | 299 | all 235 | 8 | 1, 3 |
| `0x82412E1C` / `sub_82412DD8` | 129 | 213 | none | 7 | 1, 3 |
| `0x82442B64` / `sub_824426B8` | 22 | 22 | none | 11 | 2 |

The 386 title headers produced 534 backend callbacks because some packet
addresses execute more than once. Of 4,635 prepared draws in backend frame
6001, 4,101 matched none of these headers or the 44 generic-wrapper header
addresses. The generic headers also had no match in that frame. The three
caller functions are proven by the generated title code, but their scene
role, view, material and resource lifetimes remain unproved. A render-target
bit or shader family cannot substitute for those relationships.

The next runtime capture must carry a bounded title owner/generation, view,
record and selected LOD through final draw preparation and join the resulting
submissions to RenderDoc phase and resource identity.
Capture helper entry **and post-original state** so transforms/palettes are
not read before the title finishes them. Distinguish main, shadow and
reflection dispatch by owner/view relationships. Record unmatched title
entries and GPU draws on both sides of the join. Until this is demonstrated,
SNR-01 and Gate A stay open and no shader/attachment heuristic authorizes
suppression.
