# FH1 renderer test automation

This is a Forza Horizon 1-only unattended test path. It launches the real game
and native renderer with a synthetic controller, writes full-resolution PPM
captures, and exits through the normal window-close path. Scripts use completed
guest-output frames by default; `# clock-hz N` makes their frame numbers an
explicit wall-time clock for stock-versus-unlocked comparisons. It does not use
computer use, screen scraping, or a physical controller.

Run a scenario against the installed preview save:

```powershell
$stateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift\source\0.1.0\.local\preview'
python tools/run-fh1-render-test.py config/render-tests/fh1-map.fh1test `
  --state-root $stateRoot --record-baseline
```

Every run copies only `user` and `config` from that state root into a private
sibling directory beside its output. FH1 may autosave in the private copy, but
the selected seed and the user's normal save are never written. Cache contents
are deliberately not shared between runs. `--seed-shader-storage`
`--seed-pipeline-prewarm` copies the immutable FH1 native shader/pipeline catalog
and its allowlist; it no longer seeds writable `.xsh`/`.xpso` stores.
Supplying `--shader-pack` automatically seeds the catalog because the shipping
backend needs both pieces.

Pass `--baseline-dir <previous-output>` to compare each capture named by an
`# expect-image` line with a known-good run. Those lines set limits for mean
absolute error, root-mean-square error, and changed-pixel ratio. Dynamic race
and free-roam shots intentionally allow traffic, camera, and simulation drift;
the static SELECT map has a tight limit. Baselines contain game imagery and
therefore remain local rather than being committed. Creating such a reference
requires the explicit `--record-baseline` switch; a scenario with image
expectations otherwise fails before launch, preventing a missed reference from
being reported as a successful visual gate.

`# expect-performance` sets maximum median frame time, minimum presentation
rate, and the permitted main-loop-rate range. The legacy telemetry field is
named `simulation_tick_count`, but the measured hook is the FH1 application
loop and must not be interpreted as an individual physics-step counter.
`# require-native` requires an
exact FH1 native family to execute. A run also fails for missing or wrong-frame
captures, blank output, renderer/GPU/device-loss errors, a missed capture frame,
or an abnormal process exit. The PowerShell launcher owns the exact child PID
and terminates it if the render-test timeout expires.

`# expect-distinct-presentation <minimum-hz>` rejects repeated host presents;
only distinct completed FH1 frames count. Use repeatable
`--game-argument=<cvar>` options for cadence and resolution qualification. The
launcher serializes the list so multiple PowerShell options cannot be mistaken
for launcher parameters.

`# expect-capture-mae <first> <second> <minimum>` proves that a scripted mode
transition actually happened before a baseline can pass. The map scenarios use
it to reject tutorial profiles where SELECT is intentionally unavailable.

Add `--collect-pass-inventory` for a dedicated run that records the ranked
exact FH1 pass-family identities, draw ranges, samples, and measured GPU
nanoseconds in `result.json`. These are the compatibility-cost inventory used
to choose or reject further V5 retirements; native-family counts separately
prove work actually removed. Normal performance runs leave this instrumentation
off so its per-draw timing does not contaminate frame measurements.

The committed scenarios cover:

- `fh1-smoke.fh1test`: launch, capture, and clean self-termination;
- `fh1-fmv.fh1test`: startup/FMV composition with
  `--include-opening-movies`;
- `fh1-free-roam.fh1test`: driving view, HUD, and minimap;
- `fh1-map.fh1test`: SELECT map roads/icons and return to free roam; and
- `fh1-pause.fh1test`: pause overlay and return to free roam; and
- `fh1-photo-mode.fh1test`: enter and leave FH1 photo mode; and
- `fh1-source-60.fh1test`: sustained driving with a real distinct-frame gate;
  and
- `fh1-hfr-modes-control.fh1test` / `fh1-hfr-modes-unlocked.fh1test`: paired
  wall-time free-roam, SELECT-map, pause, and resume qualification; and
- `fh1-race.fh1test`: event entry, car/start menus, live race HUD, and motion
  without completing the event.

This is not a synthetic renderer unit test and does not bypass the real FH1
runtime. A normal host window may exist while the run is unattended; hiding or
reimplementing it adds no test reliability. Map and race traces still require a
known progressed local seed at their expected location. The runner copies that
seed before launch; unknown or locked scene state fails before it can become a
visual baseline.
