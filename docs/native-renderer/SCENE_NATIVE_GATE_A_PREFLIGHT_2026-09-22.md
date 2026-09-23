# Scene-native Gate A dependency and cost preflight

Status: read-only Gate A preflight, **not** an implementable SNR-05 cut or a
performance result. Compatibility remains authoritative.

## Measured budget

The two uncontended [SNR-00 controls](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#qualified-local-control)
had 20.066 and 20.060 ms frame medians on the saved sustained-race route.
At their 20.063 ms centre, Gate B's 15% threshold is **3.009 ms/frame**.
That is the required *net* improvement after native extraction, build,
upload, resource bridges and any retained compatibility work. The controls
are pilot noise evidence, not the final ABBA comparison.

The default-off GPU corpus and SNR-01 census ran together on the same 1×
route with executable SHA-256
`C9C57BD9B6030F7AAAE5B6C5486703565C0DED512EEE0A78D56F4DBDDB3EDEF5`.
It exited normally with seven captures. The local ordered log is
`.local/native-renderer/snr05/preflight-corpus-run-a.log` (SHA-256
`3EC4EF3BBCF21EDF87CF8029E63134E38D790D3B62C6681F833C458CF2951A0F`);
the repeatable summary is
`.local/native-renderer/snr05/preflight-corpus-run-a-summary.json` (SHA-256
`2DBF7320FE2BC06C2709FCF290087929F6520D07D751D275BE3A61D6573F9C1C`).
All ten emitted GPU timing-loss reports were zero.

The sampled backend-frame-6000 prepared draws map the two candidate target tuples to
attachment hashes `CF7DF63124BB2FAF` (`0x30000`) and `84241CB4C5BD3DC8`
(`0xC0000`). `tools/summarize-snr05-candidate-pass-cost.py` joins these to
the SDK's pass-family attachment labels, then sums timestamped pass samples
every 60 frames from 5400 through 6060. These labels are an **attachment
proxy**, not a title-view join on each sampled frame. They include work that
must remain, and a few families lack an emitted attachment label.

| Sampled GPU work, ms/frame | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| All timestamped passes | 7.037 | 9.374 | 12.519 |
| Mapped candidate attachments | 2.060 | 3.759 | 5.551 |
| Unmapped pass families | 0.011 | 0.058 | 0.126 |
| Backend preparation CPU summed over mapped candidate passes | 1.852 | 2.611 | 3.089 |

At frames 6000 and 6060, mapped candidate GPU work was 2.060 and 2.126 ms;
even assigning all unmapped pass time to the candidate gives 2.168 and
2.252 ms. Earlier sampled frames reached 5.551 ms, so cost varies along the
route. The 3.759 ms median is **not** removable time: it includes the retained
clear, resolves and other work on those attachments. Backend preparation CPU
is a different-thread sum that may overlap GPU execution and includes work
that native rendering may still need. Adding it to GPU milliseconds would
misstate the possible frame-time gain. Instrumented frame times are excluded
from the control comparison; one pass sample had a recording-wall outlier.
The mapped phase's median exceeds the 3.009 ms net target by only 0.750 ms
before accounting for retained GPU work or native draw cost. CPU-side savings
could change the result, but require a paired critical-path measurement.

Reproduce the calculation from the saved log:

```powershell
python tools/summarize-snr05-candidate-pass-cost.py `
  .local/native-renderer/snr05/preflight-corpus-run-a.log `
  --backend-frame 6000 --start-frame 5400 --end-frame 6060 `
  --target 14020500/00030000/00010400/00000003 `
  --target 14020500/000C0000/00010400/00000003 `
  --output .local/native-renderer/snr05/preflight-corpus-run-a-summary.json
```

To recapture, first verify the installed AppData preview contains a
`ForzaProfile/ForzaProfile` and no `pinyon_shift` process is running, then use
the repository launcher and the same route:

```powershell
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
.\tools\launch-preview.ps1 -Configuration RelWithDebInfo `
  -StateRoot $stateRoot `
  -RenderTestScript config/render-tests/fh1-race-sustained.fh1test `
  -RenderTestOutput .local/native-renderer/snr05/<run-id> `
  -RenderTestTimeoutSeconds 240 -Hidden `
  -GameArgumentsJson '["--pinyon_shift_fh1_gpu_corpus=true","--pinyon_shift_snr01_trace_source_frame=6000","--pinyon_shift_snr01_trace_following_frame=true"]' -Json
```

## Retained producers and unresolved bridges

| Work/resource | Evidence | Gate A treatment |
| --- | --- | --- |
| Scene-target clear | The exact candidate direct-root packet joins `sub_8240E130` in the [SNR-01 census](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#title-clear-producer-joins-the-candidate-scene-target-packet). | Retain as the scene color/depth prerequisite. Do not count its time as removable. |
| Preceding D24S8 and D32S8 depth phases | The [RenderDoc producer/consumer join](CPU_HOTSPOT_RESULTS_2026-09-21.md#renderdoc-race-frame-producer-and-consumer-join--2026-09-22) found 1,079 and 1,094 draws; both outputs feed later compute or pixel reads. | Retain until equivalent current depth is published for every consumer. |
| Reflection cube production and scene sampling | The [SNR-01 cube join](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#reflection-cube-consumers-and-the-separate-title-command-path) found 728 consumer draws in its bounded replay. | Retain reflected views and their publication/sampling path; the main-view cut cannot delete them by target similarity. |
| Selected vegetation pixel inputs | The [SNR-03 texture join](SCENE_NATIVE_SNR03_EVIDENCE_2026-09-22.md#selected-vegetation-texture-dependencies) finds five 256×256 slot-0 descriptors and one shared full-view slot-13 descriptor. At matched RenderDoc draw 11206, the full-view image byte-matches a 3,686,400-byte prefix of a buffer used by compute before the copy. The [capture-wide census](SCENE_NATIVE_SNR03_EVIDENCE_2026-09-22.md#capture-wide-vegetation-pixel-input-census) finds 54 two-texture draws and one shader; its BC3 alpha and interpolated alpha input feed discard/sample-mask, while the full-view sample feeds color. The [live binding join](SCENE_NATIVE_SNR03_EVIDENCE_2026-09-22.md#same-frame-final-pixel-descriptor-join) maps all 67 selected packets to five unsigned BC3 SRV indices and one shared full-view SRV index. | Bridge the five current BC3 resources for a bounded alpha-coverage diagnostic. Retain the full-view compute/copy publication for compatibility and any faithful color work; it is not removable based on this census. Copy from the guest command stream and order private sampling after its submission fence; the output callback precedes that submission. |
| Selected scene color/depth | The RenderDoc race frame found 2,579 scene-color draws and ten later pixel readers; the latest SNR-01 replay attributes its candidate attachment writers to view 8 or a retained clear. | A private diagnostic target is safe beside compatibility. Suppression would require an exact color/depth bridge and consumer order. |
| Post-processing and history | [PERF-10](PERFORMANCE_10_RESULTS_2026-09-21.md) proved partial updates, previous-frame reads, format aliases and alternating history. | Retain the chain; a latest-producer texture handoff is invalid. |
| 24 repeated point draws | The [SNR-01 write-state replay](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#exact-attachment-write-state-of-the-repeated-point-draws) found no attachment writes; query and other guest-visible effects remain unresolved. | Exclude from the diagnostic image slice, retain command execution. |
| Query, resolve and control side effects | [Guest-visible dependency evidence](GUEST_VISIBLE_RENDER_DEPENDENCIES.md#title-side-effect-boundaries) identifies query lifecycle and resolve event/memory/wait packets, but not all consumers. | Retain until exact consumers and synchronization are proved. |

This preflight does **not** reject the native scene approach: sampled candidate
GPU work is sometimes substantial, and title/backend CPU work may also be
replaceable. It rejects a savings claim based on draw counts or on the full
candidate pass duration. Continue the bounded same-frame diagnostic, then
measure extraction/build/upload and the required color/depth bridge. Before
SNR-10 suppression, replace these generous attachment estimates with a
pass/resource cut whose producers, consumers and removable work are exact.

## Exact view-8 ordering check

The later [session-bounded SNR-01 replay](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#process-bounded-replay-passes-the-full-candidate-boundary-census)
is a single backend frame, not another timing sample. Its strict ledger
accounts for all 2,705 candidate-target draws in backend frame 6001. The
title clear is ordinal 1634; the view-8 contribution spans ordinals
1635–4314, followed by 24 no-attachment-write point draws. The two color
words are used *within* this span, rather than forming two independently
composable passes.

| Joined source in this frame | Prepared draws | Color word(s) | Cut status |
| --- | ---: | --- | --- |
| View-8 scene lists with `CCarPresentation` / `CCarModel` owner | 636 / 431 | `000C0000` | Candidate, pending per-item geometry/material/lifetime |
| View-8 scene lists with one shared procedural state | 893 | 865 on `00030000`, 28 on `000C0000` | Candidate boundary only; per-list model/material ownership open |
| Character-manager direct records / procedural item-node packets | 261 / 170 | `000C0000` / `00030000` | Candidate, pending material/resource generations |
| Other semantic / scalar direct packets | 147 / 121 | `000C0000` / both | Mixed, cannot assign wholly to native slice |
| `CRealtimeSky` / `CStandardParticleRenderer` / race-line / view strip | 9 / 6 / 3 / 3 | Both / `000C0000` | Retain pending exact bridge and composition |
| Joined title clear / no-write indirect point draws | 1 / 24 | `00030000` | Retain; points have guest-visible effects to check |

The retained sky and presentation packets recur between candidate scene
lists: sky appears at ordinals 2028–2032, 3502–3506 and 4242–4246;
race-line at 2036, 3510 and 4250; particle at 2086–2087, 3741–3742 and
4312–4313; and the depth-tested view strip at 2088, 3743 and 4314. Later
scene-list and direct draws still write the same candidate attachments.
A single end-of-frame overlay cannot be assumed to preserve this ordering.
SNR-05 must prove the exact read/write/resolve dependencies and choose a
handoff or native replacement at each required point before any suppression.

The table is a draw provenance and ordering check, not a removable-cost
estimate: it provides no GPU duration per semantic family and does not
establish the untyped owner's material or the scalar packets' contents.
All 893 draws share one state pointer, first word `0xBF0C2E94`, and flush
return site `0x824170BC`. Its address equals the argument to the
`CProceduralModels` dispatch plus the title-code offset `0xE940` in this
frame. The 95 distinct list objects under that state still need exact
model, geometry and material joins; see the
[state provenance](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#shared-procedural-state-behind-the-largest-view-8-scene-list-family).
In a later strict replay, three `CTrackRenderModelInstance_Unified`
resources join three lists and 147 of 652 candidate prepared draws under
that state. The other 505 were not joined in that replay;
see the [bounded resource join](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#selected-track-model-instances-reach-three-bounded-scene-lists).
The subsequent [two-caller probe](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#both-shared-state-callers-reach-selected-track-model-resources)
resolves that family in a different sampled frame: all 856 state draws
join selected track-model-instance objects through 207 exact title
packets. The final-build repeat joins all 596 state draws through 154
packets in another frame. This narrows resource-object provenance; it
does not establish geometry, material, lifetime or a safe suppression
bridge.
Recompute it from
`.local/native-renderer/snr01/clear-complete-run-a-ledger.json` using
`classification`, `owner_first_word`, `title_packet_caller_lr`, `target`
and `ordinal`; the ledger's log SHA-256 is
`9BF6DC293F4D82B18064C6AC5FA3A9F82FCBC71BA0A9580CD17B089FFCC71953`.
