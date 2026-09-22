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
replace the title record. Next, join each record to the geometry, material and
resource objects it passes into `sub_824399F8`, then prove lifetimes and the
separate list path before SNR-02 can close.
