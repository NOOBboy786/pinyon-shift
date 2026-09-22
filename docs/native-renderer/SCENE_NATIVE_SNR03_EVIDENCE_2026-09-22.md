# Scene-native SNR-03 bounded publication evidence

Status: **metadata publication proved for one view-8 vegetation contribution;
SNR-03 and Gate A remain open.** This is not geometry ownership, resource
freshness, native rendering or a performance result. Compatibility output is
unchanged and remains the default.

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
valid only within one replay. The snapshot copies descriptor *addresses*,
not the referenced vertex bytes or a resource generation. It also has not
established the final per-item transform or material. Those fields must be
proven before a native diagnostic draw can consume the snapshot; this
metadata handoff alone does not close SNR-03 or SNR-04.

After adding explicit pending-scene cleanup on shutdown, the final
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
