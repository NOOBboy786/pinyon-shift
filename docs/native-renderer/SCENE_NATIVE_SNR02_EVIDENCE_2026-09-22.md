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
