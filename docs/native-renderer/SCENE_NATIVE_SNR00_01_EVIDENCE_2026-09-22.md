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
