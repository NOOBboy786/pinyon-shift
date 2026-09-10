# Manual discovery findings — 2026-09-08

Session `20260908T233942Z-p25372` exited normally after approximately 21.8 minutes
of CSV recording (79,507 rows). All six slowdown markers have screenshots.
Evidence lives in `.local/native-renderer/discovery/manual-20260908-2/`, including
`marker-triage.json`, the original markers, sampled logs and session CSV reference.
The renderer was instrumented; these observations locate reproductions rather
than establish an optimization's performance benefit.

## Marked locations and frame times

Locations below describe the screenshots, not confirmed map coordinates. Values
cover the eight seconds ending at each marker's latest observed CSV timestamp,
before that marker's screenshot capture. CSV flush/poll latency means the endpoint
precedes the hotkey; inspect the surrounding interval when reproducing.

| Marker | CSV time | Visible location | Median ms | p95 ms | Maximum ms |
| --- | ---: | --- | ---: | ---: | ---: |
| 1 | 70.1 s | Downtown street, tall corner building and storefronts | 22.44 | 57.43 | 98.12 |
| 2 | 355.4 s | Town residential intersection | 21.32 | 73.95 | 119.57 |
| 3 | 364.0 s | Horizon Outpost entrance, tent and crowd | 44.84 | 100.63 | 145.57 |
| 4 | 482.2 s | Town plaza/parking area, large buildings and blue awnings | 43.30 | 113.13 | 154.76 |
| 5 | 711.6 s | Divided highway, desert scenery and traffic | 29.24 | 58.67 | 118.48 |
| 6 | 847.4 s | Wooded junction with a Gladstone Canyon direction sign | 25.32 | 155.51 | 215.66 |

## Investigation order

1. **Outpost and plaza (3/4): sustained slowdown.** Their preceding windows have
   approximately 43–45 ms median frame times. Reproduce stationary views and camera
   turns, then compare scene preparation, GPU passes and resource activity with an
   adjacent fast view. Crowds/buildings are visible context, not established causes.
2. **Gladstone Canyon junction (6): severe frame-time spikes.** Start before the
   marked approach and follow the turn. A 215.66 ms frame precedes the marker's
   screenshot, so this spike cannot be attributed to that screenshot operation.
3. **Highway (5): a different workload.** High-speed travel and traffic broaden the
   evidence beyond town geometry. Investigate streaming/cache activity as a
   hypothesis; do not assume it shares the town slowdown's cause.
4. Keep 1/2 as additional urban comparison points.

The six preceding windows report zero command-buffer stalls and zero resolve
readback bytes, with only zero or one pipeline-cache miss per window. These
counters provide no evidence for a repeated pipeline-miss storm or logged CPU
readbacks in those windows. They do not exclude other synchronization, GPU copies,
resource residency or CPU work. GPU timing and frame timing differ, but those
overlapping/asynchronous measurements cannot be subtracted to identify CPU cost.

## Recording limitations and follow-up

The cumulative execution-key inventory reached its cap after the first usable
five-minute checkpoint. Later snapshots report overflow; the existing strict
ranking correctly rejects them. The report therefore retains an earlier ranking
of 289 shader pairs / 42,756 keys, not final whole-session coverage. Pass collisions
also make pass coverage incomplete. Frame CSV and all six markers remain useful.

Before another long session, preserve a separate bounded shader-family inventory
or otherwise prevent changing execution identities from exhausting discovery
coverage; clearly distinguish the latest snapshot from the last valid ranking.
Do not merely remove the overflow check or claim that the earlier ranking covers
later locations. Existing sampled timing logs can still be analyzed with the exact
session ID and selected source frames.

No renderer fix or root-cause attribution is claimed here. The next useful step is
a short matched reproduction of marker 3/4 or 6 with clean timing and targeted
diagnostics, using these screenshots as location references.

### Coverage-tooling follow-up completed

The recorder now maintains an independent bounded shader-pair map that continues
after detailed-key saturation, with explicit family overflow and latest-checkpoint
status. Production saturation checks and a live periodic-checkpoint smoke passed.
This session's report now labels the capped legacy snapshot as incomplete and
preserves its earlier ranking as `coverage-ranking-last-valid.json`; missing past
families cannot be reconstructed. Existing markers and frame-time data are intact.

## P2 cost triage: sampled spans (2026-09-09)

The existing session-isolated pass/texture rankers were applied to the eight
seconds preceding each marker's latest CSV time. Source-frame counter totals stay
within 0–1 of CSV row ordinal in this session; two rows were trimmed from the
selection boundaries before selecting GPU source frames. Association remains
approximate because CPU/GPU processing and logging are asynchronous. There are
only two to five sampled frames per window, not a matched benchmark.

| Marker | GPU source frames | Sum of observed pass spans, ms/frame | Observed preparation CPU, ms/frame | Texture conversion/copy, ms/frame |
| --- | --- | ---: | ---: | ---: |
| 1 | 6360, 6420, 6480, 6540 | 13.57 | 3.64 | 1.01 |
| 2 | 22080, 22140, 22200, 22260, 22320 | 14.24 | 4.67 | 1.15 |
| 3 | 22380, 22440 | 27.41 | 4.30 | 1.14 |
| 4 | 26400, 26460 | 14.45 | 5.25 | 1.22 |
| 5 | 37680, 37740, 37800, 37860 | 22.52 | 4.27 | 1.14 |
| 6 | 46320, 46380 | 13.37 | 3.77 | 1.14 |

Texture timings overlap pass spans: do not add the columns. These are measured
span subsets, not complete GPU frame time. CSV native GPU timing drops are zero
in the selected windows, which does not prove all work or every hitch was sampled.
The capped corpus still maps most first-draw identities; unknown mappings remain
null in the JSON instead of borrowing an unrelated shader identity.

### Outliers change the next investigation

- At Outpost source frame **22380**, family `07108CCA78F7D62F` spans **22.590 ms**
  across 753 draws (0.445 ms recorded preparation CPU). Its first pair is
  `41138347EF20F84C/5246C7C219B57DDB`, which does not identify every draw in the span.
  Across all 15 observed occurrences of this family in the session, the median
  span is **0.590 ms**, and the second largest is **1.493 ms**. Workload draw counts
  vary, so those occurrences are not controlled before/after comparisons.
- At highway source frame **37800**, family `60E03C6C350D8476` spans **19.170 ms**
  for one draw, starting with `1E6883FCCDE1F688` and no pixel shader. Across 752
  observed occurrences, its median is **0.111 ms**, and the second largest is
  **0.200 ms**. The neighboring three samples in marker 5 are around 0.111 ms.
- Consequently, the large window averages are not evidence that these shader
  families consistently cost 11 ms or 5 ms. Timestamp spans can include queue
  starvation, residency/scheduling delays or preceding work, not just shader
  execution. These are hypotheses requiring a targeted trace.

Before a visual simplification, reproduce one of these intervals and correlate
CPU submission timing, GPU scheduling/residency and exact pass contents. Retain
the highway one-draw span as a useful comparison against the Outpost's mixed
753-draw span. Marker 6's limited pass samples do not explain its worst hitch;
do not conclude that its GPU cost is only 13 ms.

Artifacts: `marker-001-pass-ranking.json` through `marker-006-pass-ranking.json`,
`marker-cost-summary.json`, and `outpost-highway-target-spans.json` in the original
session directory. The archive contains only the expected session start, and the
two outlier-family datasets contain no duplicate submission/record identities.
P2.1 remains incomplete; this expands discovery evidence, not qualification.
