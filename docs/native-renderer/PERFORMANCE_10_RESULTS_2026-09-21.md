# PERF-10 post-processing chain inventory — 2026-09-21

Status: **simple native handoff rejected; no production behavior changed.**

The selected chain is the recurring 1280×720 R10G10B10A2 target at guest
address `0x1C4E1000` in the captured session. The address is diagnostic evidence,
not a persistent identity. A default-off SDK probe correlated successful resolve
destinations with the shader pair active when the texture cache reimported each
destination. The fixed 1x open-world route produced 1,228 consecutive complete
chain frames (source frames 2,651–3,878) and exited normally.

## Observed lifetime

The target is a temporal, partially updated surface rather than a single
producer followed by a single consumer:

1. `D34A83D9E6B3A399/E9CD565D9C61D037` reads the previous contents, normally
   twice per frame.
2. A 1,310,720-byte resolve updates 1,280×256 pixels every frame.
3. The same shader pair reads the mixed old/new contents, and
   `2C53E1A563484076/E17BECBE8BE65806` performs the RMS downsample.
4. Every other frame, a 3,768,320-byte resolve publishes the complete padded
   1,280×736 backing surface. The visible texture remains 1,280×720.
5. `20A41D46F34D238E/614588022744BF6B` then consumes the full publication.

Nine uncommon reads used `972F0220C6D5A9A2/129FCB5D371AE0FC`, so even this
bounded route has an additional compatibility consumer. Across the complete
block, the selected address had 1,867 publications totaling 4,017,520,640 bytes
and 4,326 actual texture reload consumers. The median frame issued two
publications totaling 5,079,040 bytes and four reloads. Those reloads issued
4,326 conversion dispatches, 4,326 texture copies totaling 15,947,366,400
visible bytes, and 12,978 resource state changes (destination to copy, scratch
to source, destination back to shader read). PERF-03 measured the individual
full-screen conversion at 11.3–14.1 microseconds and its copy at 7.2–8.2
microseconds. At 3.52 reloads per frame, their measured GPU upper bound is
0.065–0.079 ms/frame; clean texture-request CPU cost was 0.01918 ms/frame.

The surrounding full-screen chain also uses `0x1DAC5000`, `0x1CE2D000`, and
alternating history destinations `0x1BDB1000`/`0x1C149000`. Their median
publication traffic in the same frames was 6,258,688, 7,536,640, and 1,884,160
bytes respectively. Several addresses are sampled under multiple guest formats,
which makes the shared-memory representation part of the compatibility contract.

## Decision

A direct latest-producer texture handoff is incorrect. It would replace the
required previous-frame read, lose pixels outside the 256-row partial update,
and bypass format aliases and the alternating history targets. A correct native
implementation needs a persistent 1,280×736 owner that applies ordered partial
and full publications while retaining exact guest-format views and a bridge for
every external reader. That is a new ownership system, not a safe removal of one
resolve/reimport pair, and the measured conversion cost does not justify adding
it without a new profile showing this chain on the critical path.

No resolve, reload, transition, gamma conversion, crop, or history behavior was
changed. The compatibility path remains authoritative at every scale.

## Evidence and reproduction

- SDK probe commit: `814959b`.
- Staged `rexgpu-fh1.dll` SHA-256:
  `6752A3956F871A5AD880B04B7394383DAEEF9EAC87636C104C273C77A1440E43`.
- Route: `config/render-tests/fh1-open-world-performance.fh1test`, symmetric 1x,
  AppData preview state, `--fh1_post_chain_probe=true`.
- Local evidence:
  `.local/native-renderer/performance/perf-10/chain-probe-2-1x/`.
- Summarizer: `python tools/summarize-fh1-texture-reloads.py <samples.log>`;
  its `--self-test` passes.
- Rollback/normal operation: `--fh1_post_chain_probe=false` (the default), or
  revert SDK commit `814959b` to remove instrumentation.

The probe route is diagnostic only: logging reached the archive cap, so its
frame timings are not an A/B performance result. It retained the complete
1,228-frame chain block used for the counts above.
