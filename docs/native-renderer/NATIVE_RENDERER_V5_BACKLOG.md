# Forza Horizon 1 Native Renderer V5 Backlog

Status: active implementation record, 2026-09-04

V5 keeps the V4 strategy: recognize and replace the exact GPU work emitted by
Forza Horizon 1. It is not a general Xbox 360, Xenos, Xenia, ShiftGlue, or
ReXGlue renderer project.

This backlog supersedes V3 for prioritization. Older documents remain useful
as evidence, especially where they record failed approaches or exact FH1 pass
identities.

Launcher-side production, device warmup, and multi-vendor qualification continue
in the [V6 backlog](./NATIVE_RENDERER_V6_BACKLOG.md).

## Final goal

Replace as much of the Xenos renderer's FH1 workload as is correct and useful,
then delete the superseded prototype and discovery code.

Complete removal is preferred, but not at the cost of guest-visible
correctness. A small compatibility core may remain for command decoding,
memory exports, queries, synchronization, or rare fallback work when replacing
it would cost more than it saves. Success is measured by work no longer done,
lower hardware requirements, stable frame pacing, and correct FH1 output—not by
renaming Xenos code or creating a new renderer framework.

## Scope lock

- Target only Forza Horizon 1, title ID `4D5309C9`, on the current D3D12 host.
- Hard-coded FH1 pass, shader, attachment, and mode identities are allowed.
- Keep the guest simulation at its original rate. Higher presentation FPS must
  not change physics, AI, scripts, audio, input sampling, or save behavior.
- Reuse the existing presenter, pacing scheduler, and D3D12 resources before
  adding code or dependencies.
- Add an abstraction only after two real FH1 call sites need it.
- Unknown work fails closed to the proven path until its replacement passes
  visual, side-effect, and performance gates.

## Current baseline

- V4 prewarms known FH1 pipelines and fast-paths the pass beginning at
  attachment `4A23C979E555853F`, draw `39E7407EABA44369`.
- V4 is still hosted by the Xenos D3D12 command processor. It does not yet make
  a native FH1 frame authoritative or suppress most Xenos GPU work.
- At a 30 Hz simulation and 60 Hz host presentation, the presenter commonly
  displays every new game frame once and then presents one duplicate. That
  duplicate slot is the first interpolation target.
- V5 does not use FSR, FidelityFX Frame Generation, or another external frame
  generation dependency.
- The old 2x accumulator experiment caused incomplete output and
  `DEVICE_HUNG`/TDR failures. It is evidence, not the V5 upscaling design.

## Milestone order

### V5-03 — Account for and retire the hottest Xenos work

Turn the V4 execution corpus into a deletion list, not another general pass
classification system.

Current target:

- pass family `FA79E5778D949D02`;
- attachment `4A23C979E555853F`;
- first family `B45B38234A27121C` and first draw `39E7407EABA44369`;
  and
- 87–121 draws per observed frame, measured at 1.69 ms average GPU time in
  AppData-backed session `20260902T194551Z-p39648`.

The first attempted V5 boundary only skipped full-key construction after the
generic command processor had already prepared and issued each draw. Matched
AppData-backed runs rejected it: baseline session
`20260902T182227Z-p27160` measured a 33,085 us median and 35,343 us p95 frame,
while candidate `20260902T181649Z-p22396` measured 33,325 us and 36,255 us
despite reporting 740,586 covered draws and no fallbacks. The candidate was
0.7% slower at the median and 2.6% slower at p95, so the branch and its
misleading native-authority counters were removed. V5-03 remains open until an
executor bypasses material Xenos preparation or GPU work and passes this gate.

The first exact replacement landed for the one-draw pass
`8E5438D6E9B49B79` / execution `A20B16064DBF09DF`. FH1's translated path used
eight 160-pixel vertical rectangles and a 165-instruction pixel shader to
point-sample the resolved 1280x720 scene and apply its final square-root tone
map. The V5 path validates the exact execution key, shader pair, 384-byte mesh,
source binding, attachment, sample count, and hazard state, then replaces it
with a title-specific fullscreen D3D12 draw and suppresses the Xenos draw only
after the native draw succeeds. A reverse-order title-screen pair recorded
1,857 compatibility samples at 1,472,951 ns average versus 1,857 native samples
at 784,414 ns average: 688,537 ns, or 46.8%, removed from that pass. The native
run reported 1,858 equivalent Xenos draws removed and no device error. This is
not a recurring gameplay retirement: its counter stops after title/loading,
so it does not contribute to the V5-03 exit gate.

The first recurring gameplay retirement now replaces velocity-dilation family
`5B8F44932893A6CE` on attachment `BD706BD142DBDE84`. The FH1-only executor
validates the exact shader, pipeline, attachment, resource, operation,
constant, texture, render-target, and hazard state, performs the title's
point-sampled one-pixel vertical dilation in a native fullscreen draw, and
suppresses the Xenos draw only after the native draw succeeds. AppData-backed
session `20260902T200015Z-p7088` removed 390 of 390 equivalent Xenos draws,
rendered free roam without visible corruption or flicker, and exited normally.
The first comparison averaged 187,948 ns versus roughly 194,000–203,000 ns in
recent Xenos runs. A longer static free-roam pair then measured 165,058 ns for
1,058 native samples in session `20260902T200746Z-p46360` versus 220,462 ns for
1,059 Xenos samples in session `20260902T200344Z-p11104`: 55,404 ns, or 25.1%,
removed from this pass. Both runs exited normally and the native run removed
1,117 equivalent Xenos draws overall. This establishes repeatable native
authority and an out-of-noise gain for one recurring pass, but it is only one
draw per frame. At that point V5-03 still required the fixed-race check and
the material 1.69 ms scene-family target.

The first material-scene replacement targets FH1 vertex shader
`79034645B1CB882B` with pixel shader `CAE1DB68AFFA9D3C`, pipeline
`54F089D48255B100`, and attachment `4A23C979E555853F`. It substitutes a direct
FH1 HLSL vertex shader for the translated Xenos vertex program while retaining
the proven pixel shader, fixed-function state, resources, and fail-closed PSO
fallback. AppData-backed session `20260902T202220Z-p47388` reached the saved
free-roam scene, rendered without visible corruption or flicker, exited
normally, and reported 50,730 translated Xenos vertex executions removed.
Pass family `FA79E5778D949D02` averaged 1,265,946 ns over 1,124 samples. The
immediately following translated-path run `20260902T202710Z-p47384` loaded the
same save and view and averaged 1,694,884 ns over 1,082 samples: 428,938 ns,
or 25.3%, removed from the scene family. Neither run logged a pipeline-creation
or device error. This supplied the controlled fixed-view performance gate;
the fixed-race correctness gate was completed later.

A longer AppData-backed validation, `20260902T203043Z-p46384`, exercised the
title screen, menus, Race Central entry/exit, free roam, and a day/night
transition without visible corruption or flicker, removed 142,917 translated
world-lit vertex executions, and exited normally. The scene family averaged
1,274,935 ns over 3,166 samples. This broadens mode coverage but is not the
required fixed-race comparison.

A second direct vertex substitution for shader pair
`ED90DA6EFF5C6BCA` / `57B9400F6B398736`, pipeline `6007AED1FE9E0F31`,
was rejected and removed. After correcting a stale runtime-DLL deployment,
session `20260902T210104Z-p40500` proved that the candidate executed 64,042
times and rendered cleanly, but the same scene family averaged 1,736,539 ns
over 1,566 samples. That regressed the retained world-lit native run and did
not beat the 1,694,884 ns translated baseline, so fewer host instructions alone
were not sufficient evidence of a useful replacement. The immediate rollback
session `20260902T210759Z-p43952` restored the retained world-lit-only path,
rendered the same saved view cleanly, removed 84,421 translated world-lit
vertex executions, and averaged 1,225,327 ns over 1,872 samples. That 29.4%
recovery confirms the rejected candidate—not ordinary run variance—caused the
regression.

A later recurring one-draw candidate using vertex shader
`C7D52884ECA9A039` and pixel shader `E68FE55ECD482EC5` was rejected before an
executor was added. Disassembly showed a roughly 416-instruction pixel shader
with dynamic constant-buffer indexing and many guest float constants. It was
not a small, exact fullscreen operation, so a direct replacement would have
duplicated substantial Xenos semantics without evidence that it was the next
useful FH1 target.

V5-04 added a second profitable direct world vertex substitution for exact
shader pair `984DBF6AF14DBEBD` / `6FDA0F1CDE67D12F`, pipeline
`E51530EC1E65DC58`, and attachment `4A23C979E555853F`. It preserves the
translated pixel shader and existing resources, and falls back to the
translated vertex shader if its native PSO cannot be created. Candidate
session `20260902T235723Z-p25376` rendered the saved Recaro Rush free-roam view
cleanly, exited normally, removed 17,766 translated vertex executions, and
averaged 1,259,434 ns for pass family `FA79E5778D949D02` over 2,515 samples.
The same-view control `20260903T000140Z-p48900`, with only this substitution
disabled and the retained native path unchanged, averaged 1,443,645 ns over
3,116 samples. The exact addition removed 184,211 ns, or 12.8%, from the hot
scene family without a pipeline or device error, so it is retained.

The FH1 vertex substitution for `D25C81F5BF6DD4C6` was removed. Although its
captured free-roam pass saved 108,635 ns, it also consumed the same shader in
the HUD and map: the live minimap disappeared and the SELECT map lost its road
and icon layers. A V4-on/V4-off comparison reproduced the fault, and disabling
only this substitution restored both overlays while every other native path
remained enabled. V5-04 therefore keeps the translated Xenos vertex shader for
this shared UI/scene program rather than adding mode-specific admission state.

V5-04 also retains a depth-only mesh substitution for the four identical FH1
vertex programs `9BF2991815B941B9`, `C8C39E5AE1B08DE6`,
`B646F85EF69A57E0`, and `D0C40C04F166092E`, specialized only by their captured
20/24/28/32-byte strides. Admission is restricted to the eight captured
pipeline/attachment pairs on `1D55CD5276D9AA51` and `36602A7E532469D3`, with
no pixel shader and no hazards. Candidate session `20260903T003406Z-p48924`
rendered the saved Recaro Rush view cleanly, exited normally, and removed
263,669 translated vertex executions. Against same-view control
`20260903T003818Z-p26932`, the stable 198-draw pass fell from 1,272,829 ns to
1,145,441 ns (10.0%) and the 117-draw pass from 1,144,379 ns to 943,434 ns
(17.6%). The two 325-329-draw attachment-`36602A7E532469D3` families improved
by 4.8% when weighted by samples. Neither run logged a pipeline or device
failure.

An exact alpha-shadow pixel replacement for vertex/pixel pair
`41138347EF20F84C` / `5246C7C219B57DDB` and pipeline
`AFDE61E5EB2C3685` was implemented and then removed. Candidate session
`20260903T010426Z-p32412` rendered the saved Recaro Rush view cleanly,
exited normally, and replaced 53,663 translated pixel executions. Against
same-view control `20260903T010827Z-p45656`, however, the stable pass-family
changes ranged from a 1.4% improvement to a 1.5% regression. That is
measurement noise rather than a profitable retirement, so V5-04 retains no
shader, counters, admission code, or cache changes from this candidate.

An exact shared terrain-depth vertex replacement for shaders
`CA293E0A1CB4B416` and `4E1DA281CC3D7EDB` was also implemented and removed.
Candidate session `20260903T012335Z-p48980` rendered the saved Recaro Rush
view cleanly, exited normally, and replaced 140,825 translated vertex
executions. The 80-draw family averaged 984,227 ns, but the immediately
following translated control `20260903T012751Z-p40044` changed the larger
pass to a different dynamic family and averaged 1,097,083 ns for the 80-draw
family. Against the earlier stable control, the candidate instead regressed
that 80-draw family by 1.6% while improving the larger matching family by only
2.7%. The gain was not repeatable across valid fixed-view captures, so the
shader, bytecode, counters, and admission code were deleted.

The exact one-draw four-tap pass using vertex/pixel pair
`D5E12A97B3A84881` / `58CE51CE56247C16`, pipeline `4040F6AF2D8DAFC4`,
and attachment `9A79B32F7ECF54CF` was likewise implemented and removed.
Native session `20260903T021930Z-p792` rendered free roam, its minimap, and
the SELECT map correctly and replaced 2,252 translated draws, but averaged
705,331 ns after 2,251 samples. The translated control
`20260903T020820Z-p35932` averaged 657,325 ns after 668 samples. The native
replacement was 7.3% slower and produced substantially more dropped timing
samples, so V5-04 retains no code or shaders from it.

The paired manual race gate used native session
`20260902T233441Z-p47636` and compatibility session
`20260902T234335Z-p46980`. Both completed the same offline race and exited
normally without a GPU device-loss or pipeline-creation error. The native run
removed 644 tone-map draws, 10,304 velocity-dilation draws, and 423,868
translated world-lit vertex executions. Its target scene family averaged
1,208,326 ns over 9,395 samples versus 1,256,080 ns over 3,217 compatibility
samples. The captures had different aggregate draw mixes (65–272, average 136,
versus 93–290, average 214), so the 3.8% aggregate race delta is correctness
and coverage evidence, not the controlled performance claim. The controlled
saved-view pair above remains the performance gate at a repeatable 25.3% gain.

V5-03 is complete: recurring velocity GPU work is native-authoritative and
absent from Xenos, the material world-lit scene workload executes a direct
FH1 vertex shader, the fixed free-roam comparison is outside measurement
noise, and the fixed race exercises both replacements without renderer
failure. Further scene retirement continues under V5-04 in measured order.

Work:

- Measure CPU time, GPU time, draw count, bandwidth, and frequency for exact
  FH1 pass identities during one fixed race and one fixed free-roam route.
- Fix only corpus ambiguity that prevents selecting or validating those hot
  passes.
- Promote the highest-cost proven V4 pass family to an FH1 direct executor.
- Suppress its equivalent Xenos draws after output, resource lifetime, resolve,
  query, and memory-export behavior match.
- Report both native coverage and Xenos work actually removed per capture.

Exit gate:

- At least one recurring gameplay pass is native-authoritative and its Xenos
  GPU work is absent, with matching output and guest-visible side effects.
- The fixed routes show a repeatable CPU or GPU gain outside measurement noise.

### V5-04 — Native-authoritative gameplay scene

Replace the expensive passes that form the normal driving view, in measured
order: opaque world, road/terrain, vehicle, shadows/reflections, transparencies,
post-processing, and HUD.

Each pass family must:

- use its exact FH1 identity and already-captured resources;
- preserve resolves and guest-visible side effects;
- fail closed on an unknown variant;
- suppress the equivalent Xenos visual work only after comparison passes; and
- delete any older observer or prototype made obsolete by the replacement.

Exit gate:

- Normal free roam and racing use a native-authoritative final frame.
- Xenos is no longer the visual authority for the supported gameplay modes.
- Remaining fallbacks are enumerated by exact FH1 mode/pass and measured cost.

Clean free-roam session `p47424` rendered normally, retained the live minimap
and the SELECT-map road/icon layers, and exited normally without a device-loss
or pipeline-creation failure. Final manual race session
`20260903T023429Z-p26184` also looked and played correctly, exited normally,
and recorded no renderer, pipeline, validation, TDR, or device-loss error. It
removed 1,858 complete tone-map draws, 4,780 complete velocity-dilation draws,
188,765 world-lit vertex translations, 39,250 UV2 world-lit vertex
translations, and 939,858 depth-mesh vertex translations. Its 142,349 timing
samples measured 33,268 us median and 35,619 us p95 frame time, 30.059 median
FPS, 20.320 FPS one-percent low, 59.987 Hz host presentation, and 29.928 Hz
simulation. However, the same session authoritatively reported
`mode=xenos, authority=xenos`; V5-04 therefore remains open until the final
supported gameplay output is native-authoritative rather than merely
containing native in-place replacements.

The remaining measured Xenos work in the fixed Recaro Rush free-roam view is:

| Exact FH1 shader family | Measured GPU cost | Why it remains translated |
| --- | ---: | --- |
| terrain/depth `5A28C7FAFD86F112`, `CA293E0A1CB4B416`, `4E1DA281CC3D7EDB` | 0.35-1.22 ms per recurring pass | approximate direct stages are disabled; an isolated retry removed 214,800 translated executions but changed 57.51 FPS to 57.44 FPS and was reverted |
| world-lit `79034645B1CB882B` / `CAE1DB68AFFA9D3C` and `984DBF6AF14DBEBD` / `6FDA0F1CDE67D12F` | 0.42-0.69 ms, 93-123 draws | approximate direct stages are disabled; translated material shaders and guest resources remain authoritative |
| alpha-shadow `41138347EF20F84C` / `5246C7C219B57DDB` | 0.64 ms, 193 draws | approximate direct stage is disabled after the visual regressions |
| shadow-mask `A3B9ED5D5C87230E` / `93626E75D17576C5` | 0.17 ms, 8 draws | approximate direct stage is disabled after the visual regressions |
| four-tap `D5E12A97B3A84881` / `58CE51CE56247C16` | 0.66 ms, 1 draw | exact native replacement was 7.3% slower |
| event mesh `D25C81F5BF6DD4C6` / `57ACCCFC063672EC` | compatibility path | approximate substitution is disabled with the other handwritten scene shaders |
| complex one-draw post variants `C7D52884ECA9A039` / `E68FE55ECD482EC5` and `ECE830AC0333767F` | 0.17 ms each | roughly 416-instruction dynamic shader; below the justified rewrite threshold |

All smaller measured families are at or below 0.03 ms each. They stay on the
compatibility path until a later milestone demonstrates a larger aggregate
benefit; V5-04 adds no speculative renderer machinery for them.

The current corpus records live index count, index-buffer address, and length
for batching analysis. On the fixed open-world route, terrain vertex family
`CA293E0A1CB4B416` produced 94,382 executions across one pipeline and one
attachment, but 81 index buffers and 65 index counts. The replacement must
therefore flatten heterogeneous static geometry and supply per-draw constants;
simple repeated-draw instancing is not equivalent.

V5-04 was previously closed at a measured compatibility boundary, but the
full-retirement goal reopens it: the completed image still depends on the
Xenos-compatible draw/resource path. The FH1-only
automation introduced after the manual qualification reproduced free roam,
HUD/minimap, SELECT-map roads/icons, event menus, and race output without
computer use. Map sessions `20260903T042245Z-p23960` and
`20260903T042651Z-p48204` passed exact-frame image, native-family, device/log,
and 60 Hz presentation / 30 Hz simulation gates; their static map images had
0.003 MAE and zero pixels above the comparison tolerance. A later audit found
that session `20260903T042839Z-p33920` had stopped in tutorial free roam rather
than entering Recaro Rush, so it is not race evidence. The replacement fixture
now requires the race-only lap, position, and standings HUD before it can pass.

Dedicated pause/free-roam inventory session `20260903T045051Z-p48244` removed
635 velocity-dilation draws, 14,946 world-lit vertex translations, 2,420 UV2
world-lit vertex translations, and 135,895 depth-mesh vertex translations. Its
largest exact compatibility families still cost 1.971 ms for 458-584 draws
(`7EA8B7770CA8D294`) and 1.202 ms for 93-119 draws
(`FA79E5778D949D02`). Every attempted exact replacement of the remaining hot
work was either slower, not repeatably outside noise, or broke FH1 HUD/map
output as itemized above. A native complete-frame reconstruction would thus be
a broad Xenos semantic rewrite with no measured benefit. Final output remains
explicitly `authority=xenos`; this is the enumerated compatibility ceiling,
not a native-authority claim. V5-05 proceeds using the automated gates while
V5-06 retains the final decision on this compatibility core.

### V5-05 — FH1 breadth and edge modes

Close only the gaps needed by this game: festival and garage frontends,
showcases, night/rain variants if present in the captured campaign, replays,
photo mode, loading screens, menus, pause, and FMV composition.

Exit gate:

- A representative campaign flow has no unexplained Xenos visual fallback.
- Every retained fallback has a correctness or cost justification.

V5-05 is qualified for the modes currently reached by the installed campaign
fixture, but remains open for the inaccessible campaign modes below.
The FH1-only unattended sessions exercised startup and three opening-FMV
frames (`20260903T050020Z-p16120`), free roam and HUD/minimap, SELECT map and
its road/icon layers, pause/resume (`20260903T044846Z-p23380`), event loading
and car/start menus, and the actual photo camera
(`20260903T045756Z-p10560`). Every run used exact guest-output frame captures,
normal shutdown, device/log checks, and native-family counters where the mode
contains native gameplay work. The photo-camera run presented at 60.005 Hz
with 29.043 Hz simulation and no renderer error.

Garage/festival interiors, showcases, replays, and campaign-controlled
night/rain variants are not reachable deterministically from this save without
changing campaign state or building a general FH1 navigation bot. They remain
explicit whole-frame Xenos compatibility modes. Their renderer cost is bounded
by the same compatibility implementation already required for normal gameplay;
no mode-specific V5 machinery is justified until a stable local fixture can
reach one. Unknown modes continue to fail closed to the complete Xenos frame.

### V5-01 — Real source presentation

Present FH1 at the display rate, or at an explicitly selected host rate up to
the existing 240 Hz limit, while the game continues to simulate normally.

This milestone resumes only after V5-04 and V5-05 expose authoritative FH1
scene motion/state and a stable HUD/composition boundary. Final-output,
color-only optical flow and velocity-buffer warping are not fallbacks: both
reached correct host pacing while still looking like 30 FPS and produced UI
and sky flicker. They are rejected and disabled.

Work:

- Drive FH1's own render loop at the requested presentation cadence. The first
  exact-title prototype uses the game's observed two-vblanks-per-render policy:
  120 Hz guest vblank requests real 60 Hz title rendering.
- Keep gameplay updates at their validated rate by separating the update and
  render boundaries in the recompiled FH1 loop. Interpolate title camera,
  vehicle, traffic, and animation presentation state before each real render;
  never synthesize or warp the completed framebuffer.
- Pace those real frames with the existing deadline scheduler.
- Reset history on camera cuts, loading transitions, menus, pause, FMV,
  surface resize, device loss, and long frame gaps. Present the newest real
  frame when history is invalid.
- Establish an FH1-specific HUD policy before enabling the mode by default:
  compose stable HUD after interpolation where practical, otherwise exclude
  or clamp its regions so text and gauges do not warp.
- Record real title frames, fallback duplicates, dropped frames, and late
  presents.

Exit gate:

- 30 Hz gameplay produces stable 60/90/120/refresh-rate presentation without
  changing simulation tick counts over the same timed route.
- Additional title renders replace expected duplicates; source-state sampling
  adds no more than one presentation interval of latency.
- Camera cuts, races, free roam, menus, pause, loading, and FMV recover without
  stale-frame flashes or device removal.
- Paired captures show acceptable motion, HUD, particles, shadows, and vehicle
  edges at 60 Hz and at least one high-refresh target.

V5-01 is reopened. Manual session `20260903T163708Z-p15928` proved the previous
velocity warp was not acceptable: 1,650 generated presents still looked like
30 FPS and visibly flickered in the UI and sky. Schema 14 removes that path
and starts the real-render prototype at FH1's source cadence boundary. No FSR,
optical flow, completed-frame blend, or framebuffer warp qualifies for V5-01.

The 120 Hz vblank diagnostic is not itself a solution. At 1x, automated session
`20260903T164829Z-p49212` drove the title loop at 56.883 Hz and the host at
60.002 Hz, but produced only about 40 distinct frames per second (813 repeated
presents) and a 41.232 median derived FPS. The similar 2x result rules out
resolution as the primary limit. It was superseded by the measured 240 Hz
source-rendered path below.
The source-60 scenario now requires at least 55 distinct title frames per
second, so host pacing alone cannot pass this milestone.

Source-driven presentation is now proven, but V5-01 remains open for gameplay
timing qualification. FH1's renderer can produce real frames above 60 Hz when
the guest vblank source runs at 240 Hz. The FH1-only presenter mode displays a
completed source frame once and suppresses independent duplicate paints; it
does not queue, blend, warp, or synthesize images. Unattended driving session
`20260903T213126Z-p45744` produced 61.102 source frames/s and 60.687 distinct
host presents/s with zero duplicate presents, zero resolve readback, all four
retained native families active, valid HUD/minimap captures, and no device or
pipeline failure. The same route observed 113.955 main-loop ticks/s, so the
mode is not complete until fixed-rate and frame-dependent gameplay behavior is
qualified or corrected. Xenos also remains the visual authority and is tracked
separately by the active renderer-retirement goal.

The first wall-time gameplay gate is now automated. Scenario
`fh1-timing-straight.fh1test` samples the active player-vehicle transform once
per second before the unattended route reaches its first bend, and the runner
can compare those transforms against a stock result with
`--pose-baseline-result`. Stock session `20260903T215949Z-p48792` produced
31.372 source frames/s. Unlocked session `20260903T220339Z-p15312` produced
91.328 real source frames/s and 89.741 distinct presents/s with no duplicates;
all five wall-time pose checkpoints remained within 0.855 m of stock under the
1.25 m gate. This supersedes the misleading long-route comparison in which an
unsteered car reached the road bend at different sub-frame phases and collided
with the guardrail. It proves early free-roam wall-clock vehicle behavior, not
the remaining race, AI, rewind, pause, loading, FMV, or audio exit gates.

Schema 16 replaces the diagnostic vblank-rate switch with the actual FH1
render limit: `pinyon_shift_fh1_render_fps_limit`. A value of zero removes the
title-side cap; a nonzero value selects the requested real render rate. The
paired private-save runs `20260903T224937Z-p17632` (30 FPS control) and
`20260903T225020Z-p41708` (uncapped) used the same seed and wall-time inputs.
The control produced 31.426 source frames/s. The uncapped run produced 277.634
distinct source frames/s and 148.532 distinct host presents/s with zero
duplicates. Its five vehicle checkpoints differed by at most 0.450 m from the
control. This confirms that the uncapped path executes additional FH1 renders
rather than replaying or synthesizing completed images. The timing scenario no
longer requires velocity dilation because that optional one-draw pass is not
guaranteed on this short route and is unrelated to its timing assertion.

Schema 18 changes the zero setting from an intentionally excessive 1000 Hz
guest-vblank clock to the active monitor refresh detected after the game window
opens; explicit 30–240 FPS overrides remain available. FH1 still receives two
vblanks per requested real source frame. On the detected 120 Hz display,
session `20260903T233027Z-p47152` produced 89.727 real source frames/s and
89.426 distinct presents/s in the progressed free-roam/map/pause route, with
zero duplicates, only 15 dropped presents over 53 seconds, and no deadline
miss. The previous unlimited-clock run queued 5,465 presents and discarded
5,063, so display-linked pacing removes work the monitor cannot consume.

The second wall-time gate covers free roam, the SELECT map and its road/icon
layers, return to gameplay, pause, and resume at the configured 2560x1440
target. Stock session `20260903T221202Z-p44688` produced 30.214 source frames/s
and 59.993 presents/s with 1,581 duplicate presents. Unlocked session
`20260903T221626Z-p49688` produced 76.279 real source frames/s and 75.826
distinct presents/s with zero duplicates, no renderer/device error, and all
four retained native families active. Every image gate passed; the static map
comparison remained tight at 1.820 MAE, 4.233 RMSE, and 10.13% pixels outside
the four-level channel tolerance. Dynamic gameplay uses wider thresholds
because traffic, foliage, camera, and time-of-day state legitimately differ at
the same wall-time instant.

Renderer tests now clone only the selected seed's `user` and `config` trees to
a per-run state root. The game can autosave inside that private copy, but the
seed and the user's normal save are never written. Shader caches are not
copied, keeping runs independent. The previous shared-state approach changed
the car's saved position and made the Recaro Rush route nondeterministic.

The progressed static-mode pair now uses sessions
`20260903T232055Z-p49636` (30 FPS) and `20260903T233027Z-p47152`
(display-linked). The map road/icon image differs by 0.0037 MAE and zero pixels
outside the four-level tolerance; pause/resume and free roam pass, and the
stationary player pose differs by 3.5 mm. The runner also requires the map
capture to differ from free roam by at least 20 MAE, preventing a tutorial
profile with a locked SELECT map from becoming a false baseline.

The post-cleanup run `20260903T234423Z-p49676` repeats that gate after deleting
the failed procedural accumulator from both the title and SDK. It produces
89.184 real source frames/s and 89.051 distinct presents/s, zero duplicates,
eight dropped presents, and no deadline miss. The map is pixel-identical to
the 30 FPS control within tolerance (0.0007 MAE), the map semantic gate passes
at 64.25 MAE, and the stationary pose differs by 1.1 mm.

The title's actual gameplay delta is now observed immediately after FH1
computes it and before it dispatches the frame's update systems. This replaces
the earlier assumption that main-loop call count was equivalent to simulation
speed. Matched progressed-save sessions `20260903T235856Z-p49732` (30 FPS) and
`20260904T000000Z-p45148` (display-linked) accumulated 51.017 and 50.854
seconds of title-authored game time. The 30 FPS control averaged a 33.301 ms
update and tracked active wall time at 1.022x; display-linked rendering averaged
an 8.390 ms update and tracked active wall time at 1.004x. The latter produced
4,716 real source frames at 88.966 Hz and 4,670 distinct presents at 88.098 Hz,
with zero duplicates. Its stationary vehicle pose stayed within 3.2 mm of the
control and its SELECT-map image differed by only 0.006 MAE. Both HFR scenarios
now fail automatically if title-authored time leaves the 0.95x-1.08x wall-time
range or emits more than two invalid startup deltas.

Schema 19 removes the obsolete renderer selector and diagnostic output modes,
leaving a single FH1 presentation path. After that cleanup and removal of the
failed retained/hybrid compositor shaders, packaged-backend session
`20260904T004028Z-p25496` produced 89.018 real source frames/s and 88.188
distinct presents/s with zero duplicates or deadline misses. Title-authored
time tracked active wall time at 1.007x with an 8.395 ms mean update. Free roam,
SELECT map roads/icons, map return, pause, resume, native-family coverage, image
comparison, and the stationary vehicle-pose gate all passed unattended.

The rebuilt Recaro Rush fixture now provides real race/AI coverage. Session
`20260904T010744Z-p40948` entered an eight-car race and passed semantic checks
for the lap, position, and eight-place standings HUD in both stationary and
moving captures. It produced 54.295 real source frames/s over the full
menu/loading/race run, 54.096 distinct presents/s, zero duplicate presents,
and title-authored time at 1.004x active wall time. Native substitutions covered
71,985 depth-mesh, 12,199 world-lit, and 2,087 UV2 world-lit draws with no
renderer/device error; XMA reported no space, progress, or recovery stalls.
This qualifies race entry, AI presence, race HUD, and title timing. It does not
yet prove audible content or the inaccessible campaign modes tracked by V5-05.
At the configured 2x target the same run also exposes the remaining scaled
resolve cost: 142,017 delayed readbacks copied 91.75 GB and 329 cache misses
forced 516.2 ms of queue waits. Eliminating that guest-visible compatibility
dependency, rather than adding another speculative shader path, is the next
measured renderer-retirement target.

Repeat session `20260904T011110Z-p49652` passed the same race gate with 54.395
source frames/s, 54.196 distinct presents/s, zero duplicates, 1.004x title
time, and comparable race-HUD fractions. This confirms that the replacement
fixture is reproducible rather than a one-run menu timing coincidence.

The matched isolated 2x run `20260904T011242Z-p1940` then disabled resolve
readback entirely. It passed the same race, AI, HUD, native-family, device/log,
and 1.004x title-time gates with 55.802 real source frames/s and 55.504 distinct
presents/s. Its captured player car, road, crowd, sky, and HUD were clean, while
resolve requests, copied bytes, cache misses, and queue waits all fell to zero.
The Experimental 2x preset therefore now uses native scaled resolves with no
readback; `fast` remains only a custom diagnostic and the unqualified 3x preset,
while synchronous `full` remains the explicit showroom compatibility option.

Instrumentation session `20260904T012414Z-p49324` also fixes the unattended
shutdown boundary so its 38,718-key execution corpus is written before the SDK
hard-exits. It maps the current race hotspots directly: family
`7EA8B7770CA8D294` starts with depth vertex shader `CA293E0A1CB4B416`, families
`3A7422A541240B0D` and `75685608BAC84742` start with terrain/depth shader
`5A28C7FAFD86F112`, and `FA79E5778D949D02` starts with the already
vertex-native UV2 world-lit pair. This confirms the older free-roam ranking in
the real race workload and rules out another easy unidentified high-cost pass.
Qualified session `20260904T013028Z-p31788` makes the corpus a mandatory runner
artifact and passed with 39,252 unique execution keys, no overflow or key-hash
collision, zero resolve readback, 53.953 real source frames/s, 53.882 distinct
presents/s, zero duplicates, and 1.004x title time. Its changing race inventory
again ranked the same three untranslated terrain/depth shaders
`5A28C7FAFD86F112`, `CA293E0A1CB4B416`, and `4E1DA281CC3D7EDB` at the top.

The cited Unleashed Recompiled implementation reinforces the title-specific
approach: its high-frame-rate support combines a higher source frame cap with
many game-address-specific delta-time and camera fixes rather than a generic
presenter interpolation layer. FH1 already supplies a correct variable delta
at its main update boundary, so V5 keeps that path and will add similarly
targeted fixes only when a reproducible FH1 subsystem gate proves one is
frame-dependent.

### V5-02 — Native resolution scaling above the original resolution

Render FH1 above its original resolution by scaling its exact D3D12 targets,
passes, and resolves. Do not reconstruct a larger image from the final 720p
frame.

Work:

- Extend only the exact FH1 targets, viewports, scissors, texture reads, and
  resolves required by the authoritative gameplay frame.
- Qualify 1920x1080, 2560x1440, and 3840x2160 output, preserving aspect ratio,
  safe area, readable HUD, and guest-visible resolve behavior.
- Keep V5-01 interpolation after the higher-resolution frame is complete so
  its history always consumes matching dimensions.
- Do not use FSR, FidelityFX, or another reconstruction/upscaling SDK.
- Do not revive the failed scaled accumulator path.

Exit gate:

- 1080p, 1440p, and 4K output survive a representative race, free roam, menus,
  pause, loading, and FMV with no TDR or device removal.
- Captures contain more real detail than 720p scaling on road markings,
  foliage, vehicle edges, HUD, and text without crop or resolve corruption.
- V5-01 frame pacing and latency gates still pass with upscaling enabled.
- Each scale ships only if it is stable and visibly better at a justified
  performance cost.

V5-02 is bounded complete using the D3D12 renderer's existing integer target
scale, which already scales render targets, viewports, scissors, texture reads,
and resolves before presentation. No final-image reconstruction path was added.
The release keeps 1x for minimum requirements, 2x for a 2560x1440 render (and
supersampled 1080p output), and 3x for a 3840x2160 render. Fractional target
scaling is not added because it would duplicate the proven integer resolve
machinery for one intermediate output size.

Session `20260903T055221Z-p10732` captured four real 3840x2160 free-roam frames,
kept every recurring native family active, presented at 60.003 Hz with 29.012
Hz simulation, and missed no deadlines. Combined interpolation session
`20260903T060839Z-p588` captured 3840x2160 previous/generated/current history
with clean road, foliage, vehicle, HUD, and text output. Its synchronous 75 MB
evidence readbacks reduced measured presentation to 57.833 Hz; the no-readback
4K route above is the pacing result. No FSR, FidelityFX, scaled accumulator, or
other reconstruction path is used.

### V5-06 — Minimize or retire the Xenos renderer

- Make the FH1 native path the release default after a clean-save and existing-
  save campaign smoke test.
- Remove V1–V4 discovery switches, broad observers, unused prototype renderers,
  stale accumulators, duplicate resource bridges, and diagnostics no longer
  needed by a live V5 gate.
- Keep only the smallest Xenos compatibility subset required by the enumerated
  fallbacks and guest-visible side effects.
- If the fallback set reaches zero, remove the Xenos renderer from the FH1
  runtime and build. Do not generalize the replacement for another title.

Exit gate:

- Default FH1 play does not execute Xenos visual draws.
- Performance, memory use, startup time, and minimum-GPU testing improve or at
  least do not regress against the V4 Xenos baseline.
- The retained compatibility surface, if any, is small, documented, measured,
  and unreachable during the representative campaign flow.

V5-06 was previously bounded at the measured compatibility ceiling documented
in V5-04, but is reopened by the full-retirement goal. Schema 12 enables the profitable exact FH1 native substitutions and
calibrated interpolation for fresh and migrated configurations. The failed
scaled-accumulator helper/test changes were removed. Release mode installs no
V1-V4 draw/copy discovery observers; the opt-in corpus remains solely because
it supplies the automated exact-pass inventory and fallback-cost evidence.

Schema 17 removes the dormant V1-V3 texture-replay bridge, its private buffer,
texture, render-target, resource-identity and worker implementations, their
test-only targets, and the failed retained/hybrid/comparison output selectors.
Those paths were disabled in normal play and were not used by any retained V5
substitution. The exact FH1 shader capture/corpus and diagnostic clear/triangle
remain available; migrated configurations selecting a removed prototype fall
back explicitly to `xenos`. The release build and an unattended real-game
smoke run (`20260903T230302Z-p44892`) pass after the deletion.

Schema 18 also removes the rejected procedural resolve assembly/frame
accumulator experiment end to end: title planner and diagnostics, launch
switches, summary tools, unit targets, SDK callback contract, D3D12 copy path,
and its two MSAA compute shaders. The retained FH1 substitutions never called
that disabled path. The release build, 618 tool tests, and progressed
free-roam/map/pause HFR gate pass after removing it.

The shipping analysis profile no longer injects the V1-V3 PM4 lineage,
procedural-model, static-world, track-presentation, vehicle-owner, or renderer
configuration discovery hooks. Those title calls were default-off observers
whose evidence had already selected the retained V5 work. Removing them
rewrote 70 generated FH1 translation units and deleted 35,177 bytes of hook
declarations. The corresponding 34 hook-presence tests were removed while the
offline exact GPU corpus and its functional tests remain.

The observer implementation was then reduced from 1,505,916 bytes to 1,415
bytes. It now contains only the sole-VdSwap source-frame counter plus optional
prepared-draw/copy callbacks for the exact FH1 GPU corpus; the old semantic
scene reconstruction, replay, publication, suppression, readback-parity,
vehicle identity, and title-provenance machinery is no longer compiled or
linked. Release build `2A20D03D3007615808D5D85A8615390B857419DECAAE069DAA275FEE8009A30C`
and all 585 remaining tool tests pass. Post-removal unattended session
`20260904T001740Z-p47332` passes free roam, SELECT map and roads/icons,
map return, pause, resume, native-family coverage, image comparison, and
title-time gates. It produced 87.805 real source frames/s and 87.446 distinct
presents/s with zero duplicates, while title time tracked active wall time at
1.003x and the stationary vehicle differed from the 30 FPS control by 1.5 mm.

Schema 19 also deletes the rejected diagnostic-clear/triangle and retained,
hybrid, and comparison compositor implementation from the SDK. Normal FH1
packaging now builds and loads only `rexgpu-fh1.dll`; the generic
`rexgpu-xenos.dll` target, runtime selection, staging rule, and stale packaged
artifacts are gone. The clean pinned-toolchain build, all 575 tool tests, and
session `20260904T004028Z-p25496` pass with `gpu_plugin=fh1` recorded at runtime.
This makes the product boundary title-specific without disguising the remaining
implementation: `rexgpu-fh1.dll` still contains the translated command/register
compatibility core and still executes unconverted FH1 visual workloads.

The first paired world-material stage is now native as well. Shader pair
`79034645B1CB882B` / `CAE1DB68AFFA9D3C` uses direct FH1 HLSL for both stages,
including the exact texture-sign, alpha-test, coverage, and resolution-scale
behavior observed in the captured program. Automated 2x race session
`20260904T014107Z-p13804` passed with 9,782 draws (19,564 translated shader
executions removed), no native fallback, no resolve readback, zero duplicate
presents, 55.778 source frames/s, 55.622 presents/s, and title time at 1.004x
wall time. The race HUD, eight-car event, road, crowd, sky, and vehicle image
were intact. Its complete corpus contained 38,071 keys and 4,966 pass families
with zero overflow or key collision.

The next exact conversion target is the UV2 material pair
`984DBF6AF14DBEBD` / `6FDA0F1CDE67D12F`. Its captured pixel program has 29
guest instructions but expands to 516 translated host instructions. It samples
texture fetches 0 and 1 from the two UV pairs emitted by the already-native
vertex shader, converts each sample from RGB to luminance and back using the
title constants, then combines them with the vertex color and UV selector:

```text
a = lerp(dot(t0.zxy, c254.xyz), t0.rgb, c9.x)
b = lerp(dot(t1.zxy, c254.xyz), t1.rgb, c10.x)
base = (a + c254.w) * c5.x + c255.x
detail = (b + c254.w) * c6.x + c255.x
lit = base * vertex + a * c5.z + c5.w
rgb = sqrt(abs(((lit * c5.y) * detail + b * c6.z + c6.w) *
               c6.y + selector.xyz))
alpha0 = (t0.a * c4.y * c7.z - vertex.a) * c7.x + vertex.a
alpha = (((c8.y * selector.w) * alpha0 +
          (t1.a * c4.y * c8.z - alpha0)) * c8.x + alpha0)
```

The native stage must reuse the proven texture-sign, exponent, scaled-coordinate,
alpha-test, and sample-coverage helpers from `CAE1DB68AFFA9D3C`; omitting those
is specifically disallowed because it would reintroduce the observed foliage,
sky, and UI flicker class. The exact descriptor layout is two sampler/texture
triples in `b4`, fetch constants at `b3`, nine float constants at `b1`, and the
existing unbounded `s0` / `t0,space1` tables.

That UV2 pixel stage is now implemented as direct FH1 HLSL and paired with its
native vertex stage. It compiles to 346 host instructions versus 516 in the
generic translation. Automated 2x race session `20260904T014831Z-p41576`
passed with 3,295 UV2 draws (6,590 translated shader executions removed),
19,335 first-family native draws, 88,012 native depth draws, zero fallback,
zero resolve readback, zero duplicate presents, no XMA stalls, and title time
at 1.003x wall time. Visual inspection confirmed the race HUD, sky, vegetation,
crowd, road, and car remained intact. The noisy car-select thumbnail strip was
pixel-identical in the preceding translated-pixel baseline, so it is not a
regression from this conversion and remains a separately tracked compatibility
artifact. The run captured 39,004 execution keys and 6,325 pass families with
zero overflow or key collision.

The paired conversion also passed the progressed free-roam/map/pause gate in
session `20260904T015233Z-p43788`: SELECT-map roads/icons remained present,
map comparison stayed at 0.818 MAE / 8.824 RMSE, all five visual comparisons
passed, and pause/resume preserved the vehicle pose. It produced 88.453 unique
source frames/s and 87.718 presents/s with zero duplicates while title time
tracked wall time at 1.008x. This closes the map/HUD regression gate for the
UV2 pixel stage.

The shorter standalone map fixture was also corrected to use its intended
60 Hz wall-time clock rather than source-frame time, and to accept the current
FH1 main-loop telemetry range instead of the obsolete 30 Hz assumption. Session
`20260904T015603Z-p42976` then passed at 105.896 unique source frames/s with the
SELECT map visible, native coverage for both material pairs and depth meshes,
zero duplicates, and title time at 1.013x wall time.

Full-retirement work then restored two candidates that the earlier
performance-only gate had rejected. Terrain-depth shaders
`CA293E0A1CB4B416`, `4E1DA281CC3D7EDB`, and `5A28C7FAFD86F112` now use two
direct FH1 vertex variants preserving their distinct clip transforms. Exact
alpha-shadow pair `41138347EF20F84C` / `5246C7C219B57DDB` also uses a direct
pixel stage. Release race session `20260904T022456Z-p49444` passed with 590,321
terrain-depth and 17,173 alpha-shadow native draws, zero resolve readbacks and
duplicate presents, 53.599 real source frames/s, and 1.004x title time. Release
HFR session `20260904T022659Z-p45072` passed free roam, SELECT-map roads/icons,
map return, pause, and resume at 89.523 source frames/s and 1.009x title time.

The next exact pair, `A3B9ED5D5C87230E` / `93626E75D17576C5`, retains its
translated vertex stage but replaces the shadow-mask pixel stage. The direct
FH1 shader implements the captured projected-depth reconstruction, rotating
four-tap sample pattern, texture-sign/exponent decoding, and comparison mask in
214 host instruction slots versus roughly 481 translated slots. HFR session
`20260904T023356Z-p47332` passed all five modes with 2,690 native shadow-mask
draws, 88.764 real source frames/s, zero duplicate presents, and a 0.003 map
MAE against the preceding native baseline. Race session
`20260904T023511Z-p604` passed the event, eight-car HUD, and moving-race gates
with 4,106 native shadow-mask draws, 54.610 source frames/s, zero resolve
readbacks or duplicates, and 1.004x title time. Visual inspection found the
road, sky, crowds, vehicles, shadows, and HUD intact.

The shared `D25C81F5BF6DD4C6` vertex program is now native only for exact
event-scene pixel pair `57ACCCFC063672EC` on attachment
`BD706BD142DBDE84`. The earlier broad substitution failed because the SELECT
map uses the same vertex shader with different pixel programs; those identities
remain excluded. The direct 24-byte event vertex decodes position, UV, and
packed color and compiles to 125 host instruction slots versus roughly 166
translated. Race session `20260904T024200Z-p4924` passed with 452 native
event-mesh draws, correct event and car-select composition, 54.145 real source
frames/s, zero readbacks or duplicate presents, and 1.004x title time. HFR
session `20260904T024340Z-p35312` passed free roam, map roads/icons, map return,
pause, and resume; as intended, it recorded no event-mesh draws because none of
the excluded map/HUD pairs matched.

Exact layered-lit pair `3BC346726C1C2535` / `9584B309533EF6C9` now retains
its translated vertex stage but replaces its high-volume pixel stage on
attachments `7336ADFF531DCC00` and `5750888EB6A93037`. The direct shader
preserves FH1 texture sign/gamma decoding, scaled-coordinate sampling, alpha
test, alpha-to-coverage, and color exponent and compiles to roughly 194 host
instruction slots versus 254 translated. HFR session
`20260904T024901Z-p5256` passed all progressed modes with 74,386 native
layered-lit draws, intact SELECT-map roads/icons, 87.444 unique source
frames/s, zero duplicate presents, and 1.005x title time. The 2x race session
`20260904T025044Z-p27844` passed with 444,577 native layered-lit draws,
54.690 unique source frames/s, zero resolve readbacks or duplicate presents,
and 1.004x title time; visual inspection confirmed the road, sky, crowd,
vehicles, shadows, minimap, and race HUD remained intact.

Exact blended-lit pair `8D8A197476841A9A` / `BA6A2871A980A4E8` now keeps
its translated vertex stage and replaces its pixel stage on attachment
`7336ADFF531DCC00`. The direct FH1 shader implements the captured single
texture sample, two-constant light blend, base-color accumulation, alpha
test/coverage, and output exponent in roughly 195 host instruction slots
versus 256 translated. HFR session `20260904T025710Z-p5060` passed all five
progressed modes with 139,029 native blended-lit draws, 89.585 unique source
frames/s, zero duplicate presents, and title time at 1.004x wall time. The
SELECT map comparison was 0.003 MAE / 0.054 RMSE and visual inspection
confirmed roads, route, and icons remained intact. The 2x eight-car race
session `20260904T025900Z-p47492` passed with 157,493 native blended-lit
draws, 53.898 unique source frames/s, zero resolve readbacks or duplicate
presents, and 1.004x title time. Event and moving-race captures retained the
car, road, crowd, sky, vegetation, lighting, and complete race HUD.

Exact gradient-fade pair `ED90DA6EFF5C6BCA` / `57B9400F6B398736` now
retains its translated vertex stage and replaces its analytic pixel stage.
The direct FH1 shader reproduces the captured curve derivatives, edge width,
fade terms, alpha test/coverage, constant color, and output exponent in about
69 host instruction slots versus 157 translated. HFR session
`20260904T030307Z-p49248` passed with 175,306 native gradient-fade draws,
88.763 unique source frames/s, zero duplicate presents, intact SELECT-map
roads/icons, and title time at 1.007x wall time. The 2x race session
`20260904T030426Z-p44736` passed with 243,759 native gradient-fade draws,
53.799 unique source frames/s, zero resolve readbacks or duplicate presents,
and 1.004x title time. Visual inspection confirmed correct event and moving
race geometry, sky, crowds, flags, road, car, shadows, and complete HUD.

Exact passthrough-color pair `B6C9863F710683EC` / `A4A965C189287B99`
now replaces its one-instruction guest pixel program while retaining the
translated vertex stage. The direct FH1 shader preserves alpha test/coverage
and output exponent and compiles to about 51 host instruction slots versus 82
translated. HFR session `20260904T030820Z-p39548` passed with 143,136 native
passthrough-color draws, 89.714 unique source frames/s, zero duplicate
presents, intact map roads/icons, and title time at 1.006x wall time. The 2x
race session `20260904T030942Z-p49560` passed with 120,336 native draws,
54.150 unique source frames/s, zero resolve readbacks or duplicate presents,
and 1.004x title time. Visual inspection confirmed intact race geometry,
crowds, flags, car, lighting, and complete HUD.

Exact constant-blend pair `CC2F3F4B3FBA53F5` / `CDA93D7ADC1991D8`
now retains its translated vertex stage and replaces the pixel stage. The
direct FH1 shader reproduces the captured input-color scale, constant-color
blend, constant alpha, alpha test/coverage, and output exponent in about 56
host instruction slots versus 102 translated. HFR session
`20260904T031233Z-p38260` passed all progressed modes with 12,941 native
constant-blend draws, 89.422 unique source frames/s, zero duplicate presents,
intact map roads/icons, and title time at 1.006x wall time. The 2x race session
`20260904T031359Z-p48960` passed with 89,258 native constant-blend draws,
55.086 unique source frames/s, zero resolve readbacks or duplicate presents,
and 1.003x title time. Visual inspection confirmed intact race geometry,
crowds, flags, car, lighting, and complete HUD.

The FH1 D3D12 plugin remains the explicit compatibility core and final image
authority while remaining shader families are converted. Terrain-depth,
alpha-shadow, shadow-mask, the exact event-mesh pair, layered-lit pixels, and
blended-lit and gradient-fade pixels are no longer part of that compatibility
ceiling. The exact passthrough-color pixel stage is also native;
the exact constant-blend pixel stage is native as well. Post, shared HUD/map,
frontend, and unreachable campaign modes still require individual proof before
their translated paths can be removed.

Exact textured-alpha pair `C62548CAA393B216` / `98B579267495657C`
is now direct FH1 HLSL for both observed attachment layouts. The shader retains
the guest texture-sign/exponent decode, material alpha threshold, hardware alpha
test and alpha-to-coverage behavior while reducing the host shader from roughly
236 translated slots to 194. The automated 2x eight-car race session
`20260904T032245Z-p2528` passed with 21,478 native textured-alpha draws, 55.915
unique source frames/s, zero duplicate presents, correct simulation wall-time,
and intact event signage, crowds, flags, vehicles, route, and race HUD. The
720p free-roam/map session `20260904T032115Z-p48196` also passed at 88.998 unique
source frames/s with zero duplicate presents; that route does not execute this
race-specific pair. The race fixture now requires this exact native stage.

Exact binary-alpha-mask pixel `2B83D3E3C1FCEE3C` is now direct FH1 HLSL for
the byte-identical `197BAACCCEF0ED45` and `7CD5A236D3A01D3F` vertex variants
on the observed `36602A7E532469D3` attachment. It
preserves scaled UV sampling, texture alpha sign/exponent decode, the guest
material discard, hardware alpha test, and alpha-to-coverage while reducing
the host shader from roughly 162 translated slots to 75. Automated 2x race
session `20260904T032640Z-p43788` passed with 30,532 native binary-alpha-mask
draws, 53.876 unique source frames/s, zero duplicate presents, correct
simulation wall-time, and intact alpha-tested crowds, flags, foliage, event
geometry, vehicles, route, and complete race HUD. The race fixture now
requires this exact native stage.

Exact explicit-LOD texture pair `2C53E1A563484076` / `21937679208E59A5`
is now direct FH1 HLSL for all three observed attachment layouts. It preserves
early depth-stencil, the guest-controlled mip level and fetch bias, texture
sign/exponent decode, and output exponent while reducing the host shader from
roughly 158 translated slots to 133. Automated 2x race session
`20260904T032947Z-p49960` passed with 28,730 native explicit-LOD texture draws,
54.041 unique source frames/s, zero duplicate presents, correct simulation
wall-time, and intact road/terrain detail, event assets, crowds, route,
vehicles, and race HUD. The same run enforced both promoted alpha-stage gates;
the race fixture now also requires this explicit-LOD stage. Final gated race
session `20260904T033403Z-p27004` passed all three new native requirements at
56.718 unique source frames/s with zero duplicate presents and 1.004x
simulation wall-time.

The automated race HUD gate now accepts the first valid HUD-bearing capture
from `race-ready` or `race-moving`. FH1 can legitimately finish the grid
transition on either side of the fixed capture boundary under uncapped host
load; the gate still fails unless one capture contains the lap, place, and
standings regions. This removes timing flakiness without weakening the visual
requirement.

Corpus analysis also corrected a false remaining-work entry: pair
`79034645B1CB882B` / `CAE1DB68AFFA9D3C` was already the native world-lit
route. Its apparent translated count came from grouping execution identities
without subtracting native shader-hash coverage, so the duplicate candidate
and counters were removed.

Exact two-texture-lit pair `5834939992FFC765` / `C2F1242C2535A57E` now
retains its complex translated vertex stage and replaces only the compact FH1
pixel stage on pipeline `D6F1F27D2AE301B0` and attachments
`5750888EB6A93037` and `7336ADFF531DCC00`. The direct shader preserves both
guest texture fetches, texture signs and exponents, the captured shadow/light
blend, vertex tint, alpha test and coverage, and output exponent in roughly
242 host slots versus 349 translated slots. Automated 2x race session
`20260904T035011Z-p30808` passed with 58,882 native two-texture-lit draws,
53.925 real source frames/s, zero duplicate presents or resolve readbacks, and
title time at 1.003x wall time. Visual inspection confirmed intact sky,
terrain, vehicles, crowds, banners, event cinematic, and complete race HUD.
The race fixture now requires this exact native stage.
Final gated session `20260904T035217Z-p18788` independently passed with
51,883 two-texture-lit draws, 56.100 real source frames/s, zero duplicate
presents or resolve readbacks, and 1.004x title time.

V5-06 now has a title-specific ahead-of-time shader route. ReXGlue's existing
FH1 `.xsh` guest-shader store and `.xpso` pipeline-specialization store drive
all known translations during isolated startup; the capture writer records
native bytecode plus the exact binding metadata required by runtime pipeline
creation. A 2.7-second unattended startup pass produced 721 V2 entries and
15,825,060 bytecode bytes with no rejected callback, replacing the slow and
non-convergent repeated-race capture loop.

The D3D12 pipeline cache loads the configuration-keyed V2 pack only for FH1
title ID `4D5309C9`. Exact hits bypass `DxbcShaderTranslator`; misses remain
observable only during explicit local corpus construction. Normal FH1 runtime
structurally rejects and terminally marks any miss before translation, while
the automated runner's independent zero-miss gate checks the capture summary.

The 15,970,624-byte NVIDIA 2x pack passed unattended race, free-roam, SELECT
map and return, pause/resume, photo mode, and combined HFR mode coverage with
zero runtime translations. Strict HFR session `20260904T043852Z-p44060`
rendered all five captures at 2560x1440, produced 73.426 real source frames/s,
zero duplicate presents, 1,186 native velocity-dilate draws, and title time at
1.004x wall time. Strict mode without a pack failed on explicit precompiled
shader misses, proving that it cannot silently fall back to Xenos translation.

Strict 1x HFR session `20260904T044521Z-p45072` also completed with zero misses
and duplicate presents. A first 3x timing attempt rendered five valid 3840x2160
captures with zero misses, but the synchronous readbacks contaminated the
simulation gate with five 400+ ms instrumentation frames. The capture-light
replacement scenario separates those concerns. Strict 3x session
`20260904T045529Z-p556` passed with a valid 3840x2160 world frame, zero misses,
75.066 real source frames/s, 74.860 presents/s, zero duplicate presents, and
title time at 0.995x wall time. The current NVIDIA configuration is therefore
strictly qualified at 1x, 2x, and 3x.

The FH1-only producer now scans loose `.fxobj` assets plus method-21 LZX track
archives. It extracts 3,349 unique raw programs from 4,293 containers and uses
the assets' 34 vertex declarations to generate 8,377 runtime-patched vertex
variants, yielding 11,726 programs. This follows XenosRecomp's static asset
model without adopting its Sonic-specific sampler, cube, or vertex ABI.

Automated 2x producer session `20260904T055222Z-p28564` translated 9,600 vertex
and 12,098 pixel variants with zero failures. The merged 21,984-entry pack is
472,656,904 bytes and passed strict no-translation session
`20260904T055452Z-p33360` with no `.xsh` seed, zero capture entries, 86.478 real
source frames/s, zero duplicate presents, and 1.007x title time. The finite
seed now covers generated/system shaders and two DriverHands skinning variants;
ordinary retail vertex and pixel coverage is asset-derived.

The asset-derived producer is now strictly qualified on the current NVIDIA
configuration at 1x, 2x, and 3x. All three packs contain 21,984 exact entries;
the strict sessions captured zero misses without `.xsh` seeds. Ordinary local
launches verify and stage the configured scale's pack and automatically enable
the strict no-translation gate. V5-06 remains open for distributable pack
production and the remaining command/register/resolve compatibility work,
which must be removed or individually justified.

The offline producer no longer derives its specialization set from an existing
pack. Clean 1x session `20260904T061601Z-p48584` translated all 9,600 vertex
and 12,098 pixel asset variants with zero failures and no `.xsh` or pack seed.
Only the finite runtime-generated/system program set remains as local seed
material; retail shader coverage is now self-contained and deterministic.

A strict 3x race run then disabled resolve readback while retaining the full
event-menu, loading, eight-car AI, race-HUD, moving-gameplay, native-family,
shader-pack, and renderer/device gates. All seven 3840x2160 captures completed,
and resolve readback fell from tens of gigabytes to zero requests, bytes, cache
misses, and waits. The eight invalid simulation samples correspond to the
seven synchronous 4K evidence captures; accumulated title time still tracked
wall time at 0.975x. Strict ordinary launch now forces native scaled resolves
instead of preserving a migrated `fast` readback setting.

The obsolete D3D12 resolve-readback implementation is now deleted rather than
merely disabled: its copy routine, downscale resources and bytecode, runtime
cvar, launcher controls, showroom preset, crash-report fields, A/B workflow,
and qualification plan are gone. Configuration schema 20 removes the retired
keys during migration. Post-deletion strict 2x session
`20260904T063224Z-p30084` completed from a schema-15 source configuration at
2560x1440 with zero shader misses, zero resolve-readback activity, 88.098 real
source frames/s, zero duplicate presents, and title time at 1.006x wall time.
The focused 54-test suite, release runtime build, and launcher build also pass.

The next retirement measurement separates shader and pipeline work correctly.
The route counter had counted on-demand native-pack loads as translations; it
now increments only when `DxbcShaderTranslator` actually executes. Strict 2x
session `20260904T063651Z-p48220` preloaded the existing FH1 `.xsh`/`.xpso`
catalog, selected 380 of 11,151 stored pipeline descriptions, and completed
with zero real runtime shader translations. Prewarming reduced pipeline-cache
misses from 307 to 77, but eight pipelines were still created synchronously.
Therefore the next V5-06 unit is an FH1-native startup pipeline catalog (or
asset-load integration equivalent) that reaches zero synchronous creations;
the `.xsh` metadata bridge must not be removed until that replacement can
construct the prewarmed pipelines without losing shader analysis metadata.

Blocking prewarm also contained a worker-drain bug: it waited only when
temporary workers existed, so catalog verification raced the normal worker
set. The corrected initialization waits for every active worker before
verification. Strict repeat `20260904T063940Z-p41344` verified all 303 selected
pipelines (previously 295), reported zero `pipeline_not_prewarmed` draws and
zero real shader translations, and kept title time at 1.005x wall time. Four
new synchronous pipeline creations remain outside the current catalog.

`tools/build-fh1-gpu-prewarm.py` now merges new execution corpora into an
existing FH1 manifest, so representative modes converge into one bounded
startup catalog rather than replacing each other. The first union contains 380
pipeline hashes, 36,299 draw identities and 401 copy identities. Strict 2x
session `20260904T064247Z-p49376` verified all 373 descriptions available in
its input store, reduced runtime pipeline misses from 71 to 10, and reached
zero synchronous pipeline creations, zero shader translations and zero
prewarm fallback draws. Ordinary launches now hash-verify and stage this local
`.xsh`/`.xpso`/manifest bundle when available.

The catalog was then expanded through the combined unlocked-HFR/UI route and
the full event-to-eight-car-race route. HFR session
`20260904T064757Z-p49476` passed free roam, SELECT map and return,
pause/resume, every native-family gate and all five image comparisons with
zero pipeline misses, zero synchronous creations, zero shader translations,
76.280 real source frames/s and 1.006x title time. Race session
`20260904T065341Z-p1260` passed all seven captures, race HUD, moving gameplay,
eight-car AI, zero shader translations, zero synchronous creations and zero
prewarm fallback draws at 52.231 real source frames/s and 1.003x title time.
The remaining three global pipeline-cache misses were asynchronous utility
work and did not correspond to a new FH1 pipeline hash. The staged catalog now
contains 461 pipeline hashes, 73,781 draw identities and 690 copy identities.

The legacy `pinyon_shift_fh1_native_v4` switch is now retired. FH1's native
route is unconditional in the title-specific GPU plugin, schema 21 removes the
persisted setting, and launcher, graphics-tool and crash-report support for the
old escape hatch is gone. Strict 2x unlocked-HFR session
`20260904T070431Z-p24828` migrated a schema-20 isolated state, passed free roam,
SELECT map and return, pause/resume, all five image comparisons and every
required native family. It loaded the complete shader and startup catalogs,
reported zero runtime shader translations, zero synchronous pipeline
creations, zero prewarm fallbacks and only the three known asynchronous utility
cache misses, while rendering 76.605 source frames/s at 1.006x title time.

The separate `pinyon_shift_fh1_require_precompiled_shaders` escape hatch is
now deleted as well. The title-specific pipeline cache enforces precompiled-only
operation for every normal FH1 launch; only a validated `.local` disc-corpus
producer run with an installed capture observer may invoke the translator.
Positive strict session `20260904T070857Z-p34300` again passed the combined HFR
and UI route with zero runtime translations and zero synchronous pipeline
creation at 76.782 source frames/s and 1.007x title time. Negative no-pack
session `20260904T071055Z-p35632` was rejected on explicit precompiled misses
and recorded zero translated shaders, proving the old runtime fallback cannot
be restored by launching the executable directly.

The compiler boundary is now physical rather than policy-only. Normal
`rexgpu-fh1.dll` excludes the DXBC compiler translation units and bodies;
translation is available only in the explicit, unstaged
`rexgpu-fh1-producer.dll` selected for a validated disc-corpus run. The binary
gate reports 2,760,704 bytes for the runtime plugin versus 3,138,560 for the
producer and rejects translator-only markers in the former.

Normal FH1 startup also no longer opens or mutates generic `.xsh`/`.xpso`
stores. The local catalog builder converts the last qualified capture into
read-only `fh1-native-shaders-v1.bin` (subsequently replaced by the analyzed v2
catalog) and
`fh1-native-pipelines-v1.bin`; it filters 11,323 captured pipeline records down
to the 461 unique descriptions admitted by FH1's execution corpus, shrinking
that input from 815,268 to 33,204 bytes. Automated session
`20260904T074153Z-p40876` selected and verified all 461 pipelines, loaded 1,012
startup shader analyses, captured zero shader misses, reported zero pipeline
misses, and exited normally. The full unlocked-HFR/UI route immediately before
it also completed all five captures with zero shader and pipeline misses,
70.935 real source frames/s, no duplicate presents, and title time at 1.014x
wall time; its harness rejection was only dynamic free-roam image drift against
a prior run, not a renderer, pacing, or simulation failure.

The abandoned isolated-draw replay and retained-pass publication experiment is
now physically removed. This deletes its private color/depth targets, MSAA
depth readback shader, CPU readback queues, resolve-preview snapshot, deferred
swap publication, guest-suppression request ABI, and the remaining draw-state
restore branch. No live FH1 renderer or test callback consumed its output; the
only remaining calls were orphan bookkeeping at swap. The shipping plugin fell
from 2,735,104 to 2,702,336 bytes. Post-deletion smoke session
`20260904T080010Z-p3476` loaded all 21,984 2x shader specializations and 461
startup pipelines, captured zero shader misses, reported zero pipeline misses
and duplicate presents, and completed normally.

Six orphan diagnostic observer paths are now removed from the command,
register, draw, texture and resolve hot paths: raw draw capture, shader-constant
write provenance, indirect-buffer capture, draw outcomes, borrowed native
texture export and the duplicate native-resolve channel. No FH1 runtime or
producer installed any of them; the live prepared-draw, copy, shader-producer
and render-test interfaces remain. The shipping plugin fell again from
2,702,336 to 2,694,144 bytes. Post-deletion 2x smoke session
`20260904T080554Z-p43568` loaded the complete 21,984-shader and 461-pipeline
native catalogs, captured zero shader misses, reported zero pipeline misses and
zero duplicate presents, and completed normally; the runtime/producer binary
gate and focused 37-test suite also pass.

DXBC/DXIL shader disassembly is now producer-only as well. The shipping plugin
no longer registers its disassembly cvars, initializes DXC converter/compiler
interfaces, disassembles AOT binaries, or publishes translation callbacks; the
explicit offline producer retains all four behaviors. Its disassembly method
and D3D provider dependency are now compile-time absent from the runtime too.
The binary gate rejects the controls and implementation markers; the runtime
fell from 2,694,144 to 2,684,416 bytes. Strict 2x smoke session
`20260904T081108Z-p38624` again loaded the 21,984-shader and 461-pipeline native
catalogs with zero shader misses, zero pipeline misses, zero resolve readback
and zero duplicate presents.

The remaining PM4 adapter now has title-specific reachability evidence rather
than a generic-Xenos assumption. Temporary cumulative instrumentation covered
the unlocked free-roam/map/pause route (`20260904T094302Z-p43320`), the complete
4,230-frame race script (`20260904T094425Z-p50576`), opening movies
(`20260904T094623Z-p48512`), and photo mode (`20260904T094645Z-p16564`). Their
union executed 24 type-3 opcodes; photo mode uniquely proved that Z-pass report
side effects are still guest-visible. The static FH1 dispatcher inventory now
recognizes every Xenos opcode rather than a hand-picked subset and independently
finds title constructors for dormant-but-reachable indirect-PFD, memory-write,
visibility-query, register-to-memory and idle-wait operations. The temporary
runtime counters were removed after collection. `PM4_SET_BIN_SELECT`'s combined
form and `PM4_CONTEXT_UPDATE` were absent from both the four-mode runtime union
and every generated FH1 translation unit, so those two generic handlers are now
deleted; split bin-select packets remain because FH1 executes them. The runtime
plugin is now 2,683,904 bytes. Post-prune unlocked-HFR/UI session
`20260904T095121Z-p44672` passed at 71.429 real source frames/s and 1.015x title
time with zero shader or pipeline misses, zero duplicate presents and intact
map/pause transitions; the runtime/producer binary gate and 50 focused tests
also pass. The static inventory test additionally requires its opcode map to
match FH1's complete compiled `Type3Opcode` declaration, preventing future
partial-census regressions.

FH1 shader reflection and modification-independent microcode analysis are now
offline too. The producer writes `fh1-native-shaders-v2.bin` after scanning the
complete disc corpus; its 1,012 sorted records contain only runtime-needed
constant maps, vertex stream bindings, output/register flags and memory-export
facts, with per-record XXH3 integrity. Normal startup hydrates those records,
loads exact DXIL variants from the 21,984-entry native pack and fails closed on
missing or malformed metadata. It no longer reads the copied `.xsh` catalog or
calls `AnalyzeUcode`; the binary verifier enforces that separation. Producer
session `20260904T100420Z-p49224` wrote the 837,428-byte catalog with zero
corpus failures. Shipping session `20260904T100639Z-p42016` then passed the full
2x unlocked-HFR/map/pause route at 71.402 distinct source frames/s and 1.006x
title time with zero shader misses or duplicate presents.
The analysis and disassembly translation units are now producer-only at the
build graph as well; the one runtime interpolation-mask calculation moved into
the ordinary shader object. This reduced `rexgpu-fh1.dll` from 2,687,488 to
2,654,208 bytes. Post-split smoke session `20260904T101023Z-p48284` loaded all
1,012 analysis records and 528 required variants and exited normally. The
binary gate and 51 focused tests pass.

The D3D12 CPU memexport-readback compatibility path is now deleted. Across 12
recorded performance streams and 23,167 samples, including unlocked HFR/UI,
race, photo mode and FMV routes, FH1 executed zero memexport draws and zero
memexport bytes, fallbacks or waits. The removal drops the legacy backend CVar,
synchronous queue-wait path, double-buffered readback cache and its allocation,
mapping, eviction and teardown code. Native GPU memexport writes, shared-memory
ordering and texture invalidation remain because those are the minimum correct
guest-memory semantics if an export is encountered. The binary gate rejects
the removed D3D12 readback control.

The remaining compatibility surface is title input/state translation, not a
second visual authority:

| Component | FH1-specific reason retained |
| --- | --- |
| PM4 adapter | FH1's recompiled CPU still emits the measured 24-opcode command stream; dormant statically constructed operations are retained only where guest side effects remain reachable. |
| Register file | Live SQ/RB/PA/VGT values select exact precompiled shader variants, PSOs, resources, viewport and blend/depth state per draw. |
| Resource and render-target caches | Convert FH1 tiled textures, EDRAM addresses, resolves and hazards into native D3D12 resources; host render targets are unconditional. |
| Shader interpreter tables | The draw-extent estimator interprets FH1 vertex positions to conservatively bound host render-target accesses; no shader compilation uses them. |
| Occlusion/ZPD reporting | Photo mode executes query packets and consumes their guest-visible results, so native D3D12 queries and result publication remain. |
| Render-target transfer conversions | Native host-target load/store, resolve and format conversion require the shared numeric conversion emitters; unreachable ROV code is linker-stripped and rejected by the binary gate. |

This is the current minimum compatibility core. Removing any listed item now
requires replacing its stated FH1 guest-visible contract, rather than merely
renaming or duplicating it in another renderer layer.

The final offline-production pass also closes the intermittent event and car
selection coverage gap. The producer now rewrites its analysis catalog after
new title-generated shaders are analyzed and explicitly precompiles six exact
FH1 car-selector variants that are not present in the retail `.fxobj` corpus
and are not deterministically requested by every timed replay. The final
catalog contains 11,628 analyzed programs, is 8,409,800 bytes, and has SHA-256
`09F6FDC0FBD9961BA000A2B30B3839FA9D4BA0292D09F7FA436EC4B761D0613E`.
The NVIDIA 1x, 2x and 3x packs each contain 22,012 exact DXIL variants; their
SHA-256 values are respectively
`1636179BF8633D7406C7C3C735DD600C0C05666D8A8A8CAC188433730A38C026`,
`D6E62162510BE0EDFC0CA4D1624B498F51024F7BC5AC2597A23C37929E030A3E`,
and `53288ADF3C958C994D857CC2DEEF8877A0EA1DF4E3B89207B7E6AF18778C83B0`.

The final compiler-free matrix passed without `.xsh`/`.xpso` runtime input or
shader-pack misses. Race sessions `20260904T113108Z-p28548`,
`20260904T114556Z-p29404`, and `20260904T115526Z-p50688` covered event entry,
car selection, race HUD, eight-car AI and moving gameplay at 2x, 1x and 3x.
The 3x run presented 50.977 distinct source frames/s while title time remained
at 0.978x wall time; the 1x run presented 56.494 frames/s at 1.000x title time.
Combined free-roam/SELECT-map/pause session `20260904T115814Z-p33860` passed
all five image comparisons, including map roads and icons, at 73.934 source
frames/s and 1.007x title time. Photo-mode session
`20260904T115719Z-p13804` passed at 76.222 source frames/s and 1.007x title
time. Opening-FMV session `20260904T120009Z-p50416` captured all three movie
frames with zero shader misses. The race script no longer samples a
resolution-dependent black loading transition, and allows the nine protected
simulation-delta rejections observed during the longer 3x event transitions;
its accumulated title-time ratio remains independently bounded to 0.95–1.08.

The earlier V5-06 boundary is no longer the completion boundary. Normal FH1
execution contains no shader compiler, runtime shader analysis, writable
generic shader stores, resolve readback path, or competing reconstructed-frame
renderer. The retained PM4/register/resource/query code is the individually
accounted compatibility core above: it translates FH1 state and side effects
into native D3D12 work, but is not a second visual authority.

## Status

| ID | State | Deliverable |
| --- | --- | --- |
| V5-03 | complete | first measured Xenos workload retired |
| V5-04 | reopened | replace and batch the native-authoritative gameplay scene |
| V5-05 | reopened | complete the representative campaign visual matrix |
| V5-01 | complete | real title renders with fixed-rate gameplay simulation |
| V5-02 | bounded complete | qualified 2x/3x native target scaling; no FSR |
| V5-06 | reopened | retire the remaining Xenos visual command/resource core |

Execution order is V5-03, V5-04, V5-05, V5-01, V5-02, then V5-06. Obsolete
Xenos and prototype code is still deleted continuously; V5-06 is the final
release-default and compatibility-core retirement gate.

V5-01 is qualified in free roam and an eight-car race with correct title-time
tracking, distinct source frames, race UI, and no XMA stalls. V5-06 now closes
only when the representative campaign matrix has no Xenos visual draws, or a
small measured residue is proven necessary and documented.

## Explicit non-goals

- A renderer for other Xbox 360 games or other ReXGlue projects.
- A reusable Xenos emulation API or new cross-backend renderer architecture.
- Uncapping the guest simulation, physics, AI, scripts, or audio.
- Replacing existing presenter or pacing code without a measured FH1
  limitation.
- Carrying old prototype code forward because it may become useful later.
