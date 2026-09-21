# PERF-03 texture reload attribution — 2026-09-21

Status: **deferred into PERF-10; no standalone texture-cache candidate.**

The fixed 1x open-world route used the installed AppData save and the existing
20–46.7-second measurement window. A default-off
`fh1_texture_reload_probe` correlated exact texture keys and dirty ranges with
shared-memory invalidations. The probe records the invalidating address range,
CPU/GPU source, affected base or mip range, requested bytes and scaled state.
`tools/summarize-fh1-texture-reloads.py` reproduces the ranking.

## Finding

The route recorded 3,569 base-only reload attempts requesting 2,157,186,624
bytes. No mip reload was observed. Of 3,542 correlated texture invalidations,
3,374 were caused by GPU writes and 168 by CPU writes. Every recurring large
target was therefore changing producer output rather than unchanged immutable
content evicted or spuriously dirtied by a neighboring write.

| Base observed in this run | Contract | Loads | Requested bytes | Cause |
| --- | --- | ---: | ---: | --- |
| `0x1C4E1000` | 1280×720 R10G10B10A2 | 335 | 1,262,387,200 | GPU producer |
| `0x1BDB1000` | 1280×720 R10G10B10A2 | 89 | 335,380,480 | GPU producer |
| `0x1C149000` | 1280×720 R10G10B10A2 | 89 | 335,380,480 | GPU producer |
| `0x1DE5D000` | 320×192 R10G10B10A2 | 339 | 83,312,640 | GPU producer |
| `0x136FB000` | 16×16×16 format 6 | 168 | 21,299,712 | CPU producer |

Addresses identify this capture only; the contract and producer generation are
the required identity. The sole recurring CPU-updated texture changes each time,
so retaining its previous conversion would be stale. Two successfully retired
full-screen GPU samples measured 11.3–14.1 microseconds for conversion and
7.2–8.2 microseconds for the copy. The clean uninstrumented window spent 32.568
ms total in texture-request CPU timing over 1,698 frames, or 0.019 ms/frame.
This is too small to justify a second cache or generation-hash path.

The measured opportunity is native-producer reimport. Sharing those changing
render targets through their consumers requires the producer/consumer lifetime,
format, history and fallback contract owned by PERF-10. Implementing it as an
immutable-content cache under PERF-03 would preserve stale output. PERF-03 is
therefore closed as a deferred dependency: its evidence selects PERF-10's first
subchain rather than creating overlapping cache machinery.

## Reproduction and validation

The probe run exited normally. The Release staged preview built successfully,
and the summarizer self-test passes:

```powershell
python tools/summarize-fh1-texture-reloads.py --self-test
python tools/summarize-fh1-texture-reloads.py `
  .local/native-renderer/performance/perf-03/reload-probe-1x/samples.log
```

Tested title revision was `10ac7d1a8abd154fd82faaa24008928caf278cec`;
the committed SDK probe is `3346eb268873e44c09e6a264b0159775ca594fea`.
The staged `rexgpu-fh1.dll` SHA256 was
`DC9EB37ED5782DAE6A7970AF401CB833075574820F89823D90C297D053271FFA`.
Rollback is `--fh1_texture_reload_probe=false`, its default. Raw evidence is
local under `.local/native-renderer/performance/perf-03/` because it contains
game-derived and machine-specific data.
