# SNR-02 title submodel and resource evidence

Status: in progress. This evidence identifies selected local-car submodels and
their prepared GPU resource census. It does not qualify a native scene, material
mapping, resource lifetime or draw suppression.

## Exact local-car GPU census

The [SNR-00/01 evidence log](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#local-car-title-buffers-join-exactly-to-prepared-draws-and-fetches)
establishes the profile-bearing player → `CCar` → `CCarPresentation` →
`CCarModel` chain. Its 49 view-8 title buffers join by exact packet header and
target to 108 backend executions and 268 prepared draws. The draw set contains
104 index-range/primitive tuples, 48 vertex-buffer layout tuples and 25 texture
payload tuples. The verifier command is:

```powershell
python tools/verify-snr01-player-presentation.py `
  .local/native-renderer/snr01/local-car-selection-run-a-full.log `
  --require-owner-calls --require-backend-join
```

These tuples are a bounded starting set. GPU fetch state does not identify
title material roles or distinguish allocation and payload generations.

## Selected `CCarSubModel` records

Generated `sub_82439960` calls `sub_824385D8` with its third entry argument as
the selector. The returned record has a pointer at offset 356 that the title
reads before building draw state. A read-only hook at return `0x82439990`
records that pointer and 32 bytes of its inline data. The verified base image
SHA-256 is
`6014727FA7B0B79727FD5F32A2E2377533DC8E29679E8D2462BD764D331FA305`.
For observed record vtable `0x8223FDD0`, it resolves complete-object locator
`0x8235E00C` and type descriptor `0x832B40F0` to `CCarSubModel`.

The saved sustained-race replay exited normally with seven captures. Executable
SHA-256 was
`CFA582FE0A77D185A4ED5CAE5630CCE9537DB5B7C96A6690DF01E710E977B0BD`.
The isolated source-frame-6000 log at
`.local/native-renderer/snr02/local-car-model-tags-run-a.log` has SHA-256
`4856D898A8B6850F8380C17E03DCF7BDDD85453C037B28D3060043A31D21E279`.
`tools/verify-snr01-player-presentation.py --require-model-records` passes on
that log.

| Selector | Title inline name | Direct model calls | Selected records |
| ---: | --- | ---: | ---: |
| 0 | `winga` | 2 | 1 |
| 7 | `exhaustRa` | 2 | 1 |
| 10 | `bumperRa` | 7 | 1 |
| 17 | `mirrorR` | 3 | 1 |
| 18 | `mirrorL` | 3 | 1 |
| 33 | `headlightL` | 6 | 1 |
| 34 | `headlightR` | 6 | 1 |

All 29 direct model calls selected one of these seven stable record and inline
name pointers. The other two local model calls entered `sub_82419A30` and
emitted four scene buffers each; they do not pass through this record lookup.
The names identify title submodel slots, not draw material roles. Some selectors
share shader pairs while using disjoint index ranges; shader identity cannot
replace the title record. The selected record goes into `sub_824399F8` for
transform preparation; geometry and material ownership still need a separate
join before SNR-02 can close.

## Submodel to prepared-draw partition

The same replay's full timestamp-ordered diagnostic log is at
`.local/native-renderer/snr02/local-car-model-tags-run-a-full.log` (SHA-256
`ECE23DC261192D72BD55CE768A2B112B61AD2AC907205CD730A75586C072EFCB`).
Run the verifier with both `--require-model-records` and
`--require-backend-join` to check the selected record, scene packet, backend
execution and prepared-draw chain in one capture.

| Title path | Scene buffers | Backend executions | Prepared draws | Distinct index tuples |
| --- | ---: | ---: | ---: | ---: |
| `winga` | 2 | 4 | 4 | 2 |
| `exhaustRa` | 2 | 4 | 4 | 2 |
| `bumperRa` | 7 | 14 | 14 | 7 |
| `mirrorR` | 3 | 6 | 6 | 3 |
| `mirrorL` | 3 | 6 | 6 | 3 |
| `headlightL` | 6 | 17 | 19 | 6 |
| `headlightR` | 6 | 17 | 19 | 6 |
| Separate `sub_82419A30` list path | 8 | 16 | 40 | 5 |

These 112 model draws partition by exact caller and selector: 72 arise from
the seven named `CCarSubModel` records and 40 from the separate list path.
The latter reuses selector value 0, so grouping by selector alone would
incorrectly label those 40 draws as `winga`. The local presentation accounts
for the other 156 draws in the 268-draw car census. This is draw provenance,
not proof that each backend execution is a distinct visible car part.

## Static path after submodel selection

The generated title code makes a useful boundary explicit. `sub_824399F8`
reads the selected record's byte at +352 and its binding pointer at +356. It
copies a 64-byte matrix from either the model at +800 or the binding at +176,
optionally composes the record's matrix at +288, and calls `sub_82435F50` to
publish transform state. It does not read a mesh or material pointer from the
record. Back in `sub_82439960`, the title loads the model field at +32860
and passes it as argument 5 to `sub_824167F8`. The latter emits the child
scene-list packets, which already join exactly to the 72 prepared draws above.

The separate `sub_82419A30` path instead iterates four model slots at
`model + (3188 + slot) * 4`; it reaches the same scene-list flush but never
selects a `CCarSubModel` record. A record name alone cannot serve as resource
provenance.

An instrumented replay exited normally with seven captures (executable SHA-256
`F27A3F0A5DA31A1F0B81A789ED90E21CE4A2F1D1D1427C3EC4AC0E48CA5C8195`).
Its full bounded log at `.local/native-renderer/snr02/model-inputs-run-a-full.log`
has SHA-256
`B263A4D20A830FC29533B3B32305C230449A6919C61A9DA901E403562FCA1753`.
All 31 local model calls read **1** at `model + 32860`, and all 37 scene-list
flushes received that same value as argument 5. It is not a geometry-list
pointer. All four sampled model slots held the same nonzero source pointer in
every call. The 37 flushes emitted 37 distinct transient list objects.
`tools/verify-snr01-player-presentation.py --require-model-records
--require-backend-join` checks these joins along with the 268-draw census.
Next, follow the renderer state queues used by `sub_824167F8` and relate
their entries to each packet's final geometry and material resources.

## Command-buffer node ownership

`sub_82416A00` reads its command-list object's linked-node head at +116.
For each node it reads a count at +4 and packet pairs from the node's
8-byte entries before writing a child indirect packet at `0x82416F18`.
An extended read-only packet hook captured the node and entry index during
another normal-exit, seven-capture saved-race replay (executable SHA-256
`8736F0EF656CE9594A41EA8FBAF3EA5EF6BD14B319B2E38990F9B69E3E168E06`).
The bounded log is `.local/native-renderer/snr02/model-node-run-a-full.log`
(SHA-256 `442B86F2E2BA2CEDFC651E92380F39DE665CC033E4F4ECE2105C93953B2EB72A`).

Every one of the local car's 49 packets used a distinct node exactly
184 bytes after its distinct command-list object; every node had count 1
and emitted entry 1. That partitions into 37 model and 12 presentation
packets. The same verifier command above checks this capture and its
268 prepared draws. These nodes are transient per-submission containers,
not a reusable mesh identity or resource lifetime key. The resource owner
must be found before this command-list packaging step.

## Title model descriptor to draw provenance

The two direct-model call sites in `sub_82437600` and the third in
`sub_8245AA98` read the model selector and command-list pointer from a
12-byte entry in a vector rooted at `CCarPresentation + 6044`. Both paths
pass those fields directly to `sub_82439960`. Read-only hooks immediately
before the three calls captured the vector header, entry and fields. The
normal-exit, seven-capture replay used executable SHA-256
`13DE77BC8E502F7687CA5F89FC3727CD05BA30B25DFD77E43B377C66438F8F4A`;
`.local/native-renderer/snr02/model-descriptor-run-a-full.log` has SHA-256
`2C328AA8D5EED843BF161356632E97C8282A6239794CB9C301A90794E0F38050`.

All 29 local direct-model calls joined one-to-one to distinct live title
descriptor entries. Twenty-seven entries came from table header 1799 and
two from header 1913; every entry lay within its header's begin/end range
on the 12-byte stride. Its selector matched the selected `CCarSubModel`, and
its command-list pointer matched the corresponding title packet's list
object. The existing packet-to-backend join then accounts for all 72 draws
from these descriptors. The separate two-call, 40-draw model path does not
use this descriptor loop. `--require-model-records --require-backend-join`
now verifies the full descriptor-to-draw chain when these records are present.

These descriptors provide an exact title submission identity for the direct
model path. They still do not identify the mesh/material allocation or
freshness behind each prepared draw. The next ownership trace must follow
who populates the command-list descriptor and its child PM4 buffer, while
keeping the separate path distinct.

## Presentation table owner

A further read-only replay dereferenced the first word at the presentation
table root and the first word of each selected command list. The seven-capture
saved-race route exited normally with executable SHA-256
`E64184AD9AF538A89B88D620227ECFB562F7183A290C3FF37E3D849D0A1F461F`;
`.local/native-renderer/snr02/table-owner-run-a-full.log` has SHA-256
`53D301CF1D89729E3B09ED8EDECCD470E9E85444984E391DB94D67BF40279A7C`.
The existing verifier passed its model-record and backend-join requirements.

For all 29 local direct-model descriptors, the table root's first word points
to a live object whose first word is vtable `0x8200373C`. The image's RTTI
locator `0x8235A9DC` resolves through type descriptor `0x832B036C` to
`TRefCountedObjectThreadSafe<CPresentation>`. The selected command lists begin
with scalar `0x00500009`, not a vtable. This identifies a presentation
reference holder at the table root and confirms that the lists are submission
containers. Neither word identifies a persistent mesh or material owner.

The title lookup `sub_8243CCF0` indexes the table by its three selection
arguments (with the third clamped to 0..5) and returns a list pointer or null;
`sub_8243CDC0` flushes a non-null result. This explains why a direct-model
selector can have no packet, but it does not establish who creates the list
or its geometry payload. The next trace must follow that producer and join
its resource lifetime to the prepared draw.

## Static car asset and material binding lead

`tools/discover-native-renderer-vehicle-asset-material.py` passed against
`.local/derived-source/generated/default` and the verified base image. Its
local output at `.local/native-renderer/snr02/vehicle-asset-material-static.json`
has SHA-256
`199FE0E219BBED156DF7B8FE4A6E7F2C1C520DF7EA130B0488EA383F1326B426`.
The image RTTI distinguishes `CCarMaterialSettingsResourceType`,
`CCarModelResourceType`, `CCarMaterialSettingsResource` and
`CCarModelResource`; the audit checks their vtables against generated functions.

The title's path builder `sub_82543558` uses the `Tire` shader-settings paths,
including UI, normal and SLOD variants, and a `Wheels` asset path. Car resource
construction in `sub_824D11B0` calls material binding `sub_82549670` twice
with its embedded binding object at offset 1056. This proves a title-owned
tire/wheel material *family* and supplies a precise runtime probe boundary:
record the root, binding object, load-UI/SLOD flags and asset-key identity at
`0x82549670`, then follow later resolution to a selected title draw and
its backend geometry. The static audit alone does not prove which selected
local-car draw uses that binding, any other material role, geometry ownership
or resource freshness. No native admission follows from it.

### Runtime binding observations

A default-off, 512-record-capped hook at `0x82549674` ran the saved sustained
race to normal exit with seven captures. Executable SHA-256 was
`190190F83B5CAD5C85F0ED10234D9AB12ED0F585B2D5FDB998D71DBB387B5307`;
the ordered diagnostic log at
`.local/native-renderer/snr02/material-binding-run-a-full.log` has SHA-256
`FDBE5D7ED1A2AE375D5670A22C7F94A2A162C24544C5A52D170A1BD2B0CE4E48`.
The local-car model/backend verifier and camera/view verifier both pass on
this replay; the former again finds 49 buffers and 268 prepared draws.

The hook observed 32 calls between source frames 1449 and 4092. Every call
returned to `0x824D2EE0` within the car-resource construction path, used
binding offset 1056, and passed zero for both load-UI and SLOD flags. The
root address is sometimes reused, while its first word changes; it must not
be treated as a stable resource identity or vtable. Generated
`sub_82543558` reads the asset-key string at root offset 1712 and its capacity
at offset 1732 before appending that key to the tire settings path. Further
inspection of generated `sub_82549670` shows that it passes the resulting
temporary string to `sub_82480FC0`, which moves/copies it into the binding
object. This hook therefore proves path setup, not material-object creation
or resource generation. A later trace must follow resolution from the binding
string to the selected draw. These 32 loading-time records do not yet
establish that any specific local-player draw uses this family.

## Selected car transform input

Generated `sub_824399F8` starts with the `CCarSubModel` record in `r6`.
It copies a 64-byte matrix from either model offset 800 or binding offset
176, depending on the binding flag at offset 28. When record byte 352 is
set, it composes the record matrix at offset 288 into that copy. The call at
`0x82439B54` passes the resulting stack matrix to `sub_82435F50`, which
continues writing title render state. Thus this is an authoritative *input*
to title preparation, not a proved final GPU transform.

A default-off, 512-record-capped read-only pair of hooks at `0x824399F8`
and `0x82439B54` records the selected record, title owner call, 16 exact
matrix words, render-state pointer and flag. The corrected preview executable
SHA-256 was `B037815627439E43AB1A76F98EBF34D3BAB84AEBDB50AE3170D666897C2E646F`.
The seven-capture saved-race replay exited normally; its ordered diagnostic
log at `.local/native-renderer/snr02/matrix-input-run-a-full.log` has SHA-256
`FC087E0B911EC77535DB17710BFFA5C1AA6167BE26D03900295990BFC57B32C2`.
The verifier's model-record, matrix-input and backend-join requirements pass
for source frame 6000.

All 29 selected direct-model calls still join their title descriptors and
records. Twelve call the later matrix-consuming routine and each captured
matrix matches its selected record. Seventeen do not make that call; static
control flow skips it when both the binding and record composition flags are
clear. This replay has 49 local-car command buffers and 268 prepared draws,
including calls without a new matrix input. The trace therefore does not
yet explain the carried render state for those calls or identify the final
matrix at draw time. The number of view-8 presentations also varied from
the earlier capture (four here); the verifier now requires the local
presentation's view-8 ownership rather than assuming all eight car
presentations share it.

The next bounded trace must observe title state after `sub_82435F50` and
associate its matrix with each draw, including calls that reuse state. This
still leaves actual mesh/material identity and resource generations open
before an immutable scene can be admitted.

## Selected track-model instance version

The shared-state draw join in the [SNR-01 evidence](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#both-shared-state-callers-reach-selected-track-model-resources)
identifies a `CTrackRenderModelInstance_Unified` at each selected resource
pointer. Generated `sub_82DEB718` compares the instance's cached low 16 bits
at offset 12 with the parent `CTrackRenderModel_Unified` high 16 bits at
offset 12. Generated `sub_82DEB748` copies that parent version into the
instance; `sub_82DEB7B0` also sets the instance's `0x800` flag while copying
the version. These fields give a bounded readiness/version check, not an
allocation generation.

A default-off probe of both selected shared-state callers captured the
instance, its parent at offset 4, the cached and parent version words, and
the runtime pointer at offset 16. The RelWithDebInfo executable SHA-256 was
`B7AAE85D030B1F0B601EB7A979937ACFAEF7E5BE00C5F692EE342FE2AE49FD48`.
The saved sustained-race route exited normally with seven compatibility
captures. The process-filtered log at
`.local/native-renderer/snr02/track-version-run-a-filtered.log` has SHA-256
`03647848A6B9CF3EB39BEDB3D75D7A74C4101BD09FC59A344EA8E0C75FDBB86E`;
its source-frame-6000 census ledger has SHA-256
`4D445AB3332B5E8DE01D6848C2C03B272116A2B99EB1C7FFACC5063C2BF3B8B7`.
The strict frame-wide census and state/resource/draw verifier passed.

The verifier joins all 164 selected view-8 shared-state packets to all 758
candidate draws. The procedural-model caller contributes 45 packets, three
resource pointers and 128 draws, all with cached version 1. The track-model
caller contributes 119 packets, 113 resource pointers and 630 draws: 606
with cached version 1 and 24 with version 9. Across the complete probe
records for the source frame, all 283 calls have instance vtable
`0x820019CC`, parent vtable `0x82001D74`, nonzero parent and runtime pointers,
ready result 1, and cached version equal to the parent's current version.
The instance flag's high 16 bits are `0x800` in those records.

This proves version parity at the selected call boundaries in this replay.
The next SNR-02 trace must identify the parent/runtime object's mesh and
material choice at the resulting draw, and establish a true generation or
allocation lifetime across release and reload. Until then, pointer plus
cached version is a diagnostic identity only, not an immutable-scene key.

## Track-model descriptor selection reaches selected draws

Generated `sub_824365B0` reads the selected instance's parent at offset 4,
then the parent's model root at offset 48. Its container is model root +128.
After a nonzero halfword check at container +8, it calculates the table index
as `selector_a * 3 + selector_b`, reads the descriptor pointer from the table
at container +40, and passes that pointer to `sub_82439868`. The latter
writes it to the render-state object at offset 1200. The halfword is only a
nonzero gate: it was 1 on all 312 observed calls while indices reached 18,
so it is not the table length.

A default-off hook at `0x8243669C`, immediately after that state write, logs
the parent, model root, table, selectors, index, descriptor and state field
for the selected source frame. The first RelWithDebInfo capture used executable
SHA-256 `819DBE39AF136AC0556DBD87A5126048E2B3AC292172FA66CDE98B9AB893A05E`
and the saved sustained-race route exited normally with seven compatibility
captures. The process-filtered log at
`.local/native-renderer/snr02/track-descriptor-run-a-filtered.log` has SHA-256
`71566B1A275D67BCB93D2482960ED1D74CC0C1B9D780762A38D9D04C49C3F801`;
its strict frame-wide ledger has SHA-256
`CBE3AAAE40E50EA5642D37E29B770CF507FAE7BFF34E4ECDE3B96B751205C729`.
The log calls the nonzero gate `count`; the hook now names it `gate_word8`
after the observed indices disproved the count interpretation. The verifier
accepts both field names and the corrected source builds with executable
SHA-256 `A1B775FAF18FD64D7BDDB3077315BF4DDA1C5FA96996A70478FF2D9D3DE3ACAF`.

For source frame 6000, the strict frame-wide census and the
`--require-track-descriptor` resource join pass. All 312 track-descriptor
events match the parent at the ready check, the calculated selector index,
the parent-root/container relationship and the state field. The 119 selected
track packets carry 86 distinct descriptor pointers and join all 580 track
candidate draws (550 on color `00030000`, 30 on `000C0000`). The other 46
shared-state packets and 138 candidate draws use the procedural-model caller;
this descriptor hook does not cover that caller.

This establishes a title-owned selected descriptor *pointer* for this track
caller and its exact packet/draw join. It does not yet identify the
descriptor's mesh ranges, material/texture roles, transform or resource
generation. The next trace must follow the descriptor through its submission
routine to authoritative geometry and material objects, and independently
resolve the procedural-model caller.

### Descriptor is a command-list container

The static consumer corrects the next-hop interpretation. At flush,
`sub_82417060` reads state offset 1200, loads word 0 from that selected
record and passes it to `sub_824167F8`. A source-frame-only extension of the
descriptor probe captured its first eight words. The RelWithDebInfo executable
SHA-256 was `0E794DA8594509CE045A9EA134141307C4BCD7208C921C43AD9A5046BFD31DE2`.
The saved sustained-race route exited normally with seven compatibility
captures. The process-filtered log at
`.local/native-renderer/snr02/track-descriptor-words-run-a-filtered.log`
has SHA-256
`3D9AA9DBBCF927B3E95D636588CE83496B9BD2F92B8C6C0D02AA708075DCFCC3`;
its strict source-frame-6000 ledger has SHA-256
`D766EEC4098D06C3BDA1FE08BC84066F3E563B39C4AD66276E4B011C0F2E66C8`.

The frame-wide census and
`verify-snr01-state-resource-join.py --require-track-descriptor-words`
pass. All 120 selected track packets have `descriptor.word4 & 0x1fffffff`
equal to the packet's physical command-buffer target; those packets join all
595 track candidate draws. They use 87 distinct selected descriptor pointers
from 114 resource pointers. Across all 258 observed track-descriptor calls,
word 0 equals word 3, words 1 and 5 are zero, and words 0, 2 and 4 are
nonzero. These are observed layout facts, not field type declarations.

The selected pointer is therefore a command-list container in this path,
not an authoritative mesh/material identity. The next SNR-02 step must trace
the nested traversal's geometry/material objects and command-list producer
to the backend fetches and shaders. Treating this descriptor address as a
mesh key would confuse submission storage with the underlying resource.

### Cached track command list and nested rebuild path

Generated `sub_824365B0` turns the selected index into a bit mask and checks
it against flags at the parent object +56. A set bit skips the nested
`CTrackModel` traversal. A sparse default-off gate probe found cache misses
in 21 pre-target 128-frame buckets on the saved sustained race. At source
frame 6000, all 324 observed gates were set. At source frame 6001, two of
324 calls missed; those two calls reached four selected 56-byte records and
one selected view-8 scene packet. Both used the same track-model instance.

The source-frame-6001 runtime vtables are `0x820016B4`, `0x82001474` and
`0x8200143C`, which the verified title-image RTTI identifies as
`CTrackModel`, `CTrackSubModel` and `CTrackMesh`. The generated virtual
dispatches support that traversal: `CTrackModel` slot 2 returns its count
and slot 4 selects a submodel; `CTrackSubModel` slot 3 returns its pointer
range count and slot 5 selects a mesh; `CTrackMesh` slot 5 runs the
selection check at `sub_82437058`. For all four observed record events,
`record = record_base + 56 * CTrackMesh.entry_index`. The bounded
`verify-snr02-track-rebuild.py` checks the earlier parent/flag address,
runtime types, nested call order, record formula and packet scope.
For the rebuilding call that emitted a packet, it also checks that the
selected descriptor's word-4 command target is that packet's target.

The scout used RelWithDebInfo executable SHA-256
`02E048746B6EB647120F33E16E1C8EBE2609E49EBC8199D1C1CE64F248307496`
and exited normally with seven compatibility captures. Its process-filtered
log at `.local/native-renderer/snr02/track-gate-scout-run-a-filtered.log`
has SHA-256
`E1C81034F1ED74FFCF1D6E1BC2BF2CA413323CE9132592D9A6F11ACAF48FFA21`.
The first log labeled the later `r30` value `instance`; generated code has
already changed that register to `parent + 56`, so the hook now calls it
`flags_address` and the verifier accepts both labels while checking the
actual relationship.

A second normal saved-race replay traced frame 6001 as the primary frame,
but all 369 track gates there were cached and the nested traversal did not
run. Its process-filtered log has SHA-256
`C9DB68E9471C0CFA308F891D11DB41EE7ECF1F98B80D48EE06EB8B09CBD64335`;
its strict frame-wide ledger has SHA-256
`6A42A22208047B09B3EAD0A4B418552EEEE7D9FB62ABFAF97ED49775B89A91E0`.
The frame-wide census and command-target join passed for source frame 6001:
164 shared-state packets joined 762 candidate draws, including 119 track
packets and 627 track draws. This replay does not join a rebuilding record
to backend draws, because no rebuild occurred in its traced frame.

The title-side graph now reaches a selected `CTrackMesh` and its 56-byte
record, but the record's geometry/material fields and allocation lifetime
remain unresolved. Rebuild timing varies across replays; the next capture
must trigger on an actual cache miss and retain that source frame through
backend consumption, rather than relying on a fixed source-frame number.

### Event-triggered rebuild reaches backend execution

The default-off `--pinyon_shift_snr02_trace_first_rebuild_after_frame=4800`
probe captures the first track cache miss after that source frame, preserving
its selected descriptor and physical command target. It records selected
`CTrackMesh` records, the title's flush of that exact target and the backend
indirect execution, indexed draws and fetches in the following frame. The
bounded verifier is:

```powershell
python tools/verify-snr02-rebuild-execution.py `
  .local/native-renderer/snr02/track-event-trigger-run-b-filtered.log
```

Two saved sustained-race replays exited normally with seven compatibility
captures each. Run A's process-filtered log has SHA-256
`8209277A7C555DEE29D1D23EF00180C02E2DAA0D4F6A7FD82F6EA079B6921554`.
Its source frame 5017 had a cache miss, four selected record visits and one
flush of command target `0x172593C0`. Backend frame 5018 executed that target
once, preparing two indexed draws with one vertex fetch each. The second
replay used executable SHA-256
`253B1B16E75810ECAFDCE43E9B2B094AFC7C1D5443674E1986D35B248D036970`;
its filtered log has SHA-256
`A83E67AFB988A14BC229BE19FEB7610AF527C99B404075F05510A6BB9B7EEAFB`.
Its source frame 4919 had 18 selected record visits and six flushes of
`0x17499CA0`; backend frame 4920 executed that target six times, preparing
36 indexed draws, 36 vertex fetches and six texture fetches. The records
include repeated visits to the same mesh records within the source frame,
not 18 distinct meshes. Every prepared draw had normalized color mask zero;
the six textured draws had a pixel shader, but still wrote no color. This
captured command list is a depth-only submission, so it does not yet prove a
main-view scene-color material or complete the selected slice.

This establishes a reproducible title `CTrackMesh` record → command-list
flush → backend geometry/fetch chain despite variable rebuild timing. It also
shows why the next capture must select a color-writing view-8 submission.

### View-8 color-writing track contribution

The event probe can now track the presentation view-call ordinal and restrict
capture with `--pinyon_shift_snr02_trace_view_call=8`. A saved sustained-race
replay with the frame threshold at 4800 exited normally with seven compatibility
captures. The RelWithDebInfo executable SHA-256 was
`177182D1F7CC4F2A2F78C990DF9A7FF940A192945088150DA87B104C990621A0`;
the process-filtered log at
`.local/native-renderer/snr02/track-view8-event-run-a-filtered.log` has
SHA-256
`7E17107376F237C11A6032EE4CADCAFB2E59BD612CCB87BCAE2D0D46C53F5347`.
Its title-to-backend chain passes:

```powershell
python tools/verify-snr02-rebuild-execution.py `
  .local/native-renderer/snr02/track-view8-event-run-a-filtered.log `
  --view-call 8 --require-color
```

Source frame 4834 missed the track cache for the selected bit at parent
`0xAAFDF660`, traversed a `CTrackModel` → `CTrackSubModel` → `CTrackMesh`
entry and selected its 56-byte record at `0x2E8F8B80`. The title flushed
descriptor `0x2EB99800` to physical command target `0x17577E60`. Backend
frame 4835 executed that same target and prepared one 2,060-index draw with
one vertex fetch (guest base `0x11C64580`, 39,552 bytes) and three texture
fetches at constants 0, 5 and 13. It has a nonzero pixel shader, normalized
color mask 7 and color attachment `00030000`, one of the two candidate
scene-color groups. The indexed buffer starts at guest `0x11C63560` and is
4,120 bytes. This is a concrete color-writing main-view track contribution,
not a semantic material map: the selected record's fields, texture roles,
transform and allocation/payload generations remain to be established.

### The selected record is a control path, not yet a material key

Generated `sub_824365B0` first tests the selected bit at `parent + 56`.
For a selected 56-byte record, its word 0 can index the table at the traversal
object +16 and pass that entry's field +60 to `sub_82C24168`, but the bit at
`flags_address + 8` can skip the lookup. Independently, record words 10–11
bound a four-byte control range, capped by the title at 20 entries; the bit
at `flags_address + 16` can skip that range. The path passes the selected
`CTrackMesh` to `sub_82450440`, but that callee does not read its mesh
argument; it updates shared command state from the selected descriptor and
control flags. The title then flushes the command list. These are observed
control relationships, not decoded geometry or material roles.

A bounded view-8 replay exited normally with seven compatibility captures.
Its RelWithDebInfo executable SHA-256 was
`A082202D58B7CE16CCD7ECB00C7ACFA3FBF9C91ADBA5CD5CCF16CB01D642B09D`;
the process-filtered log at
`.local/native-renderer/snr02/track-record-flags-view8-run-a-filtered.log`
has SHA-256
`D32FC3CF2D898C5E8FA320C3BA383A6A88FF33AF469F545CBFD41153AB98523E`.
It passes:

```powershell
python tools/verify-snr02-rebuild-execution.py `
  .local/native-renderer/snr02/track-record-flags-view8-run-a-filtered.log `
  --view-call 8 --require-color --require-record-control
```

Source frame 4830 selected one track record with a valid word-0 index, but
`resource_skip_flag=true`: the resource-table lookup did not run in this
call. `range_skip_flag=false`, and its six control words were
`[0, -2, -2, -2, -2, 1]`; the `-2` values take a distinct control branch,
not a resource-pointer dereference. The title flushed `0x17577E60`, and
backend frame 4831 used it for the same color-writing, three-texture-fetch
draw family as the prior replay. The cached resource path means this capture
does **not** establish material ownership or freshness. An exploratory probe
that dereferenced the mesh's raw +140 word crashed; the final probe records
that word without dereferencing it. The next lookup must follow the title's
actual producer and resource-allocation paths, including the earlier point
that populated the cached command list.

### Selected command-list header and backend length

Generated `sub_82439868` stores the selected descriptor pointer at state
offset 1200. `sub_82450440` tests its word 0 but does not consume the
`CTrackMesh` argument. At flush, `sub_82417060` reads descriptor word 0 and
passes it to `sub_824167F8` for submission. A new event-triggered header
capture checks this layout against the same view-8 color draw.

The sustained-race replay exited normally with seven compatibility captures.
Its RelWithDebInfo executable SHA-256 was
`29CBBCDA620CF901206E4BF671B3BBD959B2103C8D425E62308BBECE928EDA0C`;
the process-filtered log at
`.local/native-renderer/snr02/track-descriptor-header-view8-run-a-filtered.log`
has SHA-256
`E683ABF504ABA5B5406178E5F26D5CE8B87894AE61410411160A5D8A75B16910`.
The bounded check is:

```powershell
python tools/verify-snr02-rebuild-execution.py `
  .local/native-renderer/snr02/track-descriptor-header-view8-run-a-filtered.log `
  --view-call 8 --require-color --require-record-control `
  --require-descriptor-header
```

At source frame 4806, the selected descriptor had words
`[0xAC991808, 0, 0xABA251AC, 0xAC991808, 0xB7577E60, 0, 352, 1124]`.
Word 2 equals the selected `CTrackModel` container +44; words 0 and 3 are
equal; word 4 masks to the physical target `0x17577E60`. The next backend
frame executed that target with `command_bytes=1116`, eight fewer than
descriptor word 7, and prepared the same color-writing 2,060-index draw.
This validates a command-list header and owner link for one selected
contribution. It does not identify word 0's allocation owner, establish when
the list was built or map material/texture roles. The next trace should
follow the table entry that supplied this descriptor back to its constructor
and stream/resource generation events.

### Car-presentation scalar resource references

The [frame-wide scalar join](SCENE_NATIVE_SNR00_01_EVIDENCE_2026-09-22.md#car-presentation-scalar-packets-cross-both-candidate-color-groups)
identifies three title packets per `CCarPresentation + 2016` subobject:
two depth-only packets followed by a color-writing packet. Generated
`sub_82443600` reads pointers at subobject offsets `+4` and `+12`. Before
the color packet it checks `+16` and passes that reference to
`sub_824AFB20` when nonzero; otherwise it passes the `+12` reference.
This branch means the `+12` object alone does not prove the selected color
texture in every car.

A default-off scalar trace now snapshots those three pointer fields and
their first words at the three known call sites. The bounded checker
`--require-car-scalar-resources` joins the snapshots to prepared draws,
resolves first-word RTTI against the title image, and requires a stable
three-site packet group per observed subobject. Two saved-race replays with
the final probe exited normally and each produced seven compatibility
captures. Both passed the strict frame-wide census with this additional
check:

| Replay | Prepared draws | Joined car draws | Car subobjects | Filtered log SHA-256 | Ledger SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| `car-scalar-field16-run-a` | 3,426 | 9 | 1 | `DF8769C228A36B733C47F8837BD0C43C4AE5E8B10A3264A1E5E46A00A4A5A09A` | `0CF9EC0C53E92183A6D535EBA4085E4F206642C2E23C05250294426C10CAF1B6` |
| `car-scalar-field16-run-b` | 3,352 | 9 | 1 | `332E7F9AB5289A0D3E11C8C67F3EB6469C5D94E0AEDC6C42C4F65051FFFA3EBA` | `BCC9D794A1C338CF1AE844AAAFCA768F3F6BC252CA5688E5C1F7D626AB118394` |

The RelWithDebInfo executable SHA-256 was
`5A25D18068FB59177E1DCA4275486466EDEB2A360E8EB44FC086B6424DFDD583`.
For each observed triple, `+4` resolves to `CFXLShaderResource` and `+12`
to `CTextureResource`; `+16` was zero, so the color path selected `+12`.
The three pointers were stable across repeated prepared executions of each
packet. An earlier probe without `+16` covered six car subobjects and found
the same `+4`/`+12` classes, but cannot establish their color selection.
The selected-reference helper `sub_824AFB20` clears a destination slot,
calls the resource object's virtual slot `+8`, then stores the pointer.
For both observed resource vtables that slot targets `sub_824493C0`, which
atomically increments the object's counter at `+32`; virtual slot `+12`
targets `sub_82448FD8`, which decrements it and destroys on zero. This is
title-side reference ownership, not a proven GPU submission fence or
payload-generation rule.
Object class and pointer identity still do not prove actual GPU payload,
semantic texture role, generation, or submission lifetime. These remain
SNR-02 blockers, and this evidence alone does not admit the car triple to
the native slice.

Rebuild either final ledger from its `.local/native-renderer/snr01` filtered
log, changing `run-a` to `run-b` for the second replay:

```powershell
python tools/summarize-snr01-frame-wide-census.py `
  .local/native-renderer/snr01/car-scalar-field16-run-a-filtered.log `
  --source-frame 6000 --require-direct-family `
  --require-direct-family-record --require-semantic-item-node `
  --require-second-path --require-scalar-draw `
  --require-animated-scalar --require-car-scalar-resources `
  --require-dynamic-quad --title-image .local/ui-verify/default-image.bin `
  --require-candidate-boundary `
  --output .local/native-renderer/snr01/car-scalar-field16-run-a-ledger.json
```

### Car color texture resolves to the prepared fetch descriptor

The observed command-device vtable `0x8200306C` sends virtual slot `+92` to
`sub_82444B18`. Called with the selected resource reference at color-pass
setup, this method follows its `+168` member, calls virtual slot `+20`,
and passes the returned descriptor and texture slot to `sub_82442528`.
That writer reads descriptor words at offsets `+28` through `+48` and
updates the title's fetch state. A default-off hook at `0x82444B68`
records the resource and those already-read words before the state update.

Two sustained-race replays with the final probe exited normally with seven
compatibility captures each. Their RelWithDebInfo executable SHA-256 was
`CC92F85820937887A6F8AF8E7BDD7210F29806E61F0EAC5BEF03EDB8FAB4A0F8`.
Both used `fh1-race-sustained.fh1test` with
`--pinyon_shift_fh1_gpu_corpus=true`,
`--pinyon_shift_fh1_clear_producer_trace=true`,
`--pinyon_shift_snr01_trace_source_frame=6000`, and
`--pinyon_shift_snr01_trace_following_frame=true`; the filtered logs came
from their process-scoped sessions through `extract-snr01-run-log.py`.
The strict frame-wide candidate-boundary census and
`--require-car-texture-descriptor` both passed:

| Replay | Prepared draws | Filtered log SHA-256 | Ledger SHA-256 |
| --- | ---: | --- | --- |
| `car-texture-descriptor-run-a` | 2,794 | `FA30D808CD2299CE5780EC2F426F2B190221B51262CDC310C71AFEA2956D91D4` | `FD79AD7F5B1C815A8437B6A7CB4CE1DAEAD9760869541EB2F750884CF34B77A3` |
| `car-texture-descriptor-run-b` | 3,313 | `26450160D08FCDC1D4BA863EE24BADB09EFCBD324430AC2297C7DB5B2E929F51` | `E98C58AF9DE8AE9F4A018C261092BD72549FC91015B9A3C8800A84BB36E883AA` |

Each replay had one captured car subobject. Its color packet executed three
times, each with exactly one slot-0 texture fetch. The source-frame
resolution event named the exact selected `CTextureResource` pointer and
the next direct packet ordinal. For run A, resource `0x2E09DB40`
resolved to `0x2F1AB0B0`; descriptor word `+32` was `0xB5768086` and the
prepared fetch base was `0x15768000`. For run B, resource `0x2E00B870`
resolved to `0x2EEDB150`; descriptor word `+32` was `0xB5981086` and the
prepared base was `0x15981000`. In both runs, the descriptor's `+32` word
masked by `0x1FFFF000` equals the prepared base,
its low six bits equal format 6, and its `+36` word decodes width and
height as 64 each (`low 13 bits + 1`, `bits 13–25 + 1`). The verifier also
requires an unchanged fetch descriptor across all three executions.

This establishes the bounded title resource → resolved descriptor →
prepared texture-fetch relationship for the observed car color packets.
It does not establish the resource's semantic role, when its texture bytes
were produced, their generation or a lifetime through a native GPU fence.
The depth-only packets have no shader-used texture fetch. A separate
exploratory replay omitted the clear-producer trace and therefore could
not pass the full candidate-boundary check; it was not used for this
boundary claim.

Rebuild either final ledger, changing `run-a` to `run-b` for the repeat:

```powershell
python tools/summarize-snr01-frame-wide-census.py `
  .local/native-renderer/snr02/car-texture-descriptor-run-a-filtered.log `
  --source-frame 6000 --require-direct-family `
  --require-direct-family-record --require-semantic-item-node `
  --require-second-path --require-scalar-draw `
  --require-animated-scalar --require-car-scalar-resources `
  --require-car-texture-descriptor --require-dynamic-quad `
  --title-image .local/ui-verify/default-image.bin `
  --require-candidate-boundary `
  --output .local/native-renderer/snr02/car-texture-descriptor-run-a-ledger.json
```
