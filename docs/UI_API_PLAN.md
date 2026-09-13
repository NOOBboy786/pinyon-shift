# Game UI API: research and implementation tasks

Research date: 2026-09-10. Status: active implementation backlog; UI-01 is
complete, UI-02 has bootstrap and pause-list runtime traces, and the remaining
runtime UI API work is open.

Source inspected: Pinyon Shift `c34f3f1c8693f2eeaaf67c5bb8365d34d4db6255`,
ShiftGlue `7349a0951ebf2bb55720f8bf2e855bb1677ec990`, and locally extracted
MS-2505 game assets. The working tree had unrelated SDK/test changes; runtime
claims below are limited to the named release build and AppData save runs.

## Recommendation and first deliverable

Build a small C++ API over FH1's existing UI scene, component, and event
systems. Let the original game render the resulting interface. This offers
the best prospect of preserving fonts, materials, layout, animation, sounds,
controller behavior, and composition with the game world.

The first deliverable must **modify an existing screen and add a working
control to it**. A new entry in the real pause menu should open an extension
page made from original components, then return to the same selection. A
later HUD example must demonstrate that the API also works during gameplay.
An independently drawn overlay does not meet the existing-screen requirement.

The principal uncertainty is whether the shipped component contracts let us
construct or populate additional controls safely. Resolve that with UI-01
through UI-04 before promising a general toolkit. A text replacement alone
does not pass this gate.

## What the investigation established

### Current implementation checkpoint

The first foundation is now compiled and exercised without changing the
generated game code:

- `tools/inspect-fh1-ui.py` produces the private, asset-free catalog described
  by UI-01 and its three focused tests pass.
- A default-off `PINYON_SHIFT_UI_TRACE=1` hook at the verified native UI4
  registry construction call (`0x824850A4`) records the returned guest object,
  context, and owner values as `ui.scene_registry.constructed`. The bounded
  registry scan now also records the title's registered `708_PAUSE`,
  `925_PAUSE_MENU`, `947_HUD`, and `BUTTON_BAR_SCENE` names, including their
  registry field offsets (`0x578`, `0x5F8`, `0x2B0`, and `0xAD0`) and image
  string pointers (`0x8203FCB8`, `0x8203FC1C`, `0x8204002C`, and
  `0x8203F828`). These are names in the registry, not live scene instances.
- The release build ran through the existing pause render-test route and
  completed normally. Its three captures (`free-roam`, `pause`, `resumed`) and
  input-step events are under `.local/ui-api-research/2026-09-10/pause-runtime`;
  the corresponding runtime event log records the registry event and the
  pause/resume route. The relinked run is preserved under
  `.local/ui-api-research/2026-09-10/pause-runtime-scenes` and proves the
  observation point plus the registered scene-name mapping, not yet
  scene-open/close ownership or component mutation. The relinked executable
  used for that run has SHA-256
  `A63DEA488F4D4B056EFB2B7C07B83677AF47224355B3550342979AB908587B27`.
- The expanded trace resolves the three UI4 bootstrap calls on the live
  `CUserInterface4` object (`vtable 0x820038DC`): registry setter
  `0x826413C8` at slot 224, resource setter `0x82E5E0D0` at slot 228, and
  scene/context setter `0x82E729F8` at slot 232. The following event call uses
  ID `302` and resolves to `0x82E72970`, which stores the manager state at
  offset 100. The indexed table stores 12 bootstrap entries in slots 29–40,
  then repeatedly reads slots 30 and 38 during the route. This identifies the
  bootstrap contract, but it does not identify scene open/close ownership or a
  safe insertion path. The latest completed trace is the normal-exit list-probe
  run in `.local/ui-api-research/2026-09-10/pause-runtime-list2`, with runtime
  log `20260911T005806Z-p35252.jsonl` and three captures.
- `src/ui/fh1_ui_api.h` and `.cpp` provide the first source-level API boundary:
  generation-checked scene handles, semantic component IDs, stock component
  kinds, bounded operations, stale-handle rejection, duplicate-ID rejection,
  and a drain point for the future title-owner adapter. The asset-free C++ test
  covers its queue and lifetime invariants.
- The rebuilt constructor and button probes are preserved under
  `.local/ui-api-research/2026-09-10/pause-runtime-constructor3` and
  `.local/ui-api-research/2026-09-10/pause-runtime-button-probe2`; their
  runtime logs are `20260911T012249Z-p25724.jsonl` and
  `20260911T014502Z-p35820.jsonl`. These runs establish live list ownership
  and a pause-button text boundary, while item ownership, setters, and
  activation remain open.
- The follow-up field scan is preserved under
  `.local/ui-api-research/2026-09-10/pause-runtime-menu-fields2`; runtime log
  `20260911T020745Z-p276.jsonl` observes the same graph on the bootstrap and
  pause-open `CMenuCtrl` objects. Its `+312` field points to the live
  `CAnimatedScrollingListCtrl` (`0x82063974`) and `+316` points to the live
  `CBreadcrumbMenu` (`0x82063CA4`). This is a verified owner-to-child graph,
  not a public offset contract; item creation, ordering, and activation are
  still open.

The clean list-probe run exercised the authored indexed-table and inherited
menu-list hooks. The normal-exit run is preserved under
`.local/ui-api-research/2026-09-10/pause-runtime-list2` with runtime log
`20260911T005806Z-p35252.jsonl` and three captures. It recorded
`0x82E7CD78` during bootstrap, the same entry on object `0x2ECCAD28` at the
pause-open input (frame 961), and `0x82E77260` on that object at the resume
input (frame 1141). Both pause-time calls reported vtable `0x8206D3B8`,
argument `2`, and value `0x40797CF0`; the component trace reached its bounded
512-event cap during startup. Static RTTI and vtable inspection ties both list
entry points to the shipped `CAnimatedScrollingListCtrl` and `CMenuCtrl`
families, making this a live pause-list lead without proving item insertion or
activation semantics.

The rebuilt `pause-runtime-constructor3` run (runtime log
`20260911T012249Z-p25724.jsonl`) moved the read-only probe to the shared
constructor entry `0x828116C8`. It captured allocation `0x2ED11D20`, followed
by the live list object `0x2ED11D28` (`+8`) with vtable `0x8206D3B8`; the same
relationship appeared for the earlier bootstrap allocation `0x2E2B1000` and
list object `0x2E2B1008`. RTTI locator inspection identifies
`0x8206D3B8` as `CMenuCtrl@ForzaUI`; its live field `+312` points at an
`CAnimatedScrollingListCtrl` subobject (`0x82063974`) and field `+316` points
at a `CBreadcrumbMenu` subobject (`0x82063CA4`). This closes the
static-to-live object relationship needed for UI-03, while item-provider and
activation contracts remain open.

The bounded `pause-runtime-button-probe2` run (runtime log
`20260911T014502Z-p35820.jsonl`) reached the route-specific
`CPauseMenuButton` constructor at `0x8264FC08`. Each observed button had its
`CUI4TextElement` subobject at `button + 252` with vtable `0x82026B38`; the
constructor initialized the text object before the probe. Several instances
carried printable inline text at offsets `+84` through `+99` (for example
`eetle_04`), while other instances held pointers or numeric layout values.
This is the first verified live label-read boundary. The byte slice is only a
bounded diagnostic read, not yet a complete localization decode. It does not
identify the title's text setter, localization path, list item ownership, or
an action callback, so the probe remains read-only and capped.

A short candidate-method trace (`pause-runtime-text-methods1`, log
`20260911T015138Z-p36040.jsonl`) produced no calls for the unresolved
`CUI4TextElement` vtable entries during the route. A separate probe of the
generated `0x82E74FC8` helper was intentionally discarded after it matched
many unrelated UI object vtables rather than a text-only contract. The next
setter investigation must therefore follow a pause-button caller or a direct
property write, rather than publish either helper as an ABI.

The narrowed `pause-runtime-text-value2` run (runtime log
`20260911T023717Z-p23796.jsonl`) did reach the direct helper
`0x82E73BE0` three times with receivers whose vtable was `0x82026B38`.
The generated body writes `r5` to the text object at `+4` and `r4` at `+8`;
the trace captured both guest arguments and exited normally. This is a useful
candidate value/resource-pair setter, but the observed receivers were not
correlated to a specific `CPauseMenuButton` in that route, and no mutation was
attempted. Keep the public setter closed until that correlation and a visible
before/after label change are captured.

A follow-up `pause-runtime-text-value4` run (runtime log
`20260911T024028Z-p14308.jsonl`) used the stock pause route and filtered the
same helper for receivers at exactly `CPauseMenuButton +252`. It captured the
button constructors but zero calls to `0x82E73BE0` for those embedded text
objects. Keep this helper as a generic value/resource-pair candidate only; the
pause-label setter remains unresolved.

Static inspection narrows the next trace. `CPauseMenuButton` vtable entries
`54` through `64` (including `0x8264F460` through `0x8264F580`) tail-call
`0x82E74FC8`; that helper reads the button's `+84` label-resource pointer and
then delegates to the generic resource/hash helper. It is a getter/resource
lookup path, not a text setter. The normal button base constructor
(`0x82665198` through `0x827E5150`) initializes that `+84` pointer from the
factory input, while `0x8264FBA0` separately constructs the `+252`
`CUI4TextElement` layout subobject. The two fields are therefore distinct
extension seams; the generic `0x82E73BE0` pair write cannot be promoted to the
pause-label API without a caller that proves which resource or text object it
owns.

The constructor path is now instrumented to record `button +84` and its first
word as `label_resource_vtable` in the existing bounded construction event.
The clean `pause-runtime-resource2` run (log
`20260911T033039Z-p30084.jsonl`, captures under
`.local/ui-api-research/2026-09-10/pause-runtime-resource2`) recorded fourteen
button constructions. Every sampled `+84` resource pointed at vtable
`0x8224CC94` (`CUI4CustomObject` by RTTI), while the separate `+252` object
remained vtable `0x82026B38`. This confirms a stable resource/layout split on
the stock route, but it still does not prove a safe resource replacement or a
list insertion call.

A temporary read-only hook at the verified resource method `0x82E76048` was
then run in `pause-resource-method1` (log `20260911T034757Z-p25468.jsonl`).
It reached its bounded 256-event cap. The first seven pause-button resources
were observed with stable method indices `argument_4 = 2, 5, 8, 11, 14, 17,
20`, matching the first seven constructor resources. The method reads resource
fields at `+8` and `+12`, calls object-vtable slots 7 and 24, stores a result,
and invokes a resource-vtable slot 28; it behaves as property/binding setup,
not a proven label setter. The hook is removed from the authored surface and
the method is not promoted to the public API.

The normal-exit `pause-runtime-text-get1` run (runtime log
`20260911T030443Z-p36060.jsonl`, captures under
`.local/ui-api-research/2026-09-10/pause-runtime-text-get1`) recorded fourteen
pause-button constructions, including a visible `Leaf_11` inline value at the
embedded text object, but zero calls to `0x82E74FC8` and zero calls to
`0x82E73BE0` for either the text object or its nested resource. The getter and
pair-helper traces are therefore not on the visible pause-label path for this
route. The next setter probe must follow constructor-time binding or direct
content writes; neither helper is promoted to the public API.

The follow-up normal-exit `pause-runtime-field1` run (runtime log
`20260911T031616Z-p29988.jsonl`) also saw fourteen constructions and no calls
to the two static `CPauseMenuButton` field stores (`0x8264F450` and
`0x8264F458`) during bootstrap or pause open. Those one-run probes are now
removed from the authored hook surface; the result narrows the next experiment
to the constructor's post-initialization content boundary.

The pause-time vtable `0x8206D3B8` begins with `0x82806DD0` and
`0x82806E50`, the generated wrapper callers that forward into the two list
entries. This is a concrete derived menu/list table rather than the generic
`CUserInterface4` table; keep it as a runtime classification lead and do not
publish the table address as an ABI.

The targeted field scan in `pause-runtime-menu-fields2` also distinguishes the
menu owner from its child controls: `CMenuCtrl +312` is the animated list and
`+316` is the breadcrumb controller. The same fields appear on the bootstrap
and pause-open instances, so a future adapter can validate this graph before
using a title-owned list. It still must obtain the current scene instance and
call only recovered methods; writing either field or treating the offsets as a
general layout is unsafe.

The typed-wrapper trace in `pause-runtime-menu-dispatch-20260911022121`
(`20260911T022121Z-p37140.jsonl`) records the wrapper arguments before the
owner map call. Both bootstrap and pause-open dispatches use key `2`; the
bootstrap value is a `CSplash` object (`0x82059E8C`) and the pause value is a
`CPauseMenu` object (`0x8205109C`). Each wrapper routes through the owner's
`+312` animated-list child (`0x82063974`); its secondary vtable
`0x82063A0C` exposes slots 0 and 1 as `0x82E7CD78` and `0x82E77260`, followed
by the same owner calls. This establishes a screen-registration seam, not a
visible item ID or a safe append operation; the next trace must follow the
child list's provider/focus methods before any mutation.

A temporary navigation route (`.local/ui-api-research/2026-09-10/
pause-navigation.fh1test`) then sent one D-pad-down press followed by A while
the pause overlay was open. The `pause-navigation` capture shows a stock
Street Racing transition/loading page, and the later capture shows the map
screen with its `B EXIT MAP` prompt. This proves that the pause list accepted
focus movement and stock activation on the same save. The scripted B press was
too early to close the loaded screen, so return timing and a bounded
activation callback trace remain open work.

A follow-up route (`pause-navigation3.fh1test`, log
`20260911T010517Z-p408.jsonl`) waited longer, dismissed the resulting stock
dialog with A, and sent B after the map loaded. It exited normally and
captured the Ford Challenge screen followed by the map screen, but the map
remained visible after the scripted B. Treat that as successful activation and
safe process recovery, not as proof of screen close; the next input trace must
hold or repeat the title's map-exit action after the route is ready.

Holding B for one second in `pause-navigation4.fh1test` (log
`20260911T010714Z-p3856.jsonl`) moved from the map back to the stock
single-player/multiplayer selection screen. The process again exited normally.
This establishes a usable parent-screen back path inside the title, while the
pause-to-free-roam close and the semantic activation callback are still open.

UI-02 through UI-04 remain gates. No hook currently edits a shipped scene or
claims that the queue is connected to the guest graph. The default-off
`PINYON_SHIFT_UI_EXPERIMENT=hide_first` probe did consume the host API's
`SetVisible` operation at the frame boundary and wrote the first constructed
button's `+160` state byte, recording `ui.experiment.visible_mutation`; the
stock menu remained visible. The clean baseline
`pause-ui-baseline2` (log `20260911T035342Z-p29968.jsonl`) has pause raw hash
`ADBE4173176F6B16`, while the frame-boundary experiment
`pause-ui-hide-first-frame` has `F83696F20EF2AF29` and still renders all stock
items. This proves the queue-to-guest mutation plumbing is reversible, but
`+160` is not the visible list gate. Recover the actual item render/state path
before claiming scene mutation or insertion.

### Contract table and stock pause contents (2026-09-11)

The authored component contract table is now located in the verified image.
It is an array of `{name pointer, factory pointer}` pairs at `0x82031628`
through `0x82031C28`; the entries relevant to a pause extension are
`PAUSE_MENU_BUTTON` -> `0x82651438`, `ANIMATED_SCROLLING_LIST` -> `0x82643938`,
`MENU` -> `0x82645558`, `BUTTON_TEXT` -> `0x82651120`,
`BUTTON_TEXT_AND_TEXTURE` -> `0x826558F8`, `TEXT_LIST_ITEM` -> `0x82666B00`,
`HELP_BUTTON_BAR` -> `0x82644670`, `HUD` -> `0x82644700`, and
`MESSAGE_BOX` -> `0x826455A0`. The table also lists car, garage, livery,
scoreboard, storefront, and tab families; the full name/factory list is a
verified static result for UI-07 and UI-08. No recompiled function calls these
factories directly, so the adapter must resolve and validate the table rather
than assume a direct call site. `PAUSE_MENU_BUTTON` allocates 280 bytes and
then calls the constructor `0x8264FBA0` with the factory argument, which is the
input that becomes the button's `+84` label resource.

A stock pause capture (`.local/ui-api-research/2026-09-10/
pause-runtime-resource2/pause.png`) reads, through Windows OCR of the local
PNG, as: `MAP`, `MULTIPLAYER`, `PHOTO MODE`, `MESSAGE CENTER`,
`SPONSOR CHALLENGES`, `MY PROFILE`, `QUIT`, with the current car name
(`Volkswagen Corrado VR6`) and `NxtLv1 120 PTS` in the header and
`SELECT RESUME` in the button bar. That read is the reference for a visible
label change and is reproducible with the same OCR step; it is not part of the
public tree.

The new default-off `PINYON_SHIFT_UI_EXPERIMENT=text_probe` mode records a
bounded inventory of every observed pause-button text object and writes a
16-byte literal over a field that already holds printable inline text,
re-applying the write at each frame boundary. In
`.local/ui-api-research/2026-09-11/pause-text-probe1` (runtime log
`20260911T045156Z-p35544.jsonl`) it wrote one target,
`ui.experiment.text_write{slot=4, text_object=2E8E37BC, before=SL65AMG_09,
after=Pinyon UI}`. The write landed after the pause capture and the field held
a car name, not a visible pause item, so this run does not claim a visible
change. It does prove the queue-to-guest write path for a text target and
narrows the next step: the visible item labels are not the `+84` inline field
sampled here.

The bounded inventory from the 1x run (`.local/ui-api-research/2026-09-11/
pause-text-probe3`, runtime log `20260911T050458Z-p31392.jsonl`) recorded seven
targets, all still in their pre-binding state: vtable `0x82026B38`, words at
`+0..+40` zero apart from a nested `CUI4TextElement` pointer at `+12` and
vtable `0x820336A4` at `+36`, and an empty `+84` field. No target held
printable inline text while the pause overlay was up, so no write occurred in
that run. Item labels are therefore bound after construction, through a path
the current inventory does not sample; a probe that samples later or follows
the `+12`/`+36` objects is the next step. The two 14-button construction
batches (seven buttons each, at front-end load and at pause open) match the
seven visible pause items, which makes the second batch the natural target set.

Environment notes and the current runtime blocker. After the host executable is
rebuilt, every pause-route run on this machine produces a **frozen guest
output**: the `free-roam`, `pause`, and `resumed` captures share one
`raw_hash` (`F66290FE948EC6B1` in the 1x run
`.local/ui-api-research/2026-09-11/pause-text-probe3`, `38FBCB8091496AF1` in
the 3x run `pause-text-probe1`), while guest logic still runs normally — 14
pause-button constructions, registry attaches, the text inventory, every
`fh1.render_test.input_step` at its scheduled frame, and
`opening_movie.skipped`. The runtime log fills with
`FH1 vertex shader <hash> is absent from the offline analysis catalog` followed
by `PM4_DRAW_INDX(...): Failed in backend`, so the native path is failing its
draws. The offline pack in the preview state root was produced by an earlier
build; `tools/prepare-fh1-shaders.ps1` reuses a pack from
`.local/native-renderer/managed/run-*/` instead of reproducing one for the
current binary, so a rebuilt renderer cannot be exercised until a matching pack
exists. `tools/produce-fh1-artifacts.ps1 -WorkRoot <new> -RenderTestScript
<route> -Scale 1` is the production path, but it writes only into its work root
and does not register the result in the managed store; that registration step
is still open. No production run was performed for this checkpoint. A capture
comparison must therefore assert that the frames differ before claiming a
visual result.

Two smaller environment facts: the preview state root carries
`draw_resolution_scale_x/y = 3` for other renderer work, and the render-test
runner forwards `--game-argument=--draw_resolution_scale_x=1` (and `_y`) to the
game, which returns captures to 1280x720. Windows PowerShell 5.1 in this
environment resolves `Microsoft.PowerShell.Utility` to the PowerShell 7 module
first, which hides `Get-FileHash`; run the project scripts with a
`PSModulePath` that lists only the Windows PowerShell module directories, or
with `pwsh`. Reading visible text out of a capture needs a PPM-to-PNG
conversion first, because the captures are written as binary PPM and the
Windows OCR engine reads PNG.

### Pause component contracts (static, 2026-09-11)

`PAUSE_MENU_BUTTON` factory `0x82651438` allocates 280 bytes through
`sub_82C0F6C0` and calls constructor `0x8264FBA0` with the contract argument;
the constructor chains to base `sub_8264F3F0` and then `sub_827E5150`. It
writes four vtables (`+0`, `+4`, `+8`, `+32`) and embeds **two 12-byte
`CUI4TextElement` objects** at `+252` and `+264` through `sub_82E73B88`, then
clears the byte at `+276`. `sub_82E73B88` writes only
`{vptr = 0x82026B38, +4 = 0, +8 = 0}`, so a label lives in the `(+4, +8)` pair
of one of those elements. The earlier inventory that reported a "nested
`CUI4TextElement` pointer at `+12`" was reading the second element's vtable at
`+252 + 12`, not a pointer field.

`CPauseMenuButton` embeds **three** 12-byte `CUI4TextElement` objects, not two:
the grandparent constructor `sub_827E5150` creates `+164` (and initialises
`+176` through `sub_825D4C60`, zeroes `+200`, calls `sub_82411478` for `+204`,
and clears bytes `+232`..`+235`), while `sub_8264FBA0` creates `+252` and
`+264` and clears the byte at `+276`. The pair sampler previously read only
`+252` and `+264`; it now samples all three offsets, which is the first place a
visible label can still be hiding.

`0x82E73BE0` writes its `r5` argument to `+4` and `r4` to `+8` of such an
element, which matches the pair layout, but the pause route never reaches it,
so it stays an unproven candidate rather than the pause-label setter. The next
label probe must sample the `(+4, +8)` pair of the pause-open button batch while
the overlay is up, or hook the factory entry `0x82651438` to capture its caller
and the contract argument that becomes the label resource.

List and registration shape for the same screen: `sub_8282A760` first calls
`sub_82E7CD78` (keyed insert into the control's map) and then walks a container
at `[+32, +36)` in 20-byte strides, dispatching each child through vtable offset
`+32`; `sub_8282A7C0` mirrors it, and `sub_828306A8` walks a different range in
64-byte strides through `sub_8282EFD0`. Those are the structural seams for
reading and eventually extending a stock list; none is yet proven to be the
pause item provider, and no factory has a direct call site, so the caller of the
contract table remains the open question for insertion.

The rewritten `text_probe` mode is now a read-only pair sampler: it reads the
verified `(+4, +8)` pair of both embedded elements on every observed pause
button, six samples per second at 30-frame intervals, and records any readable
string those words point to. A 1x run
(`.local/ui-api-research/2026-09-11/pause-pair1`, runtime log
`20260911T225740Z-p31104.jsonl`) produced 320 `ui.experiment.text_pair` events
and shows the pair holding float-like values, not text: the first element
carries `value = 0x42251390` (~41.27) and `resource = 0x43814360` (~258.5) on
every button and the second element stays zero. So the label is not in the
text-element pair either; the remaining candidates are the button's `+84` label
resource and its `CUI4CustomObject` contents.

Correction to the earlier probe: the old write targeted `button + 252 + 84`,
which is `button + 336` and therefore **outside the 280-byte
`CPauseMenuButton` allocation** — that run wrote into a neighbouring heap
object, and the `SL65AMG_09` string it recorded belonged to that neighbour. The
write path is removed; the probe is read-only until a verified write target
exists.

Render environment, current state: with a rebuilt executable and a pack that
`tools/prepare-fh1-shaders.ps1` freshly produced *and validated* for that exact
build and scale (receipt key `396269EA17FCBC50D42C3FB912B8D1B1AB831265AF5FB85F8480A5F2AD5F6294`,
`4D5309C9.fh1-native-v2.10DE.09.1x1.pnsp`), every route renders flat frames.
The pause route and the shader-preparation route that produced the pack both
capture 1280x720 images with three sampled distinct colours, identical
`raw_hash` across captures, and 9,727 `FH1 vertex shader ... is absent from the
offline analysis catalog` errors in the run log. UI-04 runtime evidence is
blocked on that, not on the probe. A known-good executable/pack pair from
before the rebuilds, or a pause-route-driven pack production, is the next thing
to try.

The label search is now closed on two fronts. The title's text-pair helper
`0x82E73BE0` is never called with any of a pause button's three text elements
(`ui.pause_button.text_set` = 0 events over a full route), so it is not the
pause-label setter for any of the three offsets. Searching guest memory for the
rendered text is also negative: an incremental, page-validated sweep of
`0x2C000000`-`0x52000000` finds no `MULTIPLAYER` anywhere, while the same probe
finds and rewrites the ASCII car name (`Corrado` -> `PINYONX`, 11 verified
same-length writes with read-back confirmation) without changing the rendered
pause header. The engine therefore draws UI text from glyph runs or a layout
cache, not from the ASCII buffers a string search can find. A future label
probe has to hook the text-layout path (string to glyph run) rather than poking
strings, and the second UI allocation region observed at `0x40...` is the place
to look for the layout objects.

The widened probe settles the question. With the window covering
`0x10000000`-`0x82000000` and both ASCII and UTF-16LE encodings, a pause-route
run found 75 ASCII copies of `MULTIPLAYER` and rewrote every one to
`PINYONSHIFT` with read-back confirmation; 66 of those writes landed before the
pause capture (10 at 06:18:34, 2 at :35, 54 at :36, capture at :37). The
rendered pause item still reads `MULTIPLAYER`. The same probe rewrote 11 ASCII
copies of the car name `Corrado` in an earlier run without changing the pause
header. Pause-menu labels are therefore not drawn from any writable ASCII
buffer: the engine lays text out into glyph data when the scene is built and
renders that, so the label path has to be intercepted at the text-layout or
text-property stage, during scene construction, instead of by rewriting strings
after the fact. UI-04's label half stays open with that narrowed target; the
insertion half is unaffected and still points at
`sub_82E78078(registry, descriptor, name)`.

The insertion seam now has a driver, and the driver changes the plan. Hooking
the per-child builder `0x82E7A238` shows 117 invocations per pause route, all
from `0x82F268F0`, with records in the UI data heap (`0x4170Exxx`) and scene
owners at `0x2E1A0050` and neighbours. That caller is not a loop over a record
vector: it repeatedly calls `stream->vtable[1]` to read 4, 4, 4, 1, 1 byte
fields into stack buffers, accumulating the byte count, and branches on the
flags it reads. Authored scene children are therefore **deserialized from a
scene byte stream**, and the builder is a virtual method the deserializer
invokes per element. An extra item can consequently be added in only two ways:
synthesize a descriptor at runtime and call the create-by-name entry
`sub_82E78078(registry, descriptor, name)` through the title's own
initialization path (the UI-08 route, which needs a host-to-guest call), or
extend the stream before it is parsed, which is exactly the conditional UI-14
fallback. Repurposing or appending to an already-built list is not available,
and the previously probed `+160`/`+84`/string fields are not part of the
constructed item's contract.

The last two candidates close the question. The same probe searched
`0x10000000`-`0x82000000` for the two labels that contain a space, `PHOTO MODE`
and `MESSAGE CENTER`, in ASCII and UTF-16LE: **zero hits for either**. The
`MULTIPLAYER` copies found earlier are therefore state identifiers
(`SET_FOR_MULTIPLAYER` and friends), not the visible label. Pause-menu item
labels are not stored as text anywhere in guest memory; the scene carries
pre-shaped glyph data and the renderer submits that. Changing a menu label is
consequently not a text write at all: it needs either glyph-level
substitution at submission time or a re-authored scene, which is the UI-14
asset path. That is the precise blocker for UI-04's label half, and it is
independent of the insertion half.

The label source is no longer unknown. `media/stringtables/` holds one archive
per language (`EN.zip`, `DE.zip`, ...); inside `EN.zip`, `PauseMenu.str` is an
`LSB2` localization blob whose strings are UTF-16LE. It contains every visible
pause label at these byte offsets: `MESSAGE CENTER` 447, `RESUME` 477,
`SPONSOR CHALLENGES` 491, `QUIT` 681, `MULTIPLAYER` 4895, `MY PROFILE` 4919,
`PHOTO MODE` 5653, `MAP` 5707. `GameStrings.str` and `MainMenu.str` use the
same layout. Nothing in the archive holds these labels as ASCII, which is why
the earlier game-data searches came up empty, and why the runtime ASCII copies
found by the probe are derived text rather than the table itself.

The label half of UI-04 therefore reduces to one bounded probe: patch the
string table at its loader boundary, so the title's own text layout resolves
the modified string. Two candidate boundaries, in preference order: the
archive read that produces `PauseMenu.str` (the game reads the member through
the VFS, so the bytes can be substituted before parsing), or the loaded blob in
guest memory once it exists and before the pause scene is built. Patching the
on-disk archive is not an option with the current tooling because the project
carries LZX decompression only.

Two more runs settle the timing side. Restricting the sweep to the two UI
regions (`0x2E000000`-`0x30000000`, `0x40000000`-`0x42000000`) so a pass takes
about five frames still finds no UTF-16 copy of any label and no `PHOTO MODE`
in any encoding, while the per-frame scan cost perturbs the wall-clock route
enough that the pause overlay is no longer open at the capture frame. The
labels therefore never exist as text in the scanned heap in either encoding:
the string table is converted to glyph data as it is consumed, which is
consistent with every negative result above. Any future label probe must hook
the conversion itself (the consumer of the LSB2 strings) rather than search
memory, and must not add per-frame work while a wall-clock route is running.

The `LSB2` magic itself sits at `0x82230470` inside a data table whose
neighbour at `0x8223046C` is a destructor vtable (its first entry `0x82CAB8B0`
is a plain `store vtable, free-if-flag` stub). That parser/loader is not among
the emitted functions, so the conversion consumer has to be reached by a
targeted image scan for the `0x82230470` reference or by a runtime hook rather
than by grepping the generated sources.

The label half of UI-04 is proven. `sub_82CAFF28` is the string-table loader:
it builds `game:\media\StringTables\en\<name>.str`, opens a VFS stream, and
calls `sub_82CAC5B8`, the LSB2 reader, which compares the magic at
`0x82230470`, allocates `8 + payload_size` and reads the payload. `handle+4` is
the payload, `handle+8` the string pool, whose 6-byte index is searched by
`sub_82A831B0` and resolved by `sub_82CAB7D8` into a pointer straight into the
pool. The pool holds **big-endian UTF-16** code units, so the earlier
"UTF-16LE" reading of the `.str` file was one byte off — the same bytes seen
from the neighbouring byte. Because every consumer reads the pool directly, a
same-length in-place rewrite at load is visible everywhere: with the
default-off `PINYON_SHIFT_UI_EXPERIMENT=label_patch` the pause menu renders
`PINYONSHIFT` where `MULTIPLAYER` was and `PNYON MOD` where `PHOTO MODE` was,
while a control run on the same binary, pack and route shows the originals.
Two earlier claims are corrected: the labels do exist in guest memory (as BE
UTF-16), and the LSB2 reader is an emitted function that references
`0x82230470`.

The insertion half now has the missing capability and a sharper blocker. A new
codegen option (`context = true` on a midasm hook) publishes the live
`PPCContext` and `base` to the host function, so a hook can call recompiled
title code through the runtime's indirect-function table with an isolated
context copy. Re-entering the title's own builder `sub_82E7A238` with a copied
element record does create a genuine second `CPauseMenuButton` (component
vtable `0x820336A4`, its own 28-byte descriptor and enabled state), and the
title's own code links it into the owner's `+8` map and `+40`/`+56` child
vectors. The rendered pause capture is nevertheless unchanged: rows come from
the per-item element records the scene deserializer (`sub_82F268F0`) allocates
from the scene byte stream at a 4 KiB stride and feeds to the builder, not from
the containers the builder populates. Insertion therefore needs the stream side
(UI-14, duplicating or extending a per-item record) or another consumer of
those records; the container path alone cannot produce a row. The construction
path is now fully characterised: create-by-name is called only from
`0x82E7A38C` inside `sub_82E7A238`, the contract name is an MSVC `std::string`
at `r1+96` (observed values `menu`, `breadcrumb_menu`, `button_text`,
`super_stacker`, `help_button_bar`, `slider_tracker`, `spinner`,
`scrolling_text`, `pause_menu_button`), and the registry pointer is the global
at `0x834B53D4`.

Row creation is now characterised. The deserializer is `sub_82F26560`; per
authored item it allocates a wrapper record with `sub_82F2E870` (entry base
`+68`, kind 7), or an element record with `sub_82F2DF08` (entry base `+32`,
kind from the stream), appends each property through `sub_82F2E000` into the
document at `+80`, appends the record to the section pool with `sub_82F2EA38`
(vector at `section+92`, data `+124`, capacity `+128`, size `+132`), and finally
calls the component builder `sub_82E7A238` indirectly at `0x82F268EC`. Record
fields: `+0` name hash, `+4` stream value, `+12` parent, `+16` next sibling,
`+20` first child, `+28` flag halfword whose bit 0 selects the `+32` or `+68`
entry base, `+30` kind, `+31` property count, then `{id, value}` entries. The
seven pause rows are seven wrapper records at `0x1004` stride whose sibling
chain grows by exactly one entry per parsed row, and each item record carries
nine properties that differ only in four type-`0x14` object references — the
per-row geometry/identity object lives there, not in the owner containers.

A faithful replay of that sequence is implemented behind
`PINYON_SHIFT_UI_INSERT_MODE=replay` but its preconditions did not hold at
runtime (`pool_growth=0`, `element_matches_owner=0`), so the probe fell back to
the container-only path and still produced no eighth row. That fallback is the
precise remaining gap: the replay needs the document, element and section
identities the deserializer uses for a real row, which the new
`PinyonShiftTraceUiItemBuildCall` hook publishes at `0x82F268D0`.

The replay now runs, and it establishes the real limit. The earlier guard was
wrong: at `0x82F268EC` the deserializer calls `element->vtable[15]`, which is
`0x82F2A250`; that reads `*(element+32)` and tail-calls its vtable slot 1, so
the builder's owner is the `CUI4CustomObject` at `element+32` (vtable
`0x8224BFC4`), never the element itself, and the document is `element+0x1F4`.
With the precondition corrected (`element == *(owner+4)`,
`*(element+32) == owner`, `document+80 == record`) the probe replays the
sequence with the title's own allocators: the wrapper record and element record
are byte-identical to a source row in the fixed field region and in all nine
property entries, the section pool grows `0xFB -> 0xFD`, a real
`CPauseMenuButton` is created and one container pair is added.

The title then crashes anyway. Every variant that leaves the extra records in
the live scene document during deserialization dies with a guest access
violation (`0xC0000005`, read at `0x400000000` / `0x100000000`) 50-90 frames
after the insert and before the first capture, while a control run on the same
binary and route completes; the bisect shows that omitting the builder, the
pool push, the properties, the parent link, or the header copy each still
crashes, and only a heavily reduced variant reaches the capture frames. The
live document therefore cannot admit an extra record at all, reachable or not.
That closes the runtime-construction route for insertion and leaves the UI-14
stream route: patch the scene payload at its loader boundary so the title's own
deserializer builds the extra item from authored data, the same interception
pattern that already works for the string table.

The UI-14 stream boundary is now characterised, and it does not admit an
authored extra item either. The scene path format is
`GAME:\Media\UI\Scenes\UI4\%s.bgf` (image string `0x82036AD4`), and the bytes
reach the scene builder
through the 12-byte reader at `document+12` (vtable `0x82274BEC`) whose slot-1
method `sub_82F25568` copies sequentially from the cursor object at
`reader+4`. That the reader hands over the authored member verbatim is proved
directly: with `PINYON_SHIFT_UI_EXPERIMENT=scene_probe`, the delivered bytes at
the start of `925_PAUSE_MENU` are `01 04 00 00 00 1A "AnarkBGF"`, identical to
the extracted file header.

One item section is read by `sub_82F26560`: a 4-byte declared byte length and
then `*(document+16) + *(document+20)` items. Each item is
`F1(4) F2(4) F3(4) B1(1) B2(1)`, followed by one extra byte and one extra word
when bit 2 of `B2` is set (wrapper: `sub_82F2E870`, kind 7, entry base `+68`) or
by `B1` as the kind byte (element: `sub_82F2DF08`, kind 8, entry base `+32`),
then a 4-byte property count and `N * {4-byte id, 4-byte value}` appended with
`sub_82F2E000` and pushed with `sub_82F2EA38`. The parsed fields are
byte-identical to the authored stream: the observed wrapper
`068C6274 FFFFFFFF 00000001 07 05` matches `925_PAUSE_MENU.bgf` at `0x3AE2`,
and the seven pause rows are seven consecutive wrapper+element pairs of 121
bytes (31-byte wrapper + 90-byte element) at `0x40DF + k * 3461`.

Extension is defeated by two fields that live outside the item stream. The
count is `*(document+16) + *(document+20)` read at `0x82F26630`, not a stream
value, so it can only be raised by writing a private document field. The
stream itself is length-checked: after the last item `r27` must equal the
4-byte declared length or `0x82F268F8` reports an error through `sub_82F30550`
and returns 0, aborting the whole scene build. Adding one row therefore needs
the count, the declared length, and 121 contiguous item bytes to change
together. Because the reader is one sequential cursor shared with the element's
other sections, the only way to place the extra bytes is to insert them into
the in-memory scene image and shift the remainder; there is no spare item slot
to repurpose (all seven wrapper records are live list rows, and the scene's
remaining items belong to other components). UI-14 therefore needs a scene
re-encoder that rewrites the length and count fields together with the shifted
document, not an in-place payload patch. The read-only probe hooks
(`PinyonShiftTraceUiSceneDeserializerEntry`, `…ItemLength`, `…ItemFields`,
`…StreamRead`, `…ReadResult`) stay default-off and are the tooling for that
work; a default-off run and a `scene_probe` run both render the seven stock
labels (captures under `.local/ui-insert4/`).

The loader boundary is identified as well: the pause scene is read as
`GAME:\Media\UI\Scenes\UI4\925_PAUSE_MENU.bgf` by a 12-byte reader object at
`document+12` (vtable `0x82274BEC`, slot-1 method `sub_82F25568`, sequential
cursor at `reader+4`), and the decompressed member sits in the UI heap
byte-identical to the extracted member — that is the buffer a re-encoder's
output would have to reach.

The UI-14 workstream now has its tooling and a proven feed, with only the
visual confirmation outstanding. `tools/fh1-ui-scene-insert.py` parses the
pause member strictly (the item section must consume exactly its 4-byte
declared length, and the seven authored row wrapper+element pairs must be
present with matching parent indices), and re-encodes it without changes
byte-for-byte (roundtrip reproduces the 168329-byte stock member, sha256
`c03bb7c4…`). Its insert mode duplicates row 0's 121-byte wrapper+element pair
at the section end, rewrites the copy's element parent index to the appended
wrapper's record index, raises the declared length `0xB25B -> 0xB2D4`, and
increments the header count words at `0x24`/`0x28` and their mirrors at
`0x70`/`0x74`. The count question is settled in the member's favour: the item
count is copied out of those header words by the scene header parse, so a
re-encoded member alone yields count+2 — confirmed by a run that consumed the
re-encoded declaration `0xB2D4` and reported `elements=504, wrappers=52`.

Feeding works too: the object at `reader+4` is a stream cursor whose `+4` is
the member's byte offset but whose `+0` is an internal buffer, so there is no
single base pointer to swap; instead the reader method `sub_82F25568` is
intercepted (bulk continuation `0x82F255EC` and the byte loop `0x82F255C0`) and
every byte delivered for the pause member is served from a guest copy of the
re-encoded member allocated with `SystemHeapAlloc`. The member is recognised
from the first `0x24` delivered bytes. All of this stays behind
`PINYON_SHIFT_UI_EXPERIMENT=scene_insert` and is one-shot.

What remains is the verification run: insert-mode captures showed the world
still loading at the pause capture frame, and one variant died with a null
indirect call inside the per-child builder loop, so the eighth row has not yet
been confirmed on screen. That is now a timing/crash question about the
substituted payload, not a format or capability question.

### Original game assets

The local `media/UI.zip` contains 694 entries: 230 `.bgf`, 205 `.bsg`, 205
`.fbf`, five Lua files, and ancillary assets. There are no `.swf`, `.gfx`,
`.xui`, or `.xur` entries in this archive. Those counts describe shipped
content, not the number of active screens or reusable templates.

Ten selected archive entries were extracted locally with the existing
[LZX helper](../tools/fh1_archive_extract.cpp); all ten matched their ZIP
uncompressed size and CRC. They include the three `925_PAUSE_MENU` files,
`BUTTON_BAR_SCENE.bgf`, `947_HUD.bsg`, three Lua behaviors, `fontmap.xml`,
and a font conversion log. The inspection found:

| Evidence | Consequence for the API |
| --- | --- |
| Pause and button-bar `.bgf` files contain the `AnarkBGF` marker. | Start from the Anark/UI4 integration, rather than assuming Flash/Scaleform or Xbox XUI. |
| Pause content contains `UIContract`, `ANIMATED_SCROLLING_LIST`, `PAUSE_MENU_BUTTON`, `BUTTON`, and `SUPER_STACKER`. | Named component contracts are promising integration points; their runtime methods and capacities remain unknown. |
| Paths include `parent.Layer.Option_List` and `parent.Layer.ScreenTitle.TEXT_SCREEN_TITLE`. | Prototype semantic lookup through the existing graph. Do not expose guessed offsets or global name searches as the public API. |
| The button bar contains `HELP_BUTTON_BAR` and `HELP_BUTTON`. | Reuse original prompt/glyph components and navigation conventions. |
| Pause `.fbf` data names noise, dirt, tape, message-icon materials, and Horizon fonts. | A matching UI needs the original material/animation composition as well as colors and typography. |
| `media/ui/Fonts.zip` contains 39 entries, including 18 `.dt` files and `fontmap.xml`; the map defines Horizon font aliases and CHT/KO/JP fallback adjustments. | Reuse title font resolution. A desktop TTF substitute would not establish fidelity. |
| `media/ui/Textures.zip` contains 3,312 `.xds` entries; `media/ui/textures/Horizon.zip` contains 1,061. | Reuse title texture lookup and ownership before considering a separate host decoder. |
| Lua behaviors reference element attributes and events; one delegates to another script path. | Scripting is a discovery lead only. Presence does not prove execution, a complete shipped script environment, or an extensible Lua API. |

The archives also contain `708_PAUSE`, `925_PAUSE_MENU`, multiple options
screens, and HUD variants. A filename is not proof that a particular gameplay
route loads that screen. UI-02 must identify the active route.

Most entries use compression method 21. Unlike the headerless track payloads
handled by the current [shader extraction caller](../tools/extract-fh1-shader-corpus.py),
the inspected UI entries have local ZIP headers. Passing `header_offset`
directly to the helper failed. Passing the payload offset after the 30-byte
header, filename, and extra field succeeded. Preserve both layouts when
reusing that code; ordinary Python `ZipFile.read()` cannot decode method 21.
Do not assume ordinary ZIP repacking preserves the title's archive semantics.

### Executable discovery leads

The existing local analysis image contains Anark 4.0.7 source-path strings,
`AKBGFDeserializer`, `AKBSGDeserializer`, contract/element/animation builders,
and RTTI for scene, input, and rendering classes. This independently supports
the Anark/UI4 identification. It does not establish an ABI or callable API.

Useful seeds for the next investigation:

| Image address | String or type seed | Investigate |
| --- | --- | --- |
| `0x82036AD4` | UI4 scene `.bgf` path format | Scene resource lookup and archive resolution |
| `0x8203FC1C` | `925_PAUSE_MENU` | Pause registration and scene activation |
| `0x82030788` | `PAUSE_MENU_BUTTON` | Component binding/factory and activation |
| `0x820314B0` | `ANIMATED_SCROLLING_LIST` | Item provider, capacity, focus, and scrolling |
| `0x8224C0DC` | `CAnark4SceneResource::PreProcess` | Load/relocation and companion-file processing |
| `0x8224C294` | `UIContract` | Contract resolution and typed properties |
| `0x8224C38C` | `COMMAND_FIREEVENT` | Event dispatch and command boundary |
| `0x832BBB68` | `CSceneManager@Anark4` RTTI | Create, activate, deactivate, release |
| `0x832BBC44` | `CCustomObjectFactory@Anark4` RTTI | Supported object construction and initialization |
| `0x832BBCB0` | `CInputEngine@Anark4` RTTI | Action routing and focus ownership |
| `0x832BBE68` | `CRenderEngine@Anark4` RTTI | Update/render boundary and resource lifetime |

Addresses above identify data, not hook locations or constructors. Revalidate
every seed against the selected image before resolving callers.

The class-family scan adds one bounded, reusable lead for UI-03:

| Type family | Primary vtable | Relevant entries | Current use |
| --- | --- | --- | --- |
| `CAnimatedScrollingListCtrl@ForzaUI` | `0x82063974` / `0x82063A0C` | `0x82E7CD78`, `0x82E77260` | The `+312` helper is RTTI-classified as this type; its primary constructors are `sub_827E4B18` and related thunks. |
| `CMenuCtrl@ForzaUI` | `0x8206D3B8` | `0x82E7CD78`, `0x82E77260` | Live pause object at owner `+8`; constructor writes this subobject vtable. |
| `CBreadcrumbMenu@ForzaUI` | `0x82063CA4` | `0x82E7CD78`, `0x82E77260` | Live pause object field `+316`; do not use it as a public ABI. |
| `CPauseMenuButton@ForzaUI` | `0x8203363C` | `sub_8264FBA0` / post-construction probe `0x8264FC08` | The factory input becomes the label-resource pointer at button `+84` (runtime vtable `0x8224CC94`); a separate embedded text/layout object is initialized at `+252`. The class and offsets are verified, but the public action and setter contracts are still open. |
| `CUI4TextElement` | `0x82026B38` | vtable methods include `0x827D86E0`, `0x82E74378`, `0x82E74448`, `0x82E74518`, `0x82E745A0`, and `0x82E74668`; candidate value pair helper `0x82E73BE0` | Live pause-button layout objects use this vtable. A targeted read-only trace reached `0x82E73BE0`; its generated body stores the two arguments into the text object's `+4`/`+8` pair. Keep it as a generic resource-pair candidate until a caller proves the owned object and a post-write rendering change. |

The image's authored contract table provides a second, stronger construction
lead. It maps the names `MENU`, `ANIMATED_SCROLLING_LIST`, and
`PAUSE_MENU_BUTTON` to factories `0x82645558`, `0x82643938`, and
`0x82651438`; the first two allocate 332 and 808 bytes respectively, while
the button factory allocates 280 bytes before running its normal constructor.
These are title-owned factories selected by contract name, not a callable host
ABI. The adapter should resolve the contract table and validate the current
image before considering a factory call; it must not reproduce these sizes or
constructors in extension code.

Generated callers `sub_8282A760` and `sub_8282A7C0` call these entries and then
iterate a child range whose begin/end fields are at object offsets 32 and 36,
dispatching each child through vtable slots 32 and 36 respectively. That is a
structural population lead only; it does not identify the live pause-list
instance or make those offsets part of the public API.

Two additional generated callers (`sub_82806DD0` and `sub_82806E50`) forward
typed values through an owner field at offset 312 before calling the same list
entries; `sub_826676F0` enumerates a begin/end range at offsets 116 and 120
before the call. These are useful caller shapes for the runtime trace and
confirm that the functions participate in stock object population, while their
screen ownership and item semantics remain unresolved.

The generated body of `sub_82E7CD78` advances to the `+8` list subobject,
looks up a 32-bit key through its ordered map, creates a map node on a miss,
stores the caller's value at the new child `+12`, and links it through the
existing container helper. `sub_82E77260` follows the same lookup path and
then applies a typed update. The pause route supplies key `2`; this is a
useful insertion lead, not yet proof that the key represents a visible menu
item or that a host-created node is safe to activate.

The static constructor path is also bounded: `sub_82645558` allocates 332
bytes and calls `sub_828116C8`; that constructor writes the `CMenuCtrl`
parent vtable at offset 4, the `0x8206D3B8` list vtable at offset 8, and
initializes fields at offsets 0, 4, 32, 108, and 300–328. The runtime probe
now confirms this `+8` subobject layout on the active pause route. The fields
remain private until their item-provider and ownership meanings are confirmed.

The inspected analysis image SHA-256 is
`5ce77d34952a8c65b432d84e5eb9b321f2cbb9f8c0377567decd77afbf93927c`.
Its derivation was not re-run against the current XEX during this research.

Raw extracted files and inspection manifests remain private under
`.local/ui-api-research/2026-09-10/`; `inspection.json` records entry hashes,
size checks, and CRC checks, and `image-strings.json` records discovery seeds.
Publish independently authored findings and code, not those assets or dumps.

### Existing project foundations

| Existing code | Reuse and limitation |
| --- | --- |
| [Title hook configuration](../config/rexglue/analysis/main-xex.toml) and [runtime hooks](../src/pinyon_shift_runtime_hooks.cpp) | Existing mid-instruction hooks and bounded observation patterns. Add title UI integration here through a dedicated UI implementation; do not edit generated translations. |
| [Host lifecycle](../src/pinyon_shift_app.h) | Own API startup/shutdown and attach to the runtime. Windows UI-thread callbacks are not automatically safe title UI update points. |
| [ReXApp extension hooks](../thirdparty/shiftglue-sdk/include/rex/rex_app.h) | `OnCreateDialogs`, `OnConfigureFonts`, and `OnConfigureStyle` support host ImGui tools. Useful for inspection, but these do not edit FH1 scenes. |
| [SDK input setup](../thirdparty/shiftglue-sdk/src/ui/rex_app.cpp) | Current active-input gating checks ImGui `WantCaptureMouse`. Do not treat it as a complete controller/keyboard/modal ownership contract. |
| [SDK virtual filesystem](../thirdparty/shiftglue-sdk/src/filesystem/virtual_file_system.cpp) | Device registration and path resolution exist. Resolution picks the first matching device; it is not an archive-member overlay or a general merge mechanism. |
| [Render test harness](native-renderer/FH1_RENDER_TEST_AUTOMATION.md), [visual baselines](../tools/visual-baseline.py), [image comparison](../tools/compare-native-renderer-images.py) | Extend existing scene routes and captures. Input delivery alone does not prove a control was focused or activated. |
| [Current renderer findings](DEVELOPMENT.md) | The earlier HUD admission prototype is unretained. UI API work must not silently enable it or depend on full renderer replacement. |

## Alternatives and external research

| Approach | Assessment |
| --- | --- |
| Wrap original scene/component contracts | Preferred. Potentially preserves actual appearance and behavior with the smallest rendering change. Requires runtime discovery and a demonstrated insertion path. |
| Patch local UI assets at load time | Useful fallback for data/layout restrictions. Requires validated formats, companion-file handling, cache invalidation, and immutable original inputs. Static edits alone do not supply events or high-level controls. |
| New ImGui interface | Already available for developer tools. A themed overlay still needs a title bridge to modify existing screens and cannot by itself reproduce their materials, transitions, and focus. |
| New RmlUi or browser-based interface | Offers a higher-level authoring model, but adds rendering/input integration and a separate style implementation. Defer while the original system remains viable. |
| Replace the entire UI renderer/middleware | Too broad for this foundation. Only reconsider after a specific unsupported requirement is demonstrated. |

Anark's representative described Gameface as an artist-authored UI runtime
and identified Forza Motorsport 2 as a customer in this
[first-party interview](https://www.gamedeveloper.com/game-platforms/tooling-around-anark-on-gameface-s-next-gen-ui).
That is historical context, not evidence of FH1 compatibility; FH1 evidence
comes from the local files above. Do not confuse historical Anark Gameface
with a modern product that happens to share the Gameface name.

[RmlUi's own integration guide](https://mikke89.github.io/RmlUiDoc/pages/cpp_manual/integrating.html)
requires a render interface, application-driven update/render calls, fonts,
and input injection. This supports treating it as an alternative renderer
integration, not an adapter for existing Anark scenes.
[Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp) demonstrates useful
in-game configuration and mod support in a recomp, but does not establish a
way to edit FH1's UI.

The [ForzaTech localization toolkit](https://github.com/7akeem0/forzatech-localization-toolkit)
documents newer Forza games' fonts and UI archive layout constraints. Its
documented `.vfont` formats are not the `.dt` assets inspected here. Treat it
as a format-research reference, not an FH1-compatible dependency. No verified
drop-in FH1 scene editor or public UI SDK was established by this search.

## Proposed API boundary

Start with one compiled-in extension and a C++ source API. Use a small set of
declarative component descriptions for ordinary UI work. No external script
engine, binary plugin ABI, UI editor, or general mod loader is needed to prove
the foundation.

```text
Extension: named screens, components, data, and actions
        |
Pinyon UI API: semantic lookup, scoped edits, reusable components
        |
FH1 adapter: verified contracts, lifecycle, guest calls, event routing
        |
Original UI4/Anark scene system -> existing game rendering path
```

| API capability | Intended behavior |
| --- | --- |
| Observe a named scene becoming ready/closing | Attach once per instance; reapply after reload; invalidate handles on destruction. |
| Find a supported component by semantic ID | Map a stable public ID to a verified scene-local contract; report missing/ambiguous matches. |
| Modify text, visibility, enabled state, image, and layout | Validate supported types and ownership. Restore scoped changes without overwriting later title updates. |
| Add/remove menu items and bind actions | Use the title list/provider and event mechanisms. Preserve existing items, scrolling, and selection. |
| Build a page from stock components | Menu item, label, button prompt, toggle, and choice row initially. Match measured style through original component instances. |
| Bind extension data | Update changed values at the title UI update boundary, rather than rebuilding controls on every render. |
| Show/close a page or modal | Participate in scene navigation, focus, pause state, transitions, and return behavior. |
| Attach a noninteractive HUD component | Use a verified HUD slot, inherit visibility rules, and never claim input. |

Semantic IDs are an API design, not existing game exports. The first API should
explicitly list supported screens and component types; arbitrary modification
of every shipped screen is not a v0.1 promise.

Illustrative authoring shape, **not implemented or compilable yet**:

```cpp
ui.on_scene_ready("pause_menu", [](ui::Scene& scene) {
  scene.menu("options").add_item({
      .id = "pinyon.interface_demo",
      .label = ui::text("pinyon.interface_demo"),
      .action = ui::open_page("pinyon.interface_demo"),
  });
});
```

Callers should not know guest addresses, PPC registers, shader hashes, font
file names, or material pointers. Template/control factories should carry the
original defaults, with a small set of semantic variants for intentional
differences. Reusing the renderer alone does not establish style fidelity.

The adapter must execute mutations on the proven title UI owner thread at a
safe update point, preserve the guest calling convention, and use guest-owned
allocation/string lifetimes. Do not pass host pointers as guest objects or
call title functions directly from the ImGui/window thread. Bound queued work
and reject stale scene generations; render callbacks must not mutate the graph.

## Actionable backlog

Unchecked tasks below are open; checked rows record bounded foundation work,
not a complete runtime implementation. Size bands are planning estimates for focused
engineering work: S = up to one day, M = two to three days, L = four to five
days. Reverse-engineering tasks have low estimate confidence. If an L task
exceeds its timebox, record the unresolved contract and split the investigation.

| Task | Priority | Depends on | Size | Deliverable |
| --- | --- | --- | --- | --- |
| UI-01 | P0 | — | S | Reproducible archive/asset catalog |
| UI-02 | P0 | UI-01 | L | Verified scene lifecycle and loading path |
| UI-03 | P0 | UI-02 | L | Component, list, property, and event contracts |
| UI-04 | P0 | UI-03 | M | Existing-screen modification and insertion proof |
| UI-05 | P0 | UI-04 | M | Safe guest bridge and scoped ownership |
| UI-06 | P0 | UI-05 | M | Public API for supported existing-screen edits |
| UI-07 | P0 | UI-05 | M | Original style/component catalog and font resolution |
| UI-08 | P0 | UI-06, UI-07 | L | Higher-level components and new page navigation |
| UI-09 | P0 | UI-08 | M | Focus, controller, keyboard, and modal behavior |
| UI-10 | P0 | UI-06, UI-07 | M | In-game HUD extension and binding proof |
| UI-11 | P0 | UI-08, UI-09, UI-10 | M | Real extension demo with host settings |
| UI-12 | P0 | UI-09, UI-10, UI-11 | M | Regression/performance qualification |
| UI-13 | P0 | UI-12 | S | Documented v0.1 API and recovery path |
| UI-14 | Conditional | UI-04 feasibility failure | L | Minimal asset-load extension path |

### UI-01 — Make asset discovery reproducible

- [x] Add one `tools/inspect-fh1-ui.py` entry point that lists archive entries,
  methods, sizes, hashes, scene families, font aliases, and asset references.
  Reuse `zipfile` for metadata and the existing LZX helper for payloads.
  Handle both local-header and raw-payload offsets; validate bounds, output
  sizes, and CRCs. Keep all derived output below `.local/`.
- [x] Record input XEX/archive hashes and the analysis-image provenance. Inventory
  localization resources and companion files without assuming file roles. The
  local run wrote `.local/ui-api-research/2026-09-10/catalog.json` for four
  archives and extracted the pause menu, button bar, HUD, Lua behaviors, and
  `fontmap.xml`.
- [x] Done when the ten inspected samples reproduce and one asset-free check
  rejects a malformed offset/truncated entry. Do not write a scene serializer.

### UI-02 — Trace one real screen end to end

- [x] Trace the UI4 registry construction and bootstrap dispatches on the
  pause render-test route, including the live manager object and indexed table
  activity. The lifecycle and active-scene owner are still unresolved.
- [ ] Resolve callers of the scene-path and pause seeds, then trace boot menu ->
  free roam -> pause -> options -> back. Record the actual loaded scene IDs,
  resource paths, instance identity, owner thread, load/unload order, and safe
  mutation point. Check all callers of each proposed shared hook.
- [ ] Identify archive vs loose-file precedence, cache ownership, and whether
  `.bgf`, `.bsg`, and `.fbf` are all consumed on this route. Trace scene rendering
  to the existing submission path; no new GPU renderer is required.
- [ ] Done when a bounded, default-off trace shows three open/close cycles with
  consistent ownership and no guessed hook addresses. Keep hooks in authored
  configuration and `src/ui/`, not generated code.

### UI-03 — Recover the smallest usable component contracts

- [x] Confirm the shipped class families and static method seeds for
  `CUI4Element`, `CUI4Control`, `CMenuCtrl`, `CScrollingListCtrl`, and
  `CAnimatedScrollingListCtrl`; the inherited list entry points are
  `0x82E7CD78` and `0x82E77260`. Runtime ownership, lookup, and activation are
  still unverified.
- [x] Observe a live pause-time list object: the constructor probe records a
  332-byte owner allocation and the list subobject at owner `+8`, with vtable
  `0x8206D3B8`; calls `0x82E7CD78` on pause open and `0x82E77260` on resume.
  This identifies a route-specific object and call timing, but not its item
  provider, focus state, or activation callback.
- [x] Exercise the stock focus and activation path with D-pad-down then A. The
  route reaches a Street Racing transition and the map screen, proving input
  acceptance and stock navigation on the same save. A held B returns from the
  map to its stock parent selection screen; pause-to-free-roam close timing
  still needs a dedicated trace.
- [x] Read a live pause-button label boundary. The post-construction probe at
  `0x8264FC08` sees `CPauseMenuButton` text at `+252` with vtable
  `0x82026B38`; the run recorded printable inline text such as `Explorer_10`.
- [x] Locate the authored component contract table in the verified image: an
  array of `{name pointer, factory pointer}` pairs at `0x82031628` through
  `0x82031C28`, including `PAUSE_MENU_BUTTON` -> `0x82651438`,
  `ANIMATED_SCROLLING_LIST` -> `0x82643938`, `MENU` -> `0x82645558`, and the
  button, list, tab, grid, slider, HUD, and garage families. No recompiled
  function calls these factories directly; the adapter must resolve and
  validate the table.
- [ ] Follow `UIContract`, pause-button, list, and command-dispatch references.
  Recover the text/property setter, list population, activation, selection,
  resource references, destruction, and guest ABI. Determine whether the list
  is dynamic, virtualized, or limited to preauthored slots.
- [ ] Trace how the title rewrites bound values so a patch is not immediately
  overwritten. Determine whether shipped Lua actually executes before assigning
  it any role. A usable native contract is sufficient without Lua.
- [ ] Done when one label read and one existing control's full activation path
  are explained with verified types, callers, and ownership.

### UI-04 — Prove modification AND extension before building the API

- [ ] Behind one default-off flag, change a real pause-menu label and append an
  additional selectable item using the original list/component mechanism.
  Give it an extension-owned action that records one bounded activation event.
  It must coexist with every existing item; repurposing a stock item fails.
- [ ] Verify focus/scroll behavior at the added item, correct activation, back,
  and repeated close/reopen with no duplicates. Capture stock and modified states
  on the same build. Disabling the flag must recover the original interface.
- [ ] Decision gate: pass -> UI-05; fixed capacity or no safe construction path
  -> UI-14. An overlay, label replacement alone, or silent scope reduction is
  not an acceptable substitute for insertion.

### UI-05 — Harden the title bridge and lifetime rules

- [x] Establish the asset-free source boundary in `src/ui/`: bounded pending
  operations, generation-tagged scene handles, semantic IDs, and cleanup
  semantics are implemented and tested. This is only the host-side queue; it
  is not evidence that guest calls are safe or connected yet.
- [ ] Implement only the guest calls proven above, with typed arguments,
  validated guest ranges, supported-image checks, and generation-tagged handles.
  Queue host requests to the established title update boundary; reject shutdown,
  expired scenes, unsupported contracts, and excessive pending work.
- [ ] Give each extension a scoped registration that removes its listeners and
  owned controls. Define conflict/rollback behavior: do not blindly restore an
  old property over a newer title-owned value. Apply changes atomically enough
  that a failed insertion leaves the original scene usable.
- [ ] Done when an asset-free lifecycle check covers a stale handle, failed
  operation, duplicate registration, and cleanup; runtime reopen/exit also passes.

### UI-06 — Expose supported existing-screen edits

- [x] Add the initial source API header/implementation for the future adapter;
  the supported-screen operation set remains intentionally unadvertised until
  UI-04 proves a live component contract.
- [ ] Add the smallest public header and implementation under `src/ui/` for
  scene-ready/closing hooks, scoped component lookup, typed property changes,
  menu insertion/removal, and action registration. Semantic IDs resolve through
  the adapter; unsupported operations return an explicit error.
- [ ] Define ownership, insertion ordering, and duplicate-ID behavior for two
  compiled-in extensions. Reject conflicting destructive edits rather than
  silently using registration order. Keep engine internals private.
- [ ] Done when the UI-04 experiment uses only this API and a missing target
  leaves the stock scene functional. Verify cleanup and conflict handling.

### UI-07 — Preserve original styling as reusable component defaults

- [ ] Catalog active pause/options/HUD examples: font aliases and metrics,
  localized fallback, material layers/masks, clipping, margins, alignment,
  selected/disabled states, prompt glyphs, sounds, and transition timing.
  Resolve exact values/assets locally; do not invent a similar-looking theme.
- [ ] Prefer title component instances/factories and title text layout. Use
  measured semantic variants only where supported. Cover long translated labels,
  numbers, glyph fallback, and a missing-asset error without a crash.
- [ ] Done when an added control beside a stock sibling matches at 1x and 2x,
  both idle and during focus animation. Include a long Latin translation and
  a CJK locale; keep redistributable definitions free of extracted assets.

### UI-08 — Build higher-level pages with original controls

- [ ] Add declarative descriptions for a page, menu item, label, button prompt,
  toggle, and choice row, using UI-07 defaults. Populate existing contracts or
  instantiate a validated stock template through its real initialization path.
  Do not shallow-copy guest objects or duplicate pointers in compiled blobs.
- [ ] Register a new logical extension page in the title navigation flow. Reuse
  a stock layout if feasible; retain the original screen underneath, back stack,
  focus restoration, transition duration, and teardown.
- [ ] Done when the extra pause entry opens a page containing new labels and
  controls, their values/actions work, and back returns to the original item.
  Feature authors must not supply guest addresses or rendering code.

### UI-09 — Complete input and modal integration

- [ ] Use the original semantic actions for navigation, accept, back, and tabs.
  Preserve controller repeats, dead zones, held-button release across opening,
  disconnect/reconnect, keyboard mappings, and loss of window focus.
- [ ] Establish one input owner during modals; prevent accept/back leaking into
  the underlying menu or gameplay. Reuse the title's pause/navigation behavior
  instead of pausing arbitrary runtime threads. Confirm coexistence with SDK
  settings/console and platform dialogs. Noninteractive HUD content takes no focus.
- [ ] Done when scripted assertions and manual controller/keyboard checks show
  one action per activation and no stuck inputs. If mouse interaction is exposed,
  qualify hit testing and scaling; otherwise document keyboard/controller support.

### UI-10 — Demonstrate extension during gameplay

- [ ] Identify an active HUD container and append one noninteractive value using
  a stock text/panel component. Use extension-owned session data first so this
  test does not depend on unverified gameplay-memory offsets or save writes.
- [ ] Update only changed data at the title update boundary. Inherit the title's
  HUD suppression rules for pause, map, cutscenes, photo mode, and transitions.
  Verify the new component's layer, clipping, cleanup, and render-resource lifetime.
- [ ] Done when original HUD elements can be scoped-edited and the extra element
  survives a race/free-roam transition without duplicates or residual rendering.
  Do not activate the unretained renderer HUD prototype.

### UI-11 — Ship a useful first extension example

- [ ] Replace the proof action with a "Pinyon Shift" page reachable from the
  existing menu. Include a host-owned "Show session information" toggle for the
  UI-10 HUD component and a choice row for its detail level. This exercises
  navigation, bindings, high-level controls, and a visible result.
- [ ] Persist only these host preferences through the established config system
  with validation and migration as needed. Do not add fields to ForzaProfile or
  reinterpret existing game-setting persistence. Failed writes keep the session
  usable and report that preferences were not saved.
- [ ] Done when both settings work, survive relaunch, and recover to defaults.
  A second small extension must use the API without changing the FH1 adapter.

### UI-12 — Qualify the foundation against the real game

- [ ] Extend the existing `.fh1test` routes and visual checks to cover pause,
  options, extension page, modal, map, garage, and gameplay HUD. Add API lifecycle
  markers so checks establish actual scene readiness, control count, selected ID,
  and accepted action; controller delivery alone is insufficient.
- [ ] Run the matrix below, preserve failed runs, and compare control/candidate
  captures plus clean timing windows. Cover release code generation/build as
  well as asset-free API checks. No generic UI test framework is necessary.
- [ ] Done when the visual/input/lifetime gates pass and measured added cost
  fits the agreed budget, with unresolved coverage explicitly recorded.

### UI-13 — Make v0.1 usable by the next feature

- [ ] Document supported semantic IDs/components, API calls, thread/lifetime
  rules, text/localization, actions, errors, ordering/conflicts, and examples.
  Keep unsupported screens explicit. Version the source API when breaking changes
  occur; do not promise a stable external DLL ABI.
- [ ] Provide one startup disable/recovery path and concise diagnostics including
  extension ID and compatibility result. Unsupported game versions must decline
  activation without changing stock UI. Package only authored code/descriptions.
- [ ] Done when another developer can implement one menu extension using the
  documentation without editing generated code, SDK internals, or original assets.

### UI-14 — Conditional fallback: extend the asset load path

- [ ] If UI-04 proves the live graph/list cannot admit a new item, document the
  precise limitation. Locate a loader boundary where an authored recipe can
  create a modified local scene from the user's original assets before relocation
  and contract binding. Verify all required companion files and allocations.
- [ ] Add only the format support needed for that extra item/page. Require a
  no-change roundtrip before modifications, bounded parsing, source hashes,
  deterministic cache keys, and atomic derived-output activation. Never patch the
  extracted base archive in place or assume VFS can replace individual members.
- [ ] Reuse original runtime actions and rendering. Pass UI-04 using this route,
  then continue UI-05. If neither route works within the timebox, report the exact
  blocker and re-estimate scene-format work; do not declare an overlay successful.

## Qualification matrix and release gates

| Area | Required evidence |
| --- | --- |
| Existing-screen editing | A scoped label/property change on the active stock screen; correct restoration after disabling. |
| Genuine extension | One additional item, new page, and HUD element, with all original controls retained. |
| Style | Side-by-side stock/new siblings, focused/disabled states, text baselines, masks, glyphs, sounds, and animation recordings. |
| Resolution | Supported 16:9 at 1x/2x; output resize/fullscreen and Windows DPI changes. Test 3x before claiming 3x support. |
| Layout boundaries | Existing safe area and coordinate system preserved; no forced ultrawide or HDR changes. Document behavior on letterboxed outputs. |
| Localization | Long Latin labels, CJK fallback, missing translation, numeric formatting, clipping/ellipsis. |
| Navigation/input | Controller and keyboard, held accept/back, rapid open/close, modal nesting, SDK dialog interaction, reconnect, focus loss. |
| Lifecycle | Repeated scene reload, race/free-roam change, shutdown, failed registration, unsupported image, missing component, stale handle, duplicate ID. |
| Rendering | Pause/map/modal transparency, correct layering, HUD suppression, no new artifacts or stale texture references. |
| State | Host preference persistence/recovery, unchanged save format and progression behavior, normal exit and relaunch. |
| Cost | At least three matched control/candidate timing runs; UI CPU/GPU cost, whole-frame median/p95/p99, memory, and open/close latency. |

Provisional cost targets, to calibrate on the named reference machine after
UI-04: inactive extensions produce no steady per-frame guest calls or resource
allocations; the simple active example adds at most 0.5 ms p95 CPU time and no
more than 3% whole-frame p95/p99 regression outside measured run variance.
After warmup, 100 open/close cycles must leave no retained extension instances
or monotonically growing extension-owned resources. These are proposed
acceptance budgets, not measured results; agree a revised budget explicitly if
the baseline makes one inappropriate.

Record source/SDK/image and executable hashes, renderer pack/catalog hashes,
configuration, output size, locale, scenario, and actual loaded scene IDs.
Compare animation durations against wall time, not just frame count. Keep
captures and verbose tracing outside clean performance windows.

Follow [AGENTS.md](../AGENTS.md) for every installed-AppData gameplay run:
verify the profile exists and no game process is running, then use
`tools/launch-preview.ps1 -StateRoot <installed-preview-state>`.
Do not copy, reset, move, or overwrite that save to prepare a UI test. Existing
seed-copying automation must not be applied to this save. UI experiments must
not write progression; ordinary in-game autosave behavior still exists.

## Start here

Implement UI-01, UI-02, UI-03, and UI-04 in order. The first reviewable gameplay
checkpoint is the real pause-screen insertion, with before/after evidence and
an activation trace. Re-estimate the remaining work after that gate.

Then build UI-05 through UI-09 for the usable menu API, followed by the HUD and
settings example, qualification, and documentation.

Defer an external mod loader, hot reload, Lua/JavaScript bindings, visual
authoring editor, arbitrary custom shaders, and whole-UI replacement. Add each
only when an actual extension requires it. The foundation is complete when
feature code can safely change a supported original screen and add controls
that behave and render like they belong to the game.
