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
`RelWithDebInfo`, checks each binary against its PDB, records a focused kernel
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
   Use this view for scheduler delay and blocked time.
3. **Generic Events**, restricted to provider
   `PinyonShift-CriticalPath` and event `SourceFrame`. The `SourceFrame` field
   is the frame boundary used to correlate the two CPU tables.

Verify that title, `rexruntimerd`, and `rexgpu-fh1rd` stacks show function
names. An address-only stack is a failed symbol check and must not be used to
justify an optimization.

For a compact checked-in report, export or normalize the three WPA views to:

```text
markers.csv: timestamp_ms,source_frame
samples.csv: timestamp_ms,cpu_ms,module,function
waits.csv:   timestamp_ms,wait_ms,wait_reason
```

Then run:

```powershell
python tools/summarize-cpu-hotspots.py markers.csv samples.csv `
  --waits waits.csv --output cpu-hotspots.json
```

The script assigns every sample and wait to the latest preceding source-frame
marker and writes both JSON and Markdown, ranked by total sampled CPU or wait
time. Keep the ETL beside the report so stacks can be inspected before changing
code.

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
