# Forza Horizon 1 Native Renderer V6 Backlog

Status: planned, 2026-09-04

V6 productizes the compiler-free renderer completed by V5. A clean launcher
setup must derive, validate, and stage every native GPU artifact required by
Forza Horizon 1 from the user's verified game files. Normal gameplay must
remain unable to translate Xenos shaders at runtime.

This remains an FH1-only D3D12 project. It is not a general shader installer,
Xenos renderer, ReXGlue facility, or solution for other recompiled games.

## Final goal

After the launcher verifies and extracts the supported FH1 disc, it produces
the native shader pack and startup catalogs needed by the selected GPU and
render scale, performs a device-local pipeline warmup, and launches the
compiler-free renderer with zero shader or synchronous pipeline misses.

The process must be resumable and must reuse valid artifacts. It must never
upload or redistribute game-derived shaders, silently use a pack produced for
another configuration, or restore runtime Xenos shader translation.

## Device model

V6 deliberately separates two kinds of compilation:

- The FH1 producer translates the game's Xenos shaders into DXIL. Its output is
  selected by translator version, GPU vendor, D3D12 translation flags, and
  integer render scale. It is not keyed by exact GPU model.
- D3D12 and the installed graphics driver compile the DXIL and pipeline state
  for the exact adapter. This device-specific result stays local and may be
  invalidated by a driver update.

The launcher must not invent or distribute a per-model native instruction
format. NVIDIA, AMD, and Intel are separate qualification targets only because
the existing FH1 translator consumes the vendor ID and may emit different
DXIL or bindings for vendor-specific behavior.

## Scope lock

- Title ID `4D5309C9` and the single supported retail revision only.
- D3D12 and the existing `rexgpu-fh1` / `rexgpu-fh1-producer` split only.
- Generate artifacts locally from the user's already-verified extraction.
- Keep `.dxil`, `.dxbc`, manifests with guest shader identities, and `.pnsp`
  files under `.local`; none enter the public source or launcher payload.
- Build and stage only the selected scale initially. Produce 1x, 2x, or 3x on
  demand when the user changes scale instead of spending roughly 1.4 GB on all
  three during every setup.
- Reuse the current corpus extractor, producer, pack builder, startup catalogs,
  render-test automation, and strict runtime gates.
- The normal runtime must remain compiler-free and fail closed on any missing,
  stale, malformed, or mismatched artifact.

## Current baseline and gap

- Complete NVIDIA packs exist locally for 1x, 2x, and 3x, each with 22,012
  exact shader variants.
- The runtime already selects an exact pack by translator version, adapter
  vendor ID, translation flags, and scale.
- `launch-preview.ps1` stages a matching pack and startup catalog only when
  those developer-local artifacts already exist.
- `setup-preview.ps1` verifies and extracts the game, runs code generation, and
  builds the playable recomp, but does not produce native GPU artifacts.
- `rexgpu-fh1-producer` is intentionally excluded from the normal build and
  install. Release packaging also rejects `.pnsp` and translated shader files.
- AMD and Intel production and gameplay qualification have not been completed.

## Milestone order

### V6-01 — One-command FH1 artifact production

Join the existing offline tools into one deterministic, launcher-callable
workflow. It accepts the verified game root, state root, and render scale; all
other configuration comes from the actual D3D12 adapter and renderer.

Work:

- Extract the complete FH1 shader corpus from the verified local game files.
- Build the explicit `rexgpu-fh1-producer` target without adding it to the
  default runtime build.
- Run the producer for the active adapter and requested scale.
- Assemble and verify the V2 `.pnsp`, analysis catalog, pipeline-description
  catalog, and FH1 prewarm allowlist.
- Stage the result atomically only after every format, hash, identity, coverage,
  and configuration check passes.
- Emit bounded machine-readable progress for the launcher and preserve enough
  intermediate state to resume after cancellation or failure.

Exit gate:

- Starting without pre-existing native-renderer artifacts, one command creates
  and stages a complete pack for the current NVIDIA configuration.
- The strict automated FH1 route completes with zero shader misses, zero
  runtime translations, and zero synchronous pipeline creations.
- The shipping runtime binary still contains neither the shader compiler nor
  `AnalyzeUcode`.

### V6-02 — Launcher install and on-demand scale integration

Make native artifact production part of the existing local setup rather than a
developer-only procedure.

Work:

- Invoke V6-01 after verified extraction and the playable build are available.
- Let the renderer/producer report the adapter vendor and feature flags; do not
  duplicate D3D12 compatibility decisions in launcher UI code.
- Display production, validation, warmup, cancellation, and recovery progress.
- Mark setup complete only when the selected scale's exact pack and all three
  startup files are staged in the launch state.
- When graphics settings select another integer scale, generate that scale on
  demand before launching it.
- Report an actionable unsupported-adapter or production error. Never launch
  with an NVIDIA pack on AMD/Intel or fall back to runtime translation.

Exit gate:

- A clean launcher installation from the supported disc reaches a playable,
  compiler-free NVIDIA build without manual commands or developer `.local`
  artifacts.
- Changing between 1x, 2x, and 3x either reuses a valid pack or produces and
  validates the missing one before play.

### V6-03 — Artifact identity, reuse, and update lifecycle

Avoid repeating the expensive corpus translation while making stale reuse
impossible.

Work:

- Record the supported dump identity, guest extraction identity, pack schema,
  translator version, renderer/source revision, vendor ID, translation flags,
  scale, entry count, and SHA-256 values in a local receipt.
- Verify the receipt and artifacts before reuse; do not trust filenames alone.
- Invalidate only the affected artifact set after a translator, schema,
  renderer configuration, disc revision, or adapter-vendor change.
- Use atomic replacement so cancellation cannot destroy the last valid pack.
- Keep user saves and unrelated launcher state outside cleanup and migration.
- Bound retained scale/vendor artifacts and expose their disk use to the user.

Exit gate:

- An unchanged reinstall performs verification but no shader translation.
- A deliberately changed key rebuilds exactly the affected scale/configuration.
- Interrupted production resumes or restarts safely without accepting a
  partial pack.

### V6-04 — Exact-device D3D12 pipeline warmup

Exercise the generated DXIL on the installed adapter so D3D12 and its driver
can perform the actual device-specific compilation before gameplay.

Work:

- Add a non-interactive FH1 startup mode that initializes the renderer, creates
  every admitted startup PSO, verifies completion, and exits.
- Run it after a new pack is staged and allow the driver to manage its own
  device/driver cache.
- Record adapter and driver identity only as warmup evidence; do not serialize
  or distribute opaque vendor machine code unless a later measured startup
  problem justifies a D3D12 pipeline-library implementation.
- Repeat warmup after a relevant adapter or driver change without rebuilding
  the vendor DXIL pack when its own identity remains valid.

Exit gate:

- Fresh-device validation creates every FH1 startup pipeline successfully and
  reports no device removal or invalid shader bytecode.
- The subsequent automated gameplay route reports zero synchronous pipeline
  creation and zero prewarm fallback draws.

### V6-05 — AMD and Intel qualification

Extend only the proven FH1 artifact workflow to the other supported PC GPU
vendors. Do not generalize the renderer around hypothetical devices.

Work:

- Produce exact AMD (`0x1002`) and Intel (`0x8086`) packs on representative
  hardware using the same verified FH1 corpus.
- Compare manifests and bytecode to determine where vendor-specific output is
  real; retain the existing exact-vendor key unless evidence proves it can be
  removed safely.
- Run the automated free-roam, race, SELECT-map, pause, photo, FMV, 1x, 2x,
  3x, and unlocked-presentation matrix supported by each device.
- Keep a vendor enabled only after zero-miss correctness, pacing, and
  device-loss gates pass. Unsupported adapters receive a clear launcher error.

Exit gate:

- Every advertised vendor completes production, warmup, and the FH1 mode/scale
  matrix without runtime translation or visual fallback.
- Hardware requirements name the actually tested feature levels and vendors.

### V6-06 — Release and clean-machine gate

Prove that the public launcher package contains everything needed to create
local artifacts without containing the artifacts themselves.

Work:

- Keep the producer source and build recipe in the source payload while keeping
  its DLL unstaged outside production runs.
- Verify release archives reject game files, shader manifests, DXIL/DXBC, and
  `.pnsp` packs.
- Exercise clean setup, cancelled setup, unchanged reinstall, renderer update,
  driver update, GPU-vendor change, and on-demand scale change.
- Extend crash/support reports with artifact identities and validation results,
  never shader contents or guest identities.

Exit gate:

- A clean supported PC can go from verified FH1 disc to strict native gameplay
  through the launcher alone.
- Normal launch stages only the compiler-free renderer and validated local
  artifacts; the producer is absent while the game is running.
- Release verification and the full FH1 automated renderer matrix pass.

## Status

| ID | State | Deliverable |
| --- | --- | --- |
| V6-01 | planned | one-command local FH1 artifact production |
| V6-02 | planned | launcher setup and on-demand scale integration |
| V6-03 | planned | safe cache identity, reuse, and invalidation |
| V6-04 | planned | exact-device D3D12 pipeline warmup |
| V6-05 | planned | AMD and Intel FH1 qualification |
| V6-06 | planned | clean-machine and release gate |

Execution order is V6-01 through V6-06. NVIDIA at the currently selected scale
is the first supported path; additional scales and vendors reuse that exact
workflow only after it passes its exit gate.

## Explicit non-goals

- A shader-pack or installer framework for other games.
- A general Xenos/Xbox 360 shader compiler or renderer.
- Per-GPU-model native machine-code distribution.
- FSR, optical flow, or third-party frame generation.
- Runtime shader translation as a compatibility fallback.
- Uploading, committing, or redistributing game-derived shader artifacts.
