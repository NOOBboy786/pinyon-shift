# Pinyon Shift

Pinyon Shift is a Windows-only playable preview of a native recompilation of
the Xbox 360 release of *Forza Horizon*. The project is early, imperfect, and
surprisingly drivable.

This repository contains the launcher, build tools, host code, configuration,
and pinned ShiftGlue submodule needed to create the preview on your own computer. It does **not**
contain the game, game assets, generated translations, or a prebuilt game
executable.

> **Highly experimental renderer preview - 0.1.2-preview.3.** This build includes
> the latest native renderer checkpoint. Rendering regressions, accelerated NPC
> animations, and severe slowdowns in some areas remain possible. Xenos retirement
> is incomplete. See the [preview release notes](docs/releases/0.1.2-preview.3.md).

## Renderer status and performance

The current backend is specialized for *Forza Horizon 1*, but it is not yet a
fully native game renderer. `rexgpu-fh1.dll` removes the generic plugin boundary,
loads the title's shaders as an offline-precompiled DXIL pack, prewarms known
pipelines, and directly executes two proven fullscreen families. Most scene
draws still pass through ShiftGlue's Xenos-compatible D3D12 command, register,
render-target, texture, and resource machinery. Calling the DLL `fh1` describes
its product scope; it does not mean that all Xenos work has been retired.

The following snapshot was collected on September 4, 2026 on Windows 11 build
26200, a Ryzen 7 5800X, an RTX 4080 using driver 581.08, 128 GB RAM, and a
120 Hz display. Both current implementations used D3D12, VSync, warm caches,
and 2x internal rendering. Xenia used its 1280x720 window while Pinyon Shift
used its normal 3072x1728 window, so utilization is diagnostic rather than a
pixel-for-pixel efficiency ranking.

| Path | What executes FH1 | Shader preparation | Current authority |
| --- | --- | --- | --- |
| [Xenia Canary `577fb8e`](https://github.com/xenia-canary/xenia-canary/releases/tag/577fb8e) | Runtime PPC JIT plus the general Xenia Xbox 360/Xenos emulation stack | Runtime translation and caches | Xenia Xenos emulation |
| Historical ReXGlue Xenos | Recompiled FH1 CPU code plus generic `rexgpu-xenos.dll` | Runtime translation and caches | ReXGlue Xenos compatibility renderer |
| Current FH1 backend | Recompiled FH1 CPU code plus `rexgpu-fh1.dll` | Complete local DXIL pack and pipeline prewarm; zero misses in the measured runs | Mostly Xenos-compatible core; direct native tone-map and velocity-dilation only |

### Measured results

| Workload | Implementation | Internal scale | Result | Supporting observation |
| --- | --- | ---: | ---: | --- |
| Animated title screen | Xenia Canary `577fb8e` | 2x | 30.07 visual updates/s | 15.0 s window-surface sample; 33.305 ms median update interval |
| Animated title screen | Pre-optimization FH1 backend | 2x | **6.00 visual updates/s** | 15.0 s window-surface sample; 174.440 ms median update interval |
| Animated title screen | Current FH1 backend | 2x | **118.30 FPS median** | Final 1,000 source frames of the automated real-title run; 8.453 ms median frame and 5.453 ms median GPU span |
| Stationary open world | Xenia Canary `577fb8e` | 2x | 29.99 visual updates/s | Stock title cadence; 15.0 s window-surface sample |
| Manual open world | Pre-optimization FH1 backend | 2x | 39.07 FPS median | Frames with at least 1,000 draws; 25.593 ms median and 33.763 ms p95 |
| Heavy automated open world | Pre-optimization FH1 backend | 1x | 36.31 FPS median | Frames with at least 2,500 draws; 27.540 ms median |
| Heavy automated open world | Current FH1 backend | 1x | **58.58 FPS median** | One warm run; 17.070 ms median frame, 24.642 ms p99, and 15.749 ms median GPU span |
| Heavy automated open world | Current FH1 backend | 2x | **57.51 FPS median** | Median of three warm runs; 17.390 ms median frame, 29.110 ms p99, 34.35 FPS 1% low, and 17.241 ms median GPU timestamp span |
| Whole automated route | Current FH1 backend | 1x | **110.50 FPS median** | 3,916-frame clean shipping run; 9.050 ms median frame and 8.143 ms mean GPU span; includes title/loading and lighter frames |
| Heavy resolution control | Current FH1 backend | 1x | **50.79 FPS median** | 1,277 frames above 3,000 draws; 19.688 ms median, 23.208 ms p95, and 17.357 ms mean GPU span |
| Heavy resolution control | Current FH1 backend | 2x | **48.35 FPS median** | 1,172 frames above 3,000 draws; 20.683 ms median, 25.002 ms p95, and 20.668 ms mean GPU span |
| Heavy release route after unused draw-key removal | Current FH1 backend | 1x | **61.65 FPS median** | Median of three run medians for frames above 3,000 draws; individual medians were 15.808, 16.426, and 16.220 ms |
| Historical first-Viper drive | ReXGlue Xenos baseline | 1x | 23.35 FPS median | July 19 build; 42.830 ms median and 16.02 FPS one-percent low |

These rows are not a leaderboard. The title and Xenia open-world figures count
distinct animated window-surface changes because PresentMon ETW collection was
not permitted on the test account. Pinyon Shift's FPS rows use its internal
source-frame boundary. The historical Xenos row used an older build, route, and
save and is included only as context; it is not a matched claim that the current
backend is a specific percentage faster. The automated 1x and 2x runs use the
same cloned save and input script, but their exact draw mix changes with the
different source cadence.

The results establish two separate bottlenecks and one verified optimization:

- The title regression was command-processing overhead, not a 30 FPS title
  limit. The same bulk register fix raised the real animated title from 6-9 FPS
  to a measured 118.30 FPS median while preserving its movie-complete setup.
- Sampling found FH1's scene path spending substantial CPU time on per-register
  constant writes and ordered-tree lookups for the title-specific execution
  allowlists. Reusing the existing bulk register writer and changing those
  allowlists to hash sets raised the same heavy 2x route from a 34.54 FPS
  diagnostic snapshot to a 57.51 FPS three-run median.
- The optimized 2x route is now close to GPU-bound: its median frame was
  17.390 ms and the measured D3D12 command span was 17.241 ms. The three runs
  ranged from 52.17 to 57.86 FPS as the scene draw count changed, so stable
  60 FPS at 2x has not been achieved yet.
- The explicit 1x/2x control shows that four times as many raster pixels add
  only about 3.31 ms of mean GPU time in frames with more than 3,000 draws.
  The remaining roughly 17 ms at 1x is therefore mostly the retained
  high-draw compatibility scene, not resolution scaling. Timestamping the
  terminal resolve separately measured roughly 5-30 microseconds for the
  dominant sampled families; their hundreds of draws consume roughly
  0.5-1.5 ms. Replacing the scene families has far more leverage than another
  resolve-only shortcut.
- Normal release draws no longer build the complete FH1 census execution key
  unless a census observer is installed or the exact draw is a native tone-map
  or velocity-dilate candidate. The three optimized heavy-route medians were
  15.808-16.426 ms. One exact full-key control measured 17.103 ms, but route
  mix varies, so this is a retained-path optimization rather than a definitive
  cross-product speedup claim.

The next renderer work should therefore replace or batch the hottest FH1 scene
draw families and retire their command, resource, and render-target
compatibility work. The
corpus-only pass profiler now samples all pass attachments once per 60 source
frames and splits draw time from terminal resolve time without changing release
gameplay. Further direct shader
replacements must pass foliage, minimap, map, pause, modal, and race image gates;
the broader handwritten substitutions were disabled after corrupting those
outputs. A release comparison requires three matched runs per implementation
with the same save, route, output size, and an external present-time collector.
The detailed resume point and ranked next experiments are recorded in
[`docs/native-renderer/NATIVE_RENDERER_PERFORMANCE_CHECKPOINT_2026-09-04.md`](docs/native-renderer/NATIVE_RENDERER_PERFORMANCE_CHECKPOINT_2026-09-04.md).

The repeatable Pinyon Shift route is
[`config/render-tests/fh1-open-world-performance.fh1test`](config/render-tests/fh1-open-world-performance.fh1test).
Runtime CSVs can be summarized with:

```powershell
python tools/summarize-performance.py C:\path\to\session.perf.csv
```

## Play

1. Download `PinyonShift-Launcher.zip` from the latest release.
2. Extract the two files to a folder and run `PinyonShift.Launcher.exe`.
3. Select an ISO you personally dumped from a supported original disc.
4. Confirm ownership, then choose **Verify & Build**.
5. Leave the launcher open while it installs the Windows build tools and builds
   the preview. The first build can take 20–60 minutes and requires roughly
   25 GB of free disk space.

The preview launcher is not code-signed yet, so Windows may identify it as an
unrecognized app. Use only the archive attached to this repository's release
and verify its published SHA-256.

The launcher verifies the image before reading it. Unsupported or modified
images are rejected. Your image and extracted game files stay on your machine.
The launcher downloads build tools and the pinned ReXGlue source, extracts the
disc locally, generates the translation locally, and compiles the executable
locally. Administrator permission is requested only if Visual Studio Build
Tools must be installed.

Supported today: the USA retail base disc, serial `MS-2505`, title ID
`4D5309C9`. Windows 10/11 x64 and a DirectX 12-capable GPU are required.
The launcher includes 2× and experimental 3× (4K-class) internal-resolution
scaling for capable GPUs.

This is a public preview, not a finished remaster. Please report reproducible
problems using the issue template and do not attach game files or generated
code.

## Reporting crashes and bugs

Keep the launcher open while playing. If the game exits unexpectedly, the
launcher catches the exit, creates a sanitized diagnostic ZIP, and offers one
button to open a prefilled GitHub issue with that ZIP selected in Explorer.
Attach the selected ZIP and add the shortest reliable reproduction steps.

The public report includes build hashes, a stable crash ID, exception details,
the end of the runtime log, runtime settings, Windows build, CPU, GPU, and driver
versions. It excludes the game, saves, generated code, input capture, local
paths, and memory dumps. A fuller dump stays on the player's computer and should
only be shared privately if a maintainer requests it. Non-crash bugs can be
reported with **Report a problem** in the launcher.

## Build from source

From a PowerShell terminal in a repository checkout:

```powershell
.\tools\setup-preview.ps1 -IsoPath C:\path\to\your-disc.iso
.\tools\launch-preview.ps1
```

The setup script provisions pinned dependencies, initializes ShiftGlue,
verifies/extracts the disc, generates translated source, and
builds Release. See [Building](docs/BUILDING.md) and
[Troubleshooting](docs/TROUBLESHOOTING.md) for details.

## Project boundaries

Only independently authored project files are licensed under the
[BSD 3-Clause License](LICENSE). Microsoft, Xbox, Turn 10 Studios, Playground
Games, *Forza Horizon*, and third-party dependencies remain the property of
their respective owners. Pinyon Shift is not affiliated with or endorsed by
them. See [Legal and distribution](docs/LEGAL.md) and
[Third-party notices](THIRD_PARTY_NOTICES.md).

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Repository checks reject disc
images, executables, generated translations, extracted assets, build products,
and other machine-local material.
