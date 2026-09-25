#pragma once

#include <cstdint>

namespace pinyon_shift::scheduler {

// Thread classes for the Ryzen 3 5300U (4C/8T, 15W) scheduling policy.
// Telemetry shows GUEST_CPU_STALL causes 91.1% of open-world hitches:
// background BigZip VFS decompression workers monopolize the physical
// cores and starve the main guest emulation tick.
enum class ThreadClass : uint8_t {
  // Latency-critical: main guest simulation tick and D3D12 render/present
  // path. Pinned to cores 0 & 1 with THREAD_PRIORITY_HIGHEST.
  Foreground,
  // Throughput work: BigZip VFS decompression workers, shader translation,
  // and pipeline compile workers. Restricted to compute cores 2..7 with
  // THREAD_PRIORITY_BELOW_NORMAL so they can never preempt Foreground.
  Background,
  // Audio throughput / low latency: Audio Worker and XMA Decoder.
  // Pinned to compute cores with THREAD_PRIORITY_NORMAL so streaming bursts
  // never starve audio packets or create underrun hitches.
  Audio,
};

// Resolves the process affinity masks for each class, intersected with the
// process affinity mask and clamped to the active processor count.
// Returns false when affinity cannot be managed (fewer than 2 logical
// processors); priorities are still applied in that case.
bool ResolveAffinityMasks(uint64_t* foreground_mask,
                          uint64_t* background_mask);

// Applies the class policy to the calling thread. Safe to call repeatedly;
// affinity is only reprogrammed when it differs from the requested mask.
void PinCurrentThread(ThreadClass thread_class);

// Applies the class policy to an arbitrary process thread handle.
// `thread_handle` must have THREAD_SET_INFORMATION access.
// Returns true when both affinity and priority were programmed.
bool PinThreadHandle(void* thread_handle, ThreadClass thread_class,
                     uint64_t affinity_mask);

// Classifies a host-visible thread name (SetThreadDescription) into a
// scheduling class. Returns true and fills `thread_class` when the thread
// is managed by this policy; returns false for threads left untouched
// (UI, input, kernel dispatch, timer queues, unnamed threads).
bool ClassifyThreadName(const wchar_t* name, ThreadClass* thread_class);

// Well-known SDK thread names managed by this policy.
bool IsForegroundThreadName(const wchar_t* name);
bool IsBackgroundThreadName(const wchar_t* name);
bool IsAudioThreadName(const wchar_t* name);

// Ensures Windows scheduler timer resolution is set to 1ms via timeBeginPeriod(1)
// during initialization and restored via timeEndPeriod(1) at shutdown.
void InitializeScheduler();
void ShutdownScheduler();

}  // namespace pinyon_shift::scheduler
