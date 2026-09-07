# FH1 native-renderer performance checkpoint — 2026-09-04

This is the resume point for the active goal to make Pinyon Shift's *Forza
Horizon 1* renderer genuinely native and materially faster and lighter than
Xenia Canary. The goal is **not complete**.

## Resume audit — 2026-09-04, 23:25 UTC

### Remote checkpoint and highly experimental preview (2026-09-07)

- Publication update: preview.1 CI stopped on a legacy CP1252 em dash in this document before any release was published. Converted that one invalid UTF-8 byte to its UTF-8 representation, preserving all other text. Successful publication target is now 0.1.2-preview.2; see [release notes](../releases/0.1.2-preview.2.md).

- Release checkpoint: 0.1.2-preview.1, preview channel, targeting remote dev. ShiftGlue source pinned to 6db74f6de0230727358d93f8a221f40fbba6a792. Release notes: [0.1.2-preview.1](../releases/0.1.2-preview.1.md).
- Includes all retained native renderer source, shader headers, automation, prototype cleanup and playtest feedback. Local captures, generated game code, game data, saves, binary shader packs and temporary diagnostic DLLs remain local. Full C347/21B70 terrain pair remains disabled; Xenos retirement remains incomplete.
- Preview releases require dev ancestry; stable releases retain main ancestry. This preview is explicitly highly experimental and documents animation-timing concerns and severe area-specific performance drops. No new minimum-hardware claim.
- The nested libmspack working changes are materialized Windows symlinks produced by the existing prepare-rexglue.ps1 repair step, not renderer source changes; their upstream pin remains unchanged.

### Manual playtest feedback (2026-09-07)

- User reports around70FPS in general driving, apparently accelerated NPC animations (possibly title-screen UI transitions), and severe area-specific choppiness that clears after leaving. Recorded with original screenshot and follow-up checklist in [PLAYTEST_FEEDBACK_2026-09-07.md](PLAYTEST_FEEDBACK_2026-09-07.md). Screenshot shows approximately14.8 renderFPS/12.9 presentFPS. Causes and exact map location remain unconfirmed; investigate later. No runtime changes made for this feedback.

### Same-input terrain timing diagnostic (2026-09-07)

- CURRENT PRODUCTION UNCHANGED: staged and artifact DLL75521DA21DBAC16D95CA6C6F9E11640A5A601A393E86C6D4192044782A3863E4. All five diagnostic C++/header files restored byte-for-byte to `terrain-paired-before`; final rebuild `terrain-paired-final-restored-build.log` reproduced the hash. C347 standalone and C347/21B70 full pair remain disabled. Retained normalization and fetch branches remain intact. No game is running. Full Xenos retirement remains active/incomplete.
- Previous turn was progress (retained normalization). This turn is diagnostic progress: replaced unmatched gameplay comparisons with identical-input GPU draw measurements and verified the restore procedure. Artifacts below are under `.local/native-renderer/` and are temporary diagnostics, not production features.
- `terrain-paired-diagnostic.py apply|restore` builds from the saved terrain-pair pipeline integration and current normalized shader headers. Creates an original-bytecode comparison PSO only for the qualified native pair with an identical root signature; original translations loaded under existing lock. Both PSOs must be non-null before sampling. Direct PSO binding sets the deferred executor's current pipeline, so these sampled draws cannot be skipped due to pending async creation. Comparison PSO lifetime belongs to Pipeline. Backups retain resources until shutdown. All bound accumulated color/depth/stencil targets copied before sampling; restored before EVERY warm-up/measured draw; copies and PSO binding outside timestamps. Reject memexport, active legacy/modern occlusion queries, metadata hazards, unavailable queries, or insufficient query slots. Final target contents always come from legacy shaders. No new production configuration.
- Initial two-draw alternating-order diagnostic D2BE584E1CB26621B326A2683B6A48BFF1195D7C92F82AB17BA238CA513632E0, PID48824 normal exit:125 pairs. Severe first-draw penalty: native-first ratio2.2606, native-second0.5196. This is order bias, NOT shader performance evidence. `terrain-paired-1x-smoke/paired-timing.json`.
- Improved diagnostic performs one warm-up of each shader, then ABBA or BAAB on EACH identical draw/input. Four measured draws per pair, two samples per shader, one sample selection every10frames. `terrain-paired-abba-candidate.dll`7700FB36F2324171467F41AC2BAC02D84F957539440B1229DE1A48CA3905080E. PID10840 normal exit.129 complete pairs, all first terrain draws with378 indices; native mean totals658432ns vs legacy650752ns (+1.1802%), median paired difference0. Native-first -0.3096%, legacy-first +2.72%. Small draw subset, not a broad speed claim.
- Capture-only every-frame variant65EE2EA62D321DFAD8CBC52D5A4CE333CA7DB22C1A38B0CE919C99DB023528A6, PID31792 normal exit. `terrain-paired-rdc/frame_frame3074.rdc` and `terrain-paired-capture-parity.py`: actual warm-ups plus BAAB quartet, six native/legacy draws. Exact bytecode assertions for normalized native VS4ED4C11E/native PS4F5188 versus original VS26BD8517/original1x PS2A082D. All six post-VS outputs equal (181440bytes); before-draw inputs equal after each restore and all after-draw targets equal (251658240 target/sample bytes per comparison phase), including four MSAA samples of D32S8_TYPELESS and R16G16B16A16_FLOAT. 1x refers to resolution scale, not MSAA. Report `terrain-paired-capture-parity/report.json`. This validates one captured paired input, not every timed input.
- Rotating selection through first16 eligible terrain draws, FEF12E66D15A2B9B0F1AE1E4B3B3A5E92D9899C028A26AD5C96C1A96C6D2889B (`terrain-paired-rotating-candidate.dll`), PID4804 normal exit.100 complete pairs,13 index counts4..378, median31. Native295936ns vs legacy326144ns averaged over duplicate samples (-9.2622%, absolute mean -302.08ns/draw);48 native wins/32ties/20losses. Median paired delta0; native-first -0.6897%, legacy-first -16.4265% shows residual order sensitivity. Largest absolute pair delta3072ns. Do not extrapolate this tiny warmed-draw result to frame time, CPU usage, all terrain workloads, or minimum hardware. Timestamp quantization previously observed1024ns; two-sample means can differ512ns. Descriptive bootstrap in JSON assumes independent pairs and is NOT an independent-trial confidence claim.
- `summarize-terrain-paired.py <run-dir>` reads ALL archived rotated runtime logs, filters using actual PID session timestamps, requires normal exit, complete unique four-sample records and correct ABBA/BAAB shader order. `--self-check` rejects missing/duplicate/reordered/invalid timestamp records. `terrain-paired-abba-1x` and `terrain-paired-rotating-1x` contain launch metadata, runtime archives and paired-timing reports. Latest source snapshot `terrain-paired-source` has rotating selection; capture source separately `terrain-paired-capture-command-processor.cpp`. Preserve exact current production backups when reusing diagnostics.
- Checks: all diagnostic builds succeeded; capture parity passed; paired parser self-check passed;51 shader-pack/native-renderer/release/render-test unit checks passed after first production restoration; final restoration verified every source byte and both DLL hashes. No production optimization retained this turn. Next useful work should target a concrete remaining renderer dependency or shader cost; avoid more unmatched gameplay runs or claiming this microbenchmark alone justifies enabling the full pair.

### Retained packed terrain normalization (2026-09-07)

- NEW CURRENT staged/artifact DLL75521DA21DBAC16D95CA6C6F9E11640A5A601A393E86C6D4192044782A3863E4, `.local/native-renderer/terrain-normalization-candidate.dll`. Supersedes A4FF9E shared-fetch baseline. Do not blindly restore older helper or shader headers. Material pair and standalone C347 remain disabled; no pipeline gate/binding changes in this retained step.
- Retained rounded reciprocal multiplication for shared SNORM16 and SNORM101111 unpacking in fh1_terrain_vertex.hlsli and UNORM16 UV/SNORM8 color in fh1_terrain_lit.vs.hlsl. Matches original translator OpMul with float reciprocal constants. Regenerated ALL five terrain VS headers, including both owned-depth variants. All five compiled disassemblies now contain only the perspective-related DIV; packed normalization DIVs are gone. Driver-level optimization/speedup is not established by DXBC instruction selection.
- Extended tools/check-fh1-terrain-fetch.py: compiles five variants, exact source/header bytecode identity, rejects packed-normalization DIV operands, retains exclusive SRV/UAV branch checks. Passed. Clear and packed-world compiled checks passed;51 pack/renderer/release/render-test unit checks passed. `terrain-normalization-build.log`; gameplay smoke PID30500 normal exit (`terrain-normalization-smoke`).
- Full prototype exact parity with native material PS: terrain-normalized-parity2x18draws/175168vertexbytes/3019898880targetbytes; terrain-normalized-1x-parity1x16draws/136640vertexbytes/671088640targetbytes. Both include completed SNORM101111 operation change and are exact against originals. Normalized lit DXBC4ED4C11E39FF1D1EA35E29690D0CB791B25E5EC8EEFBF776034F283B6BC28F1B.
- Shared-depth replay (`terrain-normalized-depth-parity`)267draws/678432vertexbytes and125952000final depth-target bytes exact across all3terrain-depth families. Owned-depth replay (`terrain-normalized-owned-parity`)204draws/657840vertexbytes and125952000final depth-target bytes exact. Owned replay uses historical terrain-root capture with three root SRVs pointing at fallback shared memory; it validates owned shader arithmetic/root layout, not every later cache relocation. Only arithmetic changed, buffer addressing/layout remains untouched. Depth target checks are at final selected event per target, not per draw.
- Source snapshot terrain-normalization-source/files.json; prior helper/lit source/fiveheaders/checker in terrain-normalization-before. Raw prototypes and disassemblies terrain-normalized*.dxbc/.txt. Full Xenos retirement remains active/incomplete. No lower hardware requirement or whole-game performance gain claimed.
- Next native material integration must use current normalized headers and current baseline75521DA2, not stale47B4/26F2 diagnostics. Existing unmatched gameplay/timing families cannot establish a speed comparison. An identical-input comparison, potentially reusing existing target-backup/restore diagnostic techniques, is preferable to more unmatched stationary batches; inspect query hazards and PSO readiness before designing it.

### Recovered timing logs and reciprocal-normalization prototype (2026-09-07)

- Previous turn was progress: real raw timestamps established. V5 uses V4 per-draw diagnostic plus explicit zero-drop logging and a TERRAIN_QUERY_DRAW marker. Diagnostic deferred-command replay counts marked draws and skipped PSOs. Sources `terrain-draw-timing-diagnostic-v5.cpp`, `terrain-timing-deferred-v5.cpp`; original deferred source in `terrain-timing-deferred-before.cpp`. Builds/runs in terrain-draw-timing-v5-*.
- IMPORTANT measurement artifact root cause: runtime.log ROTATES. Copying only runtime.log preserved just the last18seconds of V5 baseline and last5seconds of V5 native, omitting probe/aggregate records. This explains missing records without proving flag, shader execution or query failure. Earlier V1-V4 conclusions about absent records were based on incomplete log fragments and should not be treated as renderer failures. Recovered all runtime archives in `terrain-draw-timing-v5-runtime-archive`; future diagnostics MUST archive rotated runtime logs and filter by session times, not just copy current runtime.log. Cached/raw flag and observer were true in the valid probe.
- V5 baselinePID47872/nativePID37640 normal exits. `terrain-draw-timing-v5-records.json`: baseline18074 marked draws executed, native17092; zero skipped marked draws and zero reported query drops. Latest recovered aggregates:64baseline families/15235samples and54native families/14269samples. Aggregate samples do not include all executed draws because periodic logging trails run end; do not assume complete frame coverage. Source shader pair/pipeline/attachment states match, but full timed execution identities have ZERO intersection. Seven coarser draw families overlap; resource/dynamic/operation combinations differ. `terrain-draw-timing-v5-state-sets.json` records corpus state sets. Summarizer intentionally refuses a performance comparison with no matched full families. No speedup claim; do not loosen matching silently.
- New concrete shader observation: original C347 DXBC instruction80 normalizes SNORM16 using MUL. `pipeline/shader/dxbc_translator_fetch.cpp` lines334-342 and370-383 compute float reciprocals and emit OpMul for signed/unsigned packed formats. Native terrain emitted DIV for SNORM16, UNORM16 UV and SNORM8 color.
- Prototype `terrain-mul-vertex.hlsli` and `terrain-mul.vs.hlsl` explicitly use reciprocal multiplication for those three formats; `terrain-mul.dxbc` and disassembly compile cleanly, four corresponding DIVs disappear (494 static instruction slots unchanged). This is source-operation alignment, not proof of faster GPU machine code; the driver may already strength-reduce constant divisions. Existing direction SNORM101111 divisions are NOT changed by this prototype and remain to be aligned/validated.
- Exact combined prototype replay: `terrain-mul-parity/report.json` 2x18draws/175168vertexbytes/3019898880targetbytes; `terrain-mul-1x-parity/report.json` 1x16draws/136640vertexbytes/671088640targetbytes; both exact against original shaders. Material PS remains4F5188F2. No live integration of normalization prototype yet.
- `terrain-normalization-rounding.json` exhaustively compares CPU float32 division versus float32 reciprocal multiplication: differing normalized values1536/65536 SNORM16,512/65536 UNORM16,16/256 SNORM8,48/2048 SNORM11,96/1024 SNORM10. This illustrates arithmetic distinction; it does NOT prove old GPU output mismatches, since DXBC DIV implementation/driver optimization differs from CPU reference.
- All timing diagnostic source changes restored, retained shared-fetch source intact. Current staged/rebuilt artifact A4FF9E7455666E458F8978A6087C7D2116FE0074ADF46223AD589DDC6FF47D84; `terrain-v5-reverted-build.log`. Terrain material pair still disabled. Next: align remaining packed normalization operation, validate all shared helper users/generated headers, then assess integration without another unmatched stationary batch. Full retirement remains active/incomplete.

### Raw terrain timestamp investigation (2026-09-07)

- Previous turn produced diagnostic failure evidence, not a speed result. V3 (`terrain-draw-timing-diagnostic-v3.cpp`, DLLF6CF0059A883361D1CB77DBF60A79A569E2EC441C846AF77683E2DC036E9F697) forces terrain observation metadata population, uses frame_current_, removes modulo60 sampling, sets key.kind=Draw, adds limited begin/raw-retirement logs. BaselinePID2372 normal exit but no TERRAIN_QUERY logs. Its executable corpus20260907T174508Z-p2372.json nevertheless contains44 C347 entries/15554 observations. Screenshot was visually inspected and shows normal Recaro Rush world, not a blank/menu scene.
- V4 (`terrain-draw-timing-diagnostic-v4.cpp`) removes the outer Fh1GpuCorpusEnabled condition from terrain selection and probes cached/raw flag and prepared observer at the first8 terrain calls. BaselinePID48660 normal exit. Loaded module path verified while live: out/build/win-amd64-release/rexgpu-fh1.dll. Probe reports cached true, raw [true], observer true, heap/mapping true, frequency1000000000. The registry-mismatch hypothesis is NOT supported. Do not claim a flag-registry fix or a fully explained V3/V4 discrepancy.
- V4 raw retirement logs are real nonzero timestamps with completed submission fences and monotonic endpoints. First16 intervals:6nonzero and10zero; nonzero delta GCD1024ticks at1GHz. This is observed granularity of this sample, not proof of a hardware timestamp specification. Identical endpoints are a precision/execution concern and cannot be read as zero shader cost. `terrain-draw-timing-v4-evidence.json` preserves raw values and72 family aggregates from11:51local log window. No native comparison has been run with V4; no performance conclusion available.
- DeferredCommandList replay executes timestamp EndQuery unconditionally, but Draw commands only when current_pipeline_state is non-null. Thus future diagnosis must distinguish skipped/empty draws from timestamp granularity, not assume every recorded draw executed. Collector's latest-family logs are cumulative. Zero dropped queries are currently NOT explicitly logged if there are no signature aggregates (Finish(0) leaves signature0), so the summarizer's requirement for an existing dropped-samples line is too strict for this diagnostic. Add an explicit drop-count log to diagnostic, don't silently assume zero.
- All diagnostic source changes restored; current staged/artifact A4FF9E7455666E458F8978A6087C7D2116FE0074ADF46223AD589DDC6FF47D84. Rebuild log `terrain-timestamp-debug-reverted-build.log`. Shared fetch optimization remains; material pair disabled. Full retirement remains active/incomplete.
- Next useful work: compare baseline/native with identical V4-derived diagnostics, explicit drop reporting and matched family sample counts, plus actual deferred draw-execution evidence where zero intervals dominate; consider larger spans only if transfer exclusion remains provable. Do not rerun V1/V2 unchanged or substitute zero/missing values for timings.

### Terrain draw timing diagnostic - invalid samples (2026-09-07)

- Previous turn was progress: 1x performance evidence rejected unchanged admission. Implemented temporary per-draw timing with existing Observe/Finish query collector, bracketing ONLY D3DDrawInstanced/D3DDrawIndexedInstanced after barriers/index copies/pipeline binding. Removed old pre-draw pass Observe call in diagnostic only, selects C347/21B70, includes actual host vertex count in operation identity. Each finished span is one draw, no terminal resolve. Uses existing slot/query/fence retirement. Does not prove identical geometry or pixel inputs across runs; grouped operation identity only.
- First diagnostic `terrain-draw-timing-diagnostic.cpp`, baselinePID50892/nativePID47608 normal. Used observation_frame_sequence_ instead of original collector call's prepared_observation.frame_sequence. Baseline no family records; native zero durations. Corrected diagnostic `terrain-draw-timing-diagnostic-v2.cpp` uses prepared frame in both selection and Observe. V2 baselinePID45384/nativePID36696 normal exits, but SAME unusable measurement outcome: baseline no matching family records; native recorded zero durations. `terrain-draw-timing-v2-invalid.json`. No timing/performance conclusion available; zero is NOT a speedup.
- Preserve `.local/native-renderer/terrain-draw-timing-{v2-,}{baseline,native}.dll`, build logs, run scripts/output directories and summarizers. Summarizer fails on absent baseline records intentionally; do not relax its validity checks. Runtime logs contain multiple sessions, so timestamp-filter actual session before analysis.
- Production command_processor.cpp restored bytewise from `terrain-draw-timing-before.cpp`; pipeline cpp/header restored from `terrain-pair-1x-before`. Shared terrain fetch fix remains. Rebuilt/staged A4FF9E baseline, log `terrain-draw-timing-reverted-build.log`. Material pair still disabled.
- Next diagnostic work: establish why selected sampled frames lack baseline draws and why recorded native timestamps are zero. Inspect frame sampling aliasing, key kind/identity, query record offsets/raw ticks/frequency, command replay handling and actual draw execution. Sampling every frame temporarily would distinguish selection aliasing; raw timestamp evidence is needed before assuming it. Do not re-run unchanged gameplay benchmarks or claim per-draw timing is operational. Full Xenos retirement remains active/incomplete.

### Terrain pair 1x performance batch (2026-09-07)

- Previous turn was progress: retained shared fetch fix and completed live2x pair parity. Tested validated pair at1x against CURRENT A4FF9E shared-fetch baseline. Updated diagnostic pair DLL47B4C27C72E29CE2FF68A868C4207E0856A03952102F742F6145923F5BA61390 (`terrain-pair-updated-candidate.dll`) built with current terrain headers and saved pair pipeline integration. `terrain-pair-updated-build.log`; baseline pipeline files preserved in `terrain-pair-1x-before` and restored bytewise after build.
- `terrain-pair-1x-abba-summary.json`: A1 PID48604, B1 PID23476, B2 PID48540, A2 PID49072; all normal exits. Candidate CPU+1.53606%, median frame+4.14723%, p95+3.73520%, private memory-0.06375%, working set-0.39648%. Workload draw+3.05564%, vertex+2.22509%, GPU frame time+5.31340%. No benefit established at1x; workloads differ, so this does not isolate shader causation. Pair remains disabled. Do not keep repeating unchanged stationary gameplay batches to resolve this.
- Staged and rebuilt shared-fetch baseline A4FF9E7455666E458F8978A6087C7D2116FE0074ADF46223AD589DDC6FF47D84; `terrain-pair-1x-reverted-build.log`. Retained helper fix preserved. Full retirement remains active/incomplete.
- Timing investigation: existing `packed-bindings-gpu-profile/report.json` explicitly reports NO RenderDoc GPU duration counter samples; `constant-pair-queries/report.json` also has empty samples and missing Nsight Perf SDK entry. Do not treat empty counters as zero or repeat the same unsupported method. Same-capture GPU timing is not available through that path yet.
- Next concrete measurement: use existing in-renderer timestamp collector to isolate C347 draw time and group by matching draw workload, excluding transfers. Relevant command_processor.cpp locations: ObserveFh1GpuPassTimingDraw call3325, actual D3DDrawInstanced3947 / D3DDrawIndexedInstanced4016, collector implementation6133, FinishFh1GpuPassTiming6220, EndFh1GpuPassTimingFrame6276. Existing pass spans include other work and cannot by themselves attribute C347-first mixed-pass cost to this shader. Inspect full collector and all draw early exits before introducing diagnostic spans; use existing query/fence retirement.

### Retained shared terrain fetch fix and live2x proof (2026-09-07)

- NEW CURRENT production/artifact/staged DLL: A4FF9E7455666E458F8978A6087C7D2116FE0074ADF46223AD589DDC6FF47D84, `.local/native-renderer/terrain-fetch-candidate.dll`. This supersedes F1D8AB as current baseline. Do not blindly restore F1D8AB or old terrain headers and lose this retained fix. Terrain material pair and standalone C347 remain disabled.
- Retained explicit [branch] SRV/UAV selection in shared `fh1_terrain_vertex.hlsli`, replacing ternaries that FXC flattened into both resource loads. Regenerated lit, depth_standard and depth_offset VS headers. Existing two owned-depth variants compile byte-identically, so their headers are unchanged. Lit VS now matches validated branch8167C441 but is not admitted. No pipeline gate or runtime binding changes in this retained step.
- New runnable `tools/check-fh1-terrain-fetch.py --compiler <fxc.exe>` compiles all five terrain VS variants, checks exact generated-header identity, and verifies mutually exclusive SRV/UAV raw-load branch pairs in all three shared-memory variants. Passed. Clear and packed-world compiled checks passed;51 pack/renderer/release/render-test unit checks passed. Build log `terrain-fetch-build.log`. Gameplay smoke PID30336 normal exit, `terrain-fetch-smoke`.
- Shared-depth differential replay `terrain-branch-depth-parity/report.json`, historical pre-owned `native-indices-rdc/frame_frame3105.rdc`, replaces original terrain VS with new branch DXBC:267draws (5A28:111,4E1D:74,CA293:82),678432 vertex-output bytes all EXACT; final depth target samples125952000bytes EXACT. Target check is at last selected draw per target, not every draw. Both shared depth variants exercised; owned variants are byte-identical. `terrain-branch-depth-bytecode.json` records hashes.
- Improved terrain pair live2x `terrain-branch-live-2x-rdc`, PID45260 normal exit. `terrain-branch-live-2x-active-parity/report.json` asserts both branch VS and material PS active, replaces both originals:14draws/153440vertexbytes/2348810240targetsamplebytes EXACT. Together with prior live1x and forcedfailure tests, branch pair correctness gates now covered for tested scenes. Pair still not admitted pending performance retention decision.
- Retained source snapshot `terrain-fetch-source/files.json`; prior helper/threeheaders in `terrain-fetch-before`. No measured whole-game speedup or lower minimum hardware requirements claimed for this helper-only change. Existing gameplay generally uses unchanged owned-depth shaders. Full Xenos retirement remains active/incomplete.

### Terrain branch live 1x and fallback validation (2026-09-07)

- Previous turn classified as progress: thread attribution ruled out assuming all process CPU variance was pipeline work. This iteration completes two correctness gates for diagnostic branch pair 26F2ADBDB365BE55D56CDC66ADB8A3E453AF3BBAA2F2DE94C853EFDA6368CB6B.
- Live1x `terrain-branch-live-1x-rdc`, PID38920 normal exit. `terrain-branch-live-1x-active-parity/report.json` explicitly asserts branch VS8167C441 and material PS4F5188F2 bytecodes active, then replaces BOTH with original guest shaders (1x PS2A082D21; original VS26BD8517). 30 terrain draws,256368 vertex bytes and1258291200 target sample bytes all EXACT. This is live1x activation proof, not merely prototype substitution. Original double-fetch native pair previously passed live2x; branch pair has2x prototype parity but branch-specific live2x capture still pending.
- Forced native creation failure diagnostic `terrain-branch-forced-fallback.cpp` inserts E_FAIL only for the qualified terrain pair before native PSO creation. DLL8A45FFD3B19A4A558F1E248D7DD7D6FABE35E7B9797EB11AA0C6142B3D68B83D; `terrain-branch-forced-fallback-build.log`. Original shaders load lazily and fallback PSO creation returns HRESULT0, VSmod3F/PSmod16003F, both translations true. Run PID50064 normal exit. Evidence and captured runtime log in `terrain-branch-fallback-smoke`.
- Diagnostic sources and generated VS header restored to baseline after diagnostic build. F1D8AB baseline staged again and rebuild recorded in `terrain-validation-reverted-build.log`; forced-failure condition must not be retained. Candidate remains disabled pending performance retention decision and outstanding branch live2x proof. No full retirement or lower requirements claim.

### Terrain CPU attribution (2026-09-07)

- Previous turn was progress: explicit fetch branching preserved exact parity and narrowed the performance gap. This turn sampled per-thread CPU to test whether native pipeline setup explains the residual process CPU increase.
- Reusable diagnostic scripts `terrain-thread-cpu.ps1` and `summarize-terrain-thread-cpu.py`; two runs B1 PID46932 then A1 PID38924, normal exits. Same branch candidate 26F2ADB and F1D8AB baseline. GetThreadDescription via limited-query handles; per-thread user/kernel/total CPU sampled each second with process CPU. No source runtime instrumentation. All observed process CPU in the 34-46second windows was accounted for by matched threads.
- `terrain-thread-cpu-summary.json` and `terrain-thread-cpu-attribution.json`: candidate process 3.139935 CPU seconds/wall second vs baseline 3.029653 (+3.6401%). GPU Commands total 0.876780 vs0.865018, accounting for about10.67% of aggregate delta. Its user CPU decreased0.009241 while kernel increased0.021003. Guest thread handle F8000054 total increased0.062609, about56.77% of aggregate delta. Handle is NOT the guest entry address: xthread.cpp names threads with host ID and kernel object handle. Exact guest function role is not established.
- `terrain-thread-cpu-workload.json`, last900nonzero frame rows: candidate3450.92 vsbaseline3275.55 draws (+5.35%), vertices1653196 vs1622958 (+1.86%), simulation tick count2.04222 vs1.94778 (+4.85%), GPU frame16.9874ms vs16.1931ms (+4.90%). These frame windows do not exactly align with CPU34-46seconds; do not normalize one by the other or claim causation. Workload differs and thread samples are one diagnostic pair, not proof of a CPU regression caused by native pipeline code.
- Do not implement speculative repeated-binding/state-construction fixes: admitted native scenes already skip second state construction and bindings are initialized on cache misses only. Stronger aligned workload/thread or stack evidence is needed to target CPU changes. Candidate remains disabled pending live activation/fallback validation and convincing performance retention evidence.
- Restored staged F1D8AB baseline after diagnostic; source/artifact unchanged baseline. No game remains running. Full Xenos retirement remains active/incomplete.

### Terrain fetch branch investigation (2026-09-07)

- Previous turn classified as progress: native pair parity established, measured regression rejected. This iteration found a concrete compiled shader cost: ternary SRV/UAV fetch helpers flatten to BOTH resource loads then selection. Original guest DXBC branches first.
- Diagnostic `terrain-branch-vertex.hlsli` changes three shared-fetch helpers to explicit [branch] if/else. `terrain-branch.vs.hlsl` includes that helper. DXBC SHA256 8167C4418D2AA3F1D261D3937089A269CC045D12C59FF5837550B9FE01BCFC0A. `check-terrain-branch-loads.py` checks seven mutually exclusive SRV/UAV pairs in compiler disassembly, no unconditional raw loads, ten temporary registers (previous native eleven). Static instruction slots increase 479 to 494; instruction count alone is not a timing estimate.
- Exact combined replay with warning-free native material PS: `terrain-branch-parity/report.json` 2x18 draws/175168 vertex bytes/3019898880 target bytes; `terrain-branch-1x-parity/report.json` 1x16 draws/136640 vertex bytes/671088640 target bytes. All exact against original shaders. Prototype replay, not live activation proof.
- Diagnostic DLL 26F2ADBDB365BE55D56CDC66ADB8A3E453AF3BBAA2F2DE94C853EFDA6368CB6B in `terrain-branch-candidate.dll`; uses terrain-pair source snapshot with branch VS header. Pipeline source/header and VS header restored immediately after build. This diagnostic only changes lit VS bytecode; existing depth variants are unchanged. Production shared helper is unchanged.
- `terrain-branch-abba-summary.json`: A1 PID22364, B1 PID18620, B2 PID35588, A2 PID44340, all normal exits. Versus F1D8AB baseline CPU +4.22338%, median +0.41604%, p95 +0.49555%, private memory -0.73845%, working set +0.85803%. Workload draw +1.33057%, vertex +0.45822%, GPU time +0.37878%. Separate batch from earlier pair, not a controlled direct comparison to E23439. No CPU or hardware requirement improvement proven; candidate remains disabled and F1D8AB staged.
- Inspection: ConfigurePipeline skips its second GetCurrentStateDescription for admitted native_scene and prepares bindings only on cache miss. Do not assume per-draw binding setup or duplicate state construction for admitted draws. Rejected coarse family candidates can construct state twice; profile/count before changing this.
- Next: isolate remaining CPU difference and/or measure branch candidate directly against prior pair; live native activation and fallback checks required before retaining integration. Shared helper updates require regenerating/validating affected depth variants. Full Xenos retirement remains active/incomplete.

### Terrain pair performance rejection (2026-09-07)

- Full terrain VS+PS candidate E23439FB7664DB347188E17727D8EEC0B731FC2A926D117953778D287A61583F passed live 2x exact parity but failed the performance retention gate. Runtime integration was reverted bytewise to `before-terrain-pair` pipeline source/header, native-clear F1D8AB baseline staged again. Native terrain HLSL/bytecode and isolated candidate snapshot remain available; neither standalone C347 nor the terrain pair is admitted in production.
- `terrain-pair-abba-summary.json`: A1 PID18784, B1 PID30032, B2 PID22036, A2 PID48724, all normal exits. Candidate CPU +5.01384%, median frame +1.74983%, p95 +6.98289%, private memory +0.12472%, working set +0.54516%. Workload draws +2.29285%, vertices +1.64271%, GPU time +3.58861%. Limited stationary 2x run, not a hardware requirements measurement; workload differs, but there is no evidence to retain this candidate for performance.
- Do not repeat unchanged benchmarks or enable the pair on parity alone. Investigate shader cost / geometry access before proposing another candidate. Live 1x and forced-failure tests were deferred after rejection, not claimed complete.
- `terrain-pair-source/files.json` preserves the integrated candidate and compiled gate/binding/override checks. Production checks restored for baseline, with a retained scene-fallback gate assertion. Reverted build log: `terrain-pair-reverted-build.log`.
- Full Xenos retirement remains active/incomplete. Progress this iteration: validated material pair and rejected a measured regression; no hardware-requirement reduction claimed.

### Terrain material pair integration (2026-09-07, validation in progress)

- Integrated C34795A841E7DEFF/mod3F VS with 21B70A5E4C9CFD11/mod16003F PS only, bindless host targets at uniform 1x/2x. Standalone C347 VS remains rejected. Preserved asynchronous pipeline creation and lazy guest fallback.
- Candidate DLL E23439FB7664DB347188E17727D8EEC0B731FC2A926D117953778D287A61583F, `.local/native-renderer/terrain-pair-candidate.dll`. Production source snapshot `terrain-pair-source/files.json`; prior pipeline files in `before-terrain-pair`.
- Pixel DXBC is byte-identical to warning-free validated prototype 4F5188F2F52CFAF8DB33D5C91FD9C3B396F1DECDEC04C5EA553D5EF8556A30E4. Exact guest texture/sampler metadata installed, both native shaders selected in final scene override.
- Build successful; compiled admission/bindings/override and shadow checks passed; 51 pack/renderer/release/render-test unit checks passed.
- Live 2x capture `terrain-pair-rdc`, PID43892 normal exit. `terrain-pair-active-parity/report.json` asserts BOTH native bytecodes active, substitutes both original shaders: 10 terrain draws, 127232 vertex bytes and 1677721600 target sample bytes EXACT. This supplements earlier 1x/2x prototype combined parity, not a live 1x proof.
- ABBA versus F1D8AB native-clear baseline running; performance retention decision, live 1x proof and forced failure validation still pending. Xenos retirement goal remains active/incomplete.

### Warning-free terrain material and combined pair parity - 2026-09-07

Previous turn made progress implementing/validating material PS prototype.
Production remainsF1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F;
no production source/runtime admission changed this turn. No live game/replay.

Resolved FXC X4000 warning by replacing short-circuit AlphaTest return with
an explicit8-way comparison switch. No suppression. New source
terrain-material-alpha-fixed.ps.hlsl; bytecode terrain-material-alpha-fixed.dxbc,
SHA2564F5188F2F52CFAF8DB33D5C91FD9C3B396F1DECDEC04C5EA553D5EF8556A30E4.
This supersedes prior material prototypeF2540744 for future integration.
FXC /Tps_5_1 /Emain /O3 /enable_unbounded_descriptor_tables compiles cleanly.
Actual extracted AlphaTest compiled in terrain-material-alpha-check.cpp/.exe:
512 combinations across all8 comparisons and values including NaN,+/-inf,
signed zero and finite values pass. NotEqual preserves unordered behavior.

Combined replay now replaces BOTH VS and PS, unlike prior separate-stage
proofs. VS uses validated c347-native.dxbc2FA413C9; PS new4F5188F2.
terrain-combined-alpha-fixed-parity.py/report.json:18 draws175168 vertex
bytes and3019898880 full target bytes/all MSAA samples EXACT at2x.
terrain-combined-alpha-fixed-1x-parity.py/report.json:16draws136640 vertex
bytes and671088640 target bytes EXACT at1x. Report shader_variants counts PS
replacements only; script separately replaces the vertex_shaders set as well.
These remain prototype replay evidence, not live selection or speed claims.

NEXT integrate narrow FULL PAIR C34795/mod3F +21B70/mod16003F, bindlesshostRT
and equal1x/2x. Keep reverted standalone VS admission disabled. Pipeline cache
integration points inspected: IsFh1NativeScenePipeline, PrepareFh1SceneBindings
(exact6textures/3samplers/mask8198 from terrain-material-modifications.json),
ConfigurePipeline candidate list and async exclusion, prewarm pair exclusion,
explicit native bytecode selections (including final scene override). Avoid
repeating the earlier position-stage override bug. Existing native-scene
fallback machinery can load both original stages on demand. Reuse validated
terrain VS source/header already present in repo, add clean PS source/header.
Then compiled gate/binding checks, build, live native identity/output parity,
forced fallback, and benchmark combined pair versusF1D8AB36. Standalone81CA
regression remains relevant; cannot claim combined speedup without measurement.
Full Xenos retirement and lower requirements remain active/incomplete.

### Native terrain material PS prototype passes both scales - 2026-09-07

Previous turn made progress testing/reverting standalone VS performance.
Production remainsF1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F;
C347 standalone runtime admission remains disabled. No production edits this
turn, no running game/build/replay. Goal active/incomplete.

New LOCAL prototype: terrain-material-native.ps.hlsl / terrain-material-native.dxbc,
SHA256F254074450456752D8C9ECF02153529BBBD4CCEBB28AD3D26A9201CADFA6CEE8.
Reimplements21B70A5E4C9CFD11 material shader (guest ops6-56), preserving
lighting/specular/fog, coarse gradients, signed/gamma sample decode/exponent,
conditional cube fetch1/2 selected by bool130, 2D fetch13, alpha test and
coverage, color exponent. Adapted existing shadow ALU/decode and constant-blend
alpha helpers. AlphaTest explicitly handles NotEqual NaN semantics. Added
cube face-coordinate conversion and normalized cube sampling from original
DXBC behavior; no fixed captured textures or colors. Generic bindless ABI.
FXC ps_5_1/O3 requires /enable_unbounded_descriptor_tables. Emits X4000 at
AlphaTest return (potentially uninitialized); investigate before production,
do not silently suppress it. Initial compile lacked unbounded flag, corrected.

InputsTEXCOORD1/2/4 centroid;0/3/5 linear. b0system30uint4,b1constants17float4,
b2bool/loop10uint4,b3fetch48uint4,b4descriptor3uint4. Constants guest order:
42,43,47,57,59,113,124,125,126,127,156,157,159,168,169,254,255.
Native uses existing bounded descriptor arrays, not owned material resources yet.

terrain-material-native-parity.py/report.json: original VS retained, only PS
replaced;18draws3019898880 target bytes/full MSAA samples EXACT at2x.
terrain-material-native-1x-parity.py/report.json:16draws671088640 target bytes
EXACT at1x. Vertex data also unchanged. Pixel bytecode digest report fields
renamed pixel_sha256 (adapted checker had initially called them vertex_sha256).
These are prototype replay proofs, NOT live native selection or speed evidence.
Corpus native-clear-final-pass-profile has51 execution entries using PS21B70,
all paired with VSC34795; entry count is not draw count.

terrain-material-modifications.json enumerates both shader packs. Captured
PSmod000000000016003F at BOTH scales (2xoriginalSHAa7ef74a9...,1x2a082d21...).
Do not admit the8 other PSmods merely because bindings match. Bindings mask8198:
views(2,13,2D,unsigned),(3,13,2D,signed),(5,1,cube,unsigned),(6,1,cube,signed),
(8,2,cube,unsigned),(9,2,cube,signed). Samplers1/fetch13,4/fetch1,7/fetch2;
all min/mag/mip3,aniso7 (use-fetch constants). Exact tuples in JSON.

NEXT resolve compiler warning, then combine this PS with validated native
C347VS/mod3F as narrow full-pair admission, preserving generic pixel bindings,
async behavior, lazy fallback and preload exclusion. Standalone VS81CA6605
had a p95 regression; do NOT just re-enable unchanged standalone admission.
Require combined replay/live identity/parity and new production benchmarks.
Further owned geometry/material resources and other renderer dependencies
remain necessary for full Xenos retirement and lower requirements.

### C347 reversed benchmark: standalone runtime migration reverted - 2026-09-07

Previous turn made progress with fallback proof and first regression measurement.
This turn ran clean reversed BAAB, then reverted live admission because p95
regression persisted with comparable vertex workload. Current production
artifact/staged is AGAIN
F1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F
(native-clear-float10-candidate.dll). C347 integrated81CA6605 is NOT staged.

c347-integrated-baab.ps1 / summarize-c347-integrated-baab.py and summary.json:
all normal exits2800frames/two captures, B1PID50624,A1PID47132,A2PID40500,
B2PID11348. Candidate CPU +0.14630%, median -0.38024%, p95 +4.30105%;
private memory -0.00826%, working set +0.46557%. Draws -0.79606%, vertices
-0.04330%, guest GPU time -0.01529%. Hence vertex workload essentially matched,
but tail latency did not improve. Per-run B1/A1/A2/B2 CPU3.09997/3.07715/
3.25628/3.24272; median16.147/16.585/16.289/16.602ms;
p9519.272/19.601/19.250/21.250ms. Draws3310.26/3446.21/3382.52/3464.10.
Same2x saved scene5800X/RTX4080, CPU34-46sec,last900 nonzero frames.

c347-eight-run-summary.json preserves both orders. Combined CPU +1.33622%,
median +1.04818%, p95 +5.26269%; draw workload +3.03281%, vertices +1.56162%,
guest GPU time +1.90834%. No demonstrated speedup. This does not prove a
specific shader/GPU cause, but is insufficient to retain this isolated runtime
migration for a performance-first goal without further improvement.

Restored pipeline_cache.cpp bytewise from before-c347-integration, removing
native C347 admission, bytecode selection and include. Removed now-inapplicable
positive native-admission assertions; retained clear rejection regression.
Compiled gate passes; c347-reverted-build.log succeeds and rebuilt/staged
hash matches originalF1D8AB36. No live benchmark/game/build/replay remains.
Validated terrain-lit HLSL/header and shared terrain helpers remain in source
for further work, but new terrain-lit bytecode is currently unused. Existing
terrain-depth bytecodes remained identical after helper extraction. Native
C347 source snapshot/candidate81CA6605 and both-scale/live parity evidence
remain available, so successful correctness work is not lost.

NEXT target a broader native terrain/material or owned-geometry change that
can reduce actual work; do not re-enable the unchanged standalone vertex
migration or keep repeating the same benchmark without a new hypothesis.
Possible continuation: native21B70 PS (~54 guest instructions,2D fetch13,
conditional cube fetch1/2) or extend existing terrain-owned geometry path
while preserving pixel bindings. Full Xenos retirement remains incomplete;
this deliberate rollback does not redefine or complete the original goal.

### C347 fallback verified; first ABBA slower with higher workload - 2026-09-07

Previous turn made progress with integration/live exact2x output parity.
Current candidate/artifact/staged remains81CA6605591B50EDD53EC89F4F332EAE6C76FD141F9366DAEF1B4EA2E5A5B292.

Forced native pipeline creation failure for C347 only: diagnostic gameplay
PID46276 normal exit. c347-fallback-smoke/runtime.log and evidence.json show
one successful fallback, HRESULT0, modification3F, both VS/PS translated.
Temporary diagnostic source removed bytewise using c347-before-fallback.cpp,
rebuilt c347-restored-build.log and exact production hash verified. This
confirms lazy legacy VS recovery for the new family; no diagnostic remains.

Clean ABBA against native-clear-float10-candidate.dllF1D8AB36 completed
normally all four runs2800frames/two captures, no build/replay concurrency.
c347-integrated-abba.ps1, summarize-c347-integrated-abba.py,
c347-integrated-abba-summary.json and per-run output. PIDs A1=12840,
B1=40936,B2=49904,A2=37876. Candidate restored and hash verified afterward.

IMPORTANT: observed regression, NOT demonstrated performance improvement.
Pooled CPU +2.54094%, median frame +2.47516%, p95 +6.19968%; private memory
+0.28087%, working set +0.96218%. Candidate workload also higher: draws
+6.85753%, vertices +3.16527%, guest GPU time +3.81280%.
Per-run A1/B1/B2/A2 CPU3.17668/3.27015/3.14446/3.07898;
median16.6465/16.9330/16.7885/16.2605ms; p9520.753/21.320/21.025/19.120ms.
Draws3504.44/3667.63/3637.32/3331.72, vertices1622092/1663261/1682761/1621268.
Same2x stationary saved test,5800X/RTX4080,CPU34-46sec,last900 nonzero frames.
Do not explain away the slowdown as noise or infer per-shader cost from these
unequal scene workloads. Correctness/retirement validated, speed unproven.

NEXT reversed-order BAAB against the same baseline to test order/workload
confounding before accepting performance claims or continuing PS migration.
If slowdown persists with comparable workload, isolate cause or revert the
runtime selection while keeping proven prototype. Remaining PS21B70 is
~54 guest instructions with2D fetch13 and conditional cube fetch1/2; no
existing native cube-sampling helper found. That work remains deferred until
current performance concern is addressed. Goal remains active/incomplete.
No live game/build/replay/benchmark remains.

### Native C34795 vertex integration and live2x parity - 2026-09-07

Previous turn made progress with native terrain prototype2x parity.
New candidate/artifact/staged81CA6605591B50EDD53EC89F4F332EAE6C76FD141F9366DAEF1B4EA2E5A5B292,
c347-integrated-candidate.dll. Rollback native-clear-float10-candidate.dllF1D8AB36.
c347-integrated-source/files.json snapshots6 changed/new files;
before-c347-integration backs up prior pipeline cache and terrain-depth HLSL.

c347-modifications.json checks BOTH actual1x/2x packs: soleVS modification
000000000000003F, no textures/samplers/mask; bytecode exact reference.
1x prototype replay c347-native-output-1x-parity:16 draws136640 vertex bytes
and671088640 target bytes exact. This precedes integration, not live1x proof.

Production fh1_terrain_lit.vs.hlsl plus generated fh1_terrain_lit_vs.h selects
nativeC34795/mod3F through IsFh1NativeStandaloneVertex. Same bindless hostRT,
equal1x/2x gates; existing metadata setup/preload exclusion/async pending and
lazy native-PSO-failure fallback machinery reused. PS stays legacy. Vertex
bytecode selection added explicitly before position variant; no broad scene
native override. Shared SRV/UAV geometry remains; owned terrain buffers future.
Compiled clear/standalone gate check updated to accept exactmod3F at1x/2x,
reject wrongmod/nonuniformscale and keep C347 out of the clear pipeline.

Shared decoding/arithmetic extracted to fh1_terrain_vertex.hlsli. All FOUR
existing terrain-depth shader variants recompiled byte-identical to existing
headers, and new integrated VS byte-identical to validated prototype2FA413C9.
No existing shader headers changed. Packed-world fallback regression and
51contract tests pass. Build c347-integrated-build.log succeeds13warnings.

Live capture c347-integrated-rdc PID39140 normal exit. Startup loads489legacy
variants (previous490). c347-integrated-active-parity.py/report.json asserts
actual VS bytecode equals c347-integrated.dxbc on every selected draw, then
replaces native VS with original to compare outputs. 32 draws,
370496 vertex bytes and5368709120 full target bytes/all samples EXACT at2x.
No running game/build/replay. Current production candidate remains staged.

NEXT forced nativePSO-failure smoke to verify lazy VS fallback for this family,
then clean production ABBA againstF1D8AB36. Performance not measured for this
candidate; no CPU/minimum-hardware claims. Continue native PS/owned geometry
and remaining shader/resource/command dependency retirement. Goal active/incomplete.

### C34795 native terrain vertex prototype passes2x replay parity - 2026-09-07

Previous turn made progress measuring transfer overlap and correcting timing.
Current production artifact/staged remainsF1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F.
No production source changed this turn. No running game/build/replay.

c347-world-audit.py/report.json examines native-clear-float10-parity-rdc;
all draw commands mapped to active PSOs using command-list Reset/SetPipelineState,
rejecting unsupported indirect/bundle state. C34795A841E7DEFF is only18 draws
in this frame, one VS variant/one PS pairing21B70A5E4C9CFD11. Thus it does
NOT account for entire118-draw mixed pass timing from prior profiling.
Vertex-529/Pixel-598 DXBC and disassemblies saved; output stride112 bytes.
Existing guest ucode under v5-04-5a28-dump/shader_C34795A841E7DEFF.ucode.vert.
It is a68-instruction terrain shader,28-byte packed primary data plus
4-byte optional direction and32-byte control-grid fetches. Reuses decoding
and Fh1Mul arithmetic from production fh1_terrain_depth.vs.hlsl.

New LOCAL PROTOTYPE ONLY: .local/native-renderer/c347-native.vs.hlsl,
c347-native.dxbc. Compiled FXC vs_5_1/O3, hash
2FA413C97F7114BD03D00962954F2788E225A3115586B8F30F505917621DD340.
Original VS hash26BD8517C95962557EC8D6B0B57829A0A460FD1E53372F62DA8C8EEEA0E9E097.
Prototype explicitly computes all6 float4 interpolators and position,
preserves separate multiply/add rounding, guest zero multiplication,
endian/index rules, conditional direction, grid interpolation, quaternion
normalization, transforms and NDC. Uses existing bounded shared SRV/UAV;
owned buffers not yet implemented. Packed b1 constants25 in guest order:
0,1,2,3,8,9,10,11,12,13,14,36,37,38,39,40,41,42,58,116,124,126,127,254,255.

c347-native-vertex-parity.py/report.json:18 draws175168 vertex bytes exact.
c347-native-output-parity.py/report.json:18 draws, same175168 vertex bytes
and3019898880 render-target bytes across all samples EXACT after native VS
resource replacement. Pixel shader remains original. These are2x replay
prototype proofs, not live integrated native selection/performance evidence.
Initial replay script indentation error fixed and syntax compiled before
rerun; failed qrenderdocPID39128 explicitly stopped, no capture was running.

NEXT1x prototype parity using valid1x capture, map exact active shader-pack
modification/bindings, then integrate narrow native VS admission, metadata,
preload exclusion, async behavior and lazy PSO-failure fallback. Reuse existing
terrain helpers where appropriate without changing validated variants.
Require live native-byte identity/output checks and production benchmark.
Remaining PS and other shader/resource/command dependencies still need
retirement. Full original goal remains active/incomplete.

### Clear transfer audit and timing-attribution correction - 2026-09-07

Previous turn made progress with profiling. This turn traced scheduling and
measured transfer/clear overlap before implementing deferred transfers.
IMPORTANT correction: IssueDraw calls RT Update around3004, but
ObserveFh1GpuPassTimingDraw around3325 starts/closes pass timestamps afterward.
Thus transfers preparing the NEXT attachment can fall inside the PREVIOUS
pass interval. The0.37-0.41ms clear-family timings are not isolated clear
preparation costs. Do not use them to rank a transfer-skipping rewrite as
proven high impact. Existing profile remains useful with this limitation.

Temporary ClearFh1Rectangles logging inspected actual last_update_transfers,
GetRectangles and clear bounds every60 host frames after2000. GameplayPID44708
normal exit. Preserved native-clear-transfer-audit-run/runtime.log and
report.json:216 target records in8 retained sampled frames,208 have transfers.
Log rotation means this is a retained sample, not the full gameplay run.
Unscaled transfer rectangle area165928960 pixels; geometric clear overlap
21221888 pixels. Only13279232 pixels (8.00296%) overlap clears that overwrite
all components (color, or both depth AND stencil). Partial depth/stencil
clears must preserve the other component. Areas are not weighted by MSAA,
format, transfer shader complexity, or bandwidth; not measured GPU savings.
Many depth-only clears transfer large regions outside the cleared rectangle;
several transfers have zero intersection. Some full color/depth+stencil
clears do cover whole transfer rectangles, so a narrowly proven cutout path
may still help, but a broad scheduling rewrite is not yet justified by timing.

Temporary logging removed bytewise via native-clear-transfer-audit-source.cpp,
rebuilt native-clear-transfer-audit-restored-build.log. Production artifact/
staged hash verified unchangedF1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F.
No live game/build/replay. No production behavior changed this turn.

NEXT prioritize remaining shader/resource retirement with correct timing
scope, or first isolate actual transfer cost before changing its scheduling.
Known remaining mixed families beginC34795/21B70 and984D/6FDA. Do not ascribe
whole mixed-pass cost to the first shader. If implementing clear cutouts,
preserve cross-target transfer dependencies, all rejection/early-return
paths, uncleared pixels, and unwritten depth/stencil; existing resolve cutout
support can be reused only after those proofs. Goal active/incomplete.

### Production reprofiling after all21 native clears - 2026-09-07

Previous turn made progress with1x parity and full-clear ABBA. Current
production hash remainsF1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F.
New pass inventory gameplay PID22444 normal exit, native-clear-final-pass-profile
contains preserved runtime.log, corpus.json and summary.json. Parser recipe
summarize-native-clear-final-profile.py uses production PASS_FAMILY regex,
selects current session, latest aggregate per family, joins first-draw metadata.
Corpus19790 keys2646 passes, overflow0, collisions0; pass_collisions118928.
No live game/build/replay. No production source changed this turn.

Representative multi-draw families:53B2C36308FCD21914 samples811drawavg1.2414ms
(first8D8A/BA6A, mixed pass);8F17E2B502A6BF6215samples3drawavg0.9598ms
(firstshadowA3B9/9362);1C19836DCEF7AFE115samples118drawavg0.7487ms
(firstC34795/21B70);7C6A3248DE68D14215samples94drawavg0.6406ms
(first984D/6FDA);DFA1909F80A8082615samples437drawavg0.5883ms
(firstCA293/noPS). First shader does NOT attribute every draw in a mixed pass.
Single-clear families still expensive: F9ACFE31BE30EAFE14samples0.4114ms,
57294A9E0311F16315samples0.3907ms,ED7F805DBDC5C23630samples0.3873ms,
826B5BC82A05EB6217samples0.3740ms. These aggregate elapsed GPU times are not
isolated API-clear timings; do not claim clear instructions themselves cost this.

Next optimization lead: render-target ownership transfers before native clear.
IssueDraw calls RT Update around3004, then prepares pipeline/systemconstants,
and only attempts ClearFh1Rectangles around3558. D3D12RT Update1004 calls base
Update, then PerformTransfersAndResolveClears and binds targets. Thus native
clear currently does not omit old-content transfers. Base Transfer already
supports rectangular cutouts via GetRangeRectangles/GetRectangles; resolve
clear path uses these through ChangeOwnership and PerformTransfersAndResolveClears.
Inspect this existing mechanism before adding another abstraction.

Potential implementation: defer transfer execution for clear candidates until
all clear semantics are qualified, then omit transfer regions overwritten by
the clear; flush unchanged transfers on every rejection/fallback path. This is
an unimplemented design lead, not a proven bottleneck or safe patch yet. Must
trace all intervening GPU operations/early returns, RT binding/ownership and
preserve uncleared pixels plus unwritten depth/stencil components. Existing
resolve clear API includes actual clear-value emission, so do not blindly pass
its rectangle pointer to reuse cutouts. Validate exact parity and benchmark.
Remaining non-clear shader families/resource/command dependencies still need
retirement. Original goal remains active/incomplete.

### All21 native clears:1x parity and full production ABBA - 2026-09-07

Previous turn made progress extending float10 clears and proving2x parity.
Current candidate/artifact/staged remains
F1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F.

Actual same-input1x runtime parity now passes21 markers,417054720 bytes
across full targets/all samples, ALL EXACT. native-clear-float10-parity-1x-rdc,
PID25736 normal exit; native-clear-float10-same-input-1x-parity.py/report.json.
Temporary instrumentation removed bytewise, rebuilt (restored-1x-build.log),
and production hash verified before benchmark. Together with prior2x run,
all21 captured replacement draws have exact parity at both supported scales.

Clean production ABBA compares this candidate against pre-clear
position-pixel-fixed-candidate.dll695E0C66, not the14-clear intermediate.
native-clear-float10-abba.ps1; summarize-native-clear-float10-abba.py;
native-clear-float10-abba-summary.json, per-run process-samples and output.
All four normal exits2800frames/two captures: A1 PID46568, B1 PID43428,
B2 PID47440, A2 PID41568. No capture/replay/build concurrent with benchmark.

Pooled candidate change: CPU -3.12775%, median frame -0.49098%, p95 -7.55418%,
private memory +0.68264%, working set +0.85411%. Draw workload +6.70200%,
vertices +1.47380%, guest GPU time -0.25306%.
Per-run A1/B1/B2/A2 CPU3.17063/3.13723/3.17351/3.34386;
median16.8145/16.7070/17.0385/17.0975ms; p9520.944/20.591/21.984/25.110ms.
Draws3532.97/3753.18/3725.82/3476.26. CPU34-46sec, last900 nonzero frames,
same saved stationary2x test,5800X/RTX4080. CPU result favorable despite
higher candidate workload, but temporal drift remains; p95 improvement is
heavily driven by slow final baseline. No new minimum hardware claim.
Candidate restored after ABBA and hash verified. No live game/build/replay.

NEXT reprofile production to prioritize remaining non-clear native renderer
families (prior shadow-final-pass-profile is now stale for clear costs).
Continue retirement of remaining shader/resource/command dependencies;
all21 captured clear draws is not full Xenos retirement or game-wide coverage.
Original goal remains active and incomplete.

### All21 captured rectangle draws lowered to native clears at2x - 2026-09-07

Previous turn made progress with1x parity and seven remaining-draw audit.
Resource names in native-clear-remaining-audit/report.json now establish all
seven use guest k_2_10_10_10_FLOAT (not the previously suspected fixed16).
GetColorResourceDXGIFormat maps this guest format to R16G16B16A16_FLOAT;
GetColorDrawDXGIFormat falls through to that same format. Existing exact
native position/passthrough shaders and color exponent handling still apply.

Added ONLY k_2_10_10_10_FLOAT to both IsFh1ClearPipeline and
ClearFh1Rectangles format guards. Other gates unchanged. Updated compiled
check-fh1-clear-pipeline.py admits this format at1x/2x/4x MSAA and rejects
an unsupported format. Full51 contract tests pass. before-native-clear-float10
backs up preceding pipeline/RT source; native-clear-float10-source stores new
production pipeline/RT source and RT header. Base other files remain4E0B00F2.

NEW production candidate/artifact/staged:
F1D8AB362A6F962E3051285FEA4A01612EABF58B8199887CC1E47B0AD2FB647F
native-clear-float10-candidate.dll. Rollback native-clear-candidate.dll4E0B00F2.
Builds native-clear-float10-build.log and restored-build.log pass16 warnings.
Temporary backup/clear/restore/original-draw instrumentation removed bytewise
and rebuilt, staged hash matches candidate. No game/build/replay remains.

Actual same-input runtime2x parity: native-clear-float10-parity-rdc, gameplay
PID50248 normal exit, native-clear-float10-same-input-parity.py/report.json:
21 markers,1668218880 bytes across full targets/all samples, ALL EXACT.
All21 captured1E6883 rectangle draws now emit native API clears in the
diagnostic run. This is not a claim every rectangle draw in the game is known.
Preparation recipe prepare-native-clear-float10-diagnostic.py under.local
asserts current production backups before temporary instrumentation.

NEXT validate new candidate same-input1x (prior14-only candidate passed1x),
and benchmark expanded production candidate. Prior ABBA pertains4E0B00F2,
not this new binary. Then move to remaining non-clear renderer families and
Xenos resource/command dependencies. Full goal remains active/incomplete.

### Native rectangle clear1x runtime parity and remaining-draw audit - 2026-09-07

Previous turn made progress with production ABBA. This turn completes actual
same-input1x runtime parity:14 clear markers,186368000 bytes, ALL EXACT.
Gameplay PID46576 normal exit, native-clear-parity-1x-rdc;
native-clear-same-input-1x-parity.py/report.json. Same backup/native-clear/
restore/original-draw method and restoration/intervening-write checks as2x.
Combined actual runtime comparison:2x745472000 plus1x186368000 bytes.
Compiled helper checks pass48 captured rectangles and144 captured vertices.

prepare-native-clear-1x-diagnostic.py now preserves a reproducible temporary
instrumentation recipe under.local only. It asserts production source equals
native-clear-parity-source backups before editing. All diagnostics removed
bytewise afterward; native-clear-restored-1x-build.log succeeds. Production
artifact/staged hash verified4E0B00F2CF0BF7626EFF6C47D4B4DC2F17A527757862ADF479C9B2B0C74BF9E1.
No live game/build/replay remains. Do not ship the diagnostic recipe's build.

native-clear-remaining-audit.py/report.json inspects the actual production
native-clear-rdc capture: exactly7 remaining1E6883 draws at6867,6931,10151,
28075,28601,28792,28869. All have constant-color rectangle vertices and
R16G16B16A16 host float targets, full writes, no blend/cull/depthclip/bias.
First4 have Always depth/write and Replace stencil; last3 disable depth and
stencil. This does NOT identify the runtime rejection reason: guest format,
query state, CPU ownership and other gates still require inspection. Disabled
host depth does not imply a pipeline-gate issue: description canonicalizes
unused depth_func to Always (pipeline_cache.cpp2669-2713).

NEXT determine the actual rejection for these7 draws, especially guest color
format versus the admitted k_16_16_16_16_FLOAT (host float format alone does
not establish guest format). Instrument exact gate reasons if necessary;
do not relax guards based solely on matching host formats. Then extend and
validate replacements where semantically valid. Full Xenos retirement and
lower requirements remain the active incomplete goal.

### Native rectangle clear production ABBA - 2026-09-07

Previous goal turn made progress: actual same-input2x runtime clear parity.
This turn measured production performance, without diagnostic/replay/build
processes concurrent with the benchmark. Candidate4E0B00F2 versus preceding
position-pixel-fixed-candidate.dll695E0C66. All four runs normal exit at2800
frames/two captures: A1 PID47552, B1 PID43860, B2 PID46932, A2 PID47932.
Artifacts: native-clear-abba.ps1, summarize-native-clear-abba.py,
native-clear-abba-summary.json and native-clear-abba-{a1,b1,b2,a2}.
Staged DLL restored and hash verified4E0B00F2 after the final baseline.

Candidate pooled changes: CPU seconds/wall second -1.21835%, median frame
-0.28152%, p95 -1.97435%, private memory -0.49341%, working set -0.99984%.
Workload: draws -1.48118%, vertices -0.01163%, guest GPU time -1.13435%.
Per-run A1/B1/B2/A2 CPU3.17406/3.15290/3.04430/3.09957;
median16.6195/16.5775/16.5420/16.5935ms; p9520.004/20.078/19.741/20.617ms.
Draws3542.38/3468.05/3413.45/3442.59; vertices1641729.65/1636953.41/
1647070.29/1642676.06. Same stationary saved-game test and2x settings;
CPU window34-46seconds, last900 nonzero frame times,5800X/RTX4080.

Small favorable differences in this sample; no demonstrated large speedup
or new minimum hardware requirements. Draw workload drift remains relevant;
vertex workload is nearly unchanged. Keep the candidate for native retirement.
NEXT:1x same-input runtime clear parity, then investigate the remaining
unreplaced rectangle draws and proceed with further renderer retirement.
The original goal remains active and incomplete. No live benchmark remains.

### Native rectangle clear same-input runtime parity - 2026-09-07

Production candidate/artifact/staged remains 4E0B00F2CF0BF7626EFF6C47D4B4DC2F17A527757862ADF479C9B2B0C74BF9E1.
All temporary diagnostic source removed bytewise and rebuilt; staged hash
matches native-clear-candidate.dll. No game/build/replay remains running.

Capture-only diagnostic backed up each affected target into a matching D3D12
resource, ran native clears, restored the original contents, then returned
false to execute the original draw. Backups held original resources alive
and reused one backup per target, with explicit COPY_SOURCE/COPY_DEST and
render/depth state transitions. Diagnostics retained only under
.local/native-renderer/native-clear-parity-source (production source backups)
and native-clear-parity-build.log; they are not in the production build.

Gameplay PID48752 normal exit, capture native-clear-parity-rdc.
native-clear-same-input-parity.py/report.json validates14 native markers,
745472000 bytes across full targets/all MSAA samples at2x: ALL EXACT.
It verifies paired backup/restore copies and byte-identical restored contents
before the reference draw, and asserts the reference uses the native position
VS. Two intervening CopyBufferRegion events write shared buffer ResourceId317,
not a compared render target. No intervening compared-target writes admitted.
This is actual same-input API-clear versus original-draw runtime parity,
not the weaker clear-then-draw idempotence check. Unwritten target bytes and
samples are included. Restored production clear-pipeline and CPU-snapshot
compiled checks pass. native-clear-restored-build.log succeeds.

NEXT capture/validate the same diagnostic at1x, then run clean production
ABBA against position-pixel-fixed-candidate.dll695E0C66. Performance has NOT
been measured for this candidate. Do not claim reduced requirements yet.
14 accepted markers do not retire all21 original family draws; investigate
remaining guards after parity/performance. Overall Xenos retirement remains
incomplete and the goal remains active.

### First runtime native rectangle clears emitted - 2026-09-07

EXPERIMENTAL candidate/artifact/staged 4E0B00F2CF0BF7626EFF6C47D4B4DC2F17A527757862ADF479C9B2B0C74BF9E1.
native-clear-candidate.dll; rollback position-pixel-fixed-candidate.dll695E0C66.
native-clear-source/files.json snapshots12 files; before-native-clear preserves
preceding command processor/pipeline cache/render target source and headers.
Runtime clear output parity and performance are NOT yet proven.

IsFh1ClearPipeline qualifies exact1E6883 vertex variants/early-color PS pair,
rectangle GS, no culling/wireframe/depthclip/bias, depthAlways, full replace
stencil, no partial/sample fallback or blending, only supportedRT0 color
formats. Compiled production gate test check-fh1-clear-pipeline.py exercises
rejections. Existing packed/shadow tests and51 contract tests pass.

IssueDraw clear attempt follows target ownership/transfers, viewport/scissor
and UpdateSystemConstantValues, before guest constant uploads/residency. Guards
queries (legacy and modern), memexport,3/6 nonindexed rectangle vertices,
alpha-to-mask and pipeline state. Requires zero index offset/endian/minimum,
valid maximum/closing index, vertex fetch type3 and CPU snapshot. Decode28-byte
stride0/endian from fetch0, use validated vertex/rectangle helpers, require
constant colors perrectangle, apply color exponent. Float24-conversion cases
only admit computed depth0. All rectangles validate before native emission.
SystemConstants is468 bytes: copy into zeroed480-byte array, not past source.

D3D12RenderTargetCache::ClearFh1Rectangles prevalidates target/format/value
requirements, uses accumulated target descriptors, transitions and submits
barriers, clips to resource bounds, then emits ClearRenderTargetView and/or
ClearDepthStencilView per rectangle. No new GPU geometry allocations/uploads.
Empty clipped rectangles do nothing. Unsupported cases retain original draw.
Build native-clear-build.log succeeds16 warnings.

Live capture PID3832 normal, two captures/frame2800. native-clear-rdc and
native-clear-audit/report.json contain14 native markers and19 actual clear
commands. This confirms runtime emission only, not output parity;7 of21 prior
family draws are not established as replaced. No claim all draw clears retired.

NEXT establish same-input runtime output parity. A useful diagnostic oracle:
backup affected target contents before native clears, issue native clears,
restore exact pre-clear contents, then execute original draw. RenderDoc can
compare native-clear event target bytes to original-draw event bytes on the
same resource and original input state. Mere clear-then-draw idempotence is
insufficient (can hide under/over-clear); avoid that weaker substitute. Keep
backup resources alive through submissions and reuse them with correct state
barriers. Remove diagnostic changes and rebuild/verify production hashes before
benchmarking. Investigate declined draws after parity. Full goal active.

### CPU clear snapshot and vertex transform qualified - 2026-09-07

Staged runtime remains695E0C66. Added source helpers, not yet wired into native
clear IssueDraw path. Build clear-snapshot-build.log succeeds13 warnings;
artifact now2AEE4781EB863ED310496346F23C69618A02226E5FD4E3053F71107AC8B06EC0, NOT staged. Do not
assume artifact/staged match until next integrated build is staged/validated.

SharedMemory::CopyCpuSnapshot arms a one-shot invalidation watch under global
lock, releases lock for CopyCpuRange (preserving heap/global lock ordering),
then re-locks to reject invalidation and clean up surviving watch. Reads of
watch handle are all locked. Rejects GPU-authority through existing CopyCpuRange,
bounds and allocation failures; destination must be discarded on false.
No GPU allocation/upload/readback. Caller still supplies admitted geometry range.
Files shared_memory.h/.cpp; new tools/check-fh1-cpu-snapshot.py compiles actual
method against lock/watch mock and tests pre/post-copy invalidation, failure,
cleanup, empty/overflow ranges. Passes. Existing check-fh1-cpu-source.py extraction
boundary updated to stop at new method; actual CPU authority/extent/unchanged-
output tests pass. No existing CopyCpuRange behavior changed.

fh1_clear.h now also supplies fh1_clear_vertex for exact1E6883 fetch decode:
28-byte input, endian0-3, position.w1, separate float MUL then explicit NDC
FMA, color passthrough when used. Rejects nonfinite/subnormal inputs/intermediates
and invalid endian. It assumes caller has already proved index and range;
shader/stencil/primitive/memory visibility still require runtime qualification.

position-clear-inputs.py extracts2x capture raw28-byte shared-memory source per
vertex, actualsystem120words/fetch0, hostindices and postVS bytes.1x counterpart
position-clear-1x-inputs uses valid1x capture. All21 draws each are nonindexed,
3 or6 vertices;72 source vertices per scale. tools/check-fh1-clear.py --inputs
accepts these reports and compares actual compiled CPU helper output by memcmp
with captured postVS bytes. Combined --audit and --inputs invocation passes
48 rectangles and144 vertices across both scales. No output hash inferred from
shader names; raw source/constant and postVS bytes are evidence.

NEXT wire exact clear qualification into IssueDraw after target update using
watched CPU snapshot, vertex helper and rectangle helper, then expose emitter
on D3D12RenderTargetCache using accumulated targets and existing barrier/
descriptor patterns. Initially require observed nonindexed rectangle form,
exact shadermods and raster/depth/stencil/format state; reject query/memexport/
GPU-written or invalidated source. Run actual native-clear capture comparisons
and performance. Mathematical predictions and CPU helper equality do not yet
prove live native-clear execution. Full renderer retirement remains active.

### Compiled clear rectangle lowering and runtime flow traced - 2026-09-07

Production DLL unchanged695E0C66. Added SDK include/rex/graphics/d3d12/
fh1_clear.h with fh1_clear_rectangle: three post-VS rectangle-list corners,
viewport/depth/scissor -> clipped integer bounds and clamped constant depth.
Requires finite normal-or-zero input components, w1, constant depth, three
unique corners of an axis-aligned rectangle, and integral screen coordinates.
Uses64-bit scissor arithmetic; completely clipped rectangles become empty.
Shader, raster/stencil state and memory visibility remain caller obligations.
This helper is NOT yet wired into IssueDraw; no native clear runtime claim.

Runnable tools/check-fh1-clear.py compiles production helper, exercises bad
geometry/nonfinite/fractional/variabledepth/w/scissor-overflow cases, and accepts
--audit captureJSON repeatedly. Ran with position-clear-expanded-audit and
position-clear-expanded-1x-audit: all48 rectangles across42 draws pass (24 per
scale). Expected rectangle/depth values derived independently from captured
post-VS vertices. Prior output prediction proves exactly21 draws per
scale,1668218880/417054720 output bytes, as previous section records.

Runtime flow traced: D3D12RenderTargetCache::Update calls base ownership update,
PerformTransfersAndResolveClears, then SetCommandListRenderTargets. Clear must
run after this update and use accumulated targets/resource states. Existing
resolve clear implementation around4568+ supplies descriptor/barrier patterns.
IssueDraw computes cached viewport and scaled scissor around3490-3520, then
UpdateSystemConstantValues around3550 before guest uploads/residency. This
provides a first integration location with existing native-pass precedent;
earlier placement can later avoid redundant guest pipeline preparation.

SharedMemory::CopyCpuRange rejects GPU-written pages and protects CPU memory;
caller must arm a watch first. Do NOT hold global critical region while calling
it: EnablePhysicalMemoryAccessCallbacks intentionally runs outside global lock
to preserve heap/global lock ordering. Arm watch under lock, release for copy,
then re-lock to reject invalidation and unwatch. Captured CPU bytes must be the
immutable geometry used to derive clear rectangles; no GPU readback stalls.
GetFh1OwnedGeometry would allocate/upload64KiB windows unnecessarily for these
small CPU-only clear snapshots, so do not use it merely to get CPU bytes.

Next implement watched snapshot acquisition plus exact state/index/fetch proof,
feed shader-equivalent projected vertices to helper, and emit clears through
render-target cache preserving transfers, descriptors and barriers. Exclude
queries/memexport and unsupported state. Validate runtime CPU transformation
against shader output and actual native-clear capture before benchmarking.
Goal remains full renderer retirement/lower requirements, active/incomplete.

### Native clear byte prediction qualified at both scales - 2026-09-07

Production unchanged695E0C66. Previous turn was progress: measured pixel
migration and identified clear candidates. This phase qualifies their exact
output transformation; it does NOT yet execute native D3D12 clears.

position-clear-expanded-audit exports post-GS triangle-list vertices, geometry
shader disassembly, target dimensions/formats and state from position-pixel-
fixed-rdc. GS expands each three input vertices into six output vertices
covering an axis-aligned rectangle.21 draws, some two rectangles per draw.
All screen-space corners integer-aligned after viewport transform; scissor
and target extent clip the resulting rectangles. Native GS types614/1649 in
this capture; disassembly preserved.1x counterpart position-clear-expanded-
1x-audit uses valid shadow-mask-1x-ready-rdc.

Correction to previous audit summary: colors are constant, not universally
zero. Observed white, zero,0.06640625/0.0390625/0.015625, and0.25882354 gray.
Prediction reads actual b0 system[15].y exponent and converts constant output
into R8G8B8A8_UNORM or R16G16B16A16_FLOAT. Depth D24S8_TYPELESS is four bytes;
D32S8_TYPELESS eight bytes. Preserve stencil/padding unless stencil replacement
is enabled. Clamp depth after viewport transform (including small negative
post-VS values). Depth compareAlways, depth writes, stencil compareAlways/
Replace/full mask and equal front/back, blend/logic disabled and full color
mask are asserted for writing targets. Sample mask full, alpha-to-coverage off.

Runnable position-clear-prediction.py reads each target at event-1, predicts
only clipped rectangle writes (preserving every other byte), and compares
against actual draw output at event for every MSAA sample. It validates
integer corners/rectangle shape, constant depth/w and color before prediction.
After correcting the initial zero-color assumption, all21 draws match exactly:
2x 1668218880 bytes, report position-clear-prediction/report.json;
1x 417054720 bytes, report position-clear-1x-prediction/report.json.
This proves captured output equivalence of the mathematical clear operation,
not yet a runtime native-clear implementation or unobserved state coverage.

NEXT implement a qualified runtime path preserving original target ownership,
transfer and barrier behavior. Existing render_target_cache.cpp resolve clears
already use D3DClearDepthStencilView and native color clears (around4568+), with
per-format handling. IssueDraw calls render_target_cache_->Update around3004
before draw pipeline preparation. Trace that ownership flow before placing a
clear fast path. Need runtime geometry/state/CPU visibility proof, query and
memexport exclusions, exact rectangle/color/depth computation, then live
capture parity and performance. Do not replace the operation with broader
shader-only success; goal remains full Xenos renderer retirement.

### Position pixel performance and clear-operation audit - 2026-09-07

Production remains695E0C66 position-pixel-fixed-candidate, artifact/staged match.
position-pixel-fixed-abba compares C8D0196B vertex-only baseline against695E0C66
native pixel candidate. PIDs49328/50752/44524/45912, A1/B1/B2/A2 all normal,
two captures/frame2800, same AppData2x. No build/replay overlap. Last900 nonzero
frame rows; process34-46s. Summary position-pixel-fixed-abba-summary.json:
CPU+3.846%,median-0.226%,p95-1.053%,
private+0.307%,working+0.181%;draw-2.573%,
vertices-0.792%,GPUtime-0.291%.
CPU rates A1/B1/B2/A2:3.137/3.355/3.166/3.142, median17.001/16.5285/17.088/
16.6915ms, p95 21.029/19.952/21.098/20.458ms. CPU rises while candidate pooled
workload is lower; no demonstrated performance gain. B1 is notably higher CPU
than other runs. Retain parity-verified native retirement step, but do not
claim lower hardware requirements or explain away the CPU result as noise.

New position-clear-audit.py/report.json inspects all21 matching draws in
position-pixel-fixed-rdc: post-VS vertices, viewport/scissor, explicit blend/
render-target arrays, depth/stencil state, and geometry shader IDs. Vertices
have constant depth/w and (for color) zero color. Rectangles use geometry
expansion; native clear is a promising next operation to qualify, not yet
implemented or proven equivalent. Example event377:16384x16384 viewport,
scissor width160, vertices bound128x128 screen rectangle, blend disabled,
writeMask15, depth/stencil enabled. Depth-only events676/731 use depth1 and
stencil disabled; rectangles may be multiple per draw and clipped by scissor.
Late depth values include small negative values and must preserve clamping.

Next inspect geometry expansion/post-GS and derive exact clipped integer
rectangles, depth/stencil/color state predicates and target dimensions. Reuse
existing render_target_cache.cpp ClearDepthStencilViewAllocatedRects/clear
operations; preserve render-target ownership/transfers and hazards. Validate
replacement output against captured draws before enabling native clears.
Other expensive families and shared renderer subsystems remain; full renderer
retirement remains active/incomplete.

### Position pixel selection fixed, live parity and fallback - 2026-09-07

CURRENT candidate/artifact/staged 695E0C66862F577EC92C4F412DEA6D6CCF8B7F33A06A53A1BA72970207AADCBA.
position-pixel-fixed-candidate.dll; rollback position-color-candidate.dll
C8D0196B. position-pixel-fixed-source/files.json snapshots seven files.
DC7EAD57 position-pixel-candidate.dll is superseded: its native PSOs fell back
and it must NOT be used as evidence of active native pixel shaders.

Initial live capture PID42740 normal but identity check failed (position-pixel-
active-parity/report.json). Runtime logs showed nine natural fallback PSOs.
Root cause: final native scene shader override had a catch-all else selecting
blended-world VS/PS for the new position family, overwriting correct earlier
selection. Changed else to explicit8D8A197476841A9A condition, fixing shared
selection behavior for newly admitted families. Regression check compiles the
actual override and verifies position/unknown families remain unchanged and
all three intended families still select their shaders. Build and admission/
binding/fallback checks plus51 contract tests pass.

Corrected capture PID38880 normal. position-pixel-fixed-active-parity asserts
both integrated native VS and native linear/centroid PS bytes on all nine
matching color draws; replacing PS with originals gives exact1080033280 bytes
of color/depth at2x, every matching draw boundary/MSAA sample. Prior1x prototype
parity remains270008320 bytes and compiled PS bytes unchanged. No full renderer
retirement claim; other shader families/shared subsystems still remain.

Forced native position PSOs to fail, PID512 normal exit. Preserved
position-pixel-fallback-smoke/runtime.log, position-pixel-fallback-evidence.json:
three linear and six centroid fallback PSOs, result0, both stages translated
true. Source restored with byte rewrite, rebuilt and staged hashes verified.
position-pixel-fallback-diagnostic.dll is NOT staged. Restored build log:
position-pixel-fixed-restored-build.log.

NEXT: controlled A/B against vertex-only C8D0196B, using corrected695E0C66
candidate. No performance result yet for this pixel migration. Then investigate
remaining GPU cost of these single-draw passes/native clear opportunities or
next measured legacy families. Native stage count alone is not speed evidence.

### Pass-through pixel integration and prototype parity - 2026-09-07

Candidate/artifact/staged DC7EAD57C0C6D0F4117C118FDDFDB1BF3E037CE86E7243A85385513209315CC4.
position-pixel-candidate.dll; rollback position-color-candidate.dll C8D0196B.
position-pixel-source/files.json snapshots seven files; before-position-pixel/
preserves preceding SDK source/header. Full renderer retirement incomplete.

Integrated A4A965C189287B99 PS paired with1E6883FCCDE1F688/mod1 VS.
Exact PSmods0000400000000001(linear),0000400000010001(centroid), equal1x/2x,
bindless host targets only. Native source fh1_passthrough_early.ps.hlsl uses
[earlydepthstencil], corresponding interpolation qualifier, output color times
system[15].y. No alpha/coverage logic: those other variants are not admitted.
position-passthrough-modifications.json matches exact original PS bytes in
2x pack; both variants have zero textures/samplers/mask. Other mods excluded.

IsFh1NativePositionPipeline extends native scene qualification. Qualified pair
skips both stage preloads, supplies empty binding metadata, preserves async
creation, and uses existing lazy legacy creation-failure path. VS ownership
and shared buffer behavior unchanged. New PS headers compile byte-identically
to prototypes verified in RenderDoc.

Prototype reports position-passthrough-1x-parity and2x-parity: nine draws/two
PS variants; exact 270008320/1080033280 color/depth bytes at every draw
boundary and MSAA sample.2x uses position-color-rdc,1x valid shadow-mask-1x-
ready-rdc. Original PS bytes asserted before substitution to select variants.
Compiled admission tests include all hash/mod bit flips (only bit16 selects
other valid PS), scale/path/bindless gates. Empty-binding/mismatchedPS checks
and packed-world fallback checks pass. All51 contract tests pass.
position-pixel-build.log succeeds with16 warnings.

Smoke PID36140 normal exit, two captures/frame2800. Preserved runtime.log in
position-pixel-smoke. Startup490 legacy variants versus492,452 prewarmed PSOs.
NEXT: capture position-pixel-rdc and assert live native PS bytes, replace with
originals for exact parity; force both native pixel variants' PSOs to fail,
verify fallback, restore bytewise/rebuild; A/B against C8D0196B. These live
identity/fallback/performance checks have NOT yet run for the pixel integration.
No performance claim for this phase. The preceding vertex-only performance
result does not validate this new candidate's speed.

### Position/color fallback and performance validation - 2026-09-07

Current candidate/artifact/staged C8D0196BF039D756972C6A305EE4D6603D970EDE39B995099881B375EA9830C7 unchanged.
Forced native PSO failure for both1E6883 VS variants using temporary diagnostic
build. PID35064 normal exit; preserved position-color-fallback-smoke/runtime.log
and position-color-fallback-evidence.json. Five mod0 and nine mod1 successful
fallback PSOs, result0 and VS translatedtrue. Mod1 PS translatedtrue, mod0
PSfalse because no PS exists. Only observed error was known missing-device.
Diagnostic DLL position-color-fallback-diagnostic.dll is not staged.
Production source restored via byte rewrite and rebuilt successfully;
position-color-restored-build.log, source/artifact/staged match production.

position-color-abba.ps1 compares shadow-final-candidate D5BF9AEA baseline
against C8D0196B candidate,2x same AppData stationary performance script.
A1/B1/B2/A2 PIDs49724/7064/1216/44172 all normal, two captures/frame2800.
No build/replay overlap, last900 nonzero frames and process34-46s windows.
position-color-abba-summary.json records full runs and workload:
CPU-3.941%,median-3.119%,p95-9.290%,
private-0.231%,working+0.560%.
Pooled draw+0.210%,vertices+0.588%,GPUtime-3.852%.
CPU rates A1/B1/B2/A2:3.314/3.199/3.189/3.335 CPU-seconds/wall-second.
Median ms17.636/16.656/16.193/16.2705; p95ms24.698/20.582/19.658/19.663.
Per-run average draws3654/3634/3352/3317 show temporal workload drift despite
close pooled means. p95 improvement depends strongly on first baseline run.
Promising short-run CPU evidence, not a broadly established p95 gain or proof
of minimum hardware requirements. Keep candidate; parity and lazy fallback
are verified and two more legacy VS preloads retired.

Next remove the remaining A4A965 pass-through PS variants paired with1E6883,
qualifying early-depth and linear/centroid semantics and exact modification
gates. Existing alpha/coverage shader differs from captured variants. Then
address measured GPU pass cost/native clear opportunities or next expensive
legacy family. Full Xenos renderer retirement remains active/incomplete.

### Position/color vertex integration and live parity - 2026-09-07

Current candidate/artifact/staged DLL C8D0196BF039D756972C6A305EE4D6603D970EDE39B995099881B375EA9830C7.
.local/native-renderer/position-color-candidate.dll; rollback shadow-final-
candidate.dll D5BF9AEA. Source snapshot position-color-source/files.json lists
seven files. before-position-color/ preserves prior SDK pipeline source/header.

Integrated native VS1E6883FCCDE1F688 modifications0(position-only) and1(color).
fh1_position_color.vs.hlsl and two headers compile byte-identically to the
verified prototypes. Removed unused owned-geometry branch. Both still use
bounded shared-memory SRV/UAV with fetch0 and28-byte stride.
IsFh1NativeStandaloneVertex shares existing shadow stage lifecycle: empty VS
binding metadata, skip translation/preload, async pending-stage exclusion and
lazy original shader fallback. Shadow pixel and owned-geometry qualification
remain separate. Position VS selection uses modification0/1 exact output.
Pixel shaders remain legacy; this phase retires two vertex variants only.

Build position-color-build.log succeeds (16 warnings). Compiled shadow/new
standalone admission and packed-world fallback/binding checks pass, including
wrong hashes/modifications,1x/2x/equal scales, bindless and host target gates.
All51 native shader pack/renderer/release/render-test contract tests pass.

Smoke PID12340 normal exit, two captures/frame2800; preserved runtime log in
position-color-smoke. Loads492 legacy variants (previous494),452 prewarmed
PSOs. Observed known missing-device error. Native capture PID41204 normal exit,
position-color-rdc. position-color-active-parity/report.json asserts exact
integrated VS binary identity for both variants on all21 matching draws, then
replaces both with original legacy programs and compares outputs exactly:
1536 vertex bytes and
1668218880 color/depth bytes at2x, every matching
draw boundary and each MSAA sample. Prior prototype1x checks remain valid
because integrated shader binaries are identical.

NEXT: forced native PSO failure smoke for both new variants to verify lazy
fallback actually executes, restore source by rewriting bytes and rebuild,
then controlled A/B performance against D5BF9AEA. Forced fallback and new A/B
have NOT yet run. Do not infer speedup from two fewer preloads. Goal remains
active/incomplete; shared renderer subsystems and other shaders remain.

### Native position/color vertex prototypes qualified - 2026-09-07

Production remains D5BF9AEA; no runtime code or staged DLL changed this phase.
Inspected expensive VS1E6883FCCDE1F688 in current shadow-final-rdc capture.
legacy-single-pass-audit maps all capture draws through command-list PSO state,
rejects unsupported state operations, and exports both original VS variants
and both A4A965 PS interpolation variants/disassembly.21 matching draws:
9 color draws and12 depth-only draws, typically3 indices, some6.

VS is position/color passthrough: fetch0,28-byte stride,FLOAT3 at0,FLOAT4 at12,
position.w=1; endian/index handling and NDC scale/offset follow translator.
The depth-only modification omits the color output. Native prototype reuses
shadow endian/index/load and NDC implementation, removes transform constants,
uses separate Load4(address+12) preserving32-bit address wrap. Source:
.local/native-renderer/legacy-position-color.vs.hlsl, compiled color and only
DXBC variants. Shared-memory buffers still used; owned geometry not qualified.
Do not enable inherited FH1_SCENE_OWNED_GEOMETRY branch: color load is not
implemented for that configuration. Remove that unused branch on integration.

legacy-position-color-parity/report.json replaces both original VS variants
across all21 draws at2x; legacy-position-color-1x-parity/report.json repeats
against valid shadow-mask-1x-ready-rdc. Both pass exact vertex/output checks:
1x 1584 vertex bytes, 417054720 color/depth bytes;
2x 1584 vertex bytes, 1668218880 color/depth bytes.
Every matching draw boundary and each target MSAA sample checked. The report's
pixel_families label VS1E6883 means no pixel shader (PSO name lacks PS suffix).
legacy-position-validation.json records counts and compiled shader hashes.

Next integrate both exact VS modifications with existing stage admission,
binding metadata/preload bypass and lazy failure handling; qualify live native
identity/parity and forced fallback, then measure performance. A4A965 remains
legacy in these tests. Existing fh1_passthrough_color.ps.hlsl has alpha/coverage
logic; captured PS variants are early-depth linear/centroid pass-through with
output exponent only. Do not substitute existing PS without matching variant
semantics. Full Xenos retirement remains incomplete, no speedup established.

### Fresh GPU pass profile after shadow migration - 2026-09-07

Production unchanged: staged DLL D5BF9AEA3D3C698FEB81130D59FB88DD8AF8E9E88835B3C6790DA07D91A21102.
PID44408 exited normally with two captures/frame2800, same AppData save at2x,
CollectFh1PassInventory enabled. Evidence is .local/native-renderer/
shadow-final-pass-profile/{runtime.log,corpus.json,summary.json}; runnable
summarize-shadow-final-profile.py preserves latest cumulative family samples
and joins first-draw identities to this run's corpus. It asserts nonempty
positive sample counts. This is a diagnostic run, not an A/B comparison.

Leading cumulative GPU pass costs (average per sampled occurrence):
- 53B2C36308FCD219: 1.248ms, average811 draws,14 samples; first pair8D8A/BA6A.
- 8F17E2B502A6BF62: 0.975ms,3 draws,15 samples; first pairA3B9/9362 (native).
- 3AE7C526208A0E61: 0.375ms,1 draw,35 samples; first pair1E6883FCCDE1F688/A4A965C189287B99.
- ED7F805DBDC5C236: 0.398ms,1 draw,30 samples; first VS1E6883FCCDE1F688, noPS.
- BBE515B2B032F30A: 0.785ms,124 draws,14 samples; first pairC34795A841E7DEFF/21B70A5E4C9CFD11.
- 7C6A3248DE68D142: 0.658ms including0.045ms resolve,94 draws,15 samples; first pair984D/6FDA.
- C139B948D0ACD681: 0.337ms,2 draws,22 samples; first pair20A41D46F34D238E/9AAEF9B81D19D203.

These are whole-pass timings: first-draw identity does not identify every
shader in a multi-draw pass. Cumulative ranking includes loading and gameplay;
sample counts differ, so do not sum this list into a frame-time claim.
No native shader hash admission references for1E6883,C34795,20A41D found in
SDK graphics source. Their precompiled shader variants exist in aot-race-v2/
dxil and other local packs. Next inspect current RenderDoc draw state and
original disassembly for these expensive legacy families, starting1E6883
single-draw passes; qualify exact replacement and parity before integration.
Shadow shader migration alone has not eliminated its measured GPU cost.
Renderer retirement and lower hardware requirement validation remain open.

### All seven captured shadow pixel programs native - 2026-09-07

Current artifact/staged DLL SHA256
D5BF9AEA3D3C698FEB81130D59FB88DD8AF8E9E88835B3C6790DA07D91A21102,
.local/native-renderer/shadow-final-candidate.dll. Rollback:
shadow-pair-candidate.dll (87E9594E...). Source snapshot shadow-final-source/
files.json lists thirteen files; before-shadow-final/ preserves preceding
edited source/checks. Full renderer-retirement goal remains active/incomplete.
"shadow-final" means the seven captured PS in this family, not full retirement.

Integrated11824C2EC1B156C6,26C4FD34AECBE4DE,FCDF9BE8C57F7D01,
mod0000400300000001 with native A3B9/mod1. Admission/fixed binding checks now
cover all seven shadow PS at equal1x/2x, bindless host targets. Existing stage
preload, async creation, owned geometry and lazy legacy fallback remain.
Startup loads494 instead of497 legacy variants and retains452 prewarmed PSOs.
This removes the remaining three qualified shadow PS preloads.

Shared SampleGradientX now accepts OffsetY with default0.5; predicated programs
also use1.5. All14 compiled shadow PS variants remain byte-identical to their
verified predecessors/prototypes after extraction. New13/17/17-float constant
layouts and predicate/branch semantics are unchanged from prototype proofs.
shadow-final-bindings.json compares all three new offline layouts with9362,
exactly matching four views/two samplers/mask3. Emitter now consumes the shared
offset implementation directly. Admission/binding checks, emitter mutation
checks and51 contract tests pass.

Validation under .local/native-renderer:
- shadow-final-build.log and restored-build.log succeed; source restored by
 rewriting bytes after diagnostics, artifact/staged hashes match candidate.
- Existing predicated1x/2x replays: five matching draws, three PS, exact
157286400/629145600 color/depth bytes at every draw boundary and MSAA sample.
- Live capture PID35600 normal exit. shadow-final-active-parity asserts all
 three new native PS bytes, restores legacy PS and compares629145600 color/
 depth bytes exactly at2x.1x remains prototype replay plus structural admission.
- shadow-final-family-audit verifies all11 matching draws have the owned native
 VS and expected native PS bytes across all seven PS hashes. This is a shader
 identity audit; full pixel comparisons are in the staged parity reports.
- Forced the three new native PSOs to fail: PID45052 normal exit,452 prewarmed
 pipelines, successful legacy fallback for E2BE1285D4963605,9FE1C0F6F19EE6B3,
515C7C3E21551974,6B0804BFC89DDA36,B375A16D5A8418E0,89629C73D4EAB258,
 both stages translated true. Diagnostic DLL is not staged.
- Integrated validation and runtime evidence preserve hashes, performance,
 parity, startup/fallback/errors; no completion claim for uncaptured branches.

Performance: shadow-final-abba-summary.json compares87E9594E/D5BF9AEA at2x.
Four normal runs, two captures/frame2800, last900 nonzero frame rows and process
window34-46s; no capture/build/replay overlap. Candidate
CPU-1.323%,median-3.045%,p95-8.381%,
private+0.437%,working+0.274%.
Workload draw-5.137%,vertices-2.032%,GPU-time-4.948%.
This short moving-world comparison does not prove lower hardware requirements.
CPU-1.323%, median-3.045%, p95-8.381% are encouraging, but candidate draws
were5.137% lower and vertices2.032% lower, so workload confounds attribution.

Next: refresh GPU pass profiling and the remaining legacy dependency inventory
with all shadow shaders migrated, then target the next expensive legacy pass
or shared renderer subsystem. Do not equate shader-count reduction with speed.
Other shader families, texture processing, offline analysis, command/register
state and512MiB shared memory remain. Lazy legacy failure paths also remain.
Full Xenos renderer retirement is not achieved.

### Final three shadow pixel prototypes pass exact replay - 2026-09-07

Production remains87E9594E6A297066D69008D105AD09B07F7C8D57E001CB2704F61D4C880C1FE3
(shadow-pair-candidate.dll). No production admission/preload changes this phase.
Full goal active/incomplete; remaining shadow program parity is established
for the captured draws before integration.

.local/native-renderer/write-shadow-predicated.py emits standalone prototypes
11824C2EC1B156C6,26C4FD34AECBE4DE,FCDF9BE8C57F7D01,mod0000400300000001.
Files shadow-1182.ps.hlsl,shadow-26c4.ps.hlsl,shadow-fcdf.ps.hlsl and their
1x/2x.dxbc binaries use shared exact sampling/ALU helpers.1182 packs13 constants;
26C4/FCDF pack17. Manifest records constant lists and instruction counts59/66/66.
All three contain29 predicated instructions.

Predicate semantics follow SDK pipeline/shader/dxbc_translator_alu.cpp:
setp_ne_push uses src0.w==0 && src1.w!=0 for p0 and a broadcast stack result
based on x; setp_inv tests equality with1 and swaps0/1 while preserving other
values; scalar setp_ne writes p0 and previous scalar result. Paired vector/
scalar operands and next predicate are evaluated before stores. Conditional
forward jumps are replaced by instruction guards only after asserting every
skipped operation is guarded. Predicated exec markers must agree with each
instruction, and predicate changes in a predicated exec must occur last.
Unknown control flow is rejected. Extra tf0 OffsetY1.5 is preserved alongside
0.5 with the existing sub-texel correction; tf1 LOD sampling is unchanged.

check-shadow-predicated-emitter.py runs all three originals in a temporary
workspace and rejects four mutations: reversed jump sense, an unguarded skipped
operation, an early predicate change and unsupported loop control. The first
compile caught an HLSL scalar constructor issue; scalar broadcast was corrected
with .xxxx. All six variants compile. Regeneration after stricter structural
checks reproduces all three2x bytecodes exactly.

shadow-predicated-2x-parity uses current shadow-pair-rdc;1x-parity uses the valid
shadow-mask-1x-ready-rdc. Both replace all three PS independently at every
matching draw boundary, all color/depth MSAA samples exact: five draws,
629145600 bytes at2x and157286400 at1x. Distribution: two1182, two26C4, oneFCDF.
Reports preserve original legacy binaries; shadow-predicated-validation.json
records candidate hashes and totals. This is captured-output parity, not proof
that every branch is exercised in all scenes. Shader semantics and emitter
structural assertions supplement the replay evidence.

Next: extract the offset-capable sampler into shared production code while
keeping existing shader bytecodes unchanged, add three shader sources and six
headers, verify offline bindings, then extend native admission/prewarm and
run live parity/fallback/performance checks. Production still has three legacy
shadow PS loads; full Xenos renderer retirement also needs other shader families,
texture handling, offline analysis, command/register state and shared memory.

### Native22DA/8418 shadows integrated; two legacy loads removed - 2026-09-07

Current artifact/staged DLL SHA256
87E9594E6A297066D69008D105AD09B07F7C8D57E001CB2704F61D4C880C1FE3,
.local/native-renderer/shadow-pair-candidate.dll. Rollback:
shadow-26eb-candidate.dll (5E993F89...). Source snapshot shadow-pair-source/
files.json lists nine files; before-shadow-pair/ preserves prior pipeline cache
and checks. Full renderer-retirement goal remains active and incomplete.

Added22DA22B5639EBAE4 and8418C40F121D7EA7 PS, bothmod0000400300000001,
to existing native A3B9/mod1 shadows. Same equal1x/2x, bindless host-target
admission. Existing shared sampling, owned geometry, stage-specific preload,
async scheduling and lazy legacy fallback are reused. Shadow PS selection is
an explicit four-case switch. Startup now loads497 rather than499 legacy
variants while retaining452 prewarmed pipelines.

The new programs independently preserve paired ALU reads, unfused arithmetic,
sin/cos, guest pixel position and distinct fade/bounds math.22DA packs15 float
constants;8418 packs16 (additional guestc26). Source/bytecode wrappers match
the prototypes exactly at both scales. shadow-pair-bindings.json proves both
offline layouts identical to9362 (four views, two samplers, mask3). Compiled
binding/admission checks cover all four native shadow PS and reject the three
remaining legacy PS.51 contract tests pass.

Validation under .local/native-renderer:
- shadow-pair-build.log and restored-build.log succeed. Diagnostic source
 removed, source rewritten to force rebuild, artifact/staged hashes verified.
- write-shadow-22da.py and write-shadow-8418.py reuse exact helpers and shared
 sampling. Prototype replays shadow-pair-1x-parity and2x-parity replace both
 shaders independently: two draws, two shader variants, all color/depth MSAA
 samples exact (62914560 bytes at1x,251658240 at2x).
- Live capture PID37024 normal exit. shadow-pair-active-parity asserts both
 actual native PS binaries, restores original legacy PS and matches251658240
 color/depth bytes exactly at2x.1x active admission remains structurally
 covered plus prototype parity; no new live1x capture in this phase.
- Forced both new native PSO failures: PID19148 normal exit,452 prewarmed PSOs,
 successful legacy fallback for BE35A879C5BF524E,EB63806BC235A77D,
02E213034B0A2AAD,AF4EB6BDA3A63F72 with both stages translated true.
- shadow-pair-integrated-validation.json and runtime-evidence.json preserve
 parity, performance, hashes and startup/fallback/error evidence.

Performance: shadow-pair-abba-summary.json compares5E993F89/87E9594E at2x.
Four normal runs, two captures/frame2800, last900 nonzero frame rows and process
window34-46s; no capture/build/replay overlap. Candidate
CPU+3.153%,median-1.138%,p95-0.036%,
private-0.414%,working-0.399%.
Workload draw-5.462%,vertices-0.803%,GPU-time-2.099%.
This short moving-world sample does not prove lower hardware requirements.
CPU rose3.153% despite5.462% fewer draws; median improved1.138%, p95 was
essentially unchanged. Mixed evidence, not a demonstrated speed gain.

Next: remaining shadow PS11824C2EC1B156C6,26C4FD34AECBE4DE,FCDF9BE8C57F7D01.
These include predicated control flow and additional sampling offsets; do not
apply the straight-line emitter without preserving those operations. Reuse
the shared sampling implementation with exact offset support as needed.
Other shader families, texture handling, offline analysis, command/register
state and512MiB shared memory remain. Full Xenos retirement is not achieved.

### Native26EB shadow pixel integrated; legacy preload removed - 2026-09-07

Current artifact/staged DLL SHA256
5E993F89AA3934723395E6B896CBBE13C0B5904FAA1D21C60DB4ED890D4FBE3F,
.local/native-renderer/shadow-26eb-candidate.dll. Rollback:
shadow-owned-candidate.dll (BF425DF4...). Source snapshot shadow-26eb-source/
files.json lists ten files; before-shadow-26eb/ preserves preceding edited
source/checks. Full goal active/incomplete; this is verified dependency removal.

Added exact26EB620936001876/mod0000400300000001 PS for existing native
A3B9ED5D5C87230E/mod1 shadows at equal1x/2x, bindless host render targets.
Admission and fixed bindings now cover9362 and26EB. Existing stage-specific
prewarm, async scheduling, owned geometry and lazy legacy fallback are reused.
Startup loads499 rather than500 legacy variants and retains452 prewarmed PSOs.
New whole-native PSO518B760FC835C4D2 reports guest VS/PS translated false.

fh1_shadow_sampling.hlsli shares exact sampling/ALU code between the two PS
sources;26EB has13 packed constants,9362 has12. All four compiled variants
remain byte-identical to previously verified binaries after extraction.
shadow-26eb-bindings.json compares both offline pack entries exactly: four
texture views, two samplers and used mask3. Fixed bindings tests cover both.
The local26EB emitter now reads the shared file and reproduces its verified
bytecode; the historical9362 emitter still needs adapting if reused.

Validation under .local/native-renderer:
- shadow-26eb-build.log and restored-build.log succeed; production source and
 artifact/staged hashes verified after diagnostic removal.
- Compiled shadow admission and packed-world/shadow binding/fallback checks
 pass;51 contract tests pass. Admission checks both hashes, bad hash/mod bits,
 unsupported scales/paths and vertex-only admission of the five other PS.
- Existing26EB prototype replays at1x/2x remain exact: one matching draw each,
31457280/125829120 color/depth bytes, all MSAA samples.
- Live capture PID43496 normal exit. shadow-26eb-active-parity asserts native
 PS bytes, replaces them with the original legacy PS, and gets exact125829120
 color/depth bytes at2x.1x live admission is structurally covered plus prototype
 replay; there is no new active1x capture in this phase.
- Forced new native PSO failure PID38500 normal exit,452 prewarmed PSOs,
 successful518B760FC835C4D2 legacy fallback with both stages translated true.
 Diagnostic DLL must never be staged as production.
- shadow-26eb-integrated-validation.json and runtime-evidence.json preserve
 parity, performance, source/binary hashes and startup/fallback/error evidence.

Performance: shadow-26eb-abba-summary.json comparesBF425DF4/5E993F89 at2x.
Four normal runs, two captures/frame2800, last900 nonzero frame rows and process
window34-46s; no capture/build/replay overlap. Candidate
CPU+0.424%,median+1.891%,p95+5.319%,
private-0.294%,working-0.148%.
Workload draw+4.956%,vertices-0.151%,GPU-time+3.287%.
Do not infer lower hardware requirements from this short moving-world sample.
Candidate draws rose4.956% alongside p95+5.319%; CPU+0.424%. This is not a
verified speed gain; workload confounds attribution. Retained for dependency
removal, with performance attribution still open.

Next: five remaining shadow PS11824C2EC1B156C6,22DA22B5639EBAE4,
26C4FD34AECBE4DE,8418C40F121D7EA7,FCDF9BE8C57F7D01.22DA/8418 share sampling
and much ALU structure, but differ in bounds/fade math and constant packing;
translate and verify independently while reusing the shared sampling code.
Other shader families, texture handling, offline analysis, command/register
state and512MiB shared memory remain. Full Xenos retirement is not achieved.

### Next shadow pixel prototype passes exact replay - 2026-09-07

Production remains BF425DF46FCB0C7CFFAE89AC628A1281917BBA29D6ED3F4512A6309B6EDE18CC
(shadow-owned-candidate.dll). No new production admission or preload removal
in this phase. Full goal active/incomplete; next shader parity is now proven
for the captured pairing before integration.

Prototype26EB620936001876/mod0000400300000001 is in
.local/native-renderer/shadow-26eb.ps.hlsl, emitted by write-shadow-26eb.py.
It reuses9362 texture sampling and exact paired-ALU translation helpers,
preserving guest sin/cos, precise unfused arithmetic and pixel position.
Thirteen packed constants:0,1,8,9,10,24,25,27,32,33,253,254,255.
Compiled with FXC ps_5_1/O3/unbounded descriptors into shadow-26eb-1x.dxbc and
shadow-26eb-2x.dxbc;1x uses FH1_SHADOW_PIXEL_SCALE=1.0.

shadow-26eb-2x-parity uses current shadow-owned-rdc (native owned VS plus
legacy PS);1x-parity uses shadow-mask-1x-ready-rdc. Each contains one matching
A3B9/26EB draw. Replacement PS yields exact color/depth at its draw boundary,
all MSAA samples:125829120 bytes at2x,31457280 at1x. Reports retain original
legacy PS bytes and hashes; validation-summary.json records candidate hashes.
This proves that captured pairing, not every scene or other VS pairing.

Next: share the existing shadow sampling implementation, integrate this native
PS and its fixed binding metadata, extend admission checks, then build/live
capture/fallback/performance validation before removing its legacy preload.
The standalone emitter still takes its header from the9362 production source;
update that dependency when extracting shared helpers. Existing production
and six legacy shadow PS preloads remain intact until integration is verified.

### Shadow CPU attribution and bounds-cache probe - 2026-09-07

Production is unchanged from BF425DF46FCB0C7CFFAE89AC628A1281917BBA29D6ED3F4512A6309B6EDE18CC
(shadow-owned-candidate.dll). Both temporary diagnostic edits were removed;
command_processor.cpp is byte-identical to its saved production source, and
artifact/staged DLL hashes match the candidate after rebuilding. Full goal
remains active and incomplete; this phase adds measurement evidence.

The previous four-run CPU increase remains unattributed. A diagnostic times
shadow index acquisition plus geometry proof/import/reproof, including cache
misses, on the render thread. PID46260 exits normally. shadow-cost-summary.json
and evidence.json preserve cumulative samples: 14336 draws, 82.3235ms,
1327 imports, every sampled draw owned. Mean 5.742us/draw.
Between first/last samples: 21.912s elapsed and
2.507ms timed work per wall second. This direct scope is far smaller
than the earlier whole-process CPU increase. It does not measure subsequent
bindings, deferred residency effects, GPU work or other threads, so it cannot
rule out indirect cost or establish an overall speedup.

A second diagnostic examines missed depth bounds-cache lookups for equivalence
when ignoring fields that the bounds function does not read: fetch type/endian
bits, high fetch-size flags, unrelated system flags and system words1/2.
It does not change lookup behavior. PID50480 exits normally. At 1310720 calls,
14878 misses and 102 equivalent old entries; the equivalent count stays102
from the first262144-call sample through the last. bounds-probe-summary.json
preserves counters and raw lines. Reject key-normalization optimization for
now: negligible measured opportunity, no steady-state equivalent misses.

Build logs: shadow-cost-build.log, bounds-probe-build.log and
shadow-cost-restored-build.log. Diagnostics are shadow-cost-diagnostic.dll and
bounds-probe-diagnostic.dll; neither is staged. Production source backup is
shadow-cost-production-command_processor.cpp. Source was restored by rewriting
bytes to force a rebuild, avoiding the prior preserved-mtime problem.

Next: continue the six legacy shadow pixel programs (26EB620936001876 is the
smallest remaining dump), preserving independent shader/geometry parity.
Retain the mixed performance finding; direct geometry timing has narrowed the
CPU investigation but has not explained it. All remaining renderer-retirement
work from the preceding checkpoint remains necessary.

### Shadow geometry moved to bounded native buffers - 2026-09-07

Current artifact/staged DLL SHA256
BF425DF46FCB0C7CFFAE89AC628A1281917BBA29D6ED3F4512A6309B6EDE18CC,
.local/native-renderer/shadow-owned-candidate.dll. Rollback:
shadow-family-candidate.dll (7E94B7AA...). Source snapshot shadow-owned-source/
files.json lists nine files. Before-shadow-owned source backups preserve the
preceding command processor, pipeline cache, geometry helper and vertex HLSL.
Full goal remains active and incomplete; this phase removes shared geometry
reads for the captured shadow family, not the entire Xenos renderer.

Native A3B9ED5D5C87230E/mod1 uses the existing depth root's vertex SRV with
ordinary pixel tables when neither stage exports memory. The HLSL owned variant
removes the UAV and preserves per-component physical-memory bounds of Load3.
The shared variant remains byte-identical. Command processing classifies the
shadow stride as12 and reuses the existing immutable index snapshot, range
proof/import/reproof, bounded cache and all-or-nothing index/vertex ownership.
Geometry failure retains shared residency and the bounded root-SRV fallback;
PSO failure lazily restores legacy shaders and the standard root. Equal1x/2x,
host-target and bindless admission restrictions remain. No new cache/root or
runtime switch was added. Cache ceiling remains32MiB/512 entries.

Validation under .local/native-renderer:
- shadow-owned-build.log and restored-build.log succeed. Production source,
 artifact and staged DLL restored and hash-verified after diagnostic failure
 injection. Restoration initially preserved an old mtime, so the rebuild did
 no work; explicitly rewriting source forced the verified production rebuild.
- Compiled shadow admission/raw-load bounds/endian, depth range/index ownership,
 mesh import revalidation, packed-world and cache mutation/failure/budget checks
 pass;51 contract tests pass. Added12-byte cases to existing range/ownership
 checks and tools/check-fh1-shadow-load.py executes both production load paths.
- Smoke PID33656 and live RenderDoc capture PID50636 normal exits. Startup
 retains500 precompiled variants and452 prewarmed pipelines.
- shadow-owned-shader-parity (2x) and shadow-owned-1x-shader-parity replace VS
 on previous shared-buffer captures: all11 draws/all7 PS pairings exact.
 Vertex output2816 bytes each; color/depth1384120320/346030080 bytes exact.
- shadow-owned-audit verifies actual owned VS bytes, no VS UAV, all11 index
 and vertex buffers owned together:528 index bytes and1056 vertex bytes equal
 their shared-memory source, with all addressed ranges in bounds.
- shadow-owned-frozen-parity additionally replaces each live draw's vertex
 loads with literal words exported from its original shared-memory source.
 All11 post-VS outputs (2816 bytes) match exactly. This independently checks
 rebased owned-buffer output; it does not claim whole-frame target parity for
 these per-draw frozen replacements. Source snapshots live in that directory.
- Forced owned-shadow PSO failure diagnostic PID40432 exits normally, verifies
452 prewarmed pipelines, logs successful legacy fallback. Hybrid log hash0
 is not a PSO identity; only whole-native shadow pair labels carry hashes.
- Runtime evidence and validation summary preserve errors, parity, performance
 and source hashes. Known missing-device warnings occur; baseline A1 also logs
 one FFmpeg broken-frame audio error at07:25:04.914. No graphics error observed.

Performance: shadow-owned-abba-summary.json compares7E94B7AA/BF425DF4 at2x.
All four runs exit normally with two captures/frame2800. Last900 nonzero frame
rows and process window34-46s; no capture/build/replay overlap. Candidate
CPU+4.362%,median-1.647%,p95-1.579%,
private+0.558%,working+1.266%.
Workload draw-2.604%,vertices-1.314%,GPU-time-1.661%.
This short moving-world comparison does not prove lower hardware requirements.
CPU rose despite fewer candidate draws; this is mixed evidence, not a speed
gain. Attribute the CPU change before claiming an optimization benefit.

Next: replace six remaining shadow PS programs using the existing exact shader
workflow. Dumps are in v5-04-5a28-dump/ for11824C2EC1B156C6,22DA22B5639EBAE4,
26C4FD34AECBE4DE,26EB620936001876,8418C40F121D7EA7,FCDF9BE8C57F7D01 (all
mod0000400300000001).26EB is44 disassembly lines, with sin/cos and four shadow
samples; it shares much of9362's math but requires exact independent parity.
Other shader families, texture handling, offline analysis, command/register
state and512MiB shared memory remain. Owned fallback/uncaptured scenes and1x
live geometry admission still need broader coverage.

### Shadow vertex native across all seven captured pairings - 2026-09-07

Current build/staged DLL SHA256
7E94B7AA91C6B25B13052111F239FB9A864B8688DFD0C8D8B0906D1FCB1FE745,
.local/native-renderer/shadow-family-candidate.dll. Rollback: shadow-bindings-
candidate.dll (33BFFCCE...). Source snapshot shadow-family-source/files.json
lists four files; before-shadow-family-pipeline_cache.cpp/.h save preceding
source. Full renderer-retirement goal remains active and incomplete.

IsFh1NativeShadowVertex admits A3B9ED5D5C87230E/mod1 independently of PS,
retaining bindless host-render-target and equal1x/2x restrictions. Preload,
prewarm, runtime and PSO creation use this stage-specific predicate. Empty
native VS bindings are prepared for hybrid pipelines; their legacy PS loads
remain. Async scheduling stays enabled, with no pending legacy VS work.
Native PSO failure lazily loads the legacy stages and restores the original
root. Offline producer preloading remains unchanged. Startup now loads500
rather than501 variants and still verifies452 prewarmed pipelines. Both
qualified native shadow PSOs report guest VS/PS translated false.

Validation under .local/native-renderer:
- shadow-family-build.log and restored-build.log succeed; diagnostic source
 was restored and rebuilt, artifact/candidate/staged hashes match exactly.
- Compiled shadow and packed-world checks and51 contract tests pass. The
 shadow gate check also covers independent vertex admission with the other
 six PS families, while rejecting those families for native shadow PS.
- Smoke PID49156 and forced-fallback PID47548 exit normally. Diagnostic forces
 native shadow VS PSO failure, verifies452 prewarmed pipelines and successful
 legacy fallback. Hybrid diagnostic labels are zero (hash only computed for
 whole-native scenes); they do not identify individual hybrid PSOs.
- shadow-family-1x-parity and2x-parity replace every captured matching VS:
 all7 PS families,11 draws,2816 vertex bytes each,346030080/1384120320 bytes of
 color/depth data exact. Every matching draw boundary and MSAA sample checked.
- Live capture PID46992 normal exit. shadow-family-active-parity asserts raw
 native VS bytes in all11 draws across all7 PS pairings, then restores legacy
 VS:2816 vertex bytes and1384120320 color/depth bytes exact at2x. Active native
 admission at1x is structurally covered;1x broad shader parity uses older capture.
- shadow-family-runtime-evidence.json and validation-summary.json preserve
 startup/fallback/error evidence, binary/source hashes and parity totals.

Performance: shadow-family-abba-summary.json compares33BFFCCE/7E94B7AA at2x,
four normal runs with two captures/frame2800, last900 nonzero frame rows and
process window34-46s. No build/replay overlap. Candidate CPU-3.710%,
median-1.106%,p95-1.862%,private+0.772%,working+0.670%.
Workload draw+2.953%,vertices+1.208%,GPU-time-1.459%.
These four runs do not establish lower hardware requirements. Retained as
verified removal of the remaining shared legacy shadow vertex preload.

Next: own12-byte shadow geometry through the existing bounded cache, with
proof/import/reproof and parity. Six paired PS programs remain legacy, as do
other shader families, texture handling, offline analysis, command/register
state and512MiB shared memory. Xenos renderer is not yet fully retired.

### Shadow binding metadata native; legacy pixel preload removed - 2026-09-07

Current build/staged DLL SHA256
33BFFCCE49AE1E741D67DC9FB165905471E0C1A8E9F4B83CC720EBD7470D391E,
.local/native-renderer/shadow-bindings-candidate.dll. Rollback:
shadow-vertex-candidate.dll (A174F812...). Source snapshot shadow-bindings-source/
files.json lists four files; before-shadow-bindings-pipeline_cache.cpp/.h save
preceding source. Full goal active/incomplete; this turn was concrete progress.

Shared IsFh1NativeShadowPipeline applies the existing exact hash/mod/host/
bindless/equal1x-or2x predicate at prewarm, runtime configuration and creation.
Qualified shadow stages now supply fixed native binding metadata through the
existing PrepareFh1SceneBindings loader. Empty VS bindings, four2D texture
views and two samplers match shadow-native-bindings.json exactly: tf0 point/
point/point/no-aniso; tf1 fetch-constant filters/no-aniso; used mask3. Unknown
shadow PS is rejected by the binding helper. Compiled production-binding check
verifies every field and unknown rejection alongside packed-world checks.

Selected-pipeline dependency collection skips qualified shadow pairs but keeps
variants required elsewhere. Startup now loads501 rather than502 precompiled
variants, retaining452 prewarmed pipelines. Both shadow PSOs2DC3DEDC0BC15043 and
64787F66AF277EE9 log guest VS translated true, PS translated false. The VS is
still used with six other pixel shaders; this change removes one legacy pixel
load, not both stages' binary dependencies.

Async creation remains enabled for shadows as for packed-world. Native roots/
bindings are prepared before queuing, and pending legacy stage pointers stay
null. The later layered/blended shader-selection block explicitly excludes
shadow pipelines. Native PSO failure uses the existing locked lazy legacy load
and restored root. Offline producer preloading remains unchanged.

Validation under .local/native-renderer:
- shadow-bindings-build.log and restored-build.log succeed. Restored production
 DLL exactly matches candidate after diagnostic injection removal.
- Both compiled admission checks, production packed/shadow binding checks and
51 contract tests pass. Tests were adjusted to the centralized shadow predicate.
- shadow-bindings-smoke PID41496 normal exit, two captures/frame2800.
- shadow-bindings-fallback-diagnostic.dll temporarily forces native shadow PSO
 failure. PID48912 logs successful legacy fallback for both shadow PSOs (VS/PS
 translated true), verifies452 prewarmed pipelines and exits normally. Source
 was restored and rebuilt; diagnostic must never be staged as production.
- shadow-bindings-rdc PID48304 normal exit; shadow-bindings-active-parity/
 report.json asserts actual native VS and PS bytes and compares all3 vertex
 outputs and6 color/depth targets against legacy VS substitution, all exact.
 This replay is at2x;1x admission/binding metadata is covered structurally.
- shadow-bindings-runtime-evidence.json preserves available startup/fallback
 and error evidence. Only known device warning observed in successful runs.

Performance: shadow-bindings-abba-summary.json compares A174F812/33BFFCCE at2x.
PIDs4080/36648/50088/4792 all normal exits with two captures/frame2800. Last900
nonzero frame rows, process window34-46s, no build/replay overlap. CPU+4.199%,
median-0.601%,p95+2.874%,private+0.153%,working-0.204%; per-run draw/vertex/GPU
workload is recorded. Mixed four-run evidence, not a speed gain or proof of
lower hardware requirements. Retained as verified dependency reduction;
CPU/tail-latency attribution remains unresolved.

Next: inspect/validate native A3B9 VS with its six other captured PS pairings:
11824C2EC1B156C6,22DA22B5639EBAE4,26C4FD34AECBE4DE,26EB620936001876,
8418C40F121D7EA7,FCDF9BE8C57F7D01. The native vertex program is independent of
PS math, but all draw outputs and stage-specific loading/async/fallback rules
must be verified before broadening admission and removing its remaining load.
Then own12-byte geometry through the existing bounded cache. Other shader
families, texture processing, analysis, command/register state and512MiB shared
memory remain. Native shader replacement is not full renderer retirement.

### Shadow-mask vertex program native at1x/2x - 2026-09-07

Current built/staged DLL SHA256
A174F8127BEA30681B724AB6BA96C5B7DE4115B01961F2F06806244B00BDD71C,
.local/native-renderer/shadow-vertex-candidate.dll. Rollback:
shadow-mask-1x-candidate.dll (CC7699CE...). Source snapshot shadow-vertex-source/
files.json contains three files; before-shadow-vertex-pipeline_cache.cpp is the
previous source. Full optimization/Xenos retirement goal active and incomplete.

Added SDK fh1_shadow_mask.vs.hlsl and its bytecode/d3d12_5_1/fh1_shadow_mask_vs.h.
The native program decodes12-byte FLOAT3 vertices from fetch95 (ucode vf0),
applies index endian/clamp and vertex endian, then computes four ordered
z,x,y,w dot products using the existing depth-shader arithmetic pattern. Loaded
w is exactly1, including NaN inputs; it does not borrow the depth model's
conditional w. TEXCOORD0 gets the original projected position; SV_Position gets
the original flag-dependent reciprocal/xy/z adjustment and explicit NDC MAD.
Shared SRV/UAV loads remain, so geometry memory ownership is not retired.

Pipeline selection uses the existing exact shadow-pair/VSmod1/PSmod
0000400300000001/bindless/host/equal1x-or2x gate. That branch now selects both
native VS and PS. Existing legacy retry, scheduling and binding loading remain.
Production bytecode matches the standalone candidate exactly. Native VS149
slots versus legacy173; compiler counts are not runtime performance claims.

Evidence under .local/native-renderer:
- shadow-vertex-1x-parity/report.json: all3 matching draw boundaries,768 vertex
 output bytes and94371840 color/depth bytes exact.
- shadow-vertex-2x-parity/report.json: all3 boundaries,768 vertex output bytes
 and377487360 color/depth bytes exact. Both export actual legacy.dxbc.
- shadow-vertex-rdc PID26472 normal exit. shadow-vertex-active-parity/report.json
 verifies live native VS bytes and exact per-draw vertex/color/depth comparison
 when restoring the original vertex shader. Native PS remains active.
- shadow-vertex-validation-summary.json records scope and hashes. Build log
 shadow-vertex-build.log succeeds. Compiled shadow and packed-world admission/
 fallback checks plus51 contract tests pass.
- shadow-native-bindings.json records next removal target from the verified2x
 pack: vertex empty textures/samplers/mask0; PS texture entries
 (2,tf0,unsigned),(3,tf0,signed),(5,tf1,unsigned),(6,tf1,signed), all2D.
 Sampler slot1/tf0 has point mag/min/mip and disabled aniso; slot4/tf1 has
 fetch-constant mag/min/mip and disabled aniso. Used mask3. Do not reuse packed-
 world all-fetch-constant samplers blindly for this pair.

Performance: shadow-vertex-abba-summary.json, CC7699CE versusA174F812 at2x.
PIDs43644/51028/45220/32712 all normal with two captures/frame2800. PID43644 was
reused; select its newest20260907T123626Z session. Last900 nonzero frame rows,
process window34-46s; no replay/build overlap. CPU+3.947%,median-0.765%,
p95-1.377%,private+0.175%,working+0.742%. Per-run workload is recorded in the
summary. Four runs on5800X/RTX4080 give mixed evidence, not a proven overall
speed gain or lower minimum hardware requirement. Retained as exact native
stage coverage with CPU-performance attribution unresolved.

Next: stop loading the now-native shadow programs solely for binding metadata,
using the verified fixed layouts and lazy legacy fallback. Preserve async for
this pair just as for packed-world. IsFh1NativeScenePipeline currently drives
several other shader selections; if extended, exclude the shadow pair from the
layered/blended selection branch and prevent forced synchronous creation.
Shared shader variants used by unqualified pipelines must still preload.
After that, prove/own12-byte shadow geometry through the existing bounded
geometry cache. Other families, texture processing, analysis, command/register
state and512MiB shared memory remain; full retirement is not complete.

### Native shadow mask extended to1x; missing preview pack repaired - 2026-09-07

Current built/staged DLL SHA256
CC7699CE7908CFC4309DA52ED8D399CBD029F678D3CD44BA7763619B41B13A3C,
.local/native-renderer/shadow-mask-1x-candidate.dll. Rollback:
shadow-mask-candidate.dll (581B9203...). Source snapshot shadow-mask-1x-source/
files.json lists five files; before-shadow-1x-pipeline_cache.cpp and
before-shadow-1x.ps.hlsl preserve previous source. Goal active and incomplete.

First1x capture PID7064 exited normally but rendered incorrectly: the active
AppData preview cache had only the2x pack. Startup missed0041ED33AC536E1F/mod1,
aborted analysis initialization and emitted repeated backend errors. This run
(shadow-mask-1x-rdc) is INVALID parity evidence. Located the checkpoint's
complete1x pack, verified all metadata/checksums, and staged it with the existing
tools/native-shader-pack.py stage command, scale1, into the active preview cache.
SHA256 D147EE68C87D0298E0C1C394A83F68597492D4A0385BF507540EC63D9DCBA765,
21987entries/468092976bytes. No save/config files were manually touched.
The ready1x capture PID44456 loaded11628 analyzed shaders/502variants, verified
452 pipelines and exited normally. Only the known device warning remains.

One HLSL source now compiles2x (FH1_SHADOW_PIXEL_SCALE default0.5) and1x
(FH1_SHADOW_PIXEL_SCALE=1.0) pixel-position variants. Pipeline gate admits only
equal1x1/2x2 scales, exact previous VS/PS hashes and modifications, bindless host
targets. It selects the matching compiled PS; other scales still use legacy.
Legacy fallback and scheduling unchanged. Production2x bytecode is unchanged;
production1x matches the verified standalone candidate byte-for-byte.
Added bytecode/d3d12_5_1/fh1_shadow_mask_1x_ps.h. Modified admission check covers
scale combinations1-4 and all previous negative cases. Both compiled shader
gates and51 contract tests pass. Build: shadow-mask-1x-build.log.

Evidence under .local/native-renderer:
- shadow-mask-1x-ready-rdc is the valid legacy1x capture. The actual PS bytes
 match mod0000400300000001 in the verified1x pack; shadow-mask-1x-modification.json.
- shadow-mask-1x-parity.py/report.json checks all3 matching draws and6 targets:
 94371840color/depth bytes exact. legacy.dxbc exported there.
- shadow-mask-1x-active-rdc PID20972 exits normally; shadow-mask-1x-active-parity/
 report.json verifies actual native PS and exact final color/depth substitution
 back to legacy. shadow-mask-1x-preview.png inspected: world, car, road, crowds,
 shadows and HUD intact at1280x720.
- shadow-mask-1x-abba-summary.json compares581B9203 versusCC7699CE, all at1x.
 PIDs29092/17484/22036/43644 normal, two captures/frame2800. Last900 nonzero
 frame rows/process window34-46s; no replay/build overlap. CPU+3.975%,
 median+2.350%,p95+5.975%,private+0.012%,working+0.193%. Candidate workload:
 draws+1.302%,vertices+1.467%,guest GPU time+4.920%. This is NOT a speed win.
- Targeted existing GPU timestamp runs PIDs11428 baseline/17804 candidate both
 exit normally. shadow-1x-targeted-profile-summary.json joins their corpus to
 preserved shadow-1x-profile-baseline.log/candidate.log. Main3-draw family
 8F17E2B502A6BF62 averages571050ns(15samples) versus555520ns(16samples).
 Smaller8-draw family4CB4811C3D2317ED averages57958ns versus62464ns. First
 shader pair identifies a pass, not necessarily every draw. These limited
 instrumented samples do not explain/erase the whole-frame regression.

Retained as verified1x native coverage and restored local1x startup, with
whole-frame performance attribution unresolved. Lower resolution uses roughly
2540MiB private memory in these runs versus roughly4760MiB in preceding2x
runs, but that cross-resolution observation is not a controlled shader gain
or a minimum-hardware guarantee. Default launch resolution was not changed.
Next: retire shadow VS/binding dependencies and investigate actual CPU/texture/
command costs rather than equating ALU-slot reductions with speed. Broader
renderer still depends on other shader families, legacy texture processing,
analysis, command/register state and512MiB shared memory. Full retirement is
not achieved. Do not reuse the failed missing-pack capture as validation.

### Exact shadow-mask pixel stage integrated at2x - 2026-09-07

Current built/staged DLL SHA256
581B920385834CB63D05B80B40AC0CCC5721425FAAAD1FF20DA2C57BE250DCC3,
.local/native-renderer/shadow-mask-candidate.dll. Rollback:
packed-bindings-candidate.dll (2A405FD0...). Source snapshot shadow-mask-source/
files.json contains five files. before-shadow-mask-pipeline_cache.cpp and
before-shadow-mask.ps.hlsl preserve preceding source. Full goal remains active
and incomplete; this is a qualified2x pixel stage, not full Xenos retirement.

Reconstructed all30 instruction groups4-33 of93626E75D17576C5, retaining paired
ALU reads before writes, zero-product behavior, unfused arithmetic and ordered
dot products. The old implementation used projected coordinates instead of
floor(SV_Position.xy)*0.5 for guest pixel position, incorrectly saturated a
bias and changed arithmetic/output semantics. A position-only diagnostic still
failed parity. The complete exact form passes. Twelve packed float constants
map to guest[0,1,8,9,10,24,25,27,32,33,254,255]; five texture fetches use the
existing verified sampler bindings. Straight-line native code has288 slots,
legacy481. write-shadow-mask-exact.py documents the bounded reconstruction and
asserts instruction/constant coverage, using prior ALU helpers.

Updated SDK fh1_shadow_mask.ps.hlsl and bytecode/d3d12_5_1/fh1_shadow_mask_ps.h.
Pipeline selection requires bindless host targets, scale2x2, VS A3B9ED5D5C87230E
mod1 and PS93626E75D17576C5 mod0000400300000001. Actual capture legacy bytes
match that exact modification in the loaded shader pack (shadow-mask-modification.json).
Other scales and identities retain legacy; async scheduling/bindings unchanged.
Native PSO failure retries the existing legacy pipeline/root. Compiled admission
check tools/check-fh1-shadow-mask.py covers all single-bit identity/mod mismatches,
scale1-4 combinations, bindless off and ROV exclusion. Updated packed-world
fallback harness for the additional fallback condition. Both checks and51
contract tests pass. shadow-mask-build.log succeeds; production DXBC exactly
matches the verified standalone candidate.

Evidence under .local/native-renderer:
- shadow-mask-exact-parity/report.json: original captured final color/depth
 125829120bytes exact. shadow-mask-every-draw-parity/report.json checks all3
 matching draws and6 color/depth targets,377487360bytes exact.
- shadow-mask-rdc capture PID33140 normal exit; shadow-mask-active-parity/
 report.json verifies actual native PS raw bytes and exact125829120 color/depth
 bytes after substituting the original legacy program. Three matching draws.
- shadow-mask-preview.png inspected: intact world/car/road/crowds/HUD/shadows.
- shadow-mask-validation-summary.json collects stage/admission/parity evidence.

Performance: shadow-mask-abba-summary.json, A1/B1/B2/A2 PIDs50312/48008/28484/44844
all normal exits, two captures at frame2800. CPU+0.141%, median+0.642%,p95+1.044%,
private-0.479%,working+0.344%. Workload means candidate draw count-2.851%,
vertices+0.500%,guest GPU time+0.346%. No build/replay overlapped these runs.
Four stationary2x runs on5800X/RTX4080 do not prove a speed win.
Targeted existing timestamp profiler PID18392 normal exit:
shadow-mask-pass-profile-summary.json/runtime.log/corpus.json. Same3-draw family
8F17E2B502A6BF62 averages959744ns over16samples, versus960989ns/15samples for
previous baseline (-0.130%). Thus the measured shadow-pass cost is effectively
unchanged despite fewer ALU slots. Do not claim lower hardware requirements.

Next: extend exact shadow pixel positioning to1x and other requested scales
with capture-based parity, then retire its legacy VS and binding loads. Also
investigate actual sampling/target/command costs: this shader substitution did
not materially reduce the measured pass duration. Existing shaders still use
legacy texture processing/descriptors, command/register state, analysis catalog,
other vertex/pixel families and512MiB shared memory. Preserve overall objective.

### Workload confound isolated; shadow-mask target measured - 2026-09-07

Previous goal turn was progress (native binding retirement with parity/fallback
validation). This turn leaves production source and staged2A405FD0 DLL unchanged.
The full retirement/lower-requirements goal remains active and incomplete.

Re-examined the authoritative per-frame CSVs for the four packed-bindings ABBA
runs. Last900 nonzero frame rows show candidate draw count+5.305%, vertices
+3.177%, guest GPU time+2.588%. Mean draws by run A1/B1/B2/A2:
3687.760 /3773.840 /3784.712 /3490.007. Pipeline misses are0-0.003/frame,
command stalls, resolve waits and present deadline misses are zero. Thus the
reported+1.685% median/+3.158% p95 cannot be attributed to native bindings from
these runs alone. Do not erase the measured results or claim a speed gain.
Evidence: .local/native-renderer/packed-bindings-workload-analysis.json, with
session names and per-run means. Future performance decisions must account for
scene workload variation even in the stationary test (traffic/time advances).

RenderDoc EventGPUDuration returned no samples for the existing capture.
packed-bindings-gpu-profile.py/report.json records this as unavailable, not zero
GPU cost. Switched to existing renderer GPU timestamp instrumentation using
--pinyon_shift_fh1_gpu_corpus=true; no source or save changes. AppData2x run
PID50784/session20260907T115704Z exits normally. Output packed-bindings-pass-profile;
packed-bindings-pass-profile-corpus.json copies its payload-free corpus, and
packed-bindings-pass-profile-runtime.log preserves the profile log.
packed-bindings-pass-profile-summary.json joins latest cumulative pass-family
timings to first-draw shader metadata. Timestamps sample every60 source frames;
instrumented numbers guide prioritization, not uninstrumented speed claims.

Top cumulative sampled family8F17E2B502A6BF62 (attachment9A79B32F7ECF54CF)
has15 samples, exactly3 draws per sample, average960989ns/max969728ns.
Its first pair is A3B9ED5D5C87230E /93626E75D17576C5: shadow mask.
Other substantial families include world blended8D8A/BA6A (~1.27-1.31ms for
~800 draws) and C347/21B7 (~0.59-0.80ms, varying draw count). Totals across
families include different occurrence counts and startup; do not sum their
averages as a frame time or assume first-draw pair identifies every draw.

An old native fh1_shadow_mask.ps.hlsl exists but is not selected by current
pipeline_cache.cpp/command_processor.cpp. Older backlog claims are historical,
not current runtime evidence. Compiled it unchanged with FXC ps_5_1/O3 into
shadow-mask-existing.dxbc and replayed all matching pair draws in the current
packed-bindings-rdc capture. shadow-mask-existing-parity.py/report.json:
depth83886080bytes exact, color41943040bytes differs. It remains disabled.
The directory exports actual legacy.dxbc and legacy.asm for exact reconstruction.
Do not enable that old approximation on visual inspection alone. Next action:
reconstruct the shadow-mask pixel program preserving actual ALU order, sample
coordinates/decoding and output semantics; test captured color at each draw,
then broader inputs and performance before selecting it in production.

### Packed-world native bindings and lazy legacy pixels - 2026-09-07

Current build/staged DLL SHA256
2A405FD05AC41D3F40465582DDDD8D7FE8CFAC1ED5BD5E82C97B352C82CA9666,
.local/native-renderer/packed-bindings-candidate.dll. Rollback is
remaining-packed-candidate.dll (BE349BEA...). Source snapshot:
packed-bindings-source/files.json; before-packed-bindings-pipeline_cache.cpp/.h
preserve the previous source. Goal active and incomplete.

Qualified VS6934/mod7F with the nine native PS hashes/mod00004000005B007F,
bindless resources and host targets now use native per-stage binding metadata.
One fetch-order table supplies both admission and the existing binding loader.
Seven fetches maximum; each has one sampler and unsigned/signed texture views.
The compiled packed-world check verifies all nine orders, every binding index,
filter, used mask, dispatch and mismatch/fallback gates. No new dependency.

The selected prewarm pipelines determine needed legacy variants once, retaining
any variant used by an unqualified pipeline. Startup loads 502 rather than511
precompiled variants and still verifies452 pipelines. The shared vertex remains
loaded for other uses; all nine native pixel binaries no longer preload.
Packed pipelines retain async creation: their complete native bindings/root
are ready before queuing, and pending legacy stage pointers remain null.
Existing scene families keep their previous scheduling. Offline producer loads
remain unchanged. Native PSO failure still lazily loads legacy stages.

Validation under .local/native-renderer:
- packed-bindings-build.log and packed-bindings-restored-build.log succeed.
  Restored artifact hash matches the tested production candidate.
- 51 contract tests, compiled packed-world admission/binding/dispatch/fallback
  checks, and layered texture-binding checks pass.
- packed-bindings-smoke PID49192 and capture PID8736 exit normally, each with
  two captures at frame2800; packed-bindings-preview.png inspected.
- packed-bindings-active-parity/report.json verifies all211 matching draws,
  all nine native PS variants and the owned native VS. Replacing all nine PS
  with legacy code produces exactly83,886,080 color and83,886,080 depth bytes.
- packed-bindings-fallback-diagnostic.dll temporarily forces native packed
  PSO failure. PID31752 logs all nine successful lazy guest fallback pipelines,
  verifies452 prewarmed pipelines and exits normally with two captures/frame2800.
  The injection was removed and production rebuilt byte-identically. Never
  stage the diagnostic as production. Native metadata accepts legacy reloads.
- packed-bindings-validation-summary.json, packed-bindings-runtime-evidence.json
  and packed-bindings-runtime-errors.json preserve run evidence.

Performance: packed-bindings-abba-summary.json compares BE349BEA and2A405FD0.
PIDs47148,51100,12248,32112 all exit normally with two captures/frame2800.
Stationary AppData2x scene, process window34-46s, last900 nonzero frame times;
no build or GPU replay overlapped benchmarks. CPU-1.155%, median+1.685%,
p95+3.158%, private+0.209%, working-0.189%. Retained as dependency retirement,
not a speed gain; the measured frame-time increase is explicitly unresolved.
Four runs on5800X/RTX4080 do not establish lower hardware requirements.

Next: profile the remaining CPU/GPU cost before further native substitutions
accumulate small frame-time regressions. Packed shaders still consume legacy
texture descriptors/constants, and the shared VS binary has other users.
Guest analysis catalog, texture processing, other shader families, command
parsing/register state and512MiB shared memory remain. Retirement is not done.

### All captured packed-world pixel materials native - 2026-09-07

Current build/staged DLL SHA256
BE349BEA73BE42049F7BF7A6B2BF26874360A80468502160314795CFF8DE8113,
.local/native-renderer/remaining-packed-candidate.dll. Rollback: packed-blend-candidate.dll (352FF807...). Source snapshot remaining-packed-source/files.json
lists the15 changed/new files with repository-relative paths. Full Xenos
retirement remains active and incomplete; this is one captured vertex family.

Added native pixel programs for the remaining seven PS pairings under VS6934:
B98566FB7CE14699, C0E286228970074D, D96CCDCC3F783790, B1F8F94927415BED,
E163D0BE1C2F9775, EF18394497BDC2A6, 6B97D48A7336AB24. Together with A2C1/FF096,
all211 packed-world draws in the live capture now use native VS and PS code.
One explicit pixel-selection switch requires the existing VS6934/mod7F/host
admission, bindless resources and PS modification00004000005B007F. Unknown
hashes/modifications preserve the loaded legacy pixel program. Creation-failure
fallback, resource bindings, scheduling and geometry ownership are unchanged.

Five new HLSL sources use the shared fh1_world_material.hlsli. FF096/6B97 and
E163/EF18 differ only in the blend-mask channel; FH1_BLEND_MASK_Y provides the
observed y variant without duplicating their full source. Seven headers contain
the distinct compiled programs. Existing FF096 default and all seven shared-
source candidates compile byte-identically to their standalone verified shaders.
Static instruction counts (native/legacy): B985 936/1057, C0E2 562/681,
D96C 461/561, B1F8 489/613, E163 747/875, EF18 747/875, 6B97 870/997.
These compiler counts are not runtime speed measurements.

Evidence under .local/native-renderer:
- remaining-packed-corpus/ exports all seven actual shader binaries and
  reflection from packed-blend-rdc. modifications.json matches each exported
  SHA256 to exactly00004000005B007F in the loaded22012-entry shader pack.
  All have identical centroid input patterns and forceEarlyDepthStencil;
  constant packing is checked against reflection (11-14 float vectors).
- write-remaining-packed-materials.py reuses the validated ALU emitter and
  texture helpers. It asserts contiguous instruction coverage, supported
  control flow/fetch options, unique fetch order and descriptor-buffer size.
  It handles C0E2's scalar-only mulsc after serialize explicitly.
- remaining-packed-parity/report.json: seven replacements, all64 remaining
  draws,10,737,418,240 color/depth bytes exact at every matching draw boundary.
- remaining-packed-forced-parity/report.json: all64 color targets and
  5,368,709,120 bytes exact with b228 forced true in both implementations.
  remaining-packed-forced/patches.json records the two predicate opcode offsets
  for each legacy binary. Only AND-to-OR16 and checksum bytes change; diagnostic
  shaders are never selected by the game. Both lighting paths are tested with
  captured inputs, not every possible future game scene.
- remaining-packed-production/manifest.json maps source, symbol and channel
  macro to each header. All include-based bytecode comparisons pass, including
  unchanged FF096 default. remaining-packed-native/generation.json has counts.
- Live capture remaining-packed-rdc, PID42980 normal exit. remaining-packed-active-parity/report.json verifies all211 draws select all nine native pixel
  variants and the owned vertex shader, with no PS UAV. Substituting all nine
  legacy pixels yields exactly83,886,080 color and83,886,080 depth bytes.
- remaining-packed-validation-summary.json collects results. Build log:
  remaining-packed-build.log. Compiled production dispatch checks test all nine
  mappings, disabled vertex/bindless admission, all64 single-bit hash/mod
  mismatches and legacy preservation; vertex/geometry/fallback and layered
  binding checks pass. All51 contract tests pass.
- remaining-packed-preview.png inspected: intact road/world/car/people/HUD.
  remaining-packed-runtime-errors.json contains only the known device warning.

Performance: remaining-packed-abba-summary.json versus352FF807. Approved
AppData stationary2x test; PIDs40556,48428,28488,23660 all normal exit with two
captures/frame2800. Last900 nonzero frame times, process window34-46seconds;
no GPU replay/build overlap. CPU-0.936%, median+1.509%, p95+1.963%, private+0.544%,
working+1.096%. Retained as verified native material coverage with a small
measured frame-time cost, not a speed gain. Differences remain provisional
from four runs on5800X/RTX4080; no minimum-hardware claim or favorable-number
reruns. Further optimization remains part of the active goal.

Next: retire the now-native packed family's legacy shader loading/binding
metadata while preserving async behavior. Inspect all callers and any uses of
these PS hashes with other vertex families before changing eager loading.
The rejected lazy VS experiment forced synchronous compilation; do not repeat
that scheduling change. Native per-stage binding layouts can be derived from
the verified fetch-order/descriptor metadata, with lazy legacy fallback for
unqualified states. The broader renderer still uses guest shader analysis,
texture processing, command parsing/register state, other shader families and
512 MiB shared memory. Full retirement requires addressing those dependencies,
not just finishing the packed-world material list.

### Second packed world native material retained - 2026-09-07

Current build/staged DLL SHA256
352FF807A4FFA37011F50872D1465320A9EA50CB8754F5FAD11C2719E773F3A5,
.local/native-renderer/packed-blend-candidate.dll. Rollback: packed-pixel-candidate.dll
(2CE5D363...). Source snapshot packed-blend-source/ uses repository-relative
paths. Full Xenos retirement remains active and incomplete.

Added SDK fh1_packed_world_blend.ps.hlsl and generated PS header for
FF096DC71B188012/mod00004000005B007F, paired with native VS6934/mod7F on host
render targets with bindless resources. This covers another32 captured draws.
Its59 arithmetic/fetch groups preserve14 float constants, six fetches in order
5,7,13,1,0,2, texture-channel permutations, signed/gamma views, offsets/gradients,
centroid inputs, opaque early depth, scalar pairing and b228 lighting. FXC uses
870 static instruction slots versus997; this is not a runtime speed claim.
The existing fallback restores both legacy shader binaries and root.

The two native packed materials now share66 identical helper lines through
fh1_world_material.hlsli. Both include-based shaders compile byte-identically
to their replay-verified standalone versions; the existing A2C1 material's
header and bytecode are unchanged. No shader-loading, scheduling, geometry,
texture-cache or root-selection changes were made.

Evidence under .local/native-renderer:
- write-packed-world-blend-pixel.py reuses the existing arithmetic/texture
  emitter, asserts instruction7..65 coverage and14 constants.
- packed-blend-pixel-every-draw/report.json: all32 draws on packed-pixel-rdc,
  5,368,709,120 color/depth bytes exact at every matching draw boundary.
- packed-blend-pixel-forced-light/report.json: all32 color targets and
  2,684,354,560 bytes exact with b228 forced true in both implementations.
  Reference DXBC changes its two AND predicates at shader offsets0x4C60 and
  0x4CF8 to OR16 and recomputes the checksum using the existing SDK helper.
  Forced shaders are diagnostic only and never selected by the game build.
- packed-world-shared-include.dxbc matches the retained A2C1 pixel exactly;
  packed-world-blend-shared-include.dxbc and packed-world-blend-production.dxbc
  match packed-world-blend-pixel.dxbc exactly.
- Capture packed-blend-rdc, PID26464 normal exit. packed-blend-active-parity/
  report.json verifies all32 live draws use the native pixel and owned vertex
  shader; replacing the pixel with legacy matches83,886,080 color and
  83,886,080 depth bytes. Pixel UAVs are absent.
- packed-blend-validation-summary.json collects parity. packed-blend-build.log
  succeeds; compiled admission tests check both hash/modification pairs, all64
  single-bit mismatches, bindless disable, selection of the correct bytecode,
  and fallback. Layered binding checks and all51 contracts pass.
- packed-blend-preview.png inspected: intact world/car/people/HUD. Runtime
  errors are only the known ResolvePath device warning; archived separately.

Performance: packed-blend-abba-summary.json versus2CE5D363, approved AppData
stationary2x test. PIDs45284,39028,50860,36312 all normal exit, two captures at
frame2800. Last900 nonzero frame times and process window34-46seconds, no GPU
replay/build overlap. CPU-0.139%, median+0.387%, p95-0.342%, private-0.027%,
working-0.028%. Retained as verified native material coverage with effectively
unchanged performance. Tiny differences are provisional from four runs on
5800X/RTX4080; no unchanged reruns or minimum-hardware claim are warranted.

Next: migrate the remaining seven packed-world pixel pairings as a batch,
reusing the shared helpers and emitter. remaining-packed-materials.json audits
C0E286228970074D, D96CCDCC3F783790, B98566FB7CE14699, 6B97D48A7336AB24,
EF18394497BDC2A6, E163D0BE1C2F9775, B1F8F94927415BED. All have ucode dumps;
three lack compiled binaries in v5-shader-dump, so export their actual shader
bytes/reflection from an existing capture before comparison. FF096 and6B97
ucode differ only at fetch18: blend-mask x versus y. Reuse one source with an
explicit channel variant rather than duplicating its program. Other variants
have2-6 texture fetches and11-14 float constants, using already supported ALU
operations; verify their full fetch/control flow before conversion. Native
materials still depend on legacy bindings/texture processing and fallback,
and broader command/guest-state/shared-memory retirement remains required.

### Packed world native pixel program retained - 2026-09-07

Current build/staged DLL SHA256
2CE5D363C73CE22A4C693718F99B2B9346D57072FE9C11D6984B1424464397F6,
.local/native-renderer/packed-pixel-candidate.dll. Rollback is
packed-owned-wrap-candidate.dll (ADEABFDA...). Source snapshot packed-pixel-source/
contains repository-relative paths. Full Xenos retirement remains incomplete.

Added src/graphics/shaders/fh1_packed_world.ps.hlsl and its generated PS header
inside the SDK. Pipeline admission requires native VS6934E161812AB10B/mod7F,
host render targets, bindless resources and exact PSA2C1F872E049AD8B modification
00004000005B007F. This replaces the pixel program for115 captured packed-world
draws. Existing creation-failure fallback restores both original shader binaries
and root. Legacy shader loads, scheduling, geometry cache and root selection
are unchanged. The previous lazy-load experiment remains rejected.

Native material preserves14 packed float constants, seven texture fetches
(tf6,7,13,2,5,1,0), unsigned/signed/gamma decoding, coarse gradients/exponents,
fetch13 half-texel offset, exact descriptor order, centroid interpolation,
opaque early depth, b228 lighting, paired scalar previous-result ordering,
zero-multiply handling and output exponent bias. Sign-view admission only uses
channels consumed by each fetch. The64 arithmetic/fetch groups are expressed
directly without the translated control-flow loop. FXC static instruction slots
1065 versus1174, not a runtime speed measurement.

All evidence below is under .local/native-renderer:
- write-packed-world-pixel.py reuses the existing arithmetic emitter and pixel
  texture helpers. It asserts complete instruction8..71 coverage and14 constants;
  bare c0 must be included, not only constants with an explicit swizzle.
- Initial packed-world-pixel.dxbc / initial-fh1-packed-world.ps.hlsl are superseded
  by packed-world-pixel-masked.dxbc. Production output is byte-identical to the
  latter (SHA25670A3A8D1DFF8D2F54C44C3DA1087246FEB8E7FAA1C5FF3DA27AA6B7A01BFF6D0).
- packed-pixel-every-draw/report.json: initial candidate versus legacy pixel on
  packed-owned-mirror capture; all115 draws,230 color/depth targets and
  19,293,798,400 bytes exact. All captured b228 values are false.
- packed-pixel-masked-every-draw/report.json: final candidate, all115 color
  targets/9,646,899,200 bytes exact at every matching draw boundary.
- packed-pixel-forced-light/report.json: all115 color targets/9,646,899,200 bytes
  exact with b228 forced true in both shaders. Diagnostic reference changes
  only the two AND predicates to OR16 (byte offsets28172/28324) plus the DXBC
  checksum; FXC disassembly confirms both changes. Native diagnostic source
  forces its boolean expression true. Existing SDK DXBCChecksum code is reused
  by checksum-dxbc.cpp. This tests both lighting paths with captured inputs;
  these forced diagnostic shaders are never selected by the game build.
- packed-pixel-rdc capture PID41784, normal exit. packed-pixel-active-parity/
  report.json verifies all115 actual draws use the final native pixel and owned
  wrapped-load vertex shader, with no PS UAV. Replacing the pixel back with its
  legacy binary matches83,886,080 color and83,886,080 depth bytes exactly.
- packed-pixel-validation-summary.json collects the parity results.
  packed-pixel-build.log succeeds. Compiled production vertex/pixel admission
  checks test all64 single-bit hash/modification mismatches, disabled bindless,
  and fallback. Layered binding checks and all51 contracts pass.
- packed-pixel-preview.png from the normal timed candidate run was inspected:
  world, road, car, people and HUD remain intact. Runtime errors are only the
  known ResolvePath device warning (packed-pixel-runtime-errors.json).

Performance: packed-pixel-abba-summary.json against ADEABFDA, approved AppData
stationary2x open-world test. PIDs47996,50000,47752,48596 all normal exit with
2 captures/frame2800. Last900 nonzero frame times, process samples34-46seconds;
no GPU replay/build overlap. CPU+1.343%, median-1.263%, p95-4.129%, private+0.333%,
working+0.942%. Retained as a verified native shader migration with a modest
frame-time benefit in this four-run sample; small differences are provisional
on5800X/RTX4080, not a new minimum-hardware claim. No unchanged reruns needed.

Next: continue native pixel coverage (FF096DC71B188012 is the next32-draw
pairing in the earlier packed-world census), or remove this now-native pair's
legacy metadata/binary load while preserving async behavior. Native material
still uses the legacy texture cache, guest fetch/system constants, descriptor
tables and shader pack bindings/fallback. Other shader families, command
parsing and the512 MiB shared-memory allocation remain retirement work.

### Packed world lazy legacy load experiment rejected - 2026-09-07

Production remains ADEABFDA395A43D20132E52F7706F2567ECA56A6782A7D8C0B2A3E3A08CE285A
(packed-owned-wrap-candidate.dll). Source and both build/staged binaries were
restored. Full Xenos retirement remains active and incomplete.

Rejected candidate C0DF64102E7DE39ECE511EAB8323AF2FFEBA2824B95B6ED65B8956C6165AD609
is preserved as .local/native-renderer/packed-lazy-candidate.dll, with source in
packed-lazy-source/ and focused diff packed-lazy.diff. It factored exact
VS6934E161812AB10B/mod7F/host-target admission, skipped its eager legacy binary
load, supplied empty native vertex bindings during prewarm/configuration, kept
pixel validation, and lazily loaded the original vertex program on native PSO
failure. It also forced synchronous configuration for this family, following
the existing scene policy. That scheduling change should be avoided in any
future retry: preserve async pixel creation and omit only pending native VS.
The consumer's legacy "translation" here is a precompiled DXBC pack load,
not runtime ucode compilation. Shader analysis catalog dependency remains.

Build packed-lazy-build.log, all51 contracts, compiled packed admission/load/
fallback checks and layered root-binding checks passed. A diagnostic startup
PID21076 (normal exit), packed-lazy-debug.log, records16 successful packed PSOs
with guest VS translated false. Startup variants fell511 to510; the same452
prewarmed PSOs were verified. The gameplay screenshot packed-lazy-preview.png
was inspected and intact. Existing native shader bytecode was unchanged;
this phase did not repeat the earlier byte-exact GPU replay parity audit.

All timing runs used the approved AppData save, stationary2x open-world test,
last900 nonzero frame times and process window34-46seconds. All normal exit,
two captures/frame2800; no build or GPU replay overlapped the timed windows.
ABBA PIDs41348,46932,49936,33700: CPU+1.755%, median+1.667%, p95+4.219%.
Reverse BAAB PIDs49852,45052,36416,40048: CPU+3.706%, median-0.279%, p95+2.548%.
Combined packed-lazy-combined.json: CPU+2.724%, median+0.690%, p95+3.380%,
private-0.119%, working-0.074%. These noisy5800X/RTX4080 measurements do not
establish causation, but both orders cost CPU and p95, so do not retain this
change or rerun it unchanged to chase a favorable result.

Next useful target: native PS A2C1F872E049AD8B/mod00004000005B007F, paired with
115 of211 packed-world draws in the prior capture. Its ucode is in
.local/v5-shader-dump/shader_A2C1F872E049AD8B.ucode.frag: seven texture fetches
(tf6,7,13,2,5,1,0), conditional b228 lighting, and existing color/coverage
semantics need preservation. Reuse established native pixel texture helpers
and validate byte-exact output before changing runtime admission. The legacy
packed vertex load can be revisited with preserved async behavior alongside
that substantive pixel replacement.

### Packed world geometry ownership retained - 2026-09-07

Current built/staged DLL SHA256
`ADEABFDA395A43D20132E52F7706F2567ECA56A6782A7D8C0B2A3E3A08CE285A`,
saved as .local/native-renderer/packed-owned-wrap-candidate.dll. Rollback:
packed-world-candidate.dll (04FD0E18...). Source snapshot: packed-owned-wrap-source/
with repository-relative paths. Full Xenos retirement remains incomplete.

The native VS6934E161812AB10B family now owns GuestDMA indices and its complete
28-byte fetch95 stream using the existing indexed mesh proof/cache. Its scene
stride is28; it uses the depth root's direct vertex SRV with ordinary pixel
texture tables. Blended/lit continue using the layered fixed-material root.
The existing shader hash/modification/host-target admission is preserved; the
new geometry variant also requires bindless resources and no vertex/pixel
memexport. Root mismatch, proof/import failure, unsupported indices and shader
creation failure preserve the shared path. Index/vertex ownership is all-or-
nothing for this family. Existing post-import alias revalidation and complete
read-extent keys are reused. No cache cap or bounds helper changes:32 MiB/512
entries, full28-byte extent. Other families and texture handling still use
shared memory, so the global512 MiB buffer is not removable yet.

The new FH1_SCENE_OWNED_GEOMETRY variant uses the existing bounded raw-load
helpers and has no UAV declaration. Default/shared shader bytecode remains
byte-for-byte identical to packed-world.dxbc. The final variant preserves the
separate normal load at address+12: folding it into Load4.w would change an
invalid shared-fallback address whose independent normal offset wraps to low
physical memory. That initial optimization was caught in review and removed.
The executable raw-load check now extracts the production packed LoadWord and
normal expression, testing physical limits and uint32 wrapping in both modes.
The corrected shader is packed-world-owned-wrap.dxbc. Do not use the older
packed-world-owned.dxbc /3883FA45 candidate as the retained version.

Evidence, under .local/native-renderer:
- packed-world-geometry-ranges/report.json: all211 draws indexed,16-bit, endian1;
  all complete28-byte fetch ranges fit, maximum132,440 bytes. The existing
  tools/check-fh1-depth-geometry.py passes all211 captured index fixtures.
- packed-owned-shader-parity/report.json: initial SRV-only variant matches all
  11,985,024 vertex-output bytes and83,886,080 color plus83,886,080 depth bytes
  against the prior native shader on its original shared-input capture.
- packed-owned-mirror-rdc/frame_frame3066.rdc (PID27856, normal exit): a temporary
  capture-only RequestRange refresh provides authoritative shared references.
  packed-owned-mirror-audit/report.json confirms all211 draws own both inputs;
  383,484 index bytes and5,548,900 vertex bytes match fresh shared references
  exactly. Active VS is the owned variant; vertex/pixel UAV declarations are
  absent. Capture instrumentation is removed from production.
- packed-owned-wrap-parity/report.json replaces the initial owned shader in
  that capture with the corrected separate-normal-load variant: all211 full
  vertex outputs and both color/depth targets match exactly at the same byte
  counts. Owned buffer data/admission are unchanged by the shader correction.
- packed-world-shared-wrap-check.dxbc is byte-identical to the prior shared
  shader. packed-owned-wrap-build.log is the successful production build.
  Actual command_processor.cpp matches packed-owned-production.cpp exactly,
  proving the capture-only reference residency additions are absent.
- Admission/memexport/root-fallback checks, index ownership, post-import
  revalidation, raw-load boundary/wrap checks, and all51 contract tests pass.
  Missing depth root is explicitly covered for the packed geometry path.
- Corrected production screenshot packed-owned-wrap-preview.png inspected;
  normal gameplay rendering is intact.

Performance: packed-owned-wrap-abba-summary.json versus04FD0E18, approved
AppData stationary2x open-world test; PIDs36328,50936,49924,33920 all normal
exit, two captures at frame2800. Last900 nonzero frame times and process
window34-46seconds, no replay or build overlap. CPU-2.973%, median+0.332%,
p95-0.649%, private-0.473%, working-1.018%. Retained as a verified dependency
reduction with near-baseline frame times. Small differences are provisional
from one four-run sample on5800X/RTX4080, not a minimum-hardware claim.
The earlier packed-owned-abba results belong to the superseded3883FA45 shader
and are not combined with final measurements. No further unchanged reruns are
needed to chase a favorable number.

Next: remove this native vertex family's remaining startup translation and
metadata dependency using existing precompiled-binding support, or continue
native pixel conversion for its high-count pairings. Its pixel programs,
command parsing, guest register state, texture processing and other shader
families still depend on Xenos. Do not equate owned geometry with full retirement.

### Packed world vertex shader retained - 2026-09-07

Current built/staged DLL SHA256
`04FD0E1856C583DC0123D2078B2430D88A300BAD571D41F9006BCDBDF0028D24`,
saved as .local/native-renderer/packed-world-candidate.dll. Rollback baseline:
scene-fixed-dirty-candidate.dll (6423887A...). Source snapshot is under
packed-world-source/ with repository-relative paths. Full retirement remains
incomplete; the fixed material and owned geometry work below remains active.

VS6934E161812AB10B now uses fh1_packed_world.vs.hlsl, a direct form of its40
arithmetic instructions and28-byte position/packed-normal/two-UV/color fetches.
It preserves all seven TEXCOORD outputs, fog calculations, zero-multiply rules,
scalar previous-result ordering, guest endian/index handling and NDC adjustment.
Float constant packing remains the original20 vectors. Compiled shader uses348
instruction slots versus547 in the old translation; this is a static compiler
count, not a direct runtime speed claim. Original shared SRV/UAV inputs remain.

Pipeline admission requires the exact vertex hash, modification0x7F (seven
interpolators, standard vertex variant), and host render targets. Pixel shaders
and root layout are unchanged. Pipeline creation failure restores original
translated stages/root through the existing fallback. Older disabled native
world experiments remain disabled. The initial297AC5A3 build mistakenly used
their disabled switch and was caught by live bytecode verification; it is
preserved as packed-world-inactive-candidate.dll and was never benchmarked.
The active04FD0E18 build uses its own exact admission condition.

Correctness evidence under .local/native-renderer:
- packed-world-parity/report.json replaces the old shader in the retained
  scene-fixed-dirty capture with the new DXBC:211 draws across9 pixel pairings,
  all11,985,024 vertex-output bytes exact, plus83,886,080 color bytes and
 83,886,080 depth bytes exact at the final affected target event.
- packed-world-active-rdc/frame_frame3088.rdc (PID44824) confirms installed
  native bytecode is selected. packed-world-native-parity/report.json replaces
  it with the original shader on that same frame: all211 draws and the same
  vertex/color/depth byte counts match exactly. Complete interpolators are
  included, not just positions. Both replay scripts remain available.
- Pixel pairings/counts: A2C1F872E049AD8B (115), FF096DC71B188012 (32),
  C0E286228970074D (19), D96CCDCC3F783790 (16), B98566FB7CE14699 (15),
  6B97D48A7336AB24 (8), EF18394497BDC2A6 (3), E163D0BE1C2F9775 (2),
  B1F8F94927415BED (1).
- Active gameplay capture exited normally; packed-world-active-preview.png
  was visually inspected. The earlier inactive capture is not selection proof.
- packed-world-active-build.log records the successful release build. The
  new tools/check-fh1-packed-world.py compiles actual admission/fallback gates,
  rejecting every single-bit hash/modification mutation and the ROV path.
  Fixed-material binding checks and all51 contract tests pass. Final admission
  and contract tests passed again after removing the disabled-switch mistake.

Performance against6423887A, approved AppData stationary2x open-world run,
last900 nonzero frame times and process samples34-46seconds. All eight runs
normal exit, two captures, frame2800 completion; no replay overlap.
ABBA (39724,26264,44096,49032): median-4.728%, p95-7.140%, CPU+4.370%,
private+0.463%, working-0.178%. First baseline was an outlier at18.348/23.649ms
versus second16.765/21.673ms. Reverse BAAB (15532,47484,15128,46124):
median-0.839%, p95-1.080%, CPU-4.285%, private-0.087%, working-0.420%.
packed-world-combined.json: median-2.821%, p95-4.201%, CPU+0.056%,
private+0.188%, working-0.299%. Retain: both orderings improve frame times,
CPU is effectively flat in combination. Treat benefit as modest/uncertain;
the first baseline outlier inflates the combined result. Only5800X/RTX4080
was measured; no minimum-hardware claim.

Next: remove this family's shared-memory geometry dependency using the
existing28-byte indexed mesh proof/owned cache and a qualified SRV-only root,
after auditing actual index/fetch usage. Its pixel stages still use translated
programs, and current startup still translates the vertex for metadata/fallback.
Do not mistake native VS selection for retirement of those dependencies.
The remaining shader families, command parser, guest register state and texture
processing also still prevent full Xenos retirement.

### Fixed blended/lit materials retained after redundant binding removal - 2026-09-07

Current built/staged DLL SHA256
`6423887A63C888BE6F01DF45D778916D34307C4EB197E521F6898EC7F30FCD27`,
saved as `.local/native-renderer/scene-fixed-dirty-candidate.dll`.
Rollback baseline is scene-owned-candidate.dll (56A49A2A...). Source snapshot:
scene-fixed-dirty-source/ (repository-relative paths). Full Xenos retirement
remains incomplete. The previous rejected 8ACEAA56 candidate is not staged.

This retains the previously verified fixed texture variants for blended and
lit native scene pairs, their layered root reuse, exact geometry ownership,
and the layered-only non-indexed geometry guard described below. It removes
unbounded pixel arrays and b4 descriptor-index uploads from these two native
pairs. Other renderer families still require bindless resources and Xenos
infrastructure; this does not establish lower global feature requirements yet.

The previous candidate rebound unsigned texture, signed texture and sampler
whenever pixel descriptor state became dirty. A structured RenderDoc command
census confirmed redundant work: root382 had797 writes each to slots3,8,9;
793 signed-texture and790 sampler writes repeated their prior descriptors.
The revised capture has3 signed-texture writes,6 sampler writes and797 unsigned
writes, none redundant. Source change stores three uint32 descriptor indices
on the command processor, compares each independently after descriptor updates,
and clears only its changed root bit. Actual root/heap invalidation still forces
rebinding even when indices stay equal. Binding emission uses these indices.
No texture/resource cache, root layout, shader arithmetic, geometry bytecode,
or cache-cap change was added. The optimization also applies to layered draws.

Correctness evidence, under .local/native-renderer:
- scene-fixed-dirty-rdc/frame_frame3178.rdc, PID39676 normal exit; screenshot
  scene-fixed-dirty-preview.png visually inspected and intact.
- scene-fixed-dirty-binding-census.json and scene-fixed-binding-census.json
  give the before/after command counts, resetting tracked tables at root,
  command-list and descriptor-heap changes.
- scene-fixed-dirty-texture-inputs.json: all499 blended/lit draws (254/245)
  match scene-owned-mirror exactly in owned index/vertex bytes, texture views,
  all mip contents of13 textures, and samplers. Both fixed pixel bytecodes are
  verified active with exactly two resources, one sampler and no b4. Zero
  unmatched draws. compare-scene-fixed-dirty-texture-inputs.py reproduces it.
- scene-fixed-dirty-layered-inputs.json: all356 layered draws match against
  scene-owned-mirror in draw parameters, texture views, all mip contents of8
  textures and samplers, with zero unmatched draws. This audit checks material
  inputs; layered geometry/shader code was not modified by this optimization.
- Pixel shader bytecodes are the same as the prior fixed candidate, whose
  visible representative color/depth replay parity is documented below.
  No new full-frame pixel equivalence claim is made from cross-capture inputs.
- Release build passed (scene-fixed-dirty-build.log). Executable depth-index,
  mesh-ownership and fixed-material binding checks passed; all51 contract tests
  passed. The binding check extracts actual production branches and covers
  independently changing slots, unchanged dirty state, first-use zero indices,
  heap rollover with unchanged index, root switches, upload restoration and
  missing-root fallback. No runtime edits occurred after the tested build.

Performance versus retained56A49A baseline, identical approved AppData2x
stationary open-world test, last900 nonzero frame times and process samples
34-46seconds. All eight runs exited normally with two captures at frame2800;
no replay overlapped benchmarks. ABBA PIDs23244,43320,32312,26264:
CPU+0.624%, median+1.117%, p95+2.625%, private-0.574%, working-0.214%.
Reverse BAAB PIDs50308,2384,32844,27740: CPU-1.642%, median+1.160%,
p95+0.366%, private+0.049%, working+0.500%.
scene-fixed-dirty-combined.json: CPU-0.508%, median+1.139%, p95+1.480%,
private-0.263%, working+0.143%. The prior repeated+4.89% CPU cost is no longer
present. Retained as a dependency-reduction step with near-baseline performance
and a measured small frame-time cost, not a speedup or minimum-hardware claim.
Only the local5800X/RTX4080 was measured.

Next: continue removing shared geometry and translated shader dependencies
from remaining high-count families using remaining-geometry-families/report.json.
Do not keep rerunning this unchanged candidate to seek a more favorable number.
The command parser, guest register/shader state, shared memory for remaining
families, and texture processing still block full Xenos retirement. Investigate
larger costs there; fixed material inputs now have an established bounded path.

### Blended/lit fixed texture slots verified, rejected for CPU cost - 2026-09-07

Current built/staged DLL remains
`56A49A2AB252B63A78F0118DDC18EFE89F47F3074C53F657C274DE3033778E24`
(scene-owned-candidate.dll). Source was restored and rebuilt; the rebuilt hash
matches this baseline exactly. Full Xenos retirement remains incomplete.

Tested candidate: scene-fixed-candidate.dll, SHA256
`8ACEAA563C9441CC9F88CDEB0AAB70166FA374CE7DCA3127DE481C6B757180CA`.
The candidate reused the layered root for the exact blended/lit native pairs,
with unsigned t0 space1, signed t1 space1 and sampler s0, omitting b4 and
unbounded pixel arrays. It reused existing material binding and geometry
ownership paths. The layered non-indexed geometry shortcut was explicitly
restricted to VS3BC346726C1C2535 to avoid applying its stride to these pairs.
Both legacy pixel variants compiled byte-for-byte identically to their prior
versions; fixed variants compiled without unbounded descriptor-table support.
No geometry bytecode or cache-cap changes.

Correctness evidence (all paths below are under .local/native-renderer):
- scene-fixed-shaders/compile-report.json: unchanged default variants; new
  fixed reflection contains exactly two textures, one sampler and no b4.
- scene-fixed-rdc/frame_frame3087.rdc: PID44096, normal exit, intact screenshot
  scene-fixed-preview.png, inspected visually.
- compare-scene-fixed-texture-inputs.py / scene-fixed-texture-inputs.json:
  exact multiset equality against scene-owned-mirror/frame_frame3124.rdc for
  all 499 draws (254 blended, 245 lit). Owned index/vertex bytes, texture views,
  all mip contents of 13 textures, and samplers match, with zero unmatched draws.
- scene-fixed-visible-reference-replay.py / .json: sampled visible events14841
  (blended) and14855 (lit) match all 167,772,160 color/depth bytes per event.
  Fixed shader registers are remapped to the old capture's descriptor indices;
  replacements are removed between families. Each sampled draw changes all
  eight target/sample images. This is representative output evidence, not a
  full-frame output parity claim. The earlier scene-fixed-reference-replay.json
  sampled invisible draws and is not useful pixel parity evidence.
- Candidate depth-index, mesh-ownership and fixed texture binding executable
  checks passed, plus all51 contract tests. Updated checks are archived with
  the candidate. Restored baseline depth-index/mesh checks and all51 contracts
  passed again; scene-fixed-restore-build.log records the successful rebuild.

Performance: approved AppData launch, existing stationary 2x open-world test,
all eight runs normal exit with two captures at frame2800. Last900 nonzero
frame times; process sample window34-46seconds. No replay overlapped benchmarks.
ABBA (PIDs41204,33332,17336,4184): median-1.92%, p95-3.41%, CPU+3.80%,
private+0.50%, working+0.75%. Reverse BAAB (33820,31016,36204,25844):
median-1.13%, p95+1.45%, CPU+5.96%, private+0.15%, working-0.31%.
Combined scene-fixed-combined.json: median-1.53%, p95-1.00%, CPU+4.89%,
private+0.32%, working+0.22%. The repeated CPU cost is undesirable for lowering
requirements; do not promote this candidate as a performance improvement.
These measurements are only on the local5800X/RTX4080, not minimum hardware.

All seven modified candidate source/test files and both generated headers are
preserved under scene-fixed-source/ with repository-relative paths. Before
snapshots are before-scene-fixed-*. The source and runtime are restored to the
prior retained implementation; unrelated repository work is untouched.

Next: investigate the fixed binding CPU cost before adopting it. Existing
UpdateBindings invalidates all three fixed material root tables whenever the
pixel descriptor state is dirty, even when the signed/null view or sampler
stays unchanged. Redundant table updates are a hypothesis to measure, not a
proven cause. Reuse the existing root dirty tracking/heap invalidation rather
than introducing another descriptor cache. Alternatively continue converting
remaining high-count shared-geometry shader families from the existing census.
Command parsing, guest shader/register state, shared memory for other families,
and texture processing still prevent full Xenos retirement.

### Blended and lit scene geometry ownership retained - 2026-09-07

Current built/staged DLL SHA256
`56A49A2AB252B63A78F0118DDC18EFE89F47F3074C53F657C274DE3033778E24`,
saved as `.local/native-renderer/scene-owned-candidate.dll`.
Rollback baseline: terrain-maximum-candidate.dll, D6473754...
Full Xenos retirement remains incomplete.

The native blended pair (VS8D8A197476841A9A / PSBA6A2871A980A4E8)
and lit pair (VSAD2C355A6BE1EE87 / PS2F2137BF953DA7AF) now own
GuestDMA indices and their complete fetch95 vertex stream. Blended reads
16 bytes per vertex; lit reads 20, including its UV word beyond the position.
Admission requires the exact pair, no memexport, host render targets and the
qualified native root. Failed proofs/imports and unsupported indices retain
shared inputs; scene ownership is all-or-nothing. Existing mesh-depth and
terrain paths remain active. The 32 MiB / 512-entry cache cap is unchanged.

Both native pixel shaders read textures, not shared geometry, so these pairs
reuse the depth root's single direct vertex SRV with normal pixel slots.
Pipeline failure restores translated stages and the original root. New
FH1_SCENE_OWNED_GEOMETRY vertex variants omit UAVs and use the shared
fh1_scene_geometry.hlsli raw-load helpers, with vector fast paths and explicit
physical per-component zero bounds for direct root SRVs. Both existing shared
shader variants compile byte-for-byte identically to their before-change
versions (scene-owned-shaders/compile-report.json). The original lit shared
UV load stays inline to avoid an unrelated address-hoisting bytecode change.
Pixel shader bytecode is unchanged.

The indexed bounds helper/cache accepts the vertex read extent (default 12
for existing depth callers). It bounds max_index * stride + vertex_bytes,
rejects zero, unaligned or oversized extents, and admits stride16 only with
its complete 16-byte read. The depth proof key grows from 15 to 16 words,
including the read extent before the eight system words. A cached depth-only
position bound cannot be reused for a larger scene read. Scene draws pass
16/20 explicitly, then use the existing post-import alias revalidation and
fetch95 rebasing/residency skip. On scene failure the index binding also
returns to shared memory. Native scene pixels need no shared geometry read,
so the existing complete-owned-draw transition predicate applies.

Evidence selecting these families: remaining-geometry-families/report.json
counts 254 blended and 245 lit draws in the retained terrain capture, the
largest remaining groups after layered. scene-geometry-ranges/report.json
and raw per-event indices inspect all 499 draws in scene-root capture:
all indexed, zero base vertex, index endian1, complete ranges fit declared
fetch95 buffers. These are saved fixtures, not assumptions for other draws.

Root/shader qualification: scene-root-candidate.dll SHA256
6BC3746E8F9F654649D8EF0D59C4C7685C4BB20023AD8317C2241DA46973AFCA;
normal AppData PID13172, scene-root-rdc/frame_frame3122.rdc.
scene-root-parity/report.json verifies 499 draws use the expected compiled
variants and a zero-offset shared root SRV. Replacing them with previous
shared vertex shaders produces exact parity for all 5,803,712 vertex-output
bytes (including interpolators), the 83,886,080-byte color target and the
83,886,080-byte depth target across every sample. scene-root-preview.png
was viewed and scene intact. Root-only variant was not separately benchmarked.

Final ownership qualification: normal PID43384,
scene-owned-mirror-rdc/frame_frame3124.rdc and
scene-owned-mirror-audit/report.json. All 499 selected draws fully own
indices and vertex input; 222,490 index bytes and 1,432,080 vertex bytes
match freshly requested shared sources exactly at each draw. Audit tracks
all command-list PSOs, maps all draws, rejects unsupported command-state
operations, decodes actual bound indices/reset/endian/clamp, reconstructs
physical addresses from owned resource names plus descriptor/rebased offsets,
and checks no partial ownership. Diagnostic fresh-source requests were
removed; rebuilding reproduced the uninstrumented candidate hash exactly.
scene-owned-preview.png (candidate ABBA B2) was viewed: scene intact.

Performance versus retained terrain ownership D6473754...:
scene-owned-abba-summary.json: median -4.16%, p95 -4.93%, CPU -2.45%,
private +0.65%, working +1.50%. A2 baseline was slower (18.233/23.408 ms
median/p95 versus A1 16.882/21.212), so reverse order was run to qualify
that apparent gain. scene-owned-baab-summary.json: median -0.20%, p95
-1.08%, CPU -1.37%, private +0.06%, working +0.35% -- essentially flat.
scene-owned-combined.json has all eight runs and mean changes: median
-2.22%, p95 -3.05%, CPU -1.92%, private +0.36%, working +0.93%.
Treat this as no measured regression with a modest/uncertain speed benefit,
not a universal FPS claim. All eight runs exit normally, complete frame2800
and capture twice. ABBA PIDs44152/49472/44080/25736; BAAB actual order
33740/18532/35588/5164. Same stationary AppData save, 2x scale, 5800X /
RTX4080 / 120 Hz, last900 frame samples and seconds34-46 process samples.
No GPU replay ran during timing. Broader scenes and lower hardware remain open.

Validation: Release builds; 51 renderer/pack/release/render-test contract tests;
check-fh1-scene-load.py (actual shared header, physical boundaries and UAV/SRV
fallback); check-fh1-depth-geometry.py with --fixtures depth-index-snapshot
and --scene-fixtures scene-geometry-ranges (819 captured draws plus synthetic
extent failures); check-fh1-geometry-cache.py (new extent key plus existing
terrain/mesh invalidation, proof reuse, budget/fence behavior);
check-fh1-depth-indices.py (new exact pairs, wrong pixel partners, memexport/
path/root rejection and prior index cases); check-fh1-mesh-ownership.py
(actual draw block, all six mesh/scene stride cases, full read extent,
failed/moved/enlarged post-import proof and safe smaller-range acceptance).
Use --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe for C++ harnesses.
Built, staged and saved candidate hashes match; no gameplay/replay is running.

Backups: before-scene-root-pipeline_cache.cpp; before-scene-owned-blended.hlsl
and -lit.hlsl; before-scene-owned-command_processor.cpp/.h and -fh1_geometry.h;
before-scene-owned-check-fh1-depth-geometry.py, -check-fh1-geometry-cache.py,
-check-fh1-depth-indices.py. scene-owned-production.cpp is uninstrumented;
scene-owned-mirror.cpp is capture-only. Preserve existing unrelated work.

Next candidates include replacing these two pixel shaders' unbounded texture/
sampler descriptor indexing with fixed native slots: both sample unsigned/
signed views at descriptor indices z/w with sampler y, potentially reusing
the layered two-view/one-sampler root. Trace actual texture-binding order and
constant handling before doing so. Remaining shader families, texture/resource
ownership, native command production, unsupported-index fallbacks, broader
qualification and final backend removal remain incomplete. The 512 MiB shared
buffer still exists for other consumers; these changes do not retire Xenos
by themselves. Artifact paths above are under .local/native-renderer/ unless
qualified as source/tools paths.

### Full terrain geometry ownership retained with reused index maxima - 2026-09-07

Current built/staged DLL SHA256
`D6473754AE86C295FC22A31B1A472F6485D82DDD94EF46F842F30F84A87C3D8E`,
saved as `.local/native-renderer/terrain-maximum-candidate.dll`.
Rollback baseline is `terrain-root-candidate.dll` (AC563E61...), which has
three terrain root SRVs but shared inputs. Full Xenos retirement is incomplete.

Qualified native terrain depth now owns its GuestDMA indices and primary
fetch95, optional direction fetch90 and control fetch89. Admission extends the
existing three terrain hashes only for null pixel shader, no memexport and
host render targets; a terrain index import also requires its qualified root.
Converted/builtin indices, unsupported constants, missing CPU snapshots,
failed imports and failed bounds proofs retain the shared path. Terrain is
all-or-nothing: failure returns its index binding and every stream to shared.
Mesh-depth admission remains otherwise unchanged.

The draw packs float constants using the same ascending float_bitmap walk as
UpdateBindings, accepting 10 or 11 static constants only and checking bitmap
count. It supplies the actual immutable index snapshot, system words and all
three fetch pairs to terrain_geometry_ranges. After vertex imports, it
revalidates indices if any import occurred; missing, moved or enlarged ranges
reject ownership. This handles index/vertex cache-window aliasing.

Terrain proofs live beside existing mesh proofs in each geometry cache entry,
with at most 32 entries and FIFO replacement. The 33-word key includes index
address/size/width/reset, all eight system words, six fetch words and fifteen
relevant float components. Matrices and unused floats are excluded; c8.x is
normalized to its optional-direction branch. Imports clear both caches.
Each proof also saves its optional decoded index maximum. A different terrain
tile with identical first 12 key words reuses that maximum, while recomputing
its changed resource bounds. Invalid/all-reset maxima are cached safely too.
This avoids rescanning the same index bytes for different terrain parameters.

UpdateBindings tracks both secondary addresses, invalidates fetch constants
when their ownership changes, and rebases only active owned fetch90/89 to
low address bits; existing fetch95 rebasing remains. Root SRVs use the owned
addresses or shared fallback. Vertex residency skips all terrain streams only
on complete ownership (inactive direction is not read). The existing fully
owned indexed-draw predicate then omits shared UseForReading. CPU imports now
invalidate residency bits AND address/size tags for fetch89/90/95, preventing
later shared draws from reusing stale state. No shader or root-layout changes
were made in this ownership phase.

Cache sizing was measured, not assumed. The first 16 MiB / 256-entry candidate
F58AD07CED1D214ABFD7FE582E714392EE24B9D5E6AB6FFAB71438B2174CE3E0
passed fresh-input parity (189/189 draws, 127,906 index bytes and 16,594,696
vertex bytes), but terrain-owned-abba-summary.json reports median +7.96%,
p95 +247.37%, CPU -9.24%. Candidate p95 was 71.274/74.356 ms versus baseline
21.361/20.563 ms. Imports reached roughly 20,000 at the 16 MiB cap versus
174 baseline. This variant is rejected; do not restore it for performance.

Increasing the bound to 32 MiB / 512 entries reduced observed allocations to
roughly 21-25 MiB and imports to hundreds or low thousands. That intermediate
D37490F81C33AB86970AC4C0DA21551FE370B503E85F7EBC9E8AF51F546DDB83
still regressed: terrain-owned-32m-baab-summary.json median +2.45%, p95 +6.08%,
CPU +3.60%. A normal diagnostic run PID42356 logged terrain proof hits:
55,095/65,535 initially and 263,741/327,679 later (about 80% overall).
The retained maximum-reuse change addresses index rescans on those misses.
Diagnostic source/counters are removed from production.

Retained performance: terrain-maximum-abba-summary.json, versus AC563E61...
root-only baseline: median -2.91%, p95 -6.95%, CPU +1.30%, private +0.34%,
working set +0.54%. All four runs exit normally, capture twice and complete
frame 2800: A1 PID45484 (16.9935/21.402 ms median/p95), B1 PID31856
(16.371/19.601), B2 PID33856 (16.8585/20.956), A2 PID42032
(17.2325/22.186). This is one four-run sample on the same stationary AppData
save, 2x scale, 5800X / RTX 4080 / 120 Hz, last 900 frame samples and
seconds 34-46 process samples. It is not broader-scene or minimum-hardware
qualification. The cache now permits 32 MiB GPU allocation plus up to 32 MiB
CPU index snapshots and bounded proof metadata; actual allocation is on demand.
The shared 512 MiB allocation still exists until remaining consumers retire.

Fresh final qualification: PID10876, terrain-maximum-mirror-rdc/frame_frame3137.rdc;
terrain-maximum-mirror-audit/report.json verifies 215/215 terrain draws fully
owned, 129,104 exact index bytes and 18,382,252 exact vertex bytes against
freshly requested shared sources at each draw. All draw PSOs are tracked via
structured command-list state, all draws mapped, and unsupported command-state
operations rejected. No partial ownership occurs. The audit reconstructs
physical addresses from owned resource names, descriptor offsets and rebased
fetches, uses actual bound indices/endian/reset/clamp, and checks every active
stream's exact bytes. Captured c9=(100,10,0,9) is explicitly asserted by this
audit; general grid bounds are separately tested. Prior terrain-root replay
already proves these unchanged shader variants' vertex and depth parity.
terrain-maximum-preview.png (candidate B2) was viewed: scene intact.

Validation passes: Release build; check-fh1-terrain-ownership.py (actual draw
block, sparse constant packing, count mismatch, every failed import and moved/
grown reproof range); check-fh1-geometry-cache.py (actual cache methods, all
key fields, maximum reuse, alias invalidation, GPU snapshot rejection, FIFO,
32 MiB/512-entry fence policy, all stream residency/rebasing/binding changes);
check-fh1-depth-indices.py (all seven hash admission cases, pixel/export/path
rejection, terrain root fallback, existing index residency branches);
check-fh1-terrain-geometry.py (331 captured draws, 32,000 interval samples);
and 51 renderer/pack/release/render-test contract tests. Run C++ harnesses
with --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe. After capture,
restoring uninstrumented source and rebuilding reproduced the retained DLL
hash exactly; built/staged/candidate match. No gameplay or replay is running.

Resume artifacts: before-terrain-owned-command_processor.cpp/.h and
before-terrain-owned-check-fh1-geometry-cache.py / check-fh1-depth-indices.py
preserve the AC563E61 phase. terrain-owned-16m.cpp and
terrain-owned-16m-cache-check.py preserve the first rejected ownership variant.
terrain-owned-32m-production.cpp and before-terrain-maximum.h / -check.py
preserve the second variant. terrain-maximum-production.cpp is current;
terrain-maximum-mirror.cpp is capture-only. Do not restore diagnostic source.

Next remove shared dependencies from remaining native scene families and
resource paths, including textured geometry, then native command production.
GPU-written/converted-index fallback, broader gameplay, lower-hardware tests
and final backend removal remain open. Do not claim Xenos is retired because
these terrain draws no longer consume its shared geometry buffer.
All artifact paths above are under .local/native-renderer/ unless qualified.

### Terrain direct resource bindings retained - 2026-09-07

Current built/staged DLL SHA256
`AC563E6134CBEB69151FCE7F78BA220B3B6980D7EE5BB3EA652908B585A2089F`,
saved as `.local/native-renderer/terrain-root-candidate.dll`.
Rollback baseline: `terrain-bounds-candidate.dll`, SHA256 `528ADAAA...`.
Full Xenos retirement remains incomplete. Terrain now has three explicit
root SRVs, but all three still bind shared physical memory and its indices
remain shared. Owned terrain buffers and their cached bounds are next.

`fh1_terrain_depth.vs.hlsl` adds FH1_TERRAIN_OWNED_GEOMETRY variants for both
transforms: primary t0, direction t1, control t2; no UAV. Raw Load2/Load4 keep
a vector fast path and explicit component zero fallback at the 512 MiB
boundary; LoadWord is guarded too. Overflowing intra-vector addresses do not
wrap. Existing shared/UAV variants compile byte-for-byte identically to the
before-change source. New owned headers are compiled with FXC /O3 /T vs_5_1;
standard additionally defines FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM.
`terrain-owned-shaders/compile-report.json` records all six compilation hashes
and both shared-unchanged results. Assembly confirms three SRVs, no UAV and
actual conditional loads; CPU checks exercise distinct buffer tags, every
endian mode, shared/UAV branches, vector boundaries and UINT_MAX.

The terrain root copies the depth layout, using the otherwise unused vertex
and pixel descriptor-index slots for t1/t2. UpdateBindings binds those slots
as SRVs for terrain, retains ordinary constant slots, and uses the existing
root-change invalidation. All residency and shared transitions remain active.
Pipeline admission uses the existing exact native-scene PSO allowlist and
null pixel shader; missing terrain root or PSO failure falls back to translated
stages with their original root. Root lifecycle cleanup is included.

Release build and 51 contract tests pass. New runnable check:
`python tools/check-fh1-terrain-load.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`.
Existing terrain arithmetic check passes too. AppData capture run PID47412
exits normally; `terrain-root-preview.png` was viewed and scene is intact.
`terrain-root-rdc/frame_frame3133.rdc` and `terrain-root-parity/report.json`
prove all 204 captured terrain draws use the expected compiled variants,
with three zero-offset bindings to the same 512 MiB buffer. Replacing them
with the previous shared terrain shaders gives exact parity for 657,840
post-VS bytes and both depth targets (42,065,920 + 83,886,080 bytes).
All draws are selected through structured command-list PSO tracking, with
complete draw mapping and rejection of unsupported command-state operations.

`terrain-root-abba-summary.json`: median -0.04%, p95 -1.55%, CPU -3.73%,
private -0.08%, working set +0.14%. Effectively flat median in one four-run
sample, not a general speedup claim. All runs exit normally and complete
frame 2800 with two captures: A1 PID32592, B1 PID14920, B2 PID23788,
A2 PID50356. Same stationary AppData save, 2x scale, 5800X / RTX 4080 /
120 Hz; last 900 frame samples, seconds 34-46 process samples. No replay ran
during timing. The ABBA script restores the candidate after the final run.

Next wire all-or-nothing terrain ownership into these three bindings using
the retained terrain_geometry_ranges helper. Use exact GPU index snapshots,
cache proofs without camera/unused constants, and revalidate after aliased
vertex imports. Pack constants in ascending bits of constant_register_map's
float_bitmap, exactly as UpdateBindings does; standard transform only uses
c[0..9], offset also uses c[10]. Bounds consume neither matrices nor c[10].
Rebase fetch95/90/89 only for fully qualified ownership, and suppress shared
residency/transitions only when every active stream plus indices is owned.
Do not re-enable the rejected indices-only optimization as a final state.

Backups: `before-terrain-owned-shader.hlsl` and `before-terrain-root-` plus
`command_processor.cpp`, `command_processor.h`, `pipeline_cache.cpp`.
These preserve the preceding phase, not the original clean repository.
All artifact paths above are under `.local/native-renderer/` unless qualified.

### Terrain bounds validated; indices-only ownership rejected - 2026-09-07

Current built/staged DLL SHA256
`528ADAAAA773AE220537C9CCEE6AB68D4FDE6EC00E45C3E5E7840490902E787B`,
saved as `.local/native-renderer/terrain-bounds-candidate.dll`.
Full Xenos retirement remains incomplete. Terrain still uses shared indices
and all three shared vertex streams; the earlier owned mesh-depth path remains.

Retained `fh1_geometry.h` extracts the existing endian/reset/closing-index/
offset/clamp decoder into `geometry_index_maximum`, preserving mesh-depth
behavior. New `terrain_geometry_ranges` proves primary fetch95 (28-byte
stride, first 8 bytes), optional direction fetch90 (4-byte stride), and
control fetch89 (32-byte cells). It accepts packed native c[11] constants,
proves finite pre-clamp arithmetic, rounds positive interval bounds outward,
and rejects unsupported negative/reversed grid intervals, non-finite values,
signed index conversion overflow, and declared/physical buffer overruns.
Inactive c[8].x == 0 direction records are ignored. No captured grid constants
are hard-coded. This helper is not yet wired to terrain GPU ownership.

`tools/check-fh1-terrain-geometry.py` passes all 331 captured terrain draws,
32,000 independent sampled float intervals, and synthetic boundary/fallback
cases. The capture exporter now saves actual primitive-reset state. Existing
mesh-depth geometry checks pass all 320 saved fixtures; geometry cache checks,
Release build and 51 renderer/release/pack/render-test contract tests pass.
Current retained AppData gameplay smoke PID31672 exits normally with two
captures. `terrain-bounds-retained-preview.png` was viewed: scene intact.
Built and staged hashes match; no gameplay process remains running.

Rejected candidate SHA256
`3C652AC6870090022AB961FE37D849E73D5116E6258EEE3DBF07FCC56903C7E9`
extended existing owned-index admission to the three terrain depth families,
with no pixel shader/memexport and host render targets. A diagnostic fresh
shared-source mirror proves 277/277 terrain draws own exact indices:
136,466 bytes match in `terrain-indices-mirror-audit/report.json`, from
`terrain-indices-mirror-rdc/frame_frame3093.rdc` (PID41204). Expanded actual
admission/fallback checks also passed. Diagnostic code was removed before
benchmarking; rebuilding reproduced the uninstrumented candidate hash.

Performance nevertheless regressed in both orderings against B2A7EB6B...:
`terrain-indices-abba-summary.json`: median +1.95%, p95 +4.22%, CPU -4.16%.
`terrain-indices-baab-summary.json`: median +0.09%, p95 +3.34%, CPU +10.13%.
All eight runs exit normally, capture twice and complete frame 2800. Same
stationary AppData save, 2x scale, 5800X / RTX 4080 / 120 Hz, last 900 frame
samples and seconds 34-46 process samples. The consistent tail regression
rejects this change; correctness alone is insufficient. Cache diagnostics
reach the existing 16 MiB limit, then imports settle (248 -> 258 -> 258),
so sustained churn is not established and no budget increase was made.

Command processor and its index-admission test were restored from
`before-terrain-indices.cpp` and `before-terrain-indices-check.py`.
Rejected source/test and DLL remain as `terrain-indices-rejected.cpp`,
`terrain-indices-rejected-check.py`, and `terrain-indices-candidate.dll`.
`before-terrain-bounds.h` preserves the prior helper header. Do not restore
older phase backups over the current retained work.

Next: full terrain resource bindings, using this bounds proof with the
exact immutable GPU index snapshot and the same packed constants used by
UpdateBindings (not guest registers 0..10). Cache only relevant proof inputs:
c4.xyz, c5.xyz, c7.xyzw, c8.x branch, c9.xyzw, fetch pairs and index/system
state; unused constants can contain arbitrary values and camera matrices
would needlessly invalidate proofs. All three streams must be owned before
omitting shared residency/transitions; optional direction is branch-sensitive.
Revalidate indices after vertex imports because cache windows can alias.
Root-descriptor shader variants also need explicit physical per-component
bounds. Keep the existing cache budget until measurements justify a change.
Native command production, remaining families/resources, wider gameplay and
lower-hardware qualification, and final Xenos backend removal remain open.

All artifact paths above are under `.local/native-renderer/` unless qualified.

### Fully owned depth draws omit shared transition; terrain inputs mapped - 2026-09-07

Current built/staged DLL SHA256
`B2A7EB6B281419663E6D8D25A9A76B65276BB91D808D2E3DE242645A856743E7`,
saved as `.local/native-renderer/depth-shared-transition-candidate.dll`.
Rollback: `depth-proof-cache-candidate.dll`, SHA256 `E9DC7C74...`.
Full Xenos retirement remains incomplete.

The indexed draw branch now skips shared `UseForReading` only when both
`geometry_address` and `depth_index_address` are nonzero. In the current
admission path that means a qualified native mesh-depth draw owns both
inputs; it has no pixel shader or remaining shared-buffer reads. Memexport
still uses `UseForWriting`; either missing owned input retains the read
transition. `SubmitBarriers` is unconditional. Geometry proofs, shaders,
pipeline admission and resource imports are unchanged. The existing cache
check executes all eight ownership/export combinations using the actual
production branch. Release build and 51 contract tests pass.

Timing required two orderings because the first was slightly positive.
`depth-shared-transition-abba-summary.json`: median +1.27%, p95 +2.43%,
CPU -0.70%. Reverse `depth-shared-transition-baab-summary.json`: median
-0.77%, p95 -3.14%, CPU -1.34%. The eight-run means in
`depth-shared-transition-combined.json` give median +0.24%, p95 -0.41%,
CPU -1.02%, private +0.15%, working set +0.31%. Effectively flat in this
sample, not a speedup claim. All eight runs exit normally, capture twice and
complete frame 2800; stationary AppData save, 2x scale, 5800X / RTX 4080 /
120 Hz, last 900 frame samples and seconds 34-46 process samples. Candidate
`depth-shared-transition-preview.png` was viewed and the scene is intact.
Build/staged hashes match. This removes an unused transition, not the
512 MiB shared allocation. Backups: `before-depth-shared-transition.cpp`
and `before-depth-shared-transition-check.py`.

Read-only next-family inspection: `inspect-terrain-depth-ranges.py`,
`terrain-depth-ranges/report.json` and `summary.json`, using saved
`depth-proof-cache-mirror-rdc/frame_frame3124.rdc`. All 331 selected draws
use the native terrain float layout: 175 VS5A28C7FAFD86F112, 82
VSCA293E0A1CB4B416, 74 VS4E1DA281CC3D7EDB; all use 16-bit indices.
The report preserves actual system words, three fetch records, float bits,
and per-draw raw index files. No ownership code was changed for terrain.

Terrain reads fetch95 (28-byte stride, first 8 bytes), fetch90 (4-byte
direction stream, only when c[8].x != 0), and fetch89 (two 16-byte control
loads at a 32-byte grid stride). Main ranges fit all 331 captured draws.
Direction is active in 290 draws and fits all 290; some inactive records
do not fit, so checking the optional branch matters. c[9] is exactly
(100,10,0,9) in every captured draw; control fetches declare 32,000 bytes.
For finite grid values, the clamped coordinates give indices 0..999 and
exactly 1,000 control cells. This is evidence for a bounds proof, not a
license to freeze constants or assume all future scenes use these values.

Next implement terrain's three resource bounds and bindings, preserving
fallback for unsupported parameters. The control index depends on fetched
vertex data and floating-point arithmetic; establish finite/range behavior
before rebasing its buffer. The mesh-depth single-buffer proof alone is
insufficient. Additional root bindings and the fully-owned transition
predicate must account for all three streams; partial ownership must not
accidentally suppress a shared read. Broader scene and lower-hardware
qualification, native command production and backend removal remain open.

All artifact paths in this section are under `.local/native-renderer/`.
No gameplay or replay process remains running.


### Depth vertices retained with cached bounds proofs - 2026-09-07

Current built, saved and staged DLL SHA256
`E9DC7C7422222C43B92AB6FFF1D4E67231DAAF7D89D120B50A74699FDAD126FC`,
`.local/native-renderer/depth-proof-cache-candidate.dll`.
Rollback is `layered-bounds-candidate.dll`, SHA256 `9AC786B3...`.
The four admitted mesh-depth families now own both index and vertex inputs
when bounds and CPU-source checks pass. Full Xenos retirement is incomplete.

Reactivated the qualified bounded depth root/shader and immutable index
snapshot implementation, adding at most 32 exact bounds proofs per existing
geometry-cache entry. `GetFh1DepthGeometryRange` keys all eight system words,
index address and byte size, index width, vertex stride, fetch address and
size, and primitive reset. Hits return the previously proved range, including
negative results. A bounded linear search and circular replacement avoid a
new global cache or dependency. Every import clears proofs before refreshing
the CPU snapshot, including aliased vertex imports and GPU-only imports.
Guest invalidation alone leaves the old GPU contents and their proof intact;
the next import replaces both. The existing post-vertex-import revalidation
remains mandatory. GPU-only snapshots cannot yield a CPU bounds proof.

The 16 MiB GPU cache budget and 256-entry limit remain. Retained CPU index
snapshots can add up to another 16 MiB; proof records add bounded metadata.
Do not claim a reduction in RAM requirements from this change. The previous
layered raw-load bound, nonindexed shared-transition omission and CPU-import
residency correction remain. The indexed branch still calls shared
`UseForReading` even for fully owned depth draws; that is a remaining small
dependency to audit, not an actual shader read from shared memory.

Gameplay ABBA: `depth-proof-cache-abba-summary.json`, versus 9AC786B3.
Median frame -0.47%, p95 -0.99%, CPU -0.05%, private commit +0.05%, working
set +0.05%. A1/B1/B2/A2 medians 16.5785 / 16.670 / 16.621 / 16.870 ms;
p95 20.246 / 20.623 / 20.591 / 21.379 ms. Four normal exits, two captures
each, frame 2800. Same stationary AppData save, 2x scale, 5800X / RTX 4080 /
120 Hz; last 900 nonzero frame samples and seconds 34-46 process samples.
Treat as effectively flat, not a general speedup or lower minimum hardware.
It avoids the prior uncached ownership experiment's measured regression.

Fresh input qualification: PID17448,
`depth-proof-cache-mirror-rdc/frame_frame3124.rdc` and
`depth-proof-cache-mirror-audit/report.json`. All 231 selected depth draws
own vertices and indices; all bounds fit. All 6,107,052 vertex bytes and
353,774 index bytes exactly match freshly resident shared-memory references
at those same draws. `depth-proof-cache-input-summary.json` asserts every
ownership/equality/bounds field, not just the capture's completion status.
The diagnostic build requested reference residency after preparing ownership;
that code is removed from production. This capture tests the new proof reuse.
The four generated depth headers are unchanged from the previously qualified
bounded-bytecode replay (320 draws, 2,145,456 post-VS bytes and both depth
targets exact); no new shader translation or allowlist expansion was used.

`depth-proof-cache-hit-log.txt`: 196,608 hits out of 196,951 requests, over
99.8%. After the first 343 misses, the following two groups of 65,536 hits
had no additional misses. These counters were diagnostic only and have been
removed. `depth-proof-cache-preview.png` from the ordinary candidate run was
viewed; the scene is intact.

Validation: release build passes and restored production rebuild reproduces
E9DC7C74 exactly. Geometry-cache checks exercise every proof-key field,
repeated hits, guest writes before import, aliased imports, GPU imports,
32-record capacity/replacement, fences, failures and eviction. Depth-vertex
ownership/fallback checks, all 320 saved depth-index bounds fixtures,
depth-index residency fallback checks, raw-load boundary/endian checks, and
51 shader-pack/native-renderer/release/render-test contract tests pass.

Artifacts above are under `.local/native-renderer/`. Relevant production
files are the SDK command processor header/source, pipeline cache, depth
HLSL/four generated headers, and runnable checks in `tools/`. Preparation
script `prepare-depth-proof-cache.py` and `before-depth-proof-cache/` preserve
the exact prior state. `depth-proof-cache-production.cpp` is the retained
uninstrumented source; `depth-proof-cache-mirror-command_processor.cpp` is
diagnostic only. Do not rerun older restoration scripts over this new state.
No game or replay remains running.

Next: remove the unused shared transition from fully owned indexed depth
draws, then expand native geometry/command production to remaining families
and GPU-written/converted index paths. Keep the original full retirement and
lower-requirements goal; four owned families do not satisfy it by themselves.


### Depth ownership cost isolated before another implementation - 2026-09-07

Production source restored byte-for-byte after diagnostics; rebuild and
staging reproduce `9AC786B36C9F86422EA049805AE349C5547128AE46519A02010D4631D12120D0`.
No diagnostic root, CPU snapshot or timing code remains active. The full
retirement goal is still incomplete.

First isolated the four native depth root/shader variants while keeping
vertices shared and disabling CPU index snapshots and bounds scanning.
Other retained layered fixes were preserved. Diagnostic DLL
`depth-root-only-candidate.dll` SHA256
`E61A9E05AB4DD2F659F10CBFD8D203DBBF43A922153CBC42FF84DB000F399B4A`.
`depth-root-only-abba-summary.json` versus production 9AC786B3: median
-0.62%, p95 -0.42%, CPU +2.27%, private -0.26%, working set -0.24%.
A1/B1/B2/A2 medians 16.855 / 16.996 / 16.5915 / 16.943 ms;
p95 21.047 / 21.408 / 21.148 / 21.688 ms. Four normal exits, two captures
each, frame 2800. This root/shader-only sample does not reproduce the prior
ownership slowdown; do not conclude root switches have zero cost everywhere.

Then instrumented the full rejected ownership path, preserving current
layered changes. `depth-ownership-profile-run`, PID37632, exited normally.
`depth-ownership-profile-log.txt` and `depth-ownership-profile-summary.json`
contain six groups of 65,536 depth draws. Total imports stay at 166.
Excluding the first group, median mean scan cost is 1,213 ns per call;
vertex-cache request is 309 ns per draw. Scan includes snapshot lookup and
`depth_geometry_range`; cache request includes lookup/watch handling and any
import. Timers have overhead, and these are per-group means, not per-draw
latency percentiles. The instrumented build is not a performance candidate.
The scan is about four times the measured cache-request cost in this run.

Next implementation should reuse bounds proofs for unchanged cached index
snapshots. Keep results with the existing bounded geometry-cache entry,
clear them on every import (including aliased vertex imports and GPU-only
refreshes), and key the complete proof inputs: index offset/byte count,
width, stride, system index/endian/clamp values, fetch address/size and reset.
Revalidate after a vertex import exactly as the rejected code already does.
Never cache a proof against mutable guest bytes or a different GPU snapshot.
Measure the result before retaining ownership.

An alternative inspected but not implemented is using the existing bindless
SRV heap to avoid a distinct depth root. It is lower priority now that the
root-only sample is flat. Persistent view allocation accepts individual SRVs;
`RequestOneUseSingleViewDescriptors` returns non-contiguous descriptors, so
do not assume it supplies a contiguous SRV/UAV table. A bindless geometry
descriptor would require its own fully verified fetch-rebasing and lifetime
contract; do not treat this note as implemented behavior.

All artifact paths above are under `.local/native-renderer/`. Reproducers:
`prepare-depth-root-only.py`, `prepare-depth-ownership-profile.py`,
`restore-after-depth-root-profile.py`, their saved command-processor sources,
ABBA scripts and build logs. `before-depth-root-only/manifest.json` verifies
the restored files. Diagnostic owned-depth headers were removed. Existing
layered bounds/transition and CPU-import coherence fixes remain intact.


### Layered direct-root fallback bounds restored - 2026-09-07

Current built, saved and staged DLL SHA256
`9AC786B36C9F86422EA049805AE349C5547128AE46519A02010D4631D12120D0`,
`.local/native-renderer/layered-bounds-candidate.dll`. Previous rollback is
`layered-shared-transition-candidate.dll`, SHA256 `F99DD628...`.
Full Xenos retirement and lower-hardware qualification remain incomplete.

`fh1_layered_scene.vs.hlsl::LoadWord` now returns zero for addresses at or
beyond 512 MiB and issues the raw load only below that limit. All generated
addresses are dword-aligned. The original translator forms fetch addresses
without physical wrapping (`dxbc_translator_fetch.cpp`, vertex-fetch path).
Its sized raw SRV provides zero reads outside the buffer, whereas the native
direct root SRV has no size. See Microsoft's
[root descriptor bounds contract](https://learn.microsoft.com/en-us/windows/win32/direct3d12/root-signatures-overview)
and [raw-load zero behavior](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/ld-raw--sm5---asm-).
Owned smaller buffers still rely on the existing CPU bounds proof before
rebasing; this physical guard does not replace it. Regenerated
`fh1_layered_scene_vs.h` with FXC vs_5_1, main, /O3. The generated assembly
contains conditional branches around its raw loads, not unconditional loads
followed by a zero select. No pipeline allowlist or binding change.

`tools/check-fh1-layered-load.py` executes the actual shader endian/load
functions at zero, the final physical dwords, the first invalid dwords and
0xFFFFFFFC in all four endian modes. Its fake raw buffer rejects any invalid
load; the independent byte-swap reference verifies valid results. Passed.
Release `rexgpu-fh1` build and 51 shader-pack/native-renderer/release/render-test
contract tests also pass.

Exact generated-bytecode replay: `.local/native-renderer/layered-bounds-replay.py`
and `layered-bounds-replay/report.json`, using
`fixed-layered-rdc/frame_frame3116.rdc`. Structured command-list pipeline
tracking selects all 356 layered draws; every draw's full post-VS output
matches (9,547,200 bytes total). Both final color/depth resources match across
their samples, 83,886,080 bytes each. No replay error. Boundary behavior is
covered separately by the runnable raw-load check, not by these normal draws.

Gameplay ABBA versus F99DD628: `layered-bounds-abba-summary.json` and its
scripts/run directories under `.local/native-renderer/`. All four runs exit
normally, take two captures and complete frame 2800. Median frame -1.04%,
p95 -3.37%, CPU +7.02%, private commit +0.25%, working set +1.13%. Candidate
B2 CPU was 3.641 seconds per wall second versus about 3.18 in the other
three runs; do not claim CPU improvement. A1/B1/B2/A2 median frame times:
16.716 / 16.881 / 16.528 / 17.045 ms; p95 21.307 / 20.866 / 20.175 /
21.166 ms. Same stationary AppData save, 2x, 5800X / RTX 4080 / 120 Hz,
last 900 nonzero frame samples and seconds 34-46 process samples. Retained
for correctness with no observed frame-time regression, not a new speedup.

Backups: `before-layered-bounds.vs.hlsl`, `before-layered-bounds_vs.h`.
Build log: `layered-bounds-build.log`. Build/saved/staged hashes match and
no game or replay remains running. Next work should move back to remaining
native draw/resource production and the measured depth-vertex bottleneck;
the layered fallback bounds audit is now handled.


### Owned layered draws omit the unused shared transition - 2026-09-07

Retained built/staged DLL SHA256
`F99DD6284B52123D765D308084FC523A1C7D969A30602FA208B8545D6E53B8ED`,
saved as `.local/native-renderer/layered-shared-transition-candidate.dll`.
Rollback: `depth-import-coherence-candidate.dll`, SHA256 `A0480224...`.
Full retirement remains incomplete.

The nonindexed draw branch calls `UseForReading` only without owned geometry.
In the current implementation, nonzero `geometry_address` is produced only
for the qualified layered root and nonindexed draw, after successful bounds
proof and import. That native VS reads the owned buffer; its native PS reads
textures and constants, not shared memory. Memexport still calls
`UseForWriting`, failed ownership still calls `UseForReading`, indexed draws
are unchanged, and `SubmitBarriers` remains unconditional. Texture uploads
request their own shared read state. A subsequent shared-memory consumer
still transitions the tracked state itself. No shader bytecode changed.

This removes one unused dependency, not the 512 MiB buffer allocation.
The production branch is executed by `tools/check-fh1-geometry-cache.py`
for owned/shared and exporting/nonexporting cases; all checks pass. Release
build and 51 shader-pack/native-renderer/release/render-test contract tests
pass. All four AppData ABBA runs exit normally, capture twice and finish at
frame 2800. Candidate screenshot `layered-shared-transition-preview.png`
was viewed and the scene is intact; this is visual smoke validation, not a
new byte-for-byte GPU parity claim.

Artifacts under `.local/native-renderer/`:
`layered-shared-transition-abba-summary.json`, its run directories and
scripts, `layered-shared-transition-build.log`. ABBA versus `A0480224...`:
median frame +0.08%, p95 +1.97%, CPU -0.58%, private commit +0.07%, working
set +0.01%. A1/B1/B2/A2 medians are 16.6375 / 16.6745 / 16.5775 / 16.588 ms;
p95 20.126 / 20.842 / 20.608 / 20.524 ms. Treat as effectively flat in this
sample, not a speedup or lower hardware requirement. Same stationary save,
2x scale, 5800X / RTX 4080 / 120 Hz; last 900 frame samples and seconds
34-46 process samples. Build and staged hashes match; no game remains running.

Next audit: the existing layered direct-root shader's shared fallback needs
the same explicit physical raw-load bounds investigated for the rejected
depth experiment. Then continue native geometry/command production; the
application graphics hooks still only observe prepared guest draws. Do not
mistake those observers or the native shader substitutions for a native
command producer.


### Depth-vertex ownership qualified, then rejected on timing - 2026-09-07

Full Xenos retirement is still **incomplete**. Depth indices remain owned;
depth vertices still use shared memory in the active build. Do not restore
the depth-vertex experiment as a performance improvement: both final ordered
comparisons regressed. The active source restores the previous index-only
renderer and retains a small CPU-import residency correction and fixed-width
loads in the bounds helper. The helper is preparation for ownership, not a
current gameplay speedup.

Current built candidate is `depth-import-coherence-candidate.dll`, SHA256
`A048022418C720B244323E5B93D0A00770F61F4344C51D0CEBDAF1D7A7784A77`.
Previous index-only rollback remains `depth-indices-cache-candidate.dll`,
SHA256 `96B99BA1E03544C1116FF109F5F69ACE62B4A76D733B94BDF9E3E49599FB00EE`.
All local artifacts below are under `.local/native-renderer/`.

The retained correction's independent ABBA is
`depth-import-coherence-abba-summary.json`: median frame time -1.39%,
p95 -6.39%, CPU seconds per wall second -1.79%, private commit -0.22%,
working set -0.73%. A1/B1/B2/A2 medians are
16.7825 / 16.603 / 16.3595 / 16.6455 ms; p95 values are
21.833 / 20.514 / 19.718 / 21.147 ms. All four runs exited normally,
produced two captures and completed frame 2800. Treat these as no observed
regression in this sample, not a robust new speedup or reduced requirement.
The built artifact, saved candidate and staged DLL hashes match.

Retained correction: a successful CPU import into `GetFh1OwnedGeometry`
invalidates fetch 95's vertex-residency bit and resets its address/size tag.
Those uploaded bytes may be newer than shared memory; a later shared draw
must request residency rather than accepting an old tag. Cache hits and
GPU-source imports retain the existing fast path. This also covers the
existing layered geometry and owned depth indices. It is not a complete
audit of arbitrary shared-only vertex cache coherence.

The attempted depth-vertex implementation reused the 16 MiB geometry cache,
added a direct vertex SRV root for the four qualified mesh-depth families,
and retained CPU snapshots of index windows from the exact bytes uploaded
to the GPU. GPU imports cleared the snapshots. A vertex import could alias
and replace its index window, so bounds were proved again after an actual
import; cache hits needed only one proof. Snapshot memory could add up to
another 16 MiB; it was not free memory savings. Invalid bounds, unavailable
CPU snapshots and ownership failures used shared geometry. No PSO allowlist
was broadened. This code and its headers are **not active**.

Qualification evidence for the rejected implementation:

- `depth-owned-bounded-bytecode-parity/report.json`: the exact generated
  shader headers match all 320 reference draws, 2,145,456 post-VS bytes and
  both depth targets (42,065,920 and 83,886,080 bytes). Earlier HLSL and
  unbounded-header parity reports also passed but are superseded by this one.
- `depth-vertices-cache-mirror-rdc/frame_frame3041.rdc`, PID 44276, and
  `depth-vertices-cache-mirror-audit/report.json`: all 231 selected draws own
  vertices and indices, with 6,107,052 vertex bytes and 353,774 index bytes
  exactly matching fresh shared-memory sources at the same draws. Every
  bound fits. The diagnostic build explicitly requested shared residency
  after preparing ownership; that reference-only code was removed afterward.
- Earlier normal capture `depth-vertices-rdc/frame_frame3066.rdc` demonstrates
  ownership but does not establish full source parity: its unused shared
  source could be stale. Do not cite its partial comparisons as all-pass.
- Production-block alias/fallback checks and raw-load boundary/endian checks
  passed before archiving; bounds checks still pass all 320 saved index
  fixtures. The final fixed-load candidate screenshot is
  `depth-vertices-fixed-preview.png`; it was viewed and the scene was intact.

The direct root needed explicit physical-address bounds for shared fallback.
[D3D12 root descriptors lack size-based bounds checking](https://learn.microsoft.com/en-us/windows/win32/direct3d12/root-signatures-overview),
while [ld_raw returns zero for each out-of-bounds 32-bit component](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/ld-raw--sm5---asm-).
The experimental shader handles the final two physical dwords separately
and returns zero beyond 512 MiB. Its generated bounded headers passed the
replay above. Audit the older layered root fallback separately before
extending this technique to additional families.

Timing decisions, all versus index-only `96B99BA1...`:

| Candidate / report prefix | Median frame delta | p95 delta | Decision |
| --- | ---: | ---: | --- |
| `3489D71F...`, `depth-vertices-abba` | +6.29% | +7.66% | reject per-draw guest snapshot |
| `B9163283...`, `depth-vertices-cache-abba` | +0.44% | -1.62% | superseded; missing residency correction |
| `DD8F1EF8...`, `depth-vertices-final-abba` | +8.12% | +5.66% | reject clearing residency on every ownership switch |
| `C54B2D02...`, `depth-vertices-import-abba` | +10.15% | +5.99% | reject dynamic-size index loads |
| `853FC4F5...`, `depth-vertices-fixed-abba` | +2.34% | +5.70% | reject; CPU -2.69% |
| same `853FC4F5...`, `depth-vertices-fixed-baab` | +8.17% | +8.38% | reverse-order repeat also regresses; CPU +2.36% |

The last candidate's full SHA256 is
`853FC4F5D576748C9FF6A5A2CBACA3EFBA24AB639CB955CF20ABF05C0526AABA`.
Every timing report is `<prefix>-summary.json`; scripts and process samples
are preserved. These are stationary AppData-save runs at 2x scale, 5800X /
RTX 4080 / 120 Hz, four normal exits per comparison, frames through 2800.
Frame statistics use the last 900 nonzero samples; process statistics use
seconds 34-46. Variation is substantial, but neither final ordering supports
shipping depth-vertex ownership as a speedup. No lower hardware minimum is
established. Candidate cache logs show stable imports rather than an import
loop. Files named `depth-vertices-final-*` are an obsolete rejected prototype,
not the retained build.

One real helper bottleneck was dynamic-size `memcpy` for each decoded index.
Replacing it with explicit 16-bit or 32-bit copies preserves endian, reset,
closing-index, offset-wrap and clamp semantics. The saved microbenchmark
`depth-index-scan-benchmark.json` reports median 145.0702 -> 18.2248 ms for
16-bit indices (about 7.96x), 39.3526 -> 19.8217 ms for 32-bit (about 1.99x),
for 2,000 calls over 8,192 indices, with identical checksums. Reproducer:
`run-depth-index-scan-benchmark.py` and its C++ source. This speedup alone
did not overcome the whole renderer experiment's frame-time regression.

Recovery: `depth-vertices-rejected-853f/` contains the complete changed files,
four generated owned headers, experimental checks, SHA256 manifest, and
baseline-to-experiment patches. Restore related files together before running
those experimental checks. `park-depth-vertices.py` documents the selective
rollback; do not rerun it over current work. Original per-turn backups are
`before-depth-vertices-*`. No unrelated repository changes were reverted.

Validation after rollback: release `rexgpu-fh1` build passed; geometry-cache
mutation/fence/failure/eviction checks now also exercise CPU-import residency
invalidation and hit/GPU-import preservation; depth-index ownership/fallback
checks passed; 51 shader-pack/native-renderer/release/render-test contract
tests passed. No shader bytecode changed in the retained build.

Next: find the depth-vertex path's remaining frame cost before reactivating
it. Candidates for measured investigation are root-switch overhead and
repeated bounds proofs. Do not blindly add a second cache. Fully owned draws
still call `SharedMemory::UseForReading`; audit its ordering requirements
before omitting it. Terrain depth, GPU-written/converted index paths, other
shader families, textures/render targets, native command production, and
eventual removal of Xenos parsing/translation remain outstanding.

### Depth indices moved to the existing device-local cache — 2026-09-07

Retained DLL SHA256
`96B99BA1E03544C1116FF109F5F69ACE62B4A76D733B94BDF9E3E49599FB00EE`
(`.local/native-renderer/depth-indices-cache-candidate.dll`), built and staged.
Previous rollback is `lazy-no-output-candidate.dll`, SHA256 `68FB391E...`.
Full retirement remains incomplete; depth vertex data still uses shared memory.

`PrimitiveProcessor::Process` accepts an optional guest-DMA residency deferral,
default false. Vulkan and other paths keep the default; builtin DMA still
requests residency. D3D12 defers only the four mesh-depth families with no
pixel shader/memexport on host render targets. Guest-DMA draws request the
existing `GetFh1OwnedGeometry` buffer, restoring the low four address bits for
an exact IA index address. Failed ownership requests take the original shared
residency path and propagate failures. The existing cache transitions buffers
to combined NON_PIXEL_SHADER_RESOURCE | INDEX_BUFFER read states. Its 16 MiB
budget, watches, CPU/GPU import handling and fence-safe eviction are reused;
no second cache or persistent CPU index mirror was added.

Rejected an earlier upload-heap index version, even though all 320 captured
index streams (424,428 bytes) matched the saved reference in draw order.
Its CPU-staging variant `C9C22DAD...` regressed ABBA median frame time 5.74%
and p95 10.05% versus `68FB391E...`; CPU +0.88%. Reports are
`depth-indices-cpu-audit` and `depth-indices-cpu-abba-summary.json`. Initial
prototype `847D5793...` scanned mapped upload memory; this was corrected before
that ABBA. Neither upload version is retained in production. The first capture
controller attached too late; one retry reused a test-output directory and
hit `request_invalid_or_output_exists`. Fresh-output runs completed normally.

Device-local candidate capture: PID10612,
`depth-indices-cache-rdc/frame_frame3128.rdc`. Audit selected 284 depth draws:
98 stride24, 61 stride20, 59 stride28, 66 stride32; 441,484 index bytes.
All bind owned buffers; 275 streams match the prior snapshot reference. The
remaining nine (8,002 bytes) match their shared-memory source bytes at the
same captured draws. `depth-indices-cache-source-check.json` also confirms
all selected resources have owned-cache names (64 distinct windows).
All 284 index bounds fit. Reports/scripts: `depth-indices-cache-audit` and
`depth-indices-cache-source-check.py/json`. End screenshot
`depth-indices-cache-preview.png` inspected; normal exit, two captures.

Device-local ABBA versus `68FB391E...`:

| Run | Session | Median ms | p95 ms | CPU s/s |
| --- | --- | ---: | ---: | ---: |
| a1 | 20260907T035832Z-p48320 | 16.6430 | 20.423 | 3.0833 |
| b1 | 20260907T035923Z-p50260 | 16.5545 | 20.589 | 3.3693 |
| b2 | 20260907T040014Z-p50040 | 16.6420 | 20.655 | 3.2386 |
| a2 | 20260907T040105Z-p50048 | 16.6730 | 20.744 | 3.4059 |

Median -0.36%, p95 +0.19%, CPU +1.83%, private memory -0.03%, working set +0.18%.
Treat performance as flat/noisy, not a speed or minimum-hardware improvement.
This retains index ownership while avoiding the upload-heap regression.
`depth-indices-cache-abba-summary.json` and matching launch/summarizer scripts
retain the measurements. All runs completed frame2800 with two captures.
`depth-indices-cache-log-check.json`: only the existing ResolvePath device error.

Validation: SDK build `depth-indices-cache-build.log`; runnable
`tools/check-fh1-depth-indices.py` exercises production cache selection, low
address bits, 16/32-bit sizes, zero/oversized requests, residency deferral and
fallback failure. `tools/check-fh1-geometry-cache.py` still passes mutation,
in-flight invalidation, CPU/GPU imports, allocation failure, budget and eviction;
it now checks the combined read state. Both use the local clang++ compiler.
The 320 saved depth-bound fixtures, native depth pipeline check and 51 existing
shader-pack/renderer/release/render-test checks passed during this work.

Next: qualify owned depth vertex buffers using bounds derived from the SAME
immutable index contents bound for that draw. The current cache version does
not retain the earlier per-draw CPU snapshot; do not treat an unrelated read
of mutable guest indices as proof of cached GPU index bounds. A native depth
root/SRV-only shader path and its fallback still need implementation and parity
validation. No goal completion, commits or save-file changes.

### Indexed depth geometry bounds proved; ownership integration pending

Audited all 320 shared depth-mesh draws in baseline capture
`native-indices-rdc/frame_frame3105.rdc`: 122 stride24, 63 stride20, 69 stride28,
66 stride32. All use 16-bit indices with shader endian8-in-16 and baseVertex0.
Initial bounds audit counted primitive-restart FFFF as a vertex and rejected
313 draws; `depth-index-restart-probe` confirms actual stripCutValue65535.
Corrected audit uses IsRestartEnabled/GetRestartIndex, not an assumed sentinel.

`depth-index-snapshot/report.json` and 320 per-event .bin files retain 424,428
bytes of actual host index data. All 320 now fit declared fetch ranges.
Summed required spans 7,594,816 bytes versus summed fetch sizes 10,877,104;
these are per-draw sums, not unique memory savings. Scripts
`depth-index-ranges.py` (initial conservative audit) and `depth-index-snapshot.py`
(corrected export) retained. Initial report is not a failure of native parity.

Added `depth_geometry_range` to existing `fh1_geometry.h`: validates immutable
host-index bytes, 16/32-bit formats, four supported strides, endian conversion,
closing vertex, 24-bit offset wrapping, clamp bounds, restart handling,
physical/fetch limits, and the 12-byte position load. All-reset snapshots return
no range. Requires a zero-base-vertex draw. Returns base plus necessary span.
Crucial contract: bind the SAME immutable snapshot used for bounds, never scan
mutable guest indices and later render a different copy.

`tools/check-fh1-depth-geometry.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe
--fixtures .local/native-renderer/depth-index-snapshot` passes synthetic boundary
cases plus all 320 exported snapshots against independent Python bounds.
SDK build `depth-range-build.log` passes. Header backup
`before-depth-geometry-range.h`. No runtime ownership activation yet.

Next: for qualified native depth draws, copy CPU-owned guest DMA index bytes
into an upload allocation, prove geometry bounds using that immutable copy,
bind that exact index allocation, and reuse GetFh1OwnedGeometry for vertex data.
Use ownership rejection/fallback for GPU-written indices and retain existing
conversion paths until separately covered. Add the native depth root binding
and fetch rebase, then live parity/performance checks. This will remove both
index/vertex shared-GPU-buffer dependencies for admitted draws. Full retirement
remains incomplete; no game/replay running.

### No-output predicate short-circuits unrelated draws

Moved GetNormalizedDepthControl inside the exact shader-pair/no-query/no-export
guard. Unrelated draws no longer pay the extra normalization introduced by
the preceding optimization. Eligibility and writing/query fallbacks are unchanged.
`tools/check-fh1-constant-no-output.py` now executes the entire production block
and counts normalization calls: one for the eligible pair, zero for wrong VS,
wrong/absent PS, active query, or memexport. All prior output guards still pass.
Backup `before-lazy-no-output.cpp`; SDK build succeeds.

Live AppData run 20260907T031941Z-p15312 completed normally at frame2800 with
2 captures (`lazy-no-output`). This is a behavior-preserving short-circuit
change, not a measured new speedup; do not reuse prior benchmark percentages
as measurements of this binary.
Built/staged `lazy-no-output-candidate.dll` SHA256:
68FB391ED62263AD60EC9BAE677C430956EC0DAB3D778E511FBB1AE1873896D3.
Rollback `constant-no-output-candidate.dll` (36984B...). No game/replay remains.

Next resource dependency inspected: native depth shaders still read shared
GPU geometry. GetFh1OwnedGeometry already imports CPU-owned guest ranges with
watch invalidation, upload-pool copies, fence-safe eviction and a 16MiB cap.
Its current admission is layered/root-specific and non-indexed; fetch190 is
rebased to low4 bits by UpdateBindings. `fh1_geometry.h::geometry_range` proves
bounds only for non-indexed 40-byte scaled rows. Do not reuse that proof for
depth indexed draws. PrimitiveProcessor::ProcessingResult exposes index type,
format, endian and handle but no validated min/max index range; inspect actual
indexed inputs and ownership before extending the existing cache. Full Xenos
retirement and broad lower-hardware qualification remain incomplete.

### Constant pair no-output draws bypassed and benchmarked

Query audit `constant-pair-queries/report.json` maps all captured commands:
only 2 EndQuery + 1 ResolveQueryData, all timestamp Type2, no occlusion BeginQuery
around the 24 masked point draws. RenderDoc SamplesPassed enumeration exists
but FetchCounters returned no selected samples; do not claim counter parity.

Added an early return in D3D12CommandProcessor::IssueDraw after shader analysis
and before BeginSubmission/primitive preparation. Exact VS B6C9863F710683EC +
PS A4A965C189287B99 only, no memexport, no active host occlusion query,
normalized depth/stencil disabled and normalized color mask zero. Copies are
handled first. Every writing/query state falls through unchanged. This skips
command preparation and GPU submission for provably output-free draws rather
than relying on a pixel shader replacement whose output cannot be observed.
Source backup `before-constant-no-output.cpp`.

`tools/check-fh1-constant-no-output.py` executes the production predicate and
checks shader identity, absent PS, memexport, active query, depth, stencil and
all color-mask bits, plus ordering after copy handling/before submission.
Passes; SDK builds, layered binding check and 51 Python contract tests pass.

Live capture PID 2760 completed normally, final screenshot inspected.
`constant-no-output-rdc/frame_frame3113.rdc`: 3,990 total draws, zero paired
B6C/A4A draws. `constant-no-output-audit/report.json` verifies complete command
list PSO tracking before counting. Baseline capture had 24 paired draws.
Native PS pair remains unactivated; observable writing states keep fallback.

Candidate `constant-no-output-candidate.dll`:
36984BE95F0D5C91335B3C0EBFD4D48B3F0BE608BBA1D93F7C794C3072201F1B.
Baseline/rollback `constant-native-candidate.dll` (816980...).

A/B/B/A frame times (milliseconds):

| Run | Session | Median | p95 | CPU seconds/wall second |
| --- | --- | ---: | ---: | ---: |
| A1 | 20260907T031355Z-p37416 | 16.7480 | 20.667 | 3.3666 |
| B1 | 20260907T031446Z-p32844 | 16.5480 | 19.653 | 3.1214 |
| B2 | 20260907T031537Z-p47616 | 16.4250 | 20.477 | 3.5789 |
| A2 | 20260907T031628Z-p47472 | 17.7085 | 22.306 | 3.1458 |

Mean median -4.31%, p95 -6.62%, CPU +2.89%, private commit -0.38%,
working set -0.95%. Mixed/noisy result, especially A2 frame and B2 CPU.
Do not claim a broad hardware reduction. Draw removal itself is verified.
All four runs normal, 2 captures at 2800. `constant-no-output-abba-summary.json`.
Logs retain only existing ResolvePath device lookup errors
(`constant-no-output-log-check.txt`). Built/staged hash matches 36984B...;
no game/replay remains running.
The no-output predicate currently computes normalized depth before testing
shader identity; if CPU cost matters, short-circuit that work to the matched
pair. Full Xenos retirement remains incomplete.

### Constant VS/PS pair audit: vertex parity passes, pixel proof insufficient

Added optional FH1_CONSTANT_COLOR_INTERPOLATOR to `fh1_constant_position.vs.hlsl`:
TEXCOORD0=0 and unchanged position. Recompiled null-PS BYTE array is identical
(`constant-position-after-interpolator.h`); active runtime remains unchanged.
Reused existing `fh1_passthrough_color.ps.hlsl` for A4A965C189287B99. Fixed its
AlphaTest compare5 to explicit alpha!=reference, preserving translated NaN
behavior. `tools/check-fh1-passthrough-alpha.py` executes all 8 comparisons
against finite/NaN alpha/reference values: current passes, old backup
`before-passthrough-color.hlsl` compiles and fails. Constant-position compiled
arithmetic check still passes. VS backup `before-constant-interpolator.hlsl`.

`constant-pair-audit/report.json`: 24 point-list draws, one VS Resource817 and
one PS Resource819, post-VS stride32. Actual PS has alpha-test, coverage and
scaling epilogue, no forced early depth flag; do not infer that all three
runtime PSO variants use this same PS modification. Captured shaders and
assembly saved under `constant-pair-audit`. First attempt selected the wrong
pipeline name separator and found no draws; corrected selector matches both
hashes and asserts nonempty.

Replacing both stages with the candidates matches all 24 post-VS streams
(768 bytes) and a 41,943,040-byte color target snapshot. However, deliberately
wrong magenta PS ALSO matches the color snapshot. Therefore
`constant-pair-parity/report.json` is valid vertex/interpolator evidence but
NOT sufficient PS qualification. `constant-pair-poison/report.json` records
the failed sensitivity control. Do not activate the PS pair from this result.

`constant-pair-state/report.json` explains the first selected draw: color
writeMask=0, depth/stencil disabled, 16384x16384 viewport, 32x32 scissor,
point expansion GS with 1x1 point diameter. Constant buffers/GS disassembly
saved in that directory. Query effects may remain despite no attachment
writes. Next: inspect captured query begin/end/resolve around all 24 draws,
compare query results or find observable PS draws; alternatively qualify
native VS separately while retaining translated PS. Full retirement needs
query/command semantics, not just unchanged screenshots.

Production remains 816980192D4B34A51995A2CB6EC6C825F6D04E5D07670920B8A158CF38270D74.
No pair admission/generated header and no game/replay remains running.

### Constant-position null-PS path integrated and benchmarked

Admitted B6C9863F710683EC with absent PS for observed pipeline hashes
FB9F7AF89FA5E129, E09E8BD845D68BDD, 38DC022591899969, 544EA3FFE46CB7B3,
requiring host RTs and bindless resources. Compiled
`fh1_constant_position_vs.h` with FXC vs_5_1 /O3. Reuses native scene binding
and fallback handling; preload skips the VS. The same guest shader remains
needed by PS-present paths, so do not claim its bytecode never loads later.
Census instrumentation removed. Backup `before-constant-integration.cpp`.

Capture PID 45196 exited normally, 2 screenshots, final image inspected.
`constant-native-rdc/frame_frame3085.rdc`: all 96 selected draws, 1,536 post-VS
bytes and 6 full color/depth snapshots totaling 325,058,560 bytes match the
original translated shader exactly. `constant-native-parity/report.json` and
scripts contain reverse-parity evidence. All four PSOs initialized with guest
VS translated false and PS translated false. SDK build, admission/fallback,
compiled constant-position arithmetic, layered bindings and 51 Python tests pass.

Candidate `constant-native-candidate.dll`:
816980192D4B34A51995A2CB6EC6C825F6D04E5D07670920B8A158CF38270D74.
Baseline/rollback `offset-native-candidate.dll` (4DCB59...).

A/B/B/A frame times (milliseconds):

| Run | Session | Median | p95 | CPU seconds/wall second |
| --- | --- | ---: | ---: | ---: |
| A1 | 20260907T025642Z-p45212 | 16.9305 | 21.177 | 3.2457 |
| B1 | 20260907T025733Z-p41788 | 16.5790 | 19.775 | 3.3144 |
| B2 | 20260907T025824Z-p39948 | 16.6560 | 20.909 | 3.5873 |
| A2 | 20260907T025913Z-p38736 | 17.1085 | 21.681 | 3.1703 |

Mean median -2.36%, p95 -5.07%, CPU +7.57%, private commit +0.69%,
working set +0.68%. Mixed result: lower observed frame time but higher
CPU/memory. Retain for verified shader retirement; not an overall resource
improvement or minimum-hardware claim. `constant-native-abba-summary.json`.
All four runs completed normally with 2 captures at frame 2800. Runtime errors
are only existing ResolvePath device lookup failures (`constant-native-log-check.txt`).
Built/staged candidate hash matches 816980... above. No game/replay remains.

Census also found B6C VS paired with PS A4A965C189287B99 in three PSOs:
A77429BD4DAFD095, ED3A23D29736B921, B8E99C6B58FD4ACF. These remain translated.
Guest PS simply copies r0 to color0; guest VS supplies zero interpolator.
Translated PS includes alpha-test discard, coverage-mask calculation, and output
scaling, so a bare zero-color shader is not sufficient. Inspect its epilogue
and qualify both stages and all attachments
before admitting this pair. Guest PS dumps are in `v5-04-5a28-dump`.
Point draws remain intact; no side-effect-free draw elimination claim.
Full shader/command/resource retirement remains incomplete.

### Constant-position vertex shader qualified; activation pending

Audited B6C9863F710683EC in `native-indices-rdc/frame_frame3105.rdc`.
There are 120 point-list draws: 96 with null PS and 16-byte post-VS stride,
24 with a PS and 32-byte post-VS stride. The latter need an additional
zero interpolator and are not covered by this position-only candidate.
Audit `constant-vertex-audit/report.json`, captured reference DXBC/disassembly.
The guest program has no vertex fetch and outputs position (0,0,0,1), then
the translated epilogue applies viewport scale/offset. Do not remove the
point draws: attachment/query/command behavior has not been proven redundant.

Added `fh1_constant_position.vs.hlsl`, preserving precise zero*scale and fused
mad(offset,1,scaled_position). FXC produces four instruction slots (mul,mad,
mov,ret), no vertex resource fetch, versus the translated setup/loop.
`python tools/check-fh1-constant-position.py` compiles actual source and checks
these bytecode operations, including retaining zero*scale for exceptional
IEEE values. It passes. This is a shader replacement, not draw elimination.

`constant-vertex-depth-parity/report.json` verifies all 96 null-PS draws:
1,536 post-VS bytes and 6 full attachment snapshots totaling
325,058,560 bytes are exactly equal. Despite the report key
`depth_targets`, snapshots include every bound color and depth resource at
its last selected use. One shader variant, no errors. Script
`constant-vertex-depth-parity.py`. Initial broad `constant-vertex-parity`
correctly stopped on stride32 when it reached a PS-present draw; it is not
qualification evidence. The narrowed script selects the exact null-PS name.

No generated runtime header/admission yet. Production remains
4DCB59A572362F00A0757C78D56FDF5C35D21AC12E48DDEB654DC7BE71C96756.
No game/replay running. Next: collect pipeline states and activate qualified
null-PS shader, separately inspect/qualify the 24 PS-present draws, then
continue resource/command retirement. Full goal remains incomplete.

### Offset terrain families integrated and benchmarked

Admitted CA293E0A1CB4B416 PSO 6C161CE29479E1BF and 4E1DA281CC3D7EDB
PSO D7F8863A6EEF08AB using shared native `fh1_terrain_depth_offset_vs.h`.
Both require absent guest PS, bindless resources and host RTs. Eager preload
skips both guest shaders; unqualified states and failures retain lazy pack
fallback. Census instrumentation removed. Source backup
`before-offset-integration.cpp`; compiled with FXC vs_5_1 /O3, no define.
Depth admission/fallback, terrain arithmetic, layered bindings and 51 Python
contract tests pass; SDK builds successfully.

Live capture PID 40116, `offset-native-rdc/frame_frame3099.rdc`, normal exit,
2 screenshots, final image inspected. Both PSOs log guest VS/PS translated
false. Reverse parity with original captured DXBC verifies all 82 CA draws
(351,840 post-VS bytes, 83,886,080-byte depth target at event 3517) and all
74 4E draws (267,504 post-VS bytes, 42,065,920-byte target at event 2341).
All exact, no mismatches. Reports `offset-native-{ca,4e}-parity/report.json`
and `offset-native-parity-progress.json`.

Candidate `offset-native-candidate.dll`:
4DCB59A572362F00A0757C78D56FDF5C35D21AC12E48DDEB654DC7BE71C96756.
Baseline/rollback is `terrain-native-candidate.dll` (ECC5E3...).

A/B/B/A frame times (milliseconds):

| Run | Session | Median | p95 | CPU seconds/wall second |
| --- | --- | ---: | ---: | ---: |
| A1 | 20260907T024335Z-p33796 | 16.9700 | 21.207 | 3.1915 |
| B1 | 20260907T024426Z-p50132 | 16.6320 | 21.071 | 3.2124 |
| B2 | 20260907T024517Z-p49592 | 16.3335 | 19.958 | 3.1494 |
| A2 | 20260907T024608Z-p51076 | 16.9380 | 21.297 | 3.2318 |

Mean median -2.78%, p95 -3.47%, CPU -0.96%, private commit +0.02%,
working set -0.10%. Modest frame improvement on this machine and route;
no minimum-hardware or broad workload claim. All four runs exited normally
with two captures at frame 2800. `offset-native-abba-summary.json` and
corresponding scripts retain evidence. Runtime errors are only the existing
ResolvePath device lookup failures (`offset-native-log-check.txt`).
Built/staged hash matches 4DCB59... above. No census instrumentation or
running game/replay remains.

Next: remaining families and command/resource ownership. B6C9863F710683EC
is a frequent remaining VS with a tiny constant-output guest program
(o0=0000, oPos=0001); inspect live attachments/topology and output conventions
before replacing or removing any draws. Do not assume a constant output means
no query/register/render side effects. Its guest source is in
`v5-04-5a28-dump/shader_B6C9863F710683EC.ucode.vert`.

### Offset terrain variants corrected and qualified; activation pending

Corrected the nonstandard transform in `fh1_terrain_depth.vs.hlsl` for
CA293E0A1CB4B416 and 4E1DA281CC3D7EDB. Captured translated assembly shows
that the old candidate swapped final depth/w contributions. The guest also
explicitly computes rcp(w), multiplies y, subtracts c255.x, then multiplies
by w; simplifying this to y-c255.x*w loses its intermediate rounding.
The corrected candidate preserves those operations and guest zero multiply.
Backup `.local/native-renderer/before-terrain-offset.hlsl`.

Full replacement qualification in `native-indices-rdc/frame_frame3105.rdc`:

- CA293E0A1CB4B416: all 82 draws and 351,840 post-VS bytes exact; full
  83,886,080-byte depth target at event 3629 exact.
- 4E1DA281CC3D7EDB: all 74 draws and 267,504 post-VS bytes exact; full
  42,065,920-byte depth target at event 2562 exact.

Reports/scripts `terrain-offset-ca`, `terrain-offset-4e`,
`terrain-offset-qualify.py`, `terrain-offset-progress.json`. Each report
contains one shader variant, no errors and equal true. The preliminary
`terrain-offset-old` probe failed but overlapped a source edit; do not use
it to quantify old-vs-new regression. Reference assembly remains useful.

`tools/check-fh1-terrain-depth.py` now executes both actual transform branches
in a small C++ mock. Current source passes; --source before-terrain-offset.hlsl
compiles and fails the depth/w assertion, proving the regression check.
Initially the old-source mock lacked scalar-vector multiplication; that
harness limitation was fixed before obtaining the assertion failure.

FXC recompilation of the standard variant produces byte-for-byte identical
embedded BYTE array (`terrain-standard-after-offset.h`), so the active standard
path is unchanged. Production remains ECC5E3BF6350CFFE1FE8D411C375E91E2EB3132420DF52439C570F04877C9E9A.
No new variant activated, no native header for the offset variants yet, and
no game/replay remains running. Next: census actual PSO states, admit both
qualified offset terrain families, verify live parity and benchmark. Full
retirement still needs remaining shaders and command/resource ownership.

### Terrain standard depth integrated and benchmarked

Integrated qualified VS 5A28C7FAFD86F112 for the two actual gameplay PSO hashes
034B44F468DEC548 and 2370BFB73FCCFD27. Both require absent guest PS, host RTs
and bindless resources. Added compiled `fh1_terrain_depth_standard_vs.h` using
FXC vs_5_1 /O3 /D FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM=1. Eager preload skips
this guest VS; lazy fallback retains its pack entry. Existing scene bindings
and nullable fallback are reused. Temporary census removed. Source backup
`.local/native-renderer/before-terrain-integration.cpp`.

Build, native depth admission/fallback test, terrain arithmetic test, layered
binding test and 51 Python contract tests pass. Capture PID 24208 completed
normally, both screenshots produced and final screenshot visually inspected.
Both native PSOs log guest VS translated false and PS translated false.
Live capture `terrain-native-rdc/frame_frame3124.rdc`: reverse replacement
with captured original DXBC matches all 69 draws, 35,824 post-VS bytes, and
both full depth snapshots (42,065,920 bytes at event 2617; 83,886,080 bytes at
3517). `terrain-native-parity/report.json` and scripts contain evidence.

Candidate `terrain-native-candidate.dll` SHA256
ECC5E3BF6350CFFE1FE8D411C375E91E2EB3132420DF52439C570F04877C9E9A.
Baseline/rollback `depth-remaining-native-candidate.dll` (5A2BCB...).
A/B/B/A against 5A2BCB (frame times in milliseconds):

| Run | Session | Median | p95 | CPU seconds/wall second |
| --- | --- | ---: | ---: | ---: |
| A1 | 20260907T022939Z-p49088 | 16.8700 | 21.224 | 3.2574 |
| B1 | 20260907T023029Z-p47452 | 16.2325 | 20.156 | 3.4905 |
| B2 | 20260907T023120Z-p46884 | 16.4715 | 20.045 | 3.1848 |
| A2 | 20260907T023210Z-p31364 | 16.9395 | 22.408 | 3.3527 |

Mean median -3.27%, p95 -7.86%, CPU +0.99%, private commit -0.22%,
working set +0.66%. Observed frame improvement on this machine/route;
CPU/memory mixed and no minimum-hardware claim. All four runs completed
normally with 2 captures at frame 2800. `terrain-native-abba-summary.json`
and corresponding scripts retain the evidence. Logs show only existing
ResolvePath device lookup errors (`terrain-native-log-check.txt`).
Candidate ECC5E3... remains built/staged; no game/replay remains running.

Next terrain variants CA293E0A1CB4B416/4E1DA281CC3D7EDB remain unqualified.
Their captured guest programs explicitly calculate reciprocal(w), multiply
by y, subtract c255.x, then multiply by w. Existing nonstandard candidate
algebraically simplifies this to y-c10.x*w, which does not preserve rounding.
Inspect reference DXBC before correcting/qualifying these variants. Command
production and resource dependencies remain; full retirement stays active.

### Terrain-depth 5A28 arithmetic corrected; activation pending

Qualified the existing `fh1_terrain_depth.vs.hlsl` candidate for
VS 5A28C7FAFD86F112 using `FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM=1`.
The captured guest program and translated DXBC establish z+translation,y,x
transform accumulation, a saturated interpolation before the height clamp,
zero-multiply semantics, separate guest multiply/add rounding, and a fused
final viewport offset. Corrected the candidate to preserve these operations.
The standard transform previously summed x,y,z,translation; height interpolation
omitted its first saturation. Final output uses precise arithmetic, explicit
viewport mad, and division rather than approximate reciprocal.

Final replacement parity on `native-indices-rdc/frame_frame3105.rdc`:
111 draws, 59,088 post-VS bytes, both depth snapshots (42,065,920 and
83,886,080 bytes) exactly equal. `terrain-depth-precise/report.json` and
`terrain-depth-precise.py` contain evidence. Intermediate `terrain-depth-corrected`
matched depths but failed 8 vertex streams; the first failing draw 3994 had one
one-ULP float difference caused by unfused viewport arithmetic. Diagnostic
`terrain-depth-probe/positions-{0,1}.bin` and native/reference assembly retained.
Initial `terrain-depth-qualification` used the other transform mode, so its
failure is not evidence about the old standard-transform candidate.
Old source backup: `before-terrain-depth.hlsl`.
The old source with the correct standard-transform define fails 111 of 111
vertex streams and 2 of 2 depth snapshots;
`terrain-depth-old-standard/report.json`. No replay remains running.

Runnable production arithmetic check: `python tools/check-fh1-terrain-depth.py
--compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe` passes. It checks transform
sum order, interpolation saturation, zero times infinity, and final viewport
source invariants. GPU replay is the stronger whole-program evidence.

No terrain runtime activation or generated header yet. Built/staged production
remains `5A2BCB6A020969ADD68ED6CB07CF4EDD9133A8DDC1E1CCDB0C1CB2F335334C2F`.
Next: collect actual terrain PSO descriptions, compile/admit this qualified
standard variant, verify live embedded-bytecode parity and benchmark. Other
terrain variants CA293E0A1CB4B416/4E1DA281CC3D7EDB remain unqualified; they use
the other transform mode. Full retirement still requires command/resource work.

### Remaining depth strides integrated and live parity verified

The corrected shared depth shader passed captured replacement parity for strides
20/28/32: 63/69/66 draws and 716,704/534,528/311,776 post-VS bytes respectively.
Both depth snapshots per family (42,065,920 and 83,886,080 bytes) matched exactly.
Reports: `.local/native-renderer/depth{20,28,32}-qualification/report.json`.

Added narrow native admissions for VS 9BF2991815B941B9 (PSOs 9CE112156F9A2FE7,
0D0C6B5516E60BB8), B646F85EF69A57E0 (4FAB5D009EDC7575, B11F709480BB88C7,
0462A10067F56C6C), and D0C40C04F166092E (DAA16CBF4502F6F6,
EEA552E1610954A1). All require absent guest PS, bindless resources and host RTs.
Reused existing stride bytecode selection and nullable fallback. Eager preload
skips these families; pack entries remain available for lazy fallback.
The broad depth switch remains false. Temporary census instrumentation removed.

Build and depth binding/order/layered checks plus 51 Python contract tests pass.
Live run PID 44356 exited normally with both captures; final image inspected.
All seven PSOs logged guest VS/PS translated false.
Candidate `depth-remaining-native-candidate.dll` SHA256
`5A2BCB6A020969ADD68ED6CB07CF4EDD9133A8DDC1E1CCDB0C1CB2F335334C2F`.
Rollback is `depth-native-final-candidate.dll` (8D71AC...). Source backup
`before-depth-remaining.cpp/.h`. Performance comparison and live reverse parity are complete.

Live capture `depth-remaining-native-rdc/frame_frame3077.rdc`, PID 49456:
reverse replacement with original captured DXBC verified 45/58/63 draws for
strides 20/28/32; 575,920/505,024/309,168 post-VS bytes matched exactly.
Both full depth snapshots per family also matched. The checks assert that the
live bytecode differs from the translated reference and that selected draws
are nonempty. Reports/scripts: `depth{20,28,32}-live-parity/report.json`,
`depth-remaining-live-parity.py`, `depth-remaining-reference.json`.
No new runtime errors beyond existing ResolvePath device lookup failures;
`depth-remaining-native-log-check.txt` records inspected logs.

A/B/B/A against prior stride-24 build (milliseconds):

| Run | Session | Median | p95 | CPU seconds/wall second |
| --- | --- | ---: | ---: | ---: |
| A1 | 20260907T021042Z-p29736 | 16.7240 | 21.180 | 3.5639 |
| B1 | 20260907T021133Z-p30808 | 16.6345 | 20.603 | 3.0957 |
| B2 | 20260907T021224Z-p22552 | 17.0215 | 21.337 | 3.1585 |
| A2 | 20260907T021315Z-p48320 | 16.6470 | 21.172 | 3.0775 |

Mean median frame time +0.85%, p95 -0.97%, CPU -5.83%, private commit
+0.19%, working set +0.26%. Mixed/inconclusive performance: apparent CPU
improvement is dominated by A1; B runs are slower than A2 on CPU. Retain for
verified translated shader retirement, not a hardware-requirement claim.
Evidence: `depth-remaining-native-abba-summary.json` and corresponding scripts.
No temporary census/failure injection remains; built and staged DLL hashes
match the candidate above. No game or replay remains running.

Next: investigate remaining depth families (e.g. 5A28C7FAFD86F112), expand scene
coverage, and replace command/resource dependencies. The four shared depth
strides still consume guest shared geometry and emulated command production.
Full Xenos retirement remains incomplete; the goal stays active.

### Depth stride-24 native pipeline integrated - 2026-09-07 UTC

C8C39E5AE1B08DE6 now uses the corrected native stride-24 VS for exactly two
observed depth-only pipeline descriptions: `53BA06CDA0AF43C1` and
`864862F2FDCC2307`. Admission also requires bindless resources and host render
targets. The broad four-stride substitution switch remains false; other states
retain their existing path. Temporary gameplay census session (PID 16948) found
these two hashes; that instrumentation has been removed.

Integration extends the existing native stage path, rather than overriding a
translated VS after loading it. ConfigurePipeline considers the null-PS family
before materializing guest bytecode. Startup skips its eager shader preload, and
prewarm/creation use native bindings with an absent pixel stage. Both retained
native pipeline creation logs explicitly report guest VS translated false and
PS translated false. An intermediate build still eagerly loaded the VS; do not
use `depth-native-*` artifacts for this claim. Use `depth-native-final-*`.

PrepareFh1SceneBindings now accepts an optional pixel shader. All warmup/runtime
callers were updated. The creation-failure translation loop skips missing stages,
and its logs no longer dereference a null PS. Guest bytecode remains available
for lazy fallback and unqualified states; no pack entries were removed.

Validation:

- `tools/check-fh1-depth-pipeline.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  compiles production native admission, binding preparation, startup skip and
  fallback loop. It checks both admitted hashes, adjacent-hash rejection,
  non-null-PS rejection, bindful/ROV rejection, absent/present pixel bindings,
  preparation failure, lazy translation, already-loaded stages and invalid/failing
  translations. Its first harness attempt incorrectly parsed a for-loop's
  initializer-list brace; the extractor was fixed and the production checks pass.
- Existing layered binding checker and 51 shader-pack, renderer-contract,
  release-contract and render-test Python checks pass. SDK builds pass.
- Final capture session `20260907T015011Z-p32012`: normal exit, two screenshots,
  frame 2800. `depth-native-final-preview.png` inspected, scene intact.
- `.local/native-renderer/depth-native-final-rdc/frame_frame3170.rdc` contains 66
  selected depth-family draws (the prior qualification capture contained 122).
  Reverse replacement with the original captured translated bytecode matches
  every post-VS byte: 295,936 total, zero mismatches. Both depth snapshots at the
  last selected draw match: 42,065,920 bytes at event 1266 and 83,886,080 bytes at
  event 4263. Report/script: `depth-native-final-parity/report.json` and
  `depth-native-final-parity.py`. This checks the actually embedded live native
  shader against original bytecode on the same captured inputs, not only newly
  compiled HLSL. The script rejects a live shader equal to the reference binary.
- Original captured shader: `.local/native-renderer/depth24-reference.dxbc`,
  11,576 bytes, SHA-256
  `bba7bcd6f07b2e9d9779ebc9ef695ffa5e8055a9f2dbcec5a91ed275e4203804`.
  Export/acceptance evidence `depth24-reference.json`.
- Deliberately failing native CreateGraphicsPipelineState for both depth states
  completed session `20260907T015635Z-p49536` normally with two captures/frame
  2800. Both log guest fallback with VS translated true / PS translated false.
  The failure injection was removed and rebuilding restored the exact retained
  candidate hash. Evidence: `depth-forced-fallback`, `depth-fallback-build.log`,
  `depth-native-restored-build.log`, `depth-native-final-log-check.txt`.
- The inspected runtime logs contain only the existing ResolvePath device error.

A/B/B/A versus the preceding native-index-upload build, standard AppData 2x
stationary route, all four normal exits / two captures / frame 2800:

| Run | Median ms | p95 ms | CPU seconds / wall second | Private MiB | Working MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 17.2385 | 21.974 | 3.1828 | 4692.84 | 1877.32 |
| B1 | 16.6370 | 20.791 | 3.2064 | 4676.58 | 1861.48 |
| B2 | 16.8290 | 21.324 | 3.1777 | 4708.54 | 1867.17 |
| A2 | 17.1785 | 21.679 | 3.2348 | 4715.43 | 1877.69 |

Mean median -2.76%, p95 -3.52%, CPU -0.52%, private -0.25%, working -0.70%.
Modest observed frame-time improvement; CPU/memory changes are small and do not
establish lower minimum hardware requirements. Single scene/machine only.
Evidence: `.local/native-renderer/depth-native-final-abba-summary.json`.

Retained built/staged SHA-256:
`8D71AC523B9B5A1F65966410048073E9D3F4BE97D4897F95E0B5F534A46FF1A7`
(`depth-native-final-candidate.dll`). Baseline/rollback is `native-indices-candidate.dll`
with hash `9C8707F0024997C0802681D9F5943C76F0BC1FF69AD9B38FB94AB22DC2340F7D`.
Source backups `before-depth-integration.cpp/.h`; final source copy
`depth-native-final-pipeline.cpp`. No game/replay remains running or failure
injection remains active. No saves copied or reset.

Next: qualify the remaining shared depth-mesh strides (20/28/32) against captured
outputs, collecting their actual used pipeline states before admission. Reuse
nullable native-stage integration and the corrected shader; do not enable the
broad switch. Full Xenos retirement remains incomplete: native command production,
other shader families, geometry/texture/RT ownership and general renderer
infrastructure still require work. This family still reads the shared geometry
buffer; this change retires its qualified translated shader execution, not all
of its resource/command dependencies.

### Depth stride-24 arithmetic repaired and replay-qualified - 2026-09-07 UTC

Audited the existing disabled C8C39E5AE1B08DE6 depth-only candidate against
`.local/native-renderer/native-indices-rdc/frame_frame3105.rdc`. The candidate had
two real floating-point ordering errors; it was not safe to enable as written.

1. The model transform sums z,x,y,w, but the reference projection sums w,z,x,y.
   The shared Fh1Dot4 helper previously imposed model order on both transforms.
   Projection arguments now use `.zxwy` on both operands so the existing helper
   produces the reference order. At visible event 1347 this fixes 234 differing
   depth values (235 bytes) in the 9,232-byte post-VS buffer and one differing byte
   in a 42,065,920-byte depth target. The deliberately wrong shader changes six
   target bytes, confirming the comparison detects actual contribution.
2. The wider 122-draw check still found 32 post-VS mismatches despite equal final
   depth targets. Event 4581 had 21 differing x/y values. Compiled DXBC showed FXC
   moving the multiply-add from viewport offset*w + scaled_position to
   position*scale + offset*w. Declaring final `position` precise preserves the
   intended multiply followed by the explicit offset multiply-add. The emitted
   assembly now matches the reference order. The event-4581 wrong-shader probe
   changes 52,970 depth bytes; its ordinary candidate mismatch was hidden in the
   final depth target, illustrating why position checks were required.

Source: SDK `src/graphics/shaders/fh1_depth_mesh.vs.hlsl`. Regenerated all four
20/24/28/32 stride headers with FXC vs_5_1 /O3 and the corresponding
FH1_DEPTH_STRIDE_BYTES definition, keeping the shared source and headers aligned.
Only stride 24 is GPU-qualified here; the others remain unqualified/inactive.

Final replay evidence:

- `.local/native-renderer/depth24-precise/report.json` and sibling script.
- All 122 C8C39E5AE1B08DE6 depth-only draws, one translated shader variant:
  582,448 post-VS bytes exactly equal after native replacement, zero mismatches.
- Both depth targets at their last selected draw compare exactly: 42,065,920
  bytes at event 1964 and 83,886,080 bytes at event 5349 (125,952,000 total).
- Earlier diagnostic evidence remains in `depth24-probe`, `depth24-order-probe`,
  `depth24-family`, and `depth24-draw4581`. The first full-family result is a
  **failure** (32 mismatches); use `depth24-precise` for the final result.
- Reference disassembly: `depth24-probe/reference-disassembly.txt`.
- This qualifies captured post-VS outputs and two depth snapshots, not arbitrary
  game states, other strides, complete frames, or performance.

`python tools/check-fh1-depth-order.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
compiles the production dot helper/projection expression into a small float
regression check. It distinguishes both accumulation orders and requires precise
final position. Current source passes; `--source
.local/native-renderer/depth24-probe/before-depth-order.hlsl` fails, reproducing
projection-order loss. All four FXC builds and the SDK build pass
(`depth-order-build.log`).

**Live activation is still pending.** kFh1UseNativeDepthMeshVertexShaders remains
false. Built and staged DLLs remain byte-identical to the preceding validated
renderer, SHA-256
`9C8707F0024997C0802681D9F5943C76F0BC1FF69AD9B38FB94AB22DC2340F7D`.
No game or replay process remains running. No live performance claim this turn.

Next: add depth-only admission through the real native stage path, rather than
turning on the broad four-stride substitution switch. Current
IsFh1NativeScenePipeline only recognizes three VS/PS pairs, and
PrepareFh1SceneBindings plus its creation/warmup callers unconditionally require
a pixel shader. Audit all callers before admitting a null-PS family; preserve
creation-failure fallback and exact observed pipeline constraints. The depth VS
should bypass the unused translated vertex binary, not merely override it after
loading. Then run live capture/parity and performance qualification. Remaining
renderer families, native command production and resource ownership still keep
the full Xenos retirement goal incomplete.

### Native layered bindings omit unused index uploads - 2026-09-07 UTC

UpdateBindings no longer allocates/writes vertex or pixel bindless descriptor-index
constant buffers when the fixed native layered root is active. Texture/sampler
layout keys and dirty tracking still update normally. A zero buffer address marks
a current layout with no GPU index upload; a generic pass invalidates that state
and uploads its indices before binding. The native root also omits the unused
vertex index CBV binding. Fixed pixel SRV/sampler bindings, heap rollover handling
and guest fallback retain their existing paths. No new cache or state object.

Validation:

- Release SDK build passed (`native-indices-build.log`).
- `python tools/check-fh1-layered-texture-bindings.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  compiles the production allocation, fallback restoration and root-binding
  branches. Native allocation count is zero; generic restoration uploads fresh
  buffers, retries allocation failure and preserves current uploaded bindings.
  Native draws bind neither index CBV, while fixed texture/sampler slot changes,
  heap rollover and generic-root transitions still pass.
- Existing 51 shader-pack, renderer-contract, release-contract and render-test
  Python checks pass.
- Capture session `20260907T011810Z-p32416` completed normally, two captures at
  frame 2800; `native-indices-preview.png` inspected, scene intact.
- `.local/native-renderer/native-indices-rdc/frame_frame3105.rdc` has all 356
  layered geometry / two texture views / sampler tuples equal to the previously
  verified fixed-root reference, including duplicate counts. Zero unmatched
  tuples. Eight unique texture resources include all mip bytes as in the prior
  audit. Report/script: `.local/native-renderer/native-indices-inputs.json/.py`.
  Contents are cached at first resource use; this does not verify arbitrary
  mid-frame texture mutation, per-draw constants, or whole-frame equality.
- `native-indices-log-check.txt` contains only the existing ResolvePath device
  error across the capture and four benchmark sessions.

A/B/B/A versus the preceding CPU geometry build, standard AppData 2x stationary
route, all four normal exits / two captures / frame 2800:

| Run | Median ms | p95 ms | CPU seconds / wall second | Private MiB | Working MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 17.1015 | 21.576 | 3.1414 | 4704.91 | 1874.15 |
| B1 | 16.5160 | 19.627 | 3.3854 | 4713.38 | 1889.04 |
| B2 | 16.7450 | 20.874 | 3.1752 | 4715.18 | 1888.44 |
| A2 | 16.7650 | 20.830 | 3.1976 | 4698.66 | 1874.08 |

Mean median -1.79%, p95 -4.49%, CPU +3.50%, private +0.27%, working +0.78%.
Mixed results: unused work was removed, but no overall resource reduction or
lower hardware requirement is established by this sample. Evidence:
`.local/native-renderer/native-indices-abba-summary.json` and sibling runs.

Retained built/staged SHA-256:
`9C8707F0024997C0802681D9F5943C76F0BC1FF69AD9B38FB94AB22DC2340F7D`
(`.local/native-renderer/native-indices-candidate.dll`). Baseline/rollback:
`5A0503B864260D34B25B686CCDD4D2BE419600C1BA2AF197ABB75D5FAC5A20DA`
(`cpu-geometry-validated-candidate.dll`). Source backup `before-native-indices.cpp`.
No game/replay remains running; no saves copied or reset.

The same capture maps 4,189 draws. Largest pipeline-name groups:

- Layered native VS 3BC346726C1C2535 / PS 9584B309533EF6C9: 356.
- Native VS 8D8A197476841A9A / PS BA6A2871A980A4E8: 254.
- Native VS AD2C355A6BE1EE87 / PS 2F2137BF953DA7AF: 245.
- VS C8C39E5AE1B08DE6 (no pixel shader): 122.
- VS 6934E161812AB10B / PS A2C1F872E049AD8B: 115.
- VS 5A28C7FAFD86F112 (no pixel shader): 111.

Next: investigate/qualify the existing C8C39E5AE1B08DE6 depth candidate against
live draws before enabling it. PipelineCache already contains a candidate branch;
inspect its current admission and shader semantics rather than writing another
implementation. Counts are one frame's draw frequency, not GPU-time estimates.
Full Xenos retirement remains incomplete, including remaining families, native
command production, render-target ownership and generic renderer infrastructure.

### Owned geometry imports directly from CPU data - 2026-09-07 UTC

`GetFh1OwnedGeometry` now uses the existing upload pool and protected CopyCpuRange
to fill its existing default-heap buffer from CPU-authoritative bytes. Its watch
is armed before reading. GPU-owned pages or upload-pool allocation failure use
the original shared-memory source; failed fallback removes the watch and retries
on later use. Cache allocation limits, submission lifetime, eviction and root
rebasing are unchanged. There is no extra persistent geometry allocation.

The draw-path audit also found an earlier vertex residency loop. Owned-geometry
selection now precedes that loop, and a successful owned buffer skips fetch 95's
shared residency request after the existing fetch-type validation. Other fetches
and failed owned-buffer selection retain the original path. This removes both
the cache's intermediate source copy and the redundant per-draw residency check
for the qualified native layered path, without marking skipped shared data valid.

Validation:

- Release SDK build passed (`cpu-geometry-validated-build.log`).
- `python tools/check-fh1-geometry-cache.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  passes production cache code with CPU imports, nonzero upload offsets, writes
  during import, GPU rejection, upload allocation failure, failed residency,
  cache hits, range alignment, allocation budget and in-flight eviction. Successful
  CPU imports make zero shared RequestRange calls. The extracted fetch-95 skip
  is checked for owned/fallback selection and placement after fetch validation.
- CPU-source ownership/protection checker passes; existing 51 shader-pack,
  renderer-contract, release-contract and render-test Python checks passed during
  this change. Geometry shaders and their standalone bytecode were not changed.
- Final capture session `20260907T010727Z-p23276` completed normally, two captures,
  frame 2800. `cpu-geometry-validated-preview.png` inspected, scene intact.
- `.local/native-renderer/cpu-geometry-validated-rdc/frame_frame3021.rdc`:
  3,881 mapped draws; all 356 layered draws / 214 ranges / 1,193,400 bytes match
  the previously verified geometry content multiset, including multiplicity.
  Zero fallback draws, zero missing/extra reference draws, zero in-frame copies.
  Report: `.local/native-renderer/cpu-geometry-validated-parity/geometry-parity.json`.
- `tools/check-fh1-owned-geometry-replay.py` now accepts optional
  `PINYON_SHIFT_GEOMETRY_REFERENCE` pointing to a successful prior report. This
  compares actual content hashes/lengths and duplicate counts independently of the
  current shared GPU buffer, which can be stale by design. The reference used was
  `.local/native-renderer/fixed-layered-geometry-parity/geometry-parity.json`.
  Without this option, the original same-capture shared-source check remains.
  This is geometry-input multiset equality, not per-draw constant or whole-frame
  equality, nor a claim covering arbitrary scenes/mutations.
- At the final capture's logged cache checkpoint, all 59 imports were CPU imports,
  allocation 5,242,880 bytes. Candidate benchmark logs similarly show all 64/65
  imports using CPU data. Runtime logs contain only the existing ResolvePath error
  (`cpu-geometry-validated-log-check.txt`).

A/B/B/A versus the preceding texture residency-bypass build, standard AppData 2x
stationary route; all four normal exits, two captures, frame 2800:

| Run | Median ms | p95 ms | CPU seconds / wall second | Private MiB | Working MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 17.3680 | 21.816 | 3.2815 | 4728.36 | 1895.02 |
| B1 | 17.2910 | 21.763 | 3.2245 | 4701.62 | 1871.43 |
| B2 | 16.5830 | 20.127 | 3.1925 | 4700.03 | 1881.03 |
| A2 | 16.8160 | 21.045 | 3.5415 | 4703.83 | 1890.31 |

Mean median -0.91%, p95 -2.27%, CPU -5.95%, private -0.32%, working -0.87%.
These are observed short single-scene results; run variance remains, and no lower
minimum hardware requirement or universal gain is claimed. Evidence:
`.local/native-renderer/cpu-geometry-validated-abba-summary.json` and sibling runs.

Retained built/staged SHA-256:
`5A0503B864260D34B25B686CCDD4D2BE419600C1BA2AF197ABB75D5FAC5A20DA`
(`.local/native-renderer/cpu-geometry-validated-candidate.dll`). Baseline/rollback:
`23FCF44B1E599B579963459AC5C363B3211CD1D6E1AEE559A84C6B42E1470598`
(`cpu-residency-candidate.dll`). Source backups `before-cpu-geometry.cpp/.h`.
Earlier `cpu-geometry-*` and `cpu-geometry-final-*` captures are intermediate
experiments; use the `cpu-geometry-validated-*` artifacts for retained evidence.
No game or replay process remains running; no save files copied or reset.

Next audited dependency: UpdateBindings still uploads generic vertex/pixel
bindless descriptor-index constant buffers for this fixed-binding native layered
root (including a deliberate ponytail note). Remove those unused uploads while
preserving guest fallback invalidation, texture/sampler changes and heap rollover.
Full Xenos retirement remains incomplete: other draw families, command production,
render-target ownership and generic renderer/resource infrastructure remain.

### Native BC3 imports bypass shared GPU residency - 2026-09-07 UTC

The qualified layered BC3 import now runs after watches are armed and before
shared-memory residency is requested. `PrepareTextureLoad` tries the CPU backend
and completes the watched load immediately on success, leaving no pending GPU
range. Rejected imports retain the original residency/backend path. The previous
post-residency CPU attempt was removed. Other backends default to the existing
loader; there is no second cache or resource lifetime.

`CopyCpuRange` now enables physical write-invalidation callbacks before reading,
outside the shared global lock to preserve heap/global lock ordering. It requires
a registered invalidation callback and still rejects GPU-written pages without
copying or changing GPU-valid flags. It does not call MakeRangeValid or allocate
shared GPU residency. Watches remain responsible for writes during/after copy.
This replaces the redundant raw guest upload for successful native BC3 loads;
other uses of the same memory can still request their own residency.

Validation:

- Release SDK build passed (`cpu-residency-build.log`).
- `python tools/check-fh1-texture-watch.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  passes the actual prepare/load/complete functions with CPU success/rejection,
  writes during import, partial loads and fallback. Successful CPU imports issue
  zero residency requests and zero resident-backend calls. Legacy lost-write
  source checking remains supported without running the new CPU-path cases.
- `python tools/check-fh1-cpu-source.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  additionally checks protection before source access and missing-callback
  rejection, alongside existing bounds/GPU ownership/unchanged-output cases.
- Existing 51 shader-pack, renderer-contract, release-contract and render-test
  Python checks pass.
- Capture session `20260907T005317Z-p49312` completed normally with two screenshots
  at frame 2800. `.local/native-renderer/cpu-residency-rdc/frame_frame3108.rdc`
  contains 4,114 mapped draws / 356 layered draws. All eight unique BC3 resources,
  read at first use, match the reference: 77 mips, 2,031,840 bytes. Report:
  `.local/native-renderer/cpu-residency-texture-parity.json`. This remains
  resource-content equality, not whole-frame or arbitrary mid-frame mutation proof.
- `cpu-residency-preview.png` inspected, scene intact. The capture logged 14 CPU
  imports (including streamed placeholders). `cpu-residency-log-check.txt` contains
  only the existing ResolvePath device error across capture and benchmark sessions.

A/B/B/A versus the preceding CPU-import-with-residency build, same AppData 2x
stationary route, all four normal exits / two captures / frame 2800:

| Run | Median ms | p95 ms | CPU seconds / wall second | Private MiB | Working MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 17.2135 | 22.416 | 3.6003 | 4717.75 | 1891.18 |
| B1 | 17.0100 | 22.041 | 3.7164 | 4736.52 | 1902.98 |
| B2 | 17.1245 | 21.614 | 3.1518 | 4718.02 | 1898.42 |
| A2 | 16.7075 | 21.051 | 3.3138 | 4732.90 | 1900.23 |

Mean median +0.63%, p95 +0.43%, CPU -0.67%, private +0.04%, working +0.26%:
no meaningful steady-state gain established. Import dependency removal is the
result; sustained streaming/loading and lower-end hardware remain unqualified.
Evidence: `.local/native-renderer/cpu-residency-abba-summary.json` and sibling runs.

Retained built/staged SHA-256:
`23FCF44B1E599B579963459AC5C363B3211CD1D6E1AEE559A84C6B42E1470598`
(`.local/native-renderer/cpu-residency-candidate.dll`). Previous `1EDFA0FA...`
`cpu-bc3-candidate.dll` remains the rollback. Source backups are
`.local/native-renderer/before-cpu-residency-*`. No game remains running.

Next audited dependency: `GetFh1OwnedGeometry`'s import path in
`d3d12/command_processor.cpp` still calls RequestRange then copies from the shared
GPU buffer. Its one-shot watch is already armed before this point. Reuse the
protected CPU-source gate and existing upload pool/cache/fence lifetime to remove
that intermediate source where CPU-authoritative, with GPU-written fallback and
byte-parity qualification. The full Xenos retirement goal remains incomplete:
remaining draw families, command production, render targets and other resources
still depend on the emulation renderer.

### Live CPU BC3 texture import qualified - 2026-09-07 UTC

The layered native pass now imports eligible BC3 textures on the CPU into the
existing D3D12 texture resources and upload pool. The standalone importer moved
to SDK `include/rex/graphics/pipeline/texture/bc3_import.h`; the tool calls the same
implementation. There is no second texture cache or duplicated resource lifetime.
Admission requires the actual native layered root, unscaled non-array 2D BC3,
no forced 3D tiling, available base data, dimensions at most 512, and a native
BC3 resource format. Other loads keep the existing backend path.

`SharedMemory::CopyCpuRange` checks the entire source range under the existing
critical region and rejects GPU-written pages before copying any bytes. It does
not alter residency/validity. The caller must have armed watches and protected
the source first; the current path does so through PrepareTextureLoad and
RequestRanges. CPU import reuses the repaired completion/watch lifecycle, so
writes during import remain dirty. Uploads honor D3D12 row/placement alignment,
selected base/mip subresources, resource transitions and existing fence lifetime.

This is an incremental retirement step, **not a demonstrated speedup or complete
native texture ownership**. RequestRanges still uploads raw guest bytes before
the native import, and the texture cache/guest fetch decoding remain dependencies.
Next: separate protected CPU-source import from shared-memory GPU residency,
retaining GPU-written-page fallback, watch-before-copy ordering and retry behavior.
Do not call MakeRangeValid solely to protect a CPU snapshot: that would falsely
claim GPU contents are resident/current. Partial reload selection is implemented,
but the live qualification here observes initial full-chain imports; retain
focused partial-load/failure checks when changing the residency boundary.

Validation:

- SDK and standalone importer built successfully. Importer self-test and all eight
  saved fixtures pass using the shared header (2,031,840 decoded bytes).
- `python tools/check-fh1-cpu-source.py --compiler .local/toolchain/llvm-20.1.8/bin/clang++.exe`
  passes production-function checks for page/word boundaries, GPU rejection with
  unchanged destination, unrelated GPU bits, empty/range overflow and final page.
- `tools/check-fh1-texture-watch.py` passes; the existing 51 shader-pack,
  renderer-contract, release-contract and render-test Python checks pass.
- Working capture `.local/native-renderer/cpu-bc3-rdc/frame_frame3152.rdc`:
  3,893 mapped draws, 354 layered draws. All eight unique unsigned BC3 resources,
  read at first use, match the reference across 77 mip levels / 2,031,840 bytes.
  `.local/native-renderer/cpu-bc3-texture-parity.json` records hashes/events.
  The reference has 356 layered draws, so this is content-set equality, not
  per-draw or whole-frame equality. Later mutation within the frame is not tested.
- Gameplay screenshot `cpu-bc3-preview.png` inspected; scene intact. Runtime logs
  show 13 imports in the working capture and 17/15 in candidate benchmark runs.
  `cpu-bc3-final-log-check.txt` contains only the existing ResolvePath device error.

A/B/B/A versus the preceding texture-watch build, standard AppData 2x stationary
scene, all four normal exits with two captures at frame 2800:

| Run | Median ms | p95 ms | CPU seconds / wall second | Private MiB | Working MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 16.9005 | 21.043 | 3.2594 | 4739.92 | 1881.79 |
| B1 | 17.1245 | 21.754 | 3.3524 | 4751.41 | 1883.89 |
| B2 | 17.0385 | 22.115 | 3.1496 | 4720.96 | 1891.48 |
| A2 | 16.9820 | 21.683 | 3.2971 | 4689.55 | 1882.97 |

Mean median +0.83%, p95 +2.68%, CPU -0.83%, private +0.45%, working +0.28%:
no performance gain claimed. This short stationary single-machine run does not
qualify loading performance, sustained streaming, or lower hardware requirements.
Evidence: `.local/native-renderer/cpu-bc3-abba-summary.json` and sibling script/runs.

Retained built/staged SHA-256:
`1EDFA0FA89BCB34FF64609E72E00E8BBC527022E1FD016F591F017FC5DD30143`
(`.local/native-renderer/cpu-bc3-candidate.dll`). Baseline is
`A52E4C701D1592FD2321CA3F7C1F46295AE92D8E994171ADAB0051558A6C6767`
(`texture-watch-candidate.dll`). No game remains running; no saves copied/reset.
An intermediate `cpu-bc3-active-*` experiment used the wrong fullscreen-only
predicate and did not execute imports. It was reverted; do not use those artifacts
as CPU-import evidence. The original root-based admission is correct; restored
source rebuilt to the identical retained hash above.

### Texture import invalidation race repaired - 2026-09-07 UTC

The live texture lifecycle audit found a lost-write race before native ownership
could reuse it. Previously `CommitPreparedTextureLoad` called
`MakeUpToDateAndWatch` only after residency and backend import. A CPU write during
that interval could leave the uploaded older bytes marked current. Completion
also cleared every outdated region, including a region that became dirty after
a partial load had been prepared.

The shared texture loader now arms watches in `PrepareTextureLoad`, before
`RequestRanges`. `CompleteLoad` clears only the requested base/mip regions whose
one-shot watches survived the entire upload. A callback during residency or
backend import leaves its region dirty for the next draw. Failed residency,
scaled-resolve commitment or backend loads retain dirty state and trigger binding
reconsideration. Re-preparing after a failed batch reuses existing watches instead
of replacing/leaking them. This repairs both batch and direct load callers in the
shared cache. The SharedMemory callback comment now accurately says the one-shot
handle is retired before callback entry, matching the existing implementation.

`tools/check-fh1-texture-watch.py` compiles the actual production prepare, load,
commit and callback functions with deterministic write/failure injection. It tests
CPU/GPU notifications during residency/backend load, base/mip independence,
unrequested-region writes, retries, duplicate preparation and watch counts.
The current code passes. Running the same checker against
`.local/native-renderer/before-texture-watch.cpp` fails at the assertion that the
written region remains dirty, reproducing the previous behavior. This is a
control-flow regression check, not a hardware concurrency stress test.

Retained staged/artifact/candidate DLL SHA-256:
`A52E4C701D1592FD2321CA3F7C1F46295AE92D8E994171ADAB0051558A6C6767`.
Candidate: `.local/native-renderer/texture-watch-candidate.dll`.
Prior FE4C91FC... rollback: `.local/native-renderer/fixed-layered-final.dll`.
The only subsequent source edit is the callback documentation correction.

Validation:

- SDK build and all 51 existing Python checks pass, along with the new race,
  partial-load and retry checks. The pre-change source fails the regression check.
- AppData capture session **20260907T001715Z-p51116** completes normally with two
  screenshots at frame 2800. The final screenshot was inspected and is visually
  consistent with the existing scene. Capture:
  `.local/native-renderer/texture-watch-rdc/frame_frame3061.rdc`.
  No new whole-frame pixel-equality claim is made for this lifecycle-only change.
- Five inspected runtime sessions (capture and A/B/B/A) show only the existing
  filesystem ResolvePath device error. Excerpt:
  `.local/native-renderer/texture-watch-log-check.txt`.

AppData 2x A/B/B/A against the preceding fixed-binding build:

| Run | Session | CPU seconds / wall second | Private MiB | Working MiB | Median / p95 ms |
| --- | --- | --- | --- | --- | --- |
| A1 | 20260907T001839Z-p50776 | 3.2130 | 4710.91 | 1888.74 | 17.0480 / 21.439 |
| B1 | 20260907T001929Z-p23532 | 3.3733 | 4745.06 | 1893.20 | 17.2190 / 22.823 |
| B2 | 20260907T002020Z-p39068 | 3.1647 | 4745.68 | 1891.16 | 16.8845 / 21.872 |
| A2 | 20260907T002110Z-p48692 | 3.7203 | 4686.49 | 1853.41 | 16.9100 / 21.779 |

All complete normally with two captures at frame 2800. Mean changes: median
**+0.43%**, p95 **+3.42%**, CPU **-5.70%**, private commit **+0.99%**, working set
**+1.13%**. Variation is substantial, especially baseline CPU, and draw counts
also differ. No speedup or memory reduction is claimed. Keep the correctness fix;
possible overhead remains to be checked as native texture ownership is integrated.
Reports/samples: `.local/native-renderer/texture-watch-abba-*`.

Remaining native CPU-source requirements from the code audit:

- Raw CPU physical memory can be stale for GPU-written pages. SharedMemory tracks
  these in `system_page_flags_valid_and_gpu_written_`; native import must respect
  that ownership and GPU command ordering instead of assuming CPU authority.
- `WatchMemoryRange` registers a callback but does not itself protect CPU pages.
  The existing path enables write callbacks via `MakeRangeValid` during residency.
  Removing residency requires explicit write-callback protection. Do not mark the
  GPU copy valid merely to protect CPU pages, since that would suppress needed
  uploads for other consumers.
- `MemoryInvalidationCallback` fires watches even on pages with cleared validity
  bits. Reuse this behavior where appropriate rather than inventing another broad
  asset cache. Native resource ownership and invalidation are still not integrated;
  the qualified standalone CPU importer remains the next source-format building
  block. Full Xenos retirement remains active.

### CPU texture import qualified without renderer libraries - 2026-09-07 UTC

The next texture dependency is now tested directly: the eight BC3 resources used
by the captured layered pass can be reconstructed from guest-format bytes without
TextureCache, a command processor, a GPU device or texture-load shaders.
`tools/fh1_texture_import.cpp` reuses the existing pure texture layout, packed-mip
offset and tiled-address helpers. It imports 2D non-array BC3 blocks, applies the
fetch byte order, checks source extents and emits standard DXT5 DDS assets after
comparison with captured GPU bytes. It intentionally rejects unsupported formats,
arrays and missing base levels. This is import qualification, **not yet live native
texture ownership**. No captured asset is substituted into gameplay.

The new `pinyon_shift_fh1_texture_import` target links only its source, texture
`util.cpp`, `info_formats.cpp` and the platform math helpers. Its Windows imports
are only Kernel32/MSVC/CRT; no ReXGlue renderer/runtime or D3D library is imported.
The standalone `--self-test` verifies the four byte orders with explicit expected
byte sequences and rejects unsupported formats. Each captured texture also tests
empty base/mip data rejection and verifies that changing a byte actually consumed
from the source changes the imported result.

`tools/export-fh1-layered-textures.py` reads selected fixed-root draws from
RenderDoc and exports fetch constants, bounded raw GPU shared-memory snapshots and
expected BC3 mip bytes. Its 1 MiB per-region snapshot cap is a fixture limit, not a
runtime residency rule. It requires a new output directory. The importer likewise
requires a new output directory and reports mismatches as failures.

Verified against `.local/native-renderer/fixed-layered-rdc/frame_frame3116.rdc`:

- Events **11003, 11010, 11017, 11024, 11035, 11042, 16561, 16715** cover all eight
  distinct layered textures from the preceding binding audit.
- **77 mip levels / 2,031,840 BC3 bytes match exactly**. All captured inputs are
  tiled, have packed mip tails, and use 8-in-16 byte order. Sizes include 128x128,
  256x256, 512x256 and 512x512. Linear/all-endian coverage is synthetic; broader
  formats, arrays and live mutation behavior remain unqualified.
- DDS headers, dimensions, mip counts and every compressed payload hash were
  independently checked; Pillow successfully decodes all eight DDS files.
- The target builds and both self-test and all eight source-mutation/truncation
  checks pass. All 51 existing Python checks pass.

Commands from the repository root after entering the release build environment:

```powershell
cmake --build out/build/win-amd64-release --config Release --target pinyon_shift_fh1_texture_import
out/build/win-amd64-release/pinyon_shift_fh1_texture_import.exe --self-test
out/build/win-amd64-release/pinyon_shift_fh1_texture_import.exe .local/native-renderer/bc3-import-fixtures .local/native-renderer/bc3-native-dds-new
```

Fixtures/report: `.local/native-renderer/bc3-import-fixtures/textures.json`.
Final generated assets: `.local/native-renderer/bc3-native-dds-checked`.
Independent DDS validation report: `.local/native-renderer/bc3-import-validation.json`
(validated the identical DDS payloads in `bc3-native-dds-final`). No assets are
committed or installed into the game's runtime asset path.

Production remains the verified fixed-binding DLL
`FE4C91FCBCD536B2DF679A445846AA8C3E8114824580CC3FB55D34C7A9F0D3C9`.
This turn makes no new frame-time or memory claim. Next, integrate native texture
creation and lifetime/invalidation using this qualified format import, while
preserving authoritative CPU/GPU source changes and avoiding duplicate caches.
The full Xenos-retirement goal remains active.

### Layered native textures use fixed resource slots - 2026-09-06

The qualified layered pair now uses **two fixed texture SRVs and one sampler**,
replacing the pixel shader's unbounded arrays and b4 index lookup. The native
root has separate one-entry tables for unsigned t0/space1, signed t1/space1 and
sampler s0, plus the existing geometry root SRV. The signed table reuses the
unused pixel descriptor-index root slot. Existing constant slots stay compatible.
Handles point into the existing heaps: no descriptor copying, texture duplication
or allocator was added. Texture/sampler changes dirty the fixed tables through
existing invalidation. Heap rollover resolves new sampler indices; root switches
invalidate every slot.

The generic descriptor-index upload remains for shared invalidation and guest
fallback, although the native pixel shader no longer reads it. Texture ownership,
decoding, upload and residency still use Xenos TextureCache. This is a smaller
native binding contract, **not full texture ownership or a lower application
binding-tier claim**. A missing native root explicitly enters guest fallback:
the generic unbounded root would otherwise accept this shader but bind unrelated
heap entries. The temporary root-null diagnostic has been removed.

Final staged/artifact DLL SHA-256:
`FE4C91FCBCD536B2DF679A445846AA8C3E8114824580CC3FB55D34C7A9F0D3C9`.
Capture/benchmark candidate SHA-256:
`45206BDB724F12A80BBAA15FCB3E6EDFD89DD38F74C977364BEDD49931F18178`.
Only a comment and indentation changed between them; final production received
a separate gameplay smoke test. The prior B753A086... baseline remains
`.local/native-renderer/geometry-pages-candidate.dll`.

Validation:

- `tools/check-fh1-layered-texture-bindings.py` compiles the actual production
  binding, invalidation and missing-root branches. It covers nonadjacent texture
  indices, unchanged/changed bindings, heap rollover, both root switch directions
  and missing-root fallback. It passes, as do the geometry-cache control-flow
  check, all 51 existing Python checks and the SDK build.
- Capture session **20260906T234205Z-p32492** completes normally at frame 2800
  with two screenshots; the final image was inspected. Capture:
  `.local/native-renderer/fixed-layered-rdc/frame_frame3116.rdc`.
  The geometry checker maps **4,030 draws** and verifies all **356 layered draws /
  214 ranges / 1,193,400 bytes**, with **zero fallback draws and zero geometry
  copies**. Report: `fixed-layered-geometry-parity/geometry-parity.json` under
  `.local/native-renderer`. Reflection confirms two fixed texture views and one
  sampler in the live native pixel shader.
- Cross-capture resource audit matches the complete multiset of **356 geometry /
  texture-view / sampler tuples** between the prior and fixed-root captures,
  with zero unmatched entries. It resolves the original b4 indices through the
  old root tables and compares them with the new one-entry tables. Texture
  content hashes cover every mip at each resource's first observed use; descriptor
  formats, swizzles and sampler state are included. This checks binding/content
  identity for the captured scene, not arbitrary mid-frame texture mutations.
  Report: `.local/native-renderer/layered-texture-inputs.json`; script:
  `.local/native-renderer/compare-layered-texture-inputs.py`.
- Reference replay uses known visible **event 21769** in the original
  `velocity-paired-rdc/frame_frame3069.rdc`. Fixed shader registers are relocated
  to that draw's original heap slots (unsigned t950, signed t0, sampler s7),
  preserving the captured root. The draw changes all eight color/depth samples.
  Replacement matches **167,772,160 bytes exactly**, four color and four depth
  samples. This checks the shader against original bindings, not the new live
  root. Report: `.local/native-renderer/fixed-layered-visible-reference-replay.json`.
  An earlier page-cache event 10961 probe changed no pixels; that equality result
  is not counted as visible pixel qualification.
- Forced-root-failure session **20260906T235314Z-p37612** completes normally with
  two captures. Its log confirms guest fallback AF2C95BF6EF10882, both guest stages
  translated, and native root **false**. Final production session
  **20260906T235554Z-p7344** also completes normally with two captures and native
  root **true**. Both stop at frame 2800. Inspected logs have only the existing
  filesystem ResolvePath device error; excerpt:
  `.local/native-renderer/fixed-layered-final-log-check.txt`.

AppData 2x A/B/B/A, prior page-cache build versus fixed bindings:

| Run | Session | CPU seconds / wall second | Private MiB | Working MiB | Median / p95 ms |
| --- | --- | --- | --- | --- | --- |
| A1 | 20260906T234702Z-p19012 | 3.2860 | 4720.92 | 1882.07 | 17.1765 / 22.557 |
| B1 | 20260906T234752Z-p43424 | 3.2712 | 4695.11 | 1872.69 | 16.6565 / 21.065 |
| B2 | 20260906T234842Z-p49912 | 3.2370 | 4721.33 | 1873.11 | 16.6575 / 21.256 |
| A2 | 20260906T234933Z-p39592 | 3.3349 | 4707.06 | 1867.52 | 17.1980 / 22.257 |

All runs complete normally with two captures. Mean changes: median **-3.09%**,
p95 **-5.56%**, CPU **-1.70%**, private commit **-0.12%**, working set **-0.10%**.
These are measurements for this stationary scene on the 5800X/RTX 4080, not
low-end qualification or a universal speedup. Reports and samples are
`.local/native-renderer/fixed-layered-abba-*`. GPU replays and fault-injection
smoke tests ran outside the performance comparison.

The full Xenos-retirement goal remains active. Native texture production and
ownership, command production and the remaining scene families are still required.

### Geometry allocation padding reduced with shared windows — 2026-09-06

Retained a smaller allocation strategy for the native geometry cache. Nearby
geometry ranges now share a buffer covering their enclosing **64 KiB-aligned
guest window**; crossing ranges cover two or more pages. This reuses the existing
cache, watches, budget and completed-submission eviction policy rather than
adding an allocator. The cap remains 256 entries / 16 MiB, but normal-run live
geometry allocations fall from **16 MiB to 5.0625–5.125 MiB**, about **68% less**.
The capture run retains **4.4375 MiB**. These are geometry resource allocation
counts, not a claim of equivalent application working-set savings.

The geometry SRV points into the window at a 16-byte-aligned offset. Fetch word
190 retains its lowest four bits, preserving the remaining byte offset and fetch
type. Existing fetch-register invalidation tracks changes in that low offset;
switching between owned/shared binding still invalidates the fetch buffer.
The returned GPU address now includes the aligned view offset. Import/watch
ranges cover the entire window, so neighboring writes can conservatively cause
re-imports. The GPU source still comes through SharedMemory residency. Its raw
physical view is precommitted for GPU access in `Memory::Initialize`; no new CPU
data source or save-file operation was introduced.

Final staged and artifact DLL SHA-256:
`B753A0866565061AE29D8982DB110C4E3DF0FC8847C94C3070E8EAD34ABA2BF3`.

Validation:

- Cache control-flow checks pass, including same-window reuse, aligned views,
  crossing windows, CPU/GPU invalidation, failures, budget and fenced eviction.
  The standalone GPU test now deliberately places geometry at byte 20, binds an
  SRV at byte 16 and uses a four-byte fetch offset. It reproduces the final
  capture's **9,600 vertex-output bytes exactly**; poisoning changes **41 bytes**.
  Bounds checks and all 51 existing Python checks pass.
- Session **20260906T231944Z-p48264** completed two captures and exited normally
  at frame 2800. The final screenshot was inspected. No GPU error appeared in
  the inspected session log; the existing filesystem `ResolvePath(\Device)`
  message remains. Capture: `.local/native-renderer/geometry-pages-rdc/frame_frame3122.rdc`.
- The replay checker maps **3,790 draw events** and verifies **all 356 layered
  draws / 214 geometry ranges / 1,193,400 bytes** against their GPU source.
  There are **zero fallback draws and zero geometry copy bytes** in the captured
  frame. It now accounts for both SRV and fetch offsets. Report:
  `.local/native-renderer/geometry-pages-parity/geometry-parity.json`.
- Fixture event **10961** binds an SRV at byte **8,432** of a 64 KiB buffer,
  leaving a 57,104-byte view; only 1,200 bytes belong to this geometry range.
  Export: `.local/native-renderer/geometry-pages-fixture`. Its geometry SHA-256
  remains `59622C2FCA1B2C098FCC536B9987AC86E4D7CBE20135A9AEDA3A3022616A65F5`.
- Comparing with the earlier capture, **169 common address/size pairs** match
  exactly. The other 45 ranges have different addresses; the complete multiset
  of **214 size/content hashes** is identical. See `geometry-pages-cross-capture.json`
  under `.local/native-renderer`. This is geometry evidence, not whole-frame
  pixel equality across independently timed runs.

AppData 2x A/B/B/A compares the preceding D9DDE84F... cache with this build:

| Run | Session | CPU seconds / wall second | Private MiB | Working MiB | Median / p95 ms |
| --- | --- | --- | --- | --- | --- |
| A1 | 20260906T232406Z-p45276 | 3.2123 | 4726.51 | 1877.94 | 16.704 / 21.030 |
| B1 | 20260906T232457Z-p10860 | 3.3257 | 4720.97 | 1879.60 | 16.628 / 21.186 |
| B2 | 20260906T232548Z-p44184 | 3.1863 | 4712.41 | 1875.59 | 16.696 / 21.152 |
| A2 | 20260906T232639Z-p48524 | 3.2529 | 4739.10 | 1872.79 | 17.0855 / 21.641 |

All four runs finish normally with two captures. Mean changes are median
**-1.38%**, p95 **-0.78%**, sampled CPU **+0.72%**, private commit **-0.34%**,
working set **+0.12%**. Frame-time changes remain within run variation; no firm
speedup is claimed. B1 stabilizes at **61 imports / 524,288 hits / 5,373,952
allocation bytes**, B2 at **66 / 524,288 / 5,308,416**, versus 16,777,216 bytes in
both baseline runs. Reports and samples are `.local/native-renderer/geometry-pages-abba-*`.

This reduces native geometry cache overhead without restoring per-draw copies.
Broader changing-scene qualification, native resource production, texture and
render-target ownership, and native command submission still remain. The Xenos
shared-memory import source and its allocation have not been retired.

### Bounded live geometry reuse retained — 2026-09-06

The layered native program now consumes cached owned GPU buffers in production.
`GetFh1OwnedGeometry` imports a qualified address/size range from the current
GPU shared-memory buffer once, then reuses it while its one-shot memory watch
remains armed. CPU invalidation and reported GPU writes clear the watch. It is
armed **before** residency/copy work; a notification during import stays dirty
for the next use. Request failure disarms the watch and retains fallback.

The cache allows at most **256 entries / 16 MiB of resource allocations**, using
`GetResourceAllocationInfo` for the allocation budget. CPU/driver metadata is
additional. Eviction chooses the oldest completed submission; if every candidate
is still in flight, the draw keeps the shared-memory binding. There is no extra
retired-resource queue that could grow beyond this budget. Cache clear/shutdown
wait for the GPU and unregister watches before releasing buffers. Driver resource
release happens outside the global critical region. Native imports retain exact
packed bytes, including GPU-generated data, rather than assuming the CPU view is
authoritative.

Fetch rebasing is integrated into `UpdateBindings`, eliminating the prototype's
second constant-buffer upload and duplicate root writes on every draw. Changing
owned buffers dirties the geometry SRV; changing ownership also invalidates the
fetch constant buffer. Other fetch words, including the pixel stage's texture
metadata, remain intact. Vertex residency is established before importing and
binding geometry. Unqualified/indexed draws and allocation/budget failures use
the existing binding path. This is still restricted to the admitted layered
vertex/pixel pair, not a generic replacement for guest fetch semantics.

Final production, staged DLL and the measured integrated candidate match SHA-256
`D9DDE84F186C5A1E4CDADF0DE46A457476269D02DEAFA60D45E0A46252C0D47A`.

**Validation:**

- `python tools/check-fh1-geometry-cache.py` compiles the actual production cache
  methods and binding branches against fake GPU/one-shot-watch dependencies.
  It checks CPU/GPU invalidation, invalidation during import, allocation/request
  failure, address/size identity, the allocation cap, in-flight eviction refusal,
  completed eviction, cleanup, rebasing, and owned/shared binding transitions.
  It is a control-flow test, not a substitute for real GPU or memory-watch tests.
- The existing 51 Python checks pass; the standalone geometry bounds check passes.
- Final capture session **20260906T225716Z-p48764** completed two render-test
  captures at frame 2800 and exited normally. Its final screenshot was inspected.
  Capture: `.local/native-renderer/owned-cache-integrated-rdc/frame_frame3119.rdc`.
- `tools/check-fh1-owned-geometry-replay.py` verifies **all 356 layered draws** in
  that capture: **214 distinct ranges / 1,193,400 compared bytes**, all matching
  the live GPU shared-memory source exactly. Every used buffer is owned, every
  fetch is rebased correctly, and there are **zero fallback draws / zero geometry
  copy bytes in the captured frame**. Resource names expose the original address
  and size for this audit. Report:
  `.local/native-renderer/owned-cache-integrated-parity-final/geometry-parity.json`.
- Event **10568** uses an owned **1,200-byte resource**, not a 1,200-byte physical
  allocation. Its exported live constants and geometry reproduce all **9,600
  post-VS bytes exactly** in the standalone D3D12 test. Its corrupted-input control
  changes **42 bytes**. Fixture: `.local/native-renderer/owned-cache-integrated-fixture`.
- A temporary diagnostic refused owned geometry on every odd renderer frame,
  forcing repeated owned/shared binding switches. AppData 2x session
  **20260906T230314Z-p28400** completed two captures at frame 2800 and exited
  normally; its final screenshot was inspected. No GPU error appeared in the
  inspected final-production/diagnostic logs; the existing filesystem
  `ResolvePath(\Device)` message remains. The diagnostic was removed, production
  rebuilt, and the staged/artifact hash again matched the measured candidate.

The replay checker runs under `qrenderdoc --python` with
`PINYON_SHIFT_RENDERDOC_CAPTURE` and a new `PINYON_SHIFT_RENDERDOC_EXPORT_DIR`.
The existing fixture exporter accepts event 10568 through
`PINYON_SHIFT_RENDERDOC_EVENT`. Both exporters refuse an existing output directory.
The final capture logs **371 imports / 262,144 cache hits**, within the 16 MiB
budget. The integrated B2 timing run reaches **365 imports / 524,288 hits**.
These counters include warm-up; the captured warm frame itself performs no imports.

**Performance gate:** An initial cache prototype retained duplicate fetch uploads
and root writes, averaging +2.28% median / +6.43% p95 versus baseline. It was
replaced by the integrated binding path above. The final AppData 2x A/B/B/A run
uses the same sampling method as the preceding comparison:

| Run | Session | CPU seconds / wall second | Private MiB | Working MiB | Median / p95 ms |
| --- | --- | --- | --- | --- | --- |
| A1 | 20260906T225232Z-p17040 | 3.6945 | 4745.62 | 1873.55 | 16.650 / 21.492 |
| B1 | 20260906T225323Z-p18472 | 3.5090 | 4726.97 | 1879.04 | 16.856 / 21.701 |
| B2 | 20260906T225414Z-p38848 | 3.2284 | 4728.97 | 1862.30 | 16.781 / 20.996 |
| A2 | 20260906T225505Z-p32328 | 3.2116 | 4713.75 | 1873.53 | 17.092 / 21.222 |

Mean candidate changes: median **-0.31%**, p95 **-0.04%**, sampled CPU **-2.44%**,
private commit **-0.04%**, working set **-0.15%**. All four runs complete normally
with two captures. These differences are within run variation: **no established
speedup or memory saving**. They remove the clear 8–9% per-draw-copy regression
while moving live geometry into owned buffers. Reports/raw samples are under
`.local/native-renderer/owned-cache-integrated-abba-*`; the summary is
`owned-cache-integrated-abba-summary.json` in the same directory.

The 16 MiB GPU cache is still additional to Xenos shared memory. Next work should
reduce allocation overhead, qualify changing scenes/resources, and replace the
import source with native resource production. Native command submission, texture
and render-target ownership, broader rendering parity and lower-end hardware
qualification remain incomplete. Do not equate this cache with full retirement.

### Live owned import qualified, per-draw copying rejected — 2026-09-06

Implemented and ran bounded layered geometry import through the existing GPU
scratch allocator. Immediately before each admitted non-indexed draw it copied
the current GPU shared-memory range into a separate buffer, uploaded rebased
fetch constants, overrode the direct SRV, invalidated both binding slots for the
next draw, and released the scratch resource after recording the draw. This
reused existing ordered reuse/deferred deletion and preserved GPU-generated
source bytes. Allocation or bounds rejection retained the existing binding.
It deliberately imported every draw rather than trusting unproven immutability.

**This implementation is not enabled or retained in production source.** It
passed correctness checks but failed the performance gate below. The restored
artifact and staged DLL exactly match the prior tested production SHA-256
`EDB04EA527914F9A90BFDA0F1B9DA01304809B22F928794C59A807ED9E19D20C`.

Live session **20260906T221828Z-p50844** completed two captures and exited
normally; its final image was inspected. Session **20260906T222009Z-p35700**
captured `.local/native-renderer/owned-live-rdc/frame_frame3095.rdc`. Event
**11392** binds **ResourceId::1919**, a **16 MiB** scratch buffer, instead of
the **512 MiB ResourceId::317** shared-memory buffer. Fetch address is zero,
fetch words `[3, 268436658]`, declared size **1,200 bytes**, draw count **120**.
Its geometry SHA-256 matches the earlier reference exactly:
`59622C2FCA1B2C098FCC536B9987AC86E4D7CBE20135A9AEDA3A3022616A65F5`.
This proves the captured draw consumes the imported buffer, not that the app
has eliminated its shared-memory allocation or all Xenos dependencies.

The standalone test now populates a default-heap GPU source, copies it into a
separate default-heap geometry buffer, transitions it, and runs the native VS.
The fresh live fixture reproduces **9,600 bytes exactly**; its poisoned-input
control changes **42 bytes**. The earlier fixture still passed with its original
40-byte negative control before the live fixture was selected. Bounds checks
and the 51 Python checks pass. The source buffer also exercises combined
copy-source/index/shader read states. Such combinations are permitted by the
[D3D12 read-state rules](https://learn.microsoft.com/en-us/windows/win32/direct3d12/using-resource-barriers-to-synchronize-resource-states-in-direct3d-12).

`tools/export-fh1-layered-geometry.py` now accepts optional
`PINYON_SHIFT_RENDERDOC_EVENT` (default 21769) and respects the SRV byte offset.
For this capture use event **11392**; the checked fixture is
`.local/native-renderer/owned-live-fixture-final`. It still checks the exact
shader pair, non-indexed 120-vertex draw, constant sizes and geometry bounds.

Two AppData 2x A/B/B/A comparisons used the same saved stationary scene, process
samples at elapsed 34–46 seconds and the final 900 nonzero frame-time rows.
Each run completed at frame 2800 with two captures and normal exit. Hardware
remains Ryzen 5800X / RTX 4080. These are narrow samples, not broad qualification.

| Import version | A1 median / p95 ms | B1 | B2 | A2 | Mean median change |
| --- | --- | --- | --- | --- | --- |
| Separate copy/read states | 16.653 / 20.983 | 18.491 / 22.916 | 18.1505 / 23.660 | 17.0485 / 21.620 | **+8.72%** |
| Combined copy/read states | 17.184 / 21.791 | 18.571 / 22.677 | 18.957 / 23.702 | 17.1035 / 22.162 | **+9.45%** |

Combining compatible shared-buffer read states removed unnecessary source
transitions but did not rescue per-draw copying. P95 increased **9.33%** and
**5.52%**, respectively. Working set increased about **0.89% / 0.85%**, private
commit **0.40% / 0.60%**. Lower sampled CPU use does not offset the frame-time
regression. Both production changes were reverted, including the combined-read
helper change. Reports with session IDs and raw samples are
`.local/native-renderer/owned-live-abba-summary.json` and
`.local/native-renderer/owned-combined-abba-summary.json`.

The captured command stream has **356** imports for the **356** layered draws,
from **214 distinct source address/size pairs**: **1,193,400 copied bytes** versus
**714,840 unique bytes** per frame. Separate 64 KiB-rounded allocations for
those ranges would total **14,024,704 bytes** before other costs. This is evidence
for bounded reuse, not proof of cross-frame immutability. See
`.local/native-renderer/owned-copy-summary.json`. The pipeline map reports no
missing events or unsupported command-state operations and its sampled PSOs
match replay state.

Resume with a bounded owned-buffer cache that uses mutation notifications and
GPU-ordered lifetimes, then repeat parity and performance qualification. Do not
re-enable per-draw copies as an optimization. SharedMemory watches are one-shot
and run under the global critical region; register before import, retain dirty
notifications arriving during import, and unwatch before eviction/shutdown.
CPU direct writes and GPU write provenance still need matching the authoritative
shared-memory update contract. Retained local diagnostic sources are
`owned-live-command.cpp`, `owned-live-geometry.h`, and `owned-combined-read.h`
under `.local/native-renderer`; their command source additionally needs the
`fh1_layered_owned_geometry_draws_` counter member if restored for diagnostics.
Diagnostic DLLs are `owned-live-candidate.dll` (54B59C61...) and
`owned-combined-candidate.dll` (B43DC5CD...). Neither is staged for normal use.

### Live layered root uses a direct geometry SRV — 2026-09-06

The admitted layered native pipeline now uses a separate root signature whose
shared-memory descriptor-table slot is a vertex root SRV. Other binding slots
stay compatible with existing constant and texture uploads. Root creation is
optional; the regular root remains usable if creation fails. The resource bound
to this direct SRV is **still the shared-memory buffer**, not an owned geometry
allocation. This removes a binding dependency, not the remaining resource owner.

All four pipeline creation paths now publish the root signature actually used
before publishing the PSO. Native PSO failure restores both guest shader stages
and the original guest root signature. A temporary forced-failure build verified
that rollback in gameplay; the diagnostic was removed and production rebuilt.

The standalone geometry test now qualifies addressed bounds before rebasing.
It conservatively checks physical extent, draw count, index transformation and
wrap, clamp range, finite nonnegative scale, and read-only/non-indexed admission.
Its `--self-test` exercises rejected inputs and checks individual vertex loads
across accepted small ranges. This qualification is not yet a live importer.
Bounds checks passed, normal GPU output remains **9,600 bytes exact**, and the
poisoned-input control changes **40 bytes**. The existing 51 Python checks pass.

AppData 2x runs both captured twice, completed at frame 2800 and exited normally:

- Production: **20260906T220845Z-p37916**, output
  `.local/native-renderer/layered-root-2x`; direct geometry SRV logged true.
- Forced fallback: **20260906T221020Z-p27856**, output
  `.local/native-renderer/layered-root-fallback-2x`; direct geometry SRV logged false.

Both final captures were visually inspected: the scene and HUD render normally.
Independent runs have different traffic/animation states; this is not an exact
pixel comparison. No GPU error appeared in the inspected session logs; the
existing filesystem `ResolvePath(\Device)` message remains. Final production
artifact and staged DLL match the normally tested DLL, SHA-256
`EDB04EA527914F9A90BFDA0F1B9DA01304809B22F928794C59A807ED9E19D20C`.

No speedup or lower hardware requirement is established by this change. Next
ownership work must supply an owned geometry GPU address and rebased constants,
preserve mutation visibility and fence lifetime, and retain fallback for inputs
outside proven bounds. Native command/resource ownership, broader scene parity
and lower-end hardware qualification still block full Xenos retirement.

### Layered native geometry contract is now SRV-only — 2026-09-06

Removed the RW shared-memory declaration and conditional UAV loads from
`fh1_layered_scene.vs.hlsl`. The exact admitted layered vertex/pixel pair has
no memexport; `IssueDraw` derives shared-memory UAV mode from those stages'
memexport masks and passes it to `UpdateSystemConstantValues`. This change is
restricted to that native program, not a change to generic guest shader rules.
Regenerated its bytecode: no UAV resource declaration remains, and compiler
instruction slots decrease from **532 to 487**. No frame-rate gain is claimed
from an instruction count.

The standalone owned-geometry test now creates only three CBV root parameters
and one SRV, with no dummy UAV resource or binding. It still reproduces all
**9,600 bytes** exactly; the corrupted-input control still changes **40 bytes**.
This also verifies that the production bytecode can create a PSO under the
smaller resource contract. Updated the local shader generator and checked that
it reproduces the production HLSL exactly. The 51 Python checks pass.

AppData 2x session **20260906T215817Z-p39236**, output
`.local/native-renderer/srv-only-layered-2x`, prewarms all **458** pipelines,
admits the layered native PSO, captures twice, and exits normally. The final
screenshot was inspected. The usual filesystem `ResolvePath(\Device)` message
remains; no GPU error appeared in the inspected session log. Staged and artifact
DLLs match SHA-256
`AF497D49DD81A3C92FBBC8AA667CF27F29F1F23347A905FE2EA3881C83E1E824`.

Live geometry still uses the existing shared-memory resource. The live owned
path needs a separate root/PSO resource contract, bounded vertex-fetch admission,
invalidation and GPU lifetime handling, and a retained fallback. In particular,
the guest vertex program does not bound loads to the fetch descriptor's size;
an owned buffer must prove its addressed extent before replacing that broader
resource. No unvalidated geometry cache was enabled by this change.

### Standalone owned geometry reproduces the layered vertex stage

Added `pinyon_shift_fh1_owned_geometry_tests`, an explicit Windows D3D12 test
target with **no ReXGlue/runtime library link**. It uploads the layered draw's
1,200 geometry bytes into its own buffer (1,280-byte resource after alignment),
uploads 480/400/768-byte system/float/fetch constant payloads, rebases the vertex
fetch to zero and runs the existing native layered vertex shader through stream
output. It creates no descriptor heaps or unbounded descriptor ranges and does
not instantiate the Xenos command processor or 512 MiB shared-memory resource.
Windows/D3D12 allocation granularity still applies; this is not a measured
1,200-byte physical-memory allocation or an application memory-saving claim.

At captured event **21769**, all **120** vertex invocations reproduce all
**9,600** post-VS bytes exactly, SHA-256
`3F3D882715BCFBFF00CD4752B4AEB407988FFCFC2B1D91E2875B9AF9281E25B6`.
A deliberately changed geometry byte changes **40** output bytes, so the
comparison detects an incorrect imported resource. Both positive and negative
controls passed on the RTX 4080. The test checks output byte count, device
removal and D3D12 error messages when the debug layer is available. Its import
table contains D3D12/DXGI/Windows/CRT DLLs, with no renderer DLL.

`tools/export-fh1-layered-geometry.py` exports this fixture from the qualified
capture, checks the exact shader pair/draw parameters and bounds, and refuses
an existing output directory. It reads only the constant payload sizes needed
by the native shader; root-CBV descriptor sizes otherwise include the remainder
of the upload allocation and are not meaningful constant block lengths.
The canonical exported fixture is
`.local/native-renderer/layered-owned-geometry-fixture`; original packed vertex
bytes hash to
`59622C2FCA1B2C098FCC536B9987AC86E4D7CBE20135A9AEDA3A3022616A65F5`.

Reproduce after entering the build environment:

```powershell
cmake --build out/build/win-amd64-release --config Release --target pinyon_shift_fh1_owned_geometry_tests
$env:PINYON_SHIFT_RENDERDOC_CAPTURE = '<qualified frame_frame3069.rdc>'
$env:PINYON_SHIFT_RENDERDOC_EXPORT_DIR = '<new output directory>'
qrenderdoc --python tools/export-fh1-layered-geometry.py
out/build/win-amd64-release/pinyon_shift_fh1_owned_geometry_tests.exe '<output directory>'
out/build/win-amd64-release/pinyon_shift_fh1_owned_geometry_tests.exe '<output directory>' --poison
```

This establishes that the vertex stage can consume an owned geometry resource
and captured live constants without Xenos execution. It does **not** yet move
live gameplay geometry into that ownership model, establish mutation/lifetime
tracking, reproduce pixel resources in the standalone test, or qualify lower-end
hardware. Those remain necessary integration work. The 51 existing Python
checks pass; production gameplay DLL remains unchanged at
`7DB4650FCF188382FF984B0E3C8607C80E3AC8DB3F37ABA09D52D17CE355A7D3`.

### Command/input lifetime audit for native ownership

Extended `tools/analyze-fh1-scene-bindings.py` to report input variation by
command-buffer address, length, draw offset and shader pair. A stable command
hash is not a frozen native draw record. The existing 980-record live capture
contains 974 hashed records in **20** such groups over **11** small buffers.
Every group has one observed command hash, texture-descriptor state,
vertex-descriptor state and index base, but **all 20 have multiple constant
states**, with up to **126**. Six oversized/unhashed records remain explicitly
unclassified, rather than treating a zero hash as immutable content. Resource
bytes and mutation between samples are not proved by descriptor equality.
The self-test covers changing constants under an unchanged command hash,
missing hashes and distinct draw offsets. It passes, as does analysis of the
saved runtime log. Output: `.local/native-renderer/scene-native-input-analysis.json`.

Native command submission must retain per-invocation constants/external loads
and ordered register side effects even when command templates can be reused.
This rules out replacing these buffers with frozen draw records. Existing
physical-memory invalidation callbacks can track guest-view writes and explicit
host invalidations, but direct host physical accesses do not themselves trigger
the callbacks (`rex/system/xmemory.h`). A future resource cache must account for
that boundary; sampled stable hashes alone cannot authorize lifetime reuse.

The historical `RESOURCE_WORKER.md` metadata-worker milestone is not a current
upload implementation: current `guest_output_renderer.cpp` only connects the
render-test output observer. Added that status to the historical document.
The native velocity pass also still obtains its source through the texture
cache/global bindless heap; although an existing per-draw descriptor path can
bind one texture, production shader packs are keyed by bindless configuration.
Changing only the pass would not establish a working lower-tier renderer.
No speculative binding branch, duplicate worker, or runtime behavior change was
introduced by this audit. The staged production DLL remains
`7DB4650FCF188382FF984B0E3C8607C80E3AC8DB3F37ABA09D52D17CE355A7D3`.

### Third native scene family: layered geometry — 03:01 UTC

Added direct vertex program `fh1_layered_scene.vs.hlsl` for
`3BC346726C1C2535`, paired with the existing `fh1_layered_lit.ps.hlsl`
(`9584B309533EF6C9`). Admission is restricted to pipeline description
`AF2C95BF6EF10882`, bindless resources and host render targets. The existing
native scene binding, prewarm and failure paths are reused. The vertex program
decodes the observed 40-byte packed declaration and evaluates its straight-line
arithmetic using 25 compact constants. Guest command/resource ownership remains.

The shared pixel binary deliberately remains loaded: other vertex families
still use `9584B309533EF6C9`. Deferring it initially reduced prewarm from 458 to
456; retaining it restores all **458**. The new native PSO uses both native
stages, with guest VS untranslated and guest PS already translated for those
other families. This is not full retirement of that shared pixel shader.

Evidence from the existing paired capture `frame_frame3069.rdc`, event
**21769**, pipeline resource **1042**, VS **1044**, PS **1046**:

- Pixel-only replacement: all four color samples match, **83,886,080 bytes**.
- Combined vertex/pixel replacement: all four color and depth samples match,
  **83,886,080 bytes each**. Post-VS output matches all **9,600 bytes**, SHA-256
  `3F3D882715BCFBFF00CD4752B4AEB407988FFCFC2B1D91E2875B9AF9281E25B6`.
- The selected draw changes 170,921 color bytes and 113,298 depth bytes in
  sample zero. Collapsed-vertex control changes the same counts; magenta-pixel
  control changes 171,226 color bytes. These are visible-draw comparisons.
- Reports/scripts: `.local/native-renderer/layered-pixel-replay`,
  `layered-stages-replay`, `layered-stages-depth-replay`, matching `test-*.py`,
  and `write-layered-scene-vertex.py`. Replacement affects prior uses of each
  shader in this replay; these tests are not an all-scene parity qualification.

A structured-API pipeline map covers all **3,786** capture draws without a
missing event or unknown pipeline. All **17** sampled reconstructed PSOs match
replayed pipeline state; no unsupported bundle/indirect/clear-state event was
encountered. The layered pair accounts for **356** draws, the busiest remaining
pair; the previously migrated pairs account for 254 and 245. This avoids the
earlier every-tenth-draw selection aliasing. Artifacts:
`.local/native-renderer/map-draw-pipelines.py` and `draw-pipeline-map.json`.

AppData 2x runs `20260905T025716Z-p38904` (initial),
`20260905T025833Z-p40824` (shared-PS correction), and
`20260905T025943Z-p37508` (forced failure of only the new native PSO) each exit
normally with two captures. Forced failure logs the exact new pipeline falling
back with both guest stages translated; earlier native scene pairs remain
native. Initial final screenshot inspected. All **51** Python checks pass.
The diagnostic `layered-scene-forced-fallback.dll` must never be staged for use.
Production DLL SHA-256:
`7DB4650FCF188382FF984B0E3C8607C80E3AC8DB3F37ABA09D52D17CE355A7D3`.

Four ABBA runs against the preceding mapped-pack build (same AppData 2x save):

| Run / session | CPU sec/wall sec | Private MiB | Working MiB | Median frame ms | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 / 20260905T030051Z-p42968 | 3.6082 | 4741.6 | 1835.5 | 17.199 | 21.971 |
| B1 / 20260905T030142Z-p14312 | 3.2026 | 4715.4 | 1844.6 | 17.037 | 21.303 |
| B2 / 20260905T030233Z-p12840 | 3.4480 | 4715.2 | 1855.0 | 17.026 | 21.591 |
| A2 / 20260905T030324Z-p46032 | 3.2915 | 4755.0 | 1870.1 | 17.062 | 21.565 |

Mean private memory is **33.0 MiB lower / -0.69%** in this experiment; working
set changes **-0.16%**. CPU **-3.61%**, median frame **-0.58%**, p95 **-1.47%**
do not establish a speedup given the variation between runs. Process samples
use elapsed seconds 34–46; frame metrics use the last 900 nonzero CSV rows,
not exactly the same interval. No concurrent build or RenderDoc replay ran
during these measurements. All four runs captured twice and exited normally;
B2's final screenshot was inspected. Across all seven live runs there are no
GPU error log entries; the existing `ResolvePath(\Device)` message remains.
Evidence: `layered-scene-abba.ps1`, `summarize-layered-scene-abba.py`,
`layered-scene-abba-summary.json`, `layered-scene-runs-errors.json` and the four
run directories under `.local/native-renderer`. The staged and artifact DLLs
both match the production hash above, and no game process remains running.

### Retired stale alpha-mask contract; loader regression wired into suite — 02:44 UTC

Removed the source-string test that required the rejected broad binary-alpha
path and explicitly prohibited an attachment guard. That path was deliberately
removed during the resume audit; restoring it to satisfy the test would undo
the retirement work. Replaced the test with an invocation of the compiled
`pinyon_shift_fh1_shader_pack_tests` using a temporary generated pack, exercising
the actual mapped loader, lifetime and integrity checks from the preceding
change. It runs when the Windows test executable has been built; otherwise
the portable Python suite reports an explicit skip. Build that target before
claiming runtime-loader validation. The current run executed it without skips.

All **51** shader-pack/renderer/release/render-test Python checks now pass.
Updated the dependency ledger's stale claim that Xenos executes every draw:
qualified native replacements exist, while render-target suppression remains
unqualified and guest command/resource ownership remains. This does not relax
the dependency gate or claim renderer retirement. No runtime code or staged
DLL changed this continuation; the mapped-pack SHA-256 remains
`3A7D809B06B71334393F87B45D5FB57D116901E08876C7AB61D5233EBBCA7BB2`.

### Read-only shader-pack mapping saves ~463 MiB private memory — 02:42 UTC

`Fh1ShaderPack` now owns the existing `rex::memory::MappedMemory` read-only
mapping and exposes bytecode spans into it. This removes the full-file read
buffer and one private bytecode allocation per pack entry. Metadata is still
decoded into owned structures, all existing range/content/bytecode hash checks
remain, and active guest translations still copy their selected bytecode.
`Clear` and reload invalidate entries before releasing the mapping. The Windows
mapping holds a read-only handle denying concurrent writes to the pack.

The installed 2x pack is 473,489,272 bytes (~452 MiB). Four clean ABBA AppData
runs compared the preceding production build against the mapped build:

| Run / session | CPU sec/wall sec | Private MiB | Working MiB | Median frame ms | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 / 20260905T023813Z-p28032 | 3.2534 | 5170.8 | 1839.6 | 17.132 | 21.576 |
| B1 / 20260905T023904Z-p43976 | 3.1789 | 4718.1 | 1847.3 | 16.738 | 20.646 |
| B2 / 20260905T023954Z-p21488 | 3.3203 | 4705.7 | 1845.2 | 17.098 | 21.989 |
| A2 / 20260905T024044Z-p38804 | 3.2210 | 5178.7 | 1852.0 | 17.178 | 22.356 |

Mean private memory falls **462.9 MiB / 8.94%**, repeated in both B runs.
Working set is effectively unchanged (**+0.02%**), so this is a private-commit
reduction, not evidence of 463 MiB less resident physical RAM. CPU **+0.38%**,
median frame **-1.38%**, p95 **-2.95%** remain within this experiment's variation;
no speedup claim. CPU/memory samples cover elapsed seconds 34–46; frame metrics
use the last 900 nonzero CSV rows, not exactly the same interval.
All four runs captured twice and exited normally without GPU errors. B2's
final screenshot was inspected; the usual filesystem message remains. Evidence:
`.local/native-renderer/mapped-shader-pack-abba-summary.json`, four matching
run directories, benchmark/summary scripts and `mapped-shader-pack-abba-errors.json`.

Built the DLL and `pinyon_shift_fh1_shader_pack_tests`. The C++ test now enables
assertions in Release (previously its assert-wrapped calls could be compiled
out), verifies byte contents and `MEM_MAPPED` / `PAGE_READONLY`, exercises
clear/reload and write-handle release, and rejects damaged content. It passed
with `.local/native-renderer/mapped-pack-fixture.pnsp`.
The broader Python run passed **50 of 51** tests; the one pre-existing failure
is `test_binary_alpha_mask_covers_identical_fh1_vertex_variants`, which expects
a removed legacy alpha-mask path. Its expected shader hashes are absent from
the pre-change pipeline snapshot too. It was not changed to hide the failure.
The standard 40 renderer/release/render-test checks are among those passing.

Built/staged DLL SHA-256:
`3A7D809B06B71334393F87B45D5FB57D116901E08876C7AB61D5233EBBCA7BB2`.
Rollback: `.local/native-renderer/before-mapped-shader-pack.cpp`, `.h`, `.dll`.
No saves were copied or reset. This is a measured memory-budget improvement;
low-memory hardware qualification and full Xenos retirement remain incomplete.

### Native scene startup prewarm; migration performance remains mixed — 02:34 UTC

Measured the accumulated scene migration (native binding setup, cache-hit setup
removal and second native shader pair) against the sampler-cache-fixed build
before these changes. Four clean ABBA 2x AppData runs, no concurrent build:

| Run / session | CPU sec/wall sec | Private MiB | Median frame ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| A1 / 20260905T022857Z-p49880 | 3.4243 | 5141.0 | 19.486 | 24.565 |
| B1 / 20260905T022948Z-p28828 | 3.3823 | 5165.7 | 17.102 | 22.719 |
| B2 / 20260905T023039Z-p34168 | 3.1887 | 5179.4 | 17.119 | 21.698 |
| A2 / 20260905T023130Z-p38856 | 3.2304 | 5156.4 | 16.529 | 20.550 |

Pair-mean changes: CPU **-1.26%**, private memory **+0.46%** (~24 MiB),
working set **+1.32%**, median frame **-4.98%**, p95 **-1.55%**. Baseline
variation and traffic/scheduling prevent a firm speedup claim. CPU/memory use
elapsed seconds 34–46; frame summaries use the last 900 nonzero CSV rows and
are not exactly aligned to that interval. Lower hardware requirements are
**not demonstrated** by this comparison. All runs captured twice and exited
normally without GPU errors; known filesystem messages remain. Evidence:
`.local/native-renderer/scene-migration-abba-summary.json`, corresponding
benchmark/summary scripts, four run directories and `scene-migration-abba-errors.json`.

The startup prewarmer was still rejecting native scene PSOs because their
guest stages were untranslated. Updated that existing loop to create the
translation identity objects and native bindings for qualified scene states,
then prewarm the native PSOs through its normal creation queue. Guest bytecode
is not loaded. Other states retain the existing validity checks. This moves
native PSO creation away from the first scene draw without adding a new cache.

After the benchmark, release build, sampler-layout regression and 40 tests
passed. AppData session **20260905T023256Z-p45828**, output
`.local/native-renderer/native-scene-prewarm-2x`, created all three native scene
PSOs before startup prewarm completion, each reporting both guest stages
untranslated. Variant count stays **521**; prewarmed pipeline count becomes
**458** (455 previous pipelines plus three native scene PSOs). Both captures,
normal exit and final image inspection passed; no GPU errors. The prewarm
change itself has not had a timing comparison.

Built/staged DLL SHA-256:
`25BA862764671A401E814C4C9F3FA74C1A11E38ED45AF14A3FB2C90A8B69519F`.
Rollback: `.local/native-renderer/before-native-scene-prewarm.cpp` / `.dll`.
No saves were copied or reset. Full native command/resource ownership, broad
parity, hardware qualification and Xenos retirement remain incomplete.

### Second scene family's lazy fallback independently verified — 02:27 UTC

Forced only the native **AD2C355A6BE1EE87 / 2F2137BF953DA7AF** pipeline's
initial creation to return `E_FAIL` in a temporary diagnostic build. AppData
session **20260905T022631Z-p50620**, output
`.local/native-renderer/lit-scene-fallback-2x`, then created guest fallback
pipeline **B673641288F80E60** with both guest stages translated. Both earlier
blended native pipelines still reported untranslated guest stages. This
independently exercises the new family's pack-binding compatibility and lazy
bytecode load, rather than relying only on the earlier family's test.

Both captures and normal frame-2800 exit passed without GPU errors; only the
known filesystem message remains. Evidence: the output's `validation.json`,
session log and captures. No saves were copied or reset. The diagnostic DLL is
`.local/native-renderer/lit-scene-forced-fallback.dll` and must not be shipped.
Production source was restored and rebuilt, and staged/artifact DLL hashes
both remain **AC3DDB0284EE71805D914135C5797CBDA41A99CE876DCCFD9456B367031392ED**.
Full renderer retirement, broad visual parity and hardware qualification remain
incomplete; this continuation closes the independent fallback-check gap only.

### Second native scene pair validated and staged — 02:25 UTC

Added direct `fh1_lit_scene.vs.hlsl` / `.ps.hlsl` and fxc bytecode for
**AD2C355A6BE1EE87 / 2F2137BF953DA7AF**. The vertex format is 20 bytes:
float3 position, signed normalized packed 10-bit normal and two UNORM16 UVs.
The shaders preserve parallel scalar/vector instruction inputs, fixed constant
maps, guest texture sign/gradient behavior and the corrected alpha coverage.
Static native instruction slots are 323 VS / 324 PS, not a speed measurement.

Visible captured event **20171**, pipeline `ResourceId::1566`, in
`velocity-paired-rdc/frame_frame3069.rdc` qualifies this pair. Native vertex
output matches **3,840 bytes** exactly. VS-only and combined VS/PS replacements
both match all **83,886,080 color bytes** and **83,886,080 depth/stencil bytes**
across four samples. The original draw changes 7,406 color bytes and 4,712
depth bytes in sample zero; collapsing the replacement vertex positions changes
those same counts. An initial every-tenth-draw search missed this visible draw;
the scripts now select event 20171 directly rather than treating sampling as
proof of inactivity.

Evidence under `.local/native-renderer/`: `lit-vertex-replay`,
`lit-vertex-depth-replay`, `lit-stages-replay`, `lit-stages-depth-replay`, each
with `report.json`, plus `lit-vertex-replay/vertex-comparison.json`. Matching
`test-lit-*-replay.py` scripts reproduce the checks; local
`write-lit-scene-vertex.py` / `write-lit-scene-pixel.py` produce the straight-line
candidates. This is captured-state parity, not broad scene/adapter coverage.

Reused the native binding path for the second pair: its pack binding metadata
also has no VS textures and one fetch-0 PS sampler with signed/unsigned views
at descriptor indices 2/3. Admission adds only observed pipeline-description
hash **B673641288F80E60** with the exact new shader pair. The shared helpers are
now named `IsFh1NativeScenePipeline` / `PrepareFh1SceneBindings`; existing
blended-state guards and lazy guest fallback remain. Other states still use
guest shaders. Startup defers these two shader hashes too.

Release build, sampler-layout executable regression and 40 existing tests
passed. AppData session **20260905T022410Z-p37392**, output
`.local/native-renderer/lit-scene-2x`, created all three admitted native scene
PSOs with **guest VS translated false, PS translated false**. Startup loads
**521** variants (previously 524) and prewarms **455** pipelines (previously
457). Two captures and normal frame-2800 exit passed, no GPU errors, final image
inspected; only the known filesystem message remains. No saves were copied or
reset. `validation.json` records the live evidence.

Built/staged DLL SHA-256:
`AC3DDB0284EE71805D914135C5797CBDA41A99CE876DCCFD9456B367031392ED`.
Rollback is `.local/native-renderer/before-lit-scene.dll` with matching `.cpp`
and `.h` snapshots. The new family has not had an independent forced-failure
run; it reuses the previously exercised lazy fallback path, with matching
pack bindings verified. Broader parity, native command/resource ownership,
hardware qualification and full Xenos retirement remain unfinished.

### Skip repeated setup on pipeline cache hits — 02:15 UTC

Moved root-signature lookup and geometry-shader lookup in `ConfigurePipeline`
after the existing current-pipeline and hashed-cache checks. Cached pipelines
already retain those objects, including the atomically published root signature
for queued creation. Native blended binding validation/setup now also runs only
on a pipeline cache miss. Shader/state admission and guest fallback remain
unchanged; no new cache or lifetime-tracking mechanism was added.

Release build, executable sampler-layout regression and 40 existing tests
passed. AppData 2x run **20260905T021359Z-p39812**, output
`.local/native-renderer/pipeline-setup-cache-2x`, completed both captures and
normal exit. Both native scene pipeline creations still report untranslated
guest VS/PS. No GPU errors; the known filesystem message remains. Final image
was inspected. Evidence: the output directory's `validation.json` and PNG/PPM.
This proves the smoke check, not a measured frame-time gain or broad parity.

Built/staged DLL SHA-256:
`07710010A35204CE39C3C04DCB30656BA6EDF5725240993CEA8019066A56CDB8`.
Previous source/DLL: `.local/native-renderer/before-pipeline-setup-cache.cpp`
and `.dll`. No save was copied or reset. Native command/resource ownership,
remaining shader families and full Xenos retirement are still incomplete.

### Blended scene pair no longer loads guest stage bytecode — 02:12 UTC

Separated shared binding-layout UID setup from shader translation and reused
it for the qualified native scene pair. Native VS bindings are empty; native
PS bindings are fetch 0, unsigned/signed 2D views at descriptor indices 2/3,
and fetch-controlled sampler index 1. These match the existing pack metadata
for this shader, including its other stored modifications, without loading
that metadata from the pack on the admitted native path.

`ConfigurePipeline` now checks the same two qualified description hashes
before loading translated stages, installs those native bindings and reuses
the validated description. `CreateD3D12Pipeline` permits untranslated stages
only under the shared native admission check. Startup defers both shader
hashes; unqualified states still load their original variants on demand.
Native PSO creation failure also loads both guest stages lazily before retry.
The exact two-state admission scope has not expanded.

Live proof: final session **20260905T021109Z-p23780**, output
`.local/native-renderer/native-blended-bindings-final-2x`, logs both native
pipeline creations with **guest VS translated false, PS translated false**.
Startup loads **524** variants instead of 527, and prewarms **457** pipelines
instead of 460. Both 2560x1440 captures completed, frame 2800 exited normally,
no GPU errors, and the final screenshot was inspected. Initial native run
`20260905T020826Z-p46352` passed too. Evidence is `validation.json` in each
output directory; the known filesystem message remains.

Forced-failure validation: a temporary diagnostic build returns `E_FAIL`
instead of attempting the first native blended PSO creation. Session
**20260905T020954Z-p24668**, output
`.local/native-renderer/native-blended-bindings-fallback-2x`, confirms both
guest fallback PSOs with **VS translated true, PS translated true**. Both
captures and normal exit passed without GPU errors. The diagnostic is stored
only at `.local/native-renderer/native-blended-bindings-forced-fallback.dll`;
its failure injection was removed before rebuilding/staging production.

Release build, 40 renderer/release/render-test unit tests and the executable
sampler-layout regression passed. Final production DLL SHA-256:
`817971ABB8599C906ADC1C0EEBB1D1B8BC436FAFD4379DFF1B39BDF4156282F3`.
Rollback before this continuation is `before-native-blended-bindings.dll`
under `.local/native-renderer/`. No saves were copied or reset.

This removes the admitted scene pair's dependency on loaded translated
bytecode, not the shader pack as a whole: guest fallback bytes remain in it.
Analysis-catalog metadata, guest command parsing, shared constant/resource
binding work, texture/geometry residency and render-target ownership remain.
Earlier same-capture shader parity still applies to unchanged shader bytecode;
these runtime smoke checks do not establish broad visual parity or a measured
performance gain. Full Xenos retirement and lower hardware qualification remain
active work.

### Fix shared sampler-layout interning; preliminary ABBA measurements — 02:06 UTC

Tracing the scene-stage bytecode dependency found a shared binding-cache bug
in `PipelineCache::TranslateAnalyzedShader`. Bindless sampler layouts were
looked up using the empty layout UID rather than their descriptor-layout hash.
New entries also returned `map.size()` while storing `map.size()+1` as their UID.
The three-line fix uses the hash for lookup and consistently returns/stores
the same nonzero UID. Identical layouts can now reuse descriptor-index buffers
across shaders; different layouts still invalidate bindings. Both vertex and
pixel consumers in `D3D12CommandProcessor::UpdateBindings` use this shared path.

Runnable regression: `python tools/check-fh1-sampler-layout.py` inside the
release build environment. It compiles the actual production interning block
and verifies empty/nonzero IDs, repeated layout reuse, and distinct layouts
with colliding hashes or different lengths. Passed, as did the 40 existing
renderer/release/render-test unit tests and the `rexgpu-fh1` release build.

Four fresh 2x AppData gameplay runs compared native paired shaders before
(A) and after (B) this cache fix, with no concurrent build. Each produced both
captures and exited normally; no GPU errors, only the known filesystem
`ResolvePath(\\Device)` message. The B2 final image was inspected.

| Run / session | CPU sec/wall sec | Private MiB | Median frame ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| A1 / 20260905T020217Z-p34004 | 3.4934 | 5156.0 | 20.141 | 27.074 |
| B1 / 20260905T020308Z-p48704 | 3.4005 | 5127.0 | 17.681 | 23.343 |
| B2 / 20260905T020400Z-p43860 | 3.3173 | 5142.9 | 17.477 | 22.107 |
| A2 / 20260905T020451Z-p33332 | 3.4823 | 5158.8 | 17.257 | 24.160 |

Pair-mean changes: CPU **-3.70%**, private memory **-0.44%** (22.5 MiB),
working set **+0.02%**, median frame time **-5.99%**, p95 **-11.29%**.
CPU/memory samples cover elapsed seconds 34–46; frame summaries use the last
900 nonzero CSV frame-time rows, not an exactly aligned scene interval.
Moving traffic, scheduling and the substantial A1/A2 frame-time spread limit
causal confidence. This is preliminary single-machine evidence, not revised
hardware requirements. Keep the fix for its verified cache correctness.

Evidence: `.local/native-renderer/sampler-layout-abba-summary.json`,
`sampler-layout-abba-runtime-errors.json`, four `sampler-layout-abba-*` output
directories and the matching benchmark/summary scripts. Earlier
`blended-stages-abba-*` runs overlapped compilation; do not use them as a shader
performance claim. No save was copied or reset.

Built/staged DLL SHA-256:
`2F261CF1CDC1E51B58ADA040432F2927E03BB625A576814C5443D58934E9C5AD`.
The pre-fix paired-stage DLL is `.local/native-renderer/native-blended-stages-candidate.dll`.

Remaining scene migration dependency: `ConfigurePipeline` insists on guest
translations before creating the state, and `TranslateAnalyzedShader` loads
binding layouts together with guest bytecode. `CreateD3D12Pipeline` rejects
untranslated stages before substituting native bytecode. Native scene stages
must obtain their bindings independently and bypass those checks only for
qualified native states; globally replacing a shader by hash would also affect
unqualified pairings/states. Full Xenos retirement remains unfinished.

### Native blended scene vertex/pixel pair validated and staged — 01:57 UTC

Added `fh1_blended_scene.vs.hlsl` and its fxc `vs_5_1` bytecode for guest
vertex program `8D8A197476841A9A`. This is fixed straight-line arithmetic,
including guest endian/index handling, vertex fetch and viewport conversion.
The existing two-description blended-lit gate now selects both native stages;
PSO creation failure restores both guest stages. Guest translation metadata,
bindings, resource ownership and command processing are still required.

At captured event 20164, native vertex output matches all **58,624 bytes** of
guest post-VS output. Combined native VS/PS output matches **83,886,080 color
bytes** and **83,886,080 depth/stencil bytes**, covering all four samples of
both attachments. A collapsed-position vertex negative control changes
254,747 color bytes and 172,882 depth bytes in sample zero. These checks cover
the captured visible state, not all scenes or the second PSO independently.
Native VS static instruction slots are 359 versus guest 607; this is not a
GPU performance measurement.

Reproduction/evidence under `.local/native-renderer/`:
`test-blended-vertex-replay.py`, `test-blended-stages-replay.py`,
`test-blended-stages-depth-replay.py`, and matching replay directories containing
`report.json`; `blended-vertex-replay/vertex-comparison.json` records post-VS
parity. Capture remains `velocity-paired-rdc/frame_frame3069.rdc`.

Release DLL build succeeded; 40 renderer/release/render-test unit tests passed.
Staged DLL SHA-256:
`88D499CB34A959829612806FC783CD499A8734D133AA75D09867A678D84C1D8C`.
AppData run `20260905T015602Z-p44824`, output
`.local/native-renderer/native-blended-stages-2x`, created both native paired
PSOs, captured frames 1800/2700 at 2560x1440 and exited normally at frame 2800.
No GPU errors; the existing `ResolvePath(\\Device)` filesystem message remains.
The final screenshot was inspected. This stationary scene run is a smoke
check, not broad visual or performance qualification. Saves were not manipulated.

The full Xenos retirement goal remains active: native scene execution and
resource ownership, remaining shader families, broader visual coverage and
measured lower hardware requirements are unfinished.

### Blended-lit depth/stencil parity verified; PSO difference identified

Extended the visible-draw replay check to the bound depth/stencil target.
At event **20164**, `ResourceId::2966` is 2560x1024, four samples,
`D32S8_TYPELESS`. All **83,886,080 depth/stencil bytes** match the native
replacement across its four samples. The original draw changes 172,882 bytes
of sample zero; an always-discard replacement differs by exactly 172,882 bytes.
The readback is nonempty (20,971,520 bytes/sample), depth testing and writes
are enabled. Together with the preceding color check, this qualifies both
attachments at this captured event, not the entire renderer.

Event 13717 also changes sample-zero depth (5,978 bytes); event 10326 changes
neither color nor depth and remains unqualified. Sampling every tenth draw
for pipeline `ResourceId::947` found no sample-zero depth-changing draw; this
is a coverage limitation, not proof that the pipeline never writes depth or
that other samples are inactive.

Compared the two admitted serialized pipeline descriptions directly in the
native startup catalog. Their only difference is byte 40 (`08` versus `09`),
the `strip_cut_index` field: disabled versus `0xFFFF`. All shader, blend,
rasterizer and depth/stencil description bytes otherwise match. This supports
their shared pixel-stage behavior but does not replace missing independent
visible-draw coverage. The 195-versus-256 static shader instruction-slot counts
are not measured GPU performance.

Evidence: `.local/native-renderer/blended-scene-depth-replay/report.json`,
sample-zero payloads, `scene-depth-inspection.json`, and
`blended-pipeline-state-comparison.json`. Reproducible local scripts are
`test-blended-scene-depth-replay.py` and `inspect-scene-depth.py` in the same
parent directory. No production source/DLL or save changed this continuation.
Full native scene execution, resource ownership, Xenos retirement and hardware
requirement reduction remain incomplete.

### Native blended-lit pixel stage integrated for two observed PSOs — 01:40 UTC

Broadened replay to visible event **20164** in the same capture. The original
draw changes 254,747 sample-zero bytes; the deliberately wrong replacement
changes 259,223 bytes. Corrected native blended-lit output again matches all
83,886,080 bytes across four MSAA samples. Evidence:
`.local/native-renderer/blended-scene-replay-late/report.json` and
`test-blended-scene-replay-late.py` in the parent directory. Both qualified
visible events use captured pipeline `ResourceId::868`; the other captured
pipeline had only a no-op check, so its independent visible-state coverage
remains a gap. Broader scene/adapter qualification remains pending.

Compiled the corrected HLSL with Windows SDK fxc, profile `ps_5_1`, `/O3` and
`/enable_unbounded_descriptor_tables`, into
`shaders/bytecode/d3d12_5_1/fh1_blended_lit_ps.h`. Runtime pipeline creation now
selects it only for bindless host render targets, exact VS/PS pair
`8D8A197476841A9A / BA6A2871A980A4E8`, and observed pipeline-description hashes
`5F7B3365E7F062BD` or `3FB9D30370C455D8`. Failed native PSO creation retries
with the guest bytecode. Guest vertex execution, metadata, bindings and shader
pack fallback are retained; this is a pixel-stage migration, not a native
scene executor or full Xenos retirement.

Built/staged DLL SHA-256:
`1A21883086D1BAB1706B44C18E05E5EE2B2F0FEA8190AB0C3822B9F3581DB7C5`.
Session `20260905T013922Z-p50004` logs successful native creation of both PSOs,
completes both 2x gameplay captures and exits normally. No GPU errors; the
unrelated `ResolvePath(\\Device)` filesystem message remains. Final capture
visually inspected. Logs prove pipeline creation, not a dedicated native draw
counter. Evidence: `.local/native-renderer/native-blended-pixel-2x/validation.json`,
session log and captures. SDK build and 40 existing tests pass. No performance
gain is established yet. Rollback source/DLL:
`.local/native-renderer/before-native-blended-pixel.{cpp,dll}`. No saves copied/reset.

### Native blended-lit coverage fixed; four-sample replay parity passes

Used RenderDoc `BuildTargetShader`/`ReplaceResource` to compare the existing
native `fh1_blended_lit.ps.hlsl` against captured guest shader
`BA6A2871A980A4E8`. Compilation requires `@cmdline` flags
`/T ps_5_1 /O3 /enable_unbounded_descriptor_tables`. Capture is the existing
`velocity-paired-rdc/frame_frame3069.rdc`; no gameplay or save changes needed.

Initial event 10326 matched but was a no-op: even an intentionally wrong shader
matched. Rejected that evidence. A visible draw at **event 13717**, pipeline
`ResourceId::868`, pixel shader `ResourceId::870`, changes 8,962 bytes of sample
zero. Its native replacement initially differed by 1,187 bytes there and
failed all four MSAA samples. Comparison of actual guest DXBC identified the
bug: alpha coverage uses `(Y & 1) | ((X & 1) << 1)`. Native candidates swapped
X/Y and retained unwanted high X bits. Corrected the expression in all 11
affected candidate pixel shaders after searching for its copies.

The corrected blended-lit candidate matches **all 83,886,080 bytes** across
the target's four MSAA samples at event 13717 (20,971,520 bytes/sample,
2560x1024 `R16G16B16A16_FLOAT`, target `ResourceId::2965`). A deliberately
magenta replacement changes 8,958 sample-zero bytes, confirming replacement
is effective. This is one captured scene state, not full shader/scene parity.
Other corrected candidates are not individually qualified by this result.

Evidence and reproducible local replay:
`.local/native-renderer/blended-scene-replay/report.json`, sample-zero
`baseline.bin`/`native.bin`, and `test-blended-scene-replay.py` in the parent
directory. The report retains hashes for all four samples. RenderDoc resource
replacement affects prior uses of the shader during replay, not just this draw.
Production admission has not changed and no candidate was enabled by this
test. The existing 40 tests pass. Staged DLL remains
`A3C3A54864BE80DC42079B837983722A22120FB65609AE4FB17586C65C94CB44`.
Next: broaden visible-state replay qualification and integrate native scene
submission/resources; full Xenos retirement remains incomplete.

### Scene external loads decoded and associated with live shaders

The scene analyzer now decodes `SET_CONSTANT` writes into their actual
register banks and records `LOAD_ALU_CONSTANT` and `IM_LOAD` addresses, sizes,
destination registers/stages. Predicate variants retain the active shader
loads at each draw. Invalid constant banks, truncated loads and unsupported
shader-load forms are rejected; runnable self-checks cover the decoded ranges.

Across the 11 captured buffers there are 42 shader loads and 31 external
constant loads. Constants load 16 words at `43F0` (vertex constants 252–255,
21 occurrences) or `47F0` (pixel constants 252–255, 10 occurrences). These
external contents must remain live rather than being frozen into a recipe.

Joined all 974 captured-buffer draw offsets to the active loads and checked
their word counts against the corresponding local ucode dump lengths:

| Stage | Observed shader | Words | Draw observations |
| --- | --- | ---: | ---: |
| Vertex | `AD2C355A6BE1EE87` | 174 | 490 |
| Pixel | `2F2137BF953DA7AF` | 120 | 490 |
| Vertex | `8D8A197476841A9A` | 198 | 484 |
| Pixel | `BA6A2871A980A4E8` | 39 | 484 |

Evidence: `.local/native-renderer/scene-live-state-2x/shader-load-validation.json`
and the updated `bindings-summary.json`. These associations do not prove
resource lifetimes or current contents merely from reused addresses. The
analyzer self-check and 40 existing tests pass. Production runtime/DLL did
not change; native execution of these four programs and geometry/material
ownership remain to be implemented. Full Xenos retirement is not complete.

### Constant-write deduplication rejected after A–B–B–A measurement

The preceding constant-write optimization is **removed** from production.
Four sequential AppData gameplay runs used the same script and 2x settings,
alternating baseline/candidate/candidate/baseline. Every run completed both
captures and exited normally. Process CPU/memory were sampled once per second;
comparison uses elapsed process seconds 34–46. Frame statistics use the last
900 nonzero samples, so they are not exactly the same window or frame-locked.

| Run | CPU seconds / wall second | Mean private MiB | Median frame ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| A1, p40684 | 3.3388 | 5175.1 | 16.7230 | 21.336 |
| B1, p25040 | 3.2514 | 5163.7 | 17.3860 | 22.109 |
| B2, p42156 | 3.3092 | 5189.3 | 16.6495 | 20.680 |
| A2, p28624 | 3.2160 | 5149.3 | 16.8330 | 21.322 |

Candidate versus baseline averages: CPU +0.087%, private memory +0.277%,
working set -0.507%, median frame time +1.429%, p95 +0.307%. This shows no
useful benefit in the tested workload; run variation prevents a strong causal
regression claim. Removed the extra comparisons rather than retaining an
unproven hot-path optimization. This does not show that all possible forms of
constant upload reuse are unhelpful.

Verified the source difference contained only the intended deduplication
change, restored it, touched the source to force rebuilding, rebuilt and staged
the baseline. Production DLL SHA-256 is again
`A3C3A54864BE80DC42079B837983722A22120FB65609AE4FB17586C65C94CB44`.
All 40 existing tests pass. Native velocity and scene census changes remain.

Evidence: `.local/native-renderer/constant-dedup-abba-summary.json`, four
`constant-dedup-abba-{a1,b1,b2,a2}` directories with process samples/captures,
and the session-specific AppData JSONL/CSV logs. Runnable local benchmark and
summary scripts are `constant-dedup-abba.ps1` and
`summarize-constant-dedup-abba.py` in that parent directory. Do not rerun into
existing output directories. Candidate DLL retained only as local evidence.
No save files were copied/reset. Full Xenos retirement remains incomplete.

### Skip identical shader value-bank writes — 01:19 UTC

The D3D12 scalar and bulk register entry points now return early for bitwise
identical float or bool/loop constant writes. Bulk comparison byte-swaps the
guest words before comparing with host register values. This avoids redundant
constant-buffer invalidation/copy work for exact duplicates. Fetch, scratch,
control and other register writes retain their existing behavior, including
residency invalidation and memory writebacks. Shader-layout changes independently
invalidate float buffers in `UpdateBindings`, and existing frame invalidation
is retained. The optimization does not reuse buffers whose layout changed.

SDK build, whitespace check and 40 existing tests pass. Scripted AppData run
`20260905T011814Z-p44984` completed both 2x captures and exited normally. No GPU
errors occurred; the same filesystem `ResolvePath(\\Device)` message remains.
The final capture was visually inspected. Last 900 nonzero frame samples:
median 17.1065 ms; this does **not** establish a causal speedup. Controlled
performance comparison and broader scene parity remain pending.

Built/staged DLL SHA-256:
`63AADCBD1CB6885805220357BB7D4D89600E287E0268CC28289A57CCB400E26D`.
Rollback source/DLL: `.local/native-renderer/before-constant-dedup.{cpp,dll}`.
Evidence: `.local/native-renderer/constant-dedup-2x/validation.json`, session
log and captures. No save files were copied/reset. This reduces redundant
work in the retained backend; it does not retire scene rendering or Xenos.

### Scene predicate variants resolved and joined to live draws

Traced the captured family's six type-3 opcodes against the actual command
processor: bin-mask low/high (`60/61`), set constants (`2D`), shader load
(`27`), external constant load (`2F`), and indexed draw (`22`). Crucially,
`60/61` change **mask**, not selection. Selection stays external to these
buffers. Both mask halves are initialized before predicates are evaluated.

`tools/analyze-fh1-scene-bindings.py` now resolves this specific vocabulary's
predicates for each observed selection, retaining all executed packets in
order. It rejects unknown opcodes, malformed mask writes and predicates with
unknown incoming mask. Its self-check covers mask changes between predicates,
zero selection and missing initialization. This is an offline recipe, not a
runtime renderer or permission to suppress the command buffer.

The live-state capture yields 33 command/selection variants: 30 retain two
draws and three retain one. Each skips six predicated state packets and ends
with mask `00000000FFFFFFFF`. All **974** live draw-end offsets belonging to
the 11 captured buffers match their selected recipe. Six draws from uncaptured
larger buffers remain outside this result. Evidence is in
`.local/native-renderer/scene-live-state-2x/bindings-summary.json` and
`predicate-validation.json`. Analyzer self-check and 40 existing tests pass.

Next implementation must consume live external constant/shader/resource loads
and submit native geometry/material draws while preserving ordered state
effects. Predicate specialization alone replaces no Xenos draw. Production
DLL remains `A3C3A54864BE80DC42079B837983722A22120FB65609AE4FB17586C65C94CB44`.

### Scene draw-time scratch and predicate state captured — 01:15 UTC

Extended the existing bounded, census-only scene records with `scratch_mask`,
`scratch_address`, `bin_mask`, and `bin_select`. The analyzer reports missing
state explicitly and groups observed states; its self-check covers both old
records and the new fields. Normal rendering is unchanged with census disabled.

Session `20260905T011400Z-p508` completed normally with both gameplay captures.
Its 980 scene records all contain the new state. Every record has
`SCRATCH_UMSK=00020037`, `SCRATCH_ADDR=1FCA4000`: **scratch 6/7 writebacks are
disabled at these draw points**. The captured command family's direct register
writes target scratch 6/7; none directly write the mask/address registers.
This narrows the observed requirement but does not prove state at every packet
or permit dropping ordered side effects generally.

Observed mask/selection/count tuples:

- `00000000FFFFFFFF / 000000000000000C`: 402
- `00000000FFFFFFFF / 0000000000000030`: 402
- `00000000FFFFFFFF / 0000000080000003`: 172
- `000000008000003F / 000000000000000C`: 2
- `000000008000003F / 0000000000000030`: 2

All intersect at the sampled draw points. A native scene executor must still
evaluate each predicated command using the state at that command, preserve
register effects and any enabled writebacks, and own live geometry/material
resources. No scene draw has been replaced by this diagnostic change.
Evidence: `.local/native-renderer/scene-live-state-2x/{runtime-session.log,bindings-summary.json}`.
The SDK build, analyzer self-check and 40 renderer/release/launch tests pass.
Rollback DLL: `.local/native-renderer/native-before-scene-live-state.dll`.
Full Xenos retirement and lower-hardware qualification remain pending.

### Native velocity no longer requires the guest prewarm manifest — 01:12 UTC

Removed `IsFh1PrewarmManifestLoaded()` from native velocity admission. Its
exact shader, pipeline, attachment, resource, operation, hazard, constant and
live texture checks remain. Removed the redundant three-value family hash:
the individually checked shader/pipeline/operation values reproduce
`5B8F44932893A6CE` with the existing bytewise FNV calculation. Native execution
does not need membership in the guest pipeline startup catalog.

Production SDK built successfully; all 40 renderer/release/launch tests pass.
Built/staged DLL SHA-256:
`EC0F299C157D60394FC031DCF5C4C45B419FDC318A74639A1118CA3634818CE0`.
Rollback DLL: `.local/native-renderer/native-before-manifest-independent.dll`.

For live validation, temporarily moved only the AppData cache manifest aside,
ran the required launcher with the existing AppData profile, then restored the
manifest in `finally` and verified its original hash. No save files were
copied, moved or reset. Session `20260905T011107Z-p47124` completed both 2x
gameplay captures and exited normally. Its first native draw logs guest VS
translated true, **PS translated false, prewarm manifest false**. At least
1,197 native velocity draws were logged. No GPU errors occurred; the session
contains an unrelated filesystem `ResolvePath(\\Device)` error. The final
capture was visually inspected. Evidence is in
`.local/native-renderer/native-manifest-independent-2x/validation.json`,
`runtime-session.log`, and its two captures.

The last 900 nonzero frame samples have median 16.826 ms; this is not a causal
performance comparison. Full Xenos retirement remains incomplete: scene
execution, command processing, resource/target ownership and fallback still
depend on it. The catalog remains installed for those consumers; only the
native velocity admission dependency was removed.

### Reproducible velocity replay and capture coverage audit

Added `tools/export-fh1-velocity-pair.py`, replacing the machine-specific local
replay script for future checks. It accepts the existing RenderDoc environment
variables, requires a new output directory, records the capture SHA-256,
validates the draw markers and target format, and exports paired payloads.
`tools/compare-fh1-velocity-pair.py` now rejects payloads whose SHA-256 differs
from the exported metadata; its self-check covers failed/missing exports and
payload mismatch as well as no-op and unequal draws.

Replayed all three existing paired captures. Frame 3069 reproduces the exact
41,943,040-byte match and 1,969,763 changed bytes. Frames **3070 and 3071 have
no native velocity marker** and are rejected, not counted as parity evidence.
Reports are under `.local/native-renderer/velocity-pair-3069-recheck`,
`velocity-pair-3070`, and `velocity-pair-3071`. Coverage therefore remains
**one velocity draw pair**, not three. Production renderer code and DLL were
unchanged in this continuation; no runtime speedup is claimed. The comparator
self-check and all 40 renderer/release/launch tests pass.

Example replay (use a fresh output directory each time):

```powershell
$env:PINYON_SHIFT_RENDERDOC_CAPTURE = Join-Path $PWD '.local/native-renderer/velocity-paired-rdc/frame_frame3069.rdc'
$env:PINYON_SHIFT_RENDERDOC_EXPORT_DIR = Join-Path $PWD '.local/native-renderer/velocity-pair-new-check'
$replay = Start-Process .local/tools/renderdoc-1.45/RenderDoc_1.45_64/qrenderdoc.exe -WindowStyle Hidden -ArgumentList @('--python', (Join-Path $PWD 'tools/export-fh1-velocity-pair.py')) -PassThru
$null = $replay.Handle
$replay.WaitForExit()
python tools/compare-fh1-velocity-pair.py $env:PINYON_SHIFT_RENDERDOC_EXPORT_DIR
```

Inspect `paired-output.json` and require comparator success: qrenderdoc's
process exit alone is not a reliable export-success signal. Further native
scene submission/resource ownership and full Xenos retirement remain pending.

### Same-frame velocity pixel parity verified — 01:03 UTC

A temporary diagnostic binary submitted native velocity dilation and then
continued into the guest draw in the same `IssueDraw`, marking the latter
`FH1 velocity parity guest draw`. This diagnostic is **not** the production
binary. Production source was restored, rebuilt, and the staged DLL restored
to `1511661E696DF02E12DEAF8C4E73F0ECE6744215C1A9F97628C0287DDB292F9C`;
its source was checked against the pre-test backup. The existing 40 tests pass.

AppData session 35304 completed normally under RenderDoc. In
`.local/native-renderer/velocity-paired-rdc/frame_frame3069.rdc`, native event
25193 and guest event 25208 write the same mip/slice of `ResourceId::2659`.
Both viewport/scissor rectangles are 1280x720 at the origin, within the
2560x4096 RGBA8 target allocation. No draw intervenes; sampled source
`ResourceId::13856` has identical content hashes at both events.

**All 41,943,040 target bytes match exactly.** The native draw changes
1,969,763 bytes relative to the immediately preceding event, ruling out a
trivial no-op comparison. Capture SHA-256:
`D8B553E20C97316A633340E4A9DA4A3138329B77059E828356B182897D6E4894`.
This is direct identical-input pixel parity for **one captured velocity pair**;
it does not establish all-scene or whole-renderer parity or a performance gain.

`tools/compare-fh1-velocity-pair.py` checks matching source/target/subresource,
viewport/scissor, event order, absence of intervening draws, packed RGBA8 byte
counts, nontrivial native writes, and exact native/guest bytes. Runnable checks:

```powershell
python tools/compare-fh1-velocity-pair.py --self-test
python tools/compare-fh1-velocity-pair.py .local/native-renderer/velocity-paired-rdc
```

The directory contains `before.rgba`, `native.rgba`, `guest.rgba`,
`paired-output.json`, and `comparison.json`. The focused replay exporter is
`.local/native-renderer/export-velocity-pair.py`; it uses the installed
RenderDoc API's `GetTextureData(resource, subresource)`. Additional captures
3070/3071 remain available but unqualified. Retained test binary
`velocity-pair-diagnostic.dll` is local-only and must not be shipped.
Full Xenos retirement remains pending.

### Fresh velocity RenderDoc capture acquired — 00:55 UTC

Added optional `-DirectChildProcess` to `tools/launch-preview.ps1`. It uses
`Start-Process -NoNewWindow` and caches the live process handle before waiting.
Normal launch behavior is unchanged without the switch. This allows RenderDoc
child-process injection to follow the required launcher. The first shell-based
attempt saw only PowerShell; the direct-child retry confirmed `renderdoc.dll`
inside game PID 37032, completed the scripted run and reported exit code 0.
The existing 40 tests pass. No game binary or save files changed this turn.

Three frames were captured under `.local/native-renderer/velocity-fresh-rdc-r2`:
`frame_frame3080.rdc`, `frame_frame3081.rdc`, `frame_frame3082.rdc`. Control
metadata records the exact injected game PID and trigger. The first contains
5,222 actions and **native velocity draw event 25879** (marker 25874).
Its output is `ResourceId::2833`, 2560x4096, `R8G8B8A8_UNORM`; its sampled
texture is `ResourceId::13895`, 1280x720, typeless RGBA8 viewed as UNORM,
mip/slice zero. The render target allocation height is not viewport height.
`velocity-events.json` stores these verified bindings.

The broad per-draw trace export was deliberately stopped and replaced with
the focused `.local/native-renderer/export-velocity-events.py` marker query.
That exporter completes without querying every draw. The control/launch
scripts are `velocity-renderdoc-{control.py,launch.ps1}` in the parent folder.
Next: use a temporary paired native/guest diagnostic draw to compare output
at two events in one capture. Current captures prove the required pass and
input are present, but do not yet prove guest/native pixel parity or retirement.

### Identical-input parity capture audit — 00:41 UTC

Replayed `.local/qualification/nr04c-xenos-capture-20260828/`
`reference_frame9837.rdc` with the existing pass-trace exporter. The resulting
`.local/native-renderer/velocity-reference-trace.json` contains only two
presentation draws, so it cannot validate velocity dilation. Capture SHA-256:
`4cfbd6f751cc59695b40bb9ac31fcdebafdf72e73bd55d6603158778dbc85daf`.
Other existing traces have 2,633 events for `reference_frame8134.rdc` and 220
for `open-world_frame437291.rdc`, but no verified matching velocity event has
been identified. Do not substitute these for identical-input pass parity.

The installed RenderDoc 1.45 CLI supports `capture --opt-hook-children`, so a
fresh capture can wrap the required `tools/launch-preview.ps1` launcher rather
than bypassing its AppData launch procedure. Inspected the installed Python
API; `TargetControl.TriggerCapture`/`QueueCapture` and remote-target enumeration
are available. API documentation is saved in
`.local/native-renderer/renderdoc-target-api.txt`. Next: capture and verify a
fresh frame containing the velocity draw and its live source/output textures.
This audit changes no runtime renderer code or staged binary; full parity
remains pending.

### Native velocity rectangle preparation — 00:37 UTC

Live tracing corrected an initial wrong assumption: this pass uses an
auto-indexed **rectangle list**, not a triangle list. Observed initiator
`00030088`, output path `00000000`, guest/host primitive 8, no index buffer,
three vertices. The unused triangle shortcut was removed. For the exact
velocity shader pair and these register values, with rectangle expansion in
the vertex shader disabled, the native path now fills that fixed processing
result directly instead of calling `PrimitiveProcessor::Process`. It preserves
the live (inactive) tessellation-mode field and all generic result fields;
other modes use the generic processor. Guest fallback can consume the same
rectangle description. This removes primitive preparation for the admitted
native pass, not command processing or scene geometry conversion.

Build, 40 tests and whitespace checks pass. Staged SHA-256:
`1511661E696DF02E12DEAF8C4E73F0ECE6744215C1A9F97628C0287DDB292F9C`.
Session `20260905T003541Z-p7580` confirms **native preparation true**, guest
pixel shader untranslated, and at least 1,219 native velocity draws. Both
captures completed, normal exit, no GPU errors. End capture inspected.
Median of the last 900 nonzero frame-time samples: 16.6745 ms, without causal
speedup evidence. MAEs against the preceding trace run were 5.7486 and 7.7855;
these unsynchronized captures do not prove pixel parity. Evidence is under
`.local/native-renderer/native-velocity-rectangle-2x` with validation JSON,
session log and captures. Prior production binary:
`native-before-velocity-primitive.dll` in the parent directory. Full retirement
remains incomplete; no save files were copied/reset.

### Cold velocity pixel shader and lazy fallback verified — 00:30 UTC

On the bindless path, startup now defers loading guest pixel shader
`ECE830AC0333767F`; its bytecode remains in the pack for fallback. Startup
therefore loads 527 precompiled variants and prewarms 460 guest pipelines,
versus 528/461 in the preceding run. The shared vertex shader remains eager.
This removes one eager guest shader/pipeline, not the renderer as a whole.

Native session `20260905T002621Z-p12352` logged its first velocity draw with
**guest PS translated false** (VS true), then at least 1,209 native draws.
Both captures completed and the process exited normally without GPU errors.
Last 900 nonzero samples: median 17.202 ms. End capture inspected; MAEs versus
the previous run were 2.3722 and 4.2499 with dynamic scene differences.

A temporary validation binary returned false at the start of
`DrawFh1VelocityDilate`, forcing lazy guest preparation after native admission.
Session `20260905T002813Z-p40260` completed both captures with no native velocity
draws and no GPU errors. End capture inspected; MAEs versus native were 0.9412
and 1.7508. Median 16.927 ms does not establish a performance difference.
The forced return was removed, production source rebuilt, and the production
DLL restored. **Do not ship** `native-velocity-forced-fallback.dll`; it exists
only under `.local/native-renderer` for this validation.

Production build, 40 tests and whitespace checks pass. Final built/staged hash:
`383A3589A21FB65B0FA615A987E55F48203315B1D78EEA1C4BF7C3963C1E7D4B`.
Logs/captures/validation JSON are in `native-velocity-lazy-2x` and
`native-velocity-forced-fallback-2x` under `.local/native-renderer`. Prior
production DLL: `native-before-velocity-lazy.dll`. No saves were copied/reset.
The guest pixel shader is no longer required for this admitted native draw,
but fallback, shared vertex metadata, command processing, resource/target
ownership and scene rendering still retain Xenos dependencies. Full retirement
and full parity remain incomplete.

### Velocity admission accepts analyzed metadata — 00:24 UTC

The exact velocity shader pair now supplies its known fetch-3 mask and requests
native-binding mode from `GetNativeDrawPipelineDescriptionHash`. That mode
requires analyzed shader metadata but does not require valid translated guest
bytecode; the state builder already supports metadata-only descriptions.
Tone mapping retains the translation requirement. Native decline still routes
through guest configuration before drawing. The first successful native
velocity draw logs both guest translation states for verification.

Build, 40 tests and whitespace checks pass. Tested/staged SHA-256:
`DBF086E863F9A05E4DBB4128CBD762AF96376E7CF39B370DE0E3C26F9389B392`.
Session `20260905T002254Z-p48092` completed both captures and exited normally;
at least 1,126 native velocity draws and no GPU errors were logged. **Both
guest shaders were already translated on its first native draw.** Thus this
run verifies behavior with the new metadata-only admission mode, but does not
prove cold operation without guest translations. Prewarming/shared shader
usage must be accounted for before claiming those assets can be removed.

End capture inspected; RGB MAEs versus the preceding stationary run were
2.6465 and 4.7516. Positions matched within 0.001 world units, but dynamic
scene/time differences persist. Last 900 nonzero samples: median 17.136 ms,
with no established speedup. Evidence: `.local/native-renderer/`
`native-velocity-untranslated-2x/validation.json`, captures and session log.
Rollback binary: `native-before-velocity-untranslated.dll` in the parent
directory. Cold-state validation, full parity and Xenos retirement are pending.

### Native velocity binding no longer scans translated tables — 00:21 UTC

Velocity dilation now supplies its fixed unsigned 2D fetch-3 binding directly
after the existing exact shader-pair/state admission. Removed the translated
shader binding-vector scan and signed/unsigned entry-count dependency. Live
texture resolution and the zero-swizzled-sign check remain. This does not
remove shader translation metadata from the earlier native-description check
or used-texture-mask calculation; tone-map bindings also remain translated.

Build, 40 tests and whitespace checks pass. Backend SHA-256:
`4286D492D09EAE91D098173F04A638C06BC5B9C4F032246BDBE3E06360E94257`.
Session `20260905T001920Z-p37188` exited normally after both captures, logged
at least 1,210 native velocity draws and no GPU errors. The end capture was
inspected. Vehicle position matches the prior stationary run within 0.001;
RGB MAEs were 1.1090 and 1.0966. Last 900 nonzero frame-time samples had median
17.593 ms; no performance gain is established. Evidence is in
`.local/native-renderer/native-velocity-binding-2x/validation.json`, captures
and session log. Previous binary: `native-before-velocity-binding.dll` in the
parent directory. The goal remains incomplete.

### Native state validation creates no guest GPU objects — September 5, 00:16 UTC

Moved guest root-signature lookup/creation and geometry-shader materialization
from `GetCurrentStateDescription` into its `ConfigurePipeline` caller. The
native hash caller now only builds the description; ordinary guest pipeline
configuration still supplies the same objects before cache lookup/creation.
The serialized/hashable description is unchanged. Native rendering still
requires shader metadata, primitive processing, textures and render targets;
those dependencies and all scene rendering remain to be replaced.

Backend build, 40 tests and whitespace checks pass. Tested/staged SHA-256:
`1FF01080DB42F54A167F4D3CE9CCAD4A6F78637B467E5CABFF1E0D86A083BF09`.
Subsequent comment/format edits change no executable logic. Exact session
`20260905T001411Z-p29616` completed two captures, exited normally, recorded at
least 1,199 native velocity draws and no GPU errors. Last 900 nonzero frame
samples: median 16.7315 ms, without a demonstrated causal speedup.

The end capture was inspected. Comparing against repeat candidate 1968 gave
large differences because that run moved the vehicle down the road (visible
6 km/h at its end); those images do not establish rendering parity. Against
stationary candidate 22444, with capture event positions matching within
0.001 world units, RGB MAEs were 0.6871 and 2.0931. Dynamic traffic/people still
prevent identical-frame comparisons. Evidence and caveats are saved in
`.local/native-renderer/native-state-only-2x/validation.json` with captures and
session log; rollback binary is `native-before-state-only.dll` in the parent
directory. No saves were copied/reset. Full parity and retirement are unproven.

### Native admission without guest PSO configuration — September 5, 00:12 UTC

`GetNativeDrawPipelineDescriptionHash` uses the existing state-description
builder and hash for already translated, valid shader metadata, without guest
PSO lookup or creation. The two existing native shader pairs try that path
before `ConfigurePipeline`. Unavailable metadata uses normal configuration;
failed native admission/submission configures the guest pipeline before binding
and drawing. The binding lambda references the eventual handle, avoiding a
captured null handle on fallback. This still builds a guest root signature and
uses compatibility shader metadata/state decoding, render targets and textures;
it is not full pass or scene retirement.

Backend build and 40 tests pass. Built/staged binary SHA-256:
`8FD8558290EB55744E590FC7AB24901FA7756A0785B59D0985AD2A5FDFB68A7B`.
A subsequent source comment edit changes no executable logic. Candidate runs
22444 and 1968 and repeat control 46776 completed both requested captures and
exited normally. The first candidate recorded at least 1,210 native velocity
draws and no GPU errors; its end capture was inspected. Capture MAEs versus
the preceding system-constant candidate were 1.2981 and 1.7163. Tone-map
execution and forced native-failure fallback still lack focused live coverage.

Correct last-900 nonzero sample medians: candidate 17.225 ms, repeat control
16.879 ms, repeat candidate 16.9995 ms. These show no established speedup.
**Analysis correction:** the initial 33.184 ms candidate result came from an
older session with reused PID 22444. Use exact timestamped session
`20260905T000809Z-p22444`, never the first PID glob match. The preceding three
run medians were checked and had unique matches. Corrected evidence is in
`.local/native-renderer/native-pso-repeat-comparison.json` and
`native-no-guest-pso-2x/validation.json`; repeat captures are in
`native-pso-{control,candidate}-r2-2x`. Prior binary:
`.local/native-renderer/native-before-pso-bypass.dll`. Goal remains incomplete.

### Velocity dilation skips system constants — September 5, 00:06 UTC

Successful native velocity draws now also return before
`UpdateSystemConstantValues`; their shader consumes only its texture, with no
guest system constants. Tone mapping remains after that call because it still
reads `color_exp_bias[0]`. Guest fallback still executes the original update.
The backend builds, 40 tests pass, and SDK diff whitespace checks pass.
Built/staged SHA-256:
`ABFAAB00186DC324595DE06BDB4D02D2724225C03D24E7859C2A356105BD3EB1`.

AppData run `native-velocity-system-2x` (50776) completed two captures, exited
normally, recorded at least 1,200 native velocity draws and no GPU errors.
The end capture was inspected; the white minimap persists. Capture MAEs versus
the preceding candidate were 1.6614 and 2.7867, with moving traffic and people
visible in the unsynchronized frames. Last 900 nonzero frame-time samples had
median 16.9525 ms; this does not establish a speedup. Session log, PNGs and
`validation.json` are in that run directory. Full parity remains unproven.

Next dependency: native admission currently consumes the guest pipeline
description hash from `ConfigurePipeline`, which also prepares translations,
guest root signatures and PSOs. Removing PSO preparation requires separating
state validation from object creation, or replacing the hash-based admission
with explicit validated title state. Do not skip configuration while still
reading its handle or assume the prewarm catalog is a native scene executor.

### Native full-screen submission skips guest bindings — September 5, 00:03 UTC

The existing native velocity-dilation and tone-map calls now execute after
fixed-function/system-state preparation but before `UpdateBindings`, vertex
buffer residency, memexport-range gathering, and guest primitive-topology
selection. Guest PSO binding is also deferred until native submission declines.
Their own root signatures, descriptors, PSOs and `SV_VertexID` triangle supply
the draw; `BeginSubmission` already binds the shared bindless descriptor heaps.
Admission still excludes memexport. Failed native preparation falls through to
the original guest setup, and external root/PSO setters invalidate guest state.
This removes actual compatibility preparation from successful native draws;
shader analysis, primitive processing, render-target and texture preparation,
and guest PSO configuration still occur earlier and remain to be retired.

Built/staged backend SHA-256:
`AD696FD4C84FD92A4FBA690EC6D582FB29FBE8F8F059D72F984DBA6626DA4C17`.
The backend builds and 40 contract/automation tests pass. AppData-backed 2x
open-world control (49484) and candidate (37976) both exited normally with two
captures and no GPU-error records. Both exercised native velocity dilation;
neither logged native tone-map execution, so that branch lacks live coverage
in this comparison. Candidate end capture was visually inspected. RGB mean
absolute differences versus control were 1.1865 and 0.9972 out of 255; these
wall-clock captures are not identical simulation frames or full parity proof.
The pre-existing white minimap remains visible.

Last 900 nonzero CSV frame-time samples had medians 19.021 ms (control) and
16.520 ms (candidate). One pair cannot attribute this difference to the edit,
especially with the earlier run variance; do not claim that speedup. Evidence:
`.local/native-renderer/native-early-comparison.json`, the two
`native-early-{control,candidate}-2x` directories and their session logs.
Previous staged DLL is saved as `.local/native-renderer/native-early-control.dll`.
No save files were copied or reset. Full scene replacement and Xenos retirement
remain incomplete.

### Ordered scratch side effects — executor boundary correction

The template's repeated writes to register `057E` target `SCRATCH_REG6`,
not an ordinary material register; `057F` is `SCRATCH_REG7`. The existing
`CommandProcessor::WriteRegister` writes each value to guest physical memory
when the corresponding `SCRATCH_UMSK` bit is enabled, using `SCRATCH_ADDR`
plus four times the scratch index. Preserving only final register state is
therefore insufficient. Repeated values may also be observable writes.

The analyzer now expands type-0 sequential/repeated and type-1 register writes,
retains ordered scratch writeback candidates, and marks type-3 predication.
All ten captured two-draw templates contain **24 scratch writes and 11
predicated commands**; the one-draw template contains 15 and 10 respectively.
The existing session summary was regenerated with this information. The
capture does not establish whether scratch writeback was enabled: these are
potential side effects, not evidence of 24 actual guest-memory writes.

The runnable self-check passes, including repeated writes to the same register,
sequential scratch writes, both type-1 destinations, and predication applying
only to type 3. This is an offline diagnostic change; it changes no game
execution and establishes no performance improvement. A native scene executor
must retain these ordered side effects alongside its draws, evaluate live bin
predicates, and track external loads and resources. No native scene executor
has replaced these buffers yet, and full Xenos retirement remains pending.

### Command-list object correlation — 23:47 UTC continuation

The preceding turn made progress by proving the ordered draw/transform pairs.
This continuation correlates the GPU buffers to the title's actual indirect
submission objects and captures their command contents.

- `82416A00` preserves entry `r4` in `r24`. Its loop at `82416EF0` reads
  indirect targets/counts from the object's linked list at offset 116.
- A census-only hook at `82416F18` observes `r24`, target `r10`, and count
  `r11` immediately before the target store. The verified title image contains
  instruction `955E0004` (`stwu r10,4(r30)`) there. Generated partition 201
  places the hook at that exact instruction; it changes no guest register.
- The hook records at most 4,096 unique object/target/count tuples. The GPU
  census records the containing buffer's physical base, byte length, and draw
  end offset. Address and length matches report observed associations, not
  an object's lifetime or a particular reused packet generation.
- Session `scene-producer-2x` (process 37132) recorded 980 draws from 13 buffers.
  974 draws matched **11** unique command-list objects. The six unmatched
  layered-lit follow-ups came from two larger buffers. No producer cap was
  reached. (The earlier progress update's count of 12 objects was incorrect.)

Session `scene-commands-2x` (process 37560) adds bounded command snapshots:
at most 32 distinct content hashes, at most 8 KiB per buffer. Eleven buffers
were captured. Ten contain 92 packets and two indexed draws each; one contains
62 packets and one draw. The repeated two-draw buffers are 1,788 bytes.
Every observed buffer kept the same command hash across the two sampled
gameplay frames. Those hashes are diagnostic fingerprints, not a collision-safe
or lifetime-safe admission mechanism. Both sessions exited normally with two
requested gameplay captures and no GPU errors.

The two-draw templates contain bin selection, predicated register writes,
constant uploads/loads, shader loads, texture/vertex fetch setup, and indexed
draws. The instance-transform registers identified above are supplied outside
the templates. This supports a concrete next executor boundary: compile this
exact FH1 command-list family into a native scene packet once, then submit its
ordered native draws using live instance constants. It does **not** support
simply dropping the buffer: preserve bin-predication behavior, all final
register side effects visible to retained consumers, resource changes, and
geometry/material lifetimes. The normal Xenos path still executes these draws.

`tools/analyze-fh1-scene-bindings.py` now reports object associations and
decodes command snapshots with bounds checks. Its self-check covers sequence
gaps, frame boundaries, constant differences, missing transforms, observed
hazards, physical-address normalization, exact buffer length, and truncated
packets. The executable/backend build and 40 contract/automation tests pass;
codegen warning verification accepts only the existing three warning families.
Full session logs and `bindings-summary.json` are in the two run directories
above under `.local/native-renderer/`. No saves were copied or reset.

The final ordinary (census-disabled) open-world run,
`scene-producer-disabled-2x` (process 34768), exited normally, completed both
captures, emitted no GPU errors, and emitted no scene binding, command, or
producer diagnostic records. Final executable SHA-256:
`18401B6F71F72079C82ADE49CCC557E55DFE15BB1F09C4E0CDAA188640C6ED5F`.
Final built/staged backend SHA-256:
`5EDA354DC33373C89804731C3E6A131CF234EA1BD52D30D2A3B87BC5819AC323`.

### Ordered live bindings — 23:35 UTC continuation

The previous turn made progress through the rejected-code deletion and paired
visual evidence. This continuation adds a bounded scene snapshot in the D3D12
command processor and its runnable analyzer:
`python tools/analyze-fh1-scene-bindings.py --self-test`.
The backend builds, that self-check passes, and the 33 existing release-contract
and render-runner tests still pass. The latest built/staged DLL SHA-256 is
`8810D05E2F58B3C9E7A99E1BBB60579F11B988F5C7742EA73ACD0CE58E9AE2E9`.

Snapshots require the existing census flag and observer. They sample every
600 source frames starting at frame 1200, stop at 4,096 records, and record the
target `AD2C355A6BE1EE87 / 2F2137BF953DA7AF` on attachment
`7336ADFF531DCC00` plus its immediate following prepared draw. They retain raw
live texture/vertex fetches, used float constants, bool/loop constants, shader
and pipeline identities, draw sequence, and index-buffer metadata. Ordinary
release gameplay does not construct these snapshots. They are diagnostic
evidence and are never consumed as native admission or suppression permission.

The valid initial capture (`scene-binding-2x-r2`, process 23960) recorded 490
target draws in two gameplay frames. No two adjacent target draws shared a
complete binding snapshot. 478 target-to-target intervals contained exactly
one intervening draw. The first attempted output directory had already been
created by test setup; the application correctly rejected it before gameplay.
That failed attempt is not performance or rendering evidence.

The follow-up capture (`scene-binding-pairs-2x`, process 28816) recorded 980
snapshots: 490 target draws, 484 blended-lit draws using
`8D8A197476841A9A / BA6A2871A980A4E8`, and six layered-lit draws. Both valid
runs captured their requested images, exited normally, and logged no GPU
errors. Census timings are not release performance evidence.

**Key finding:** every one of the 478 observed consecutive blended-lit → target
pairs shares all seven captured transform-register values (float constants
128–131 and 140–142). Conversely, target → next blended-lit has different
transform values in 466 of 484 instances. The candidate is an ordered
per-instance pair of different geometry/material draws, not a consecutive run
of identical draws. Do not replace it with shader-family-wide instancing or
reorder the two materials without proving visibility/blending dependencies.

Reproduce the report with:

```powershell
python tools/analyze-fh1-scene-bindings.py .local/native-renderer/scene-binding-pairs-2x/runtime-session.log
```

The report is retained beside the log as `bindings-summary.json`. The runtime
log rotated during the follow-up; its session log was recovered from the
ordered `runtime.N.log` segments using the session start timestamp. An old
byte offset alone is invalid across rotation.

Next: correlate this ordered pair to its title command-buffer producer and
recover the actual prepared instance/material data. Historical
`INDIRECT_CONTEXT_ROOTS.md` and `PROCEDURAL_MODEL_RECEIVER_LIFETIME.md` identify
the live procedural receiver dispatch `82417BC0` and its indirect producer
`82417060`. That is a lead, **not yet proof that this shader pair belongs to
that receiver**. The historical giant provenance bridge was removed earlier;
restore only the exact packet/producer correlation needed for this family.
No native scene executor or Xenos scene retirement is claimed by this capture.

The active goal now explicitly includes **fully retiring the Xenos renderer**.
The following findings supersede conflicting claims below; the earlier
measurements remain historical evidence.

- Both `kFh1UseNativeWorldVertexShaders` and
  `kFh1UseNativeDepthMeshVertexShaders` were already **false** when resumed.
  They remain false. Do not describe these substitutions as enabled or count
  them as retired scene work.
- Removed the rejected broad shader-substitution branch, its counters and
  unused accessors, the binary-alpha PSO status field and output parameter,
  and 16 unreferenced generated shader headers. Preserved the separately
  controlled world/depth vertex code and the tone-map/velocity executors.
  This is dead-code removal, with no claimed frame-time improvement.
- Release backend build and 33 release-contract/automation tests pass.
  Markdown links and the SDK whitespace check pass.
- The original staged DLL was verified against the checkpoint SHA-256 and
  retained at `.local/native-renderer/retirement-resume-original/rexgpu-fh1.dll`.
  Pre-edit pipeline source/header copies are beside it; the repository already
  had extensive uncommitted edits. No commit or reset was performed.
- Test launches use `tools/launch-preview.ps1` directly with the installed
  `0.1.0` AppData state after checking its profile and process state. No save
  was copied, reset, or overwritten by test setup. The Python runner's existing
  unconditional save-copy behavior conflicts with the current repository
  launch instructions and was not used.

Three 2x shipping runs used the existing AppData catalogs and the complete
22,012-entry pack `fh1-disc-aot-complete-2x.pnsp`. These are stationary
Recaro Rush-location runs on a Ryzen 7 5800X / RTX 4080, not a matched Xenia or
minimum-hardware comparison. Each captured both requested gameplay images and
exited normally. Heavy-frame filtering remains `draw_calls > 3000`.

| Run | Samples | Median ms | Median FPS | p95 ms | Mean guest GPU ms | Pipeline-cache misses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cleanup 1 | 1,420 | 17.033 | 58.71 | 23.035 | 17.486 | 3 |
| Cleanup 2 | 1,147 | 19.190 | 52.11 | 34.077 | 20.793 | 7 |
| Cleanup 3 | 1,456 | 16.673 | 59.98 | 21.680 | 17.152 | 3 |
| Original checkpoint DLL control | 1,389 | 17.201 | 58.14 | 22.131 | — | — |

Results and captures live in `.local/native-renderer/retirement-resume-2x-r1`
through `r3`, with `summary.json` recording the exact session log. The control
is `.local/native-renderer/retirement-resume-original-2x-control`. This spread
does not establish a speedup. Shader misses were not separately instrumented
in these three runs; pipeline-cache misses above must not be reported as zero.
The unusually bright minimap appears with both the original and cleanup DLL;
that observation establishes only that this deletion did not introduce it.

The original/cleanup five-mode capture pair also exited normally. The SELECT
map is pixel-identical at full 2560x1440 resolution. Full-image mean absolute
errors on the 0–255 channel scale are 1.324 for free roam, 1.441 after map
return, 1.043 for pause, and 1.798 after resume. Visual inspection of the map,
roads/icons, pause fonts, and open-world scene found no new corruption.
Evidence is in `.local/native-renderer/retirement-resume-original-modes` and
`retirement-resume-cleanup-modes`; the latter includes `comparison.json` and
`runtime-session.log`, which excludes earlier appended sessions. This is a
limited regression comparison, not the complete title/loading, foliage/grass,
quit-modal, race, night/weather matrix or the stale scenario-counter gate.
The final built and staged backend DLLs match SHA-256
`DEC950A39DEA95A9CB8EF8EA9B01D13029F214513903349C534381A6C79D5FA3`.

### Scene-retirement prerequisite found in the actual code

`GraphicsFh1ExecutionKey.resource_state` intentionally masks texture base/mip
addresses and vertex-buffer addresses. `dynamic_state` excludes shader float,
Boolean, and loop constants. The corpus retains only the first index-buffer
address per identity and does not retain draw order. Therefore equal census
keys **cannot authorize batching, resource reuse, or suppression**.

For attachment `7336ADFF531DCC00`, the instrumented corpus contains:

- `3BC346726C1C2535 / 9584B309533EF6C9`: 457,192 executions, one PSO,
  189 resource-layout identities and 145 operation identities.
- `AD2C355A6BE1EE87 / 2F2137BF953DA7AF`: 310,420 executions, one PSO,
  16 resource-layout identities and nine first-observed index-buffer addresses.
- `8D8A197476841A9A / BA6A2871A980A4E8`: 321,412 executions, two PSOs,
  19 resource-layout identities and eleven first-observed index-buffer addresses.

These totals include all entries for each pair on that attachment, rather than
only the checkpoint's narrower group. The indexed pair beginning `AD2C355A`
is a useful next target for a bounded, ordered snapshot of live resource and
constant bindings. The existing hashes do not prove that repeated geometry
uses identical materials. Obtain that evidence, or recover authoritative FH1
prepared instances at their title owner, before implementing the executor.

Also, existing visual scenarios still require native world/depth and rejected
shader-substitution counters that current code cannot emit. Capturing a route
directly does not pass these stale `require-native` gates. Correct them against
actual scene-retirement counters when the native executor exists; do not
restore the rejected shaders merely to satisfy the old tests.

## Scope lock

- Optimize title ID `4D5309C9` only. Do not build a general Xbox 360, Xenos,
  ReXGlue, or multi-game renderer.
- "Native" means that identified FH1 work is represented and submitted in
  host-native terms without executing the corresponding Xenos command,
  register, resource, render-target, and draw machinery.
- Offline/precompiled DXIL, an FH1 DLL name, and handwritten shaders are useful
  infrastructure, but do not by themselves retire the Xenos path.
- Uncapped presentation must consist of real source-rendered frames. Do not use
  optical flow, generated/duplicated presentation frames, or FSR.
- Preserve the 30 Hz game simulation where required and interpolate source game
  state for genuinely rendered presentation frames.
- Keep a compatibility fallback only where replacement is unsafe or has no
  practical performance or requirements benefit.

## Current truth

`rexgpu-fh1.dll` is specialized for FH1, loads a complete offline DXIL pack,
prewarms known pipelines, and contains exact native tone-map and
velocity-dilation draws. The title-screen command-processing regression is
fixed and source cadence is unlocked. Most open-world scene draws still use
ShiftGlue's Xenos-compatible D3D12 command processor, registers, resource and
texture caches, render-target cache, and per-draw submission path. The product
is therefore **mostly Xenos-compatible today, not a complete native renderer**.

The latest retained-path optimization reduces work that normal release draws
were doing solely for census/native-candidate classification. It improves the
current product and its CPU requirement, but it is not scene-path retirement.

## Work completed at this checkpoint

### Release draw-key fast path

File: `thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp`

Before this change every release draw built a complete
`GraphicsFh1ExecutionKey`. That hashes texture-fetch layouts, vertex-fetch
layouts, dynamic registers, operation state, and other Xenos state even when no
prepared-draw observer is installed. Normal release execution only needs that
full key for the two exact native fullscreen candidates.

The code now:

1. Reuses the already available vertex and pixel ucode hashes.
2. Performs a cheap comparison against the exact tone-map pair
   `A2FC50159EB69BA2 / 618DD627F3D3B9A4` and velocity-dilate pair
   `C7D52884ECA9A039 / ECE830AC0333767F`.
3. Builds the complete execution key only when a prepared-draw observer is
   installed or one of those exact native pairs is encountered.

Census and profiling runs are unchanged because they install the observer.
Exact native admission remains fail-closed because candidates still receive
the complete key. All other release scene draws skip classification data that
they cannot consume.

### Draw-versus-resolve GPU instrumentation

Files:

- `thirdparty/shiftglue-sdk/include/rex/graphics/d3d12/command_processor.h`
- `thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp`
- `tools/run-fh1-render-test.py`

Sampled pass records now have timestamps for pass start, terminal-resolve start,
and pass end. Logs and automation results expose average draw time, average
resolve time, and maximum resolve time. Sampling remains once per 60 source
frames so census diagnostics do not become a release cost.

### Reliable shader-pack automation

Files:

- `tools/run-fh1-render-test.py`
- `tools/tests/test_run_fh1_render_test.py`
- `docs/native-renderer/FH1_RENDER_TEST_AUTOMATION.md`

Supplying `--shader-pack` now also seeds the offline analysis catalog. The
shipping backend needs both the compiled pack and the catalog; previously it
was easy to launch a nominal pack test that rejected draws as absent from the
catalog. Disc-corpus roots are also normalized to their `ucode` child when
needed. Fourteen automation unit tests pass.

### Existing retained work that matters

- The type-0 bulk register path fixed the title-screen 6–9 FPS regression; the
  automated title route measured 118.30 FPS median at 2x.
- The complete current 1x pack is
  `.local/native-renderer/4D5309C9.fh1-native-v2.10DE.09.1x1.complete-current.pnsp`.
  It has 21,987 entries, is 468,092,976 bytes, and has SHA-256
  `D147EE68C87D0298E0C1C394A83F68597492D4A0385BF507540EC63D9DCBA765`.
- The shipping route produces zero shader captures/misses when the complete
  pack and catalog are seeded.
- Exact native tone-map and velocity-dilate replacements remain enabled.
- Proven native vertex substitutions remain separate from the disabled broad
  handwritten candidate branch.

## Measured evidence

All rows below use the same automated 1x shipping route and include only frames
with more than 3,000 draws. The route is deterministic in input but its exact
frame/draw mix varies with source cadence, so the control-versus-optimized
comparison is evidence, not a final cross-product benchmark.

| Build/run | Samples | Median | Median FPS | p95 | p99 | Mean guest GPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full execution key control | 1,415 | 17.103 ms | 58.47 | 22.179 ms | 27.306 ms | 16.328 ms |
| Optimized run 1 | 1,589 | 15.808 ms | 63.26 | 18.659 ms | 22.726 ms | 14.820 ms |
| Optimized run 2 | 1,528 | 16.426 ms | 60.88 | 20.104 ms | 22.709 ms | 15.362 ms |
| Optimized run 3 | 1,553 | 16.220 ms | 61.65 | 19.886 ms | 23.665 ms | 15.276 ms |
| Optimized median of run medians | — | **16.220 ms** | **61.65** | — | — | — |

Against the one exact control, the first optimized run changed median heavy
frame time from 17.103 to 15.808 ms (-7.57%), median FPS from 58.47 to 63.26
(+8.19%), p95 from 22.179 to 18.659 ms (-15.87%), and p99 from 27.306 to
22.726 ms (-16.77%). The three optimized medians span 15.808–16.426 ms. Collect
multiple interleaved control/optimized pairs if a confidence interval is needed;
do not present the single control as a definitive percentage claim.

Evidence locations:

- Control result:
  `.local/native-renderer/automated/fh1-release-full-key-control-1x/result.json`
- Optimized results:
  `.local/native-renderer/automated/fh1-release-no-key-1x/result.json`,
  `.local/native-renderer/automated/fh1-release-no-key-1x-r2/result.json`, and
  `.local/native-renderer/automated/fh1-release-no-key-1x-r3/result.json`
- Instrumented pass profile:
  `.local/native-renderer/automated/fh1-pass-phase-profile-1x-instrumented/result.json`
- Execution corpus:
  `.local/native-renderer/automated/fh1-pass-phase-profile-1x-instrumented.state/cache/fh1-gpu-corpus/20260904T224108Z-p39516.json`

The currently staged preview DLL and build artifact match. Their SHA-256 is
`0EF309F68F30042F9DC1B5B30E181EE573755FB2B73A54EF0DF9A4157B0E779D`.

## What the pass profile established

The terminal resolve is not the dominant cost in the sampled heavy families:

| Family | Approx. draws | Average pass | Average draw phase | Average resolve phase |
| --- | ---: | ---: | ---: | ---: |
| `53B2C36308FCD219` | 812 | 1.524 ms | approximately all | none |
| `35463AC55D8F5C5C` | 454 | 1.179 ms | 1.168 ms | 0.010 ms |
| `DE5FF2C4F48916DA` | 96 | 0.538 ms | 0.523 ms | 0.014 ms |

Other dominant terminal resolves measured roughly 5–30 microseconds. The
explicit heavy-frame resolution control found 17.357 ms mean guest GPU at 1x
and 20.668 ms at 2x. Four times the pixels added only about 3.31 ms; hundreds or
thousands of retained scene draws dominate both scales.

The hottest sampled attachment is `7336ADFF531DCC00`. Important shader/pipeline
groups include:

- VS `3BC346726C1C2535`, PS `9584B309533EF6C9`, pipeline
  `AF2C95BF6EF10882`: 452,976 sampled executions across 242 identities.
- VS `AD2C355A6BE1EE87`, PS `2F2137BF953DA7AF`, pipeline
  `B673641288F80E60`: 309,426 executions across 27 identities.
- VS `8D8A197476841A9A`, PS `BA6A2871A980A4E8`, pipeline
  `5F7B3365E7F062BD`: 251,125 executions across 33 identities.
- The same shader pair with pipeline `3FB9D30370C455D8`: 69,266 executions
  across 33 identities. Its first draw identity is `67C44BD8A3CC080C`, shader
  state `043A012A8A7E24BA`, resource state `0F2209506176D4F6`, dynamic state
  `9CDB3285ED30BECC`, and operation state `5300586AECBA5DCE`.
- VS `6934E161812AB10B`, PS `A2C1F872E049AD8B`: 145,087 executions.

## Invalid evidence to ignore

Do not use these two directories as performance or correctness evidence:

- `.local/native-renderer/automated/fh1-pass-phase-profile-1x`
- `.local/native-renderer/automated/fh1-pass-phase-profile-1x-qualified-save`

They supplied the shader pack without seeding the analysis catalog and rejected
offline shaders. The automation root cause is now fixed.

An earlier instrumented build also existed only under
`out/build/win-amd64-release/rexglue-artifacts`; the preview loads
`out/build/win-amd64-release/rexgpu-fh1.dll`. Always verify or copy the artifact
before testing. The two DLLs match at this checkpoint.

## Rejected or low-leverage directions

- **Another direct-host resolve shortcut:** measured resolves are microseconds,
  while retained draw families consume 0.5–1.5 ms each. Revisit only if a new
  trace contradicts this.
- **More shader-only substitutions:** they retain draw count and most Xenos
  material/resource setup. Broad experimental substitutions also produced
  foliage alpha, grass, sky, font, minimap, and modal corruption.
- **Re-enable the disabled candidate block:** `pipeline_cache.cpp` has
  `kFh1UseHandwrittenShaderSubstitutions = false`. Keep it false. Delete that
  dead experimental branch and its unused generated shaders after confirming
  which separately governed vertex substitutions are still proven.
- **Optical flow, fake/duplicate frames, or FSR:** explicitly out of scope.
- **A general Xenos renderer:** explicitly out of scope.
- **Claiming offline shaders make the path native:** they remove runtime shader
  work but not Xenos draw execution.

## Next tests and implementation ideas, in order

1. **Run the optimized build at 2x three times.** Use the complete qualified 2x
   pack and the same route. Determine whether skipping unused execution-key work
   lifts the existing 2x median and whether shader/pipeline misses remain zero.
2. **Delete disabled broad shader-substitution code.** Remove only the branch
   guarded by `kFh1UseHandwrittenShaderSubstitutions`, its counters, and unused
   bytecode includes. Preserve the separately enabled world-lit, world-lit-UV2,
   depth-mesh, tone-map, and velocity work. Build and run the visual matrix.
3. **Prototype one FH1-native scene-family executor for attachment
   `7336ADFF531DCC00`.** Start with one of the exact high-count families above.
   The success criterion is retiring its repeated Xenos material setup and draw
   submissions, not replacing only its shader bytecode. First test whether a
   stable sequence shares enough PSO, root-signature, geometry, texture, and
   constant layout to use instancing or `ExecuteIndirect`. If not, extract the
   title's authoritative prepared scene/instance data at its FH1 owner and
   submit that directly.
4. **Add retirement counters with the prototype.** Record candidate draws,
   native batches, Xenos draws suppressed, compatibility prep skipped, native
   GPU time, and fail-closed fallbacks. A candidate is useful only when the
   counters prove material Xenos work disappeared.
5. **Gate every candidate visually.** Required captures: title/loading, foliage
   leaves, grass, sky, open-world HUD/minimap, SELECT map and road layer, pause
   fonts, quit modal/background, race HUD, and representative night/weather.
   Reject on any difference not understood and accepted.
6. **Collect a matched Xenia comparison.** Use three warm runs per product with
   the same save, route, internal resolution, output size, VSync state, and an
   external present-time collector. Record exact Xenia Canary revision and all
   settings. Existing Xenia `577fb8e` visual-update samples are useful context,
   not a matched performance claim.
7. **Test minimum hardware only after scene retirement.** Use fixed CPU/GPU
   tiers and the same route. Report frame time, GPU time, one-percent low,
   shader/pipeline misses, memory, and visual gates. The final goal needs a
   measured advantage, not an architectural assumption.

## Resume commands

Build the FH1 backend:

```powershell
cmake --build out/build/win-amd64-release --config Release --target rexgpu-fh1
Copy-Item -LiteralPath out/build/win-amd64-release/rexglue-artifacts/rexgpu-fh1.dll -Destination out/build/win-amd64-release/rexgpu-fh1.dll -Force
```

Run the 1x automated shipping route (supplying the pack now auto-seeds its
analysis catalog):

```powershell
python tools/run-fh1-render-test.py config/render-tests/fh1-open-world-performance.fh1test `
  --state-root .local/native-renderer/automated/fh1-native-1x-complete-shipping.state `
  --output .local/native-renderer/automated/<new-run-name> `
  --shader-pack .local/native-renderer/4D5309C9.fh1-native-v2.10DE.09.1x1.complete-current.pnsp `
  --shader-capture-dir .local/native-renderer/<new-capture-name> `
  --seed-pipeline-prewarm --require-zero-shader-misses `
  --game-argument=--draw_resolution_scale_x=1 `
  --game-argument=--draw_resolution_scale_y=1 --timeout 180
```

Validate the automation and documentation:

```powershell
python -m unittest tools.tests.test_run_fh1_render_test
python tools/check-markdown-links.py
```

For a manual AppData-save run, first ensure no `pinyon_shift` process is
running and verify
`C:\Users\neri\AppData\Local\PinyonShift\source\0.1.0\.local\preview\user`
contains `ForzaProfile\ForzaProfile`. Then use:

```powershell
.\tools\launch-preview.ps1 -StateRoot C:\Users\neri\AppData\Local\PinyonShift\source\0.1.0\.local\preview
```

Never copy, reset, move, delete, or overwrite the save merely to launch a test.

## Repository state

The working tree and the `thirdparty/shiftglue-sdk` submodule are heavily dirty
with the accumulated renderer work. No commit was made for this checkpoint.
Preserve unrelated and pre-existing changes. Before editing, inspect both root
and submodule diffs. The active goal must remain open until native scene
retirement, visual correctness, matched performance, minimum-hardware evidence,
and source-rendered uncapped presentation are all satisfied.
