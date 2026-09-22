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

### Frozen pilot visual reference regions

The A1 control produced four 1280×720, full-resolution PPM images that fix
review locations for the initial compatibility reference. They are local
under `.local/native-renderer/snr00/control-a1/`; rerun the frozen route
above to reproduce them. Hashes identify this exact set, not a claim that
independent race replays produce identical pixels.

| Image | SHA-256 | Review rectangles `(x, y, width, height)` |
| --- | --- | --- |
| `event-entered.ppm` | `55809BC9219B7B0F58B0FAAD6C1FCE76E4330B3FBEA1C6BEB98E464F1C57D3A7` | Festival menu/text `(220, 155, 825, 390)`; car behind UI `(0, 285, 1270, 375)` |
| `race-ready.ppm` | `2627D7B42326DF4E400752B755798BE82EEE44A7E2EE247A93C12E48E44BE184` | Traffic body/glass `(500, 245, 580, 200)`; player body/glass `(470, 375, 335, 325)`; road/shadow `(235, 385, 660, 330)` |
| `race-moving.ppm` | `A9DF949B91428EACB79C45641398C7D38A8A5B11C05DC42F3E28E5296E8CE80D` | Road/terrain boundary `(0, 255, 620, 465)`; grass and fence edges `(810, 265, 390, 260)`; vehicle/shadow `(475, 380, 395, 340)`; sky/exposure `(255, 0, 700, 285)` |
| `race-sustained.ppm` | `FCD747EA54ECAABE4BDB8A57C9C1EDBB05373BAD02E63DAC642A1982A38BE4D1` | Grass/crowd alpha edges `(0, 255, 485, 365)`; player paint/glass `(465, 380, 350, 295)`; lit barriers and shadow `(180, 340, 950, 360)` |

All four show HUD, with the race timer/place in the upper corners and
speedometer at lower right during driving. `race-moving.ppm` captures the
vehicle in motion; the installed settings disable motion blur, so it is not
a blur reference. The menu image is a compatibility-only mode for the
proposed main-view slice. Mirrors, photo mode, and any uncovered reflections
still require explicit whole-frame compatibility behavior. These rectangles
are visual review targets; Gate B still requires same-frame native and
compatibility images and title-proved pass membership before judging parity.

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
an exact address/packet-position correlation, not a unique producer
generation: buffers can reuse the same physical address across frames. It
does not prove view, material, resource generation, visibility or complete
coverage. This capture is diagnostic and must not be used as a timing
comparison.

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

### Item record and final submission join

The next saved-route capture exited normally with executable SHA-256
`036EAC24EA4183D1C7DD39A41F1135A757D37F89C8F5FCF16A878D7840397153`.
The local combined log is
`.local/native-renderer/snr01/record-submission-frame-6000/title-backend-records.log`
(SHA-256
`E9C3A6C903B235F303A5FA07FD3ACD1C27D6E76F047F89EB192F1B87ADBA3E34`);
both rotated runtime log files were needed. Read-only hooks observe the
title-selected descriptor at `0x82417684`, runtime record at `0x824176BC`
and final graphics call arguments at `0x82417B7C`. These instructions are
verified in the generated item helper; the trace captures values after the
title computes them and changes no guest state.

For source frame 6000, all 353 item calls observed both records. Across 47
distinct item receiver objects, `descriptor_address - 92 × descriptor_index`
and `runtime_address - 68 × descriptor_index` each yielded one stable base
per receiver. No observed base was shared by two receivers in this frame.
The descriptor kind values were 0 (292 records), 4 (9) and 5 (52). These
are title enum values, **not** proven material roles. The final graphics
call occurred for 292 items and did not occur for 61; every submitted item
emitted exactly one procedural packet, and no non-submitted item did. All
292 packet addresses matched 353 prepared-draw callbacks in backend frame
6001 after repeated packet execution. The other 163 procedural packets came
from the two non-item emitter callers and matched 268 backend callbacks.
The 45 generic-wrapper headers again had no match; 4,341 of 4,962 prepared
draws in backend frame 6001 matched neither observed class.

This proves the observed receiver → selected descriptor/runtime record →
graphics call → PM4 header chain in the title, and an address correlation
to prepared draws in the backend. Cross-frame address reuse prevents a
unique producer-generation claim. It does not prove that the 61
non-submitted items were intentionally
culled, what the descriptor kind means, which view owns the calls, or how
addresses behave across unload/reload and reuse. The final graphics call's
`r5` and `r6` values remain raw arguments until their contract is verified.

### Active higher-level caller paths

The wrapper-caller capture exited normally with executable SHA-256
`4AA263EB5B608EF98EDE091586B2B06E89E0A9343881612EC7AD3C6EDEFBB94F`.
Its combined rotated log is
`.local/native-renderer/snr01/wrapper-caller-frame-6000/title-backend-wrapper.log`
(SHA-256
`D653055235DD21659A5342E04EA4250F4C0754C35AA615022B6417E6BBFC933C`).
Hooks just after the opening `mflr` in `sub_8243D2A0` and `sub_8243BD40`
record their original caller return addresses. Static generated code shows
these wrappers invoke vtable slots 40 and 41, respectively. They can also
invoke other implementations; a wrapper call alone is not a procedural draw.

In source frame 6000, argument equality and immediate call nesting joined
all nine actual `CProceduralModels` slot-40 calls to their wrapper invocation:
eight came from `sub_82439B70` at return `0x8243ABC8`, one from
`sub_8240E7B0` at `0x8240EC80`. The 108 actual slot-41 calls split 94
from `sub_82439B70` at `0x8243AD70` and 14 from `sub_8240E7B0` at
`0x8240ED14`. The third static wrapper caller, `sub_82DEF2B0`, was observed
at wrapper entry but did not invoke these procedural receiver methods in
this frame. The trace reports balanced procedural scopes and 416 emitter
packets. This identifies the live parent functions for the saved route, but
their camera/view and pass semantics still need to be recovered from their
own inputs and title relationships.

The existing `discover-native-renderer-track-ingress.py` static check passes
against the generated title and extracted image. RTTI identifies
`Presentation_Unified::CTrackPresentation` at vtable `0x82243774`; its
derived slots 75 and 79 point to `sub_82439B70` and `sub_8240E7B0`.
`discover-native-renderer-direct-indexed-producers.py` also verifies that
both functions call the unified track presentation helper `0x82436468`.
The local check outputs are
`.local/native-renderer/snr01/track-ingress-static.json` and
`.local/native-renderer/snr01/direct-indexed-static.json`. This makes the
two live parent functions track-presentation paths, but does not establish
which camera/view invoked each slot or that every procedural receiver is a
track mesh.

### Presentation-view scheduling boundary

Two more normal-exit saved-route captures observed source frame 6000 with
read-only hooks at the track-presentation slot-75/79 entries and at their
guarded slot-75 helper. The final capture used executable SHA-256
`F44396CFA02BF4D7DDCE71EE23A1CF62EBA0EC7653BAA6C8BC665C74E0E71494F`.
The logs are local at
`.local/native-renderer/snr01/track-entry-frame-6000/title-track.log`
(SHA-256 `91725B5AAE1F5DB668FEBC78A5F9E4CCB1E89E9F6889C289FBA7A05971066855`)
and `.local/native-renderer/snr01/track-pass-frame-6000/title-track-pass.log`
(SHA-256 `EE22F8C0EEB0D49E6625B060FE879DB077E418331E603AEC36AE9EF612FEA81A`).
The latter reports 19 slot-75 calls, two slot-79 calls, 19 helper calls,
346 procedural items, 441 emitter packets and balanced scopes. The former
reports 19 slot-75 calls, one slot-79 call and balanced scopes. These are
different route replays, so their call counts are not interchangeable.

The regenerated track-ingress static check (local output
`.local/native-renderer/snr01/track-ingress-static.json`, SHA-256
`1FF5BF64E4C8554C5309B00716E7A6925562AF2F6068B42CB7B8A95B30752549`)
verifies RTTI for `CPresentationView` and its refcounted form at vtables
`0x8200265C` and `0x8200255C`. Both slot 13 entries point to
`sub_82444E60`. Its generated code contains six direct calls to guarded
helper `sub_8244CA98`, which obtains the nested track-presentation receiver
from the view object's state and invokes vtable slot 75. In the final
capture, each of the 19 helper entries was immediately followed by one
slot-75 entry with matching outer receiver, context and selected raw
arguments. No helper entry was left unmatched. The 19 helper entries came
from six return sites in `sub_82444E60`:

| Return site | Calls | Raw argument group |
| --- | ---: | --- |
| `0x82445B14` | 8 | `r7=1, r8=0` |
| `0x82445B68` | 1 | `r7=2, r8=2` |
| `0x82445CD0` | 7 | `r7=8, r8=0` |
| `0x82445F18` | 1 | `r7=2, r8=1` |
| `0x82445FE8` | 1 | `r7=16, r8=3` |
| `0x82446008` | 1 | `r7=32768, r8=4` |

The helper can change other arguments before the vtable call; in particular
its `r6` and `r8` must not be equated blindly with the slot-75 entry's
registers. The static view relationship narrows the title scheduling
boundary, but the captured outer receiver's runtime vtable, camera object,
meaning of the raw argument groups and their graphics passes remain
unverified. Neither slot-79 invocation in the final frame is yet joined to
a specific visible-list entry. This is not a complete main-view census.

### Direct indexed packet coverage and remaining gap

The verified direct indexed emitter `sub_82416380` is a third PM4 draw
producer, separate from the generic wrapper and procedural emitter. The
updated static verifier checks its two draw-header stores at `0x824166E4`
and `0x82416774`, common exit `0x824167EC`, and 13 direct caller sites.
Its local output is `.local/native-renderer/snr01/direct-indexed-static.json`
(SHA-256 `8427DB3762EAFF57A0BC8989CCF5114AA04CE1118AE545B487356A272484ABF0`).

A default-off, read-only trace on the sustained race exited normally with
executable SHA-256
`C9CBAE6D1185B963BE29CF7927F352FFCCF17BAF1309C1A7FD5010C9DB37B0F6`.
The combined rotated log is
`.local/native-renderer/snr01/direct-packet-frame-6000/title-backend-direct.log`
(SHA-256 `15C260B49C642C3DB252539042A92C01FF6367B0DF7D94CACF588CD1A6A80920`).
In source frame 6000, two title threads made 552 direct-emitter calls and
published exactly one draw header each: 506 at the primary store and 46 at
the secondary store. The swap thread's summary reports only its own 338
calls; the other thread made 214. Both threads' call scopes balanced, and
neither per-thread packet limit was reached. Direct call ordinals are local
to each thread and must be paired with the thread ID in the log prefix.

The live direct callers were vector font (`0x82412D90`: 162), D3D9 device
helpers (`0x824131F4`: 88; `0x823F59C8`: 9), navigation-map renderer
(`0x8240F020`: 67) and a title graphics helper (`0x8243C8FC`: 226).
The statically verified unified track-mesh caller `0x82C5B038` did not
occur in this frame. These names classify the immediate source functions;
they do not label the visual content of each backend draw.

All 552 direct header physical addresses exactly matched prepared-draw
callbacks in backend frame 6001, accounting for 746 callbacks after some
buffers were executed more than once. The 406 procedural headers matched
586 callbacks; 44 generic-wrapper headers matched none. The three packet
classes had no shared addresses. Of 4,908 prepared callbacks, **3,576**
matched none of these classes. Those unmatched callbacks span 768 observed
command-buffer base addresses; their raw render-target-binding bits were
3 for 2,437 callbacks, 1 for 1,134 and 2 for five. Those bits are binding
shape, not proven view or pass identity. The direct emitter was worth
checking, but it does not close the main scene coverage gap. Next work must
recover how the many other command buffers are produced and pair their
title owner/view with backend packet identity; adding shader or target
heuristics would not establish that join.

### Additional draw-header writers

The updated static check verifies stores in `sub_8240DC70` at
`0x8240E01C`/`0x8240E0B0`, `sub_82408B70` at
`0x82408F7C`/`0x8240900C`, and `sub_829F0928` at `0x829F0A4C`.
Its local output SHA-256 is
`1F42E53D0E5C529FA969BB3ECB2D7A3CF5D3F0B90B554320240EF639DF6F139A`.
The new default-off hooks preserve the title's original code and record
only header address, word, raw command context and producer site.

The sustained-route replay exited normally with executable SHA-256
`8AC5F1386C64021DDB7E7CEEE86CF4FE128261DA652F3FFDDB26050C09EDFCE0`.
Its combined log is
`.local/native-renderer/snr01/extra-packet-frame-6000/title-backend-extra.log`
(SHA-256 `C8164EDE13B5AE520F5224FA7150620F61F4B8F9E9630CEA0175C89CE27356F9`).
Source frame 6000 published 15 headers in `sub_8240DC70` (four primary,
11 secondary), 11 primary headers in `sub_82408B70`, and none at
`0x829F0A4C`. Every one of these 26 header addresses appeared in backend
frame 6001, accounting for 48 prepared callbacks. The prior direct emitter
published 449 headers that matched 690 callbacks; 386 procedural headers
matched 510; 41 generic-wrapper headers matched none. The six address
classes were disjoint in this replay. Of 4,621 prepared callbacks, 3,373
still matched no observed header address. These extra sites therefore do
not close the coverage gap, and their title owner/view roles remain open.

There is direct evidence that physical address alone is not a generation
key: 166 addresses published by the direct emitter in source frame 6000
also appear in backend frame 5999, before this frame's publication hooks
ran. Backend frame 6000 had no address overlap with the source-6000 set;
frame 6001 did. Future joins must include command-buffer submission and
reuse generation or ordering evidence. A bounded earlier-frame capture can
test whether the remaining backend buffers were recorded before source
frame 6000, but an earlier address match by itself would still be
insufficient for native admission.

The next runtime capture must carry a bounded title owner/generation, view,
record and selected LOD through final draw preparation and join the resulting
submissions to RenderDoc phase and resource identity.
Capture helper entry **and post-original state** so transforms/palettes are
not read before the title finishes them. Distinguish main, shadow and
reflection dispatch by owner/view relationships. Record unmatched title
entries and GPU draws on both sides of the join. Until this is demonstrated,
SNR-01 and Gate A stay open and no shader/attachment heuristic authorizes
suppression.

### Backend indirect-buffer execution graph

Prepared-draw observations now carry an indirect-buffer execution ID, parent
execution ID, and the dispatch packet's physical address. The command
processor assigns a fresh ID on each indirect dispatch and restores its
parent context after nested execution. This identifies repeated executions
of the same physical buffer without changing the draw path. The default-off
SNR-01 trace logs these fields alongside the draw packet and command buffer.

The RelWithDebInfo build completed, and the saved sustained-race route exited
normally. The executable SHA-256 was
`C1C5BA1F45DF3DBFD245E3577C5E5B448248AB37558FEC82BEB64088C7C15BBE`.
The combined rotated log is
`.local/native-renderer/snr01/indirect-dispatch-frame-6000/title-backend-dispatch.log`
(SHA-256 `16D84CC90020C59B663826A0D7845661E920552E1D0E98C919589BB654A5C588`).
Backend frames 5999, 6000 and 6001 reported 4,965, 4,759 and 5,122
prepared callbacks across 1,493, 1,458 and 1,572 draw-bearing indirect
executions, respectively. All observed execution IDs and dispatch addresses
were nonzero; no execution ID recurred across these frames. Within each
frame, every execution ID mapped to exactly one parent, dispatch address,
command-buffer address and size.

In backend frame 6001, 3,986 callbacks had a nonzero parent execution ID.
Of the 1,572 draw-bearing executions, 1,122 had a parent that also produced
a prepared draw; every one of those child dispatch packets lay within the
parent's observed command-buffer range. The other parent executions cannot
be checked by this draw-only observation. Across that frame, 833 draw packet
physical addresses occurred under more than one execution ID, with as many
as 85 executions sharing one address. Physical address alone therefore
cannot identify a draw generation.

Comparing the bounded source-frame-6000 header probes with backend frame
6001 produced 1,334 address-matched and 3,788 unmatched callbacks. Only 23
draw-bearing executions had all callback addresses matched; four were mixed
and 1,545 had none matched. These are address correlations, not title-owner
or generation joins. The backend execution graph is established, but title
command-buffer submission, owner/view, record and LOD still need a bounded
join to these executions before SNR-01 or Gate A can close.

### Complete dispatch hierarchy and primary-ring publication

The draw-only observation omits indirect executions that produce no prepared
draw, including some parents of draw-bearing buffers. A separate default-off
observer now records every indirect dispatch. The saved race exited normally
with executable SHA-256
`4D52B0C637EC38CEFF2CF5EA45AEB55FB07CF6BDD4E893E523D5BCB090673658`.
The local combined log is
`.local/native-renderer/snr01/indirect-full-graph-frame-6000/title-backend-full-graph.log`
(SHA-256 `65E3CF22309C06BA7469FEEABD530C9CDC5093F4159D5C51E0E64E4C7D59B9F4`).
Backend frame 6001 contained 1,637 unique indirect executions, 5,397
prepared draws and 133 top-level dispatches. Only 29 roots had prepared
draws; 167 executions had none. Every draw resolved to a root, every parent
ID was present, and every child dispatch packet lay inside its parent's
command-buffer range. Draw ancestry was one or two indirect levels deep.
Neither 8,192-event diagnostic cap was reached. This establishes backend
hierarchy for that bounded frame, not title ownership.

Generated title code identifies `sub_82409398` as the primary-ring indirect
packet writer. Its `0x824095B0` site computes the header address from the
ring base and word cursor, writes `0xC0013F00`, then writes the target and
length. Read-only hooks capture that write site and its caller. Static call
sites at `0x82409838` in `sub_82409668` and `0x829F6308` in
`sub_829F5FF0` are the two observed immediate paths. The caller names are
source functions, not view or scene-owner labels.

The final two-source-frame replay exited normally with executable SHA-256
`3BFCE0CFB1AF4816C894A6063C3366A616A9841D9757F56F4917E769C8E86522`.
Its combined log is
`.local/native-renderer/snr01/primary-caller-frame-6000/title-backend-caller.log`
(SHA-256 `1F41FE50568B3FC3B74084AE94D741FB36936325E7BC7065BCB94ABBFC9239C4`).
Source frames 6000 and 6001 wrote 132 and 133 primary indirect packets.
Across both source frames, 168 calls came from `0x82409838` and 97 from
`0x829F6308`; all used one observed device pointer, and each call submitted
one entry. Backend frame 6001 had 1,620 indirect executions, 133 roots and
5,145 prepared draws. Every root matched exactly one earlier title packet
address, with the same target command-buffer address. Of those roots, 102
were written in source frame 6000 and 31 in source frame 6001; they account
for 1,943 and 3,202 prepared draws respectively. The address, target and
ordering checks passed for every root, with no trace cap hit.

| Source frame / immediate caller | Backend-6001 roots | Roots with draws | Prepared draws |
| --- | ---: | ---: | ---: |
| 6000 / `0x82409838` | 84 | 8 | 1,943 |
| 6000 / `0x829F6308` | 18 | 0 | 0 |
| 6001 / `0x829F6308` | 31 | 21 | 3,202 |

This partitions the observed backend work by immediate title submission
path, but a no-draw root can still contain clears, copies, state or other
effects. The table does not identify scene views or safe replacement cuts.
Reproduce the check with:

```powershell
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/primary-caller-frame-6000/title-backend-caller.log `
  --source-frames 6000 6001 --backend-frame 6001
```

Log rotation removed the beginning of backend frame 6000 in this final
capture, so the complete title-to-root claim applies only to backend frame
6001. The exact bounded submission join does not yet identify the upstream
view, visible-list entry, selected LOD, material or allocation generation.
Trace the two immediate callers back to their queue producers and title
owners before using this chain for native scene admission or draw suppression.

### Queue helper caller split

The generated `sub_82409668` queues a target and may submit it directly to
`sub_82409398`. Its common exit is `0x82409838`. A read-only scope records
the helper's caller for each primary-ring packet, including calls that cross
the source-frame boundary. The replay exited normally with executable
SHA-256 `FB8FE05B05EB198582023F908622D1F2F2CC1291BC8F9E5F62160692F66D05BE`.
The local combined log is
`.local/native-renderer/snr01/queued-caller-frame-6000/title-backend-queued.log`
(SHA-256 `99A9B894965B3C05C288A30EB9AC92E6FB15EAA67B7666BF06A33C0939DDE7C0`).
The indirect-join verifier again passed: source frames 6000/6001 each wrote
133 primary packets, and all 133 backend-6001 roots were matched by unique
address, target and order. That backend frame contained 1,621 indirect
executions and 5,133 prepared draws, with no trace cap hit.

| Source frame / title caller path | Backend-6001 roots | Roots with draws | Prepared draws |
| --- | ---: | ---: | ---: |
| 6000 / `sub_8240CF68` → `0x8240CFF8` | 41 | 0 | 0 |
| 6000 / `sub_8240D070` → `0x8240D1B0` | 41 | 8 | 1,860 |
| 6000 / `sub_82469290` → `0x824693E4` / `0x82469434` | 2 | 0 | 0 |
| 6000 / `sub_829F5FF0` → `0x829F6308` | 18 | 0 | 0 |
| 6001 / `sub_829F5FF0` → `0x829F6308` | 31 | 19 | 3,273 |

The static code shows `sub_8240D070` computes a command-buffer length from
the device's command start and write cursor before calling the queued helper.
`sub_829F5FF0` interprets command words and submits an indirect target at
its `0x829F6308` site. Thus these caller sites classify device-level
publication paths, not the scene owner that originally recorded a buffer.
No-draw roots may still perform clears, copies or state changes. The next
join must follow queue/command-buffer production back to the view and its
visible objects; adding more device-flush callers alone cannot prove SNR-01.

### Presentation-view and track-presenter boundary

Static RTTI and the generated call site identify `sub_82444E60` as
`CPresentationView` virtual slot 13. Its `sub_8244CA98` path reads the
view state at `view+4`, loads a nested `CTrackPresentation` pointer from
`state+36`, and passes the outer view to track-presentation slot 75. The
default-off, read-only hooks now record view entry, selection, track link and
common exit. The selected-context pointer and numeric view arguments remain
raw observations; they are not camera, pass or LOD labels.

The saved race exited normally with the RelWithDebInfo executable SHA-256
`CEEEAC33737C238D483554213FF31CBF12D0CF82DCFFDD78CB661750C71568C1`.
The combined local log is
`.local/native-renderer/snr01/view-scope-frame-6000-probed/title-backend-view-scope.log`
(SHA-256 `9B21DE65BB68F8BF2CAFE04D9A1B226DD224173FD785CCF38927685632423521`).
The eight source-frame-6000 view calls had one view pointer, `0x43F84EC0`,
and matched eight exits on one title thread. The entry callers were
`0x823FA398` once, `0x8240A154` six times, and `0x8245032C` once. The
six middle calls used raw argument values `0, 4, 2, 1, 3, 5`. All eight
selection events observed context pointer `0x2E02E000`. All 19 track-link
events resolved the same view through state `0x41BEBCE0` to presenter
`0x41E40120`; 19 slot-75 calls carried the view in argument 9, and two
slot-79 calls carried it in argument 5. These pointers are capture-local.

The entry/exit scopes contained 282 of 374 semantic packets, 366 of 646
direct packet events across all threads, and only 6 of 130 primary indirect
packets in source frame 6000. The per-call semantic/direct/primary counts
were `84/160/4`, `11/1/2`, `10/1/0`, `11/1/0`, `7/1/0`,
`5/1/0`, `11/1/0`, and `143/200/0`. Scope ranges matched every packet
ordinal on the view thread, with no unmatched view entry or exit. The
existing indirect-join verifier also passed: backend frame 6001 had 131
top-level roots, 1,624 indirect executions and 5,180 prepared draws;
all roots joined to source-frame-6000/6001 title packets.

```powershell
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/view-scope-frame-6000-probed/title-backend-view-scope.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The scoped calls do not cover most primary-ring publication. Some work may
be deferred, interleaved or performed by another title path; the capture
does not establish which. The next SNR-01 probe must join view/visible-list
entries to the command-buffer production and queue path, then to the exact
primary packets and backend draws. Do not infer main-view completeness or
safe draw suppression from the presenter-pointer relationship alone.

An address-range check supplies a narrower candidate join without another
hook. Every source-frame-6000 semantic and direct packet header lay inside at
least one backend-frame-6001 root command-buffer range. Mapping only the
packets within view scopes gave 15 distinct roots (7 distinct buffer ranges)
and 3,023 descendant prepared draws. Calls 1–7 reached three roots published
in source frame 6000 by the `0x8240D1B0` device path; call 8 reached twelve
roots published in source frame 6001 by the `0x829F6308` interpreter path.
The latter twelve are three executions each of four buffer ranges, so a
packet address alone cannot select one execution. This is a buffer-membership
candidate, not proof that every descendant draw belongs to the view call:
the buffer can contain packets recorded outside that scope, and address reuse
needs lifetime evidence. Capture exact buffer record/submit boundaries and
the visible-list owner before promoting these candidates to an ownership map.

### Track bucket entries to draw packets

`CTrackPresentation` slot 75 (`sub_82439B70`) indexes a pair of pointers at
`presenter + 56808 + 16 * (5 * arg5 + arg6)`. Their difference is divided
by 20, and the loop at `0x8243AB5C` visits that many 20-byte entries. It
first reads a pointer from entry word 0; a second branch reads entry word 1.
This is an authoritative title-side record traversal, but its pointer types,
record ownership and selected LOD remain unknown. Read-only hooks at
`0x8243AB64`, `0x8243AC8C` and `0x8243AD74` bracket each iteration and
record which pointer path it took and the packet ordinals emitted within it.

The final saved race exited normally with executable SHA-256
`F072059784D4689D9E067EC9CF81F0372FAB4B3D7010511E364E0C9EEDFD0C1C`.
Its local combined log is
`.local/native-renderer/snr01/track-bucket-secondary-frame-6000/title-backend-track-bucket-secondary.log`
(SHA-256 `D1FA08572A6E329C9EBC625CD6510CF5784F360978B5E887876E35544B2FBC44`).
Source frame 6000 had 445 logged entries, with no cap hit, unfinished scope
or unmatched exit. All had one view pointer (`0x4311F710`) and one nested
presenter (`0x41B10010`); every entry occurred inside a matching view call.
The bucket offset formula matched the observed slot-75 arguments. The eight
view calls contained `156, 10, 9, 8, 11, 6, 12, 233` entries respectively.

| Pointer path | Entries | Entries with packets | Distinct packet headers | Backend-6001 prepared-draw callbacks |
| --- | ---: | ---: | ---: | ---: |
| First word | 314 | 8 | 209 | 294 |
| Second word | 131 | 36 | 116 | 201 |
| Total | 445 | 44 | 325 | 495 |

The verifier checks that the two paths are exclusive, every scoped packet
ordinal exists exactly once on the same title thread, packet physical
addresses are distinct, and every one has at least one exact backend
prepared-draw packet-address match. The indirect-join verifier separately
matched all 132 backend-frame-6001 roots to title primary-ring packets;
that frame had 1,623 indirect executions and 5,123 prepared draws.

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/track-bucket-secondary-frame-6000/title-backend-track-bucket-secondary.log `
  --source-frame 6000 --backend-frame 6001
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/track-bucket-secondary-frame-6000/title-backend-track-bucket-secondary.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The other 401 entries produced no *observed semantic or direct* packet
inside their iteration. That is not yet evidence of intentional culling:
other work may be deferred, emitted by another path, or skipped for a
reason not captured here. Packet-address reuse across frames and record
allocation lifetime also remain unproven. This closes a bounded
view → presenter → raw bucket entry → PM4 header → backend draw chain for
325 packets, but it does not yet name mesh/instance, material, final
transform, LOD or pass, nor account for all draws in the selected view.

### Track bucket model identity and early guards

Static code following the 20-byte entry resolves the first pointer's `+4`
object and calls its vtable slot 13 through `sub_82413240`. The second path
calls `sub_8243F328` on entry word 1, then reads entry word 3 and byte 16
before `sub_8243BD40`. The first path passes its record to `sub_82436468`;
the second passes the resolved object and auxiliary fields to
`sub_8243BD40`. These are two different dispatch paths, not equivalent
fallbacks. The existing RTTI image verifier identifies vtable `0x82001D74`
as `Presentation_Unified::CTrackRenderModel_Unified`, with slot 13 at
`sub_82413228`. The verifier output is local at
`.local/native-renderer/snr01/track-ingress-identity-static.json`.

Read-only hooks at `0x8241325C`, `0x8243AB74`, `0x8243AC9C` and
`0x8243AD40` captured the live model vtable, first-path guard result,
second-path resolved pointer and auxiliary fields within each record scope.
The saved race exited normally with executable SHA-256
`04EE7F4C07A7CD3BC531A87D34984BB3B77D6EAAECA0D12D78447B14261F0932`.
The combined log is
`.local/native-renderer/snr01/track-bucket-identity-frame-6000/title-backend-track-bucket-identity.log`
(SHA-256 `82E21D046BB77926AD641892B1BC241509F9F9FC1BF5A34245EE501D6338F22C`).

This replay had 403 balanced bucket iterations. All 264 first-path entries
had a nonzero model object with vtable `0x82001D74`; all 264 early virtual
guards returned true, but only eight entries emitted observed packets.
All 139 second-path entries resolved a nonzero object and reached the
auxiliary-field read, but only 40 emitted observed packets. Entry word 3
was nonzero for 54 second-path entries. The captured byte-16 values were
`1` (82), `2` (45), `7` (6), `4` (4) and `6` (2); their meanings are not
established. The 48 packet-producing entries emitted 338 distinct headers,
all exactly joined to 509 backend-frame-6001 prepared-draw callbacks. The
indirect-join verifier also passed for all 131 backend roots, 1,581
executions and 4,767 prepared draws in that frame.

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/track-bucket-identity-frame-6000/title-backend-track-bucket-identity.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/track-bucket-identity-frame-6000/title-backend-track-bucket-identity.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The two early checks cannot classify the remaining 355 entries as culled:
256 first-path guards passed and 99 second-path objects resolved without
an observed packet inside that iteration. The next ownership join must
follow the selected model/auxiliary records into their concrete geometry,
LOD and material submissions, and separately account for deferred or other
packet producers before assigning an intentional-cull reason.

### Procedural item node to descriptor and packet

The generated `sub_824170D8` loop traverses six linked-list heads. At
`0x824171AC`, it reads node word 1 as an index, word 2 as an argument, and
word 0 as the item receiver. It stores the index at caller stack offset 84,
calls `sub_82417418` at `0x824171D4`, and advances through node word 3 after
the return at `0x824171D8`. The callee uses that index to address 92-byte
descriptor and 68-byte runtime-record arrays. This proves what the index
selects; it does **not** establish that the index means LOD.

Read-only hooks around that call captured node identity, list head,
receiver, index, view and track-bucket scope, and the procedural-item and
semantic-packet ranges. The saved sustained race exited normally with
executable SHA-256
`90695F45ECCB2D9D1F4D4EF90DF9520E6ACA6C9DED5C151D5A7E396C7F75E9C3`.
The combined log is
`.local/native-renderer/snr01/item-node-frame-6000/title-backend-item-node.log`
(SHA-256 `90920A6E4DDA44DA24756995BADAFB7AE1C5A6CEE3911A246F89DE45B3756D95`).

Source frame 6000 had 350 balanced item-node scopes and 350 item calls,
with one-to-one receiver/index matches. Of these, 269 nodes occurred inside
one of eight observed presentation views and a first-path track bucket.
Exactly 208 submitted one semantic packet each; all 208 packets have exact
backend-frame-6001 prepared-draw packet-address matches. The other 61
resolved both descriptor and runtime record but submitted no observed
semantic packet. Their descriptor kind was 0; no culling reason is yet
proven. The remaining 81 nodes submitted packets outside those view scopes.
Three of six static list heads were active in this frame. Per item receiver,
the descriptor and runtime array bases calculated from the index stayed
stable. The second track-bucket path did not produce a procedural-item call
in this capture; its 117 packets need a separate ownership join.

At the helper's final indirect call (`0x82417B7C`), vtable offset 160
receives literal `13` in `r4`, four times runtime-record word 7 in `r5`, and
either runtime-record word 6 or word 8 in `r6` (depending on an earlier
branch). For every submitted first-path item in this capture, the exact
backend draw's `index_count` was `4 × r6`, including packets expanded to
multiple prepared-draw callbacks. The same invariant passed the two earlier
race captures (196 and 209 first-path items). This identifies a bounded
count relationship, not yet the mesh payload, topology or semantic meaning
of literal `13`.

The track-bucket verifier now checks node/item balance, receiver/index and
packet-range equality, bucket and view ancestry, descriptor/runtime base
stability, and exact backend draw joins. The indirect-join verifier also
passed for 133 backend roots, 1,616 indirect executions and 5,242 prepared
draws. Both verifiers are runnable on the log above:

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/item-node-frame-6000/title-backend-item-node.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/item-node-frame-6000/title-backend-item-node.log `
  --source-frames 6000 6001 --backend-frame 6001
```

This closes a bounded linked node → descriptor/runtime record → PM4 header
→ backend draw path for the first track-bucket path. The next probe must
identify geometry payload, material, transform and pass at the submit call,
and trace the second bucket path. The 61 non-submitting nodes and other
packet producers remain unclassified; SNR-01 and Gate A stay open.

### Descriptor resource keys and resolver returns

Before the final draw call, `sub_82417418` reads descriptor words 0 and 1
as indices into the receiver's table at `+8`. It passes the selected table
value to `sub_82415BF8` with slot 0 or optional slot 1. That helper caches
the key per slot and, on a change, calls `sub_82415AD0`; its returned object
is passed to a render-context virtual call at vtable offset 88. The object
type and semantic resource role are not yet proven.

Read-only hooks at the two call sites and the resolver return captured a
second saved-race replay. It exited normally with executable SHA-256
`9DC46A97B54155BCB6A9BAC1D5031402C9FD34EE8EB75F085F55A66759E73BD7`.
The combined log is
`.local/native-renderer/snr01/resource-resolution-frame-6000/title-backend-resource-resolution.log`
(SHA-256 `E4C4EE1EE07B9CDAA5070514CB4B02808F7260141F61BE4FAA6983B7E3CA416D`).

Source frame 6000 had 342 balanced item nodes. All 281 submitting items
reached exactly one resource candidate in slot 0; the 61 non-submitting
items reached none. There were 11 distinct keys. The resolver ran 197 times,
for the first candidate and each subsequent key change; 84 repeated-key calls
used its cache. All resolver returns were nonzero, and each key mapped to
one distinct returned object within this frame. These are frame-local
identities, not a lifetime or streaming guarantee. The 189 first-path
submitted items still joined exactly to backend draws; the 130 second-path
packets still lack an item/resource ownership join.

The expanded bucket verifier checks candidate-to-descriptor association,
slot uniqueness, submitted versus non-submitted reachability, cache-change
behavior and one object per key. The indirect verifier passed for 133
backend roots, 1,628 executions and 4,887 prepared draws:

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/resource-resolution-frame-6000/title-backend-resource-resolution.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/resource-resolution-frame-6000/title-backend-resource-resolution.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The next relationship to recover is the concrete resource type and the
geometry/index source behind the final draw. Key-to-object stability must
also be retested across unload/reload and address reuse before SNR-02.

### Second bucket path: live virtual targets

The second path calls `sub_8243BD40` with its resolved object, then invokes
that object's vtable slot 41 at `0x8243BEB4`. RTTI in the extracted image
identifies four 42-slot vtables. The static verifier now checks their
decorated names, deleting destructors and slot-40/41 targets; its local
output is `.local/native-renderer/snr01/second-dispatch-static.json`.

| Slot-41 target | RTTI class in `proceduralGeometry` | Vtable |
| --- | --- | --- |
| `0x82417BC0` | `CProceduralModels` | `0x82002B5C` |
| `0x823FDE50` | `CProceduralAnimatedScene` | `0x820029FC` |
| `0x8245AB88` | `CProceduralCharacters` | `0x8200289C` |
| `0x824136F0` | `CProceduralVegetation` | `0x82002AAC` |

A read-only call-site hook captured the object and actual target in a
saved-race replay. It exited normally with executable SHA-256
`4E189BB5ED6C5C29E61F07B15A365BFD7158B023B5543582779CE0EFE735D632`.
The combined log is
`.local/native-renderer/snr01/second-dispatch-frame-6000/title-backend-second-dispatch.log`
(SHA-256 `0EE907D3F79F840BC9FE49CC070DECB26793C6020E3D25E95EC619A26D17EC68`).
All 145 second-path bucket entries invoked exactly one slot-41 target on
the same object returned by their secondary resolver. Their source-frame
6000 packet and backend-frame-6001 draw joins break down as follows:

| Class | Entries | Entries with packets | Distinct packets | Prepared-draw callbacks |
| --- | ---: | ---: | ---: | ---: |
| Procedural models | 97 | 0 | 0 | 0 |
| Animated scene | 12 | 6 | 10 | 17 |
| Characters | 24 | 24 | 24 | 28 |
| Vegetation | 12 | 10 | 88 | 140 |
| Total | 145 | 40 | 122 | 185 |

The 97 model calls with no scoped packet are not proven culled. The
character, vegetation and animated-scene virtual functions are the next
concrete owners to trace into mesh, instance and material submissions.
The expanded track-bucket verifier checks target membership, exact
object equality, one dispatch per second entry, and each target's packet
and backend-draw counts. The indirect verifier passed for 132 backend
roots, 1,578 executions and 4,863 prepared draws:

```powershell
python tools/discover-native-renderer-track-ingress.py `
  .local/generated/default `
  --image .local/ui-verify/default-image.bin `
  --output .local/native-renderer/snr01/second-dispatch-static.json
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/second-dispatch-frame-6000/title-backend-second-dispatch.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/second-dispatch-frame-6000/title-backend-second-dispatch.log `
  --source-frames 6000 6001 --backend-frame 6001
```

SNR-01 remains open: target class identity is stronger than an anonymous
secondary record, but no selected second-path packet has a verified
mesh/instance, transform or material owner yet.

### Second-path child calls and draw counts

The generated slot-41 implementations have different child submission
routes. `CProceduralAnimatedScene` calls `sub_82414A00` at
`0x823FDF94` and `0x823FE08C`; `CProceduralCharacters` reaches its
render-context vtable offset-164 call at `0x8245AE9C`; and
`CProceduralVegetation` reaches the corresponding call at `0x82413A80`
inside a loop. The character count argument comes from object offset 156.
Vegetation reads a per-entry count and can multiply it by three before
the call. These are raw title paths; their mesh and material roles are
still unverified.

Read-only begin/end hooks around those calls captured exact per-child
semantic/direct packet ranges. The saved sustained race exited normally
with executable SHA-256
`062E15D13CFA12F8788046ED9F1D7E56E062416DA74BB13B06371E1974AC8F3A`.
The combined log is
`.local/native-renderer/snr01/second-draw-final-frame-6000/title-backend-second-draw-final.log`
(SHA-256 `71BB10E66CAD38B45C1ECC1BFCDA5FD92DC66D7C872FE88834AC054B43FBD79F`).

In source frame 6000, all 142 second-path packets belonged to exactly
one child call, nested under the matching second bucket entry and its
slot-41 target. Every packet had an exact backend-frame-6001 prepared-draw
address match. No child scope was unfinished or returned under a different
bucket. The 52 continuations reached without a child call are counted as
skipped call sites; they do not establish intentional culling.

| Second-path class | Bucket entries | Child calls | Packets | Backend draw callbacks |
| --- | ---: | ---: | ---: | ---: |
| Procedural models | 91 | 0 | 0 | 0 |
| Animated scene | 12 | 9 | 10 direct | 21 |
| Characters | 24 | 24 | 24 semantic | 29 |
| Vegetation | 12 | 108 | 108 semantic | 200 |
| Total | 139 | 141 | 142 | 250 |

For every character and vegetation child packet, all matching backend
callbacks had `index_count = 4 ×` the title call's `r5` argument. The
animated-scene `r5` does not satisfy that count relation. The expanded
verifier requires exact child/bucket packet-set
equality and checks the count relation by packet address; the separate
indirect verifier passed for 133 backend roots, 1,705 executions and
5,123 prepared draws:

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/second-draw-final-frame-6000/title-backend-second-draw-final.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/second-draw-final-frame-6000/title-backend-second-draw-final.log `
  --source-frames 6000 6001 --backend-frame 6001
```

This closes packet ownership at the child-call level for the observed
second path. SNR-01 still needs the selected mesh/instance and final
transform/material identities, view-role classification, and an account
of packetless entries before Gate A can be considered.

### Character and vegetation state-record identity

In the generated character slot-41 function, the render-context
vtable-offset-124 call binds `owner + 132` immediately before its
vtable-offset-164 draw. In the vegetation function, the corresponding
binding argument comes from a loop-derived record pointer:
`record = running_40_byte_offset + *(owner + 108 + group_offset)`.
The same loop walks 12-byte count entries and 8-byte selector entries.
These are state-binding records, not verified mesh or instance objects.

Read-only hooks at `0x8245AE80` and `0x82413A0C` captured the raw binding
argument and carried it into each child draw scope. The saved sustained
race exited normally with executable SHA-256
`7146544F345D68575CFBCCB6B0F8E21577AF73D91EBDBCC2F235F434F1C454A2`.
The combined log is
`.local/native-renderer/snr01/second-bind-frame-6000/title-backend-second-bind.log`
(SHA-256 `1098335F4AC5B1F2EB487C149C4759E1F0B18EBBCEA22606B085D8C83ED0FD18`).

All 22 character child draws used the same render context as their
preceding slot-31 binding and exactly `resolved owner + 132` as the bound
record. They represented 11 distinct record addresses, each submitted
twice with a consistent count argument. All 108 vegetation child draws
used a nonzero bound record on the same context. They represented 54
distinct addresses, again each submitted twice with a consistent count.
The verifier preserves those repeated submissions, checks every bound
record against its child packet and exact backend draw, and still joins
all 140 second-path packets in this capture. The indirect verifier passed
for 133 backend roots, 1,660 executions and 4,940 prepared draws:

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/second-bind-frame-6000/title-backend-second-bind.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/second-bind-frame-6000/title-backend-second-bind.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The repeated addresses are frame-local identities only. The target of
both virtual slot-31 calls was not yet included in this capture.

### Slot-31 target identifies a state binding

The next saved sustained-race capture exited normally with executable
SHA-256
`BBA5D68CD973E2892B389D291B17C314952C10C7D53315EF20DEFD4B94318E58`.
Its combined log is
`.local/native-renderer/snr01/binding-target-frame-6000/title-backend-binding-target.log`
(SHA-256 `916F43884B82D20819BBC5DDA2F67A75ED55B30702B56CB0C551DC41CDB1F095`).
The hooks recorded the virtual target at the bind sites. All 26 character
and 108 vegetation child draws reached `0x82415CA8`. The generated
function reads fields at offsets 0 and 7 of the bound record, converts
the slot to a bit mask, and tail-calls `0x82410A70`. Existing
`discover-native-renderer-static-world-mesh-semantics.py` identifies
`0x82410A70` as the material-state binding used by the bounded
`CSimpleSubModel`/`CSimpleMesh` draw route. Its implementation updates
graphics-context state and dirty masks. This classifies the observed
slot-31 record as a **state-binding input**, not a geometry payload.

The character calls used 13 distinct records twice each; vegetation used
54 distinct records twice each. Both verifiers still passed. The
second-path capture contained 144 packets with 254 backend draw callbacks;
the indirect verifier matched 133 roots, 1,623 executions, and 4,643
prepared draws:

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/binding-target-frame-6000/title-backend-binding-target.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/binding-target-frame-6000/title-backend-binding-target.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The selected geometry and instance identities, final transforms and
material resources, view role, and packetless entries remain unresolved.
Do not infer geometry from these state-record addresses or publish mutable
guest state after frame publication. SNR-01 remains open.

### Resource-stage and decoded vertex-fetch join

A read-only hook at `0x82415C6C` now records the first-path resource-bind
target, and the prepared-draw callback reports index and vertex-fetch
descriptors without copying guest payloads. The generated render-context
vtable candidates at `0x8200306C` and `0x821451EC` both map offset 88 to
`0x82415C88`, offset 124 to the state bind above, and offset 164 to
`sub_82412DD8`. `0x82415C88` passes the resolved object to
`sub_82442528`, which writes resource fetch-state words. This is a
resource-stage bind, not a geometry-object proof.

The first saved-race replay exited normally with executable SHA-256
`10C991C6942C7FF84334BB6504E0E32EF06515E21DA206B405F985E38DC38204`.
Its combined log is
`.local/native-renderer/snr01/resource-index-frame-6000/title-backend-resource-index.log`
(SHA-256 `550275DA884BB6104C00C763B38653B49B4E861B6EE3910D0B6B690815B1D3E9`).
All 196 successful first-path resolutions reached exactly one
`0x82415C88` bind with the same object, slot and render context. The
decoded first-path, character and vegetation draws used non-indexed
primitive type 13; their index-buffer base and length were zero.
Animated-scene child draws instead used indexed primitive type 4. This
rules out an index-buffer address as the geometry identity for the other
three paths.

The next replay added a borrowed, eight-entry vertex-fetch view to the
ShiftGlue prepared-draw observation (`cf1b680`). It exited normally with
executable
SHA-256
`C77B3827C7F0A61DD9E93EE2C4A8B0E97E5D52F704CDFA0291CCCA17CD3D8320`.
The log is
`.local/native-renderer/snr01/vertex-fetch-frame-6000/title-backend-vertex-fetch.log`
(SHA-256 `387F427686CAE8E4BB662F03EC3A7C3891D3375B2CE13A9B81B3D19ABC748BC0`).
All 5,236 backend-frame-6001 draw callbacks had their declared fetch
lists captured: 8,333 fetch records total, none truncated or unmatched.

| Selected path | Packets | Backend callbacks | Fetch evidence |
| --- | ---: | ---: | --- |
| First | 208 | 256 | One nonzero fetch 95 per packet; 152 distinct signatures |
| Animated scene | 13 | 27 | One or two fetches; six distinct index-buffer bases |
| Characters | 24 | 30 | One fetch 95; 12 state records ↔ 12 fetch signatures |
| Vegetation | 80 | 135 | One fetch 95; 40 state records ↔ 40 fetch signatures |

Each character and vegetation packet had one fetch signature across all
of its backend executions. Within each class, every observed state record
mapped to one signature and each signature to one state record. The
signatures contain the decoded guest base, byte length, stride, fetch
slot and type; the verifier checks nonzero bases and lengths. This is a
frame-local **correlation**, not a proven allocation owner, mesh format,
or resource generation. A different route in this replay had one
animated-scene child call with no packet; the verifier reports it as a
packetless child while requiring exact ownership of every produced packet.
Its reason remains unclassified.

```powershell
python tools/verify-snr01-track-bucket-join.py `
  .local/native-renderer/snr01/vertex-fetch-frame-6000/title-backend-vertex-fetch.log `
  --source-frame 6000 --backend-frame 6001 `
  --first-model-vtable 0x82001D74
python tools/verify-snr01-indirect-join.py `
  .local/native-renderer/snr01/vertex-fetch-frame-6000/title-backend-vertex-fetch.log `
  --source-frames 6000 6001 --backend-frame 6001
```

The next SNR-01 join must trace these fetch bases back to title-owned
vertex allocations and selected instances, then identify final transforms
and the view role. SNR-02 must prove payload freshness before any native
scene uses these addresses.

### Fetch-register packet provenance

The next bounded replay recorded the last GPU packet to write each word of
the prepared vertex-fetch constants. D3D12 bulk register writes bypass the
single-register setter; the first probe therefore produced zero origins and
was not used as evidence. The corrected probe covers both paths. The
successful replay exited normally with 7 valid captures. Its build used root
`f5321c3`, SDK `cf1b680` plus this probe, executable SHA-256
`918DCEE1A611A062C4D13917E29F8BC0933D484605A38609252C09B604F95752`,
and D3D12 DLL SHA-256
`EDC60D88D34CA37E539F9FF39F7B80E7769B333CF227D64DAA96FA899E400659`.
The combined log is
`.local/native-renderer/snr01/fetch-origin-fixed-frame-6000/title-backend-fetch-origin.log`
(SHA-256 `CD59DBC0E8F2327CDFF85D787C38A664CCF61AA72091DDACF9AABA13C00AD592`).

Both SNR-01 verifiers passed for source frame 6000 and backend frame 6001.
Of 7,780 prepared fetch records, all had nonzero origins and both fetch words
pointed to the same setter packet and execution. In 7,620 records the setter
preceded the draw within its indirect-buffer execution; 160 reused fetch
state from a prior execution. Seven fetch records attached to source-frame
packet headers were in that carry-over group. The verifier now checks these
conditions when provenance fields exist, while accepting older captures.
This establishes the GPU register setter's packet, **not** the title object
or allocation that supplied the vertex bytes. Repeated command-buffer
execution and state carry-over remain part of SNR-01's ownership map.

### Character and vegetation title vertex descriptors

The generated `0x82415CA8` state-bind path loads a descriptor pointer from
the bound record's first word, then `0x82410A70` reads descriptor words at
offsets 24 and 28 to set the vertex fetch. A bounded read-only hook captured
those words at the existing character and vegetation bind sites. The saved
race exited normally with seven captures; executable SHA-256 was
`B3F9A03702693C27377503DD7C7993AC2EF2E90F9756BDF28C3F79EAED3A3477`.
The combined log is
`.local/native-renderer/snr01/vertex-descriptor-frame-6000/title-backend-vertex-descriptor.log`
(SHA-256 `097E084920ECE3FE4F4BC6065B99FD28FB52BBDCB9B115964786B9289AB48C01`).

For source frame 6000, 24 character calls produced 24 packets and 30 backend
fetches; 136 vegetation calls produced 136 packets and 230 backend fetches.
Every call's descriptor size word equaled its existing draw argument 6.
For every joined backend fetch 95, the title descriptor decoded exactly:
`guest_base = word24 & 0x1FFFFFFC`, `length = word28 & 0x03FFFFFC`,
and `type = word24 & 3`. The verifier asserts these equalities when the
title descriptor fields are present. This proves the selected draws use
the captured title-side fetch descriptor. It does not yet prove who owns
the referenced allocation, how long it lives, or which final instance
transform belongs to each packet. Other draw paths remain open.

### Vegetation owner-to-record join

The generated vegetation dispatch at `0x824136F0` retains its object in
`r23`, selects one of the pointer words at owner offsets 152, 156 or 160
(`r26` is 44, 48 or 52), and advances `r24` by 40 bytes per selected
record. It passes `r27 = selected pointer + r24` to the state-bind call
at `0x824139F4`. A bounded hook at that call captured those registers and
the pointer word before the original call ran.

The replay exited normally with seven captures, executable SHA-256
`5E764111540FF0216C1117A03D31F6BA2842C5803EEA5C68A860FDB429D3F9A7`.
Its combined log is
`.local/native-renderer/snr01/vegetation-owner-frame-6000/title-backend-vegetation-owner.log`
(SHA-256 `AB895054F1D9DF719DF0AEEF2B420348BC468701CBA15B452FFE9023CC2FE994`).
The route diverged from the earlier pilot controls, so this run supplies
ownership evidence only; it is not a matched performance comparison.

For source frame 6000, all 84 vegetation draw calls belonged to four
dispatch-owner objects. Every owner equaled its enclosing bucket's resolved
object; every selected record equaled the bound record and its captured
stream base plus a multiple-of-40 offset. These calls produced 84 packets
and 152 backend draw callbacks; all 152 fetch descriptors still matched
the title-side words. The verifier checks these joins, while 42 distinct
records each appeared twice in this frame. This proves the selected
vegetation owner-to-record-to-fetch route, but not the vertex allocation's
ownership or lifetime, material semantics, final transform, or whether the
three stream offsets are LODs rather than another title grouping.

### View call to track bucket and backend draw

The title's slot-75 function `0x82439B70` has one common return at
`0x8243BC74`. A default-off scope around those addresses now records the
active `CPresentationView` call and the exact bucket range produced by each
track-presentation call. The saved-race replay exited normally with seven
captures and executable SHA-256
`DCAF5223429357FBE21CFEB898B9220DCDD34ADC97B25359E002E6D79E79B7CC`.
Its combined log is
`.local/native-renderer/snr01/track-call-frame-6000/title-backend-track-call.log`
(SHA-256 `3BD68F330D0355753EF2712056B7CC8D1A7DEA5FF88FA2A1A32F1F3B0FC5A410`).

In source frame 6000, 19 slot-75 calls returned with no unfinished or
unmatched scope. Every one of 392 bucket entries fell within exactly its
recorded parent call. The resulting 324 selected packet headers joined
488 backend-frame-6001 prepared-draw callbacks; both ownership verifiers
passed. The expanded track-bucket verifier checks the view-call existence,
presenter and view identity, bucket range, packet join and target bits.

| View call / title caller return | Track calls | Buckets | Packets | Backend callbacks | Bound targets |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 / `0x823FA398` | 1 | 132 | 74 | 74 | Depth only, bit 0 |
| 2–7 / `0x8240A154` | 12 | 55 | 36 | 36 | Depth + color, bits 0–1 |
| 8 / `0x8245032C` | 6 | 205 | 214 | 378 | Depth + color, bits 0–1 |

The six middle view calls came from one title caller with distinct raw
view arguments 0, 4, 2, 1, 3 and 5, consistent with six face selections;
their camera and target identities are not yet proved. The eighth call
produced the dominant selected color/depth work and is the main-view
candidate, while the first call produced depth-only work. These are
**candidate roles** based on title scheduling and actual bound targets,
not permission to exclude the other views or suppress draws. Fifteen
eighth-view buckets in later track calls had no packet in this frame;
the reason remains to be classified. SNR-00's exact slice and SNR-01's
camera/pass proof remain open.

### View attachments and GPU-copy destinations

The prepared-draw observer now records the raw `RB_SURFACE_INFO`, four
`RB_COLOR_INFO` values and `RB_DEPTH_INFO` alongside the attachment-state
hash. The existing copy observer already had those registers; SNR-01 now
logs bounded copies when its default-off trace flag is enabled. This lets
the view-to-packet verifier's title ownership join continue through the
actual draw target and subsequent GPU copy. A dedicated log path with a
100 MiB rotation limit preserved the complete target-frame window. The
saved-race run exited normally with seven captures. Its executable SHA-256
was `ECF5309B58A4DAD1A594EA38ECBB7E3FE472E333D4936B3B46009744F0D669B5`,
the D3D12 DLL SHA-256 was
`BCE2BF101FF3AE684EE087264587CC032192DA57AF7E27FE195537FBD600A128`,
and the log is `.local/native-renderer/snr01/attachment-copy-full-runtime.log`
(SHA-256 `CDDDFE7C205BFC2CDC73A52A13E831D52CB6E7252B9BB46E96672B60CE8DA33C`).
Both prior SNR-01 ownership verifiers and
`tools/verify-snr01-attachment-copy-join.py` passed on source frame 6000
and backend frame 6001.

| View call | Joined backend draws | Raw attachment pattern | Copy relationship |
| --- | ---: | --- | --- |
| 1 | 74 | Depth only: surface `335545600`, color 0, depth `65536` | Copy 8 resolves 1280×720 |
| 2–7 | 6, 5, 5, 7, 5, 7 | Shared surface `67174720`, color 0 `196608`, depth `65664` | Each call's draws are followed by exactly one successful 256×256 copy, ordinals 11–16, to six distinct guest destinations |
| 8 | 367 | 229 draws on color 0 `196608`; 138 on color 0 `786432`; both surface `335676672`, depth `66560` | Twelve copies, ordinals 65–76, match the first raw target; none matches the second |

The six middle calls come from `sub_82409ED0`, which iterates six resource
slots and selects arguments 0, 4, 2, 1, 3 and 5. The six copy destinations
are `0x1C879000`, `0x1C979000`, `0x1C8F9000`, `0x1C8B9000`, `0x1C939000`
and `0x1C9B9000`: exactly `0x1C879000 + face × 0x40000` for those indices.
Each successful copy writes 256 KiB. This matches the independently recorded
256×256, six-face R10G10B10A2 reflection-cube allocation, base and face order
in [PERF-05](PERFORMANCE_02_05_RESULTS_2026-09-21.md). The title view call,
draw target and copy now establish these as the **reflection face producers**
for this captured allocation. The verifier asserts the ordered offsets and
size without hard-coding the base; this address can be reused or relocated.
The texture-binding join is established below; the generation and semantic
owner remain open.

View 8 remains the main-view candidate. Its two color targets and the
unmatched second target mean the final presentation and retained-pass
dependency cut are not yet established. The trace does not authorize
suppressing any view or pass.

### Reflection-cube consumers and the separate title command path

The prepared-draw observer now exposes the live shader-used texture fetches:
fetch constant, base/mip addresses, format, dimension and dimensions. A
default-off source-frame-6001 saved-race replay with a dedicated log exited
normally with seven captures. Its executable SHA-256 was
`D6CB1AEB4AE4448D72AC7E2AD5A2317697EE373E9B7A7522D647FC11FB2D8DDA`,
the D3D12 DLL SHA-256 was
`D83C0A2792BE79DCE3192442A3D39A7C0C00C380A964712FDE65289CC56F8253`,
and `.local/native-renderer/snr01/texture-consumer-view-runtime.log` has
SHA-256 `0128D11544B3FD27C35A07A0EC517FB8AB401D06EB4C4BBE8411964017CF6879`.
`tools/verify-snr01-cube-consumers.py` passed on source/backend frame 6001;
the indirect and track-bucket verifiers also passed for source frame 6001
and backend frame 6002.

In backend frame 6001, six successful 256×256 face copies (ordinals 8–13)
write `0x1C879000 + face × 0x40000` in order 0, 4, 2, 1, 3, 5. After the
sixth copy, 728 prepared draws each have one live texture fetch from base
`0x1C879000`, mip base `0x1C9F9000`, format 54
(`k_2_10_10_10_AS_16_16_16_16`), cube dimension and 256×256×6 shape.
All 728 render with depth and color to raw target `(surface 335676672,
color 0 786432, depth 66560)`. This is a direct producer-to-consumer address
join in one backend frame, not a shader-hash inference. The verifier checks
that every prepared draw's declared texture-fetch count appears in the log.

Each of those 728 draws descends from a source-frame-6001 primary packet
written at title caller return `0x829F6308`, with no queued caller. None of
their draw packet addresses belongs to a source-frame-6001 tracked view/slot-75
bucket. Static generated code shows `sub_829F5FF0` calls `sub_82409398` at
this return while interpreting a title command stream. This identifies a
separate command path, **not** its semantic scene owner. The consumers use the
same raw target tuple as some view-8 draws in the previous capture, but shared
EDRAM registers do not prove they belong to view 8. SNR-01 must recover this
path's source owner, view/camera and ordering before the proposed main-view
slice can be frozen or suppressed. SNR-05 must preserve the cube production,
mip publication and sampling dependency across that boundary.

### Deferred command worker carrying the cube consumers

Generated title code shows `sub_829F6360` calls the command interpreter
`sub_829F5FF0` at `0x829F6604` with a stream and queue pointer. Default-off
begin/end probes at that call bracket the primary packets written by the
interpreter. The final `fh1-race-sustained.fh1test` replay with
`--pinyon_shift_snr01_trace_source_frame=6000` exited normally with seven
captures. Its executable SHA-256 was
`5C67409D5BE1C242BA5D11CFA0966EFE8D24DF890094BCFE5EC8CDBBF581E7E7`.
The AppData log rotated at 5 MiB; the chronological concatenation of this
run's `runtime.4.log` through `runtime.1.log` and `runtime.log` is saved as
`.local/native-renderer/snr01/deferred-worker-final-sustained-combined.log`
(SHA-256 `3624D932D32D0C45963E27774DD89A8CED45B1AA74B3A65AF1F1E3F21F3B86A9`).
The cube-consumer verifier passed for source/backend frame 6001 with
`--allow-missing-view-trace`, requiring every consumer root to fall within a
matching worker begin/end packet range. The earlier view-trace replay passed
without that flag and found zero tracked-view packet overlap.

This capture has 728 cube-sampling draws from eight primary packet roots. All
roots were written by `sub_829F5FF0` at return `0x829F6308` under queue
`0x401600C8`, using worker streams `0xD3083004` and `0xD308313C`. The smaller
stream covered source-frame-6001 primary packet ordinals 50–55 and the larger
stream covered 56–98. The same worker probes bracketed two earlier
source-frame-6000 streams on that queue. Root count is capture-specific: a
previous worker-trace replay had ten roots and the view-trace replay had nine,
each for the same 728 fetches. Device
`0x4015D580`, entry array `0x7042FDF0`, shader-used fetch descriptor and raw
draw target agreed across the two captures.

The worker boundary identifies **where** deferred commands are interpreted,
not who enqueued them or which scene view owns them. A bounded probe at the
candidate queue-write instruction `0x829F680C` saw no events in source frames
5998–6001 and was removed; this does not rule out earlier or other enqueue
paths. SNR-01 still needs the command-stream producer and semantic camera/view
join. No main-view exclusion or native pass admission follows from this trace.

### Earlier linked-command writes near deferred streams

Static title code in `sub_82409668` has a branch at `0x82409710` that writes
an `0x81` or `0x8F` indirect command at `r29 + 4`, its payload at `r29 + 8`,
then links the block through `sub_823E6568`. A default-off probe at that write
captured the command address, payload, device, title return and active
slot-75 view scope. The first bounded window (source frames 5998–6001) logged
156 writes but no write close to the source-frame-6001 worker streams. A
separate probe of `sub_829EE338`, which copies commands to another buffer,
logged zero calls in source frames 6000–6001 and was removed.

The final probe kept the expensive draw/view trace at source frame 6000 and
extended **only** the linked-write window back to frame 5988. The
`fh1-race-sustained.fh1test` replay exited normally with seven captures. Its
executable SHA-256 was
`0C9617B055C3EB264FD0109F0D7604DF51B947DE04EA2C212A621238B6DD1110`,
and `.local/native-renderer/snr01/linked-indirect-wide-runtime.log` has
SHA-256 `FD39C40756805680017456FEB377138529DDA76799AFE3B2612CCCCB246D6358`.
It recorded 628 linked writes from title returns `0x8240CFF8`,
`0x8240D1B0` and `0x8246946C`. The cube-consumer verifier again found 728
fetches on the same resource,
device and target, this time from eight source-frame-6001 primary roots.

For comparison, subtracting `0x20000000` from the worker's virtual stream
pointer gives the alias used by the linked-write probe. The nearest preceding
recorded writes are:

| Worker source frame / stream | Nearest write source frame / opcode address | Distance before stream | Title return / opcode |
| --- | --- | ---: | --- |
| 6000 / `0xD301C084` | 5999 / `0xB301C030` | 84 bytes | `0x8240CFF8` / `0x8100000B` |
| 6000 / `0xD301C1B4` | 5999 / `0xB301C030` | 388 bytes | `0x8240CFF8` / `0x8100000B` |
| 6001 / `0xD319EA84` | 5997 / `0xB319EA44` | 64 bytes | `0x8240D1B0` / `0x81000010` |
| 6001 / `0xD319EBBC` | 5997 / `0xB319EA44` | 376 bytes | `0x8240D1B0` / `0x81000010` |

These were address and ordering **candidates**, not a command-chain or
view-owner join. The exact-command probe below supersedes this proximity
inference for the cube: these nearby linked writes are not its command words.

### Exact deferred command writer and reader join

The interpreter `sub_829F5FF0` now records the command pointer, opcode and
payload at `0x829F62F0`, immediately after loading the payload and before
calling `sub_82409398`. The primary-packet probe carries that physical
command address to backend draws. The `sub_8240D070` inline writer records
both its cached and stream-write paths with physical destination, opcode,
payload and active presentation-view call. The verifier joins each cube
consumer's primary packet to the preceding read and latest preceding write
at the **same physical command address**, then requires identical opcode and
payload. Physical addresses normalize guest aliases with `& 0x1FFFFFFF`.

The bounded `fh1-race-sustained.fh1test` replay exited normally with seven
captures. The executable SHA-256 was
`8C584AE9B3217EDA17A93BF5B4369982C7C8269C079C6F205E1A2D92F04A3EFD`;
`.local/native-renderer/snr01/exact-payload-runtime.log` SHA-256 was
`D8A692003F2300FD24F3BC6DC2A627704E01D02B699DE7A19D18BD557D61500A`.
Run `python tools/verify-snr01-cube-consumers.py <log> --source-frame 6001
--backend-frame 6001 --allow-missing-view-trace --require-command-writers`
to reproduce the join. It passed for 728 cube-sampling draws from eight
primary roots. In this capture, three distinct command words account for
those roots:

| Physical command | Cube draws | Opcode / payload | Writer |
| --- | ---: | --- | --- |
| `0x13103C04` | 414 | `0x81005739` / `0x130EDBA0` | frame 6000, inline path 1, view call 8 |
| `0x13103C0C` | 124 | `0x81007FD7` / `0x1310AE80` | frame 6000, inline path 1, view call 8 |
| `0x13103C24` | 190 | `0x81007FCB` / `0x1316AD00` | frame 6000, inline path 1, view call 8 |

All three writes occurred with presentation-view pointer `0x423CFA30`
active in call 8 and were read by the deferred worker in source frame 6001.
The track-bucket verifier independently passed for source frame 6000 and
backend frame 6001: 459 visible-list entries yielded 328 packet headers,
with zero unmatched submitted items inside a view. This capture's exact
command join places its three cube command writes inside call 8. The next
replay shows that this is not a universal scope boundary for all cube
commands. SNR-01 and Gate A remain open.

### Presentation-camera RTTI and the post-view command boundary

Read-only hooks after the title loads `view+400` and the selected context's
vtable identify the objects used in each source-frame-6000 presentation call.
The eight `view+400` objects all have vtable `0x82002F64`. The base image
`.local/ui-verify/default-image.bin` has SHA-256
`6014727FA7B0B79727FD5F32A2E2377533DC8E29679E8D2462BD764D331FA305`. Its
RTTI locator at `0x8235FEDC` names this type
`TRefCountedObjectThreadSafe<CPresentationCamera>`. Calls 1 and 8 use the
same camera object `0x2E493200`; calls 2–7 use another,
`0x2E0B0E00`. The six middle calls use the observed face argument sequence
`0, 4, 2, 1, 3, 5`, making their camera a reflection-view candidate, not a
proved semantic label. The selected-context vtable `0x8200306C` resolves
through locator `0x82351880` to
`TRefCountedObjectThreadSafe<CD3D9GraphicsDevice>`, so that pointer is the
graphics device rather than a camera.

The same sustained replay exited normally with seven captures. Executable
SHA-256:
`023ABF6CC94939163456131B7F60B87FCAB7655215FEAD0962AD84921F5FAC6E`.
`.local/native-renderer/snr01/view-object-vtable-runtime.log` SHA-256:
`1D7619A6AAB9FF8268A4F1A6AABB33EB2C7F5C7A9FCC1D59498CA75A58F05360`.
The exact-command verifier passed for all 728 cube-sampling draws from five
primary roots. This run's two cube command words show the scope boundary:

| Physical command | Cube draws | Writer location | Camera join |
| --- | ---: | --- | --- |
| `0x13087484` | 538 | frame 6000, inline path 1, inside view call 8 | `0x2E493200` via view `0x41849E30` |
| `0x130874A4` | 190 | frame 6000, inline path 1, after view call 8 returned | none inside a view scope |

Both writes were on the presentation thread in one sequential inline stream.
The second was logged ten lines after call 8's end, following three other
inline writes inside that call. The verifier still matches its exact address,
opcode and payload to the worker read in source frame 6001, but **does not
assign it to camera `0x2E493200`**. The track-bucket verifier also passed
for source frame 6000/backend frame 6001 with 461 visible-list entries,
324 packet headers and no unmatched submitted items inside a view.

The camera pointer join establishes two distinct camera objects and the
view-8 camera for in-scope command writes. The title's post-view publication
step and camera state/transform semantics remain to be traced before the
entire deferred cube path can be assigned to a view or the main camera.

### Distinct callers for in-view and post-view command refills

`sub_8240CF68` refills the device command stream and calls the inline writer
`sub_8240D070`. A default-off hook now records its immediate title caller on
each inline write. In the next normal-exit sustained replay, seven captures
were produced with executable SHA-256
`82BA4FB095D68F911AB1767E9AC86BE596CDD34CE37ACBA482266CCD23C4393E`.
`.local/native-renderer/snr01/refill-caller-runtime.log` has SHA-256
`B43785363493D146A102A7A27364E4A1010952430E0E242723683EBE1CCB0AAD`.
The cube verifier passed for 728 draws from six primary roots, and the
track-bucket verifier passed for 435 visible-list entries, 322 packet
headers and zero unmatched submitted items inside a view.

| Physical command | Cube draws | View call | Refill caller | Camera |
| --- | ---: | ---: | --- | --- |
| `0x131C6F0C` | 538 | 8 | `0x82467A88` | `0x2E486200` |
| `0x131C6F24` | 20 | 8 | `0x82467A88` | `0x2E486200` |
| `0x131C6F2C` | 170 | outside view scope | `0x824696CC` | unassigned |

Static code places `0x82467A88` in `sub_824679E8` after a buffer copy and
`0x824696CC` in `sub_82469478` after `sub_8243BEE0`. The latter function is
called directly by `sub_823F10C8` at `0x823F1454` after its render-request
loop. These are **different title call paths** to the same refill function;
the post-view command is not merely another write inside the presentation
callback. The immediate parent of `sub_823F10C8`, its relationship to view
call 8, and the command's camera ownership were left open by this capture.

### Render-thread parent of post-view publication

A bounded hook at the entry and common return of `sub_823F10C8` records
its caller on inline writes nested beneath it. The next sustained replay
exited normally with seven captures. Executable SHA-256:
`500BFEB8D546FB13E827B30D1D39ABFB94A30EF1711FAAD33C5EEADFC5148D04`.
`.local/native-renderer/snr01/render-request-caller-runtime.log` SHA-256:
`18701737EEFB870FFC3834AC78A28DF60A2D0B3C983F18E8F6040830D95A6CE1`.
The exact-command verifier passed for 728 cube-sampling draws from nine
primary roots. Its four command words divide as follows:

| Physical command | Cube draws | View call | Refill caller | Render-request caller |
| --- | ---: | ---: | --- | --- |
| `0x13246204` | 419 | 8 | `0x82413CF8` | none |
| `0x1324620C` | 119 | 8 | `0x82467A88` | none |
| `0x13246224` | 121 | 8 | `0x82413CF8` | none |
| `0x1324622C` | 69 | outside view scope | `0x824696CC` | `0x8245B870` |

The three in-view writes join camera `0x2E4B3200` through view
`0x4221FB90`; the post-view write has no active camera scope. Static title
code places `0x8245B870` in `sub_8245AEF8`, calling `sub_823F10C8`.
Base-image RTTI identifies vtable `0x82003284` as `CRenderThread` (locator
`0x822F182C`), with `sub_8245AEF8` in slot 8. Thus the post-view command
comes through the render-thread slot-8 path and then
`sub_823F10C8` → `sub_82469478` → `sub_8240CF68` →
`sub_8240D070`. This is a call-path join, not a camera or view-owner join.
The track-bucket verifier independently passed for source frame 6000 and
backend frame 6001 with 408 visible-list entries, 332 packet headers and
zero unmatched submitted items inside a view. SNR-01 still needs the
render-thread request's source view/camera relationship and a title-level
camera state/transform map before the full deferred path is owned.

### Presentation-camera matrix writers (static)

The same image's `CPresentationCamera` vtable at `0x82002F64` has 65 slots;
the next vtable begins at `0x8200306C`. The generated title functions provide
these exact writes to the camera object (`r3`):

| Vtable slot / function | Proven object writes or reads |
| --- | --- |
| 43 / `sub_82D8C820` | Copies four 16-byte vectors assembled on the stack into `camera+80` |
| 44 / `sub_82DB8190` | Copies four 16-byte vectors assembled on the stack into `camera+144` |
| 11 / `sub_82DBAFC0` | Reads floats at `+208`, `+212`, `+256`, `+260` and byte `+268`; constructs values at `+80`, stores its argument at `+12`, `camera+80` at `+8`, and sets dirty byte `+464` |
| 12 / `sub_82DB7C00` | Reads floats at `+208`, `+212`, `+240`, `+244`, `+248`, `+252` and byte `+268`; writes a 64-byte result at `+80`, stores its argument at `+12`, and sets `+8` and dirty byte `+464` to one |
| 8, 14, 17 | Store an argument at `+8` or floats at `+260` / `+256`, respectively, and set dirty byte `+464` |

Slots 2 and 3 change a refcount at `+496`; slots 62–64 delegate to
`sub_823F8848`, with two of them also calling helpers on `camera+272`.
These are field and call facts, not yet a projection/view/world-transform
semantic map. In particular, slot 12 uses separate branches for its byte
`+268` and argument, so a single assumed matrix convention would be unsafe.
The next bounded runtime probe should record slots 11/12/43/44 and their
camera object pointers around the eight view calls, then join the observed
state to the render-thread request and submitted matrix bindings.

### Live camera-method and view-state join

Default-off hooks at slots 11/12/43/44 and the existing view scope produced
two normal-exit sustained-race replays with seven captures each. The second
build's executable SHA-256 was
`30531EE26E6B40E34BA97D5AF15BF7E73F4225B282AC167E1437A0E408E8565D`;
`.local/native-renderer/snr01/camera-method-run-b.log` SHA-256 was
`1B909F52A1AAB090E7B7B1CD2D962FBDC641358A52FC22B961A0328AE20629A7`.
The new `tools/verify-snr01-camera-view-join.py` passes for source frame 6000.

In that frame, view calls 1 and 8 use camera `0x2E4B6200`; calls 2–7 use
camera `0x2E0B0E00`. Slot 11 runs 14 times on the first camera before the
view calls; slots 12 and 43 have no calls in this frame. Slot 44 runs once
inside every view call on its associated camera. The 64-byte region at
`camera+80` has a stable hash within every call. The `camera+144` hash stays
stable in calls 1 and 8, but changes during each of calls 2–7. Each middle
call's exit hash is the next call's entry hash. Thus the six face calls
successively update one live camera's second matrix region; they are not six
independent camera objects. This does **not** yet identify the matrix's
coordinate convention or prove main-view pass semantics.

The same frame writes one command at `0x130FE12C` after view call 8 returns,
via render-request caller `0x8245B870`, with no active view scope. Its camera
ownership remains unassigned. The track-bucket verifier passed: 441 visible
entries, 353 packet headers and zero unmatched submissions inside a view.
The cube-consumer verifier passed for 728 draws when invoked with primary
packet frame 6001 and backend frame 6001; its three consumer command writers
were in view call 8 in source frame 6000. Using source frame 6000 for that
verifier fails because the observed primary packets in this replay carry
frame 6001. This timing-dependent frame label must not be hidden by claiming
the separate post-view command has a cube consumer or camera join.

The exact post-view command is **consumed**, despite having no view scope.
The extended camera/view verifier joins its single frame-6000 writer at
`0x130FE12C` (opcode `0x810012CD`, payload `0x13186700`) to three deferred
reads and three primary packet roots in frame 6001. Each root produces ten
prepared draw callbacks: 30 callbacks from ten unique draw packet addresses.
Nine of those ten addresses have a frame-6000 direct-packet record with
`direct_call=0`, outside the instrumented direct-call scope. Their output
uses the same observed surface/depth words as other scene draws; 21 callbacks
have color word `0xC0000` and nine have `0x30000`. Neither target similarity
nor temporal adjacency assigns those packets to camera `0x2E4B6200`. SNR-01
must recover the upstream owner of the ten packets or explicitly exclude
them from the frozen slice with a proved pass/dependency boundary.

### Post-view draw writers and variable downstream work

An entry/exit scope around title function `sub_8240DC70` now attaches its
immediate caller to its direct-packet writes. In a normal-exit, seven-capture
replay, executable SHA-256
`26CD009EC6BF928392D1ABF53251FEC99A61A5F45E693B981420E5F1942954C8`,
`.local/native-renderer/snr01/indexed2-caller-run-a.log` SHA-256
`000010C4D4077A715DDEA3CE85C5FB3306CC9AAB69CEE432FCADBD3841BFA153`,
the post-view command `0x130E912C` again has three deferred reads and three
primary roots. This time they produce **231** prepared draw callbacks from
187 unique packet addresses, not the prior run's 30 from ten. Nine of the
187 addresses have a source-frame-6000 `indexed2_secondary` direct-packet
record outside the known direct-call scope. Seven record caller `0x82D07200`,
one records `0x82D0735C`, and one records `0x8244F070`.

The verified base image places `sub_82D06C28`, containing the first two call
sites, in slot 3 of vtable `0x82236214`. Its complete-object locator
`0x823586E4` names `CStandardParticleRenderer`. This proves those eight
packet writes passed through a particle-renderer method; it does not classify
all 231 callbacks under the same deferred root as particle draws.
`0x8244F070` is in `sub_8244E938`; its owner remains unidentified.

A second normal-exit, seven-capture replay after adding two read-only
secondary-object guard bytes used executable SHA-256
`19B959AD6F8E07D5158C82E2E1C7A9E7A6CF1072B609BB96992E9811DAC8524D`.
`.local/native-renderer/snr01/secondary-guard-run-a.log` SHA-256 was
`7246C0747A0185D163D55976F34E90DBA158DD7C1047C811ED1443C57DB3C1CC`.
Its post-view root produced 228 callbacks from 154 packet addresses, with
12 indexed2 direct-packet records: ten from caller `0x82D07200` and one
each from `0x82D0735C` and `0x8244F070`. The generalized camera/view
verifier passes on all three captures, checking the exact command-write,
deferred-read, primary-root and prepared-draw relationships without assuming
a fixed draw count. All observed post-view callbacks still use surface word
`0x14020500`, depth word `0x10400` and color word `0xC0000` or `0x30000`.

The track-bucket verifier passed on the last replay with 442 entries, 342
packet headers and zero unmatched in-view submissions. It failed on the
previous replay because one of 142 secondary entries had no recorded virtual
dispatch and no packet. Static `sub_8243BD40` checks bytes `+52` and `+55`
before dispatch. In the later replay all 141 dispatched secondary entries
had nonzero `+52` and zero `+55`, but the missing entry did not recur, so its
cause is **unproved**. Do not weaken the verifier to count that earlier gap
as intentional culling. SNR-01 still needs the remaining post-view packet
owners and a proven main-view/dependency boundary.

### Title owner of one packet consumed after the view

The title's `sub_82444E60` calls `sub_823E2DE0` at `0x82446160`
(return address `0x82446164`). That wrapper derives subobject and array
pointers from its input and tail-calls `sub_8244E938`, which writes an
`indexed2_secondary` packet at `0x8244F070`. This static path prompted a
default-off, read-only entry probe at `0x8244E93C`; the probe records its
caller, receiver, arguments and active presentation-view call. It does not
interpret the receiver's first word as a vtable or identify a mesh.

The rebuilt executable SHA-256 was
`F2CE5C3D1B2E5CB27EB61113F1D0F3149C0A753DB7442FFBEF528A8F871EE22A`.
The normal-exit sustained race produced seven PPM captures; log
`.local/native-renderer/snr01/indexed2-owner-run-a.log` SHA-256 was
`0533E4AE29C4115E72A523A84FC9387D6DDD76EEEB13B88CD5CCAD34AE2CEAD3`.
At source frame 6000, the probe recorded exactly one matching call:
caller LR `0x82446164`, receiver `0x43061870`, argument 5/view
`0x4248F600`, and active view call 8. The `0x8244F070` direct packet at
physical `0x12ED7F1C` followed on the same thread before view call 8 ended.
The later command at `0x13244F2C` was written **after** that view ended and
read in frame 6001. Its three roots produced 229 prepared draw callbacks
from 185 unique packet addresses; one of those addresses was the title
packet just identified. Thus command publication outside a view does not
imply every packet it consumes was produced outside that view.

`tools/verify-snr01-camera-view-join.py` now asserts this ordered
view → title call → packet → deferred-command consumer join when the new
probe is present, while retaining compatibility with older captures. It
passes this replay and the earlier secondary-guard replay. The track-bucket
verifier passes on this replay (360 entries, 266 packet headers, zero
unmatched in-view submissions), as does the cube-consumer verifier (728
draws, four command writers). The other eight directly observed post-view
packet writes still pass `CStandardParticleRenderer`; most of the 185 packet
addresses under the deferred roots lack an indexed2 direct-packet record.
The selected scene slice and any main-view dependency boundary remain
unproved, so SNR-00, SNR-01 and Gate A remain open.

### Deferred packet address recurrence

The camera/view verifier now compares the post-view root's distinct prepared
draw packet addresses in backend frame 6001 with prepared draws in backend
frames 5999 and 6000, then reports which newly observed addresses have a
source-frame direct, semantic or indexed write. Four earlier captures had an
exact new-address/direct-write match:

| Replay | Post-view addresses | Seen in prior frames | New direct records |
| --- | ---: | ---: | ---: |
| `camera-method-run-b` | 10 | 1 | 9 |
| `indexed2-caller-run-a` | 187 | 178 | 9 |
| `secondary-guard-run-a` | 154 | 142 | 12 |
| `indexed2-owner-run-a` | 185 | 176 | 9 |

In the last replay, all 176 recurring addresses occur in **each** of backend
frames 5999 and 6000. Their captured draw metadata matches frame 6001 at each
address: vertex/pixel shader IDs, index count/type/base/length, primitive type,
and vertex/texture fetch counts. These are recurrent prepared packet addresses,
not 176 source-frame-6000 writes missing from the direct-packet hook. The
addresses are absent from other frame-6001 command roots. Their earlier title
owners and allocation generations remain unknown; stable addresses and draw
metadata do not prove stable buffer contents or a main-view pass boundary.
The next ownership probe should follow the title references to these resident
command buffers, then check their resource generations before any suppression.

A separate normal-exit replay moved the bounded title probe to source frame
5999 without rebuilding (the executable SHA-256 remained
`F2CE5C3D1B2E5CB27EB61113F1D0F3149C0A753DB7442FFBEF528A8F871EE22A`).
It produced seven PPM captures; log
`.local/native-renderer/snr01/resident-origin-5999-run-a.log` SHA-256 was
`E0020B75C476F1B3EF74A32AC6F18353C89FD158D3AFD1B1CD7258C2B5EDD9B5`.
Its post-view command consumed 31 unique packet addresses in backend frame
6000: 23 had already appeared in backend frames 5998/5999 with the same
captured draw metadata, and the other eight exactly matched source-frame-5999
direct writes. The title owner probe again joined one direct packet to view
call 8. The camera/view, track-bucket (351 entries, 281 headers, zero
unmatched in-view submissions) and cube-consumer (728 draws, four writers)
verifiers passed. Moving the probe one frame earlier therefore did not find
the first writes of the recurring packets. The population also varied from
the 185-address source-frame-6000 capture, so addresses must be compared
within each replay, not across launches. A targeted memory-write watch on
known resident command pages is the next way to test mutation; it would not
by itself identify the original title allocator or render owner.

### Full-route survey of known packet writers

A default-off survey now observes the existing semantic and direct PM4 header
writer hooks throughout the replay, independently of the single-frame trace.
It restricts logging to physical ranges `[0x14000000,0x16000000)` and
`[0x17000000,0x18000000)`, with an 8,192-event cap per title thread. The
initial broader `[0x14000000,0x18000000)` attempt hit that cap in the
unrelated `0x16E…` primary-packet pool by source frame about 1830, so it
cannot establish anything about later resident packets. The filter change
excluded that pool. Survey activation is now logged explicitly.

The final filtered build's executable SHA-256 was
`3F346F83C3278B8A01DDEC792D233E391B6084A1051F423FBCA30D79614F06DC`.
Its normal-exit seven-capture log
`.local/native-renderer/snr01/resident-writers-run-c.log` SHA-256 was
`06968CEDCC1CB63EA5FDAE07A34E308F078F3FD440FCF7AA2AA9D589BDD4A28B`.
The activation marker confirms the two ranges and cap. The post-view root
consumed 70 distinct packet addresses, 62 of them also prepared in the two
preceding backend frames. **All 62 recurring addresses lie in the surveyed
ranges, and the complete replay logged zero writes from the hooked semantic
and direct packet producers in those ranges.** The other eight addresses
exactly matched source-frame direct writes. The camera/view verifier passes
and reports the survey coverage. The track-bucket verifier passed with 478
entries, 324 headers and zero unmatched in-view submissions; the cube
consumer verifier passed with 728 draws and four command writers.

Two preceding survey replays also exposed a valid packet mix that the old
camera/view verifier rejected. Their post-view roots had 245 and 248 unique
addresses; 206 in each had appeared in prior backend frames. The newly seen
addresses split into 38/39 direct writes and 1/3 semantic writes, all matched
exactly with no remaining unexplained new address. Of the direct writes,
27/29 occurred within the existing direct-emitter scope, while 11/10 used
the indexed2 path outside it. The semantic writes record emitter caller
`0x82412E1C` in `sub_82412DD8`. The verifier now accepts both known direct
paths, counts semantic/indexed writers, and reports any genuinely uncovered
new address instead of assuming all post-view writes follow indexed2.

The zero-hit resident survey excludes **only** the hooked packet producers
in its ranges during this replay. It does not prove no guest write occurred:
another title writer, a loaded/prebuilt stream, GPU production or earlier
allocation could supply the recurring packets. Stable packet addresses and
draw metadata still do not establish byte freshness or owner identity.
SNR-01/02 need a write/freshness observation on these known pages and a
title reference back to their allocator or scene owner before this portion
of the proposed main-view slice can be claimed or suppressed.

### Sampled bytes of recurring draw packets

The prepared-draw observer now hashes the bounded PM4 draw packet bytes at
the backend callback. It reads from the observed physical packet address to
the draw end, or to the command-buffer end when the draw-end offset is zero;
it rejects out-of-bounds spans and limits the sample to 32 bytes. This is a
diagnostic sample at draw preparation, not a guest-memory write watch or a
resource-generation rule.

The rebuilt executable SHA-256 was
`22D8268E6331BF6BFE5595C7845E1D4AB74079A26F7815DA48A95619FAA6CB7C`.
The sustained race exited normally with seven PPM captures; log
`.local/native-renderer/snr01/packet-byte-hashes-run-a.log` SHA-256 was
`1A7935F6A3E9A3EBDF52ECBD000AFAA04B1058ADA01B7749D2D134106C8FD9DF`.
All 14,912 traced prepared draws had a valid nonzero packet span (8, 12 or
20 bytes), and no frame/packet-address pair had conflicting sampled hashes.
The post-view root consumed 249 unique packet addresses; 206 occurred in
prior backend frames and **all 206 had matching packet byte lengths and
hashes** between those frames and backend frame 6001. The other 43 newly
observed addresses matched 40 source-frame direct writes and three semantic
writes. The generalized camera/view verifier passed with zero uncovered new
addresses. The track-bucket verifier passed with 455 entries, 334 packet
headers and zero unmatched in-view submissions; the cube-consumer verifier
passed for 728 draws and three command writers.

The byte samples make repeated PM4 draw-packet identity stronger than address
and shader-metadata recurrence alone. They do not cover referenced vertex,
index or texture bytes, prove that no write happened between samples, or name
the title owner of the resident stream. SNR-01/02 and Gate A remain open.

### Guest write watch on recurring packet pages

The next default-off probe uses ReXGlue's existing physical-memory access and
invalidation callbacks. On the first prepared draw at backend frame 5999, it
arms the packet header's physical page (only the two surveyed resident ranges,
up to 1,024 pages). It records later guest accesses and write invalidations
through frame 6001. The callback limits unwatching to the faulting range so
another cache's wider invalidation cannot silently disarm neighboring watched
pages. This is a one-shot page observation, not an exact-byte watch.

The replay build's executable SHA-256 was
`EA64056C48AAFA9F4D8E38E7B6F20EBD710049E5782A4429E8DD24264AE891BC`.
Its seven-capture, normal-exit sustained-race log
`.local/native-renderer/snr01/packet-page-watch-run-b.log` SHA-256 was
`5024F5CD23AFAEBF46F544E68CA178BCB2051C3423D79BC39CFC850EB8A2C156`.
The probe armed 730 distinct pages in frame 5999. The frame-6000 post-view
command consumed 192 unique draw packet addresses in backend frame 6001;
183 were recurring. **All 183 recurring addresses lay on 99 armed pages, and
none of those pages generated a guest access or invalidation notification**
between arming and the end of the observed window. All 183 recurring packet
byte hashes matched the preceding frames. The nine newly seen addresses
matched title direct-packet writes. The camera/view verifier reports this
coverage; track-bucket and cube-consumer verifiers also pass with their
documented frame selections.

The first version of the probe, before narrowing the callback unwatch range,
recorded two guest writes to other packet pages, neither used by its 147
recurring post-view addresses. That replay is useful as a callback activation
check but not the strongest no-write claim, since wider cache invalidation
could unwatch adjacent pages. The final replay has no such notifications.

This excludes observed guest CPU writes to those armed physical pages during
this three-frame window. It does not establish when or by whom the resident
streams were originally built, exclude host writes that bypass this callback,
prove referenced geometry and textures stayed unchanged, or extend the result
to other gameplay frames. SNR-01/02 and Gate A remain open. The next title-side
join must identify the owner of these resident command buffers and the
resource generations they reference before the proposed slice can be frozen.

### Render-thread request boundary after the presentation views

The next read-only hook brackets `CRenderThread` slot 8 at
`sub_8245AEF8`, recording the render-thread object, mode argument and
request pointer. Static generated code confirms the common return at
`0x8245BB7C`; the existing post-view path calls `sub_823F10C8` from this
slot at return `0x8245B870`. This tests whether that path shares the same
request scope as the eight presentation-view calls.

The sustained-race replay exited normally with seven captures. Its
executable SHA-256 was
`C93E989478209E3623A9AC7C809E4F53043CE20C7CFB358CB85E73693EE14A79`;
`.local/native-renderer/snr01/render-request-join-run-a.log` SHA-256 was
`4F4A805A6188EECFF177C6AB34975DA0182003564AE80573FBF8179463920C18`.
All eight source-frame-6000 presentation-view calls ended **before** the
observed slot-8 request began. The post-view inline command at physical
`0x1329FAAC` was published within that request on the same title thread.
The request used mode `1`, request pointer `0`, and render-thread object
`0x40159510`; it enclosed no presentation-view call. Later slot-8 calls on
the same object used modes 5, 2 and 4, with null request pointers.

`tools/verify-snr01-camera-view-join.py` now checks this nesting when the
slot-8 trace is present while accepting older captures without it. The
post-view command led to three primary roots and 84 prepared draws from 38
unique packet addresses in this replay; 28 recurred from prior backend
frames and ten matched source-frame direct writes. The track-bucket verifier
again found zero unmatched in-view submissions, and the cube-consumer
verifier passed for 728 draws.

This identifies the post-view publication as a later render-thread mode-1
operation. It does not make that operation a semantic scene owner or carry
the earlier camera into it. SNR-01 must recover the producer and owner of
the resident indirect buffers and the state read by the deferred command
before assigning the post-view draws to the proposed main-view slice.

### Title scene list to child indirect-buffer execution

Static generated code shows `sub_82416A00` retaining its list argument in
`r24` and writing child PM4 indirect packets from that list. The existing
scene-dump hook at `0x82416F18` now records the physical packet header,
target buffer, word count, list object, immediate caller and active view
call in the bounded SNR-01 trace. The backend indirect observer reports the
same header/target pair when executing each child buffer. This join uses
exact addresses and does not infer an owner from a shader or packet range.

The first normal-exit, seven-capture replay used executable SHA-256
`2DFE2783DC1AF1A3F0FA21CD730782354CC0E1365CD1D00091928ACFAF8603A5`;
`.local/native-renderer/snr01/scene-indirect-run-a.log` SHA-256 was
`DFE09ED3A87F40CF5B765FA8B85D67C060958C4C642A5A73F5D44A78F11B014C`.
It recorded 1,069 scene-list child packet pairs in source frame 6000. In
backend frame 6001, 1,395 of 1,410 child indirect executions matched one
of those pairs. The post-view command produced 84 draws: all 54 draws in
child buffers matched list packets emitted inside view call 8, while 30
draws were direct in the later root buffer.

A second normal-exit, seven-capture replay added an entry/exit scope around
`sub_82416A00` to retain its immediate caller. Executable SHA-256 was
`861E592B2EE178164942D56C2C8E14E36E876F210BB37AA1FB29339B370962A1`;
`.local/native-renderer/snr01/scene-indirect-caller-run-a.log` SHA-256 was
`5D016502E10172E7BF754C384D6E42BDBBD594878F11242BC940CC51765F7D17`.
Of 1,490 backend-6001 child executions, 1,475 exactly matched source-frame
scene-list packets. Its post-view command had 38 draws: all five nested
draws matched two list objects emitted inside view call 8, with immediate
caller `0x82416898` (`sub_824167F8`); 33 draws were direct in the root
buffer. Across all scene-list packets, 1,147 used that caller and 49 used
`0x8246E930` (`sub_8246E8F8`). Fifteen child executions did not match this
writer in either capture and remain a separate producer path.

The camera/view verifier now requires the exact scene-list join for every
post-view nested draw when the title scene trace is present and reports the
unmatched child-execution count separately. Track-bucket and cube-consumer
verifiers also pass for the second replay (zero unmatched in-view submitted
items; 728 cube-sampling draws).

This identifies the title **command-list object** that submitted the
resident child buffer in these captures. It is not yet the semantic mesh,
material or view owner of each draw, and it does not classify the direct
root-buffer draws or the 15 other child executions. Follow the callers of
`sub_824167F8` back to the scene object and map each list entry to its
resource generation before SNR-01/02 or Gate A can close.

### Car owner above the scene-list flush

`sub_824167F8` is the immediate caller of most `sub_82416A00` list
emissions. A read-only scope at its entry and common return now carries its
own caller onto the exact scene-indirect packet record. In a normal-exit
seven-capture replay (executable SHA-256
`173D824022FE2DACFDC98E6B4702816555DF69E8CCF46D4D30FEC99061439CBF`;
`.local/native-renderer/snr01/flush-caller-run-a.log` SHA-256
`BB56A6EC986E9E80CA4B56754BB10A14C4D6153114FB0B2980B7F569CE80172F`),
the post-view command had 180 prepared draws: all 156
draws in child buffers matched view-8 scene-list packets; 24 drew directly
in the later root buffer. The 156 nested draws split by flush caller into
`0x8243CE0C` (113), `0x8241A2A4` (28), `0x824399F0` (12), and
`0x824170BC` (3). These return sites belong to `sub_8243CDC0`,
`sub_82419A30`, `sub_82439960`, and `sub_82417060`, respectively.

The next replay captured the object retained by each of those four caller
functions. Static generated code retains entry `r3` in `r31` for the
`0x8243CE0C`, `0x824399F0` and `0x824170BC` paths, and in `r30` for
`0x8241A2A4`; those are the registers observed at the flush call. This
normal-exit replay used executable SHA-256
`79C5FEE10B510B98C8941D3ACE26A14D4CEACD9ADB97AB6A02026A7A14DF052E`;
`.local/native-renderer/snr01/flush-owner-run-a.log` SHA-256 was
`78628A0D0E57F8B2110093C49CB4EDE239BCD4157C42F67D77FE7D918C258B32`.
It produced seven captures. All 132 nested post-view draws joined exactly
to scene-list packets from view call 8; 27 draws were direct in the root
buffer. The nested draws used 54 list objects under nine retained owners.

The first word of the retained owner is `0x82003A54` for 97 draws through
`sub_8243CDC0`, and `0x82001618` for 32 draws through `sub_82439960`
and `sub_82419A30`. The verified base image
(SHA-256 `6014727FA7B0B79727FD5F32A2E2377533DC8E29679E8D2462BD764D331FA305`)
resolves these vtables through RTTI locators `0x823631DC` and
`0x8235E204` to `CCarPresentation` (inside a thread-safe ref-counted
wrapper) and `CCarModel`, respectively. The remaining three draws came
through `sub_82417060`; their owner's first word is `0xBF283F61`, not a
vtable, so that state pointer remains untyped.

The camera/view verifier reports exact scene-list joins, flush callers and
owner first words when these fields are present. It passes this replay;
the track-bucket verifier reports zero unmatched in-view submitted items,
and the cube-consumer verifier passes for 728 draws. These results prove
car-related title owners for the nested post-view packets in this window.
They do not distinguish player from traffic cars, classify the 27 direct
root-buffer draws, map car materials/geometry or prove resource freshness.
Those remaining joins are required before SNR-01/02 and Gate A can close.
