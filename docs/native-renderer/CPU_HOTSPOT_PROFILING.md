# CPU hotspot profiling

Use Windows Performance Recorder (WPR) sampling and context-switch data to
find the CPU work and waits that consume each source frame. The existing
source-frame boundary is also emitted through the
`PinyonShift-CriticalPath` TraceLogging provider, so sampled CPU and wait data
can be assigned to title frames without enabling the large diagnostic log.

## Capture the moving Recaro route

Install Windows Performance Analyzer from the Windows Performance Toolkit,
then run an elevated PowerShell from the repository root:

```powershell
.\tools\capture-cpu-profile.ps1
```

The script verifies the AppData save, rejects an already-running game, builds
`RelWithDebInfo`, checks the title, generated guest facades, and ShiftGlue
binaries against their PDBs, records a focused kernel
profile (sampled CPU, context switches, ready threads, processes, and image
loads) plus the project TraceLogging provider, runs
`config/render-tests/fh1-race.fh1test`, and saves the ETL, symbols, frame CSV,
and capture manifest below `.local/cpu-profile`.
The command fails and marks the manifest invalid if WPR reports any dropped
events; do not analyze that ETL.

The build can be prepared without elevation:

```powershell
.\tools\build-preview.ps1 -Configuration RelWithDebInfo
.\tools\verify-profile-symbols.ps1 -Json
```

Use `-SkipBuild` for repeat captures. `-MarkersOnly` records only project
events, which is useful when checking event fields but cannot identify CPU
hotspots. Both modes require an elevated WPR session on standard Windows
installations.

## Analyze the ETL

Open `pinyon-shift.etl` in WPA and add these tables:

1. **CPU Usage (Sampled)**, grouped by process, thread, module, function, and
   stack. Restrict the process to `pinyon_shift.exe` and load symbols from the
   capture's `symbols` directory.
2. **CPU Usage (Precise)**, grouped by process, thread, wait reason, and stack.
   Use this view to distinguish blocked time from scheduler delay. The CSV
   exporter below includes blocked intervals only.
3. **Generic Events**, restricted to provider
   `PinyonShift-CriticalPath` and event `SourceFrame`. The `SourceFrame` field
   is the frame boundary used to correlate the two CPU tables.

Verify that title, generated guest facades, `rexruntimerd`, and `rexgpu-fh1rd`
stacks show function names where those modules have samples. An address-only
stack is a failed symbol check and must not be used to justify an optimization.

To export the ETL directly with Microsoft's TraceEvent reader:

```powershell
dotnet run --project tools/profile-etl-export -- `
  .local/cpu-profile/<capture-directory>
```

This writes `markers.csv`, `samples.csv`, and `waits.csv` beside the ETL and
fails if the capture lost events or more than 1% of game CPU samples lack
stacks. The same CSV contract can also be produced from WPA:

```text
markers.csv: timestamp_ms,source_frame
samples.csv: timestamp_ms,cpu_ms,module,function
waits.csv:   timestamp_ms,wait_ms,wait_reason
```

Then run:

```powershell
python tools/summarize-cpu-hotspots.py markers.csv samples.csv `
  --waits waits.csv --start-frame 4200 --end-frame 4590 `
  --output race-hotspots.json
```

Choose a contiguous range from `markers.csv`; the frame numbers above reproduce
the 2026-09-21 example, which has only 31 frames after the `race-moving`
capture. Extend the route before measuring sustained moving-race performance.
The script assigns every sample and wait to the latest preceding source-frame
marker and writes both JSON and Markdown, ranked by total sampled CPU or wait
time. The JSON includes individual frame CPU and wait totals. Both metrics add
time across concurrent game threads; neither is wall-clock frame latency.
Waits include idle workers. Keep the ETL beside the report so stacks can be
inspected before changing code. See the [first measured result](CPU_HOTSPOT_RESULTS_2026-09-21.md).

## Escalate only when the trace calls for it

Use PIX timing capture when the sampled trace points to D3D12 submission,
present, or fence waits and CPU/GPU overlap needs to be measured. RenderDoc is
for a concrete graphics-state or resource-content investigation; its capture
overhead and single-frame focus do not make it a CPU frame profiler.

Microsoft references:

- [Capture and view TraceLogging data](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/capture-and-view-tracelogging-data)
- [Author recording profiles](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/authoring-recording-profiles)
- [CPU analysis](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/cpu-analysis)
- [Symbol support](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/symbol-support)
