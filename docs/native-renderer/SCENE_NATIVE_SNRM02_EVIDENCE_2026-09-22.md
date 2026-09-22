# SNR-M02 title counter wait: runtime producer join

The sustained Recaro race trace at source frames 5999–6001 identifies the
producer of the word polled by `sub_823E91F0` / `sub_829F04A8`. The title's
virtual pointer `0xffca4000` maps to physical `0x1fca5000`. ReXGlue's
`CommandProcessor::ExecutePacketType3_EVENT_WRITE_SHD` writes that physical
word while consuming the PM4 stream. The ring read-pointer writeback is at
`0x1fca503c`; scratch-register writebacks observed at `0x1fca4000` and nearby
addresses are separate. Comparing the virtual and physical numeric suffixes
without resolving the heap mapping initially produced a false match.

The final normal-exit replay, with the source-frame and physical-address trace
switches enabled, recorded 37 outer waits, 6 polling waits, 67 calls to the
title packet publisher, and 65 host stores to the published word. None of the
title publisher calls met its conditional direct-store test; no wait used the
recovery branch. All six polling waits started below their requested position,
and each contained an `EVENT_WRITE_SHD` store of the exact requested value
before its observed exit. The six waits totaled 43.124 ms wall time across
three source frames (individual waits 2.20–10.59 ms). The host log records the
raw little-endian store value; the verifier byte-swaps it to the title-visible
word before joining values and monotonic timestamps. The replay emitted all
seven expected PPMs and exited normally.

Reproduce from the verified AppData preview state with
`config/render-tests/fh1-race-sustained.fh1test`, a fresh output directory,
and these game arguments:

```text
--pinyon_shift_snr_m02_trace_source_frame=6000
--snr_m02_host_trace_source_frame=6000
--snr_m02_host_trace_physical_address=533352448
--log_file=<absolute path to a fresh log>
--log_max_file_size_mb=100
```

Run `python tools/verify-snr-m02-counter-join.py <log>` afterward. The local
evidence is `.local/native-renderer/snrm02/counter-wait-run-e.log` and its
`counter-wait-run-e/` captures. Earlier bounded replays independently showed
the same six polling waits and disabled title direct store; they were used to
identify and then eliminate the wrong ring-pointer and scratch hypotheses.

This is a **command-consumption** dependency in the current ReXGlue backend:
the title waits for a PM4 event memory write to become guest-visible. The
`EVENT_WRITE_SHD` implementation writes guest memory while parsing that packet;
this trace does not establish a hardware fence or that all preceding GPU work
has completed. Delaying or bypassing the title wait could let it run ahead of
the command processor and change buffering, route timing, or visible output.
The earlier unconditional sleep trial caused slower swaps and route divergence
and remains removed. SNR-M02 is open for a bounded pacing experiment with
matched control/replay and consumed-swap tail comparisons; no performance
improvement is claimed from the read-only hooks.
