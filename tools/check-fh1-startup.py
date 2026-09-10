"""Compile actual fence/prewarm control flow against deterministic failure fakes.

Run in the release build environment; no GPU, worker threads or game data needed.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def block(source, marker):
    start = source.index(marker)
    depth = 0
    for end in range(source.index('{', start), len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if not depth:
            return source[start:end + 1]
    raise AssertionError(f'unterminated block: {marker}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'thirdparty/shiftglue-sdk'
    cp = (root / 'src/graphics/d3d12/command_processor.cpp').read_text(encoding='utf-8')
    pc = (root / 'src/graphics/d3d12/pipeline_cache.cpp').read_text(encoding='utf-8')
    methods = '\n'.join(block(cp, marker) for marker in (
        'bool D3D12CommandProcessor::AwaitFence(',
        'bool D3D12CommandProcessor::CheckSubmissionFence('))
    workers = block(pc, 'void PipelineCache::StartCreationThreads(')
    start = pc.index('  // Create only selected pipelines;')
    warmup = pc[start:pc.index('    size_t pipelines_created', start)] + '\n  }'
    selection = pc[pc.index('      std::set<uint64_t> allowed_pipelines;'):
                   pc.index('  // Retain a legacy variant')]
    selection = selection[:selection.rfind('    }')]
    # The filtered-work guard must not wrap storage finalization or skip later setup.
    assert pc.index('  // Storage finalization') > pc.index('    size_t pipelines_created')
    assert 'if (!pipeline_stored_descriptions.empty())' in pc[pc.index('  // Storage finalization'):]
    assert 'if (!CheckSubmissionFence(' in block(cp, 'bool D3D12CommandProcessor::BeginSubmission(')
    assert 'if (!CheckSubmissionFence(query_submission))' in cp
    assert 'AwaitAllQueueOperationsCompletion(true)' in block(cp, 'void D3D12CommandProcessor::ShutdownContext(')
    harness = r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <deque>
#include <functional>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <vector>
using HRESULT = int32_t;
using UINT64 = uint64_t;
using DWORD = uint32_t;
constexpr HRESULT S_OK=0, E_FAIL=-1, DXGI_ERROR_DEVICE_REMOVED=-2;
constexpr DWORD WAIT_OBJECT_0=0, WAIT_TIMEOUT=258, WAIT_FAILED=0xffffffff;
constexpr DWORD ERROR_INVALID_FUNCTION=1;
#define FAILED(x) ((x)<0)
#define SUCCEEDED(x) ((x)>=0)
int errors=0;
#define REXGPU_ERROR(...) (++errors)
#define REXGPU_WARN(...) ((void)0)
#define REXGPU_INFO(...) ((void)0)
#define PROFILE_CMD_BUFFER_STALL() ((void)0)
struct Event { int waits=0; std::function<DWORD()> next; };
DWORD WaitForSingleObject(Event* event, DWORD ms) {
  assert(ms==100); assert(++event->waits<10); return event->next();
}
DWORD GetLastError(){return 5;}
struct ID3D12Fence {
  uint64_t completed=0, registered=0;
  HRESULT event_result=S_OK;
  int registrations=0;
  uint64_t GetCompletedValue(){return completed;}
  HRESULT SetEventOnCompletion(uint64_t value, Event*) {
    ++registrations; registered=value; return event_result;
  }
};
struct Device { HRESULT reason=S_OK; HRESULT GetDeviceRemovedReason(){return reason;} };
struct Queue { HRESULT result=S_OK; int signals=0;
  HRESULT Signal(ID3D12Fence*, uint64_t){++signals; return result;}
};
struct Provider { Device device; Queue queue;
  Device* GetDevice(){return &device;} Queue* GetDirectQueue(){return &queue;}
};
struct Resource { void Release(){} };
struct Allocator { uint64_t last_usage_submission=0; Allocator* next=nullptr; };
struct Cache { int updates=0; void CompletedSubmissionUpdated(uint64_t=0){++updates;} };
struct D3D12CommandProcessor {
  Provider provider; Event event; ID3D12Fence queue_fence, submission_fence;
  Event* fence_completion_event_=&event;
  ID3D12Fence* queue_operations_since_submission_fence_=&queue_fence;
  ID3D12Fence* submission_fence_=&submission_fence;
  bool running=true, device_removed_=false, submission_open_=false, end_result=true;
  bool queue_operations_done_since_submission_signal_=false;
  uint64_t queue_operations_since_submission_fence_last_=0;
  uint64_t submission_current_=2, submission_completed_=0;
  Allocator *command_allocator_submitted_first_=nullptr,*command_allocator_submitted_last_=nullptr;
  Allocator *command_allocator_writable_last_=nullptr,*command_allocator_writable_first_=nullptr;
  std::deque<std::pair<int,uint64_t>> view_bindless_one_use_descriptors_;
  std::deque<std::pair<uint64_t,Resource*>> resources_for_deletion_;
  Cache cache; Cache *shared_memory_=&cache,*render_target_cache_=&cache;
  Cache *primitive_processor_=&cache,*texture_cache_=&cache;
  int retirements=0;
  bool IsShutdownRequested() const {return !running;}
  Provider& GetD3D12Provider(){return provider;}
  bool EndSubmission(bool){return end_result;}
  void RetireModernZPDQueries(){++retirements;}
  void RetireNativeGuestOutputGpuTimings(){++retirements;}
  void ReleaseViewBindlessDescriptorImmediately(int){}
  void LogDeviceRemovalDiagnostics(Device*,HRESULT){++errors;}
  bool AwaitFence(ID3D12Fence*,uint64_t,bool);
  bool CheckSubmissionFence(uint64_t,bool=false);
};
/* FENCE METHODS */
size_t cores=8; int configured=-1, attempts=0, fail_at=-1;
int cancel_at=-1; D3D12CommandProcessor* owner=nullptr;
#define REXCVAR_GET(name) configured
namespace rex {
namespace chrono { struct Clock { static uint64_t QueryHostTickCount(){return 0;} }; }
namespace thread {
size_t logical_processor_count(){return cores;}
struct Thread {
  struct Parameters {};
  static std::unique_ptr<Thread> Create(Parameters, std::function<void()>) {
    int index=attempts++;
    if(index==cancel_at) owner->running=false;
    return index==fail_at ? nullptr : std::make_unique<Thread>();
  }
  void set_name(const char*){}
};
}}
struct PipelineStoredDescription { uint64_t description_hash=1; };
struct PipelineCache {
  D3D12CommandProcessor command_processor_;
  std::vector<std::unique_ptr<rex::thread::Thread>> creation_threads_;
  void CreationThread(size_t){}
  void StartCreationThreads(size_t);
  void Warm(size_t stored, size_t selected) {
    std::vector<PipelineStoredDescription> pipeline_stored_descriptions(stored), chosen(selected);
    const auto* pipeline_prewarm_descriptions=&chosen;
    size_t logical_processor_count=cores ? cores : 6;
    /* WARMUP */
  }
  size_t Select(const std::string& rows) {
    std::istringstream allowlist(rows); std::string line;
    std::vector<PipelineStoredDescription> pipeline_stored_descriptions{{1},{2}};
    std::vector<PipelineStoredDescription> fh1_pipeline_prewarm_descriptions;
    const auto* pipeline_prewarm_descriptions=&pipeline_stored_descriptions;
    std::set<uint64_t> fh1_execution_allowlist_,fh1_copy_allowlist_;
    bool fh1_prewarm_manifest_loaded_=false;
    /* SELECTION */
    assert(fh1_prewarm_manifest_loaded_);
    return pipeline_prewarm_descriptions->size();
  }
};
/* WORKERS */
int main() {
  // Actual CheckSubmissionFence: all HRESULT combinations, correct order and no false completion.
  for(HRESULT signal : {S_OK,E_FAIL}) for(HRESULT registration : {S_OK,E_FAIL}) {
    D3D12CommandProcessor c; c.queue_operations_done_since_submission_signal_=true;
    c.provider.queue.result=signal; c.queue_fence.event_result=registration;
    c.submission_fence.completed=1;
    c.event.next=[&]{assert(c.queue_fence.registrations==1);c.queue_fence.completed=1;return WAIT_OBJECT_0;};
    bool ok=c.CheckSubmissionFence(2);
    assert(ok==(signal==S_OK && registration==S_OK));
    assert(c.provider.queue.signals==1);
    assert(c.queue_fence.registrations==(signal==S_OK));
    assert(c.event.waits==int(ok));
    assert(c.queue_operations_done_since_submission_signal_==!ok);
    assert(c.submission_completed_==uint64_t(ok));
    assert(ok || (c.retirements==0 && c.cache.updates==0));
  }
  // A stale wake and timeout are not completion; registration occurs exactly once.
  { D3D12CommandProcessor c; int step=0;
    c.event.next=[&]{if(++step==1)return WAIT_OBJECT_0;if(step==2)return WAIT_TIMEOUT;
      c.submission_fence.completed=1;return WAIT_OBJECT_0;};
    assert(c.CheckSubmissionFence(1));assert(c.event.waits==3);
    assert(c.submission_fence.registrations==1 && c.submission_completed_==1);
  }
  // Wait failure, cancellation and loss leave pending work unretired.
  for(int kind=0;kind<4;++kind) {
    D3D12CommandProcessor c;
    c.event.next=[&]{if(kind==0)return WAIT_FAILED;
      if(kind==1)c.running=false;
      if(kind==2)c.submission_fence.completed=UINT64_MAX;
      if(kind==3)c.provider.device.reason=E_FAIL;
      return WAIT_TIMEOUT;};
    assert(!c.CheckSubmissionFence(1));
    assert(c.submission_completed_==0 && c.retirements==0 && c.cache.updates==0);
  }
  { D3D12CommandProcessor c;c.running=false;
    assert(!c.CheckSubmissionFence(1));assert(c.submission_fence.registrations==0);
    c.event.next=[&]{c.submission_fence.completed=1;return WAIT_OBJECT_0;};
    assert(c.CheckSubmissionFence(1,true)); // shutdown still drains before freeing resources
  }
  { D3D12CommandProcessor c;c.submission_fence.completed=UINT64_MAX;
    assert(!c.CheckSubmissionFence(0));assert(c.retirements==0 && c.submission_completed_==0);
  }
  { D3D12CommandProcessor c;c.submission_open_=true;c.end_result=false;
    assert(!c.CheckSubmissionFence(2));assert(c.retirements==0);
  }
  // Empty stored/selected sets, one job, CPU/configured caps, zero CPU report, existing workers.
  for(size_t cpu : {size_t(0),size_t(1),size_t(8),size_t(128)})
    for(int config : {-1,0,2,32}) for(size_t jobs : {size_t(0),size_t(1),size_t(3),size_t(200)}) {
      PipelineCache p;owner=&p.command_processor_;cores=cpu;configured=config;attempts=0;
      p.Warm(0,0);assert(attempts==0);
      p.Warm(200,0);assert(attempts==0);
      p.Warm(200,jobs);
      size_t count=std::min(jobs,cpu?cpu:6);
      size_t expected=std::min(count?count-1:0,size_t(config<0?32:config));
      assert(p.creation_threads_.size()==expected);
      p.Warm(200,0);assert(p.creation_threads_.size()==expected);
    }
  cores=8;configured=-1;
  for(int failure : {0,2}) {
    PipelineCache p;owner=&p.command_processor_;attempts=0;fail_at=failure;
    p.Warm(200,200);assert(attempts==failure+1);assert(p.creation_threads_.size()==size_t(failure));
  }
  fail_at=-1;
  { PipelineCache p;owner=&p.command_processor_;attempts=0;cancel_at=1;
    p.Warm(200,200);assert(attempts==2 && p.creation_threads_.size()==2);
    p.Warm(200,200);assert(attempts==2);
  }
  { PipelineCache p;int before=errors;
    assert(p.Select("")==0);assert(errors==before); // valid header, no requested PSOs
    assert(p.Select("P 0000000000000003\n")==0);assert(errors==before+1);
    assert(p.Select("P 0000000000000001\nP 0000000000000002\n")==2);
    assert(errors==before+1);
  }
}
'''
    for key, value in {'FENCE METHODS': methods, 'WORKERS': workers,
                       'WARMUP': warmup, 'SELECTION': selection}.items():
        harness = harness.replace(f'/* {key} */', value)
    with tempfile.TemporaryDirectory(prefix='fh1-startup-') as directory:
        cpp, exe = Path(directory) / 'check.cpp', Path(directory) / 'check.exe'
        cpp.write_text(harness)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Production fence waits, cancellation, prewarm selection/caps and worker failures: passed')


if __name__ == '__main__':
    main()
