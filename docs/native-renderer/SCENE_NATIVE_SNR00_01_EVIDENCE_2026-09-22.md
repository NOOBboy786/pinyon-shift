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

### Character and vegetation bound-record identity

In the generated character slot-41 function, the render-context
vtable-offset-124 call binds `owner + 132` immediately before its
vtable-offset-164 draw. In the vegetation function, the corresponding
binding argument comes from a loop-derived record pointer:
`record = running_40_byte_offset + *(owner + 108 + group_offset)`.
The same loop walks 12-byte count entries and 8-byte selector entries.
These are binding records, not yet verified mesh or instance objects.

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

The repeated addresses are frame-local identities only. The next probe
must classify the slot-31 record's underlying geometry payload and
generation, then join the final transform/material state without reading
mutable guest state after frame publication. SNR-01 remains open.
