# P2 dependency ranking: first race baseline

2026-09-07. P2 is in progress. The B848 native vertex replacement is retained
for its qualified 2x specialization; resource ownership remains open. P0 and
the remaining P1 qualification work are deferred.

## Reproduction and scope

Production DLL SHA-256:
`75521DA21DBAC16D95CA6C6F9E11640A5A601A393E86C6D4192044782A3863E4`.
Launched the installed AppData profile through `tools/launch-preview.ps1`, using
`config/render-tests/fh1-race.fh1test`, pass inventory enabled, and 2x/2x drawing
resolution. Session `20260907T201425Z-p40508` exited normally. The final screenshot
was inspected: active Recaro race, lap 1/2, place 8/8, car moving at 84 km/h.
This covers startup, menus, event entry and the start of a race, not a full lap
or the user's unidentified slowdown town.

Local evidence lives in `.local/native-renderer/p2/`: `race-runtime.log`,
`race-corpus.json`, `race-shader-ranking.json`, `race-pass-ranking.json`, the
session JSONL/performance CSV, and `race/` screenshots. Reproduce the coverage
ranking without launching the game:

```powershell
.local/toolchain/python-3.13.15/python.exe tools/rank-fh1-gpu-corpus.py .local/native-renderer/p2/race-corpus.json
```

The tool consumes one cumulative snapshot, groups draw entries by shader pair,
weights index counts by occurrence count, and retains every observed pipeline
identity. It rejects overflow, draw identity collisions and duplicate entries.
It does not infer native admission from shader hashes: admission also depends
on pipeline, modifications and configuration. Submitted indices are not unique
vertices, shaded pixels or GPU time.

## Baseline and coverage priorities

The corpus has 39,571 keys, 5,612 passes, zero overflow and zero draw identity
collisions. Its 7,463,731 draws equal the execution summary's 7,296,854 covered
in place plus 166,877 compatibility draws. Compatibility includes 165,602
uncaptured keys and 1,275 pipeline-not-prewarmed draws. Runtime translation was
zero; synchronous pipeline creation was **2**, not zero. Covered-in-place
execution does not mean every shader or resource is native.

Whole-session frame times (4,587 positive samples, including loading/menu
transitions): median 12.310 ms, p95 34.423 ms, p99 119.732 ms. These are a mixed
baseline, not steady racing performance or a before/after improvement.

These high-coverage pairs have no explicit native replacement admission in the
current D3D12 pipeline cache. Rank is by draw occurrences within this shortlist;
individual GPU cost remains unmeasured.

| Vertex / pixel shader | Draws | Submitted indices | Pipeline variants |
| --- | ---: | ---: | ---: |
| ED90DA6EFF5C6BCA / 57B9400F6B398736 | 303,581 | 147,337,422 | 3 |
| B8489164D5A86043 / 68150A8E959006CD | 291,590 | 300,829,062 | 1 |
| C1830DF50358E27D / 34DE4D8ECA877714 | 156,192 | 54,749,314 | 1 |
| C1830DF50358E27D / 7EB461BFAF59B34E | 139,189 | 93,616,252 | 1 |
| CC2F3F4B3FBA53F5 / CDA93D7ADC1991D8 | 136,723 | 32,950,814 | 1 |

Pass timing records describe spans containing mixed shader families. Their
first-draw shader cannot be credited with the entire span's cost. In particular,
the two-UV pair 984DBF6AF14DBEBD/6FDA0F1CDE67D12F leads some expensive spans but
accounts for only 33,311 draws and 1,598,928 indices in this corpus. C347/21B70
accounts for 51,758 draws and remains disabled pending its existing parity and
performance gates. Already-native layered, blended, lit, packed-world, depth
and shadow families also rank prominently; coverage alone is not a reason to
rewrite them again.

## Captured shader audit

Reused the historical 1x capture
`.local/native-renderer/p0-playtest/containment-rdc/frame_frame3034.rdc` to map
293 draws across the shortlisted vertex families. This capture was recorded
with the rejected geometry-cache experiment, so it is inspection material,
not a replacement qualification baseline for the current production renderer.
Disassembly, bindings and event identities are saved in
`p2/remaining-scene-audit/` alongside its replay script.

- ED90: 40 captured draws, representative event 28449, 48-byte post-VS stride,
  no depth target. This is a different attachment phase from the scene groups;
  do not label it world geometry based on the corpus alone.
- B848: 30 draws, representative event 11965, triangle list, 96-byte post-VS
  stride, scene color/depth targets. First scene replacement candidate to
  investigate because it combines broad coverage with one observed pipeline.
- C183: 181 draws across five pixel shaders, 144-byte post-VS stride. Qualifying
  a vertex replacement requires checking each pixel variant's inputs.
- CC2F: 42 draws, representative event 9359, triangle strip, 32-byte post-VS
  stride, scene color/depth targets.

The existing disabled two-UV HLSL compiled successfully with FXC vs_5_1. Replacing
its shader in that historical capture produced byte-identical post-VS buffers
for all seven matching draws (8,064 bytes total). They all use one shader
variant; render targets were **not** compared. Evidence:
`p2/world-uv2-original-parity/report.json`. This is insufficient to enable the
broad world-shader flag or claim visual parity, performance or dependency removal.

## Next qualification step

Capture the current production B848 scene at 2x, establish shader-specific cost
and resource/binding semantics, then compare a narrowly admitted replacement
against every matching draw's vertex and attachment outputs. Preserve topology,
guest-visible side effects and synchronization. Only retain the replacement
after representative live coverage and measured benefit or demonstrated
dependency removal without material regression. Resource ownership work remains
open; no shared-memory dependency was removed in this investigation.

Validation: `python -m unittest discover -s tools/tests -p test_rank_fh1_gpu_corpus.py`
passed; the real snapshot ranking reconciled exactly with execution totals.
The production DLL hash is unchanged and no test game was left running.

## B848 production-capture investigation

A new production 2x/2x race capture completed normally (game PID 37652):
`p2/production-rdc/frame_frame3758.rdc`. It contains 712 matching B848 draws.
Unlike the earlier inspection capture, it uses the retained production DLL.
Capture instrumentation makes this unsuitable as a live performance baseline.

The guest program fetches a 32-byte primary stream and a second stream of
12-byte packed transforms selected by vertex data. The transforms use signed
11/11/10-bit normalized fields, with separate fetch endianness. Ownership must
bound and preserve both streams; the single-stream scene import is insufficient.

A straight-line HLSL candidate is saved at `p2/fh1-skinned-scene.vs.hlsl`, with
its local generator `p2/write-skinned-scene.py`. FXC vs_5_1 compiled it to 18,560
bytes versus the captured translated shader's 25,392 bytes. This is not a
performance result. A fetch destination-swizzle error was corrected before
qualification; the first replay was stopped and superseded.

The corrected replay passed all 712 post-VS buffers, including all interpolators
and position: **10,099,584 byte-identical bytes**. A separate replay compared the
color and depth attachments at the first, middle and last matching draw: all six
comparisons passed, totaling **503,316,480 bytes**. This attachment sample is not
an every-draw attachment comparison. Reports are in
`p2/skinned-corrected-parity/` and `p2/skinned-attachment-parity/`.

The candidate is integrated through the existing standalone native-vertex path
for B848 modification `0x1F`, bindless host render targets, **2x/2x only**. It
retains the translated pixel shader and guest bindings. The compiled integrated
shader matches the replay-tested SHA-256
`B2BEB341EFB339A62A0A56779F18DB17348571DE0A1043D5D16E4124E847A61D`.
The production admission checks in `tools/check-fh1-shadow-mask.py` now also
exercise this gate, including alternate modifications, scales, binding modes,
render-target paths and single-bit hash changes. Checks and the DLL build passed.

A live race test completed normally with candidate DLL SHA-256
`1700386CF40F591702D38FFE0FBFDDA26867D41D6166E1055FB2F5BEB63AE12E`.
Its output is `p2/skinned-live-race/`, session `20260907T204948Z-p35664`.
The final screenshot was inspected: lap 1/2, place 8/8, 84 km/h. Car attachment
artifacts are visible in both this screenshot and the earlier production capture;
normal exit and this inspection do not establish whole-game visual correctness.
The execution summary reports 7,049,682 covered draws, 343,890 compatibility
draws (342,654 uncaptured keys, 1,236 not prewarmed), zero runtime translations
and two synchronous pipeline creations. It does not independently prove the
B848 native shader executed; verify the actual bound shader in a candidate
capture before counting runtime dependency removal.

`p2/skinned-investigation.json` records input hashes and completed test results.
The candidate DLL is preserved as `p2/skinned-candidate.dll`; both runtime and
artifact DLLs were restored to `p2/production-baseline.dll` after the smoke test.
That restoration was temporary; the subsequent qualification below retained
the candidate. Resource ownership remains open.

## Retained B848 native vertex specialization

The candidate capture `p2/skinned-rdc/frame_frame3823.rdc` completed normally.
`p2/skinned-bound-audit/report.json` maps 706 B848 draws to one pipeline and
verifies that its actual bound vertex shader has the replay-tested SHA-256.
This proves native-stage execution, rather than inferring it from broad
covered-in-place counters. The translated pixel stage remains.

A stationary open-world ABBA comparison used the same AppData profile, 2x/2x
resolution and `fh1-open-world-performance.fh1test`. All four runs completed;
recorded car positions agree within a millimeter. Frame/GPU metrics use the
last 12 seconds of render-test frames; process CPU/memory samples use elapsed
seconds 34-46. GPU duration is divided by its completed timing sample count.
Each run observed 35,697-37,203 B848 draws over the complete route.

| Metric | Baseline A1 / A2 | Candidate B1 / B2 | Change of means |
| --- | --- | --- | ---: |
| Median frame, ms | 20.772 / 21.118 | 20.815 / 20.939 | -0.33% |
| p95 frame, ms | 25.881 / 25.647 | 24.802 / 25.193 | -2.98% |
| Mean guest GPU, ms | 21.173 / 21.405 | 21.296 / 21.074 | -0.49% |
| CPU seconds / wall second | 3.131 / 3.196 | 3.033 / 3.183 | -1.75% |
| Private memory, MiB | 4759.45 / 4737.00 | 4773.67 / 4760.35 | +0.40% |
| Working set, MiB | 1988.87 / 1981.16 | 1989.21 / 1993.47 | +0.32% |

Draw counts differ by about 0.9%; p99 varies across baseline runs. This supports
no material regression in the tested scene, not a shader-level speedup claim.
All runs had zero runtime translations; synchronous pipeline creations were
0/0/0/1 in ABBA order. Compatibility draw counts vary substantially, so no
fallback-reduction claim is made. The measured stationary windows recorded zero
memexport, resolve readback and strict query-wait activity; they cannot qualify
replacement of those mechanisms.

Evidence: `p2/skinned-abba-{a1,b1,b2,a2}/` contains process samples and copied
session logs/CSV; `p2/skinned-abba-summary.json` contains metrics and captures.
The launcher and summary scripts are `p2/skinned-abba.ps1` and
`p2/summarize-skinned-abba.py`.

Retain the native vertex specialization based on full captured vertex parity,
sampled attachment parity, representative live coverage, proven native binding
and no material regression in the controlled stationary scene. Both runtime
and artifact DLLs now use candidate SHA-256 `1700386CF40F591702D38FFE0FBFDDA26867D41D6166E1055FB2F5BEB63AE12E`.
The baseline remains preserved for comparison. This removes the translated
B848 vertex stage for the admitted configuration, **not** its two shared-memory
streams, pixel shader or the overall Xenos renderer. Other scales are unqualified
and retain their existing paths. P2's remaining scene/cost ranking, shader/pass
coverage and resource ownership items remain open.

## B848 ownership bounds (implementation in progress)

`p2/inspect-skinned-ranges.py` inspected 14 draws distributed across the retained
native capture's 706 B848 draws. The primary stream is 32 bytes per vertex;
both transform indices are unsigned bytes plus guest c156.x. The palette fetch
is physical slot 94 (primary: 95). Its declared buffer is 2,487,252 bytes;
observed per-draw transform spans are only 180-228 bytes. Captured inputs and
the report are in `p2/skinned-ranges/`.

`skinned_transform_range` in the existing `fh1_geometry.h` conservatively bounds
all 256 possible byte indices, allowing about 3 KiB rather than importing the
entire buffer. It returns a slice starting at the first possible transform and
rejects invalid constants, signed conversion overflow, fetch overrun and
physical-memory overrun. Primary stream/index qualification will reuse
`depth_geometry_range`. `tools/check-fh1-skinned-geometry.py` passes with the 14
captured fixtures and exercises all byte values, multiple CPU rounding modes
and unsigned address rebasing. This is a bounds proof, **not active ownership**.

Next integration must preserve the pixel descriptor-index slot and texture heaps,
reuse the unused vertex descriptor-index slot for a second raw vertex SRV, and
rebase the palette fetch to the imported slice without changing c156 arithmetic.
The existing cache still allocates 64 KiB windows. Import coherence must also
invalidate slot 94 alongside the existing owned slots, and ownership must revert
all inputs together when qualification/import fails. The runtime remains the
retained native-vertex DLL; no ownership candidate has been staged yet.

### Ownership candidate integration

The candidate now binds an owned primary stream and a separate owned transform
slice. A skinned root signature preserves pixel descriptor indices and texture
heaps. Fetch rebasing uses unsigned address arithmetic without changing c156;
changes in the imported palette origin invalidate the fetch constant buffer.
Slot 94 participates in CPU-import residency invalidation. Primary index bounds
are rechecked after palette imports, and failed qualification drops both owned
streams and the owned index binding together.

Candidate DLL SHA-256:
`057C10D85C8E9F61FEAE7E6CB902C91CFFF6F2A8D59263B61A74E60A1DD8159D`.
It built and completed a live race capture normally (PID 5636), saved as
`p2/skinned-owned-rdc/frame_frame3627.rdc`. The previous retained native-vertex
DLL was restored to both runtime and artifact paths afterward. Source integration
remains provisional pending ownership qualification and regression checks.

All 14 sample observations (13 distinct draws) in
`p2/skinned-owned-inputs/report.json` bind owned mesh and
transform resources; the compared primary range and referenced transform span
match guest GPU memory byte for byte. The all-draw audit is running via
`p2/inspect-skinned-owned-inputs-all.py`, output `p2/skinned-owned-inputs-all/`.
This input comparison does not yet establish complete rendered-output parity.
Remaining gates include output validation, mutation/coverage evidence and a
controlled regression comparison against the retained native-vertex baseline.

Checks passed: `check-fh1-skinned-geometry.py` with the 14 captured fixtures,
`check-fh1-depth-geometry.py`, `check-fh1-depth-indices.py`, and
`check-fh1-geometry-cache.py`, using the local LLVM 20.1.8 compiler. The existing
harnesses were extended for the new root, slot 94, rebasing and origin changes;
initial missing-mock compile failures were corrected before these passing runs.

### Ownership qualification results (candidate still provisional)

The all-draw input audit completed: **625 draws**, 37,361,524 compared bytes,
all equal. **616 draws** bind both owned resources; **nine** bind shared memory
for both. No mixed owned/shared pair was observed. This proves input equivalence
in the captured frame, not zero fallback or universal mutation coverage.

`p2/skinned-owned-output-parity/report.json` passed three post-VS comparisons and
six color/depth comparisons. Its reference uses the previously validated vertex
arithmetic with only input reads adapted to the captured two-SRV layout and
without the ownership shader's bounds guards. The independent guest-versus-owned
byte audit and CPU address-rebasing checks validate those input adaptations;
this is not a comparison between independently recorded live frames.

`p2/skinned-owned-abba-summary.json` records four normal stationary runs against
the retained shader-only baseline. Change of means: median frame **+0.07%**,
p95 **-1.33%**, guest GPU **-1.07%**, CPU seconds/wall second **+3.66%**, private
memory **+0.38%**, working set **+0.61%**. Draw counts differ by **-1.62%** and
baseline p99 varies, so do not claim a shader speedup. Frame-time behavior is
similar; the CPU increase warrants investigation before retaining ownership.
Both staged DLLs remain the retained shader-only baseline `1700386C...`.

The nine fallback draws all bind the shared buffer as their index source and
have the same 56,576-byte primary extent. Their captured indices and transform
indices fit the declared buffers. `p2/skinned-fallback-audit/report.json` records
their event IDs and bindings. The runtime reason for refusing ownership is not
yet established; do not classify them as unsupported topology or a cache-budget
failure based on these observations alone.

Next: identify the fallback reason, investigate redundant range checks/import
cost, and rerun the affected regression/qualification checks if the candidate
changes. The bounds test now also executes the production all-or-nothing branch
under missing snapshots, palette rejection, import failure and aliased snapshot
changes. P2 remains incomplete.

### Cache-hit bounds recheck

Diagnostic race session `20260907T213228Z-p528` exited normally. Its capped
logging recorded four refused skinned index imports with the geometry cache at
33,554,432 bytes (`p2/skinned-diagnostic-fallback.log`). No missing-snapshot or
rejected-bounds diagnostic fired. These were different index ranges from the
nine captured fallback draws, so their exact runtime cause remains unconfirmed.
The temporary logging was removed after the run.

The palette import now follows the existing primary-import rule: repeat bounds
validation only after a successful import changes the import counter. Cache hits
cannot replace the immutable index snapshot. The production-branch check covers
cache hits, changed snapshots, failed imports and invalid bounds, and asserts
that hits skip the second lookup. The geometry-cache and index-fallback checks
also pass. No shader arithmetic or resource layout changed in this refinement.

Refined candidate DLL SHA-256:
`DEC57269B840A575F3C0B70561DC53E04B4D75C04CDBF739186EBD1B1945F208`.
Its controlled comparison is recorded in `p2/skinned-owned-fast-abba-summary.json`.

All four runs exited normally, with the same stationary vehicle position to
within millimeters. The refined candidate **failed the retention gate**:
mean median-frame change **+15.32%**, p95 **+15.77%**, guest GPU **+12.95%**,
CPU seconds/wall second **+9.09%**, private memory **+0.26%**, working set
**+0.31%**. Draw count changed **+4.56%**. Candidate run B2 was notably slower
than B1 (25.440 versus 20.625 ms median); the two baselines were 20.409 and
19.537 ms. This is insufficient evidence of no material regression, even though
the first candidate run was close to baseline. Do not attribute the whole
difference to the bounds recheck or claim its removal improved performance.

Skinned geometry admission is now explicitly disabled in the pipeline cache.
The qualified native vertex shader continues using its original shared bindings.
The ownership implementation and checks remain available for investigation;
neither input parity nor 616/625 owned draws overrides the performance gate.
The rebuilt disabled-candidate DLL is
`513AD56D1829DF9D0419CA0ABA165D0CC42E6F3F647EAABC81E0252BB18E24C0`.
Next: measure the import/cache cost on matched workloads before retrying
ownership; continue the missing scene/cost ranking and texture/resolve/query
dependency work. C347/21B70 and the two-UV candidate remain disabled.

The disabled-candidate build passed the stationary AppData smoke run (PID 21232,
normal exit). Its JSONL, performance CSV and captures are preserved under
`p2/skinned-owned-disabled-smoke/`; runtime and artifact DLL hashes match the
disabled build above. The admission check asserts that ownership stays disabled
until the performance gate is deliberately revisited. Root/SDK diff checks pass.

## Expanded scene coverage (2026-09-07)

The retained `513AD56D...` build completed the animated-title script with opening
movies enabled (`20260907T214408Z-p31912`) and the short straight-driving probe
(`20260907T214521Z-p41464`). Both exited normally. The title's 60-second capture
was visually checked: full Ferrari/forest animated title, logo and Press Start,
not the flat movie-skip background. The driving capture at 33 seconds shows
53 km/h **against the roadside barrier**. It supplies moving-scene coverage,
not a clean driving-performance route or reproduction of the slowdown town.

Evidence: `p2/scene-title/`, `p2/scene-driving/`, `p2/scene-summary.json`.
`p2/measure-scenes.ps1` launches through the existing preview helper and records
process samples without modifying saves. `p2/summarize-scenes.py` reuses the
corpus ranker, deduplicates repeated log lines, and keeps the final cumulative
timing record per family. Each folder retains its corpus, shader/pass rankings,
session logs, CSV and images. Corpus draw totals reconcile with execution totals;
the ranker rejects overflow and collisions.

| Observed window | Median / p95 / p99 frame ms | Guest GPU ms | CPU s/wall s | Private / working MiB |
| --- | ---: | ---: | ---: | ---: |
| Animated title, final 12 seconds | 8.450 / 10.515 / 11.249 | 5.774 | 1.716 | 2962 / 1582 |
| Driving probe, final 7 seconds | 21.082 / 27.244 / 158.242 | 23.163 | 3.453 | 4697 / 1968 |

These are single-run observations. Windows use accumulated positive frame times;
CPU/memory windows use process age with an approximately two-second startup
offset, recorded explicitly in JSON. The driving script takes five synchronous
screenshots during the measured interval, so its 158 ms p99 is **not** a clean
renderer tail measurement. Use sparse captures outside the next measurement
window and a corrected route before qualifying driving frame pacing.

Whole-session compatibility was **28.449% of 619,213 title draws** and **15.865%
of 2,161,370 driving-session draws**. Those percentages include startup and
transitions; they are execution-key fallback, not native-shader or owned-resource
fallback rates. The selected windows recorded zero memexport, resolve-readback
and ZPD activity. This does not qualify query-dependent modes or remove their
guest-visible contracts.

The title corpus's largest pair is B6C9863F710683EC/no-PS (362,592 draws), already
recognized by existing native admission. ED90/57B9 contributes 78,560 title draws
and 95,473 driving-session draws; its earlier rejected replacement remains
relevant. Do not prioritize an already-native family solely by occurrence count.

The largest **sampled cumulative** title pass is `8ADB81E88C6263DA`, exact first
draw `2228A58AD7354DC3`, pair `7156CE05C6365E51/31511D87CC0C94B9`, pipeline
`74B86629C3A0D7C8`: 122 samples, one draw, 0.478 ms average, comprising 0.403 ms
draw and 0.075 ms resolve. It includes the opening sequence; do not attribute
that cost to the final animated-title window. The one-draw `3AE7C526208A0E61`
averages 0.380 ms (64 title samples) and 0.386 ms (35 driving-session samples),
but its 1E6883/A4A965 pair already has native admission. The two-draw
`C139B948D0ACD681` span averages 0.376/0.354 ms; first pair 20A41D/9AAEF9.
Costs are per sampled pass occurrence, not complete frame totals or cost
attributable to every first-draw shader. The individual shader-cost ranking,
clean driving route, slowdown town and remaining resource work are still open.

### Driving window without screenshot overhead

Session `20260907T214908Z-p32644` exited normally on the retained DLL. The local
`p2/driving-clean.fh1test` preserves the existing inputs, takes only one image at
31 seconds, and stops at 32 seconds. The measurement uses accumulated frame-time
seconds **26.022 through 30.022**, before that image. The inspected final capture
shows the car on the road at **83 km/h**, before the later barrier contact.
This is a four-second accelerating probe, not a complete driving route.

199 measured frames: median **20.046 ms**, p95 **24.268 ms**, p99 **26.524 ms**;
guest GPU **19.410 ms**. Approximate process-age sampling records **4.008 CPU
seconds/wall second**, **4697 MiB private** and **1950 MiB working set**; the
two-second process/window alignment approximation remains explicit in JSON.
Whole-session execution compatibility is **5.124% of 1,979,902 draws**, including
100,731 uncaptured keys and 712 non-prewarmed pipelines. Runtime translations
were zero and synchronous pipeline creations were **one**, not zero.
Selected-window memexport/readback/ZPD activity was zero.

Evidence: `p2/scene-driving-clean/`, the updated `p2/scene-summary.json`, and
`p2/measure-driving-clean.ps1`. The original longer probe's 158 ms p99 must not
be compared as an optimization gain: both the measurement interval and capture
schedule changed. No renderer code or admission changed for these measurements.

### Post-processing capture audit

The production race capture `p2/production-rdc/frame_frame3758.rdc` was audited
after the live run ended, reusing the existing structured-command mapper.
`p2/remaining-postprocess-audit/report.json` maps two draws (40420 and 40448) to
VS **20A41D46F34D238E**, but PS **614588022744BF6B**, not the timed span's first
PS 9AAEF9B81D19D203. One representative pipeline emits three vertices with a
64-byte post-VS stride, no depth target and one color target. Shader bytecode
and disassembly are saved beside the report. The vertex stage contains explicit
LOD texture sampling; it is not a position-only fullscreen substitution. Its
308 disassembled instructions and the pixel stage's 1537 instructions are static
counts, not measured GPU costs. The 7156CE/31511D pair is absent from this race
frame. Next qualify the actual desired pixel variant and its resource/constant
contract before implementing or admitting a post-processing replacement.

### Post-processing input contract

`p2/postprocess-contract/report.json` now records both captured 20A41D/614588
draws and saves their complete bound constant buffers. Pixel buffers b0/b1/b3/b4
are 480/256/768/64 bytes; vertex buffers are 480/176/768/16 bytes. Both draws
have the same system flags and descriptor indices, but their float constants
and full fetch buffers differ. A replacement must preserve those live values;
one hard-coded captured constant set would not cover even this frame.

`p2/postprocess-contract/decoded-bindings.json` records the sampled fetches
0, 2, 5 and 7, unsigned texture-sign fields, and scaled-texture mask `0x20025`.
The original 614588 microcode samples tf5, six tf0 locations (linear and point),
tf2 and a 3D tf7 lookup, then performs depth-sensitive sample selection, color
conversion and output square roots. The vertex shader also samples tf17.
Thus replacing only the fullscreen vertex position, or dropping 3D texture and
scaled-fetch semantics, would not replace this pass correctly. Existing native
2D texture helpers cover only part of that contract; no new shader is admitted.

The replay script initially used an unavailable reflection attribute and reported
an error. That extraction was corrected and rerun; the final report contains
both draws and no error, with all expected constant-buffer byte counts checked.
The next capture targets the animated title's 9AAEF9 variant, not a relabeled
614588 race draw. The retained runtime remains `513AD56D...`.

The fresh title capture succeeded and the game exited normally (PID 12260).
`p2/postprocess-title-rdc/frame_frame9771.rdc` contains **both desired pairs**:
event 1784 is 7156CE/31511D (four-vertex triangle strip, 32-byte post-VS stride),
and events 1875/1903 are 20A41D/9AAEF9 (three-vertex triangle lists, 64-byte
stride). `p2/title-postprocess-audit/report.json` verifies the actual bound
pipeline names; shader bytecode and disassembly are saved beside it. The
capture controller reports completion and the session JSONL is preserved in
`p2/postprocess-title-test/`. No GPU replay overlapped live measurement.
This supplies the missing production reference for the next pixel replacement;
it is not yet replacement parity, performance qualification or dependency removal.

## Experimental 31511D pixel replacement

`fh1_video_color.ps.hlsl` now implements the three-plane sampling and exact
31511D color-conversion sequence, including guest Boolean b128, zero-product
handling, sequential dot accumulation, alpha testing, coverage and output scale.
It reuses the existing native texture/sign/coverage helper pattern. Pixel-only
replacement keeps the original vertex program, root signature, resources and
fixed-function state. Admission is **disabled** pending further qualification;
the pipeline-creation fallback includes this candidate.

The gate restricts the exact 7156CE/31511D pair, both modifications **1**, bindless
host render targets and 2x/2x drawing. The captured original pixel bytecode SHA
`156262FD2820189AEB2F7688E7CB182E38EE8EAC9B20BCC02ADE9E774DD570BC`
matches the modification-1 dump, not its early-depth 0x400000000001 sibling.
`tools/check-fh1-video-pixel.py` compiles the production predicate, exercises
hash/modification bit changes and scale/path exclusions, and checks the disabled
and creation-fallback guards. It passes, as does the renderer build.

`p2/video-pixel-parity/report.json` reports exact equality for **83,886,080 color
attachment bytes** at title event 1784; the unchanged 128 post-VS bytes also
match. Final candidate DXBC SHA-256:
`3963ED1EA7F9A6A2C09B8F9B67ECC2F5E0CBF3DF8097F58CA5AE4099168F8771`.
The initial candidate passed too; after removing unused helper code and making
the alpha predicate explicit, the comparison was rerun and still passed.
FXC reports approximately 373 instruction slots versus the original disassembly's
452 instructions. Those counts are not a measured speedup.

FXC's potentially-uninitialized `AlphaTest` warning remains unresolved. Do not
enable based on this single-frame image comparison: additional movie/title
states, Boolean branches, alpha/coverage behavior, actual live native binding
and controlled performance remain to be qualified. Local construction/replay
scripts are `p2/write-video-pixel.py` and `p2/video-pixel-parity.py`. Both staged
DLLs remain the retained `513AD56D...` build, not the experimental pixel shader.

### Warning resolved and live native binding verified

The early-return alpha helper caused FXC's initialization warning. Rewriting it
with one return preserves the comparison logic and compiles with **/WX**.
The production-helper check now tests every comparison mode against finite
values, signed zero, infinities and NaNs, including not-equal behavior. It passes.
Pixel parity was rerun: the same 83,886,080 attachment bytes still match exactly.
Updated pixel DXBC SHA:
`96AB627264DD5DE29C18E8DBB0CC83DF44C47C44E7C0872D6271673760742CC4`.

An isolated enabled candidate DLL
`68CFD66A5BF3E2788779037EE507A2E3D43EDDEC7BE09FD3CC5DE0EC78E9223A`
completed the title capture normally (PID 32632). At event 1781 in
`p2/video-candidate-rdc/frame_frame10211.rdc`, the actual bound pixel shader has
the exact candidate hash above. `p2/video-bound-audit/` saves that shader and
pipeline mapping. This proves live native pixel binding rather than merely
counting the original shader-pair identity. Both original post-process draws
remain present. Production source admission stays disabled.

The controlled title ABBA comparison is now running via `p2/video-abba.ps1`
(terminal session 76314 at this checkpoint). It uses the retained `513AD56D...`
DLL as A and `68CFD66A...` as B, and restores the retained binary when finished.
Use `p2/summarize-video-abba.py` only as results arrive; it measures the final
12 seconds and process samples at ages 55-67 seconds. Do not claim performance
qualification until all four runs and their scene/coverage evidence are checked.

### Retained video pixel stage

The ABBA comparison completed with four normal exits. Change of means:
median frame **+0.175%**, p95 **-0.540%**, p99 **-0.520%**, guest GPU
**-1.933%**, CPU seconds/wall second **+0.062%**, private memory **+0.102%**,
working set **+0.109%**. Draw count changed **-0.0015%**. This supports dependency
removal without material regression in the animated-title window; it is not a
general gameplay speedup. Detailed runs, coverage and counters are in
`p2/video-abba-summary.json`.

The exact 2x video-pixel gate is now **enabled**. Build and admission/alpha checks
pass. The rebuilt runtime and artifact DLL both match the qualified candidate:
`68CFD66A5BF3E2788779037EE507A2E3D43EDDEC7BE09FD3CC5DE0EC78E9223A`.
An additional opening-FMV run (PID 13532) exited normally with all three scripted
captures; the final image was inspected and shows the opening dashboard movie.
Evidence is `p2/video-retained-fmv/`. The prior retained DLL is preserved at
`p2/skinned-owned-disabled.dll`. B848 geometry ownership remains disabled, while
its earlier native vertex stage remains enabled. No commit/push/release occurred.

Next resource target: the video draw's three captured planes are non-tiled R8,
unsigned, no endian swap: 1280x720 with 1280-byte pitch and two 640x360 planes
with 768-byte pitch. `p2/video-texture-contract/` preserves the actual constants.
The existing texture-load lifecycle arms its watch before CPU loading and
`CopyCpuRange` rejects GPU-written pages. Investigate direct upload into the
existing D3D12 textures when guest and host row layouts match; preserve the
ordinary path for unsupported layouts and GPU-written ranges. This native
resource import has **not** been implemented or qualified yet.

### Linear video upload implementation (disabled)

The D3D12 texture cache now has a separate video request path, selected only by
the exact 7156CE/31511D pair and currently **disabled** in the command processor.
It accepts a single base-only, non-array, non-tiled R8 texture without endian
conversion or scaled resolve. It asks D3D12 for the actual copy footprint and
requires matching guest/host row pitch, zero footprint origin and a nonempty
guest data extent fitting the allocation. It then copies CPU-owned bytes directly
into the existing upload pool and issues CopyTextureRegion into the existing
native texture. No second texture cache, memory-watch system or row-repacking
buffer was added. Other layouts and GPU-written pages use the existing path.

`tools/check-fh1-video-upload.py` executes the production block with matching
luma/chroma layouts and rejected format, layout, mip, array, allocation and
CPU-ownership cases, asserting that failures issue no GPU copy/state mutation.
The existing `check-fh1-texture-watch.py` also passes its load-race/partial-load/
retry cases. The renderer builds. Initial compile errors from using a shader-
translation accessor on a shader object and a missing const mock qualifier were
fixed before these passing checks.

This is implementation evidence only: direct-upload live binding, input/output
parity, mutation coverage and performance are still required before enabling it.
Both staged DLLs remain the retained video-pixel build `68CFD66A...`.
Next build an isolated enabled upload candidate, capture its actual texture-copy
sources and compare all three native planes with the guest bytes and original
rendered output. Then measure against the retained pixel-only build.

### Live video upload and byte checks

Enabled upload candidate DLL:
`CBB5F4773E2B7F99944FCF4ACFD37B367A194789E730FB5BCC6EC72FBC8D7E65`.
The title run exited normally (PID 45672), producing
`p2/video-upload-rdc/frame_frame10397.rdc`. At video draw 1757, all three R8
planes are copied from buffer 2663. Its captured creation uses heap type **2
(UPLOAD)**, and its resource usage includes CPUWrite and CopySrc, with no GPU
write usage. Copy events 1737/1739/1741 bind the expected 1280/768/768 row pitches
and upload offsets 0/921600/1198080. This verifies actual direct upload rather
than inferring ownership from the shader hash or texture name.

`p2/video-upload-audit/report.json` records **1,382,400 matching bytes** after
removing upload row padding: luma 921,600 and each chroma plane 230,400. The
bound texture contents equal their CPU-writable upload-buffer contents exactly.
This verifies the upload transfer; it is not a comparison against a separately
recorded movie frame, whose decoded pixels would differ with timing.

`p2/video-upload-output-parity/report.json` then replaces the retained native
pixel program with the captured original modification-1 bytecode on those same
inputs: **83,886,080 attachment bytes** and the unchanged 128 post-VS bytes
match. The existing load-watch/failure checks establish the relevant CPU-side
fallback and invalidation behavior; broader live mutation coverage remains a
qualification limit. Source admission stays disabled during testing.

The upload ABBA comparison completed through `p2/video-upload-abba.ps1`:
all four runs exited normally (A1 PID 9440, B1 PID 25168, B2 PID 47932,
A2 PID 48248). A is retained pixel-only `68CFD66A...`; B is upload candidate
`CBB5F477...`. `p2/video-upload-abba-summary.json` records the final 12 seconds
of each animated-title run and process samples at ages 55-67 seconds.
No GPU replay overlapped the benchmark.

Relative to A, B measured median frame time **+0.09%**, p95 **+0.42%**,
p99 **+1.43%**, GPU time **+0.72%**, CPU usage **-5.24%**, private memory
**-0.84%**, and working set **-0.32%**. Draw counts were effectively unchanged.
Each run recorded three captures and roughly 11,200 video draws over the whole
session, zero runtime shader translations and one synchronous pipeline creation.
Selected windows recorded no memexport, resolve-readback or ZPD activity; this
does not qualify those unexercised side effects. This small title comparison
supports a CPU reduction without a large frame-time change, not a gameplay FPS
claim or a statistical guarantee.

Both staged DLLs were verified restored to `68CFD66A...`, and no game remained
running. Direct-upload source admission remains disabled pending final visual
review and broader live movie mutation coverage. The native video pixel stage
remains enabled. P2 is incomplete.

The user cannot remember the slowdown town's name. Keep its coverage explicitly
unidentified; do not substitute a nearby road or treat this as blocking the
remaining independent P2 work.

## Performance-first P2.1: repeated resolution baseline

The retained `68CFD66A...` renderer completed four normal AppData runs in
1x/2x/2x/1x order: PIDs 35180, 30984, 43580 and 47356. No renderer source,
admission or binary changed. Reused `driving-clean.fh1test`; the single screenshot
at 31 seconds follows the measured accumulated frame-time window at approximately
26-30 seconds. All four images were inspected: active driving, 83-84 km/h, on the
same road before barrier contact. Final player positions differ by at most about
0.73 m; traffic differs visibly, so workloads are similar, not identical.

| Metric | 1x A / B | 2x A / B |
| --- | ---: | ---: |
| Median frame, ms | 20.637 / 20.190 | 21.834 / 21.285 |
| p95 frame, ms | 26.901 / 24.506 | 28.249 / 28.654 |
| p99 frame, ms | 30.452 / 27.183 | 34.304 / 37.589 |
| Guest GPU, ms | 18.695 / 17.502 | 21.485 / 21.792 |
| CPU seconds / wall second | 4.302 / 3.974 | 3.948 / 3.954 |
| Private memory, MiB | 2514 / 2511 | 4691 / 4704 |
| Working set, MiB | 1949 / 1956 | 1956 / 1967 |

Change of means for 1x relative to 2x: median -5.31%, p95 -9.66%, p99 -19.83%,
GPU -16.36%, CPU +4.72%, private memory -46.51%, working set -0.45%. These short
windows contain 177-199 frames each, with approximate process-age alignment
(+2 seconds), varying traffic and fallback coverage. They establish a repeated
resolution baseline, not statistical certainty or a particular shader speedup.
Private memory is process commit, not a measured VRAM reduction. Lower resolution
helps memory substantially here but does not eliminate the frame-time cost;
this alone does not identify whether remaining cost is CPU work, GPU work or waits.

All runs recorded zero runtime translations and one synchronous pipeline creation.
Whole-session compatibility percentages were 7.405/8.804/9.068/2.189 in run order;
these include transitions and do not measure native-resource fallback. Selected
windows recorded zero memexport/readback/ZPD activity, leaving those contracts
unqualified. B848/video native gates remain 2x-only: successful 1x gameplay uses
the existing admitted/fallback paths and does not qualify those new shaders at 1x.

Evidence: `.local/native-renderer/p2/scene-scale-{1x-a,2x-a,2x-b,1x-b}/` contains
captures, session logs, performance CSV, process samples, corpus and rankings.
`measure-gameplay-scales.ps1` and `summarize-gameplay-scales.py` reuse the prior
measurement helpers; `gameplay-scales-summary.json` records the window definitions
and reconciled corpus/execution totals. Both DLL paths remain `68CFD66A...` and
no game remains running.

Profiler inspection found that `ObserveFh1GpuPassTimingDraw` samples every 60
frames, while `LogFh1GpuPassTimings` emits cumulative family totals every 600
host frames and on shutdown. This cannot precisely attribute the selected
four-second window or reconstruct complete per-frame post-process cost. Next
retain frame identity for sampled pass records and expose their draw/resolve
costs through the existing diagnostic path, then rank a bounded gameplay window
before changing 20A41D/614588. Keep profiling runs separate from performance
qualification if added logging perturbs timing. P2.1 and the full goal remain open.

### Gameplay-window pass samples

The existing corpus-only GPU timing path now preserves source-frame identity
in each pass record and logs its submission/record ID, family, first draw,
draw count and total/draw/resolve nanoseconds when the fence retires. It adds
no queries and changes no rendering admission. Normal runs with corpus disabled
do not collect these records. The diagnostic DLL built successfully:
`F181769D128A8B08BD100340283E87EE2C7C0E7F0EB14CEC8E52E713CB76BF92`.

`tools/rank-fh1-pass-samples.py` ranks one session's selected frame range,
deduplicates repeated log records, rejects conflicting identities and divides
family totals by all observed sampled frames (including frames where that family
is absent). Its `--self-test` passes. Renderer build and root/SDK diff checks pass;
the build still emits existing compiler warnings. This is diagnostic logging,
not a performance improvement; retain uninstrumented benchmarks for comparisons.

A 2x driving run with this DLL exited normally, PID 40176, session
`20260907T225102Z-p40176`. The final image was inspected: on-road driving at
83 km/h. Both runtime and artifact DLLs were restored to `68CFD66A...` afterward.
Evidence: `p2/scene-scale-2x-pass-samples/`, `p2/measure-pass-samples.ps1` and
`p2/rank-gameplay-window.py`. The ranker's report is `window-pass-ranking.json`.

The 26-30 second CSV window corresponds to source frames 2854-3048: CSV rows
are emitted by `Profiler::Flip` at CP swaps, with `observation_frame_sequence_`
incremented after the swap. Sampled frames 2880/2940/3000 contain 480 valid
pass records. The last cumulative diagnostic reports zero dropped samples.
Observed spans sum to **12.245 ms per sampled frame**; this excludes GPU work
outside those spans and is not a complete GPU-frame cost or CPU attribution.
Only three frames are sampled, so the ranking remains provisional.

Selected span-family costs (ms per sampled frame):

| Family | First shader pair (identifies the span, not all its work) | Cost |
| --- | --- | ---: |
| 8F17E2B502A6BF62 | A3B9ED5D5C87230E / 93626E75D17576C5 | 0.960 |
| 18327EF50B68D9C4 | C34795A841E7DEFF / 21B70A5E4C9CFD11 | 0.803 |
| ED7F805DBDC5C236 | 1E6883FCCDE1F688 / no PS | 0.777 |
| 7C6A3248DE68D142 | 984DBF6AF14DBEBD / 6FDA0F1CDE67D12F | 0.658 |
| 6A19B1025E8B8640 | CA293E0A1CB4B416 / no PS | 0.574 |

Grouping all spans that begin with 20A41D/614588 gives **0.355 ms per sampled
frame**, across changing family identities. Several other span groups cost more.
Do not treat these first-pair groupings as shader-level timing: for example,
C347's listed span includes 442 draws over three frames, potentially mixed.
The post-process experiment should stay bounded; even eliminating its observed
span entirely would save only about 0.355 ms in this sample. No candidate is
newly enabled. Next inspect the expensive spans' actual capture contents and
isolate one post-process simplification, while broader cost/1x qualification
and the remaining P2 items stay open.

### P2.2 offline center-sample post-process experiment

An offline HLSL prototype replaces 614588's neighboring scene-color samples with
one center sample while retaining live exposure, the 3D color lookup and final
color transforms. It removes the velocity/noise-driven sampling from this pixel
stage; it does not remove their upstream producers or resources. The prototype
currently assumes unsigned 2D inputs and a true 3D LUT, as recorded in this
capture. It has **no runtime admission** and is not a general implementation of
all fetch modes. Both prototype shaders compile with FXC ps_5_1 /O3 /WX.

Files under `.local/native-renderer/p2/`: `fh1-postprocess-center.ps.hlsl`,
`fh1-postprocess-center.dxbc`, `postprocess-center-replay.py` and its report/images
in `postprocess-center-replay/`. Center candidate DXBC SHA-256:
`F9AE4BB2654C8982A3A08BD61671F4ED2D364A9FA2EBD7A9C5C7012769A5A591`.
The original captured 614588 bytecode SHA-256 is
`B113835DD8F5A78AFB6E6771D50B26B38081599ED4E237A63F3B000D9F4B5AF7`.

Pixel replacement succeeded at both production-race events 40420/40448. Both
192-byte post-VS buffers remain exact; rendered color differs, as expected.
The second draw's original/candidate images were visually inspected and appear
close. `measure-postprocess-images.py` uses the bundled Pillow/NumPy runtime to
compare the active 2560x1440 RGB viewport, excluding unused target padding:

| Event | Mean absolute channel error (0-255) | RMS error | Pixels with any channel error >8 |
| --- | ---: | ---: | ---: |
| 40420 | 0.00498 | 0.12059 | 0.00453% |
| 40448 | 0.01047 | 0.16774 | 0.01001% |

The maximum channel error is 60, despite the small average. These are PNG image
metrics in one captured frame, not a numerical "accuracy percentage", proof of
motion quality, or universal acceptance. Details: `postprocess-visual-metrics.json`.

A separate full-sampling control prototype (`fh1-postprocess-full.ps.hlsl`,
`postprocess-full-replay/`) currently differs more: MAE 1.485/3.062 for the two
draws. Its sampling reconstruction is unvalidated; do not use it as evidence
that every center-candidate difference has been isolated to the intended blur
change. The initial control compile used HLSL's reserved `point` identifier;
renaming it to `centerSample` fixed compilation before the completed replay.

A RenderDoc EventGPUDuration attempt returned no per-draw timings and then
rejected shader replacement as unsupported. `postprocess-center-timing/report.json`
records this failed measurement, not a passing benchmark. There is **no candidate
performance result**. Use a validated live admission and the existing GPU timer
for the next measured experiment rather than treating this counter attempt as
cost evidence. The retained runtime/artifact remain `68CFD66A...`; no game or
replay remains running.

Inspection of the larger A3B9/93626 first-pair program shows a depth fetch plus
four rotated comparison samples; it warrants checking against the existing
shadow-mask implementation and actual pass bindings. Its approximately 0.960 ms
span still cannot be attributed wholly to this pixel shader from the log alone.
Next resolve the control discrepancy or otherwise validate the candidate's
remaining color math, qualify its supported live input contract, then compare
performance and motion before enabling anything. P2.2 remains open.

### Sampling-control diagnosis and input-view audit

Two control checks did not fix the large full-sampling discrepancy: preserving
arithmetic with HLSL `precise`, and expressing the guest sampling operations in
literal register/swizzle order. Both compile and replay successfully, but the
full variant remains at MAE 1.485/3.062. This does not support blaming ordinary
compiler multiply/add contraction or the high-level accumulation rewrite.

A third control retains the same full-sampling/color code but sets the sample
direction to zero. `fh1-postprocess-zero-offset.ps.hlsl` and
`postprocess-zero-offset-replay/` reduce MAE to **0.00804/0.01485**; RMS is
0.13269/0.18035 on the two active viewports. These are close to the center
candidate's 0.00498/0.01047 MAE. This localizes the large discrepancy to the
neighboring-sample path; it is not a proof that every remaining color difference
is harmless or that the full control is correct. The center candidate remains
unchanged. Reports are consolidated in `postprocess-visual-metrics.json`.

`postprocess-resource-audit.py` completed for both captured draws, with no error.
It confirms the sampled views: scene resource 2727, 2560x1440 R10G10B10A2_UNORM;
resource 2746, 640x384 R10G10B10A2_UNORM; resource 8874, 1280x720 R8G8B8A8_UNORM;
and LUT resource 2878, 16x16x16 R8G8B8A8_UNORM. All sampled views have one mip.
The first report printed opaque format objects; rerunning with ResourceFormat.Name
produced the concrete view formats. Constants and descriptors are preserved in
`postprocess-resource-audit/`. This confirms the offline unsigned/true-3D premise,
not an all-scene runtime admission contract.

No renderer shader gate or staged binary changed in these investigations. Next
qualify an isolated center candidate's live input contract and measure it, keeping
the unvalidated full control out of production. Broader motion/scenes and a
repeatable benefit remain required; no speedup is claimed from these replays.

### General fetch handling, disabled integration and first live comparison

The candidate is now in SDK source as `fh1_postprocess_center.ps.hlsl`, with its
compiled header. It handles per-channel signed/unsigned/biased/gamma fetches and
both true-3D and array-backed LUT sampling. Array slice interpolation precedes
gamma decoding, matching the original operation order. Captured unsigned/3D
replay metrics are unchanged from the initial center prototype; the additional
fetch modes still need independent runtime qualification. FXC /WX passes after
renaming the reserved `linear` local to `linearFilter`.

General candidate pixel DXBC SHA-256:
`FFC1AF6AFEA7E0908C0D058D950601BD15948B6484C700D6B2401A618457EE86`.
`postprocess-center-general-replay/` records both original race draws and unchanged
192-byte vertex outputs; `postprocess-visual-metrics.json` records image error.

Pipeline integration is **disabled**, restricted to VS20A41D modification 7,
PS614588 modification 0x0000400000000007, bindless host targets and 2x/2x.
It preserves original vertex/root/fixed-function state and includes pipeline-
creation fallback. `tools/check-fh1-postprocess-center.py` compiles the actual
predicate and checks disabled admission, all hash/modification bit exclusions,
scales/binding modes/target paths and the creation-fallback guard. It and the
existing video admission/alpha check pass. Disabled and isolated enabled renderer
builds pass; root/SDK diff checks pass.

Disabled DLL: `F74C950B89A6B85C3041BD33223B42955308555460FA3029D6BA8F41AB6D693A`.
Enabled experimental DLL: `92A20B9534579D4705FE6B4036640D27E4B5A5105D47FA5E08F4C2BBEC35593F`.
Both are saved under `p2/postprocess-{disabled,candidate}.dll`. The source gate
was restored immediately after the isolated candidate build.

Four live runs completed normally through `postprocess-abba.ps1`, using the
same short driving inputs and no pass-inventory logging. A1/B1/B2/A2 PIDs:
29064/41204/44104/37332. `summarize-postprocess-abba.py` measures accumulated
frame-time seconds 26-30 and approximate process ages 28-32; one screenshot at
31 seconds is outside the window. Each folder retains session/perf/process data.
All four screenshots were inspected. Traffic differs, and B2 shows nearby vehicle
contact at the final image, limiting workload matching.

| Run | Median frame ms | p95 ms | GPU ms | Mean draws/frame |
| --- | ---: | ---: | ---: | ---: |
| A1 | 20.577 | 28.966 | 20.728 | 3936.8 |
| B1 | 16.696 | 21.149 | 16.727 | 3420.3 |
| B2 | 16.626 | 22.280 | 16.632 | 3345.2 |
| A2 | 16.200 | 20.341 | 16.196 | 3197.2 |

Although the change of means is median -9.39%, p95 -11.92%, GPU -9.66%, CPU
-6.15%, draws also fall -5.16%, and **the final baseline is faster than either
candidate**. This is not a demonstrated shader speedup. Warm-up and changing
traffic/workload remain confounders; use a steadier repeated workload before
retaining any visual compromise. Private/working memory change only -0.32/-0.23%.
Detailed results are in `postprocess-abba-summary.json`.

An additional isolated enabled race capture completed normally, PID 36848, via
`postprocess-capture-launch.ps1` and `postprocess-capture-control.py`. Its controller
reports triggered/finished under `postprocess-native-rdc/`; actual bound-shader
auditing is the next evidence gate. No GPU replay overlapped live benchmarking.
After the run, the launcher restored the retained `68CFD66A...` runtime. P2.2
remains incomplete and the source gate stays disabled.

The bound-stage audit is complete: `postprocess-native-rdc/frame_frame3989.rdc`
has two matching draws, events 39907/39935, both using pixel resource 1361. The
saved `postprocess-native-audit/Pixel-1361.dxbc` hashes to `FFC1AF6A...`, exactly
the native candidate. Its report has no error. This proves live stage execution
in the captured race, not a speedup or complete motion/format qualification.
Next run a steadier baseline/candidate comparison; keep admission disabled until
there is a repeatable benefit and sufficient visual coverage.

### Stationary comparison: center-sample simplification not retained

`postprocess-stationary.ps1` completed four normal runs on the same A/B binaries,
PIDs 48680/43764/33184/2540. It uses the existing stationary open-world script,
with pass inventory disabled. `summarize-postprocess-stationary.py` measures
accumulated frame-time seconds **32-44**, excluding captures at 30 and 45 seconds;
process samples use approximate ages 34-46. All final images were inspected:
stationary at the Recaro Rush entrance, with matching camera/player placement.
Recorded positions agree within about a millimeter. Traffic/NPC animation still
varies; the runs are steadier, not identical or a statistical guarantee.

| Run | Median frame ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 16.613 | 19.832 | 21.573 | 16.523 | 3325.8 |
| B1 | 16.619 | 20.897 | 24.149 | 16.677 | 3355.3 |
| B2 | 16.710 | 23.063 | 27.151 | 17.008 | 3237.3 |
| A2 | 16.391 | 19.774 | 22.493 | 16.397 | 3262.7 |

Change of means: median **+0.99%**, p95 **+10.99%**, p99 **+16.42%**, GPU
**+2.32%**, draws **+0.063%**, CPU **-1.44%**, private memory **-0.26%** and
working set **-1.11%**. There is no useful demonstrated frame-time improvement,
and both candidate tail measurements are worse than both baselines. This fails
the retention gate for a visual compromise. It does not prove every scene will
regress or identify a low-level cause; do not reinterpret the earlier confounded
-9.39% driving mean as a confirmed gain.

Decision: **do not retain the center-sample simplification**. Its source gate
stays disabled, as the admission check requires. The bounded P2.2 experiment is
complete with a rejected result; signed/array mode and broader motion qualification
were not completed and are not claimed. Revisit only with a different measured
cost-reduction hypothesis, rather than spending more qualification work on this
candidate. P2.1/P2.3/P2.4/P2.5 and the full goal remain open.

Evidence: `p2/postprocess-stationary-{a1,b1,b2,a2}/`, the launcher/summarizer and
`postprocess-stationary-summary.json`. Both staged DLLs were restored to retained
`68CFD66A...`; no game/replay is left running.

Additional attribution finding: `render_target_cache_->Update` runs before
`ObserveFh1GpuPassTimingDraw`, and may itself dispatch transfers. At an attachment
change, those commands can precede the new span's timing boundary and be included
in the preceding span. The 1E6883 family can also invoke an existing native
rectangle-clear shortcut after observation. Thus the first-pair/no-PS group is
not proof of expensive pixel shading, nor a complete per-pass ownership cost.
Keep recorded values as timed command spans. Before acting on the larger spans,
inspect actual commands and separate transfer/clear cost from shader execution.


### Video upload: changing-frame qualification and 2x retention

The pending movie-update check passed on candidate `CBB5F477...` in live run
PID **37412**, normal exit. Three RenderDoc captures at approximately 45, 50 and
55 seconds (`frame8950`, `frame9400`, `frame9852`) contain video draws 1761, 1757
and 1840. All three Y/U/V hashes change between every sampled frame. For each
frame, the 1280x720 luma and two 640x360 chroma textures exactly match the active
rows of their CPU upload buffer: **4,147,200 matching bytes** across nine planes.
The upload sources have CPUWrite/CopySrc usage and no captured GPU writes.
Rendered active regions were inspected: normal changing car/movie scenes, no
obvious corruption. This proves sampled updates, not continuous motion timing,
all movie formats, or a separately recorded decoder-to-guest-memory comparison.
The prior same-input output parity and watch/race checks remain complementary
rather than being replaced by screenshot inspection.

Decision: **retain the video CPU upload at 2x** for the exact 7156CE/31511D shader
pair. Unsupported layouts, mipmapped/array/scaled/GPU-owned resources and failed
allocations retain the existing texture load path. The original texture watch
lifecycle remains in place. Other resolution scales are not admitted yet.
The earlier ABBA evidence remains the performance basis: CPU **-5.24%**, median
frame time **+0.09%**, p95 **+0.42%**, p99 **+1.43%**, GPU **+0.72%**. This is a
bounded movie upload improvement, not a general driving FPS gain or full texture
ownership retirement. The selected CPU-owned R8 loads avoid the shared GPU
texture conversion path; the renderer still uses its existing cache and watches.

`check-fh1-video-upload.py` now compiles the actual admission expression as well
as the production upload block: exact hashes, every hash bit flip, null pixel
shader, all 1x/2x/3x axis combinations, layout/ownership/allocation rejection and
luma/chroma success pass. `check-fh1-texture-watch.py` passes. Release DLL rebuild
and SDK diff checks pass (existing compiler warnings remain).

Retained DLL SHA256:
`385DDBD7C8678BA95D6FAEF109143BDB9F63A3E868776E667EBF74BA208AEF3E`.
This includes the current pass-sample diagnostics and the still-disabled center
post-process experiment; the earlier ABBA isolated the upload change, not this
combined diagnostic build. Final rebuilt title smoke PID **43864** exited
normally; its 60-second image was inspected and shows the movie plus title UI.
Both staged copies now use this DLL; `p2/video-upload-retained.dll` preserves it.
The previous `p2/video-retained.dll` remains the pre-upload baseline.

Evidence under `.local/native-renderer/p2/`: `video-upload-motion-rdc/`,
`video-upload-motion-audit-frame_frame*/report.json` and exported images,
`video-upload-motion-summary.json`, `video-upload-retained-build.log`, and
`video-upload-retained-smoke/`. Three sparse frames do not qualify 1x, other
hardware, all FMVs or timing behavior. P2.3 remains open for measured gameplay
transfer/cache work; P2.1 CPU attribution and 1x shader qualification are next.


### CPU preparation sampling: repeated probe exposes diagnostic contamination

Added the existing `fh1_prepare_cpu_time_ns` measurement to the existing sampled
GPU pass records. It accumulates once per observed draw, resets with the active
span, and is logged when that record retires. No extra clocks or GPU queries.
`rank-fh1-pass-samples.py` reports CPU totals per family and individual sampled
frame; legacy or mixed records omit CPU attribution instead of inventing zeroes.
Its runnable self-check covers accumulation, absent families, missing CPU fields,
negative timing, duplicate/conflicting records and selected windows. Build and
root/SDK whitespace checks passed.

Two diagnostic driving runs, PIDs **50340** and **38192**, exited normally.
DLL `F5C2DAF5AB20D13919ED43937F98CAEF603E3CD3A305B92CD2C9486C0B3B52E7`
contains this instrumentation. Both final screenshots were inspected: comparable
road/camera at 84/83 km/h, with different traffic. The 26-30 second windows each
contain samples at frames 2880, 2940 and 3000 (467/466 valid pass records).

| Run | Frame 2880 preparation ms | Frame 2940 ms | Frame 3000 ms |
| --- | ---: | ---: | ---: |
| First | 3.4707 | 3.0980 | 49.2127 |
| Repeat | 2.8828 | 3.0672 | 22.0227 |

The large frame-3000 values coincide with diagnostic scene-binding dumps in both
logs. `IssueDraw` records those address/constant snapshots every 600 frames,
inside the preparation clock. The dump formats/hashes guest command data and
logs each selected draw. The sampled preparation includes that overhead; these
numbers do **not** establish a steady gameplay bottleneck or a shader cost.
In particular, spans labelled with first pair 8D8A/BA6A contain other draws: the
binding dump selects AD2C/2F21 and its following draw. First-pair attribution would
therefore target the wrong work. Asynchronous producer logging may also perturb
the run; two clean samples do not remove every diagnostic effect.

The pre-dump frames (2880/2940) are saved separately, with explicit reduced scope.
Family 899E92D8FCB7724B averages 0.3334/0.3180 ms preparation per sampled frame;
B5B299DA0DBC3029 averages 0.2441/0.1906 ms. Family 53B2C36308FCD219 varies
0.3372/0.6801 ms. These are preliminary preparation spans, not import/copy-only
measurements. Timing ends before texture requests and substantial later draw
work; it cannot prove total renderer CPU cost. GPU attachment-transfer boundary
caveats documented above still apply. Do not use the contaminated whole-window
means as optimization targets or performance claims.

Evidence: `p2/scene-scale-2x-pass-cpu{,-repeat}/` runtime/corpus/perf logs,
`window-pass-ranking.json`, `window-pre-dump-ranking.json`, and final images;
`pass-cpu-build.log` and `pass-cpu.dll`. Runtime and artifact DLLs restored to
retained **385DDBD7...**; no game/replay remains running. Source retains the new
diagnostics, so it intentionally builds a different hash from the staged binary.

Next: separate the expensive binding/producer census from performance collection
before collecting a broader CPU/resource ranking. Continue 1x shader qualification;
P2.1 is still open. This finding also limits previous corpus-enabled performance
windows that include a 600-frame binding dump; corpus-disabled comparisons are
unaffected by that specific instrumentation.


### Separate scene dumps from timing collection

Detailed binding/producer census now requires both GPU corpus collection and
`--pinyon_shift_fh1_scene_dump=true` (default false, restart required). Use the
extra flag only for binding evidence, not performance runs. Existing
`-CollectFh1PassInventory` still collects execution coverage, sampled timings and
corpus output without the address/constant dumps. Both dump callers are gated;
no guest execution, rendering or resource ownership changes.

Full release executable/DLL rebuild passed. Two driving probes (PIDs **24392**,
**25092**, normal exits) confirm **zero scene-binding and scene-producer records**
while retaining 467/440 selected GPU pass records with preparation CPU values.
Both final images were inspected: the same road/camera at 84/83 km/h, traffic
varies. The original 26-30 second window and source frames 2880/2940/3000 remain.

| Run | Frame 2880 preparation ms | Frame 2940 ms | Frame 3000 ms |
| --- | ---: | ---: | ---: |
| A | 2.8722 | 2.9666 | 7.2271 |
| B | 3.2318 | 2.9310 | 5.1102 |

The previous 22-49 ms spike is substantially reduced, but not entirely explained.
Family 738B37134E7F4A0C (first pair 1E6883/A4A965) now leads sampled preparation,
1.4523/0.8786 ms per sampled frame. CA293/no-PS family E0EB0DD9AD7C4CF9 follows at
0.3040/0.2669 ms; 8D8A/BA6A family 53B2C36308FCD219 costs 0.2333/0.2456 ms.
These still aggregate mixed spans, include existing instrumentation, and exclude
later texture/import work. Remaining periodic aggregate logging or render-target
preparation may contribute; neither is established as the residual cause.
Do not claim a gameplay speedup from reducing debug collection overhead.

Evidence: `p2/scene-scale-2x-clean-cpu-{a,b}/` logs, corpus, per-window rankings
and inspected images; `census-split-build.log`. The pass ranking self-check and
root/SDK diff checks pass. No game is left running. Current staged/source build:
DLL `C55A91150E0037FEDE16BC52501D263E44A2043557FCE505F4C639943424269F`,
EXE `26EF85B1F4D5B5F6CB94F2BD92033EA67C2BE2A4FE87E42102799A31455DB499`.
The renderer retains video upload and B848/video shaders at their qualified 2x
scope; center-sample post-processing and regressing ownership remain disabled.

P2.1 remains open. Next qualify 1x shader stages and isolate the remaining
preparation/resource costs with wider sampling before choosing an optimization.
The dump-enabled path is preserved by the explicit flag but was not rerun here;
normal corpus collection is the tested path in these probes.


### 1x race reference: normal run passes, RenderDoc attempt fails

Started B848 1x qualification using the current retained C55A9115 DLL and
26EF85B1 executable, without changing any shader gate. The existing race script
at 1x reached the capture trigger in injected run PID **44956**, then reported
`Graphics device lost` and exited with 0xC0000409. Controller reports triggered
and finished, but **no RDC file was produced**. Crash ID:
`pscrash-v1-73d22b104e294c64bcb5`. The bundle's runtime tail does not provide a
specific device-removal reason; do not invent one or infer shader failure.

The same 1x race script without RenderDoc, PID **49032**, exited normally. All six
scheduled images were produced; the final 1280x720 race image was inspected and
shows the car driving at 85 km/h with geometry, crowd and UI present. This is a
successful bounded 1x reference smoke, not native B848 qualification, a completed
race, or a whole-game correctness result. The selected B848 native VS still has
its 2x gate and the bytecode is unchanged (B2BEB341...). The capture-associated
failure did not reproduce in this one uninjected control run; its cause remains
unresolved.

Evidence: `p2/skinned-1x-rdc/` controller, crash report/tail, session/perf logs and
result JSON; `p2/skinned-1x-plain-test/` images, corpus, session/perf logs and result.
Both processes are terminal, with no game left running. No shader admission was
widened and no renderer binary was replaced during this qualification attempt.

Next: obtain usable 1x reference evidence at another capture point or through a
bounded live comparison; keep the gate closed until input/output and performance
checks actually pass. Video-stage 1x qualification and broader resource ranking
remain independent work. P2.1 and the full goal remain open.


### 1x video pixel shader: same-input replay passes

The independent title/video capture at 1x succeeded, PID **46528**, normal exit,
current C55A9115 renderer. `video-1x-rdc/frame_frame9677.rdc` contains the exact
7156CE/31511D video pair at event **1729**. The reference pixel bytecode SHA is
`4684213525C9A5DBF6311D5E93B0E7948AB7B1ED40DC19AACEC45B7DADDFAA40`,
different from the native candidate (explicitly asserted to avoid self-comparison).

Replacing that shader with the unchanged retained native DXBC
`96AB627264DD5DE29C18E8DBB0CC83DF44C47C44E7C0872D6271673760742CC4`
produced **20,971,520 identical attachment bytes** and **128 identical post-VS
bytes**. Attachment allocation is 1280x2048, including padding; this is byte
identity, not an image-quality percentage. One matching draw and one shader variant
were present; the whole capture's draw-to-pipeline mapping was checked. The
60-second 1280x720 title image was inspected and shows the movie and title UI.
No RenderDoc device loss occurred here; the race capture problem remains separate.

An isolated candidate DLL broadens only this video pixel shader's scale predicate
to symmetric 1x or 2x, retaining exact shader/modification, host RT and bindless
gates. SHA `B3F59D1EDA3EA10B5B3BDD4B7753489B1A664D94ACEF2437D91AD25916AE2DC2`
is saved as `p2/video-1x-candidate.dll`; it built successfully. Production source
and staged artifacts are restored to their **2x-only** gate/C55A9115 baseline.
B848 and CPU video upload gates were not broadened. This is preparation for live
qualification, not admission or a performance claim.

Evidence: `p2/video-1x-rdc/`, `video-1x-parity.py` and its output/report directory,
`video-1x-test/`, and `video-1x-candidate-build.log`. No game/replay remains running.
Next verify native binding at 1x in the isolated candidate and run a matched title
ABBA comparison before retaining the scale extension. One captured frame does not
qualify every movie/input mode or timing behavior. The full P2 goal remains open.


### Video pixel stage retained at symmetric 1x and 2x

Live 1x candidate capture PID **44532** exited normally. In
`video-1x-native-rdc/frame_frame10327.rdc`, event **1728** binds pixel shader
96AB6272... (exact full SHA asserted by `video-1x-bound-audit.py` after mapping all
draws). This complements the previous 1x same-input attachment comparison.

A/B/B/A runs used baseline C55A9115 and isolated candidate B3F59D1, at 1x with
corpus diagnostics disabled. Measurement uses accumulated frame-time seconds
**40-52**, away from captures at 15/30/60; process samples use approximate ages
42-54. All four exited normally and all 60-second images were inspected: movie
plus title UI, no obvious visual regression. Movie phase is not bit-identical.

| Run | PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a1 | 34824 | 8.3570 | 10.5150 | 11.2140 | 5.5017 | 47.0000 |
| b1 | 1376 | 8.3815 | 10.5150 | 11.5200 | 5.5972 | 47.0007 |
| b2 | 37240 | 8.3835 | 10.5880 | 11.3130 | 5.3291 | 47.0007 |
| a2 | 36952 | 8.5085 | 10.5340 | 11.1700 | 5.7196 | 47.0000 |

Changes of means: median **-0.60%**, p95 **+0.26%**, p99 **+2.01%**, GPU
**-2.63%**, CPU **+0.09%**, draws **+0.0015%**, private memory **-0.47%**,
working set **+0.79%**. No material frame-time regression demonstrated in this
bounded title test; retain as faithful dependency replacement, not a general
performance claim. The small p99 increase is recorded rather than hidden.

Production video pixel admission now accepts symmetric 1x or 2x, preserving exact
shader/modification hashes, bindless and host-render-target constraints. The
admission/alpha check compiles the actual predicate and tests scale combinations,
hash/modification bit flips, other RT path, missing bindless support and alpha
comparisons. It passes. The release rebuild matches the tested candidate exactly:
**B3F59D1EDA3EA10B5B3BDD4B7753489B1A664D94ACEF2437D91AD25916AE2DC2**.
Both staged DLLs now contain that build; EXE remains 26EF85B1....
B848 and CPU video upload remain 2x-only; neither was silently broadened.

Evidence: `p2/video-1x-binding-summary.json`, `video-1x-bound-audit/`,
`video-1x-abba-{a1,b1,b2,a2}/`, `video-1x-abba-summary.json`, its launcher and
summarizer, and `video-1x-retained-build.log`. No game/replay remains running.
This qualifies the tested title/video path and hardware, not all FMVs, every
input mode, other scales or other hardware. P2.1 still needs B848 at 1x and fuller
CPU/resource attribution; the rest of P2 remains open.


### B848 1x reference and replay qualification

Moving the race capture trigger from 72 to 66 seconds with corpus collection
still enabled reproduced the device loss: PID **42120**, 0xC0000409, same crash
ID 73d22b104e294c64bcb5, no RDC. A controlled retry at 66 seconds with corpus
collection disabled succeeded: PID **37648**, normal exit, capture
`skinned-1x-clean-rdc/frame_frame4052.rdc`. This is evidence of a capture /
diagnostics interaction, not a proven root cause or ordinary-play crash. Use
corpus-disabled captures for the following 1x qualification. The 1x plain race
control had already passed. No guest saves were copied/reset for these runs.

The successful capture contains **489 draws** of the exact B8489164/68150A8E pair.
Every draw was mapped to its pipeline. Replacing the translated vertex shader
(reference SHA 1CD5925B8515AADB7DB9C94911CF3AEE1F66746BF2E899E218428845D990A248)
with the unchanged native B2BEB341... produced **7,557,696 identical post-VS bytes
across all 489 draws**. The reference was explicitly checked to differ from the
native bytecode, preventing a vacuous self-comparison.

First/middle/last representative draws then passed color/depth comparisons:
**six attachments, 125,829,120 identical bytes** across all attachment samples.
Full allocations include padding; this is byte equality, not an image percentage.
The final race screenshot was inspected and shows the car/crowd/UI at 84 km/h.
This proves the captured 1x inputs, not all animations or all game scenes.

Built isolated candidate **35A52EE55F452624ADF7DFF27A9C867E47522C64612A7E0E2ADFDCD81183E1D5**
(`p2/skinned-1x-candidate.dll`) by widening only B848's native vertex scale gate to
symmetric 1x/2x. Geometry ownership remains disabled; video and other gates are
unchanged. Build passed. Production source and both staged DLLs are restored to
retained **B3F59D1...**, with B848 still 2x-only. No game/replay remains running.

Evidence: `p2/skinned-1x-early-rdc/` failure record/logs,
`skinned-1x-clean-rdc/` successful capture/session logs,
`skinned-1x-parity/` and `skinned-1x-attachment-parity/` reports/raw outputs,
`skinned-1x-clean-test/` images and `skinned-1x-candidate-build.log`.
Next verify candidate native binding in a corpus-disabled 1x race capture and run
matched gameplay ABBA before retaining the extension. P2.1/full P2 remain open.


### B848 1x live binding passes; retention rejected on frame-time tails

Candidate capture PID **24028**, corpus disabled, exited normally and produced
`skinned-1x-native-rdc/frame_frame4042.rdc`. Every draw was mapped to its pipeline;
**489 B848 draws** bind native VS B2BEB341... (SHA asserted for each representative
pipeline). This completes live-binding evidence alongside the exact 1x replay.

Stationary open-world A/B/B/A uses baseline B3F59D1 and candidate 35A52EE5 at 1x,
corpus disabled, frame-time seconds **32-44** between screenshots at 30/45 seconds;
process samples use approximate ages 34-46. All four normal exits and final images
were inspected: stationary at Recaro Rush with the same camera/player placement,
with varying traffic/NPC phases. This is comparable, not identical, work.

| Run | PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a1 | 41228 | 15.9725 | 18.9330 | 21.1290 | 15.2104 | 3431.19 |
| b1 | 42760 | 16.1590 | 19.2560 | 23.7290 | 15.7436 | 3516.00 |
| b2 | 38884 | 16.6990 | 21.9610 | 24.9680 | 16.1679 | 3435.20 |
| a2 | 24648 | 16.1275 | 19.0510 | 20.7880 | 15.3771 | 3463.93 |

Changes of means: median **+2.36%**, p95 **+8.51%**, p99 **+16.17%**, GPU
**+4.33%**, draws **+0.81%**, CPU **+1.50%**, private memory **-1.02%**, working
set **-0.71%**. Both candidate p99 values exceed both baselines. Variation remains,
but this does not demonstrate the no-material-regression gate needed to retain
the native dependency replacement. Correct output alone does not justify enabling
this extension under the performance-first approach.

Decision: **do not enable B848 at 1x yet**. Keep the qualified 2x native path and
existing 1x reference path. This is not a 1x crash or visual mismatch. The exact
candidate is preserved for targeted cost diagnosis, not repeatedly rebenchmarked
without a new hypothesis. Geometry ownership is still disabled independently.
Video pixel admission remains symmetric 1x/2x; CPU video upload remains 2x-only.

Evidence: `p2/skinned-1x-bound-audit/`, `skinned-1x-native-rdc/`,
`skinned-1x-abba-{a1,b1,b2,a2}/` and `skinned-1x-abba-summary.json` with its
launcher/summarizer. Both staged DLLs restored to **B3F59D1...**, matching retained
source. No game/replay is left running. P2.1's B848 1x retention remains incomplete;
next isolate shader/resource cost before revising it, while continuing independent
P2.3 transfer work and measured scene coverage. The full P2 goal remains open.


### B848 grouped vertex loads: bounded optimization prototype passes replay

Inspection of the retained native shader disassembly confirms eight scalar raw
loads for the 32-byte primary vertex, each selecting the shared SRV/UAV. This is
a concrete optimization hypothesis, **not proof that it caused the 1x regression**.
A local prototype groups those words into two Load4 operations. Each group is
vectorized only if all 16 bytes fit inside the existing 512 MiB shared buffer;
otherwise the original scalar calls preserve boundary/address-wrap behavior.
The owned-geometry macro always retains scalar loads and its existing guard.
Transform-stream decoding, endian conversions and arithmetic are unchanged.

FXC /O3 /WX passes after rewriting the helper to a single initialized return
(the initial early-return form triggered FXC's uninitialized-value diagnostic).
DXBC SHA **4ADE226A2DABAFE8AD59EEF0B14B8D20993B4B2302A3187D89E965B2DF81052E**.
Disassembly confirms vector raw loads on the common branch and still declares
18 temporary registers. Static code also contains the scalar fallback; this is
not a total-instruction-count or runtime speedup claim.

`p2/check-vector-load.py` compiles the actual LoadWord/LoadVertexWords bodies as
C++ with buffer mocks, then checks SRV/UAV selection, offsets, boundary and
wraparound addresses, and the owned macro's scalar fallback. It passes. This
checks address-selection logic, not GPU-driver bounds behavior by itself.

Replacing the reference shader in the successful corpus-disabled 1x capture
passes **all 489 vertex outputs / 7,557,696 bytes** exactly. First/middle/last
representatives also pass **six color/depth attachments / 125,829,120 bytes**.
The original reference hash differs from the candidate; all draws are mapped.
This establishes captured-input correctness, not all scene/memory states.

Evidence: `p2/skinned-vector-load.vs.hlsl`, `.dxbc`, `.asm`, the helper check,
`skinned-vector-1x-parity/` and `skinned-vector-1x-attachment-parity/` reports and
replay scripts. No production source, shader admission or staged DLL changed;
retained renderer remains B3F59D1.... No game/replay remains running.
Next build an isolated grouped-load candidate and benchmark 1x before deciding
whether to replace the rejected 1x extension. If retained at 2x as well, qualify
that configuration independently. P2.1 and full P2 remain open.


### Grouped-load B848 live comparison: do not retain yet

Built isolated DLL **7276DBDA3BD837343AD5F64FA1B17E9C5FC8684A1E3E8737439FB6A3BCE1ADF9**
with grouped-load DXBC 4ADE226A... and the symmetric 1x/2x B848 predicate. Production
source/header were restored immediately after building; this candidate is not the
retained renderer. Candidate capture PID **50144**, corpus disabled, exited
normally. `skinned-vector-native-rdc/frame_frame4395.rdc` maps all draw pipelines;
**489 B848 draws** bind the grouped-load bytecode, verified by shader SHA.

A/B/B/A compares retained B3F59D1 against this candidate at **1x**, corpus disabled,
stationary Recaro Rush entrance. Window: frame-time seconds **32-44**, process ages
34-46, captures outside at 30/45 seconds. All runs exited normally, all final images
were inspected, and player/camera placement is consistent. Traffic/NPC phases vary.

| Run | PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a1 | 38496 | 16.1970 | 19.6390 | 21.6840 | 15.6717 | 3459.73 |
| b1 | 29772 | 16.3470 | 19.6300 | 21.5910 | 15.6155 | 3577.18 |
| b2 | 14048 | 16.0620 | 18.9690 | 25.7160 | 15.0650 | 3304.11 |
| a2 | 33844 | 15.6935 | 18.6460 | 21.5750 | 14.7905 | 3304.80 |

Changes of means: median **+1.63%**, p95 **+0.82%**, p99 **+9.36%**, GPU **+0.72%**,
draws **+1.73%**, CPU **+0.64%**, private memory **+0.75%**, working set **+0.41%**.
There is no demonstrated benefit or sufficiently clear no-regression result for
retention. Draw variation limits causality; these figures do not prove the grouped
loads themselves cause the tails. Nor can the prior scalar-native experiment be
subtracted from this run to claim a grouped-load speedup: it was a different set
of live workloads. The static reduction in common-path load operations is not a
performance result.

Decision: keep this prototype isolated, with **B848 still 2x-only in production**.
Its exact-output evidence remains useful, but stop iterating this shader based only
on whole-frame noise. Return to broader resource attribution before another B848
revision; 1x native B848 retention remains an explicit open item, not cancelled.
2x grouped-load qualification was not run and is not claimed.

Evidence: `p2/skinned-vector-build.log`, `skinned-vector-candidate.dll`,
`skinned-vector-bound-audit/`, `skinned-vector-native-rdc/`,
`skinned-vector-abba-{a1,b1,b2,a2}/`, and `skinned-vector-abba-summary.json` with
its launcher/summarizer. Both staged DLLs restored to **B3F59D1...**; no game/replay
remains running. No production shader source, header or admission changed.
P2.1/P2.3/P2.4/P2.5 and the full goal remain open.


### Resource activity audit: readback waits absent; cache counters are descriptors

Added `tools/rank-fh1-resource-window.py` to summarize explicit frame-time windows
from existing CSVs. It validates window coverage, positive-duration frame
selection and nonnegative counters. Its self-check covers boundary selection,
zero-duration rows, aggregation and invalid/incomplete windows. Counts are
reported as activity, not ranked as CPU/GPU cost; nanosecond counters retain units.

Audited two 2x driving windows (26-30 seconds, 198/199 frames) and four retained
1x stationary baselines (32-44 seconds, 754/752/739/772 frames). All six report
**zero** command-buffer stalls, resolve-readback requests/bytes/wait time,
strict ZPD query waits/time, and memexport bytes. These paths do not explain cost
in these selected windows. This is not proof that they are absent elsewhere,
in the deferred town, or outside the instrumented paths. Render-target transfers
that remain on the GPU are not counted as readbacks.

| Window | Descriptor hits/frame | Descriptor misses/frame |
| --- | ---: | ---: |
| 2x driving A | 3091.965 | 0.091 |
| 2x driving B | 3094.291 | 0.095 |
| 1x stationary first A1 | 3353.463 | 0.013 |
| 1x stationary first A2 | 3345.399 | 0.003 |
| 1x stationary grouped-load test A1 | 3413.057 | 0.004 |
| 1x stationary grouped-load test A2 | 3251.972 | 0.000 |

Critical counter interpretation: the D3D12 `PROFILE_TEXTURE_CACHE_HIT/MISS`
callers are in `FindOrCreateTextureDescriptor`, around texture_cache.cpp:2190.
They measure **SRV descriptor reuse/creation**, not texture residency, dirty
texture reloads, imported bytes or upload CPU/GPU time. A reused descriptor may
still refer to newly loaded contents. Therefore neither this table nor previous
HUD/cache-hit readings establish cheap texture uploads or justify skipping them.
The tool reports the original CSV field names with this meaning stated explicitly.

Trace: D3D12 RequestTextures calls the shared TextureCache::RequestTextures loader,
then prepares any 3D wrappers and transitions resources. Descriptor lookup is a
separate operation. CPU preparation timing ends before these later texture
requests, so it also cannot substitute for upload/import cost measurement.

Evidence: `p2/resource-window-summary.json`, computed from
`scene-scale-2x-clean-cpu-{a,b}`, retained `skinned-1x-abba-{a1,a2}` and retained
`skinned-vector-abba-{a1,a2}` CSVs. No new live run, binary or renderer behavior
change. Next measure actual texture request/load and render-target transfer cost;
do not optimize readback waiting based on these zero-activity windows or confuse
SRV reuse with upload avoidance. Broader scenes and complete cost ranking remain
open alongside B848 1x retention and the remaining P2 work.


### Actual texture request CPU timing and dirty-load activity

Appended three performance counters without renumbering existing IDs:
`texture_request_cpu_time_ns`, `texture_request_timing_samples`, and
`texture_dirty_load_attempts`. D3D12 times the existing RequestTextures call chain
(including native wrappers, residency/load work, 3D wrappers and transitions),
only with corpus enabled on every 60th source frame. Timing is outside the earlier
preparation clock and survives command submission changes because it uses the
existing frame-counter registry, not GPU-span lifetime. It is CPU elapsed time,
not GPU texture conversion time, and includes cache hits and any nested waits.

The shared PrepareTextureLoad path counts a dirty-load attempt after its locked
outdated/watch checks and before CPU or backend loading. It counts dirty requests,
including retries/failures, not unique resources, successful loads or bytes.
The unchanged watch/partial-load/race tests now include a counter mock and prove
that clean textures do not increment it. They pass. The resource-window tool
handles old/new schemas, distinguishes unsampled timing from zero cost, and its
expanded self-check passes. Full release rebuild passes; existing warnings remain.

Two new 2x driving probes, PIDs **38824** and **22696**, exited normally. Images
were inspected: comparable road/camera and 83 km/h, with traffic variation.
The 26-30 second windows contain 177/182 frames and three timed frames each.

| Run | Request CPU ms per timed frame | Individual timed-frame ms | Dirty attempts/frame |
| --- | ---: | --- | ---: |
| A | 2.4598 | 1.9236, 1.9219, 3.5340 | 86.4520 |
| B | 2.2192 | 2.3183, 2.2843, 2.0549 | 88.9505 |

This identifies material texture-request CPU work despite sparse descriptor misses.
It does not attribute all 2.2-2.5 ms to uploads or establish which textures are
expensive. Next classify the dirty loads and time their load/transfer work before
changing invalidation, copies or conversion. GPU render-target transfer cost is
still separately unmeasured. Three samples/run are provisional, not a full cost
ranking or a speedup experiment.

Frame alignment check: all 51 nonzero timing rows in run A and all nonzero timing
rows in B have zero-based CSV index modulo 60 equal to 59. In these runs the source
frame equals **CSV row + 1**, so sampled rows 2879/2939/2999 represent source frames
2880/2940/3000. Earlier shorthand treating row index directly as source frame was
not exact. Verify alignment when joining telemetry; the selected interior samples
in the prior short windows are unchanged, but edge-frame joins need this correction.

Evidence: `p2/scene-scale-2x-texture-cpu-{a,b}/` CSVs, resource-window JSONs,
corpus/runtime logs and images; `texture-timing-build.log`. Current built/staged
renderer DLL SHA **97F7FC93C27C2A8BA228BD2EEB4775A8BC1DC96BFDFB15CB74D9B1C049C158AA**;
updated counter registry runtime SHA
**FCE008D847CD0832BD021B2231BFF7EDDAED7E8DFBECA0A6D780D63E16403BA0**.
EXE remains 26EF85B1.... The runtime must accompany this renderer for the new
counter columns. Renderer behavior/admission is unchanged: B848 2x-only, video
pixel symmetric 1x/2x, CPU video upload 2x-only; grouped-load prototype not retained.
No game/replay remains running. P2.1/P2.3 and full P2 remain open.

### Texture-load classification from existing trace (2026-09-07)

Retained renderer 97F7FC93..., runtime FCE008D...; no renderer changes. One 2x
AppData driving probe (PID 23960) exited normally. Screenshot at 31 seconds shows
the expected road/camera at 83 km/h. GPU-category trace was temporarily enabled;
the original config was restored byte-for-byte. Do not use this trace-heavy run
as benchmark evidence or equate its wall-time window with earlier CSV windows.

`tools/rank-fh1-texture-loads.py` reuses existing successful-load messages. In
[26, 30) seconds since the first log timestamp, 19,923 messages cover 98 logged
signatures; 19,450 (97.626%) are scaled resolves. All use the resident-memory
backend, with no CPU-loader successes. These are messages, not unique resource
identities, dirty attempts, transferred bytes, GPU timings or frame counts. The
existing log signature omits some texture-key fields and does not identify the
specific dirty subresources. The parser checks window coverage and boundaries;
its runnable `--self-test` passed.

Repeated signatures include 1280x720 k_2_10_10_10 at 0x1C4E1000 (458 unpacked,
457 packed), 1280x720 k_8_8_8_8 at 0x1DAC5000 (458), and several smaller scaled
postprocess surfaces (458 each). Repeated unscaled loads include a 16x16x16 LUT
at 0x136FB000 (231) and a 32x32 DXT4_5 texture at 0x13721000 (220). Other unscaled
signatures account for only 22 messages. Shared addresses, different formats and
packed flags do not prove redundant work: intervening writes and layout matter.

Next prioritize scaled-resolve conversion attribution over generic asset-cache
changes. D3D12 LoadTextureDataFromResidentMemoryImpl selects a scaled load PSO,
requests a scratch GPU buffer, makes the scaled range current, dispatches the
conversion and copies into the texture. Measure that chain, then inspect whether
a bounded native producer/consumer pair can avoid it while preserving guest writes,
aliases, formats and synchronization. Counts alone do not attribute the previous
2.22-2.46 ms CPU request totals or prove a safe conversion bypass.

Evidence: `.local/native-renderer/p2/texture-load-trace/{loads.log,ranking.json,
launch-valid.json,scene/moving-end.ppm}`. The first launch (PID 27292) rejected an
already-created output directory before gameplay; rerun used a fresh child path.
No speedup or additional dependency retirement claimed; P2.1/P2.3 remain open.
### Base-only packed-tail key experiment: not retained (2026-09-07)

Tested canonicalizing the unused packed-mips bit for base-only, non-array 2D
textures whose packed tail starts after level zero. Other key fields, layouts,
write watches and load code remained unchanged. Candidate 2C896A13... then guarded
revision 6903D7D716FCA90CCA74D21A406261AEBFF888963EDA40750EA6B4962D0DBD7A
avoid duplicate cached textures; the guarded revision skips already-clear flags.
Both builds passed (existing TextureKey memcpy/memset warnings). The isolated
candidate's check links the production util.cpp and info_formats.cpp, compares
1,344 base layouts for tiled/linear formats, padded pitches and dimension edges,
and rejects small-base, mipmapped, array and non-2D cases. Watch-race/retry checks
also pass. This is layout/admission evidence, not full GPU or whole-game parity.

Two stationary 2x ABBA sets completed with normal exits and reviewed screenshots.
The first set (PIDs 29844/31992/37064/33296) included a broad repository search
overlapping B1, so it cannot support performance claims. The guarded revision's
clean set (PIDs 49648/50000/18928/27736) ran without concurrent search/build/replay.
Frame window: accumulated CSV frame-time seconds 32-44; process window: 34-46.

| Run | Median ms | P95 ms | P99 ms | GPU mean ms | Draws/frame | Dirty attempts/frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 16.536 | 19.464 | 21.086 | 16.470 | 3328.6 | 86.953 |
| B1 | 17.550 | 22.134 | 23.938 | 18.114 | 3763.0 | 87.751 |
| B2 | 17.4195 | 21.655 | 23.494 | 17.729 | 3632.5 | 86.936 |
| A2 | 16.530 | 19.631 | 21.246 | 16.321 | 3270.6 | 87.418 |

Candidate versus mean baseline: median +5.76%, p95 +12.01%, p99 +12.05%, GPU
+9.31%, draws +12.07%, dirty attempts +0.18%, process CPU +2.80%, private memory
+0.38%. Draw-count differences prevent attributing slowdown to normalization;
there is still no repeatable benefit or non-regression evidence for retention.
Do not claim private memory measures texture allocation/VRAM. Screenshots show
the same stopped car/camera with varying NPC poses and traffic, not matched GPU
work. No speedup or dependency removal claimed.

Restored original cache.cpp byte-for-byte and both renderer DLLs to retained SHA
97F7FC93C27C2A8BA228BD2EEB4775A8BC1DC96BFDFB15CB74D9B1C049C158AA. Runtime remains
FCE008D.... Candidate source/DLL and both ABBA sets remain isolated under
`.local/native-renderer/p2/packed-key*`. Reproduce the check with:
`python tools/check-fh1-packed-tail.py --source .local/native-renderer/p2/packed-key-guard-candidate.cpp --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`.

Next measure the actual scaled conversion chain (CPU and GPU) and map a bounded
producer/consumer pair; do not assume canonicalizing an unused flag removes a
material number of conversions. P2.1/P2.3 and full P2 remain open.
### Direct scaled texture GPU timestamps (2026-09-07)

Reused the existing query heap, per-frame record slots and completed-submission
retirement for base-only, non-array scaled 2D texture loads. With corpus enabled,
every 60th source frame records a start after scaled-range selection, an endpoint
before the destination-copy barriers, and an endpoint after scratch-to-texture
copies. No new wait or readback allocation. Queries share the existing 256-record
capacity with pass spans; capacity/interrupted samples are dropped. Every query
is initialized before potential interruption. Full identity is retained internally;
logged groups expose base/dimensions/format/pitch/packed/endian/signed fields and
are not a universal texture-key identity (tiling is not logged).

The conversion interval includes source transitions, setup commands and dispatch;
the copy interval includes destination/scratch barriers and CopyTextureRegion.
CPU setup before GPU command execution, scaled-range selection/residency, other
texture shapes and render-target resolves themselves are outside this scope.
Texture intervals overlap the broader pass spans: never add the two rankings.
These instrumented frames do not establish a speedup or full-frame cost percentage.

Both retained-behavior 2x driving runs exited normally: A PID 49328, B PID 47172.
Images reviewed: expected road/camera, 84/83 km/h, traffic varies. Selected source
frames 2880/2940/3000 correspond to timed CSV row + 1 in the 26-30-second window.

| Run/frame | Loads measured | Conversion ms | Copy ms |
| --- | ---: | ---: | ---: |
| A/2880 | 82 | 0.687456 | 0.441984 |
| A/2940 | 83 | 0.681984 | 0.446656 |
| A/3000 | 82 | 0.678272 | 0.443680 |
| B/2880 | 83 | 0.700096 | 0.504672 |
| B/2940 | 82 | 0.659808 | 0.434464 |
| B/3000 | 82 | 0.674496 | 0.449344 |

Mean measured conversion+copy is 1.126677/1.140960 ms per sampled frame. Largest
logged groups: 1280x720 format 7 at 0x1C4E1000, unpacked/endian 2 (0.135819/
0.128128 ms/frame); format 6 at 0x1DAC5000 (0.112640/0.111616); format 6 at
0x1CE2D000 (0.096256/0.106133). Counts/costs divide by all three selected sampled
frames, including absences. Maximum observed shared-record indices were 238/240;
this is not proof that all possible samples retired successfully.

The legacy run collector merges rotated runtime logs, so B contains A too. The
first exploratory B sum doubled counts and was discarded. New tool
`tools/rank-fh1-texture-samples.py` requires an explicit session and source frames,
tracks logging.ready boundaries, deduplicates identical records, rejects conflicts
and malformed times, and uses the supplied frame denominator. Session IDs:
`20260908T012634Z-p49328`, `20260908T012716Z-p47172`. Do not rank a merged runtime
file without filtering its session. Earlier pass-ranking evidence using merged
logs needs session revalidation before using it for a new optimization decision;
per-session CSV measurements are unaffected.

`check-fh1-texture-timing.py` compiles the production allocation/advance methods
against a fake query sink and passes disabled/sampling/capacity/pending-slot/
interrupted-submission guards. GPU ranking self-tests pass session isolation,
deduplication/conflicts, negative samples and absent-frame denominator cases.
Renderer build passes. RenderDoc EventGPUDuration was independently retried on
frame3758: counter advertised, zero results and no debug messages; no timing
claim comes from that replay.

Evidence: `p2/scene-scale-2x-texture-gpu-{a,b}/texture-gpu-ranking.json`, per-session
CSVs, merged runtime logs, corrected window records, images; `texture-gpu-timing-build.log`;
`conversion-counter-audit/report.json`. Built/staged renderer SHA
8BD8EE1F881EA1DACC3D4756D5EAC49EE82B0824D2B84398B8CFFEE8FDE9540A; runtime remains
FCE008D847CD0832BD021B2231BFF7EDDAED7E8DFBECA0A6D780D63E16403BA0.
No admission or texture invalidation changes; packed-tail candidate stays isolated.
Next trace the 0x1C4E1000 producer/consumer chain in a capture and qualify a native
path that avoids the measured conversion while preserving required guest writes,
aliasing, formats and synchronization. P2.1/P2.3 and full P2 remain open.
### Captured 0x1C4E1000 producer/consumer chain (2026-09-07)

Inspected existing `p2/production-rdc/frame_frame3758.rdc` to explain the surface
identified by direct timing. This is a separate captured workload, not the exact
2880/2940/3000 timing frames; revalidate on a fresh capture before admission.
Replay completed without errors. No renderer/source/binary change in this step.

The scaled source descriptor uses buffer ResourceId::1922, offset 1,899,511,808
(0x1C4E1000 * 4), extent 15,073,280 (0x398000 * 4). Conversion PSO 397 has DXBC SHA
9ef595f68696b7686f110da36cb56197a15458cab95b34274e9da431611090b4 and writes scratch
buffer ResourceId::1902, followed by CopyTextureRegion into R10G10B10A2 textures.

| Load dispatch | Copy | Destination | Next draw (not automatically a proven consumer) |
| ---: | ---: | --- | --- |
| 15860 | 15862 | ResourceId::9994 | 15871: VS 972F0220C6D5A9A2 / PS 129FCB5D371AE0FC |
| 20099 | 20101 | ResourceId::9994 | 20110: same VS/PS |
| 38847 | 38849 | ResourceId::2727 | 38866: VS 2C53E1A563484076 / PS E17BECBE8BE65806 |

Three Resolve Copy Full 32bpp dispatches write consecutive portions of the range:
19898 writes offset 1,899,511,808 length 5,242,880; 34315 writes offset 1,904,754,688
length 5,242,880; 38706 writes offset 1,909,997,568 length 4,587,520. Assertions
verified these cover the loaded extent exactly with no gaps. These are descriptor
ranges, including padding; they do not by themselves prove every byte was written.
Each immediately preceding RT Dump (19891/34308/38699) reads ResourceId::2886:
`RT @ 0t, <32t>, 4xMSAA, k_2_10_10_10_FLOAT`, RGBA16F, allocation 2560x1024.
The same native target is reused. Allocation dimensions are not active rectangles.

Crucially, the first texture load precedes all three captured writes, the second
occurs after the first write but before the other two, and the last follows all
three. An alias to the latest native render target cannot preserve this assembled
surface's earlier and partially updated contents. A native replacement must track
resolved regions and their lifetimes, handle the captured 4xMSAA and format
conversion, and preserve guest-visible writes and invalidation. Dropping the
intermediate/history state is not an acceptable visual approximation.

Resource usage lists showed copies/barriers but no sampled-resource uses; their
absence is insufficient evidence of an unused texture in this bindless capture.
Explicit pixel binding inspection proves ResourceId::2727 is sampled at draw
38866. It does not prove ResourceId::9994 is used at the two immediately following
draws (15871 listed other resources; 20110 returned none). Do not skip those loads
based on this incomplete usage evidence.

PS E17BECBE8BE65806 has 16 spatial taps (32 sample_d instructions implement paired
signed/unsigned handling), squares/sums RGB, multiplies by captured 1/16, then
sqrt(abs(...)); alpha is averaged. Offsets span approximately -1.498535 through
1.501465. This is a concrete RMS-downsample consumer for a native pass, not a plain
texture blit. Its individual GPU cost is not yet measured, and a cheaper kernel
has no visual/performance qualification yet.

Evidence: `p2/resolve-chain-audit/{inventory,pipelines,chain,overlaps}.json` and
`p2/resolve-chain-consumers/` bindings, constants and disassembly; local replay
scripts `resolve-chain-*.py`. Next design the smallest native resolve-region output
that can preserve partial-update/history behavior, and measure/qualify the
E17 consumer if combining conversion with that pass is cheaper. A direct view
alias is ruled out for this captured chain. P2.1/P2.3/P2.4/P2.5 remain open.
### Native E17 RMS downsample retained at 2x (2026-09-08)

Implemented `fh1_rms_downsample.ps.hlsl` for VS 2C53E1A563484076 (modification 1)
with PS E17BECBE8BE65806 (modification 0x0000400000000001). Admission requires
bindless host render targets and symmetric 2x. Other variants retain existing
behavior; failed native PSO creation uses the established fallback. No native
vertex replacement or resolve/texture-transfer bypass is claimed.

This retains all 16 offsets, signed/unsigned fetch handling, scale-aware sampling,
fetch exponent, original RGB/alpha accumulation order, zero multiplication rule,
and output exponent bias. RGB remains sqrt(abs(weight * sum(sample^2))); alpha
remains weighted sum. This is a faithful native reference, not a reduced-tap effect.

FXC /O3 /WX compilation passes. Native DXBC SHA
98F115605849974C77F19C6ED93C972012E535FCCDC92CC250F98FE457A3A5AC differs from original
702ADD76157BAD64458FD2DB4E8BB69F229A0639FF6D0E7787800BC946248161. Replacement replay
at both matching draws in frame3758 (38866/38901) produced byte-identical complete
RGBA16F attachments: 167,772,160 bytes total, plus 1,536 unchanged post-VS bytes.
This proves that captured workload, not every live input configuration.

Live 2x race capture PID 44052 exited normally. Frame4343 contains two matching
draws, and the bound pixel bytecode matches native SHA 98F11560... (audit event
39980). Corpus diagnostics were disabled for capture. Exact modification gates
are therefore exercised by a real runtime pipeline, not merely inferred.

Clean stationary 2x ABBA completed normally (PIDs 4804/31628/51860/51000). Analyze
CSV frame-time seconds 32-44, process samples 34-46; no concurrent build/replay.
All four end images reviewed: same stopped car/camera, with traffic/NPC variation.

| Run | Median ms | P95 ms | P99 ms | GPU mean ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 16.6145 | 20.625 | 22.849 | 16.667 | 3395.9 |
| B1 | 16.6275 | 20.561 | 23.085 | 16.777 | 3268.6 |
| B2 | 16.2405 | 19.532 | 21.640 | 16.274 | 3301.9 |
| A2 | 16.1650 | 19.359 | 22.517 | 16.097 | 3231.2 |

Mean candidate change: median +0.27%, p95 +0.27%, p99 -1.41%, GPU +0.88%, draws
-0.86%. Process CPU -8.39%, private memory -0.20%, working set -1.05%; do not
attribute these process changes to this pixel shader or claim repeatable CPU/FPS
improvement. Retain as native shader coverage with no material frame-time regression
in this probe. It does not lower the published requirements or retire the full
renderer, texture conversion or shared-memory dependencies.

`tools/check-fh1-rms-downsample.py` passes exact-hash/modification bit-flip,
backend/bindless/scale exclusions and fallback guard checks. Final build passes;
built/staged renderer SHA is identical to the qualified candidate:
7C336D32E78B25DC0357A84DB0D6DF89B93BC5A4063E9C47F1F7E3B8E232AA70. Runtime stays
FCE008D847CD0832BD021B2231BFF7EDDAED7E8DFBECA0A6D780D63E16403BA0.

Evidence: `p2/rms-reference-parity/report.json`, `rms-native-rdc/frame_frame4343.rdc`,
`rms-bound-audit/report.json`, `rms-abba-{a1,b1,b2,a2}/`, `rms-abba-summary.json`,
`rms-candidate-build.log`, `rms-retained-build.log`. Native RMS at 1x, lower-tap
visual/performance qualification, native region/history resolve output and remaining
P2 coverage are still open. P2 is not complete.
### Session-isolated pass ranking revalidation (2026-09-08)

Fixed the pass-ranking tool to require --session, using the same session boundary
selector as texture ranking (`tools/fh1_runtime_log.py`). This prevents rotated-log
merges from mixing different runs even when their submission/record IDs do not
collide. Both tools reject a missing session start. Checks cover cross-session
records, duplicate/conflicting records and timing denominators; both self-tests
pass with the bundled Windows Python. No renderer/binary change.

Re-ranked source frames 2880-3000 in texture-GPU sessions A
20260908T012634Z-p49328 and B 20260908T012716Z-p47172. Corrected files are
`p2/scene-scale-2x-texture-gpu-{a,b}/pass-ranking-{isolated,mapped}.json`.
466/470 observed pass records cover the same three sampled frames. First-draw
identities map to the per-session corpus, not an inferred shader name.

| Span family | First VS / PS | A ms/frame | B ms/frame |
| --- | --- | ---: | ---: |
| 8F17E2B502A6BF62 | A3B9ED5D5C87230E / 93626E75D17576C5 | 0.961195 | 0.975872 |
| ED7F805DBDC5C236 | 1E6883FCCDE1F688 / no PS | 0.775168 | 0.771755 |
| 7C6A3248DE68D142 | 984DBF6AF14DBEBD / 6FDA0F1CDE67D12F | 0.659456 | 0.628053 |

C34795A841E7DEFF / 21B70A5E4C9CFD11 also starts several large spans: A's two
largest such families measure 0.683349/0.657408 ms, while B's largest measures
0.664576 ms. These family populations differ; do not compare their sums as an
isolated shader benchmark. Spans beginning with E17 RMS total 0.130389/0.130731
ms/frame in these pre-native-RMS runs. Texture conversion and other work overlap
these intervals. Existing native shadow/clear paths already cover some leading
first-draw pairs; their whole spans are not costs of those shaders alone.

Earlier clean-CPU sessions were re-ranked independently too. CPU preparation
per sampled frame remains exactly A 2.8722/2.9666/7.2271 ms and B
3.2318/2.9310/5.1102 ms. Family 738B37134E7F4A0C remains 1.452333/0.878567 ms per
sampled frame. Those published preparation figures survive session revalidation;
this does not automatically validate every older merged-log report. Per-session
CSV benchmarks are unaffected by this logging fix.

Next prioritize the larger scene/transfer spans and remaining C347 native
coverage before spending effort on a reduced-tap RMS filter. Individual shader
cost and the complete frame ranking remain unproven. Use, for example:
`python tools/rank-fh1-pass-samples.py LOG --session SESSION --first-frame 2880 --last-frame 3000`.
P2 remains open; retained renderer is still 7C336D32... with native RMS at 2x.
## P2 manual-session cost triage (2026-09-09)

See DISCOVERY_FINDINGS_2026-09-08.md, section P2 cost triage, for session-isolated
pass/texture rankings of all six marker windows and exact source-frame ranges.
Observed texture conversion/copy averages remain1.01-1.22ms/sampleframe. The
Outpost and highway pass averages are dominated by one22.590ms753-draw span and
one19.170ms single-draw span respectively. Session-wide medians for those families
are0.590ms(15occurrences) and0.111ms(752occurrences), with second largest1.493/.200ms.
Do not attribute these isolated delays to steady shader cost or lower quality on
that basis. Next trace should correlate CPU submission, GPU scheduling/residency
and precise span contents. Evidence is under the original manual session folder;
no renderer behavior changed and no P2 item marked complete. P0/P1 remain deferred.
## P2 submission-span diagnostics (2026-09-09)

WPR GPU tracing was attempted after confirming no existing WPR session. Windows
refused profiling privilege (0xc5585011); no ETL was produced, and WPR status was
verified idle afterward. This does not block other P2 work.

Added recording_wall_ns, begin_submission and end_submission to existing sampled
GPU pass records. The clocks bracket host recording of the existing timestamp
span; no queries, waits or rendering admission were added. Wall time includes
waiting/preemption and is neither CPU utilization nor calibrated GPU busy time.
The pass ranker validates complete interval triplets and monotonic submission
order, and reports recording wall totals/maxima and cross-submission span counts.
Old records remain supported. Parser self-tests and the release build passed.

The first recorder run encountered a reused Windows PID. Fixed CSV selection by
snapshotting pre-existing CSV filenames before launch; a regression check rejects
ambiguous new files and excludes the old same-PID file. A following capture used
the previously staged GPU DLL; it is not validation of the new fields. Explicitly
staged/hash-verified rexgpu-fh1.dll EE28210F27F2052B9270FAC83770E9225A5C8F8797131590FC37355DC9CDA380
and reran. Successful evidence: .local/native-renderer/p2/submission-trace/discovery-3,
session20260909T003612Z-p19164, normal exit. All live pass records had valid interval
fields. CSV32-44seconds selected sourceframes3300..3900 step60:1847 pass records,
22 crossed submissions. Largest observed GPU span1.381376ms; largest host recording
interval4.6966ms. Example cross-submission span0508147AE577D6CE frame3300 ran from
submission12011 to12012, with0.353280ms GPU interval and1.6169ms host recording wall.

This verifies cross-submission intervals exist, not that they caused the manual
session's19-22ms outliers. The short run did not reproduce those outliers. Next
marked-area capture can distinguish same-submission from crossing intervals;
GPU residency/preemption still requires further evidence. No performance gain or
renderer dependency retirement claimed; P2 remains active and incomplete.
## RMS downsample retained at 1x (2026-09-09)

Expanded the existing exact RMS admission predicate to symmetric1x/2x, retaining
VS2C53E1A563484076/mod1, PSE17BECBE8BE65806/mod0000400000000001, bindless and host
render-target requirements. Shader code is unchanged; this remains faithful16-tap
RMS, not a cheaper filtering approximation. Unsupported/asymmetric scales and
other shader modifications remain excluded; pipeline creation fallback is intact.

Offline1x parity reused skinned-1x-clean-rdc/frame_frame4052.rdc (original capture
launched at1x), events36859/36894. All41,943,040 attachment bytes and1,536 post-VS
bytes compared exactly; originalPS6706EE6039FBE9A8B83307BE6D1C35941674CBAE3750ACA2AE1660D2E41BD79C
was replaced by nativePS98F115605849974C77F19C6ED93C972012E535FCCDC92CC250F98FE457A3A5AC.
Artifacts: rms-1x-reference-parity.py and report directory under.local/native-renderer/p2.

Live1x race capture PID1144 exited normally with corpusOFF. rms-1x-native-rdc and
rms-1x-bound-audit/report.json confirm2 matching draws at43271/43306, one PSO, with
the native98F11560 pixel bytecode bound (VS stride32,24indices). RMS gate checker
passes bit flips, shader modifications, backend/bindless exclusions, symmetric1x/2x
and all other1..3 scale combinations, and existing fallback presence.

Stationary1x ABBA completed with corpusOFF and no capture/replay/build during the
measurement windows. Timings32-44sec, process34-46sec; end screenshots reviewed,
same location at night with natural NPC/traffic variation. New per-run session
filenames were recorded explicitly to avoid Windows PID reuse ambiguity. Capture
metadata confirms1280x720 guest outputs and matching vehicle positions. logging.ready
scale strings are empty here and were not used as proof of actual scale.

Label/session PID | median ms | p95 ms | p99 ms | GPU ms | draws/frame
A1/p26020 |15.6210|18.251|20.262|15.0506|3137.81
B1/p51444 |15.6700|18.524|19.928|15.3279|3209.52
B2/p32404 |16.6070|20.626|22.068|16.5801|3528.94
A2/p4792  |16.7115|20.644|22.216|16.8867|3576.03
Candidate deltas: median-0.172%,p95+0.656%,p99-1.135%,GPU-0.092%,draws+0.367%,
CPU+0.482%,private+0.165%,working+0.826%. No material regression; no repeatable
speedup or reduced hardware requirement claimed. Retain for native coverage.

Scripts/evidence: rms-1x-abba.ps1, summarize-rms-1x-abba.py, rms-1x-abba-summary.json
and four run directories. BaselineEE28210F... is saved as rms-1x-baseline.dll.
Retained candidate963D7DBB1361F31E67784126D57F2CAFD2493F9DB037BD158CD6DF1F6366656B
is staged at both root and rexglue-artifacts/rexgpu-fh1.dll. All runs exited normally.
P2.1/P2.3/P2.4/P2.5 still have remaining work; B8481x and video CPU upload1x remain
unqualified. Renderer-wide resource ownership and Xenos retirement are not complete.
## Video CPU upload at 1x retained (2026-09-08)

Expanded only the existing video upload admission from symmetric 2x to symmetric
1x/2x for VS 7156CE05C6365E51 / PS 31511D87CC0C94B9. The upload implementation,
CPU ownership check, texture watch and unsupported-layout fallback are unchanged.
The production-body checker passes layout, allocation, ownership, shader-hash and
scale exclusions. Release rexgpu-fh1 build passed (video-upload-1x-build.log).

Three live 1x RenderDoc frames (8129, 8659, 9192), captured with corpus OFF, contain
changing movie content. Every R8 plane matches its preceding placed-footprint
upload buffer: 4,147,200 active bytes total, including padded chroma rows. Source
resource creation confirms D3D12 upload heaps. All three saved movie outputs and
four ABBA title screenshots were inspected. These are sampled visual checks, not
a complete movie playback/timing qualification. Evidence lives under
.local/native-renderer/p2/video-upload-1x-rdc and video-upload-1x-audit-frame_*.

Clean ABBA used the opening-movie/title script at 1x, corpus OFF, with no concurrent
build/capture/replay. CSV window 44-56 seconds excludes scheduled screenshots;
process samples use 46-58 seconds. Each run has 1,440 measured frames, 47 draws and
33 dirty texture loads per frame. All runs exited normally; guest output is
1280x720. Movie position varies slightly between screenshots.

| Run / session PID | Median ms | p95 ms | p99 ms | Mean GPU ms |
| --- | ---: | ---: | ---: | ---: |
| A1 / 45508 | 8.5060 | 10.519 | 11.111 | 5.4801 |
| B1 / 45276 | 8.3260 | 10.526 | 11.130 | 5.6576 |
| B2 / 3832 | 8.3415 | 10.591 | 11.432 | 5.3443 |
| A2 / 51996 | 8.5070 | 10.526 | 11.111 | 5.3106 |

Candidate deltas: median -2.031%, p95 +0.342%, p99 +1.530%, GPU +1.957%,
CPU +1.367%, private memory -0.696%, working set +0.536%. No material regression
in this bounded comparison; retain for upload coverage, with no general gameplay
speedup or lower hardware requirement claim. This does not fix the marked stalls.
Scripts: video-upload-1x-abba.ps1, summarize-video-upload-1x-abba.py; full results:
video-upload-1x-abba-summary.json and four run directories, with exact session names.

Baseline 963D7DBB1361F31E67784126D57F2CAFD2493F9DB037BD158CD6DF1F6366656B
is preserved as video-upload-1x-baseline.dll. Retained candidate
E601F4868EB2B434380CC3E40AA918A38C2DB2E471C354C8BD2E7EB584E029B2
is video-upload-1x-candidate.dll, staged at root and rexglue-artifacts/rexgpu-fh1.dll.
This supersedes the earlier statement that video CPU upload at 1x is unqualified.
Other layouts/scales, B848 at 1x, broader resource ownership, marked-stall attribution
and remaining P2 coverage are unfinished. Full Xenos renderer retirement remains P3.
## Single-range upload preparation experiment (2026-09-08, not retained)

Traced RequestTextures through PrepareTextureLoad/CommitPreparedTextureLoad and
SharedMemory::RequestRanges. Single-range callers include vertex/index requests,
memexport preservation and resolve destinations. The retained implementation uses
a temporary vector even for one range. A candidate used a stack pair and span for
count == 1, preserving validation and the shared residency/page/upload body;
multiple-range merging was unchanged. This tests CPU preparation overhead, not
native resource ownership or removal of transfers.

New tools/check-fh1-shared-ranges.py compiles the actual production function and
checks it against an independent requested-page oracle. Candidate and baseline
pass 10,000 randomized cases plus empty, invalid, boundary, overlap and allocation/
upload failure cases. An initial assertion that uploads never duplicate pages was
invalid for both implementations: distinct byte ranges can cover the same page.
The check verifies page coverage without imposing that unsupported invariant.
No change to this separate behavior is proposed here. Release build passed.

Clean 1x stationary gameplay ABBA used CSV seconds 32-44 and process seconds 34-46,
corpus OFF, with screenshots outside the measurement window. All runs exited
normally. Capture metadata shows 1280x720 at effectively the same car location;
this experiment does not claim screenshot parity or motion qualification.

| Run / session PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 / 48340 | 16.4650 | 19.649 | 21.936 | 16.1859 | 3416.19 |
| B1 / 38964 | 16.1390 | 19.551 | 22.377 | 15.9128 | 3386.35 |
| B2 / 45532 | 15.9575 | 18.912 | 22.689 | 15.5982 | 3325.46 |
| A2 / 35240 | 15.8380 | 19.137 | 21.561 | 15.5213 | 3240.40 |

Candidate delta: median -0.639%, p95 -0.833%, p99 +3.607%, GPU -0.618%,
CPU -0.750%, draws +0.829%, private memory +0.833%, working set +0.328%.
No repeatable benefit established; final baseline was fastest and workload drift
is present. Do not retain a performance-only change on this evidence. Restore
shared_memory.cpp byte-for-byte from the pre-experiment snapshot and keep renderer
E601F4868EB2B434380CC3E40AA918A38C2DB2E471C354C8BD2E7EB584E029B2 staged at both paths.
Candidate B35A7EFC9FBE191C71E4DA1A36C1CBE89935E03793A1DD3043C37865D19F4B0D and source
remain isolated as single-range-candidate.dll/.cpp under .local/native-renderer/p2.
Scripts/results: single-range-abba.ps1, summarize-single-range-abba.py,
single-range-abba-summary.json and four run directories. The reusable range checker
remains. No speedup or dependency retirement claimed. Next prioritize measured
scaled-resolve conversion/region ownership, not another allocation micro-optimization.
## Scaled 32-bit conversion reference and offline shader (2026-09-08)

Returned to measured scaled-resolve work after the allocation experiment. Existing
isolated texture samples split roughly 1.13 ms/frame into 0.68 ms conversion and
0.44 ms copy; these overlap pass spans and are not additive with pass rankings.
The 0x1C4E1000 surface contributes roughly 0.076 ms conversion plus 0.060 ms copy
per sampled frame in that probe. No new runtime timing measurement here.

Exported the source and final texture at production-rdc/frame_frame3758.rdc loads
15860/20099/38847 (copies 15862/20101/38849). Each source view is 15,073,280 bytes;
each destination is 2560x1440 R10G10B10A2_TYPELESS, 14,745,600 active bytes.
Constants: flags 297 (tiled 2D, endian 8-in-32, symmetric 2x), guest offset 0,
pitch 1280, size 2560x1440x1, host offset 0 and host pitch 10240.

A CPU reference using the SDK's actual GetTiledOffset2D reproduces all 44,236,800
active destination bytes exactly. For host group = x/4, source byte address is
4*TiledOffset2D((group/2)*4,y/2,1280,2) + ((group%2)*2+y%2)*16 + (x%4)*4,
followed by 32-bit byte reversal. Maximum exclusive source address is 15,065,088,
inside the captured view. This validates both pre-existing and partially updated
contents; it does not permit aliasing the current render target or deleting history.

Added offline fh1_scaled_32bpp_2x.cs.hlsl. It uses the existing buffer source and
scratch destination contract, with fixed 2x addressing and endian conversion.
No runtime admission, PSO registration or build integration exists yet. Captured
GPU shader replacement produces exact destination bytes at all three copies AND
identical source-buffer hashes at all three loads, so prior-history preservation
is checked through the replay. Candidate DXBC SHA256:
1E25FDB2D989BFA93C77B210F9352E7D15F75C498B75B14F6DC999F464E4A7B9.
FXC cs_5_1 /O3 reports about 60 instruction slots versus 126 for the generic shader;
this is not performance evidence. tools/check-fh1-scaled-32bpp.py compiles actual
candidate address/endian expressions, compares against SDK addressing over four
pitches and 1,440 rows, and checks 100,000 byte-swap inputs. It passes.

Local evidence: scaled-region-reference.py, check-scaled-region-reference.py,
scaled-region-shader-parity.py; scaled-region-reference/{report,byte-parity,
shader-parity}.json and exported buffers. The helper uses a bounded captured
contract; it is not a verifier for arbitrary texture layouts or other scales.
Next add exact live admission (2x, tiled 2D, base-only/no mips, 32-bit load type,
endian 2, no forced 3D tiling, valid aligned footprint), verify bound shader and
run clean comparisons before retention. Broader buffer/texture resource ownership
and removal of the scratch copy remain unfinished. Renderer DLL E601F486... is
unchanged and staged at both locations. No gameplay speedup or retirement claimed.

## Scaled 32-bit conversion live qualification and retention (2026-09-08)

Integrated an optional native compute PSO and generated FXC header. Admission is
limited to base-only, no mips/packed tail, tiled 2D single-layer unsigned format 7,
endian 2, 1280x720 with pitch 40 (1280 texels), symmetric 2x, 32bpb load shader,
and no forced 3D tiling. Other cases and optional PSO failure use the generic load.
The existing residency, watches, source history, scratch buffer, copy and barriers
are unchanged. The production address/endian/admission checker passes; release
rexgpu-fh1 build passed (scaled-32-build.log). This supersedes offline-only status.

Live race capture PID 52176 exited normally with corpus OFF. In
scaled-32-native-rdc/frame_frame4386.rdc, dispatches 21843/41732 bind native DXBC
1E25FDB2D989BFA93C77B210F9352E7D15F75C498B75B14F6DC999F464E4A7B9.
Both produce 14,745,600-byte textures. Generic replacement is exact on the second
copy but differs on the first. Further inspection establishes differing source
history on that first replay; repeating native also changes it. Therefore the
first naive replacement comparison is invalid as matched-input parity evidence.
An independent CPU address/byte-swap oracle instead matches each native and each
generic output against its OWN captured input: four comparisons, 58,982,400 bytes,
zero mismatches. The earlier three-load reference remains exact matched-source
GPU parity. No claim that fresh-capture history replay is stable. Evidence:
scaled-32-bound-audit/{inventory,cpu-oracle}.json and exported inputs/outputs.

Two clean stationary 2x comparisons ran ABBA then BAAB, with corpus OFF, no
capture/replay/build during measurement, CSV 32-44 seconds, process 34-46 seconds.
All eight runs exited normally. Eight end screenshots reviewed: same Recaro Rush
location, intact rendering, natural NPC/traffic variation. These are sampled scene
checks; broad motion/hardware/other-layout qualification remains unclaimed.

| Run / PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| a1 / 45712 | 17.3630 | 22.124 | 24.991 | 17.9302 | 3401.16 |
| b1 / 50144 | 17.0760 | 21.696 | 24.876 | 17.4406 | 3478.17 |
| b2 / 51300 | 16.7340 | 20.917 | 22.575 | 16.8225 | 3190.48 |
| a2 / 50316 | 16.1465 | 19.361 | 20.803 | 16.1151 | 3160.69 |
| b3 / 37548 | 16.6360 | 20.555 | 22.190 | 16.8376 | 3506.22 |
| a3 / 28280 | 17.1710 | 22.017 | 23.782 | 17.7225 | 3584.03 |
| a4 / 46356 | 17.0690 | 21.677 | 24.922 | 17.6814 | 3616.91 |
| b4 / 47796 | 16.7100 | 20.651 | 23.905 | 17.1782 | 3622.50 |

ABBA deltas: median +0.897%, p95 +2.719%, p99 +3.618%, GPU +0.640%, draws +1.628%.
BAAB deltas: median -2.611%, p95 -5.694%, p99 -5.357%, GPU -3.921%, draws -1.003%.
Combined descriptive deltas (not a speedup proof):
median_frame_ms -0.876%, p95_frame_ms -1.597%, p99_frame_ms -1.007%, mean_gpu_ms -1.685%, mean_draws +0.251%, mean_dirty_loads -0.508%, cpu_seconds_per_wall_second +0.982%, mean_private_mib -0.649%, mean_working_mib -0.257%.

No consistent material regression and no repeatable gain established. Retain this
faithful native conversion for its demonstrated narrow coverage, not for an FPS
claim. Generic conversion remains available for other contracts; the Xenos buffer,
resolve assembly and scratch-copy dependencies are NOT retired by this change.
Broader direct texture output/resource ownership and P2 remain incomplete.

Scripts/results: scaled-32-abba.ps1, scaled-32-baab.ps1, corresponding summaries,
scaled-32-combined-summary.json and eight scaled-32-abba-* directories. Retained DLL
1BCD7340A46FBE2A60CDA6C2A1216CD5B5377C2D1F16DC08D4C97C46F549A982
is saved as scaled-32-candidate.dll and staged at root and rexglue-artifacts.
Baseline E601F486... is saved as scaled-32-baseline.dll. Next target the separate
scratch copy/native texture output while preserving this proven source mapping.


## Direct texture output experiment rejected (2026-09-08)

Tested a direct UAV texture output variant of the qualified 2x 32-bit conversion.
Candidate capability-checks R10G10B10A2_UINT typed UAV stores, allocates an optional
UAV-capable typeless texture (ordinary allocation fallback), and writes packed
channels directly, retaining residency/history/watches and the normal UAV-to-SRV
transition. The candidate bypassed scratch allocation and CopyTextureRegion for
the same narrow contract. No guest-visible write or resolve-history bypass.

Build passed. Live race PID 5984 exited normally; capture
 direct-texture-native-rdc/frame_frame3988.rdc dispatches 19056/38294 bind shader
39BF1D4F7436A20A5400E4FAD9396A6592D39286F55328B7F80988565BD7AD8E
with R10G10B10A2_UINT UAV output. Both 14,745,600-byte results match the independent
source-address/endian oracle exactly (29,491,200 bytes). There are no copies into
the target texture in that capture. direct-texture-bound-audit/byte-parity.json
records the byte evidence. This proves removal of that copy in the candidate,
not a performance win or full resource ownership retirement.

The production-expression checker was expanded to verify direct pixel packing;
candidate eligibility/capability exclusions passed before restoration. Release
build passed. Clean 2x ABBA, corpus OFF, CSV 32-44 seconds, process 34-46 seconds,
all four normal exits:

| Run / PID | Median ms | p95 ms | p99 ms | GPU ms | Draws/frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| a1 / 51424 | 16.6555 | 20.612 | 23.317 | 16.8868 | 3477.74 |
| b1 / 50272 | 16.7570 | 20.514 | 27.075 | 17.0416 | 3444.18 |
| b2 / 46644 | 16.7510 | 20.931 | 24.386 | 16.9051 | 3365.85 |
| a2 / 45232 | 16.5290 | 19.265 | 21.382 | 16.4897 | 3369.85 |

Deltas: median +0.975%, p95 +3.932%, p99 +15.128%, GPU +1.708%, CPU +3.238%,
draws -0.548%, dirty loads -1.272%, private +0.007%, working set +0.020%.
Both candidate p99 values exceed both baseline values. Do not retain: byte
correctness and fewer copies do not excuse frame-time-tail regression. No broad
motion or screenshot qualification is claimed for this rejected candidate.

Restored texture_cache.cpp byte-for-byte and removed the direct PSO member.
Retained 1BCD7340A46FBE2A60CDA6C2A1216CD5B5377C2D1F16DC08D4C97C46F549A982 DLL
is staged at both root and rexglue-artifacts. Candidate
641774F1A3ED037DE5A05DCB7E30B6E0B4EABAAE6E90C186D30E120AA88E1986
and implementation are isolated as direct-texture-candidate.dll/.cpp; benchmark
scripts and summary are direct-texture-abba.ps1 and direct-texture-abba-summary.json.
The HLSL direct-output macro and unused generated header remain as an unbound
prototype. An automatic policy block rejected the cleanup command, so restoration
was completed without file deletion. Default buffer HLSL recompiles to the exact
retained 1E25FDB2... DXBC. The packed-channel checker remains runnable.

P2 resource coverage and transfer reduction remain unfinished. Diagnose actual
direct-write/sampling cost before revisiting this variant; do not infer that a
copy-removal design necessarily reduces GPU time. The prior buffer specialization
remains qualified; this direct-output path is absent from runtime admission.

## Direct-output GPU cost diagnosis (2026-09-08)

Ran four sampled diagnostic probes against retained 1BCD7340... and rejected
641774F1... binaries, in ABBA order. All exited normally; final cleanup restored
retained DLL hashes at root and rexglue-artifacts. No production source changes.
The probes enable existing pass inventory and fh1_discovery_sampling (one frame
in 60). These are attribution runs, not substitutes for clean performance tests.
Sessions: A1 20260909T015101Z-p36648, B1 20260909T015204Z-p17632,
B2 20260909T015306Z-p32716, A2 20260909T015409Z-p53244.

Filtered to 0x1C4E1000, 1280x720, format 7, pitch 1280, unpacked, endian 2,
unsigned. CSV 32-44 seconds supplies approximate source-frame bounds via cumulative
source counts, with boundary rows trimmed. Median conversion per observed load:
A1 0.027648 ms, A2 0.028160 ms; B1/B2 0.047104 ms. Median retained copy intervals:
0.022528/0.021504 ms; direct intervals are zero (adjacent timestamps, no copy).
Observed combined mean per load: A1 0.047443, B1 0.046604, B2 0.047488,
A2 0.047224 ms. Direct writes largely consume the time saved by removing the copy.

Recorded load counts differ: 36/27/24/34 over 12/12/11/12 sampled frames. Do not
credit lower recorded loads as an optimization. Maximum reported dropped timing
samples across these sessions are 21/212/237/171; selected-window loss has not been
fully localized. Consequently the entire per-frame sampled sum is incomplete and
not a total-work performance metric. Ranking scope already excludes lost samples.

Only frames 3780 and 3840 have three recorded target loads in all four runs:

| Run | Conversion ms/frame | Copy interval ms/frame | Combined ms/frame |
| --- | ---: | ---: | ---: |
| A1 | 0.076256 | 0.065024 | 0.141280 |
| B1 | 0.135072 | 0 | 0.135072 |
| B2 | 0.141312 | 0 | 0.141312 |
| A2 | 0.075760 | 0.064512 | 0.140272 |

These are a limited, count-matched subset, not proof of a repeatable benefit or
complete sample coverage. Texture-request CPU totals remain about 2.09-2.15 ms per
sampled CSV row. No diagnosis of the full-frame p99 regression or of subsequent
texture sampling/compression cost is established by these timings.

Evidence under .local/native-renderer/p2: direct-texture-timing.ps1,
summarize-direct-texture-timing.py, direct-texture-timing-summary.json,
direct-texture-timing-matched.json and four direct-texture-timing-* directories
with exact session references and archived runtime logs. The previous clean ABBA
retention rejection stands. Further direct-output work needs cheaper typed writes
or evidence of a larger downstream benefit; deleting a copy alone is insufficient.
Continue P2's broader shader/resource coverage and cost attribution. No performance
or dependency-retirement change is claimed by this diagnostic step.
## Terrain material contract audit and queue correction

Audited retained-renderer capture `p2/scaled-32-native-rdc/frame_frame4386.rdc`
using `p2/terrain-material-contract.py`. All 45 C34795A841E7DEFF /
21B70A5E4C9CFD11 draws use pixel DXBC SHA256
`a7ef74a90c10e1891ac1f7ec72b12ff5620a54c364b665bc5367e2066e490899`.
Every captured draw has b130 false, unsigned fetches 1/2/13, scaled mask 8194,
and identical fetch constants per slot. This exercises cube fetch 1, not the
alternate cube-fetch-2 branch. Bound resources include a 2560x1440 RGBA8 texture
and a 512x512 six-slice RGB10A2 cube resource. The audit's dimension field
reports the underlying resource type, not the shader descriptor view type.
Evidence: `p2/terrain-material-contract/{report,fetch-summary}.json`.

Queue correction: `fh1_terrain_material.ps.hlsl` already implements this pixel
stage. The historical checkpoint records full-pair parity, failed 2x/1x
stationary retention tests, and later paired-draw diagnostics. It is incorrect
to treat the material stage as an unimplemented next replacement. This input
audit supplies no new performance evidence and does not justify re-enabling
it or repeating the unchanged pair benchmark. Revisit only with a materially
changed candidate or newly measured workload. Coverage of the alternate branch
and other resource modes cannot be inferred from these 45 draws.

Production remains disabled for this pair. Both staged renderer DLLs still
hash `1BCD7340A46FBE2A60CDA6C2A1216CD5B5377C2D1F16DC08D4C97C46F549A982`.
No renderer source or binary changed in this audit. P2 remains incomplete.
## RGBA8 scaled-conversion extension: offline proof, live qualification pending

Previous goal turn corrected the terrain queue; this turn tested new resource
coverage. Audited all 129 generic scaled-32 dispatches in retained-renderer
capture `scaled-32-native-rdc/frame_frame4386.rdc`. Four full-resolution RGBA8
loads at events 12430, 16016, 42674 and 43452 use the same flags 297, 1280-pixel
guest pitch and 2560x1440 output contract as the retained RGB10A2 kernel.
The census also includes mip/array/offset and other-endian contracts: it does
not justify enabling the specialization for all 129 dispatches.

Reused the existing kernel without HLSL changes. Offline replacement matches
all four sources and outputs exactly (58,982,400 output bytes). Independent CPU
address/endian checks validate both implementations against their own captured
inputs: eight checks, 117,964,800 output bytes, zero mismatches. Global replay
replacement can affect other dispatches; matching selected input hashes and
independent checks are essential to this bounded claim. Evidence/scripts:
`p2/scaled-32-coverage{.py,/report.json}` and
`p2/scaled-32-rgba-parity{.py,/report.json,/cpu-oracle.json}`.

Candidate only broadens the existing exact admission predicate from format 7
to formats 6/7; dimensions, endian, 2x, base-only, unpacked, unsigned and optional
PSO fallback remain unchanged. DLL SHA256
`07123E1FF515C600EE187DBC9EE2D22C1E13D2891443A7620AA7574E4D897FE6`.
Candidate source/binary/check snapshot: `p2/scaled-rgba-candidate.*` and
`p2/scaled-rgba-candidate-check.py` (archived tools script, root resolution must
be adjusted if executing from its archive location). Build and admission/address
checker passed before testing.

Live race capture PID11548 failed at capture trigger with device loss and
exit -1073740791; no RDC was produced. Crash id
`pscrash-v1-b2810c7ffe5a180ec91b`. No attribution to the candidate versus capture
instrumentation is established. This supplies no live-binding proof. Do not
claim the format extension is qualified from the offline replay alone.

Clean stationary 2x ABBA completed normally: A1 PID50264, B1 PID27660,
B2 PID24028, A2 PID11160. Candidate changes: median -1.0687%, p95 +0.7219%,
p99 +1.2990%, mean GPU -1.2145%, CPU +4.3637%, draws -2.2200%, dirty loads
-2.3895%, private memory -0.2772%, working memory -0.1564%. No repeatable speedup
established; traffic/workload differs. All four end screenshots inspected:
stationary Recaro event approach, intact scene/UI, differing traffic/NPC poses.
No motion or broad-scene qualification claimed. Evidence: `scaled-rgba-abba-*`,
`scaled-rgba-abba-summary.json`; helper `summarize-scaled-rgba-abba.py`.

Extension remains unqualified and disabled. Production texture_cache.cpp restored
bytewise, production checker restored and passed, release renderer rebuilt.
Both renderer paths restored to retained
`1BCD7340A46FBE2A60CDA6C2A1216CD5B5377C2D1F16DC08D4C97C46F549A982`.
Next resolve live-binding/capture qualification for this existing candidate;
do not reimplement the kernel or interpret this batch as a speedup. P2 remains
active and incomplete.
## RGBA8 live qualification and retention decision

Earlier stationary capture succeeds: candidate PID36164 exited normally and
produced `p2/scaled-rgba-stationary-rdc/frame_frame3055.rdc`. This avoids the
failed later race capture; it does not diagnose or fix that capture failure.
`scaled-rgba-live-audit.py` verifies the native shader bytecode on all eight
specialized dispatches, including four RGBA8 loads (6877,10496,29303,30119).
All four RGBA8 loads have matching native/reference input and output hashes
and stable native replays: 58,982,400 exact output bytes. Two RGB10A2 history
states vary on replay, as in earlier audits. Independent CPU checks validate
all eight loads against each implementation's own source: 16 checks,
235,929,600 bytes, zero mismatches. Reports under `p2/scaled-rgba-live-audit/`.
This completes the previously missing captured live-binding check for RGBA8.

Reversed BAAB completed normally: B3 PID30336, A3 PID46448, A4 PID51448,
B4 PID36828. Changes: median -0.2395%, p95 -0.5005%, p99 +6.5930%, GPU
-0.5079%, CPU +0.8046%, draws -2.8381%, dirty loads +1.3717%, private memory
+0.0383%, working memory +1.0284%. All four end screenshots inspected; scene
and UI intact, traffic and NPC poses differ. No motion qualification claimed.

Across eight runs (equal weighting of per-run metrics): median -0.6533%,
p95 +0.1048%, p99 +3.9489%, GPU -0.8595%, CPU +2.5739%, draws -2.5355%.
Frame tails increase in both orderings despite fewer draws. This does not
isolate shader causation, but supplies insufficient evidence of no material
regression; the extension is NOT retained. Do not repeat the unchanged batch
or enable it solely from exact bytes. A matched per-dispatch measurement or
a materially cheaper conversion is needed before reconsidering it.
Evidence: `scaled-rgba-baab-summary.json`, `scaled-rgba-combined-summary.json`,
`scaled-rgba-abba-{b3,a3,a4,b4}/`, scripts `scaled-rgba-baab.ps1` and
`summarize-scaled-rgba-baab.py`.

Production source remains restored to format-7-only admission. Both renderer
DLLs remain `1BCD7340A46FBE2A60CDA6C2A1216CD5B5377C2D1F16DC08D4C97C46F549A982`.
No game/replay remains running. Candidate and exact live evidence are preserved.
P2.1 still needs stronger matched cost attribution; P2 remains incomplete.
## Timing-loss attribution and bounded capacity fix

Previous turn completed RGBA8 live qualification and rejected retention. This
turn fixes a measurement limitation before another conversion experiment.
The existing total conflated busy slots, capacity exhaustion, interrupted
texture endpoints and invalid texture records; invalid pass records were
silently skipped. Added four cumulative reason counters to the existing log
cadence and now count invalid pass records. These are loss EVENTS, not unique
samples: interruption and subsequent invalid retirement can count twice.
No query waits or rendering-path changes were introduced.

Compiled production-method checks now exercise capacity versus busy slots,
interrupted frame/submission guards and missing-family/reversed-timestamp pass
rejection. `tools/check-fh1-texture-timing.py --compiler
.local/toolchain/llvm-20.1.8/bin/clang++.exe` passes. Texture ranking exposes the
latest session-wide reason report, with null for older/missing reports, rejects
invalid/decreasing counts, and explicitly does not localize cumulative losses
to requested frames. `tools/rank-fh1-texture-samples.py --self-test` passes.

At original capacity256, diagnostic PID31792 exited normally and logged 83
capacity losses, zero busy/interrupted/invalid events. Evidence:
`p2/timing-loss-probe/`. This identifies actual exhaustion rather than assuming
it from the old aggregate. Raised the existing bounded capacity to512; no
unbounded allocation or new scheduling/wait mechanism. Diagnostic PID46124,
session `20260909T023706Z-p46124`, exited normally. All observed reason reports
are zero; maximum emitted slot-record index267 proves the old bound was
insufficient. 8,329 unique pass/texture records were recovered across the session.
This one probe does not prove512 sufficient for every scene; overflow remains
explicit. Evidence `p2/timing-capacity-probe/` and associated probe/summarizer.

Sampled gameplay source frames3240..3840 step60 (11 frames, approximate mapping
from 32-44 CSV seconds, excludes screenshot intervals): retained RGB10A2
0x1C4E1000 has33 loads, mean conversion0.075782ms/frame plus copy0.064791ms/frame;
median conversion0.027648ms/load. Full-resolution RGBA8 addresses1DAC5000 and
1CE2D000 each have22 loads and total conversion+copy0.112640 and0.093172ms/frame.
They total0.205812ms/frame in this probe, not an established optimization gain.
Texture request CPU averages2.1783ms per sampled CSV row. These spans overlap
pass spans and exclude preparation before conversion; do not sum them with pass
cost or treat them as all texture activity. Ranking/report:
`timing-capacity-probe/texture-ranking.json`, `timing-capacity-summary.json`.

NEW retained renderer DLL (both staged paths) SHA256:
`2FD4B204410C644AA12466EA9A7B79C76777C0E31E8AB74F64F098BF422EA1AF`.
Release build and normal diagnostic run pass. RGBA8 extension and direct-output
candidate remain disabled; format7 specialization remains intact. This retains
measurement correctness/coverage, not an FPS improvement. Next use the improved
sample coverage for matched cost attribution; P2 remains incomplete.
## Resolution-sensitive pass cost with complete observed timing reports

Previous turn retained the timing-capacity fix. New 1x diagnostic run PID7172,
session20260909T024055Z-p7172, exits normally with zero reported timing losses.
Compared against preceding 2x PID46124 using the same retained2FD4B204 renderer,
stationary AppData location and32-44s CSV window. Both end images inspected:
same Recaro approach, correct1280x720/2560x1440 output; NPC/traffic differs.
This is one diagnostic run per scale, not a repeated clean performance A/B.

| Metric | 1x | 2x |
| --- | ---: | ---: |
| Median / p95 / p99 frame ms | 16.373 /20.730 /22.672 |16.807 /21.214 /24.133 |
| Mean guest GPU ms |15.595 |17.197 |
| CPU seconds/wall second |3.112 |3.240 |
| Mean draws |3634.22 |3668.88 |
| Private MiB |2555.19 |4748.06 |
| Working MiB |1992.88 |1991.82 |

Pass-ranking windows contain12 sampled1x frames and11 sampled2x frames, matched
by approximate elapsed gameplay window rather than equal source frame numbers.
All expected sampled frames are present, with1921/1889 unique pass records and
zero reported loss reasons. `compare-resolution-costs.py` joins shared families
and records draw/occurrence counts; existing ranker self-test passes.

| Pass family | GPU ms/frame1x | GPU ms/frame2x | Draws/frame1x /2x |
| --- | ---: | ---: | ---: |
|53B2C36308FCD219 |1.1481 |1.2762 |811.08 /811.18 |
|8F17E2B502A6BF62 |0.5429 |0.9658 |3 /3 |
|ED7F805DBDC5C236 |0.1956 |0.7766 |2 /2 |
|4C3611D703B31EDE |0.4782 |0.4800 |26 /26 |
|57294A9E0311F163 |0.0969 |0.3975 |1 /1 |

The largest geometry span's CPU preparation is0.7012/0.6796ms per sampled frame;
its811 draws barely change with resolution. Single-clear spans ED7F/5729 scale
about4x, but are NOT isolated clear API costs. Revalidated current source:
D3D12RenderTargetCache::Update calls PerformTransfersAndResolveClears before the
new draw's pass observation; preparation transfers can land inside the previous
pass's timestamp interval. Historical transfer-cutout audit already identified
this boundary problem and only8% geometric overlap for full-component clears.
Do not infer that reducing clear quality or cutting scene effects would recover
these whole spans; geometry overlap alone is not GPU-cost attribution.

NEXT concrete P2.1 step: isolate GPU time for actual render-target ownership
transfers/resolve clears at PerformTransfersAndResolveClears (both Update and
resolve-clear callers), preserving bounded sampling, initialization, retirement
and explicit losses. Reuse existing query machinery; do not change transfer
scheduling or omit preserved depth/stencil components on this evidence. This
should distinguish transfer work from the already-native clear operation before
any cutout/simplification experiment. P2.4 remains conditional on that attribution.
Evidence: `p2/timing-1x-probe/`, both `pass-ranking.json` files,
`p2/resolution-cost-comparison.json`, `p2/compare-resolution-costs.py`.
No renderer source/binary changed; retained2FD4B204 remains staged. P2 incomplete.
## Direct render-target transfer timing retained

Previous turn provided1x/2x pass comparison and identified ambiguous pass
boundaries. Added timing inside PerformTransfersAndResolveClears, covering both
Update and resolve-clear callers. The existing bounded query token is now named
Fh1GpuWorkTiming and shared with texture loads; existing texture endpoints are
unchanged. Only sampled frames scan transfer lists; empty/no-clear calls are
skipped. Normal and early exits close the interval. Submission interruption
invalidates the sample through existing guards, without waiting or changing
transfer scheduling, bindings, barriers, writes or fallback behavior.

Records identify requested transfer descriptor count and whether resolve-clear
arguments are present. Counts are not actual GPU draws, rectangles or transferred
bytes. The GPU interval includes host-depth stores, ownership transfers, barriers
and any resolve clears performed by this function; it is not just a clear API
cost or a GPU busy-time measurement. These intervals overlap the old pass spans.

Release build passes. Production-method checker now covers empty calls,
transfer-only and clear-only allocation, successful completion and interrupted
submission retirement, in addition to previous bounds/loss tests. Texture/pass
ranking self-tests also pass. Normal sampled gameplay runs:2x PID53088/session
20260909T024854Z-p53088,1x PID2512/session20260909T025038Z-p2512. Both report zero
busy/capacity/interrupted/invalid losses. No RenderDoc required for this timing.

32-44s CSV gameplay windows,11 sampled source frames each:

| Function-call category | 1x calls / mean GPU ms per sampled frame | 2x calls / mean GPU ms per sampled frame |
| --- | ---: | ---: |
| No resolve-clear arguments |420 /1.435183 |421 /5.683200 |
| Resolve-clear arguments present |937 /0.202007 |939 /0.280204 |
| All selected calls |1357 /1.637190 |1360 /5.963404 |

This near4x increase in ordinary transfer intervals, with nearly equal call
counts, is stronger attribution than the prior single-clear pass association.
It identifies substantial resolution-sensitive transfer work; it does not prove
all that time is removable or isolate every destination/source/transfer shader.
One diagnostic run per scale, same stationary fixture, not an FPS benchmark or
an exact matched-input comparison. Keep effects simplification conditional;
prioritize ownership transfer analysis before quality reductions or another
~0.2ms texture conversion experiment.

Evidence and reproducer: `p2/transfer-timing-probe/`,
`p2/transfer-timing-1x-probe/`, `p2/summarize-transfer-timing.py`,
`p2/transfer-timing-summary.json`; per-run `transfer-ranking.json` includes
largest calls and frame totals. Next map dominant calls to actual source/target
contracts and overlap before attempting a narrower transfer/cutout replacement;
preserve uncleared pixels and independent depth/stencil components.

NEW retained renderer hash (both staged paths):
`87B79AABEC3F06326DF616DC02CCC3588E1CFFEFEE3A4E2B3590A17655EA23B5`.
Instrumentation retained, no performance improvement or dependency removal
claimed. RGBA8 extension/direct output remain disabled. P2 stays incomplete.
## Dominant transfer source/destination contract audit

Previous turn retained direct GPU transfer timing. Temporary audit tags each
call by the complete ordered source/destination/host-depth-source/tile-range
list, plus target keys and call kind. Metadata logging precedes the interval.
Resolve-clear signatures are excluded from this contract ranking because clear
values/rectangle were not hashed. The parser rejects differing entries under
one signature/index and requires every timed ordinary-transfer descriptor to
have matching metadata. No first-entry attribution for mixed lists.

2x PID1376, normal exit, zero reported losses.11 sampled gameplay frames from
32-44s CSV window;35 distinct ordinary transfer lists. Their audit intervals sum
5.663648ms/frame, consistent in scale with earlier5.6832ms ordinary intervals,
but verbose logging can perturb timings. This is contract discovery, not a
new controlled performance result. `p2/transfer-contract-probe/contracts.json`
contains every list and decoded key. `summarize-transfer-contracts.py` reproduces
it from the archived session and CSV. Diagnostic source snapshots are
`transfer-contract-audit-{rt,cp}.cpp` and `transfer-contract-audit-cp.h`.

Largest list E2950943A57676F6:44calls/11frames,1.572119ms/frame. Two ranges
[720,2048) and[0,720), source00206AD0 -> destination00306AD0. Both are D24S8,
base tile720, pitch13 tiles at32bpp; source1xMSAA, destination4xMSAA. No separate
host-depth preservation source. This covers all2048 EDRAM tiles via wraparound.
Reverse list44DCDDC7E394EE36:22calls,0.408483ms/frame, ranges[1552,2048) and
[0,720), same keys reversed. Equal format does NOT imply identical memory or
MSAA sample layout, and neither depth nor stencil may be dropped.

Next largest1AE36768E7E8D89C:11calls,0.406342ms/frame, four sources (RGB10 float
and floating depth with differing base/pitch) to D24S8 key00308000. This mixed
conversion must not be mistaken for a same-format copy. Other lists retain
independent host-depth sources and require preservation of both representations.

NEXT inspect the dominant D24S8 1x->4x transfer's actual bound shader and sample
mapping, including native stencil-reference-output availability; the source
already has an optional native stencil-output path, so do not reimplement it
without checking live selection. Prioritize this measured contract over the
rejected RGBA8 conversion. No transfer skipping or MSAA quality change admitted.

All three verbose-audit source files restored bytewise to retained backups;
rebuilt normal renderer. Both DLLs remain87B79AABEC3F06326DF616DC02CCC3588E1CFFEFEE3A4E2B3590A17655EA23B5.
No game remains running. No new performance gain/dependency retirement claimed;
P2 active/incomplete.
Restored-source rebuild produced BF0F9A799577294B56844B779ABE74DF20B924D6CDF5D53F5730E4069022A84E despite byte-identical restoration of the three audit files; no binary reproducibility claim. Saved as transfer-contract-restored-rebuild.dll. Both staged paths explicitly restaged from the validated87B79AAB binary and hashes verified.

## D24S8 depth/stencil addressing experiment (2026-09-09 UTC)

Captured `scaled-rgba-stationary-rdc/frame_frame3055.rdc` (earlier RGBA
candidate; unchanged RT transfer implementation) establishes the dominant
1xMSAA -> 4xMSAA copy: event711 depth plus events718,721,724,727,730,733,736,739
stencil masks1,2,4,8,16,32,64,128. Source16324 is2080x5056 single-sampled
D24S8, destination16433 is1040x2528 four-sampled D24S8. Every draw has address
constant13325 (source/destination pitch13, base delta0). Depth shader SHA256
d1649a246e53361978acfcbbb194dc575c2b984d8a569ecc9248ebfe4f2b9c57;
stencil76574cb4f3631908a0fa04fe701585bc9dfe20e73499f02594a9a91211c5cbdc.
Audits `depth-transfer-{shader,stencil,constants}-audit.py` retain reports/DXBC.

Native stencil-reference output already defaults on in source. Standalone
D3D12 feature query on the NVIDIA10de:2704 adapter returns S_OK and
PSSpecifiedStencilRefSupported=0. WARP returns1. This explains why the existing
hardware-feature-gated path cannot replace the eight stencil-bit passes on
this adapter; do not force unsupported SV_StencilRef. Evidence:
`query-stencil-feature.cpp`, `stencil-feature.txt` under `.local/native-renderer/p2`.

Tested a bounded 2x shader address shortcut: for constant13325 and valid
unwrapped destination tiles, sourceXY=2*destinationXY+sampleXY. Generic mapping
remains for other addresses, coordinates beyond pitch, and the padded final
row's EDRAM wrap. Both depth and stencil preserve original loads and writes.
`check-depth-transfer-fast.cpp` checks11,411,780 coordinates including padded
boundaries;10,485,760 fast-path samples match. FXC ps_5_1/O3 shaders compile
without warnings. Replay replacement compares all four samples after each of
nine draws:378,593,280 bytes identical; repeated original readback stable.
`depth-transfer-fast-parity/report.json` preserves hashes. This is one captured
transfer group, not broad scene/motion qualification. Replay FetchCounters
returned no matching timing records; no zero-cost inference or replay speedup.

Temporary runtime candidate restricted to D24S8 depth-to-depth/depth-to-stencil,
1xMSAA->4xMSAA,2x resolution, native stencil reference unavailable. Eight clean
stationary runs, orderABBA thenBAAB, all normal exit. Candidate
BD00A54C5147C31CDC7062A9B7568FC332AD3E60A99B7B8F28B4B7ADD7196E3C;
baseline87B79AABEC3F06326DF616DC02CCC3588E1CFFEFEE3A4E2B3590A17655EA23B5.
32-44s frame window,34-46s process window. Candidate changes:

| Order | Median frame | p95 | p99 | Mean GPU | Draw count |
| --- | ---: | ---: | ---: | ---: | ---: |
| ABBA | +0.797% | +3.576% | +13.468% | +1.946% | +0.119% |
| BAAB | +1.325% | +2.780% | +5.599% | +2.561% | +3.491% |
| Combined | +1.060% | +3.178% | +9.607% | +2.253% | +1.802% |

Combined CPU utilization -5.264%; memory effectively unchanged. Traffic/draw
counts differ, so these results do not prove isolated shader causality. They
provide no qualifying performance gain and fail retention. All eight end
screens inspected: consistent scene/geometry, varying traffic. No motion
qualification claimed. `summarize-depth-transfer-fast.py` reproduces the report;
`depth-transfer-fast-abba-*` retain session/CSV/process evidence. Candidate
HLSL/DXBC/source/DLL remain local experimental artifacts only.

REJECTED retention. Production RT source restored bytewise. Found stale
command_processor object from the previous temporary signature audit: linking
the new candidate exposed an undefined two-argument transfer timing function.
Refreshing restored header/source timestamps and rebuilding fixes it; a new
baseline rebuild exactly reproduces87B79AAB..., resolving the earlier BF0F9A...
binary discrepancy. Both staged DLL paths verified87B79AAB...; no game/replay
left running. No performance improvement or dependency retirement claimed.

NEXT: investigate reducing actual transfer/stencil work with proven ownership
and data requirements, or rank the next transfer contract. Do not repeat this
unchanged address-only candidate or enable unsupported stencil-reference output.
Original user-marked area slowdown remains unresolved; P2 goal stays active.

## Stencil-content and writer audit (2026-09-09 UTC)

Follow-up to the rejected address-only shortcut: all source stencil bytes are
zero at the four dominant D24S8 transfer depth draws711,2012,2991,3299 in the
same captured frame. Destination stencil remains zero through the first copy's
nine depth/stencil draws. Readback includes the full resource/padding and four
destination samples. `transfer-stencil-content-audit.py` and its report retain
per-byte histograms and hashes; no production shader changed.

Validated readback interpretation with an intentionally inverted stencil-bit
shader in replay only. At event718 it writes bit0 to2,621,440 pixels per sample
(10,485,760 total);7,680 padded pixels/sample remain0. The high byte changes
from0 to1, confirming D24S8 readback includes stencil and the original zero
histogram is meaningful. `stencil-readback-probe.{hlsl,dxbc,py}` and report
preserve this positive control. No game renderer uses this diagnostic shader.

Audited441 distinct graphics PSOs:227 guest variants;174 stencil-enabled guest
variants account for2,916 draws. Representative dynamic references include
21,6,15 and0 with replacement operations/write mask255. Dynamic references
are sampled at the representative draw, not proven invariant per PSO. These
states contradict any global claim that FH1 does not use stencil. Evidence:
`stencil-writer-state.py`, `stencil-writer-state/{report,summary}.json`.

Source trace: ChangeOwnership is already shared by draw and resolve-clear
paths. It merges ranges and preserves separate host-depth ownership but does
not track stencil values. Color/depth reinterpretation and partial clear
cutouts can preserve old bytes. A format/base whitelist or capture-zero
assumption is insufficient for removing stencil draws.

NEXT: attribute the zero-valued transfer ranges to their clears/writers and
measure whether conservative per-range known-value tracking admits these
copies. If tracked, invalidate on uncertain writes/color aliasing and preserve
partial tile contents; zero must be proven at runtime. GPU-side detection is
an alternative only if tracking cannot admit the measured case economically.
No stencil copies skipped, no performance gain claimed, original slowdown
unresolved. Production remains validated87B79AAB; goal active. This turn adds
content/positive-control/writer evidence, not another unchanged benchmark.

## Dominant stencil transfer provenance (2026-09-09 UTC)

Audited draws through event3400 whose actual depth attachment is16324 or16433:
518 draws total,374 guest draws, all374 with stencil disabled. The remaining
144 are transfer draws. This narrows the prior whole-frame174 stencil-enabled
PSOs: those are not proof of writes to these particular two resources during
this interval. `stencil-transfer-provenance.py` and report/summary retain actual
per-draw attachment and dynamic stencil state; no representative-PSO assumption.

31 clear actions also decoded. Source16324 event530 clears stencil0 over ten
rectangles covering the2048-tile domain; destination16433 event704 covers the
same domain in five4xMSAA rectangles. Later full destination stencil clears at
2005,2984,3292; source partial clears at1958,3244 join previous covered regions.
Depth-only clears carry arbitrary stencil argument21 or0 but MUST NOT mark
stencil known: their ClearFlags is1. ClearFlags2 actually clears stencil.
Repeated structured array child names are preserved as a list (initial decoder
collapsed these names; independently reread clears repair the final report and
assert every multi-rectangle count). Float depth values intentionally omitted.

Crucial limitation: subsequent transfer draws repopulate cleared stencil, and
source16324 receives both depth-source and color-source conversions before711.
Therefore clear coverage plus disabled guest stencil is not sufficient to prove
zero after incoming transfers. Resource creation explicitly uses zeroed
D3D12_HEAP_FLAG_NONE, but cross-format writes still invalidate a simple
per-resource zero flag. No safe runtime bypass established yet.

Next experiment: GPU-side source-stencil detection for the measured transfer
contract, keeping all original draws when any required bit is present. Reuse
existing transfer descriptors and preserve barriers; evaluate reduction cost
before retention. Deferred command list currently has no predication or
ExecuteIndirect wrapper, so account for the small command plumbing required.
Do not install a format whitelist or skip based on this capture's zero values.
Source/destination bounds, sample mapping and wrapped tiles remain mandatory.
No production edits/performance gain claimed; retained87B79AAB unchanged.

## Disabled stencil-predication experiment (2026-09-09 UTC)

Implemented `fh1_stencil_predication=false` experiment. Reuses existing stencil
transfer shader/root descriptors/rectangles/sample mapping with mask255 and a
read-only PSO (ninth cached stencil pipeline; depth/stencil writes disabled).
One binary occlusion query counts samples surviving the shader's discard.
Resolve to an8-byte GPU predicate; COPY_DEST/PREDICATION transitions; original
eight stencil draws execute only if nonzero. Explicitly clear predication
before later work. No compute shader, CPU readback or capture-based whitelist.
Current admission is depth-to-stencil D24S8,1xMSAA->4xMSAA, with existing native
stencil-reference path unavailable. Both supported resolution scales follow
existing generated addressing, but only2x tested so far. Creation failure
falls back to original copies. Query/predicate resources released with cache.

Added deferred SetPredication command and public active-host-query guard.
If either legacy guest query or modern ZPD segment is active, do not run this
experiment: extra query draw or skipped draws could affect guest counts.
Current cvar checked at invocation too, so disabling it stops predication even
if the optional pipeline was already created. Nontrivial command serialization,
64-bit offset, enable/disable and both query guard cases compile/run via
`tools/check-fh1-stencil-predication.py --compiler <clang++>`; passed. Renderer
build passes. No changes to guest query values or synchronization intended;
broader active-query gameplay qualification remains outstanding.

Captured enabled2x PID39504, normal exit. Candidate DLL
ADE06550F0F6989BBE94857072D89E3B6D090306F71627999410B6FEB736FEC8;
`stencil-predicate-rdc/frame_frame3047.rdc`. Four query draws683,1323,2028,2145
use address13325/mask255. All source stencil bytes zero (42,065,920 bytes read
per source occurrence); each resolved predicate0. Eight subsequent draws per
query use skipIfZero=true and predication is explicitly cleared afterward.
Read-only query state asserted. `stencil-predicate-{audit,results}.py` and reports
retain captured bindings/predicate bytes. End screenshot inspected: expected
stationary scene; this is not broad screenshot/motion or performance qualification.

Replay positive control replaces shared query/copy shader with a test shader
that passes every valid MSAA sample. Predicate becomes1, all eight copies
execute and stencil becomes255 over2,621,440 pixels/sample, while7,680 padded
pixels/sample remain0. Four samples checked. `stencil-predicate-positive` files
and report retain this synthetic control; it validates nonzero predicate/copy
execution, not production nonzero-input fidelity across arbitrary scenes.

After adding the invocation-time cvar check, current built candidate is
B709E04BF7B66A9A3AE2F8E9445C5A72AC4A9E6CB3371ECDC73395D824F0DAA4,
saved as `stencil-predicate-candidate-current.dll`; compiled checker rerun passed.
The captured ADE... build differs only by that guard. Current source contains
the disabled experiment. Both staged game/artifact DLLs explicitly restored
to validated87B79AAB...; no game/replay running. Prior source snapshots under
`stencil-predicate-before-*` allow reverting just this experiment.

NEXT: matched enabled/disabled gameplay cost tests, zero/nonzero source output
qualification and1x/motion coverage before retention. The extra query and GPU
predicate dependency may cost more than the eight copies it removes; no FPS
improvement, completed slowdown fix, or dependency retirement claimed yet.
Do not enable by default without the backlog's complete acceptance evidence.

## Stencil-predication retention test: not retained (2026-09-09 UTC)

Eight clean2x runs ABBA thenBAAB; A validated87B79AAB, B candidateB709E04B with
`--fh1_stencil_predication=true`. All normal exit. Existing stationary fixture,
32-44s frame window/34-46s process window; no capture/build/profiling workload
during benchmark. `stencil-predicate-abba.ps1`, per-run session/CSV/process files
and `summarize-stencil-predicate.py` retain reproducible evidence.

| Order | Median frame | p95 | p99 | Mean GPU | Draw count |
| --- | ---: | ---: | ---: | ---: | ---: |
| ABBA | +2.180% | +6.913% | +14.868% | +4.126% | +2.902% |
| BAAB | -3.272% | -6.181% | -6.738% | -4.422% | -2.697% |
| Combined | -0.553% | +0.353% | +3.829% | -0.173% | +0.096% |

Combined CPU -1.145%, private memory -0.138%, working memory -0.215%. Opposing
orders and draw-count drift prevent attributing changes cleanly to predication.
There is no repeatable qualifying GPU/frame-tail benefit; this is a failure
to establish retention evidence, not proof the query intrinsically regresses.
Do not repeat the same unchanged stationary benchmark and call it new evidence.

All eight end screenshots inspected. Traffic and NPC poses vary. Baseline a3
has a conspicuous red region across the rear window, absent in the other end
screens; record as a baseline artifact, not a candidate-caused regression or a
broad visual pass. P0/P1 investigation remains deferred. Contact sheet:
`stencil-predicate-ends.png`. Candidate1x, broad motion, and production nonzero
source fidelity were not completed because the performance gate failed.

Removed the disabled experiment from runtime source: restored five files
bytewise from `stencil-predicate-before-*`, archived candidate versions as
`stencil-predicate-rejected-*`. Removed its tools checker after archiving it as
`check-fh1-stencil-predication-rejected.py` (its repo-root discovery needs
adjustment if run from the archive). The checker passed before restoration;
it should not be run against the restored renderer that lacks those methods.
No unused predication wrapper, query objects, extra pipeline slot or cvar left
in production. Restored-source build succeeds and exactly reproduces87B79AAB.
Both staged DLL paths verified87B79AAB; no game/replay remains running.

NEXT: strengthen isolated transfer-cost measurement or qualify a different
measured resource/scene contract. Query-based zero detection and address-only
shortcut are both unretained; do not mistake byte/readback correctness for a
performance benefit. P2 remains incomplete and original area slowdown unresolved.

## Replay counter failure diagnosed (2026-09-09 UTC)

Investigated empty FetchCounters results rather than repeating shader or live
benchmarks. `replay-counter-diagnostic.py` confirms EventGPUDuration is advertised
(counter1), yet entire-frame collection returns zero records both initially
and after selecting draw711. This is not an event-filter mismatch.

`replay-counter-log.py` archives the actual diagnostic log. RenderDoc1.45
`d3d12_counters.cpp:662` reports D3D12 counters require Windows Developer Mode;
replay_controller then reports a fatal device-lost state with that same reason.
Therefore subsequent results from that controller cannot be treated as usable
measurements. This was not a renderer crash, measured zero cost, missing event,
or evidence of transfer performance. The separate missing Nsight Perf SDK
notice does not establish the cause of generic duration failure; the explicit
Developer Mode diagnostic does. Registry read confirms
HKLM/SOFTWARE/Microsoft/Windows/CurrentVersion/AppModelUnlock/
AllowDevelopmentWithoutDevLicense=0.

Added local `replay-counter-preflight.py`: read-only Developer Mode check before
opening a replay device, and fail collection on empty records. Executed here:
reports developer_mode_enabled=false and stops before device creation. No OS
settings changed or SDK installed. Asked user whether they want to enable
Developer Mode; answer pending at this checkpoint. Existing native GPU timing
still works, so this capability limitation does not block the whole P2 goal.

NEXT if enabled: reopen a fresh controller, verify complete nonempty duration
records, then use the same captured workload for isolated transfer-cost
screening. Capture replay GPU timing does not replace end-to-end CPU, memory,
1x/2x or gameplay/motion qualification. If left off, continue native per-transfer
timestamps with explicit workload/contract matching. No unchanged benchmark
repetition. Production remains validated87B79AAB, no game/replay running.

## Reusable native transfer-contract ranking (2026-09-09 UTC)

Added `tools/rank-fh1-transfer-contracts.py`, reusing the existing session-log
reader. Explicit session and source frames required. Rejects missing sampled
frames, conflicting duplicates, missing/extra contract entries, invalid tile
ranges and decreasing loss counters. Deduplicates identical records and ranks
full ordered transfer lists, never attributing a whole interval to its first
source. Resolve-clear calls are excluded because the older audit signatures
omit clear rectangle/value data. Exposes latest session-wide timing losses and
marks reported completeness false if unavailable/nonzero; no unsampled coverage
or clean performance claim from verbose logs.

Runnable --self-test covers those failures, whole-list denominator, clear
exclusion and session isolation; passed. Applied to archived PID1376 session
20260909T025710Z-p1376, frames3240..3840 step60:35 groups,418 ordinary records,
11 frames, zero reported losses. Every signature/call-count/nanosecond total
matches the previous one-off ranking. Result archived at
`transfer-contract-probe/qualified-contract-ranking.json`; qualification here
is audit structure/sample completeness, not performance retention.

This makes existing native evidence reproducible without Windows Developer
Mode. Current runtime logs without verbose contract signatures are explicitly
rejected rather than grouped by mere descriptor count. No renderer or system
settings changed. Developer Mode question remains pending; existing active
P2 work is not globally blocked by that replay-counter capability. Next use
complete contracts for paired native measurements or fresh replay counters if
the user enables Developer Mode. Do not repeat unchanged unqualified candidates.

## A1/A2: full-frame D24S8 resource-use closure (2026-09-09 UTC)

Retained runtime hash verified87B79AAB; no game was running. Reused captured
scaled-rgba-stationary-rdc/frame_frame3055.rdc (earlier RGBA8 candidate, unchanged
transfer implementation). Read-only RenderDoc resource usage plus actual bound
consumer reflection/descriptors now covers the full frame, beyond the earlier
provenance cutoff at event3400. No counters requested or OS settings changed.

Resource16324, D24S8 base720/pitch13/1xMSAA:495 depth-target draws, including387
named guest draws;45 pixel-read events and4 unique compute-read dispatches.
Resource16433, same base/pitch D24S8/4xMSAA:36 depth-target draws, all verified
transfer helpers by shader reflection, no guest geometry draws;77 pixel-read
events and2 unique compute-read dispatches. GetUsage lists each depth/stencil
compute SRV separately, so raw8/4 CS usage records are not8/4 dispatches.

Four forward depth+eight-stencil groups at711,2012,2991,3299 populate16433.
Its eight clear events pair transfer stencil initialization with partial
DEPTH-only clears744,2045,3024,3332. The latter preserve stencil (ClearFlags1),
with captured rectangles560,512..960,1024;0,0..960,1024; and0,0..480,512 twice.
Source16324 receives seven reverse groups. Later consumers3490..3573 transfer
to14642 (D24FS8 base0/pitch16/4xMSAA), with separate floating-depth sources.
Compute dumps3233/3469 read16433 depth and stencil into EDRAM buffer319;
16324 dumps1947/2925/3228/3464 do likewise. Thus no direct guest geometry use
of16433 does NOT make its contents dead or authorize dropping its consumers.

Source trace: IssueDraw calls render_target_cache_->Update around3030, before
native FH1 rectangle-clear admission around3609 and ClearFh1Rectangles around3659.
Update derives a new key including sample count and claims ranges through
ChangeOwnership. Existing native clear replaces rasterization but explicitly
preserves earlier ownership/transfer preparation. This identifies a concrete
next seam: qualify a depth clear directly against the existing native owner,
with correct guest-address/sample mapping, before forcing a4x representation.
This could eliminate the intermediate and round trips instead of optimizing
stencil-copy arithmetic. Need exact clear producer attribution, mapped partial
regions, ownership accounting, subsequent mixed-depth consumers, query guards,
1x/2x parity and matched live cost before implementation/retention. Do not infer
that a different physical representation can be cleared with unchanged coordinates.

Reproducer .local/native-renderer/p2/native-chain-usage.py runs via qrenderdoc
--python; native-chain-usage-check.py validates read bindings, consumer joins,
usage counts and all36 transfer-only writes; executed successfully. Artifacts:
native-chain-usage/report.json and summary.json. Both replay processes exited.
A1 matched-chain timing and A2 game-side lifetime remain incomplete. No renderer
changes, speedup, native ownership completion or slowdown fix claimed.
## A2: native clear producer confirmed (2026-09-09 UTC)

Read-only replay native-clear-producer.py completed (PID41736 exited).
All four partial depth clears744,2045,3024,3332 have the direct enclosing
PinyonShift native FH1 rectangle clear marker and write ResourceId::16433.
This closes producer attribution: these are IssueDraw native rectangle clears,
not Resolve clear operations. Script asserts all four markers and saves
.local/native-renderer/p2/native-clear-producer.json; no GPU counters used.

Source inspection confirms an early-clear implementation cannot simply move
ClearFh1Rectangles: that method chooses last_update_accumulated_render_targets,
while IsFh1ClearPipeline depends on the configured pipeline description after
Update. Preserve its shader modification, raster, depth/stencil and color gates.
Viewport calculation itself uses registers, scale, normalized depth and target
conversion policy; reuse GetHostViewportInfo and GetScissor for early preparation.
UpdateSystemConstantValues and fixed-function stencil reference currently run
later, so an early path must derive the equivalent inputs rather than read stale
system constants or ff_stencil_ref_. Existing CopyCpuSnapshot authority and query
exclusions remain mandatory. First derive and check the exact clear-address
mapping against the existing 1x owner; then expose ownership admission before
Update. Do not use the last bound target as proof of current tile ownership.

Retained runtime SHA25687B79AABEC3F06326DF616DC02CCC3588E1CFFEFEE3A4E2B3590A17655EA23B5
verified unchanged. No production renderer edits or performance claim. A1/A2
remain incomplete; this evidence narrows the implementation seam for A3.
## A2/A3: partial-clear address mapping checked (2026-09-09 UTC)

Added and ran local check-native-clear-mapping.cpp (clang++ C++20 -O2).
PASS:7,204,228 sample coordinates, at symmetric resolution scales1 and2.
Reference follows CreateTransferPixelShader tile division, horizontal/vertical
sample-bit insertion, modulo2048 tile adjustment and source pitch division.
For same-base/same-pitch D24S8, 4xMSAA clear rectangles map to doubled 1xMSAA
bounds provided the entire rectangle lies in the unique2048-tile domain.
Checks cover recorded rectangles and an unaligned rectangle, each with a
one-pixel exterior guard, plus last valid partial tile row and rejection of
padding, wrapping, over-pitch, empty and invalid-scale inputs.

This is CPU addressing evidence, not GPU depth/stencil equivalence or ownership
proof. No production helper added yet. Next ownership admission must inspect
ownership_ranges_ for each touched tile row (including absolute base wrapping),
not last_update_accumulated_render_targets. Existing IsOwnedBy/ChangeOwnership
also account for separate host depth history; preserve that contract rather
than inventing an independent lifetime map. A rectangular clear may touch only
part of a tile: unchanged pixels and stencil must remain on the same valid owner.
A1/A2 and live A3-A6 qualification remain open; no measured speedup claimed.
## A2/A3: live pre-clear ownership established (2026-09-09 UTC)

Temporary bounded logging inside common RenderTargetCache::Update records
ownership before any changes for VS1E6883,4xMSAA,depth-write,no-color and base720.
First broad probe PID25604 exhausted its240 records in title-screen base0 clears;
it is not gameplay ownership evidence. Targeted probe PID28960/session
20260909T042910Z-p28960 exits normally with240 complete base720 snapshots.
Audit binary8B91FE07006F2C4544C79AF45E279A55DF04FFCC680AB3C52C54C5F108783897.

All240 snapshots have the same seven ranges, covering absolute tiles0..2048
without gaps. Every current owner is00206AD0 (base720,pitch13,1x,D24S8).
Unorm history keys are empty. Floating-depth history remains:
0..4:00608000;4..8:00600804;8..128:00608000;128..256:00682080;
256..720:00608000;720..1440:006082D0;1440..2048:00710400.
This supports direct mutation of the already-authoritative1x resource, while
keeping separate floating-depth history references unchanged. It does not
prove arbitrary scenes or admission of all logged draws as native clears.

Do not reuse !WouldOwnershipChangeRequireTransfers as an ownership predicate:
it also returns false for empty tiles. The early-clear gate needs explicit
current-owner equality for every affected tile, plus matching D24S8/base/pitch,
validated rectangles and all existing shader/raster/query/CPU-authority checks.
Do not reject the whole candidate merely because float history exists; the
existing later transfer path already reconciles that history against guest bits.

Reproducer local native-clear-owner-targeted-probe.ps1 and archived temporary
native-clear-owner-targeted-audit.cpp. summarize-native-clear-owners.py selects
the exact runtime session, validates expected range counts and contiguous full
coverage, sorts by tile start (merged logs sort equal timestamps lexically),
and writes native-clear-owner-targeted-probe/owner-summary.json. Check passed.
Verbose diagnostic run is not performance evidence. Source restored bytewise
and rebuilt; both staged/artifact DLLs reproduce87B79AABEC3F06326DF616DC02CCC3588E1CFFEFEE3A4E2B3590A17655EA23B5.
A1-A6 remain open; next implement bounded early clear against existing ownership.
## A3: opt-in early owned-depth clear candidate (2026-09-09 UTC)

Implemented fh1_owned_depth_clear (defaultfalse). Before Update, a bounded
VS1E6883/no-PS/4x D24S8 depth-only rectangle draw reuses ConfigurePipeline and
IsFh1ClearPipeline, query/memexport/index/CPU-authority gates, GetHostViewportInfo,
GetScissor, UpdateSystemConstantValues and existing vertex/rectangle decoding.
The D3D12 clear validates the mapped bounds before touching any resource. Common
GetFullyOwnedRenderTarget requires explicit current-owner equality across the
whole ownership map; empty or mixed owners fall back. It retains separate float
history and clears only depth in the existing1x resource. No4x ownership claim,
transfer preparation, color writes or stencil writes on admitted draws.
Current gate deliberately covers the measured whole-EDRAM owner contract;
per-row mixed-owner admission remains deferred until a measured need.

New tools/check-fh1-owned-depth-clear.cpp compiles against the actual fh1_clear.h
mapping helper:7,204,228 sample mappings at1x/2x, exterior guards and wrapped/padded
rejection pass, as do negative/NaN/infinite/out-of-range depth and preserved-value
checks. Command: clang++ -std=c++20 -O2 -Ithirdparty/shiftglue-sdk/include
 tools/check-fh1-owned-depth-clear.cpp -o .local/native-renderer/p2/check-owned-depth-clear.exe
then run that executable. rexgpu-fh1 Release target build passes.

Candidate SHA256C6596D51136B41390EBD2247F30B78A1AC1DE7D004D7D53FFB9E269168AE5936
archived as early-clear-candidate.dll. Opt-in2x smoke PID51072/session
20260909T043541Z-p51072 exits normally; logs show at least3072 admitted clears.
Open-world-end screenshot inspected: no obvious scene/geometry failure, but
this is not pixel equivalence, nonzero-stencil or motion qualification.

Existing timing-summary logic reused for32..44s window,11 sampled frames:
308 ordinary intervals,3.105699ms/frame;943 clear intervals,.245574ms/frame;
total3.351273ms/frame, all busy/capacity/interrupted/invalid losses zero.
Earlier2x diagnostic probe had421 ordinary intervals,5.683200ms/frame.
This suggests removed work but is NOT matched clean A/B performance or complete
contract attribution. Do not infer a retained speedup from this single run.
Artifacts early-clear-probe, early-clear-timing-summary.json and scripts local.

Source candidate remains opt-in and unqualified. Probe restores staged and
rexglue-artifacts DLLs to87B79AAB; future builds contain the new defaultfalse
candidate. Need capture proof of removed transfers and downstream depth/stencil
history equivalence,1x smoke, matched repeated1x/2x performance/memory and motion
including difficult areas. A1-A6 remain unchecked; no completion claimed.
## A3/A5: 1x smoke and captured owned-clear boundaries (2026-09-09 UTC)

Unchanged opt-in candidate C6596D51 passes1x open-world smoke PID46908/session
20260909T043826Z-p46908, normal exit, at least5120 admitted clears. End screenshot
inspected with no obvious rendering failure. Sampled32..44s timing window:
336 ordinary intervals at.803067ms/frame;1023 clear intervals at.183125ms/frame;
total.986192ms/frame, zero busy/capacity/interrupted/invalid losses. These are
single-run diagnostic observations, not matched repeated performance retention.

Fresh2x RenderDoc capture PID51592 completed normally: early-clear-rdc/
frame_frame3081.rdc. Four owned-depth clears677,1318,1889,1913 target resource16437
(D24S8 base720,pitch13,1xMSAA,2080x5056). No base720/pitch13/4x D24S8 texture exists
in this capture. An unrelated base720/pitch5/4x texture exists with no frame uses.
Owner resource has9 barriers,11 clears,243 depth-target draws,14 pixel reads,
8 compute-read usage entries. Do not compare whole-frame counts directly to the
older capture: these are separate live inputs, not a matched replay comparison.

Readback before/after each owned clear checks42,065,920 bytes per texture:
all four pass exact stencil preservation, all pixels outside the rectangle
unchanged, and depth bytes equal1.0 within the rectangle. Bounds are0,0..960,1024;
0,0..1920,2048;0,0..960,1024 twice. Total168,263,680 output bytes checked against
corresponding pre-clear contents and expected writes. All captured stencil bytes
were zero: this does NOT establish nonzero-stencil coverage or full downstream
history equivalence. No counter collection or OS changes needed.

Reproducer early-clear-capture-audit.py uses structured clear commands and
GetTextureData; actual SDObject float accessor is AsFloat. Final replay PID4100
exited, report early-clear-capture-audit.json contains4 successful readbacks and
no error. Prior accessor discovery attempts are not validation results.
Both staged/artifact runtimes remain qualified87B79AAB. Candidate source remains
opt-in. Next: nonzero/history correctness and matched repeated performance at
both scales, then motion/difficult-area qualification. A1-A6 remain unchecked.
## A6 screening: eight clean 2x toggle runs (2026-09-09 UTC)

Completed early-clear-abba.ps1 in ABBA/BAAB order, all8 normal exits.
Both A and B use identical C6596D51 binary, with explicit
fh1_owned_depth_clear=false/true respectively. Same stationary route/settings;
no corpus/discovery sampling, builds or replay during measurement. Qualified87
restored afterward. Runs a1:44984,b1:4100,b2:53020,a2:51660,b3:52616,a3:28028,
a4:46116,b4:43696. Each output archives session/perf and process samples.

Means of per-run metrics, off -> on:
median16.582625 ->16.635750ms (+.320%);
p95 20.314000 ->20.274250ms (-.196%);
p99 22.845000 ->22.581000ms (-1.156%);
GPU16.666853 ->16.785012ms (+.709%);
CPU3.322039 ->3.170535 process-seconds/wall-second (-4.561%);
private4735.654 ->4685.329MiB (-50.325MiB,-1.063%);
working set-.787%. Draws per row+4.208%; dirty loads+.174%.

Ordering-block checks: ABBA median/p95/p99+2.078/+3.966/+5.927%,
BAAB-1.416/-4.164/-7.574%. GPU+3.276/-1.796% respectively.
Thus no repeatable end-to-end FPS or frame-tail gain established. CPU reduction
is consistent:ABBA-4.881%,BAAB-4.239%; private memory-1.071/-1.054%.
Workload varies despite same scripted inputs:draws/source-frame span3340..3790;
normalizing source_frame_count does not eliminate the variation. Do not call
this deterministic matched-workload evidence or use it to close A1 wholesale.

Summary .local/native-renderer/p2/early-clear-abba-summary.json includes raw
run metrics and both ordering blocks; summarize-early-clear-abba.py reproduces
combined metrics. Candidate remains opt-in: dependency removal plus consistent
CPU/memory savings justify continued qualification, not automatic rejection
for lack of FPS gain and not retention yet. Need1x repeated runs, nonzero stencil,
downstream history equivalence, motion and relevant difficult-area evidence.
A1-A6 remain incomplete.
## A4: nonzero-stencil GPU preservation check (2026-09-09 UTC)

Temporary diagnostic fixture initializes the existing depth resource stencil to
0xA5 immediately before each actual owned-depth clear; the production clear body
is unchanged. Fixture build8EFB7700AD0B36781C51C2DB62D8D21E187BB3EB9E53DAD9ABCB2E28FFA112F8.
2x capture PID41104 exits normally, early-clear-nonzero-rdc/frame_frame3087.rdc.
This intentionally modified scene is correctness stress evidence, not gameplay
fidelity or performance evidence. No save files manipulated.

Replay PID48912 exits with4 passing before/after checks at648,1340,1913,1940.
Each before image must contain exactly0xA5 at all10,516,480 stencil positions;
all values remain identical afterward. Entire42,065,920-byte images are checked
for unchanged pixels outside the rectangle and exact depth1.0 inside. Rectangles:
0,1024..960,2048;0,0..1920,2048;0,0..960,1024 twice.
All168,263,680 output bytes pass corresponding checks. This extends earlier zero
stencil evidence to an explicitly verified nonzero pattern and offset rectangle.
It does not prove all downstream mixed-format depth history or1x stress coverage.

Reproducer early-clear-nonzero-capture-audit.py requires the sentinel before each
clear and writes early-clear-nonzero-capture-audit.json. Fixture and pre-fixture
source archived locally as early-clear-nonzero-fixture.cpp / -before.cpp.
Source restored bytewise and rebuilt: candidate reproducesC6596D51 exactly;
both staged/artifact DLLs then restored to qualified87B79AAB. Production source
contains no stencil seed; the early-clear feature remains defaultfalse.
Next: downstream history equivalence,1x repeated performance and motion/area
coverage. A1-A6 remain incomplete; no retention claimed from this stress test.
## A6 screening: eight clean 1x toggle runs (2026-09-09 UTC)

Completed early-clear-1x-abba.ps1, all8 normal exits in ABBA/BAAB order.
Identical C6596D51 binary and explicit false/true flag in both arms; same route,
1x scale, no profiling/replay/build workload during measurement. PIDs in order:
a1:45668,b1:51656,b2:31016,a2:42172,b3:2476,a3:49192,a4:33268,b4:1580.
Qualified87 runtime restored by benchmark finally block.

Means of per-run metrics, off -> on:
median16.611625 ->16.263625ms (-2.095%);
p95 20.411000 ->19.513500ms (-4.397%);
p99 22.974750 ->21.772250ms (-5.234%);
GPU16.185013 ->15.709681ms (-2.937%);
CPU3.190098 ->3.164223 process-seconds/wall-second (-.811%);
private2541.266 ->2528.883MiB (-12.383MiB,-.487%);
working set-.192%. Draws/row-2.687%; dirty loads+.700%.

Both ordering blocks improve frame-time tails: ABBA median/p95/p99
-3.085/-6.503/-5.906%; BAAB-1.097/-2.291/-4.591%.
GPU-4.964/-.875%, CPU-.484/-1.139%, private-.863/-.109%.
Workload is not deterministic: draw counts differ-7.202% in ABBA,+2.077% BAAB.
Thus route-level screening is encouraging at1x, but these numbers do not prove
an exact matched-input speedup or hardware requirement reduction. Together with
2x consistent CPU/private-memory savings and captured intermediate removal,
continue candidate qualification rather than revert based on inconclusive2x FPS.

Artifacts early-clear-1x-abba-{label} archive session/perf/process samples;
early-clear-1x-abba-summary.json records run metrics and ordering blocks.
summarize-early-clear-1x-abba.py reproduces the combined metrics. No source edits
this turn. Still needed: downstream mixed-depth history equivalence and motion/
difficult-area coverage; no default enable or A1-A6 completion claimed.
## A2/A4: downstream floating-depth output checked (2026-09-09 UTC)

Replayed unchanged early-clear-rdc/frame_frame3081.rdc. Full current-owner
consumer inventory closes18 unique reads:4 compute dumps,8 stencil transfers,
6 depth transfers. Depth consumers2139,2143,2147,2151,2156,2161 all bind
xe_transfer_depth AND xe_transfer_host_depth; history sources cover base0/pitch16,
base4/pitch1,base720/pitch16 at1x,base128/pitch4 at2x andbase1024/pitch32 at4x.
Exported exact bound source/history resources and all4 samples of final D24FS8
base0/pitch16 target14711 after2161. No GPU counters requested.

Local check-early-clear-history.py independently computes addresses from EDRAM
tiles,base,pitch and sample bits, including native2x vertical sample reversal.
Uses observed seven history partitions and mathematical20e4-to-float conversion,
then checks the final full1280x2048x4 target against preserved history where
its quantized bits match current guest bits, otherwise current-value conversion.
All10,485,760 depth samples and stencil values match exactly, zero mismatches.
Both paths exercised:4,327,159 history matches and6,158,601 guest conversions.
This is whole downstream target evidence, not merely verifying history bindings.
It proves this captured2x state, not unseen scenes,1x history or every resolve dump.

Artifacts early-clear-consumers/report.json records18 consumers,address constants,
7 exported textures and per-sample files; six shader disassemblies archived.
early-clear-consumers/history-check.json records the exact comparison counts.
Reproducer early-clear-consumers.py via qrenderdoc --python, then
C:/Users/neri/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
.local/native-renderer/p2/check-early-clear-history.py. Final replay exited.
No production changes this turn. Candidate remains opt-in C6596D51 and staged
runtime87. Remaining qualification includes1x downstream/history, resolve dump
side effects, motion/difficult-area coverage and final evidence audit; goal open.
## A4: depth dump contents and nonzero downstream history (2026-09-09 UTC)

Exported the1x owner texture plus EDRAM buffer immediately before/after each
2x-frame dump1303,1873,1899,2089. Independent NumPy check decodes actual dispatch
sizes/constants, computes source tile addressing, depth half-column swap and
24-bit-depth/high-bits plus stencil/low-byte packing. Reconstructs the entire
41,943,040-byte EDRAM buffer from its previous contents plus expected writes.
All4 buffers match exactly with zero inside/outside mismatches. Written samples
respectively1,146,880;4,259,840;1,182,720;1,182,720. The source stencil here iszero.
This verifies dump buffer side effects; it does not by itself validate every
subsequent resolve-copy output or guest synchronization case.

Artifacts early-clear-dumps/report.json, per-event source/before/after binaries,
shader disassembly and check.json. Reproducers early-clear-dumps.py and
check-early-clear-dumps.py; replay PID51756 exited normally.

Also repeated full downstream history model on diagnostic nonzero-stencil
capture frame3087. All10,485,760 final depth/stencil samples match, with
10,485,760 nonzero final stencil values. History matches4,327,227 samples;
current-value conversions6,158,533. Thus nonzero preservation extends through
the later D24FS8 transfer, not just the immediate clear. This is diagnostic
content stress, not visual/performance qualification of the modified scene.

Artifacts early-clear-nonzero-consumers/{report,history-check}.json and exported
textures; early-clear-nonzero-consumers.py / check-early-clear-nonzero-history.py.
Replay PID52428 exited; all checks passed. No production source/binary changes.
Next:1x resource-chain correctness and motion/difficult-area qualification;
complete-chain attribution/final audit remain open before retaining by default.
## A4: captured 1x resource-chain checks (2026-09-09 UTC)

Unchanged opt-in C6596D51,1x RenderDoc capture PID53164 exits normally;
early-clear-1x-rdc/frame_frame3070.rdc. Staged runtime restored87 afterward.
Reused actual-resource exporters and address checks with tile dimensions derived
from captured scale, rather than treating2x byte evidence as1x qualification.

All4 owned-clear readbacks562,1249,2141,2313 pass expected depth, stencil and
outside-rectangle preservation over10,516,480-byte images each. Bounds:
0,512..480,1024;0,0..960,1024;0,0..480,512 twice. Captured stencil iszero.
Full downstream D24FS8 target passes all2,621,440 depth/stencil samples;
history-preservation1,081,246 and current-value-conversion1,540,194 samples,
zero mismatches. All4 EDRAM dumps1234,2125,2297,2410 pass entire10,485,760-byte
buffer comparisons, including unmodified regions. Written sample counts:
286,720;1,064,960;295,680;295,680 respectively.

Artifacts early-clear-1x-consumers/{report,history-check}.json,
early-clear-1x-capture-audit.json and early-clear-1x-dumps/{report,check}.json.
Reproducers use corresponding1x consumer/clear/dump exporter and history/dump
checker scripts in.local/native-renderer/p2. Replay PIDs1920,39004,3544 exited.
No production changes. This closes these captured1x content checks, not all
unseen scenes,resolve-copy/synchronization paths or motion coverage.

Next motion route already exists: config/render-tests/fh1-race.fh1test exercises
Recaro Rush from the current AppData fixture, with race HUD, distinct presentation
and simulation-time gates. Use it for candidate/baseline motion qualification;
recorded downtown/outpost/plaza/canyon discovery areas still need relevant
coverage and must not be silently replaced by this stationary/race fixture.
A1-A6 completion and default retention remain unproven.
## A6: 2x Recaro Rush motion probe (2026-09-09 UTC)

Opt-in C6596D51 runs existing config/render-tests/fh1-race.fh1test via authorized
AppData launch, PID41080/session20260909T051619Z-p41080. Normal exit, scenario
completion event present, no checked renderer/device/pipeline failure patterns.
At least8192 owned-depth clears logged. Six expected screenshots produced;
race-moving inspected: actual race HUD, car85km/h, geometry/crowds/shadows visible
without obvious scene failure. This is6seconds scripted acceleration, not a
complete race or proof of smooth motion everywhere.

Applied existing parse_scenario,MAE,race-HUD and performance-summary helpers to
recorded output (launch-preview alone does not evaluate Python-runner assertions).
Capture difference78.911MAE exceeds20 minimum. Race HUD check passes.
Median11,197us; presentation and distinct-presentation62.321Hz; simulation
cadence102.161Hz. Simulation-time71.207104s / active wall70.907495s =1.004225,
invalid deltas2: both within existing scenario bounds. These whole-run metrics
include menus/loading, so are not clean race-only optimization benchmarks.

Overall qualification.json remains passed=false because all16 required named
native-family counters were absent from this session. Do not silently remove
those scenario requirements or report the whole scenario as passing. The
motion/timing checks pass individually; missing counters require separate
coverage investigation/baseline comparison. check-early-clear-race.py reuses
runner helpers and records every check, including the failures. Runtime/session,
perf,process samples and screenshots archived under early-clear-race-probe.

Qualified87 staged/artifact runtime restored. No production source changes.
Next: baseline motion comparison, current native coverage evidence,1x motion
and relevant previously marked difficult-area coverage. Goal/default retention
remain open; do not replace difficult-area work with this race-start fixture.
## A6: current clear coverage gate; baseline race crash (2026-09-09 UTC)

Source search finds no producers for the16 legacy named native-family counters
required by fh1-race. Preserved that scenario unchanged. Added
config/render-tests/fh1-owned-depth-race.fh1test with identical inputs,captures,
HUD,MAE,performance,simulation and distinct-presentation requirements, and the
current owned-depth-clear counter as this resource-chain coverage gate. This is
a scoped goal test, not a claim that legacy renderer-wide coverage now passes.

Runner NATIVE_COUNTER now also accepts non-V5 native clear records, preserving
legacy draw/vertex-draw parsing.16 existing/added unit tests pass; added tests
verify both counter forms, reject unrelated messages and prove the new scenario
has identical actions and non-coverage requirements. Applied to existing candidate
PID41080 output: all scoped checks pass including8192 owned depth clears.
early-clear-race-probe/owned-qualification.json records this result; original
qualification.json retains the legacy coverage failures.

Feature-off comparison (same C6596D51 binary,flagfalse), PID17708/session
20260909T052128Z-p17708, crashes before race-ready with0xC0000005 read at target
0x100000004. Fault module pinyon_shift.exe offset0x48AA082. Crash ID
pscrash-v1-ee6551b0ab9ec370e1af. Crash snapshot/report archived under
.local/native-renderer/p2/early-clear-race-off-probe; original diagnostic ZIP
remains in AppData reports. No external issue submitted. This run is NOT a valid
baseline and does not identify cause or establish an early-clear regression.
llvm-symbolizer returned no symbol for this executable/offset; no top-level PDB
present. Do not conceal this failed attempt or claim a successful comparison.

Qualified87 runtime restored; no game running. Next obtain a valid qualified
baseline race comparison and investigate/reproduce the access violation if it
recurs.1x motion and recorded difficult-area coverage remain necessary. New
runner/scenario changes do not complete A1-A6 or justify default enable.
## A6: qualified baseline and 1x race motion checks (2026-09-09 UTC)

Qualified runtime 87B79AAB completed the 2x race control normally in session
20260909T052501Z-p50484. All six captures, HUD, image-change, cadence and
simulation-time checks passed, with zero owned-depth-clear admissions as expected.
Median frame time 10.623 ms; presentation/distinct cadence 52.735 Hz; simulation
95.184 Hz, simulation/active-wall ratio 0.995726, four invalid deltas. The moving
capture shows the car at 80 km/h. Evidence: early-clear-race-qualified-probe and
check-early-clear-race-qualified.py under .local/native-renderer/p2.
This establishes a successful qualified control; it does not explain or erase
the earlier C659 feature-off access violation.

Opt-in C6596D51 completed the 1x scoped race scenario normally in session
20260909T052738Z-p49704. All scoped assertions pass: six captures, race HUD,
76.621 MAE versus the pre-race capture, median 12.488 ms, presentation/distinct
cadence 61.125 Hz, simulation 96.857 Hz, simulation/active-wall ratio 1.003705,
two invalid deltas, at least 7168 owned clears, completion and no checked renderer
error patterns. The moving screenshot was inspected: car at 77 km/h, race HUD,
track, crowd and shadows visible without obvious scene failure. Evidence:
early-clear-race-1x-probe/owned-qualification.json, process-samples.json, runtime
log and captures; checker check-early-owned-race-1x.py.

These are short scripted race-start motion checks, not full races, NPC animation
qualification or matched race-only performance measurements. Candidate 2x also
passed its scoped checks previously; different race timing/poses prevent a
pixel-equivalence or FPS-gain claim between these single runs. Legacy broad
native-family requirements remain separate and unchanged. Recorded difficult-area
coverage, remaining chain boundary accounting and final retention remain open.
Qualified 87B79AAB staged runtime restored and verified; no game remains running.
## A2/A6: source lifetime audit and declaration cleanup (2026-09-09 UTC)

Added OWNED_DEPTH_CHAIN_CONTRACT.md to record the actual ownership boundary,
creation/clear/history/alias/resolve/eviction/destruction behavior and remaining
compatibility work. Source confirms cache eviction retains current and both
history owners, and destruction invalidates ownership before deleting targets.
Resolve still dumps authoritative contents, dispatches the copy, orders UAV
writes, invalidates texture ranges and reports the written extent. Captured dump
checks do not yet independently prove final resolve destination bytes. Runtime
reset/recreation and the pre-packet game producer remain unproven.

Removed two accidental unused GetFullyOwnedRenderTarget declarations from the
nested RenderTarget and Transfer types. The sole intended protected cache helper
remains. Build rexgpu-fh1 passes; 16 runner tests pass; existing mapping executable
passes 7,204,228 checks. Build log: p2/owned-clear-declaration-build.log.
New build hash 2B9CED2AEB9270BCECA5FC981BE8539D72A3101AC0B8F42CFF89AE3119F60F10
archived as p2/owned-clear-declaration-candidate.dll. Earlier runtime evidence is
for C6596D51 and is not relabeled as a run of this new binary. Both staged runtime
DLLs restored to qualified87. A1-A6 remain open, candidate default remains false.
## A2/A4: final resolve publication readbacks (2026-09-09 UTC)

Replayed the existing candidate captures to trace each of the four checked depth
dumps to its first subsequent compute read of EDRAM. At 2x these are dump/copy
1303/1310,1873/1880,1899/1906,2089/2096. Each uses Resolve Copy Fast 32bpp
1x/2xMSAA, with only a barrier between dump and read. Archived actual dispatch,
resource views, constants, shader disassembly, full EDRAM source and before/after
destination view bytes in p2/early-clear-publication. Replay PID52372 terminated
normally without a report error. Destination ranges are 8,126,464;16,777,216;
8,667,136;8,667,136 bytes. All four have zero changed bytes in this stationary
capture, despite varied contents. This is NOT a publication-correctness pass.

The 1x replay exposes the whole 512 MiB shared-memory UAV; the initial bounded
export guard correctly rejected that allocation. Updated the local 1x exporter
to read the destination texture extent from captured destination base and pitch/
height constants instead, retaining original descriptor metadata separately.
Successful replay PID44284 terminated normally, no report error. Dump/copy pairs
1234/1241,2125/2132,2297/2304,2410/2417 change 112180,254102,401344,345642 bytes.
This provides changing-output evidence for the next independent value/address
check. Metadata and binary readbacks: p2/early-clear-1x-publication; scripts
p2/early-clear-publication.py and p2/early-clear-1x-publication.py.

Next compare actual destination values and untouched regions against an
independent resolve addressing/endianness model. Capture disassembly prints
integer constants as floats; the SDK generated bytecode header contains readable
integer assembly for resolve_fast_32bpp_1x2xmsaa[_scaled]_cs.h. No production
source or runtime changed this turn. Qualified87 remains staged; A1-A6 active.
## A4: exact final resolve publication checks pass (2026-09-09 UTC)

Added tools/check-fh1-owned-resolve.py. It evaluates each captured output pixel
using independent EDRAM tile/half-row addressing, 32bpp 2D tiled destination
addressing, byte reversal, symmetric resolution scaling and half-pixel gap fill.
It starts expected destination contents from the before buffer, writes only
predicted pixels and compares the complete exported range with the after buffer.
Assertions reject unsupported format/layout/sample/scale state and overlapping
or out-of-range destination addresses. This is a bounded depth-resolve checker,
not a generic shader emulator.

Both commands pass using the installed NumPy runtime:
  python tools/check-fh1-owned-resolve.py .local/native-renderer/p2/early-clear-1x-publication
  python tools/check-fh1-owned-resolve.py .local/native-renderer/p2/early-clear-publication

1x events1241,2132,2304,2417: respectively262144,1048576,270400,270400
predicted pixels; each full4,194,304-byte exported texture range matches exactly.
These runs include changing destination data. 2x events1310,1880,1906,2096:
1048576,4194304,1081600,1081600 pixels; entire8,126,464;16,777,216;8,667,136;
8,667,136-byte destination views match exactly. No mismatches across all eight
copies. Results saved in each export directory/value-check.json.

The 2x stationary copies had no changed bytes, but now their values are checked
against independently addressed source data rather than accepting no change as
proof. Outside-write pixels within the exported ranges are checked; writes
outside those ranges and other resolve formats are not claimed. Updated the
chain contract accordingly. Source producer boundary, matched chain attribution,
runtime reset/recreation, difficult-area coverage and final retention remain open.
No game or production build changed; the qualified runtime stays staged.
## A4/A6: live cache eviction passes at 1x/2x (2026-09-09 UTC)

Traced supported cache eviction: D3D12 ClearCaches requests clearing; frame close
waits for all GPU queue operations before clearing caches. Current render-target
and independent history owners survive common ClearCache. Full target destruction
occurs in shutdown; no supported in-game full reset command was found.

Temporary diagnostic fixture requested real ClearCaches after owned-clear counts
1024 and2048 and logged completion after shared-memory cache clearing. Build hash
FE0A1194504F03DEE7B68D1AB1F10FB3160A3569B74C7F5E07849B50EA951F60,
archived p2/owned-clear-eviction-fixture.dll. Both modified source files were
restored byte-for-byte before running; no fixture instrumentation remains.

2x PID36540/session20260909T054612Z-p36540: normal exit, cache completions at
frames1957/2213, owned clears continue to8192. All scoped race checks plus exact
request/completion ordering and later native admission pass. Median11.834ms,
present/distinct63.524Hz, simulation100.541Hz, simulation/active-wall0.993618,
invalid deltas4, capture MAE77.502. 1x PID46688/session20260909T054814Z-p46688:
normal exit, completions1959/2215, owned clears9216, same checks pass. Median
11.0815ms, present/distinct67.142Hz, simulation100.673Hz, time ratio0.994541,
invalid deltas4, MAE76.560. Both moving captures visually inspected at84km/h;
track, crowd, shadows and HUD present without obvious scene failure. These
forced-eviction runs are correctness probes, not clean performance comparisons.

Evidence p2/owned-clear-eviction[-1x]-probe, process/session logs, captures and
owned-qualification.json. Local checker check-owned-eviction-race[-1x].py reuses
existing race helpers and adds ordered eviction completion/continued-admission
checks. Production-source rebuild initially did no work because restoring backup
files preserved old timestamps. Touched the two restored source timestamps and
rebuilt: exact expected2B9CED2AEB9270BCECA5FC981BE8539D72A3101AC0B8F42CFF89AE3119F60F10.
Both staged/artifact DLLs restored to qualified87 afterward.

This proves the supported live eviction path in the scripted scene at both
scales, not arbitrary device loss or a forced destructive in-game reset. Final
retention, matched complete-chain attribution and difficult-area coverage remain
open. No saves were copied/reset; launch used the authorized AppData state root.
## A1/A5: same-binary complete transfer-contract comparison (2026-09-09 UTC)

Reapplied the prior audited transfer-signature metadata to current source in a
temporary diagnostic build, hash259D5F876067BF6C8DDCA9B2BC3C3C8FEFB388A9C5BE7BAE15B04A83F0F05739
(p2/owned-contract-fixture.dll). All three source files restored byte-for-byte.
Four authorized open-world diagnostic runs used identical binary/scenario and
feature off/on at each scale. All exited normally: 2x off PID26476/session
20260909T055522Z-p26476, on PID33260/session20260909T055626Z-p33260; 1x off
PID51972/session20260909T055743Z-p51972, on PID47392/session20260909T055847Z-p47392.
A pre-launch script argument error created no game/session; corrected before runs.

summarize-owned-contract.py reuses tools/rank-fh1-transfer-contracts.py, validates
all sampled source frames in the32-44s interval and archives session/perf data.
All four report zero busy/capacity/interrupted/invalid timing losses. 2x has10 off
and11 on sampled frames; 1x11 off and10 on. These are diagnostic live scenes with
logging overhead and different source frames, not identical-workload clean FPS
benchmarks. Full ordered transfer signatures are retained in contracts.json.

compare-owned-contracts.py accounts for every ordinary interval involving the
selected owner/intermediate. On runs contain no source/destination/history use
of the eliminated0x306AD0 4x target. Pure round trips comprise six signatures:
E2950943A57676F6,9042BE20F80E9496,44DCDDC7E394EE36,7B6753D432012633,
CF245FD27E54D493,88769272D80676F6. Their removed cost is2.577818ms and10.6
intervals per sampled frame at2x;0.619241ms and9.363636 intervals at1x.
Dominant forward E295 runs exactly4 times per sampled off frame, costing1.565184ms
at2x and0.387258ms at1x; it is absent in both on runs.

Retained initialization and mixed floating-depth consumer each execute once per
sampled frame in all runs. Full destination/current-source/history mappings match
per tile after substituting the native owner for the eliminated intermediate.
At1x two off consumer signatures split the same mapping differently; the initial
per-signature count comparison rejected them. Combining only identical full
per-tile maps yields the same one-call-per-frame boundary. This is not first-entry
or descriptor-count grouping. Independent captured GPU history checks remain the
value-correctness evidence. Initialization cost off/on:2x0.321331/0.313065ms,
1x0.084992/0.080794ms. Mixed-depth consumer:2x0.421581/0.440134ms,
1x0.108358/0.107622ms. Total ordinary intervals off/on:2x5.667533/3.093411ms;
1x1.424477/0.799846ms. Do not claim these differences as measured frame-time gains.

Evidence: p2/owned-contract-{1x,2x}-{off,on}, corresponding comparison.json files,
local summarize-owned-contract.py and compare-owned-contracts.py. Clear, dump,
resolve-copy, CPU preparation and synchronization costs are outside this ordinary-
transfer timing account. A1's complete-chain cost coverage therefore remains open,
as do difficult-area qualification and retention. Restored-source rebuild passes
and reproduces2B9CED2AEB9270BCECA5FC981BE8539D72A3101AC0B8F42CFF89AE3119F60F10;
both runtime DLLs restored to qualified87. No diagnostic instrumentation retained.
## A1: inclusive phase timing fixture ready; shared GPU occupied (2026-09-09 UTC)

Built diagnostic p2/owned-phase-fixture.dll, SHA256
5A3ED1E6856CCF13F3BB47C05A7AE42278A7810AD38C710BDDE6ABA340B90A04.
Reproducible patch script p2/make-owned-phase-fixture.py adds short-lived timing
scopes backed by the existing sampled timestamp allocator. Phase1 wraps the known
4x D24S8 clear draw from the early native-admission boundary through return,
including native preparation or the compatibility Update/clear path. Phase2
wraps depth resolves after successful parsing for pitch13/base720 through return,
including dump/copy/resolve-clear/barrier work. CPU recording wall time is logged
separately from GPU duration. Parent scopes include nested transfers: never add
the earlier transfer interval totals to these inclusive times. Common pre-boundary
draw processing and resolve parsing are explicitly outside these scopes.

Build passes. All three source files restored byte-for-byte and verified against
p2/owned-phase-before. Fixture exists only as a diagnostic DLL and local patch
script. p2/owned-phase-2x-probe.ps1 uses the same fixture for off/on runs and
restores qualified87. p2/summarize-owned-phases.py requires every selected source
frame to have four complete samples of each phase and zero reported timing
losses before writing phases.json. Neither this count nor the timing is yet
confirmed at runtime; any failure must be investigated, not silently relaxed.

Launch guard prevented execution because another task was using the GPU/game.
Authoritative process inspection found PID28612, then PID50240, both from
.local/non-renderer-optimization/compiler-pgo-dump/pinyon_shift.exe. App task
Retire Xenos renderer (5), thread01a08472-511f-75b1-b29c-51b42db2d25c, is active
on non-renderer/compiler optimization. Did not terminate or alter those sessions.
No phase run or new phase timing result exists yet. Both renderer runtime DLLs
remain qualified87. Defer GPU measurements and restored-source rebuild until
that workload is idle; revalidate live processes before proceeding. This turn
made fixture/checker progress, not a completed A1 result or a goal blocker audit.
## A3/A4: executable ownership lifetime check (2026-09-09 UTC)

Added tools/check-fh1-owned-lifetime.py. It extracts and compiles the actual
GetFullyOwnedRenderTarget, ClearCache and DestroyAllRenderTargets bodies against
a minimal resource shell. Checks pass for missing/null/empty/mixed ownership,
retention of current and both independent history owners, orphan eviction,
destruction with and without shutdown, and lookup after same-key recreation.
Command: python tools/check-fh1-owned-lifetime.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe.
This is a CPU ownership-method check, not a GPU device-loss simulation. It
complements the prior live1x/2x eviction tests. No production renderer change.

Inspected the old p0-playtest/town-approach route and map capture: endpoint is
near Recaro Rush on the east side of Montano Plains. Existing checkpoint already
records that it did not reproduce the reported collapse. It must not substitute
for the later downtown/outpost/plaza/canyon discovery markers. Marker001 shows
downtown buildings; the old approach route does not establish that location.

The separate non-renderer task moved from PGO game training to an active compiler
build (ninja PID49544/cmake51092 with live clang workers,339-340/360 at last read).
No renderer timing run launched during that workload. Inclusive phase fixture
remains ready. Goal active; this turn adds executable lifetime evidence, while
GPU phase timing and difficult-area qualification remain pending.
## A1: phase samples valid; cost comparison contaminated (2026-09-09 UTC)

After verifying no game/compiler process was live, ran the pending2x off/on
inclusive phase probe. Both exited normally: off PID14028/session
20260909T061238Z-p14028, on PID49872/session20260909T061343Z-p49872.
Fixture5A3ED1E6, unchanged executable882D9247. Both have exactly four clear and
four resolve phase samples in every selected source frame, zero reported timing
losses. Off12 sampled frames; on9. This validates the fixture's runtime selection
and query completion, not qualification of measured costs.

Raw off/on phase costs per sampled frame: clear GPU1.570645/0.010354ms,
clear recording wall0.020342/0.006644ms; resolve GPU0.076544/0.073159ms,
resolve recording wall0.030692/0.048722ms. Do NOT retain these as a qualified cost
comparison: another compiler build (ninja PID49756) started06:13:24UTC and
continued throughout the on run. Runtime inspection confirmed concurrent clang
workers. CPU recording wall time is especially susceptible to this contention.
Both phases.json files explicitly mark qualification_cost_accepted=false.

Hardened local phase probe scripts to reject active compiler workloads at launch
and record competing compiler process IDs/start times during execution. Summary
requires an explicit uncontended observation before accepting costs; missing
observations never imply a clean environment. This does not replace scheduling
exclusive windows. Asked user which of the two active goals should receive the
next exclusive benchmark window; answer pending. Do not stop the other task's
work without coordination. No further game run started. Qualified87 restored.
Evidence p2/owned-phase-2x-{off,on};1x probe remains unexecuted. Production source
is restored, but restored-source rebuild remains deferred while compiler work is
active. A1/A6 remain open; phase measurement needs an uncontended rerun.
## A1/A3-A5: uncontended inclusive phase runs; implementation gates (2026-09-09 UTC)

Other optimization task was verified idle and no game/compiler process was live
before starting. All four diagnostic runs exit normally and record no competing
compiler processes. Each has12 selected source frames, four clear and four resolve
samples per frame, zero busy/capacity/interrupted/invalid losses. Fixture5A3ED1E6
and executable882D9247 unchanged. 2x off PID32208/session20260909T071320Z-p32208;
on PID26296/session20260909T071438Z-p26296. 1x off PID41816/session
20260909T071626Z-p41816; on PID48868/session20260909T071743Z-p48868.

Per sampled frame, off -> on:
- 2x inclusive clear GPU1.572267 ->0.010496ms; CPU recording wall0.018258 ->0.004142ms.
- 2x depth resolve GPU0.076971 ->0.073557ms; CPU recording wall0.039875 ->0.026767ms.
- 1x inclusive clear GPU0.389717 ->0.004352ms; CPU recording wall0.020817 ->0.006975ms.
- 1x depth resolve GPU0.027648 ->0.027221ms; CPU recording wall0.030708 ->0.029658ms.

Clear includes its nested forward transfer in the off path; resolve includes
its dump/copy/barrier work. Do not add previous nested transfer totals to these
inclusive values. These are diagnostic component costs, not total-frame gains.
CPU numbers are recording wall time, not thread CPU. Common upstream processing
before the hook remains outside the scopes. Reproducible evidence in
p2/owned-phase-2x-clean-{off,on}, p2/owned-phase-1x-{off,on}, phases.json and
summarize-owned-phases.py. Earlier contaminated2x pair remains rejected.
The outer shell's stale/null LASTEXITCODE check falsely reported failure after
both2x probes exited normally; it did not restart either run. Launched1x directly
after checking terminal results, preserving all original2x evidence.

Restored-source build passes and reproduces2B9CED2AEB9270BCECA5FC981BE8539D72A3101AC0B8F42CFF89AE3119F60F10.
Both runtime DLLs restored to qualified87. No fixture instrumentation retained.

Checklist A3-A5 now checked for implementation of this selected chain: current
native allocation identity/lifetime and fallback are explicit; exact1x/2x clear,
history and publication plus nonzero-stencil/lifetime/eviction checks pass; captures
and complete-contract comparisons prove removed intermediate work with retained
consumer boundaries. This does not claim final retention, arbitrary device-loss
handling or full Xenos retirement. A1/A2 final scope audit and A6 difficult-area
coverage/final source-binary qualification remain open. Goal stays active.
## A1/A2 audited; final candidate race checks (2026-09-09 UTC)

Expanded OWNED_DEPTH_CHAIN_CONTRACT.md with non-additive1x/2x cost coverage,
recording-wall measurements, source-frame/loss checks and explicit consumer
inventory. A1/A2 now checked based on combined evidence. The actual game GPU
producer is clear vertex program1E6883FCCDE1F688, distinct from renderer-generated
transfer shaders. Earliest verified usable hook is IssueDraw before Update,
with full validated clear state and vertex snapshot. Upstream CPU packet-emitter
routine remains unidentified and is explicitly retained; bypassing it is B3,
not something this chain migration claims to implement. The cost table accounts
for initialization, inclusive clear, eliminated round trips, inclusive publication
and mixed-history consumption; overlapping intervals are not summed into FPS.

Exact final uninstrumented candidate2B9CED2A was tested at both scales using the
scoped race scenario and existing AppData save. 2x PID52644/session
20260909T072325Z-p52644: normal exit, all six captures and scoped checks pass,
8192 owned clears, median11.049ms, present/distinct64.640Hz, simulation101.678Hz,
time ratio1.004324, invalid deltas2, MAE79.513. Moving screenshot inspected at
85km/h; track/crowd/shadows/HUD visible without obvious scene failure.
1x PID26064/session20260909T072530Z-p26064: normal exit, all scoped checks pass,
9216 clears, median10.1455ms, present/distinct68.147Hz, simulation102.782Hz,
time ratio1.004754, invalid deltas2, MAE77.982. No checked renderer error patterns
in either session. These are whole-run short race-start checks, not FPS benchmarks
or a substitute for difficult-area coverage. Evidence p2/final-owned-race-{1x,2x}-probe
and check-final-owned-race-{1x,2x}.py. Qualified87 restored afterward.

A1-A5 complete for the selected chain. A6 remains open for final retention
comparison against the qualified runtime and recorded difficult-area coverage.
No default enable, publication or hardware-requirements claim made. Goal active.
## Final retention comparison started (2026-09-09 UTC)

A6 exact-binary 2x ABBA/BAAB comparison is running through local
`p2/final-owned-abba.ps1 -Scale 2`. A uses qualified 87B79AAB; B uses
final uninstrumented 2B9CED2A with owned depth clear enabled. Profiling is
not enabled. The harness records compiler contention and rejects overlapping
runs. First baseline PID49072 and candidate PID42156 exited normally.
Remaining runs are in progress; no retention or performance conclusion yet.
Local summary tool: `p2/summarize-final-owned-abba.py 2`.
The live execution handle is 11171; poll it before considering another launch.
1x comparison and recorded difficult-area coverage remain pending.
## Exact final candidate: completed 2x retention comparison (2026-09-09 UTC)

Eight unprofiled ABBA/BAAB runs completed normally, no observed compiler
contention. Qualified 87B79AAB versus final 2B9CED2A with owned clears enabled;
all eight binary hashes verified by summarize-final-owned-abba.py. Evidence:
.local/native-renderer/p2/final-owned-2x-abba-{a1,b1,b2,a2,b3,a3,a4,b4}
and final-owned-2x-abba-summary.json. Qualified runtime restored after batch.

Baseline -> candidate, mean of four runs per configuration:
median 17.538500 -> 16.491625 ms (-5.969%); p95 21.907000 -> 20.426250 ms
(-6.759%); p99 25.566500 -> 22.898000 ms (-10.437%). GPU 17.621376 ->
16.582133 ms (-5.898%); CPU 3.188675 -> 3.135371 process-seconds/wall-second
(-1.672%); private memory 4747.545 -> 4697.062 MiB (-50.483 MiB).
Both blocks improve median/p95/p99: ABBA -8.393/-7.462/-10.280%,
BAAB -3.354/-6.002/-10.597%. Both improve CPU and private memory.
Draw counts differ (-4.559% overall); this is a live stationary scene, not
identical replay. Do not infer a precise causal FPS gain or generalize to
hard areas from this sample. Earlier same-binary toggle results remain relevant.

The 1x eight-run comparison has now started using the same harness, live exec
handle 29616 (poll before starting another launch).
A6 remains open for 1x evidence, image review and recorded difficult-area coverage.
## Exact final candidate: 1x comparison and image review (2026-09-09 UTC)

All eight final-owned-1x-abba runs exited normally with no reported compiler
contention; exact hashes validated. Summary: p2/final-owned-1x-abba-summary.json.
Baseline -> candidate mean per-run median 15.987375 ->16.094500 ms (+0.670%);
p95 19.079750 ->19.509250 ms (+2.251%); p99 21.703500 ->21.589000 ms (-0.528%).
GPU 15.188492 ->15.431802 ms (+1.602%); CPU 3.184664 ->3.167591 process-seconds
per wall-second (-0.536%); private 2534.958 ->2537.673 MiB (+2.716 MiB).
ABBA median/p95/p99 +0.189/-0.550/-2.946%; BAAB +1.163/+5.132/+1.976%.
Draws +3.752% overall (+5.293/+2.175% by block). Live workload variation and
opposing earlier same-binary 1x results prevent a firm no-regression conclusion.
The BAAB p95 increase warrants longer-window investigation; do not average it away.

Visually inspected final-owned-abba-contact.png showing final a4/b4 open-world
captures at both scales. Road, car, shadows, crowd, event marker and HUD are
present without an obvious scene failure. Captures differ in live crowd motion;
this is a scene sanity review, not pixel identity or NPC timing qualification.
The marker-004 discovery screenshot is a separate urban plaza and remains
uncovered. Both DLLs restored to qualified87; owned clear remains opt-in.
A6 open: resolve 1x retention uncertainty, difficult-area coverage, final retention.
## Longer-window 1x retention investigation started (2026-09-09 UTC)

The mixed exact-binary 1x result is unresolved, not accepted or discarded.
Preselected follow-up: eight runs in ABBA/BAAB order, same binaries and start
scene, 72-second measurement windows (source-frame elapsed32-104s; process
elapsed34-106s), rather than the earlier12-second windows. End capture105s,
stop110s. No changes to candidate code. This tests whether the short-window
p95 variation persists over sustained workload; it is not repeated-until-pass.
Retain both block results and all earlier conflicting evidence.

Local harness final-owned-long-abba.ps1 -Scale1, scenario final-owned-long.fh1test,
summarizer summarize-final-owned-long-abba.py1, outputs final-owned-1x-long-abba-*.
Live exec handle75385; poll before another launch. Compiler overlap aborts the
batch and leaves its records rejected. A6 still requires difficult-area evidence.
## Longer-window 1x result (2026-09-09 UTC)

The preselected eight-run ABBA/BAAB batch completed normally with no compiler
contention. Each run supplies4370-4721 frames from seconds32-104; process
samples cover34-106. Exact87/2B hashes verified. Evidence:
p2/final-owned-1x-long-abba-{a1,b1,b2,a2,b3,a3,a4,b4},
final-owned-1x-long-abba-summary.json and summarize-final-owned-long-abba.py.

Baseline -> candidate: median15.977375 ->15.715125ms (-1.641%);
p9519.336000 ->18.736250ms (-3.102%); p9922.020250 ->20.967000ms (-4.783%).
GPU15.259203 ->14.933631ms (-2.134%); CPU3.189935 ->3.162315 process-seconds
per wall-second (-0.866%); private2574.795 ->2553.811MiB (-20.984MiB).
ABBA median/p95/p99 -0.299/-1.521/-0.316%; BAAB -2.969/-4.675/-9.055%.
Both blocks reduce CPU and private memory; ABBA GPU+0.044%, BAAB-4.262%.
Draws-1.546% overall (-0.986/-2.101% by block), so live-workload variation
still limits precise causal performance claims. The earlier short-window p95
increase is not persistent in this longer sample; its records remain intact.
No further unchanged stationary repeat is planned merely to improve averages.

Reviewed final-owned-long-contact.png (a1/b1/a4/b4 end captures): expected
Recaro Rush road, car, crowd, terrain, shadows and HUD remain visible with no
obvious scene regression. Traffic/crowd animation differs between live runs.
Both staged/artifact DLLs verified restored to qualified87. Candidate remains
opt-in pending recorded difficult-area qualification and final retention.
The old locate-town map was also inspected: it locates the Recaro Rush start,
not the discovery plaza. No difficult-area coverage is claimed from this route.
## Difficult-area map navigation identified (2026-09-09 UTC)

Used existing synthetic input tests with qualified87 at1x; no new runtime code.
Map survey PID45580, town-target PID37916 and outpost-target PID34148 all exited
normally. The final screenshot explicitly identifies HORIZON OUTPOST / NORTH
CARSON and offers fast travel for10,000 Cr; current balance301,076 Cr. A route
was set, but fast travel was not purchased. Scripts/captures:
p2/difficult-area-{map-survey,town-target,outpost-target}.fh1test and matching
directories. This establishes an actionable map destination in the urban area,
not proof that its street viewpoint matches marker003/004 or that it has been
qualified. Must compare the arrived scene with original discovery screenshots.

Asked user whether to spend10,000 in-game credits once or have them drive there.
The permission request is for the concrete balance change, not another approval
of renderer testing. Do not repeatedly spend credits for comparison runs.
No game currently running; qualified87 stays staged. A6 remains open.
## Benchmark admission and session audit (2026-09-09 UTC)

Archived session-scoped runtime logs for all24 final benchmark runs before
rotation: runtime-session.log inside each short1x/2x and long1x output directory.
Used tools/fh1_runtime_log.py to isolate exact logging.ready session boundaries.
All12 candidate sessions admit native owned clears (short1x5120-6144,
short2x5120, long1x21504-22528); all12 baseline sessions report zero admissions.
All scenarios complete; none matches the scoped renderer-error patterns used
by the race checker. These counters are periodically logged lower bounds, not
exact total clears or sampled-window-only counts. Summary:
p2/final-owned-benchmark-session-audit.json. This verifies actual native use
behind the timing results, not only the launch argument or DLL filename.

Provenance caveat found during audit: process.start.executable_sha256 is read
from pinyon_shift_build.json by LoadBuildProvenance; it is not a live executable
hash. All24 sessions AND the preceding exact-candidate race sessions report
manifest9D4683C7. Actual on-disk executable hashes882D9247, matching the earlier
directly recorded executable; LastWriteTimeUtc2026-09-09T00:09:23, before these
runs. No evidence of an executable change between those test batches. Do not
use manifest9D as direct binary identity. GPU DLL hashes were directly measured
by the benchmark harness. Future retention probes should record direct EXE hashes
as well. No runtime change or new race rerun is justified by this stale manifest.

Travel approval remains pending. No credits spent, game closed, A6 still open.
## User authorized in-game travel; North Carson reached (2026-09-09 UTC)

User explicitly authorized spending any in-game credits needed for testing.
This supersedes the earlier pending10,000-credit question; do not ask again.
No real-money purchases are authorized or needed. Travel dialogue PID26408 and
confirmed arrival PID22092 exited normally using qualified87. Arrival screenshot
labels NORTH CARSON and captures position(-4271.483398,-5.340042,1186.721313).
The preliminary1x arrival window60-70s has319 frames, median25.039ms,p9559.623ms;
this is a diagnostic probe, not a retention comparison.

Relaunch PID27356 returns to Recaro Rush, so tests must include travel rather
than assume a persistent North Carson start. A second entrance probe is running
via north-carson-entrance-probe.fh1test (exec75077): travel, then reverse six
seconds to expose the street entrance. No save files copied or modified by tools.
Match that view to original discovery marker003 before claiming hard-area coverage.
Goal-tool status still reads blocked from the previous permission wait, but the
user has supplied the missing authorization and work is proceeding in this turn.
## North Carson comparison: rejected navigation batch, corrected1x (2026-09-09 UTC)

User authorizes any in-game credits needed; authorization is not limited to one
travel. Initial north-carson-1x-abba batch is REJECTED: a1 arrived, b1/b2/a2 stayed
in map selecting Carson Lot. Apparent timing gains are invalid; summary explicitly
sets qualification_valid=false. Contact sheets north-carson-1x-contact.png and
north-carson-map-drift.png prove the mismatch. No2x repeat of that failed route.

Adjusted final map stick movements in north-carson-v2.fh1test. Added local
check-north-carson-arrival.py using existing recorded vehicle poses: require
arrival within5m of(-4271.483398,-5.340042,1186.721313), unchanged stationary
position, reverse movement3-100m and end within150m. Checker correctly rejects
known map-only b1 and accepts known arrived a1. Harness now aborts immediately
on failed arrival/motion before continuing; summarizer also requires the check.

All four corrected1x ABBA runs normal, arrival/motion pass, no compiler contention.
Candidate changes: median-18.585%,p95-11.764%,p99-0.416%,GPU-12.002%,CPU+2.736%,
private memory+0.277%,draws-5.059%. These are26-second stationary Outpost windows,
not exact replay or proof of an overall requirement reduction. Detailed evidence
north-carson-1x-v2-abba-* and summary. Corrected2x batch now running (exechandle
returned separately); final image/runtime review and retention still pending.
## North Carson scene coverage complete; 2x tails unresolved (2026-09-09 UTC)

All eight corrected v2 runs (four1x,four2x) exited normally, passed arrival and
reverse-motion checks, and reported no compiler contention. Direct EXE hashes
all882D9247; directly checked DLLs87B79AAB baseline /2B9CED2A candidate.
check-north-carson-sessions.py passes all8 and archives runtime-session.log.
Candidate owned-clear counter increments occur specifically between outpost-ready
and outpost-stationary captures in every candidate run; baseline none. No scoped
renderer-error matches. Contact sheet north-carson-qualified-scene-contact.png
was visually inspected: car/crowd/tent/shadows/fences/HUD intact at both scales
and after reversing. This covers the North Carson Outpost scene corresponding
to discovery marker003 from inside/entrance viewpoints; it does not cover the
separate plaza marker004 or claim identical camera/time-of-day reconstruction.

1x baseline -> candidate (mean of two runs each): median23.6795 ->19.27875ms;
p9533.8835 ->29.8975ms; p9946.2225 ->46.030ms; GPU21.47560 ->18.89818ms;
CPU2.87855 ->2.95731 process-seconds/wall-second; private2742.966 ->2750.574MiB.
2x: median24.762 ->24.437ms; p9554.0615 ->55.3745ms; p9963.165 ->78.6155ms;
GPU23.45398 ->23.22750ms; CPU2.84198 ->2.83712; private4962.414 ->4921.342MiB.
2x p99+24.461% prevents final retention without further investigation. Individual
p99s a1/b1/b2/a2=67.343/66.261/90.970/58.987ms, so this is strongest in b2.
Worst b2 frames100-115ms report GPU intervals21-24ms and zero resolve-readback/
strict-ZPD wait counters. GPU timings may lag frame rows; this is a lead for
CPU/presentation/queue attribution, not proof that the GPU or candidate is innocent.
Do not enable by default or run unchanged repeats merely until a passing mean.
Next work: attribute the difficult-area tail stalls before retaining or redesigning.

The credit permission/access blocker is resolved. User authorizes in-game credits
as needed; do not ask again. Candidate remains opt-in and qualified87 is restored.
A6 remains open for tail investigation and final retention, not for missing access.
### A6 North Carson tail attribution (2026-09-09 UTC)

Temporary command-processor timing fixture `EAD81FC0BB2A8EC5A7CBBE6408F7B818FCFE80C0AF95FF790AD5BE9E43FF0C2D`
compares the same DLL with owned clears off/on. Both corrected v3 routes pass
arrival and motion guards. Earlier two diagnostic navigation failures are excluded;
they stayed at Recaro on the map and did not test North Carson.

The valid pair reproduces broad draw-processing stalls with the feature disabled
as well as enabled: off has a 160.362 ms frame containing 135.191 ms across draws
(max individual draw 2.738 ms); on has a 149.953 ms frame containing 120.755 ms
across draws (max individual draw 2.170 ms). These are wall-time scopes, not thread
CPU time. They narrow attribution to aggregate draw handling/scheduling but do
not identify a specific bottleneck or prove the old clean regression unrelated.
Capture-related swap stalls are excluded from clean performance windows. GPU CSV
intervals retire asynchronously and cannot be paired naively with a CPU row.

Evidence: `p2/north-carson-2x-tail-v3-{a1,b1}/{tails.json,runtime-session.log}`.
Profiling overhead is not used for retention performance. A WPR CPU recording
attempt failed to enable the system profiling policy (0xc5585011); no recording
started and no OS policy was changed. Diagnostic source has been restored and
rebuilt: production candidate hash is again `2B9CED2AEB9270BCECA5FC981BE8539D72A3101AC0B8F42CFF89AE3119F60F10`.

Before seeing results, a clean four-run ABBA at 2x is fixed to an 86-second
stationary window (source frame clock 62..148 seconds), followed by the existing
reverse/brake motion route. The original short-window results remain evidence;
this batch tests sustained difficult-area tails rather than selecting a better
slice of the existing recordings. A6 remains open pending this comparison.
### A6 complete: retain 1x owned depth; scaled fallback (2026-09-09 UTC)

The longer clean 2x North Carson ABBA fails retention: median 21.121 -> 21.462 ms,
p95 29.953 -> 62.238 ms, p99 49.152 -> 93.433 ms (+90.09%). GPU 21.546 ->
23.460 ms; process CPU 3.413 -> 3.332 seconds/wall second; private 4990.2 ->
4954.1 MiB. All four arrival/motion/session checks pass without compiler overlap
or renderer errors. The initial short +24.46% p99 result remains recorded.

Retain the demonstrated 1x chain instead: enable `fh1_owned_depth_clear` by default
with an explicit symmetric-1x guard before native preparation. Scaled rendering
continues through the qualified compatibility clear path. The 1x implementation
is otherwise unchanged from measured2B; its longer ordinary-scene median/p95/p99
improve 1.64%/3.10%/4.78%, and North Carson median/p95 improve 18.58%/11.76% with
approximately flat p99. CPU/private-memory tradeoffs are recorded in the report.

Final retained DLL: `27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50`.
Actual EXE: `882D9247F23B97B0121A0D7F15F3EFB4569728777A26F03EF2B676D8A9DBCB52`.
Release DLL build, ownership/lifetime checker, final exact-DLL default-setting
1x and 2x race-start checks pass. Sessions `20260909T222559Z-p18136` and
`20260909T222721Z-p21300` record respectively 10,240 and zero native owned clears;
simulation/wall ratios 1.004550/1.003516, all captures/HUD checks, normal completion,
no renderer errors. Images inspected. The first final harness accidentally staged
baseline87; its failed native-counter gate is excluded and corrected v2 checks
assert DLL identity. No profiling code remains; staged/artifact DLLs are retained27.

[A6 retention report](A6_OWNED_DEPTH_RETENTION.md) records the exact scope,
measurements, local evidence and reproduction. A1-A6 are complete for useful
retained ownership at 1x; the failed 2x optimization is a B1 follow-up requiring
new attribution or a changed design. Guest decoding, ownership transitions,
float-depth history, EDRAM dump and resolve publication remain compatibility
requirements. Full Xenos retirement, broader town slowdown fixes and hardware
claims remain open. No publication is part of this closure.

## B epic execution, 2026-09-10 UTC

The B1-B4 goal is active. [B execution and coverage](B_EPIC_EXECUTION.md) fixes
the required scenes and resource families, records a tested discovery pass-count
correction (zero collisions and exact live draw accounting), and describes an
opt-in full-tile depth/stencil clear candidate for base-0 D24S8. The candidate
builds and runs but has not passed content/history and retention gates. A6 stays
qualified at 1x only; its unchanged failed 2x design remains disabled. All B
items remain open. Direct binary identities and local evidence are in that doc.

## B epic follow-up: tile-clear correctness, no new retention (2026-09-10 UTC)

The base-0 full-tile clear candidate passes nonzero depth/stencil and untouched-
region checks at 1x/2x, both outgoing pixel transfers, the EDRAM dump and final
RGB7e3A2-to-RGB10A2 tiled texture publication. Independent models report zero
mismatches. Production ownership checks now cover mixed-owner eviction and
same-key recreation; two live eviction requests followed by Recaro race-start
and driving checks pass at both scales. These are correctness proofs within the
recorded contracts, not full scene coverage or device-reset qualification.

No candidate enabled. Initial 1x ABBA is unfavorable (+14.30% median) with a
+13.15% recorded draw-workload difference. Longer 2x Outpost ABBA initially
appeared to worsen p95 by 26.22%, but image review found A2's HUD/prompt hidden
while the other runs retained them. That block is now explicitly invalid for a
matched renderer comparison; do not claim that number as a proven regression.
New tools/check-fh1-outpost-workload.py passes A1/B1/B2 and rejects A2. Control
and validate activity/HUD state before another long route; preserve the rejected
block. Do not simply repeat unchanged tests seeking a favorable result.

Detailed identities, raw result tables, replay/check scripts and limitations:
[B epic execution](B_EPIC_EXECUTION.md). Candidate source remains default-off
with original hashes; unseeded DLL5ED43C... is archived, not retained. Diagnostic
seed DLL81988E... and eviction DLL764637... never become runtime defaults.
Qualified root/artifact DLL remains27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50;
actual EXE3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3.
B1-B4 remain open. Next attribute changed work/cost or pursue the next valuable
chain, continue full scene/dependency accounting and B2-B4 implementation.


## B2 checkpoint: allocation recycling remains experimental (2026-09-10 UTC)

Continue from [B execution and coverage](B_EPIC_EXECUTION.md), its B2 sections.
New measured CPU attribution finds geometry creation/eviction/import consuming
41.629 ms of one 80.009 ms Outpost interval. An opt-in same-sized, completed-
submission buffer-recycling candidate avoids about 40% of observed new-window
allocations there without enlarging the 32 MiB budget. The production-body cache
check, Release build and a nonzero 128 KiB live GPU-copy/first-consumer audit pass.

Retention is not established: the 2x Outpost block has unfavorable reverse tails
and later collision/camera divergence; free 1x/2x Recaro blocks have low activation,
varying traffic/work and mixed tails. Do not enable recycling or repeat unchanged
short comparisons to fish for a gain. The paired Outpost cost run is invalid: the
game refused its 10,000 CR fare with only 1,076 CR left. Paid travel must wait for
normal gameplay credits or a qualified free driving approach; saves were not edited.

A focused probe additionally shows the historical largest-containing-window policy
can redirect a CPU snapshot lookup while a held GPU address still names the earlier
small window. Exact-key and an isolated smallest-containing lookup preserve that
identity in the probe. No containment change is made in production; this supplies
a concrete constraint/new design to investigate, not qualification to enable it.

Production source keeps both tile ownership and recycling default-off; A6 remains
1x-only. Candidate DLL: 8AF0207FE28A2D5FC26F2E45205B9DB13F55FA7EA79DCAEA854027D67C41011F.
Qualified root/artifact DLL is restored to
27B486FD5BBD928B90186AF2778D8489F364B3C78993FDB7818CC8514E318B50.
EXE: 3721619222F6269492B40D91CD4972A7C7536E82C2F7067958F76BD8229AFFD3.
Minimal source diffs/hashes, diagnostic fixtures, raw runs and checks live in
.local/native-renderer/b2/. Every launched game/replay/build has exited.
Next: investigate stable overlap ownership or another measured B2 reduction,
qualify sustained motion/lifetimes and cost before retention, and continue the
fixed B1 scene/dependency inventory plus B3/B4. The B1-B4 goal remains active.


## B checkpoint — 2026-09-10 UTC

See [the source checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md) for exact
identities, stable-containment implementation and bounded 1x GPU validation.
Both 2x instrumented attempts failed before usable capture/route completion;
the candidate logs a guest null read, while the feature-off control does not.
Containment, recycling and tile-clear experiments remain default-off and
unretained. A6 retains its 1x scope. B1-B4 remain active and incomplete.


## 2026-09-10 follow-up: containment proof and guest clear producer

See [B execution](B_EPIC_EXECUTION.md) and the
[current checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md). The revised
capture fixture provides bounded 2x GPU validation: 18/19 checked owners,
24/25 representative consumers and one actual 65,536-byte copy per frame all
match. The 18 common owners are unchanged; live mutation/streaming remains open.
The longer 1x comparison is incomplete after a 20.03 m stationary displacement;
no ABBA verdict or retention follows. Preserve the failed workload and qualify a
changed stationary route before further comparison. Retained DLL `27B486...`
is restored at both runtime paths, and all experimental flags remain default-off.

B3 now has a checked static upstream anchor: `sub_8240E130` emits the known
clear shader from `0x820C5FD0` via copy callsite `0x8240E4A8`; the direct wrapper
calls it at `0x824019D0`. This establishes where to measure obsolete guest work,
not that it can all be skipped. Device dirty state, rectangle/scissor handling
and command-buffer refill/flush still need a live contract. No producer bypass
or CPU saving is claimed. B1-B4 remain open with their full original criteria.


## 2026-09-10 B3 attribution: clear emission has a small CPU contribution

The new opt-in producer trace measures roughly 0.03-0.045 ms per local gameplay
frame at the median for all 15 clear invocations together. It observes 108 + 36
shader-copy bytes per invocation, with no pairing errors. This makes a complex
rewrite of this producer a low CPU priority in the measured scene; downstream
GPU decoding and other producers remain unmeasured. B3 is still open, including
its actual pre-packet bypass requirement. Return first to measured geometry
preparation while retaining the producer anchor for later complete-chain work.
See [B execution](B_EPIC_EXECUTION.md) for phase tails, diagnostic overhead,
1x/2x identities and the 2x wrapper's unrecorded OS exit-code limitation.
The qualified EXE/DLL are restored; the trace is source-only and default-off.


## 2026-09-10 B2 comparison: no containment retention

The completed 1x handbrake C-A-B-B-A-C block holds the player stationary, but
traffic differs and timings are mixed. At the last periodic records, candidate
mean imports rise from 4,934.5 to 5,430 and imported bytes from 340,328,448 to
402,128,896 against same-binary exact mode; no recurring-work reduction is
established. Qualified-DLL controls also show mixed differences. The 2x free-road
block is deferred after review, and containment remains off. Full numbers and
scope are in [B execution](B_EPIC_EXECUTION.md).

The next workload lead is a retained-build closed-course Recaro Rush probe:
it completes with a fixed 68..103-second pose and verified race HUD/motion.
One probe is not matched performance or sustained streaming evidence. Use it
to establish representative cost/repeatability, while preserving the entire
B1 scene set and every B2/B3/B4 completion requirement.


## B follow-up: CRT correction and thumbnail coverage (2026-09-10 UTC)

The separate CRT scope defect is corrected and bounded 1x/2x race smoke checks
pass on candidate EXE `C24D88...`. Existing simulation-delta observations and
startup errors remain documented; no performance or renderer-crash fix is
claimed. Baseline EXE `372161...` and retained DLL `27B486...` remain staged.
See [B execution](B_EPIC_EXECUTION.md) and the
[checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md) for exact identities.

The Recaro car-selection screen has visibly corrupted thumbnails in both the
retained 1x control and corrected 1x/2x runs. Add its producer/upload/consumer
chain to B1's unresolved menu coverage. This is a correctness observation, not
cost attribution or evidence for widening native admission. All B items remain
open; the prior containment rejection and small clear-producer CPU opportunity
still determine the next implementation choices.


## B2: narrower CPU invalidation lead (2026-09-10 UTC)

CPU-page fingerprints identify substantial repeated imports. A new default-off
64 KiB invalidation limit passes range/ownership checks and two bounded 1x
on-runs reduce hold-phase imports to about 183/182 per second versus 405 in
the first off control. The full clean comparison is incomplete: A2 lacks its
early race HUD, C2/2x are unrun, and the old acceleration window overlaps a
capture. **No retention or general FPS gain.** See
[B execution](B_EPIC_EXECUTION.md) and the [checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md).

Qualify actual measurement-phase HUD bookends with captures outside timed
windows, preserving the early-HUD issue explicitly. A separate unimplemented
lead is avoiding the GPU reimport for a CPU-snapshot upgrade while the existing
owner watch remains valid. Retained DLL `27B486...` and the full B scope remain.

Later attribution: the CPU-only snapshot shortcut saves under 0.4% of observed
imported-plus-avoided bytes at either scale. Its implementation is archived and
removed; the 12,451 earlier snapshot requests included new/dirty owners. Prioritize
the larger 64 KiB invalidation lead, which still has no retention result.

The revised strict HUD comparison also stops, and denser sampling now reproduces
brief missing-HUD captures in both retained and candidate-off paths. Attribute UI
generation/drawing and output publication/capture before further retention runs;
matching car poses miss a six-second race-entry offset in the latest control.
The full records and unchanged B1-B4 scope are in [B execution](B_EPIC_EXECUTION.md).
The early-race interval also shows roughly 56..85 ms source-frame medians in
dense/sparse capture observations before recovery. Prioritize attribution of
that active racing workload and UI gap; late stationary comparisons alone miss
it. A 30-FPS-cap probe is inconclusive because that interval only achieves about
15 source FPS. These are diagnostic observations, not retained speedups.

Latest attribution (`20260910T072547Z-p23496`) promotes **early-race geometry
buffer churn** as the next B2 investigation: about 45 creations/evictions and
22.47 ms allocation-plus-eviction CPU per source frame, versus 0.54 ms import
CPU. These are instrumented measurements, not independent frame savings. Test
the existing exact-size recycler's removed work here before designing a larger
capacity reuse path; the latter remains unimplemented. The 64 KiB invalidation
lead and full mutation/streaming/retention requirements remain open.

Output-resource joins map two missing-HUD captures to source frames lacking all
148 draws from three shader pairs present in passing neighbors. Their correlation
with the missing HUD does not establish HUD production; two are cataloged as
world-lit specializations. Resource-chain/producer attribution and host-visible
behavior remain unproven. GPU timings are
sampled every 60 source frames, so missing records cannot be counted as zero
cost. See [B execution](B_EPIC_EXECUTION.md) for exact identities, intervals and
limits. Qualified binaries/defaults and all B1-B4 completion criteria are unchanged.

Follow-up: **matching-victim exact-size recycling** is now the next B2 candidate
for GPU-content and matched performance qualification. SDK `acd222c` searches
the existing bounded cache for the oldest completed matching allocation, with
no new pool, capacity field or budget increase. The larger-capacity experiment
was implemented, measured and archived after sharply higher native-cache
rejections and late recurring work. Both designs' evidence is preserved.

The exact-size search observes about five early-race creations/frame and no
late allocations/evictions in its diagnostic, then passes clean 1x/2x strict HUD,
hold and motion smoke checks. It remains default-off and unretained; these are
not matched performance or sustained streaming results. See
[B execution](B_EPIC_EXECUTION.md) and the [checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md)
for binary identities, known defects and the unchanged full B1-B4 scope.

Latest qualification: 18 actual 2x matching-recycler copies (2,293,760 bytes)
and first draw consumers pass GPU byte checks; ten reuse a matching victim
beyond the oldest entry. The adjacent capture has no marked copies and adds
no proof. Direct replay verifies HUD writes from nine sampled draws of the
three previously correlated shader pairs, strengthening the upstream HUD
omission lead without identifying its cause. A single-confirmation retained
route passes strict HUD/hold/motion but demonstrates why race-clock alignment
must accompany pose checks. Prioritize that qualification before matched
1x/2x retention; fresh 1x GPU, sustained streaming, memory/tails and the full
B1-B4 scope remain open. Detailed evidence is in [B execution](B_EPIC_EXECUTION.md)
and the [latest checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md).

Later qualification adds delivered-input/capture-clock checks after the first
new block fails event arrival. A braked-entry same-binary off/on pair preserves
race stage and HUD/motion while early median improves 46.015→25.222 ms and
periodic allocations fall 23,707→4,006. Handbrake p99 rises 11.28%; this remains
a single diagnostic pair without memory/2x/streaming retention. Continue
repeated qualification with the new timing gates, not default enablement.

Checkpoint follow-up: the preselected repeated C-A-B-B-A-C block has completed
only its first C/A/B at 1x. Input, clock, race-stage and HUD/motion gates pass;
matching process CPU/RAM/fault and per-process GPU-memory samples are available.
The second B/A/C and all 2x runs remain pending. The first B again reduces early
frame cost and allocations, while later tails and import rates are mixed.
Keep the matching-victim candidate default-off until the complete comparison,
GPU/lifetime and full scene-set requirements pass. See
[B execution](B_EPIC_EXECUTION.md#repeated-recycler-comparison-with-process-and-gpu-memory-sampling)
for all completed results and the [checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md)
for the exact next run. No B item or hardware-requirement claim completes here.

The final 1x retained control subsequently skips a scheduled menu pulse, so
the repeated block is stopped rather than qualified. Wider pulses are a new
prospective protocol. A normal 1x injected run verifies 12 actual recycled
copies and first consumers; a preceding capture crash and an adjacent frame
without marked copies remain explicit limitations. The off control also adds
eight missing precompiled variants to B1 coverage. SDK `202247a` now logs and
flushes both presentation/device-loss HRESULTs before the fatal callback.
This improves attribution, not speed or retention. Static B4 postprocessing
anchors are checked; actual cost, side effects and NPC/UI timing remain open.
See the latest B execution/checkpoint for source/binary identities and resume
order. The full B1-B4 goal is active and experimental recycling stays off.

Latest checkpoint: the eight apparent variant gaps are caused by stale AppData
1x pack staging. All eight exist in the current local packs; the newer 1x pack
preserves every old entry and is now staged explicitly. The first control of
a fresh widened-pulse comparison passes input/clock/HUD/motion checks with zero
GPU errors. Five further 1x and all six 2x runs remain; no new performance
retention or B-item completion follows from this control. See
[B execution](B_EPIC_EXECUTION.md#shader-misses-traced-to-stale-staging-prospective-comparison-v2)
and the latest checkpoint for pinned identities, metrics and resume order.

The subsequent A2 fails the early-HUD gate despite correct pack/input delivery,
stopping v2 before its last 1x control or any 2x run. Two diagnostic probes
reproduce the defect at decoder and indirect-buffer boundaries: full observed
HUD-list references disappear while short, unskipped references remain. Their
producer, contents and publication order need tracing before new retention
runs. Early recycling gains repeat, but later hold tails worsen and no setting
is retained. See [B execution](B_EPIC_EXECUTION.md#v2-stops-on-an-early-hud-gap-trace-the-indirect-buffer-submission)
for the complete results, exact diagnostic identities and B4 dataflow correction.

CPU/list-content tracing now identifies the short lists as scissor-only setup
and follows their submission through the guest's twelve-slot queue and render-job
dispatcher. Most come from queue draining, but a reproduced missing-HUD frame
also has two empty normal-mode lists. Follow producer/finalizer generation and
handoff before any presentation workaround or fresh retention comparison. The
broad dispatcher probe hit its cap and remains rejected; the narrowed probe
completes accounting without fixing the defect. See
[B execution](B_EPIC_EXECUTION.md#cpu-submission-queue-and-dispatcher-evidence).
  No B item, performance setting or hardware claim is retained by this evidence.

  Subsequent lifecycle and enqueue attribution moves the defect upstream:
  drawing jobs are discarded during recording before some lists are consumed
  in normal mode. The checked enqueue prefix links 48 such cycles; that run
  still fails its trace cap, and the lifecycle run misses one early capture.
  Follow the per-frame queue discard policy before resuming comparisons. See
  [producer evidence](B_EPIC_EXECUTION.md#empty-normal-mode-lists-originate-in-producer-side-job-discards).

The next local prototype retains jobs within a checked HUD recording span
until the existing worker makes its render/drain decision. Its complete
selected-outcome trace has no cap failure: 506,175 jobs reach recording despite
the old discard inputs, and 3,893 matched cycles contain no empty normal-mode
submission. All 27 captured HUDs and 8,421 slot lifetimes pass their checks;
drain mode still skips drawing. This is bounded stationary 1x evidence, with
51 present drops in an instrumented run, not performance or retention proof.
Memory pressure, full scenes/motion and clean repeated comparisons remain next.
See [prototype evidence](B_EPIC_EXECUTION.md#hud-admission-prototype-passes-bounded-correctness-checks)
and the [checkpoint](NATIVE_RENDERER_CHECKPOINT_2026-09-10.md#latest-handoff-hud-admission-prototype-awaits-retention).
The production path is restored, recycling stays off, and B1-B4 remain open.

The clean HUD candidate now passes enabled 1x/2x motion preflights and all four
1x A-B-B-A workload checks. Memory observations do not show higher peak private
use, but acceleration p99 rises 28.87% across the two enabled repetitions due
to one five-frame burst. Both enabled runs also report more startup mailbox
replacement drops; localization places all drops before ten seconds, outside
the race windows. Keep those findings explicit and adoption unqualified.
At that checkpoint all matched 2x runs remained pending; broader lifetime/scenes
and UI/NPC timing remain open. See
[clean comparison](B_EPIC_EXECUTION.md#clean-hud-admission-both-preflights-pass-1x-comparison-remains-unqualified).

The matched **2x block now stops at B1** (`20260910T125513Z-p8816`):
automated HUD/pose/motion checks pass, but manual prestart review finds green/
white windshield and colored headlight artifacts absent from A1. B2/A2 stay
unexecuted. Keep the failed visual evidence and existing 1x tail/startup results;
there is no valid 2x performance comparison or retained HUD correction.

A separate RenderDoc diagnostic (`20260910T130420Z-p22000`) exits normally but
does not reproduce the artifact. Its two GPU captures are clean references.
An inventory and pixel history are available, but reused/tiled target coordinates
have not been mapped to the failing windshield surface. Also establish whether
the admission helper's vtable/owner predicate applies beyond the sampled HUD
instance; the predicate alone is not proof of HUD-only scope. Attribute the
failure before another qualification design. See
[failure and diagnostic evidence](B_EPIC_EXECUTION.md#clean-hud-admission-2x-comparison-stops-on-a-visual-failure).
Retained runtime/source hashes are restored and verified, the complete 1x pack
is staged, recycling stays off, and every B1-B4 completion criterion stays open.

Reference attribution now identifies the fixed-function renderer's constructor
and the glass material's active inputs. Three scene strips plus a later
180-degree UV reorientation explain why the first raw pixel history cannot
be assigned directly to the windshield. Glass pair `CE0FFEB0986E9971` /
`1D38BA65C9D3C506` selects cube fetch 2 (`1C879000`, mip `1C9F9000`) and 2D
fetch 13 (`1CE2D000`). The clean frame has no cube writes, so earlier production
and publication are the next resource-history targets. This adds diagnostic
anchors, not a measured optimization or failed-frame attribution. See
[reference glass inputs](B_EPIC_EXECUTION.md#reference-glass-inputs-and-fixed-function-renderer-scope).
