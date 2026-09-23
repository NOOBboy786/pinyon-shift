# Scene-native SNR-03 bounded publication evidence

Status: **metadata, guarded vertex bytes and final draw-state variants published for one view-8
vegetation contribution; SNR-03 and Gate A remain open.** This is not a final
transform/material scene, native rendering or a performance result.
Compatibility output remains the default.

The default-off `pinyon_shift_snr03_probe_frame=6000` probe copies each
submitted view-8 vegetation item's selected title owner, record, vertex
descriptor/address/size, packet address and bucket entry. At view end it
copies the two observed 16-word camera matrix regions and moves the ordered
items into an immutable owned snapshot keyed by source frame. The output
callback accepts only that exact source frame at output frame 6001; it never
substitutes a newer snapshot. The pending map holds at most two frames and
reports a drop, missing frame or rejected snapshot rather than silently
using stale data. The probe records no output commands, and the original
render-test callback and compatibility image remain in place.

The saved sustained-race replay exited normally with seven compatibility
captures. Executable SHA-256 was
`0E3FB5E9ACAC1E8A37ABD2AB238C33C33DAA05E70356384B9A4FEC57EACE74E0`.
The ordered log at
`.local/native-renderer/snr03/vegetation-publication-run-b-session.log` has
SHA-256 `F4AD4B46CD8AB66F1897775E79FC47B401BAAECB72FDE6A8F8C2D1EC11ECC7AD`.
The frame-wide ledger at
`.local/native-renderer/snr03/vegetation-publication-run-b-ledger.json` has
SHA-256 `5B49BE9D0A4105441776055824E3F1B55F4861416FBCEA4882703A24B2A99B64`.

The title published 65 ordered items for source frame 6000, view object
`0x4223FBA0`, camera `0x2E4AA200`; output frame 6001 consumed the same
65-item fingerprint `15948577987137503943`. The verifier independently
joins every published packet to the ledger's title view, vegetation caller,
owner, selected record, vertex descriptor/address/size and bucket entry.
All 65 packet addresses match in title submission order, producing 135
backend-frame-6001 prepared-draw callbacks. The separate track-bucket
verifier finds 130 vegetation packets across depth and color views, 65 bound
records and 200 callbacks in this replay. Thus the bounded view-8 publication
contains all of that route's selected vegetation packet identities, while
retaining their original order and one-to-many backend execution.

The earlier replay of the first version of this probe also published and
consumed the exact source/output pair, with 55 items and matching
fingerprints. The change to 65 is route/visibility variation, not a
cross-replay identity comparison. Pointer values and packet addresses are
valid only within one replay. That metadata-only snapshot copies descriptor
*addresses*, not the referenced vertex bytes or a resource generation. It
also has not established the final per-item transform or material. Those
fields must be proven before a native diagnostic draw can consume the
snapshot; this
metadata handoff alone does not close SNR-03 or SNR-04.

After adding explicit pending-scene cleanup on shutdown, that version's
RelWithDebInfo build had executable SHA-256
`166EB1C00F0E1469C7E6FB4A00465A31EEC8775CEBCDFB8E6D9CE8A2FF860D90`.
With the SNR-03 probe disabled and no diagnostic arguments, the same saved
route exited normally and produced all seven compatibility captures. Its
`fh1.render_test.complete` event reports frame 6920 and seven captures.
This is a default-off smoke check, not an image-equivalence or FPS result.

Reproduce the bounded check with the saved AppData profile and no existing
`pinyon_shift` process:

```powershell
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
.\tools\launch-preview.ps1 -Configuration RelWithDebInfo `
  -StateRoot $stateRoot `
  -RenderTestScript config/render-tests/fh1-race-sustained.fh1test `
  -RenderTestOutput .local/native-renderer/snr03/<run-id> `
  -RenderTestTimeoutSeconds 240 -Hidden `
  -GameArgumentsJson '["--pinyon_shift_fh1_gpu_corpus=true","--pinyon_shift_snr01_trace_source_frame=6000","--pinyon_shift_snr01_trace_following_frame=true","--pinyon_shift_snr03_probe_frame=6000"]' -Json
python tools/summarize-snr01-frame-wide-census.py <ordered-log> `
  --source-frame 6000 --require-direct-family `
  --require-direct-family-record --require-semantic-item-node `
  --require-second-path --output <ledger.json>
python tools/verify-snr03-vegetation-publication.py <ordered-log> `
  <ledger.json> --source-frame 6000
```

## Guarded vertex payload handoff

The next default-off probe decodes the title descriptor words for the same
view-8 vegetation packet set and calls the SDK's existing
`SharedMemory::CopyCpuSnapshot` on command-thread fetch 95. That routine
rejects GPU-written pages and invalidation during a CPU copy. The probe only
attempts four-word-stride fetches on backend frame 6001, limits each range to
32 KiB and the frame to 2 MiB, and passes successful bytes to the prepared
draw observer for immediate copying. A first run attempted unrelated fetch-95
layouts and exhausted the 2 MiB cap before vegetation; narrowing the probe to
the observed four-word stride addressed that instrumentation error. The stride
is a probe filter, **not** semantic native-renderer admission.

The saved-race replay of the owned-byte version exited normally with seven
captures. The selected title scene had 67 packet identities, and 142 prepared
fetches joined them. Every joined fetch decoded to the title base, length and
type, returned a guarded CPU snapshot, and produced one stable content hash
per packet across repeated executions. The output callback found every
selected packet and built an immutable owned scene with **376,272 unique
vertex bytes**; repeated backend copies totaled 858,224 bytes. No scene or
geometry rejection was logged. The first selected fetch followed title
publication, and all selected fetches preceded output-frame consumption.

The instrumented-run executable SHA-256 is
`0FB772EAC60BFDC5191150B46DFC15FA3A4CBB2824FCB7835C20E5EE0C197170`;
the D3D12 DLL SHA-256 is
`1D645CD6F09827C4DD5B7904F063818C764C0F2EA4226572F3413A56B992CDFB`.
The filtered ordered evidence log is
`.local/native-renderer/snr03/owned-vertex-run-a-signal.log` with SHA-256
`CDEFCB2F55ECCAD5CBDD027A21067A7FA18E2743E72BABE151CC231EDEC8CA5A`.
The verifier is:

```powershell
python tools/verify-snr03-vertex-cpu-snapshots.py `
  .local/native-renderer/snr03/owned-vertex-run-a-signal.log `
  --source-frame 6000
```

The first probe-only replay found that title view hooks still required the
SNR-01 trace flag and logged a missing scene. The corrected title frame gate
uses the SNR-03 probe frame independently. With only
`pinyon_shift_snr03_probe_frame=6000` enabled, a repeat replay exited
normally, published 59 items and consumed an owned 252,304-byte contribution
at output frame 6001 with no rejection and seven compatibility captures.
The final executable SHA-256 is
`1E6075F0EB5D9E3D119D737AF126A1A64CB094DA8CFD12078BB52181E0F82947`,
with SDK revision `e45fe08c7d7a5e2cd408586d088447d5986447b0`.

With the probe off, that final build again completed the saved route normally
at frame 6920 and produced seven compatibility captures. This is a smoke
check, not an image-equivalence or FPS comparison. The owned contribution is
now suitable as a vertex-byte input to a future diagnostic, but it still
lacks final per-item transforms, semantic materials, index/topology proof for
native drawing, and the rest of the main-view slice. SNR-03/SNR-04 remain open.

## Vegetation draw-state and packed-quad evidence

The translated color vertex shader `5834939992FFC765` computes
`floor(vertex_id * 0.25)` before loading a 16-byte source record. The guest
emits non-indexed quad lists (`primitive_type=13`), and all 67 selected
view-8 packets have `index_count * 4 == fetch_95_length`. Together these
establish one captured 16-byte record per guest quad. The SDK's current
quad-list expansion is a plausible triangle source, but its winding and the
native decode of the packed values are not independently verified.

The command-thread binding dump now includes the physical draw-packet key
and covers the vegetation shaders on probe frame 6001. Joining that key to
the title publication found 142 prepared executions for the 67 selected
packets. Each has the same color vertex/pixel shader pair, attachment state,
quad count, fetch base and length, and 24 observed vertex float-constant
registers across its repeated executions. Two of those constant vectors
(registers 17020 and 17024) are stable within each of the seven title owners
and distinct between owners. These are **raw final draw-state words**, not
yet identified as model transforms or camera matrices.

The owned scene now copies those 24 register vectors and the guest vertex
count on the command thread, along with the guarded vertex bytes. Repeated
executions of a selected packet must agree; the output callback hashes only
the owned copy. An initial replay correctly rejected the scene because the
new probe indexed the register bank from `0x4200`; the bank begins at
`0x4000`. With the offset corrected, the saved-race replay exited normally,
produced seven compatibility captures, and consumed 67 packets, 376,272
unique vertex bytes and 24 constant vectors per item on output frame 6001.
The executable SHA-256 was
`BA75D45B732F093824B201CE6BD22E927FA084BE20B600E097C5BC1F0D46807A`;
the SDK revision is `54bdb02cbb0b391135d92e2d41c32cdd4cc573d1`;
the D3D12 DLL SHA-256 was
`E24F81E16DE98CEE64F9944F601F5D8496868D65C3932E22044BFC7CA5C119E1`.
The ordered filtered evidence is
`.local/native-renderer/snr03/owned-state-run-b-signal.log` (SHA-256
`6994862BB59EFD19D1A5C2D8B4EFE9958510A07704FC22CB96ADE18EBA599595`).
Check it with:

```powershell
python tools/verify-snr03-vegetation-binding.py `
  .local/native-renderer/snr03/owned-state-run-b-signal.log `
  --source-frame 6000
```

The same final build with the probe off completed the saved route normally
and produced seven compatibility captures. This is a compatibility smoke
check, not an image-equivalence or performance result.

This extends one bounded immutable contribution; it does not close SNR-03 or
SNR-04. Semantic transforms, the rest of the selected main-view scene,
native identity/depth output and full-resolution comparisons remain open.

## Final system state belongs to a dynamic draw variant

The prepared-draw callback precedes `UpdateSystemConstantValues`, so its
vertex constant copy cannot own the SDK's final clip/viewport state. A second
read-only callback now runs immediately after that update. For the selected
vegetation packets it copies the first 40 system words and the four fetch-47
words into the bounded output-frame scene. The words are borrowed only during
the callback; the scene holds its own copies and includes them in its
fingerprint.

The first replay rejected the scene: repeated executions of the same packet
changed system word 33 (`ndc_scale.y`) from `1.0` to about `1.552`. A follow-up
replay showed 60 selected packets with two distinct prepared-draw dynamic
states and 12 with one. The change is a real viewport variant, not evidence
that the packet's vertex bytes changed. Treating a packet as one final draw
state would discard authoritative execution state.

The scene therefore owns up to four final states per packet, keyed by the
prepared draw's dynamic-state hash. Repeated executions under the same key
must have identical system and fetch words; an extra variant, changed bytes,
missing state or missing packet rejects the scene. The saved sustained-race
replay exited normally with seven compatibility captures. Source frame 6000
published 67 selected packet identities; backend frame 6001 produced 142
distinct `(packet, dynamic state)` snapshots and consumed an immutable scene
with 376,272 unique vertex bytes. The final replay's packet repeat
distribution was 22 once, 15 twice and 30 three times. The verifier joined
**all 142** variants to the 142 distinct prepared bindings, checked fetch
words against the binding dump and exact title camera words against every
selected execution. No
geometry rejection or final-state mismatch was logged.

With the probe off, this same build completed the saved route at frame 6920,
exited normally and produced seven compatibility captures. This is a smoke
check, not image equivalence or a performance result.

Executable SHA-256: `B90539CFD9569485587733D341A3E0E9EC1D98C64A59A826F7F969C91B5BAB99`.
D3D12 DLL SHA-256: `4DC57BB9505AFF3B3056BDE75891F1068155B80936021783D4EA8E341E3E5037`.
The filtered ordered log is
`.local/native-renderer/snr03/final-system-run-d-signal.log` (SHA-256
`10A8105465AB113D78BCF927225826FB696D4A05D72D7FCBF3ED6EADE24C4DBB`).
Recheck it with:

```powershell
python tools/verify-snr03-vegetation-binding.py `
  .local/native-renderer/snr03/final-system-run-d-signal.log `
  --source-frame 6000 --require-camera-match --require-final-state `
  --reference-size 1280x720
```

These are raw final system words, not a proved native clip transform. The
diagnostic still needs to select the correct dynamic variant for each native
submission, validate packed-quad decode and depth, and expand beyond this
vegetation contribution to the complete frozen main-view slice. SNR-03 and
SNR-04 remain open.

The SDK's offline shader analysis catalog also resolves the vertex constant
layout without a register-order guess. Its entry for vegetation VS
`5834939992FFC765` has `float_count=23`, one fetch `(95, 4)`, and bitmap
indices `128–131, 157–161, 163, 214–215, 221, 241–245, 250–251, 253–255`.
These are exactly the first 23 vectors in the owned draw's sorted constant
array; the 24th captured vector, index 256, is outside this vertex shader's
map. The catalog at
`.local/native-renderer/seeded-probe/producer-state/cache/fh1-native-shaders-v2.bin`
has SHA-256
`3C77C669F68F645B5F2B27351D1BB1054B98EE92A3AADE5057D5B2F428CAA5C2`.
Its captured specialization-`0x1F` bytecode has SHA-256
`2ADFE080228C468CE9AEC7E21D19798FC8AAA32CDBA5D7325C4FAC4070F21FAA`.
The bytecode expects system, compressed float and fetch constant buffers plus
raw shared-memory SRV/UAV bindings. Feeding it owned vertex bytes still
requires an explicitly remapped fetch base and a private diagnostic pipeline;
the catalog match alone is not a native render.

The captured VS applies its final viewport remap as
`clip.xyz = clip.xyz * ndc_scale + clip.w * ndc_offset`. In the final 1280×720
replay, all 142 selected dynamic states had `scale.x=1`, `scale.z=-1`,
`offset.x=1/1280` and `offset.z=1`. Their Y scales were 1.0 (45 states),
1.551724 (67) or 3.461539 (30), with different bin selections. For every
state, `(offset.y + 1) / scale.y - 1` equals `-1/720` within `10⁻⁶`.
This is evidence that the repeated packet executions use vertically tiled
viewport remaps and that a full-resolution diagnostic can normalize this
*system* remap to `(1, 1, -1)` and `(1/1280, -1/720, 1)`. It does not prove
the upstream billboard/clip calculation or depth parity. Recheck the invariant
with `--reference-size 1280x720` on the verifier command above; a deliberately
wrong 1280×800 reference is rejected.

## Same-frame owned-scene fixture for the first SNR-04 draw

The probe now writes `snr03-scene-6000.bin` beside a scripted render test's
captures after exact output-frame consumption. This local-only `SNR03F1`
little-endian fixture contains source frame, title view/camera and both camera
word arrays, then ordered item metadata, all 24 captured constant vectors,
guarded vertex bytes and every `(dynamic state, 40 system words, 4 fetch words)`
variant. The writer closes a temporary file before renaming it to the final
name; a failed or partial write is never presented as a fixture. It does not
write to the guest output or change the save.

The saved sustained-race replay exited normally with seven compatibility
captures. At output frame 6001 it wrote a 431,500-byte fixture in 2,071 µs,
containing 67 ordered packets, 376,272 unique vertex bytes and 142 final-state
variants. The fixture SHA-256 is
`0D46FE9CCE413E9B97BC780ABCAE26AFE5E3255A05B3E82EF3F3D8EB03BFB673`;
the executable SHA-256 is
`D090DE04CA792B92B96F62A9DABE22C8A341BBEBDBF527F005D60EE4F05C956A`.
The filtered ordered log at
`.local/native-renderer/snr03/scene-fixture-run-a-signal.log` has SHA-256
`F1C8C9BF082CD574E20CCE23D1E2BB3D0B6A543A47F0A9138A8B98D9B7ECFDE3`.
The parser checks every item, all 24 constant vectors per selected prepared
binding, the final-state keys and logged system/fetch words, camera rows,
lengths and end-of-file. It rejects a truncated fixture and a deliberately
corrupted constant:

```powershell
python tools/verify-snr03-scene-fixture.py `
  .local/native-renderer/snr03/scene-fixture-run-a/snr03-scene-6000.bin `
  .local/native-renderer/snr03/scene-fixture-run-a-signal.log
```

The same executable also completed the sustained-race route with the SNR-03
probe disabled: normal exit, seven compatibility PPM captures and no fixture.

This is a reproducible input for the first private identity/depth experiment,
not a GPU draw or a Gate A result. The fixture is one frame of one vegetation
contribution; it does not establish winding, transformed positions, depth
parity, material/resource lifetimes or complete selected-slice coverage.

## Captured quad decomposition for the vegetation shader

The local RenderDoc race-start capture at
`.local/cpu-profile/traffic-attribution/race-start-capture_frame4709.rdc`
(SHA-256 `2CCCD83B0ADEBB6E9E96CD0C846986FB6036D415340B93267260F4CA92F59CB7`)
contains draw event 27072 with 160 vertices and the **exact** vegetation VS
bytecode SHA-256 `2ADFE080228C468CE9AEC7E21D19798FC8AAA32CDBA5D7325C4FAC4070F21FAA`.
RenderDoc identifies its input topology as `LineList_Adj`; the captured GS
expands 160 VS vertices to 240 triangle-list vertices. Of 40 quads, 39 have
identical positions at all four vertices. The one nondegenerate quad (index
32) maps to triangle indices `(0,1,3)` and `(1,2,3)` by exact post-VS/post-GS
position bytes. The local output is
`.local/native-renderer/snr04/quad-evidence.json` (SHA-256
`11BFE090D48E1ED69D0FE35383A295820502B0FA35235DF19C5BD5AD80F803FE`).

`tools/check-snr04-renderdoc-quad.py` reproduces the check when run through
the bundled qrenderdoc Python host with `SNR04_CAPTURE` set to that capture,
`SNR04_EVENT=27072`, and `SNR04_OUTPUT` set to a local JSON path. It checks
the bytecode hash, topology, counts and every nondegenerate quad; event 495
is rejected as a wrong shader. The same draw has depth writes with
`GreaterEqual`, so the private diagnostic clears depth to zero and uses that
comparison. This establishes the compatibility renderer's
quad decomposition for that shader. The old capture is at a different frame
from source frame 6000, so it does not yet establish same-frame post-VS,
coverage or depth parity for the owned fixture.

## Offline full-resolution private diagnostic

`pinyon_shift_snr04_owned_scene_diagnostic` replays the verified frame-6000
fixture through the exact SHA-checked vertex shader into private 1280×720
RGBA identity and D32 depth targets. It rebases fetch 95 onto each owned raw
buffer, uploads the first 23 catalog-mapped float vectors, uses one system
variant after validating that alternatives differ only in viewport Y words,
normalizes that viewport to 1280×720, and indexes each guest quad as
`(0,1,3)` and `(1,2,3)`. It waits for a GPU fence before readback. No game
output, save, or compatibility command list is involved.

```powershell
. .\tools\release-common.ps1
$toolchain = Enter-PinyonBuildEnvironment
& $toolchain.CMake --build --preset win-amd64-relwithdebinfo `
  --target pinyon_shift_snr04_owned_scene_diagnostic
& .\out\build\win-amd64-relwithdebinfo\pinyon_shift_snr04_owned_scene_diagnostic.exe `
  .local/native-renderer/snr03/scene-fixture-run-a/snr03-scene-6000.bin `
  .local/native-renderer/seeded-probe/translation/dxil/vertex_5834939992FFC765_000000000000001F.dxil `
  .local/native-renderer/snr04/offline-run-c
```

Two runs produced identical `identity.ppm` (SHA-256
`25646AAA945A80247094F22A669AE0F491876929EE0BEEB7E59CC3CBBE545695`)
and `depth.f32` (SHA-256
`31C1085BDB52B6332D2AA41FEAC171711C0438B47459543DB6BC49F95AF53C23`
after matching the captured 0–0.5 depth viewport).
All 67 packets were drawn; 410,331 pixels have a packet identity and 39
packets own at least one pixel. The remaining 28 may be offscreen or occluded;
zero final pixels is not evidence of unsupported geometry. The local summary
records per-packet pixel counts and one run's extraction 3.6 ms, resource and
pipeline build 290 ms, submit/fence/readback 55.7 ms and file write 44.3 ms.
These are cold standalone diagnostic costs, not frame-time or FPS results.
The executable rejects a truncated fixture and incorrect VS bytecode.

The identity image covers large billboard rectangles over scene regions where
the presented image is transparent. The diagnostic does not sample foliage
alpha textures or reproduce the compatibility pixel shader, so its pixels
cannot be compared directly to the presented color as visible foliage.

## Same-run RenderDoc post-VS comparison

A visible RenderDoc-wrapped saved-race run produced a different but internally
consistent frame-6000 fixture: 72 owned vegetation packets, 392,096 raw
vertex bytes and 189 final draw variants. The fixture SHA-256 is
`2FEEE3D8E83E5A807A6955B1E83809D323D504AEAA093360AF483D19659BB21D`.
`tools/verify-snr03-scene-fixture.py` passed against the same run's ordered
signal log. RenderDoc capture `extended-capture_frame6000.rdc` has SHA-256
`60D849F461DA39961437D99FC6DE8DD0EFDD20860FA51FAA33EC8D73613E7E51`.
Its selected draw count and per-vertex post-VS positions identify it as the
matching reference, despite the game's fixture publication reporting output
frame 6001. The separately captured RenderDoc frame 6001 contains only one
draw and is not the selected scene reference.

The private diagnostic now stream-outputs every item's VS positions using
the fixture's original viewport system words, while retaining normalized
1280×720 viewport words for its separate identity/depth raster pass. The
1,568,384-byte `postvs.f32x4` has SHA-256
`8D79C9C5BE3A346D45CBE742D0D0A1811C00DB1048A61D46504DB91E824F6466`.
`tools/check-snr04-capture-slice.py` found a byte-identical captured post-VS
stream for each of the 72 items. The capture contains exactly 189 draws with
the selected shader and fixture vertex counts, matching the fixture's
variant-weighted count distribution. This proves the owned geometry, fetch,
constants, and original viewport state produce the same VS positions for
every selected item in the captured frame. It does not identify each of the
other 117 viewport variants by packet identity. All 189 selected draws use
viewport depth range 0–0.5, which the private raster pass now matches.

To reproduce locally, copy `config/render-tests/fh1-race-sustained.fh1test`
to `.local/native-renderer/snr04/renderdoc-extended.fh1test`, change only
`stop 6920` to `stop 9000`, and launch the built preview visibly with the
repository's AppData `-StateRoot` procedure:

```powershell
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
.\tools\launch-preview.ps1 -Configuration RelWithDebInfo -StateRoot $stateRoot `
  -RenderTestScript .local/native-renderer/snr04/renderdoc-extended.fh1test `
  -RenderTestOutput .local/native-renderer/snr04/renderdoc-extended-output `
  -RenderTestTimeoutSeconds 360 `
  -RenderDocCommand .local/tools/renderdoc-1.46/RenderDoc_1.46_64/renderdoccmd.exe `
  -RenderDocCapturePrefix .local/native-renderer/snr04/extended-capture `
  -GameArgumentsJson '["--pinyon_shift_fh1_gpu_corpus=true","--pinyon_shift_fh1_scene_dump=true","--pinyon_shift_snr01_trace_source_frame=6000","--pinyon_shift_snr03_probe_frame=6000"]' -Json
```

While that run is active, run `qrenderdoc.exe --python` with
`tools/queue-snr04-renderdoc-capture.py` and `SNR04_OUTPUT` set to a local
JSON path; its target control must connect and register D3D12 before it queues
frames 6000–6002. Then set `SNR04_CAPTURE`, `SNR04_FIXTURE`, and
`SNR04_OUTPUT` for `tools/probe-snr04-renderdoc-slice.py` in the same way and
run it through `qrenderdoc.exe --python`. Run the private diagnostic on that
fixture and exact VS bytecode, then compare with:

```powershell
python tools/check-snr04-capture-slice.py `
  .local/native-renderer/snr04/renderdoc-extended-output/snr03-scene-6000.bin `
  .local/native-renderer/snr04/offline-same-run/postvs.f32x4 `
  .local/native-renderer/snr04/tracked-slice-probe.json
```

This post-VS result still does not test compatibility depth or visible
coverage. The diagnostic uses unmasked identity pixels, and no native live
callback or unload/reload path has been qualified. Gate A stays open.

### Bounded compatibility depth readback

At matched item 27, RenderDoc event 11206 writes a `D32S8_TYPELESS`, 4×MSAA
depth target. Its backing texture is 1280×512 while the viewport is 1280×720
with depth range 0–0.5. Sample 0 changes 27,072 texels between event 11205
and 11206. The private diagnostic previously used depth range 0–1, making
overlapping values roughly twice the capture's depth. After changing its
range to 0–0.5, 18,123 changed sample-0 texels overlap the diagnostic's
final item-27 identity. Their median absolute depth difference is
`0.00000400096`; 11,439 are within `0.0001`, while the maximum difference
is `0.01682`. This is **partial** evidence of depth mapping, not a pass:
the private raster still lacks foliage alpha, preceding scene depth and 4×
sample coverage. It cannot prove visible coverage or depth parity for this
item, let alone the full selected slice.

`tools/probe-snr04-renderdoc-depth.py` reproduces the before/after readback
with `SNR04_CAPTURE` set to the frame-6000 RDC, `SNR04_EVENT=11206`, and
`SNR04_OUTPUT` set to a local JSON path. It writes two local raw depth files
beside the JSON. Recheck the bounded overlap with:

```powershell
python tools/check-snr04-depth-overlap.py `
  .local/native-renderer/snr04/item27-tracked-depth.json `
  .local/native-renderer/snr04/offline-same-run/identity.ppm `
  .local/native-renderer/snr04/offline-same-run/depth.f32 --item 27
```

### Private diagnostic on the live output callback

The same SNR-03 output-frame callback now invokes the private renderer when
`PINYON_SHIFT_SNR04_VS` names the exact locally translated vegetation VS.
It receives the callback's D3D12 device and already-owned frame-6000
scene bytes, creates separate color/depth targets and a private command queue,
waits for its fence, and writes diagnostic readbacks before returning. It
does not bind or write the guest output; the callback still yields to normal
compatibility rendering. With the variable absent, no diagnostic GPU work is
scheduled. The standalone executable calls the same renderer source.

The initial two AppData-backed sustained-race replays wrote `snr04-private-6000` during
output frame 6001 and exited normally with all seven compatibility captures.
The second replay's `SNR03F1` fixture has SHA-256
`D2A8FFDAB08A4A4D5FC1402379EDF42F9960A8DA41D7AF18A8D9D6D5C6FA5A02`;
`tools/verify-snr03-scene-fixture.py` passed its 67 ordered items, 376,272
vertex bytes, 135 final variants and title/command-state join. Its private
identity, depth and post-VS outputs each match a standalone replay of this
*same* fixture byte-for-byte (SHA-256 respectively
`5112A309739EF7BA746E542A9D5E334313A8A95CDEA8684080667409FD0A8A66`,
`32F7691B05405F16266E0BE52A3D4A7F1256BDE51C245686EE740A5C1E55F3B7`,
`768F650DF2A058261C5B43F90A2FA00B580A3053CBED310B4B1BF0A2BD0EA3E0`).
The callback logged 395,185 diagnostic identity pixels and 206,332 µs for
the cold diagnostic. That is not a frame-time or FPS comparison.
In a separate negative replay, setting `PINYON_SHIFT_SNR04_VS` to the fixture
instead of VS bytecode logged `reason=wrong vegetation vertex shader`, wrote
no private target, and still exited normally with all seven compatibility
captures. Thus a rejected diagnostic leaves guest output active.

The local verified output is `.local/native-renderer/snr04/live-run-b`; its
ordered signal log is `.local/native-renderer/snr04/live-run-b-signal.log`.
Reproduce with the saved-race procedure, a fresh render-test output path,
and the additional environment variable:

```powershell
$env:PINYON_SHIFT_SNR04_VS = (Resolve-Path `
  .local/native-renderer/seeded-probe/translation/dxil/vertex_5834939992FFC765_000000000000001F.dxil).Path
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
.\tools\launch-preview.ps1 -Configuration RelWithDebInfo -StateRoot $stateRoot `
  -RenderTestScript config/render-tests/fh1-race-sustained.fh1test `
  -RenderTestOutput .local/native-renderer/snr04/live-run-new `
  -RenderTestTimeoutSeconds 240 -Hidden `
  -GameArgumentsJson '["--pinyon_shift_fh1_gpu_corpus=true","--pinyon_shift_fh1_scene_dump=true","--pinyon_shift_snr01_trace_source_frame=6000","--pinyon_shift_snr03_probe_frame=6000"]' -Json
Remove-Item Env:PINYON_SHIFT_SNR04_VS
```

This is a live, frame-matched diagnostic for the **bounded vegetation
contribution**, not full selected main-view ownership or compatibility
coverage/depth parity. The fixture write and private queue/fence are
diagnostic costs, not a production bridge or suppression path.

### In-memory owned-scene handoff

The output callback now serializes its immutable `Snr03OwnedScene` once and
passes those bytes directly to the private renderer. The same bytes are
written as a separate `SNR03F1` fixture for verification; the fixture-write
result no longer gates the in-memory diagnostic call.
The standalone executable retains its file-path entry point. Neither path
rereads mutable guest state at the later output callback.

With RelWithDebInfo executable SHA-256
`E1E3A37281FDB18E8444758219ECA19B9B2E8BF1141BA99DFE9AF9FF95AC0483`,
an AppData-backed sustained-race replay exited normally with seven
compatibility captures. It consumed source frame 6000 on output frame 6001
and rendered 128,956 private identity pixels. The written fixture SHA-256
`B63567567079ADBEAE3B8856244F8B1493F264491FC9ABB7B01C3A42E8D9EB0F`
passed `verify-snr03-scene-fixture.py`: 60 ordered items, 306,176 owned
vertex bytes, and 120 final variants. The in-memory renderer's fixture hash
matches that file. A standalone replay of the same file produced
byte-identical identity, depth and post-VS outputs, with SHA-256 respectively
`109EA36B5FDC69C5D612F38C24D222160ECA16227A7BB49725371A24892375EB`,
`D042A06D72DBBCB7D475A8CD88A3F84FFC099D23D7165A4872F11F13211318BF`,
and `70BE32478A33305C1B050C8BF5C1ADE81D87821B50D0A4A304EF504AA95CC1A9`.
This verifies both entry points for the captured scene; it does not compare
different visibility sets or remove the private queue, fence and readback
costs. The diagnostic still covers only the bounded vegetation contribution.

The local replay is `.local/native-renderer/snr04/memory-run-a` and its
ordered log is `.local/native-renderer/snr04/memory-run-a-signal.log`
(SHA-256 `9526BEE24E7166A3BE3B5DA24B6C0A5E79492C37FCE8E47F5F70B66406871B90`).
The saved-race launch command above reproduces it with a fresh output path.
Recheck the fixture and standalone parity with:

```powershell
python tools/verify-snr03-scene-fixture.py `
  .local/native-renderer/snr04/memory-run-a/snr03-scene-6000.bin `
  .local/native-renderer/snr04/memory-run-a-signal.log
.\out\build\win-amd64-relwithdebinfo\pinyon_shift_snr04_owned_scene_diagnostic.exe `
  .local/native-renderer/snr04/memory-run-a/snr03-scene-6000.bin `
  .local/native-renderer/seeded-probe/translation/dxil/vertex_5834939992FFC765_000000000000001F.dxil `
  .local/native-renderer/snr04/memory-run-a-standalone-verify
```

## Title camera to selected draw-state join

The title scene publication now logs the two already-owned 4x4 camera word
arrays at offsets 80 and 144 for the one SNR-03 probe frame. No guest state is
modified. A normal-exit saved-race replay produced seven compatibility
captures and published 67 selected vegetation packets at source frame 6000.
They joined 132 command-thread prepared bindings at output frame 6001.

All 132 bindings contain title camera offset-144 row 2 exactly at vertex
constant register 17028 and row 3 exactly at register 17016. Registers
17356, 17360 and 17364 each contain the first three elements of a column
formed from offset-144 rows 0–2, also exact in every binding. The fourth
elements of those three registers differ from the corresponding title row-3
words by 1, 18 and 1 integer units in this replay. The verifier checks only
the exact relationships; those differing words are not asserted equal.
Offset-80 words do not have a comparable direct row/column match in this
selected shader's captured constant set.

This establishes a source-camera-to-final-draw relationship for the bounded
vegetation contribution. It does not yet prove the complete clip transform,
the role of offset 80, packed vertex decode, per-item transforms, or camera
stability under streaming and other modes. Those remain admission blockers
for SNR-04's native diagnostic.

The executable SHA-256 was
`98A6E196A0514DBBE77EF4071185F1AEEDC891C174B15FA045C48A360F59863B`.
The ordered filtered log is
`.local/native-renderer/snr03/camera-match-run-a-signal.log` (SHA-256
`481F232BFF758DC642C45579F28076ABEA3C4F57605AF87C1F8A00742674229B`).
Recheck the exact join with:

```powershell
python tools/verify-snr03-vegetation-binding.py `
  .local/native-renderer/snr03/camera-match-run-a-signal.log `
  --source-frame 6000 --require-camera-match
```

## Selected vegetation texture dependencies

The final `FH1 scene binding` records also carry the pixel-stage fetch
descriptors for each selected vegetation packet. The bounded
`--require-texture-descriptors` check joins them through the same packet
identity as the owned geometry, requires stable descriptors across repeated
executions, and decodes the title fetch words. It passes on the
`camera-match-run-a`, `final-system-run-d`, `scene-fixture-run-a`, `live-run-b`, and
`renderdoc-extended` signal logs. The latter is the capture-matched run:
72 selected packets and 189 prepared bindings. Each selected binding uses
slots 0 and 13. Slot 0 has five distinct 256×256 format-20 descriptors;
slot 13 has one shared 1280×720 format-6 descriptor. The descriptor words
establish sizes and binding identity, not texture contents or generations.

For the matched vegetation draw at event 11206 in
`extended-capture_frame6000.rdc` (SHA-256
`60D849F461DA39961437D99FC6DE8DD20860FA51FAA33EC8D73613E7E51`),
RenderDoc reports two pixel-stage images in that order: 256×256 BC3_UNORM
`ResourceId::7915` and 1280×720 R8G8B8A8_TYPELESS `ResourceId::8416`.
The latter's latest captured copy before this draw is event 9232 from the
16 MiB buffer `ResourceId::1600`; the buffer's latest prior compute
read/write use is event 9230. The repeatable probe compares actual bytes:
the copied 3,686,400-byte image equals source-buffer bytes
`[0, 3,686,400)` after event 9230 and is unchanged at draw 11206 (SHA-256
`F63E6DC567A4D93D42EEA9CDEE53D5E1C04FFF9CFECABCE7539FAC3AC01E063E`).
This proves the captured same-frame payload bridge from the compute-used
buffer to the sampled image. It does not establish which compute inputs
produced those bytes, the original title-side resource owner, or the
full-view image's semantic role. The
private diagnostic samples neither image, so visible alpha coverage and
the full-view pixel dependency remain unresolved.

The same RenderDoc probe now reads BC3 mip 0 at event 11206. Its 65,536
compressed bytes have SHA-256
`18F6CE118B46945A4C2A63F5EE8E6E242D08570C53E03ABB8C77B97F08556D48`.
Decoding the BC3 alpha selectors gives 37,353 zero-alpha texels, 5,663
255-alpha texels and 22,520 intermediate-alpha texels. The texture has no
recorded earlier use in this capture, so the replay does not establish its
upload or title-side payload generation. In the full-view image, byte 3 of
900,227 pixels is zero and of 21,373 pixels is 255; no intermediate value
occurs. These payload counts alone do not establish sampled channels or
discard behavior.

The captured pixel shader `ResourceId::975` disassembly (SHA-256
`C6935BE87C7176FCDA130D1C68436B8DA1AD6298C307FD893D995D99AA0EB1E5`)
and constant block 3 join descriptor indices 736 and 898 to those two images.
The first sample group reads four channels from index 736; the second reads
the first channel from index 898. The first group's alpha is multiplied by
interpolated `v4.w` and later reaches conditional `discard_z` and sample-mask
logic. The full-view image's byte-3 distribution therefore does not by
itself describe this draw's alpha test; its sampled first channel and the
shader constants need further comparison. This disassembly is the translated
DXBC shader for one matched draw, not a semantic material or all-variant proof.
Faithful coverage comparison still needs both current textures, the relevant
shader constants and the sampled depth state.

The expanded probe result is
`.local/native-renderer/snr04/vegetation-texture-shader-11206.json`
(SHA-256 `F2B8D2FD7DC6AEDB6CF5D53C9363DE09DEDF97B4EC7C78F1A328F7FF5B755600`)
with sibling `.dxbc.txt`.

Recheck the binding census and capture chain:

```powershell
python tools/verify-snr03-vegetation-binding.py `
  .local/native-renderer/snr04/renderdoc-extended-signal.log `
  --source-frame 6000 --require-texture-descriptors
$env:SNR04_CAPTURE = (Resolve-Path `
  .local/native-renderer/snr04/extended-capture_frame6000.rdc).Path
$env:SNR04_OUTPUT = (Join-Path (Get-Location) `
  '.local/native-renderer/snr04/vegetation-texture-shader-11206.json')
$env:SNR04_EVENT = '11206'
& .local/tools/renderdoc-1.46/RenderDoc_1.46_64/qrenderdoc.exe `
  --python tools/probe-snr04-vegetation-textures.py
```

The checked JSON has SHA-256
`2CE8E4D7E6C660C95B40733FB74C25C458AB9011CE30A6DA0713F45D026E49AC`.
