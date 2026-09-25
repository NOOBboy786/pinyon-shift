// Pinyon Shift host thread scheduler.
//
// Reserves logical processors 0 & 1 for the latency-critical guest tick
// and D3D12 render/present path, and confines throughput workers
// (BigZip VFS decompression, XMA/audio decode, pipeline compilers) to
// logical processors 2 & 3. The ReXGlue SDK ships with
// `ignore_thread_affinities=true`, so every guest and worker thread
// floats across all cores by default; on the 4C/8T 15W APU that lets
// decompression workers starve the main tick (GUEST_CPU_STALL, 91.1% of
// hitches). This host-side policy restores the split without touching
// the 2,048-draw command-processor chunking that resolved the TDR hang.

#include "pinyon_shift_thread_scheduler.h"

#if defined(_WIN32)

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>

#include <atomic>
#include <cwchar>
#include <cwctype>

namespace pinyon_shift::scheduler {
namespace {

constexpr int kForegroundPriority = THREAD_PRIORITY_HIGHEST;
constexpr int kBackgroundPriority = THREAD_PRIORITY_BELOW_NORMAL;
constexpr int kAudioPriority = THREAD_PRIORITY_NORMAL;

// Logical-processor split: foreground owns 0 & 1, background widens to 2..7 (mask 0xFC on 8-LP systems).
constexpr uint64_t kForegroundMask = 0x3ull;
constexpr uint64_t kBackgroundMask = 0xFCull;

static std::atomic<int> g_timer_ref_count{0};
static HMODULE g_winmm_module = nullptr;

DWORD_PTR ActiveProcessorMask() {
  DWORD_PTR process_mask = 0;
  DWORD_PTR system_mask = 0;
  if (!GetProcessAffinityMask(GetCurrentProcess(), &process_mask,
                              &system_mask)) {
    return 0;
  }
  return process_mask;
}

bool NameEquals(const wchar_t* name, const wchar_t* expected) {
  if (!name || !expected) {
    return false;
  }
  while (*expected) {
    if (std::towupper(*name) != std::towupper(*expected)) {
      return false;
    }
    ++name;
    ++expected;
  }
  return *name == L'\0';
}

bool NameStartsWith(const wchar_t* name, const wchar_t* prefix) {
  if (!name || !prefix) {
    return false;
  }
  while (*prefix) {
    if (std::towupper(*name) != std::towupper(*prefix)) {
      return false;
    }
    ++name;
    ++prefix;
  }
  return true;
}

}  // namespace

void InitializeScheduler() {
  if (g_timer_ref_count.fetch_add(1, std::memory_order_acq_rel) == 0) {
    g_winmm_module = LoadLibraryA("winmm.dll");
    if (g_winmm_module) {
      using TimeBeginPeriodFn = UINT(WINAPI*)(UINT);
      auto time_begin = reinterpret_cast<TimeBeginPeriodFn>(
          GetProcAddress(g_winmm_module, "timeBeginPeriod"));
      if (time_begin) {
        time_begin(1);
      }
    }
  }
}

void ShutdownScheduler() {
  int count = g_timer_ref_count.load(std::memory_order_acquire);
  while (count > 0) {
    if (g_timer_ref_count.compare_exchange_weak(count, count - 1,
                                                std::memory_order_acq_rel)) {
      if (count == 1) {
        if (g_winmm_module) {
          using TimeEndPeriodFn = UINT(WINAPI*)(UINT);
          auto time_end = reinterpret_cast<TimeEndPeriodFn>(
              GetProcAddress(g_winmm_module, "timeEndPeriod"));
          if (time_end) {
            time_end(1);
          }
          FreeLibrary(g_winmm_module);
          g_winmm_module = nullptr;
        }
      }
      break;
    }
  }
}

bool ResolveAffinityMasks(uint64_t* foreground_mask,
                          uint64_t* background_mask) {
  const DWORD_PTR process_mask = ActiveProcessorMask();
  if (process_mask == 0) {
    return false;
  }
  DWORD active_count = 0;
  for (DWORD_PTR bit = process_mask; bit; bit >>= 1) {
    active_count += (bit & 1u);
  }
  if (active_count < 2) {
    return false;
  }
  uint64_t foreground = 0;
  if (active_count == 2) {
    // Dedicated split for 2-LP systems: 1 LP foreground, 1 LP background.
    // Pick the lowest active logical processor for foreground.
    foreground = process_mask & (~process_mask + 1);
  } else {
    // If standard foreground mask (cores 0 & 1) matches at least 2 active bits, use it.
    const uint64_t preferred = kForegroundMask & process_mask;
    DWORD preferred_count = 0;
    for (uint64_t bit = preferred; bit; bit >>= 1) {
      preferred_count += (bit & 1u);
    }
    if (preferred_count >= 2) {
      foreground = preferred;
    } else {
      // Pick the lowest two active logical processors from process_mask.
      const uint64_t bit1 = process_mask & (~process_mask + 1);
      const uint64_t rem = process_mask & ~bit1;
      const uint64_t bit2 = rem & (~rem + 1);
      foreground = bit1 | bit2;
    }
  }
  // Widen background to all remaining compute LPs (e.g. process_mask & ~foreground,
  // yielding mask 0xFC on 8-LP systems like the Ryzen 3 5300U).
  uint64_t background = process_mask & ~foreground;
  if (background == 0 || background == foreground) {
    background = kBackgroundMask & process_mask;
  }
  if (foreground == 0 || background == 0) {
    return false;
  }
  if (foreground_mask) {
    *foreground_mask = foreground;
  }
  if (background_mask) {
    *background_mask = background;
  }
  return true;
}

bool PinThreadHandle(void* thread_handle, ThreadClass thread_class,
                     uint64_t affinity_mask) {
  HANDLE handle = static_cast<HANDLE>(thread_handle);
  if (!handle) {
    return false;
  }
  int priority = kBackgroundPriority;
  if (thread_class == ThreadClass::Foreground) {
    priority = kForegroundPriority;
  } else if (thread_class == ThreadClass::Audio) {
    priority = kAudioPriority;
  }
  BOOL priority_ok = SetThreadPriority(handle, priority);
  BOOL affinity_ok = TRUE;
  if (affinity_mask != 0) {
    affinity_ok = SetThreadAffinityMask(handle,
                                        static_cast<DWORD_PTR>(affinity_mask)) != 0;
  }
  return priority_ok && affinity_ok;
}

void PinCurrentThread(ThreadClass thread_class) {
  uint64_t foreground = 0;
  uint64_t background = 0;
  uint64_t mask = 0;
  if (ResolveAffinityMasks(&foreground, &background)) {
    mask = thread_class == ThreadClass::Foreground ? foreground : background;
  }
  PinThreadHandle(GetCurrentThread(), thread_class, mask);
}

bool IsForegroundThreadName(const wchar_t* name) {
  // "Main XThread" is the guest simulation tick (kernel_state.cpp).
  // "GPU Commands" is the D3D12 command-processor worker that owns the
  // chunked draw submission path; "GPU VSync" owns present pacing.
  // (graphics_system.cpp, command_processor.cpp).
  return NameStartsWith(name, L"Main XThread") ||
         NameStartsWith(name, L"GPU Commands") ||
         NameStartsWith(name, L"GPU VSync");
}

bool IsAudioThreadName(const wchar_t* name) {
  // Audio decode runs on "Audio Worker" (audio_system.cpp) and "XMA Decoder"
  // (xma_decoder.cpp). Keep at THREAD_PRIORITY_NORMAL so streaming bursts
  // never starve audio packets or create underrun hitches.
  return NameStartsWith(name, L"Audio Worker") ||
         NameStartsWith(name, L"XMA Decoder");
}

bool IsBackgroundThreadName(const wchar_t* name) {
  // Guest worker threads (XThreadXXXX, excluding the main tick handled by
  // TID) run title code including BigZip VFS decompression. Pipeline
  // compilers and translation workers stay off foreground cores.
  return NameStartsWith(name, L"XThread") ||
         NameStartsWith(name, L"D3D12 Pipelines") ||
         NameStartsWith(name, L"Shader Translation") ||
         NameStartsWith(name, L"D3D12 Storage writer") ||
         NameStartsWith(name, L"Vulkan Pipelines") ||
         NameStartsWith(name, L"Vulkan Storage writer");
}

bool ClassifyThreadName(const wchar_t* name, ThreadClass* thread_class) {
  if (!name || !thread_class) {
    return false;
  }
  if (IsForegroundThreadName(name)) {
    *thread_class = ThreadClass::Foreground;
    return true;
  }
  if (IsAudioThreadName(name)) {
    *thread_class = ThreadClass::Audio;
    return true;
  }
  if (IsBackgroundThreadName(name)) {
    *thread_class = ThreadClass::Background;
    return true;
  }
  return false;
}

}  // namespace pinyon_shift::scheduler

#else  // !defined(_WIN32)

namespace pinyon_shift::scheduler {

void InitializeScheduler() {}
void ShutdownScheduler() {}

bool ResolveAffinityMasks(uint64_t* foreground_mask,
                          uint64_t* background_mask) {
  if (foreground_mask) {
    *foreground_mask = 0;
  }
  if (background_mask) {
    *background_mask = 0;
  }
  return false;
}

bool PinThreadHandle(void*, ThreadClass, uint64_t) { return false; }

void PinCurrentThread(ThreadClass) {}

bool IsForegroundThreadName(const wchar_t*) { return false; }
bool IsAudioThreadName(const wchar_t*) { return false; }
bool IsBackgroundThreadName(const wchar_t*) { return false; }

bool ClassifyThreadName(const wchar_t*, ThreadClass*) { return false; }

}  // namespace pinyon_shift::scheduler

#endif  // defined(_WIN32)
