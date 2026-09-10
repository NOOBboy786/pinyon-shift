# GitHub user issue pass — 2026-09-10

Reviewed all 11 open issues and their available comments/attachments. No issues
were closed or replies posted. Changes below target the next build; they have
not been released as a new preview or verified on reporters' machines.

| Issue | Finding and action | Remaining evidence/work |
| --- | --- | --- |
| [313](https://github.com/arcanite24/pinyon-shift/issues/313) | The attached JSON says **preview configuration failed**, not a download failure. Preview.3 omits required CMake source inputs and uses checkout-only SDK paths. Both are already fixed on dev; packaging now fails for missing required inputs, with coverage for literal CMake inputs. | Test the next packaged build. The report omits the underlying CMake error, so attribution is provisional. |
| [312](https://github.com/arcanite24/pinyon-shift/issues/312) | Same configuration-stage symptom on preview.3. The packaged-source corrections above apply. | Need the actual CMake error if it persists. |
| [210](https://github.com/arcanite24/pinyon-shift/issues/210) | CMake rejects preset schema version 6. Provision a SHA256-pinned CMake 3.31.10 instead of depending on the Visual Studio bundled version. Local developer fallback checks the required minimum 3.25. | Reporter confirmation with the next launcher. |
| [45](https://github.com/arcanite24/pinyon-shift/issues/45) | Attachment only says code-generator build failed. Four configure/build steps now persist complete stdout/stderr logs; setup-error.json includes exit code, log path and output tail. | Actual compiler/linker error still needed; diagnostics improvement is not a compiler fix. |
| [62](https://github.com/arcanite24/pinyon-shift/issues/62) | Wrapper error only. CMake provisioning and preserved configure output improve recovery/diagnosis. | Underlying CMake error still needed. |
| [69](https://github.com/arcanite24/pinyon-shift/issues/69) | Staging report omits the failure. Existing setup already rejects a running game; full build logs now persist. | Cannot distinguish lock, copy or other failure from provided lines. |
| [212](https://github.com/arcanite24/pinyon-shift/issues/212) | Only unused-parameter warnings and Ninja's final failure are shown. Full logs now preserve the real failure. | First failed command/compiler error needed. |
| [311](https://github.com/arcanite24/pinyon-shift/issues/311) | Packaged launcher supports `PINYON_SHIFT_INSTALL_ROOT`, keeping source, local tools, extracted game and default state on the selected drive. README documents launching this way. | Partial: no graphical folder selector or portable relocation/export. Existing installs/saves are not moved; VS Build Tools still use system storage. |
| [224](https://github.com/arcanite24/pinyon-shift/issues/224) | A crash ID and 0xC0000409 without the diagnostic ZIP do not identify the failure. | Diagnostic ZIP and reproduction steps needed. No speculative crash patch. |
| [121](https://github.com/arcanite24/pinyon-shift/issues/121) | Existing native-renderer/cache changes may help, but no matching AMD intro run exists. Earlier maintainer request for repeat-route logs remains unanswered. | Reporter hardware/preset-specific timing required; not closed by NVIDIA Carson results. |
| [310](https://github.com/arcanite24/pinyon-shift/issues/310) | macOS request (plus Linux comment) is a platform project, not an isolated bug. | Non-Windows graphics, runtime and launcher work remain out of this fix pass. |

## Validation

- Release-contract checks exercise native stderr on both successful and failing
  commands, retained exit status, old-CMake rejection, local-CMake preference,
  pinned downloads and packaged CMake source coverage.
- Pinned CMake archive downloaded and verified against the official Kitware
  release asset digest; both project and SDK preset inventories parse.
- Release launcher builds with zero warnings/errors. Packaged payload validation
  checks source inclusion; no full fresh disc-to-game rebuild is claimed.
- The running gameplay/discovery session and unrelated SDK edits remain intact.

The new issue form asks for the exact release and first underlying error so
future reports contain enough evidence to investigate.
