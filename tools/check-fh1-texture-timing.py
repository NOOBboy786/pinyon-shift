"""Compile production timestamp allocation/retirement guards with a fake query sink."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    source = (repo / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
    invalid_start = source.index('      if (!record.family || copy_start < start || end < copy_start) {')
    invalid_pass = source[invalid_start:source.index('\n      }', invalid_start) + len('\n      }')]
    methods = []
    for name in ['bool D3D12CommandProcessor::IsFh1GpuWorkTimingSampleFrame() const',
                 'D3D12CommandProcessor::Fh1GpuWorkTiming\n',
                 'D3D12CommandProcessor::Fh1GpuWorkTiming\nD3D12CommandProcessor::BeginFh1RenderTargetTransferTiming(',
                 'void D3D12CommandProcessor::FinishFh1RenderTargetTransferTiming(',
                 'void D3D12CommandProcessor::AdvanceFh1GpuWorkTiming(']:
        start = source.index(name)
        depth = 0
        for end in range(source.index('{', start), len(source)):
            depth += (source[end] == '{') - (source[end] == '}')
            if not depth:
                methods.append(source[start:end + 1])
                break
    harness = r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <vector>
#include <iostream>
bool enabled = true;
bool Fh1GpuCorpusEnabled() { return enabled; }
constexpr int D3D12_QUERY_TYPE_TIMESTAMP = 0;
struct D3D12TextureCache { struct TextureKey { bool is_valid = true; }; };
struct D3D12CommandProcessor {
 struct Fh1GpuWorkTiming { uint64_t frame=0, submission=0; uint32_t record=UINT32_MAX; };
 struct Heap { bool available=true; explicit operator bool() const {return available;} int Get(){return 1;} } native_guest_output_gpu_query_heap_;
 struct Sink { std::vector<uint32_t> queries; void D3DEndQuery(int,int,uint32_t q){queries.push_back(q);} } deferred_command_list_;
 struct Record { D3D12TextureCache::TextureKey texture_key; uint64_t frame=0; uint32_t query_offset=0,transfer_count=0; bool work_complete=false,render_target_transfer=false,resolve_clear=false; };
 struct Slot { uint64_t submission=0; uint32_t record_count=0; std::array<Record,2> records; };
 static constexpr uint32_t kQueueFrames=2, kFh1GpuPassTimingCapacity=2,
     kNativeGuestOutputGpuQueriesPerFrame=5, kGpuTimingQueriesPerFrame=11;
 uint64_t frame_current_=1, submission_current_=4, observation_frame_sequence_=60;
 uint64_t fh1_gpu_pass_timing_drops_=0;
 uint64_t fh1_gpu_pass_timing_busy_drops_=0, fh1_gpu_pass_timing_capacity_drops_=0,
     fh1_gpu_pass_timing_interrupted_drops_=0, fh1_gpu_pass_timing_invalid_drops_=0;
 std::array<Slot,kQueueFrames> fh1_gpu_pass_timing_slots_{};
 Fh1GpuWorkTiming BeginFh1TextureLoadTiming(const D3D12TextureCache::TextureKey&);
 void AdvanceFh1GpuWorkTiming(const Fh1GpuWorkTiming&,bool);
 bool IsFh1GpuWorkTimingSampleFrame() const;
 Fh1GpuWorkTiming BeginFh1RenderTargetTransferTiming(uint32_t,bool);
 void FinishFh1RenderTargetTransferTiming(const Fh1GpuWorkTiming&);
};
PRODUCTION_METHODS
int main() {
 uint64_t fh1_gpu_pass_timing_drops_=0, fh1_gpu_pass_timing_invalid_drops_=0;
 uint32_t valid_records=0;
 for (uint32_t scenario=0;scenario<4;++scenario) {
  struct {uint64_t family;} record{scenario==0?0u:1u};
  uint64_t start=2,copy_start=scenario==1?1:3,end=scenario==2?2:4;
  INVALID_PASS
  ++valid_records;
 }
 assert(valid_records==1 && fh1_gpu_pass_timing_drops_==3 && fh1_gpu_pass_timing_invalid_drops_==3);
 D3D12TextureCache::TextureKey key;
 D3D12CommandProcessor c;
 enabled=false; assert(c.BeginFh1TextureLoadTiming(key).record==UINT32_MAX); enabled=true;
 c.native_guest_output_gpu_query_heap_.available=false;
 assert(c.BeginFh1TextureLoadTiming(key).record==UINT32_MAX);
 c.native_guest_output_gpu_query_heap_.available=true;
 c.observation_frame_sequence_=61; assert(c.BeginFh1TextureLoadTiming(key).record==UINT32_MAX);
 c.observation_frame_sequence_=60;
 auto token=c.BeginFh1TextureLoadTiming(key);
 assert(token.record==0 && token.frame==1 && token.submission==4);
 assert((c.deferred_command_list_.queries==std::vector<uint32_t>{16,17,18}));
 c.AdvanceFh1GpuWorkTiming(token,false); c.AdvanceFh1GpuWorkTiming(token,true);
 assert(c.fh1_gpu_pass_timing_slots_[1].records[0].work_complete);
 assert((c.deferred_command_list_.queries==std::vector<uint32_t>{16,17,18,17,18}));
 auto second=c.BeginFh1TextureLoadTiming(key); assert(second.record==1);
 assert(c.BeginFh1TextureLoadTiming(key).record==UINT32_MAX && c.fh1_gpu_pass_timing_drops_==1);
 assert(c.fh1_gpu_pass_timing_capacity_drops_==1 && c.fh1_gpu_pass_timing_busy_drops_==0);
 auto size=c.deferred_command_list_.queries.size();
 ++c.submission_current_; c.AdvanceFh1GpuWorkTiming(second,true);
 assert(c.deferred_command_list_.queries.size()==size && !c.fh1_gpu_pass_timing_slots_[1].records[1].work_complete);
 --c.submission_current_; ++c.frame_current_; c.AdvanceFh1GpuWorkTiming(second,true);
 assert(c.deferred_command_list_.queries.size()==size);
 --c.frame_current_; c.fh1_gpu_pass_timing_slots_[1].submission=4;
 c.AdvanceFh1GpuWorkTiming(second,true);
 assert(c.BeginFh1TextureLoadTiming(key).record==UINT32_MAX);
 assert(c.fh1_gpu_pass_timing_interrupted_drops_==3 && c.fh1_gpu_pass_timing_busy_drops_==1);
 c.AdvanceFh1GpuWorkTiming({},true);
 assert(c.deferred_command_list_.queries.size()==size);
 D3D12CommandProcessor rt;
 assert(rt.BeginFh1RenderTargetTransferTiming(0,false).record==UINT32_MAX);
 assert(rt.deferred_command_list_.queries.empty());
 auto transfer=rt.BeginFh1RenderTargetTransferTiming(3,false);
 assert(transfer.record==0 && rt.fh1_gpu_pass_timing_slots_[1].records[0].render_target_transfer);
 assert(rt.fh1_gpu_pass_timing_slots_[1].records[0].transfer_count==3);
 rt.FinishFh1RenderTargetTransferTiming(transfer);
 assert(rt.fh1_gpu_pass_timing_slots_[1].records[0].work_complete);
 auto clear=rt.BeginFh1RenderTargetTransferTiming(0,true);
 assert(clear.record==1 && rt.fh1_gpu_pass_timing_slots_[1].records[1].resolve_clear);
 ++rt.submission_current_;rt.FinishFh1RenderTargetTransferTiming(clear);
 assert(!rt.fh1_gpu_pass_timing_slots_[1].records[1].work_complete);
 assert(rt.fh1_gpu_pass_timing_interrupted_drops_==2);
 std::cout << "texture timestamp sampling, capacity and interrupted-submission guards pass\n";
}
'''.replace('PRODUCTION_METHODS', '\n'.join(methods)).replace('INVALID_PASS', invalid_pass)
    with tempfile.TemporaryDirectory(prefix='fh1-texture-timing-') as temp:
        cpp, exe = Path(temp) / 'check.cpp', Path(temp) / 'check.exe'
        cpp.write_text(harness)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
