"""Exercise production geometry cache control flow with fake GPU and one-shot watches.

Run in the release build environment. This checks cache bytes, invalidation and
fence policy with fake GPU objects; actual D3D12 copies need separate validation.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'thirdparty/shiftglue-sdk'
    source = (root / 'src/graphics/d3d12/command_processor.cpp').read_text()
    methods = source.split('// BEGIN FH1 OWNED GEOMETRY CACHE\n')[1].split('// END FH1 OWNED GEOMETRY CACHE')[0]
    def block_at(marker):
        start = source.index(marker)
        depth = 0
        for end in range(source.index('{', start), len(source)):
            depth += (source[end] == '{') - (source[end] == '}')
            if depth == 0:
                return source[start:end + 1]
        raise AssertionError('unterminated binding block')
    invalidate = block_at('void D3D12CommandProcessor::InvalidateVertexBufferResidency(')
    draw_start = source.index('  // Draw.\n')
    access_start = source.index('    if (memexport_used)', draw_start)
    draw_access = source[access_start:source.index('    SubmitBarriers();', access_start)]
    index_start = source.index('    deferred_command_list_.D3DIASetIndexBuffer(&index_buffer_view);')
    access_start = source.index('    if (memexport_used)', index_start)
    index_access = source[access_start:source.index('    SubmitBarriers();', access_start)]
    skinned_binding = block_at('if (current_fh1_skinned_origin_ != skinned_origin)')
    binding = block_at('if (current_fh1_geometry_address_ != geometry_address)')
    rebase = block_at('if (geometry_address) {\n      const uint32_t rebased')
    terrain_binding = block_at('if (current_fh1_terrain_addresses_ != terrain_addresses)')
    terrain_rebase = block_at('for (uint32_t i = 0; i < 2; ++i) {\n      if (!terrain_addresses[i]) continue;')
    skip_start = source.index('if (geometry_address && (vfetch_index')
    skip = source[skip_start:source.index(';', skip_start)+1]
    assert source.index('D3D12_GPU_VIRTUAL_ADDRESS geometry_address = 0;') < skip_start
    assert source.rfind('switch (vfetch_constant.type)', 0, skip_start) > source.index('  // Ensure vertex buffers are resident.')
    header = (root / 'include/rex/graphics/d3d12/command_processor.h').read_text()
    members = header[header.index('  struct Fh1Geometry {'):header.index('  uint64_t fh1_geometry_hits_ = 0;') + len('  uint64_t fh1_geometry_hits_ = 0;')]
    harness = r"""
#include <algorithm>
#include <rex/graphics/d3d12/fh1_geometry.h>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <memory>
#include <map>
#include <mutex>
#include <string>
#include <span>
#include <unordered_map>
#include <utility>
#include <vector>
using D3D12_GPU_VIRTUAL_ADDRESS = uint64_t;
using D3D12_RESOURCE_STATES = int;
constexpr int D3D12_RESOURCE_STATE_COPY_DEST=1, D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE=2, D3D12_RESOURCE_STATE_INDEX_BUFFER=4;
constexpr int D3D12_RESOURCE_FLAG_NONE=0;
#define FAILED(x) ((x)!=0)
#define IID_PPV_ARGS(x) x
#define REXGPU_INFO(...) ((void)0)
inline bool fh1_recycle_geometry_buffers=false;
inline bool fh1_contain_geometry_windows=false;
#define REXCVAR_GET(name) name
struct ID3D12Resource { std::vector<uint8_t> bytes; explicit ID3D12Resource(size_t size):bytes(size){} void SetName(const wchar_t*){} uint64_t GetGPUVirtualAddress(){return reinterpret_cast<uint64_t>(bytes.data());} };
namespace Microsoft::WRL {
template<class T> struct ComPtr {
  T* ptr=nullptr;
  ~ComPtr(){delete ptr;}
  ComPtr()=default;
  ComPtr(const ComPtr&)=delete;
  ComPtr(ComPtr&& other):ptr(std::exchange(other.ptr,nullptr)){}
  ComPtr& operator=(ComPtr&& other){if(this!=std::addressof(other)){delete ptr;ptr=std::exchange(other.ptr,nullptr);}return *this;}
  T* Get()const{return ptr;}
  T* operator->()const{return ptr;}
  T** operator&(){return &ptr;}
};
}
namespace thread { struct global_critical_region {
  static auto AcquireDirect(){static std::recursive_mutex mutex;return std::unique_lock<std::recursive_mutex>(mutex);}
}; }
struct D3D12_RESOURCE_DESC { uint64_t size; };
namespace ui::d3d12::util {
inline int kHeapPropertiesDefault=0;
void FillBufferResourceDesc(D3D12_RESOURCE_DESC& desc,uint32_t size,int){desc.size=size;}
}
struct Device {
  bool fail=false;
  uint32_t creations=0;
  struct Allocation {uint64_t SizeInBytes;};
  Allocation GetResourceAllocationInfo(int,int,const D3D12_RESOURCE_DESC* d){return {(d->size+65535)&~uint64_t(65535)};}
  int CreateCommittedResource(const int*,int,const D3D12_RESOURCE_DESC* d,int,void*,ID3D12Resource** out){
    if(fail)return 1;*out=new ID3D12Resource(d->size);++creations;return 0;
  }
};
struct Provider {Device device; Device* GetDevice()const{return const_cast<Device*>(&device);} int GetHeapFlagCreateNotZeroed()const{return 0;} };
struct SharedMemory {
  static constexpr uint32_t kBufferSize=1u<<29;
  using WatchHandle=void*;
  using Callback=void(*)(const std::unique_lock<std::recursive_mutex>&,void*,void*,uint64_t,bool);
  struct Watch{uint32_t start,size;Callback callback;void* context;void* data;uint64_t argument;};
  std::unordered_map<void*,std::unique_ptr<Watch>> watches;
  ID3D12Resource source{64*1024*1024};
  bool fail=false, invalidate_during_request=false, cpu=false, invalidate_during_copy=false;
  int requests=0;
  bool CopyCpuRange(uint32_t address,std::span<uint8_t> destination){
    if(!cpu)return false;
    assert(!watches.empty());
    std::memcpy(destination.data(),source.bytes.data()+address,destination.size());
    if(invalidate_during_copy){invalidate_during_copy=false;invalidate(address,false);}
    return true;
  }
  void* WatchMemoryRange(uint32_t start,uint32_t size,Callback cb,void* ctx,void* data,uint64_t arg){
    auto w=std::make_unique<Watch>(Watch{start,size,cb,ctx,data,arg});auto* p=w.get();watches.emplace(p,std::move(w));return p;
  }
  void UnwatchMemoryRange(void* p){assert(watches.erase(p)==1);}
  void invalidate(uint32_t start,bool gpu){
    auto lock=thread::global_critical_region::AcquireDirect();
    for(auto it=watches.begin();it!=watches.end();){
      auto& w=*it->second;
      if(start>=w.start && start<w.start+w.size){auto copy=w;it=watches.erase(it);copy.callback(lock,copy.context,copy.data,copy.argument,gpu);}else ++it;
    }
  }
  bool RequestRange(uint32_t address,uint32_t){
    ++requests;
    if(invalidate_during_request){invalidate_during_request=false;invalidate(address,false);}return !fail;
  }
  void UseAsCopySource(){}
  ID3D12Resource* GetBuffer(){return &source;}
};
struct Commands {
  void D3DCopyBufferRegion(ID3D12Resource* dst,uint32_t offset,ID3D12Resource* src,uint32_t start,uint32_t size){
    assert(start+size<=src->bytes.size());assert(offset+size<=dst->bytes.size());
    std::memcpy(dst->bytes.data()+offset,src->bytes.data()+start,size);
  }
};
struct UploadPool {
  ID3D12Resource buffer{32*1024*1024};bool fail=false;
  uint8_t* Request(uint64_t,uint32_t size,uint32_t alignment,ID3D12Resource** source,size_t* offset,void*){
    if(fail)return nullptr;
    assert(alignment==16 && size+128<=buffer.bytes.size());
    *source=&buffer;*offset=128;return buffer.bytes.data()+128;
  }
};
struct D3D12CommandProcessor {
  UploadPool pool;UploadPool* constant_buffer_pool_=&pool;uint64_t frame_current_=1;
  Provider provider;SharedMemory memory;SharedMemory* shared_memory_=&memory;Commands deferred_command_list_;
  uint64_t submission_current_=1,submission_completed_=0;
  const Provider& GetD3D12Provider(){return provider;}
  std::vector<std::array<int,2>> barriers;
  void PushTransitionBarrier(ID3D12Resource*,int from,int to){barriers.push_back({from,to});}
  void SubmitBarriers(){}
  uint32_t current_fh1_skinned_origin_=0;
  void bind_skinned(uint32_t skinned_origin){ /* SKINNED BINDING */ }
  uint64_t current_fh1_geometry_address_=0;
  std::array<uint64_t,2> current_fh1_terrain_addresses_{};
  void bind_terrain(std::array<uint64_t,2> terrain_addresses){
    constexpr uint32_t kRootParameter_Bindless_DescriptorIndicesVertex=6,kRootParameter_Bindless_DescriptorIndicesPixel=7;
    /* TERRAIN BINDING */
  }
  uint32_t current_graphics_root_up_to_date_=~0u;
  struct {bool up_to_date=true;} cbuffer_binding_fetch_;
  void bind_geometry(uint64_t geometry_address){
    uint32_t root_parameter_shared_memory_and_bindful_edram=5;
    /* BINDING */
  }
  struct VertexBufferState {uint32_t address=UINT32_MAX,size=UINT32_MAX;};
  std::array<VertexBufferState,96> vertex_buffer_states_;
  uint64_t vertex_buffers_in_sync_[2]={};
  void InvalidateVertexBufferResidency(uint32_t vfetch_index);
  /* MEMBERS */
};
uint32_t terrain_scans=0;
auto geometry_index_maximum(std::span<const uint32_t,8> system,std::span<const uint8_t> bytes,uint32_t width,bool reset){
 ++terrain_scans;return rex::graphics::d3d12::geometry_index_maximum(system,bytes,width,reset);
}
uint32_t terrain_ranges_calls=0;
auto terrain_geometry_ranges(uint32_t maximum,std::span<const float,44> constants,std::span<const uint32_t,6> fetches){
 ++terrain_ranges_calls;return rex::graphics::d3d12::terrain_geometry_ranges(maximum,constants,fetches);
}
uint32_t bound_scans=0;
auto depth_geometry_range(std::span<const uint32_t,8> system,std::span<const uint8_t> bytes,
 uint32_t width,uint32_t stride,uint32_t address,uint32_t size,bool reset,uint32_t vertex_bytes=12){
 ++bound_scans;return rex::graphics::d3d12::depth_geometry_range(system,bytes,width,stride,address,size,reset,vertex_bytes);
}
/* METHODS */
/* INVALIDATE */
int main(int argc,char**){
  fh1_contain_geometry_windows=argc>1;
  {
    // A new larger import must not redirect snapshots away from a held owner.
    D3D12CommandProcessor c;c.memory.cpu=true;c.memory.source.bytes[64]=7;
    auto held=c.GetFh1OwnedGeometry(64,4,true);assert(held);
    c.memory.source.bytes[64]=9;c.memory.invalidate(64,false);
    auto larger=c.GetFh1OwnedGeometry(0,131072,true);assert(larger);
    assert(*reinterpret_cast<uint8_t*>(held)==7);
    assert(reinterpret_cast<uint8_t*>(larger)[64]==9);
    assert(c.GetFh1OwnedGeometryCpuRange(64,4)[0]==7);
    assert(c.GetFh1OwnedGeometry(64,4,true)==held); // Refresh the original owner.
    assert(*reinterpret_cast<uint8_t*>(held)==9);
    c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty());
  }
  {
    D3D12CommandProcessor c;c.memory.cpu=true;
    c.memory.source.bytes[64]=1;c.memory.source.bytes[65552]=77;
    auto large=c.GetFh1OwnedGeometry(0,131072);assert(large);
    auto nested=c.GetFh1OwnedGeometry(64,16,true);assert(nested);
    const bool contained=fh1_contain_geometry_windows;
    assert((nested==large+64)==contained);
    assert(c.fh1_geometry_.size()==(contained?1u:2u));
    assert(c.fh1_geometry_bytes_==(contained?131072u:196608u));
    assert(c.GetFh1OwnedGeometryCpuRange(64,16)[0]==1);
    assert(c.GetFh1OwnedGeometryCpuRange(65552,1).empty()); // Different base.
    const auto imports=c.fh1_geometry_imports_;
    c.memory.source.bytes[65552]=88;c.memory.invalidate(65552,false);
    assert(c.GetFh1OwnedGeometry(64,16,true)==nested);
    assert(c.fh1_geometry_imports_==imports+contained);
    if(contained){
      assert(c.fh1_geometry_.begin()->second.cpu_snapshot.size()==131072);
      assert(c.fh1_geometry_.begin()->second.cpu_snapshot[65552]==88);
      assert(reinterpret_cast<uint8_t*>(large)[65552]==88);
      auto& owner=c.fh1_geometry_.begin()->second;
      owner.depth_bounds.emplace_back();owner.terrain_bounds.emplace_back();
      c.memory.cpu=false;c.memory.source.bytes[64]=4;c.memory.invalidate(64,true);
      assert(c.GetFh1OwnedGeometry(64,16,true)==nested);
      assert(c.GetFh1OwnedGeometryCpuRange(64,16).empty());
      assert(owner.depth_bounds.empty() && owner.terrain_bounds.empty());
      assert(*reinterpret_cast<uint8_t*>(nested)==4);
      assert(reinterpret_cast<uint8_t*>(large)[65552]==88);
      c.memory.cpu=true;c.memory.source.bytes[64]=5;c.memory.invalidate(64,false);
      assert(c.GetFh1OwnedGeometry(64,16,true)==nested);
      assert(c.GetFh1OwnedGeometryCpuRange(64,16)[0]==5);
    }
    assert(bool(c.fh1_geometry_contained_uses_)==contained);
    c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty());
    // Same guest range after destruction must get fresh contents and metadata.
    c.memory.source.bytes[64]=6;
    assert(c.GetFh1OwnedGeometry(0,131072,true));
    assert(c.GetFh1OwnedGeometry(64,16,true));
    assert(c.GetFh1OwnedGeometryCpuRange(64,16)[0]==6);
    c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty());
  }
  if(fh1_contain_geometry_windows){
    D3D12CommandProcessor c;c.memory.cpu=true;c.memory.source.bytes[64]=7;
    constexpr uint32_t size=16*1024*1024;
    auto held=c.GetFh1OwnedGeometry(0,size,true);assert(held);
    c.submission_current_=2;assert(c.GetFh1OwnedGeometry(size,size));
    c.submission_current_=3;c.submission_completed_=2;c.frame_current_=3;
    assert(c.GetFh1OwnedGeometry(64,16,true)==held+64);
    c.submission_current_=4;assert(c.GetFh1OwnedGeometry(2*size,size));
    assert(c.fh1_geometry_.contains(size)); // Nested use protected first owner.
    assert(!c.fh1_geometry_.contains((uint64_t(size)<<32)|size));
    assert(c.GetFh1OwnedGeometryCpuRange(64,16)[0]==7);
    assert(reinterpret_cast<uint8_t*>(held)[64]==7);
    assert(c.fh1_geometry_bytes_==32*1024*1024);
    c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty());
  }
  for(bool recycle:{false,true}) {
    fh1_recycle_geometry_buffers=recycle;
    D3D12CommandProcessor c;c.memory.cpu=true;
    constexpr uint32_t bytes=16*1024*1024;
    std::fill_n(c.memory.source.bytes.begin(),bytes,0xA5);
    std::fill_n(c.memory.source.bytes.begin()+bytes,bytes,0xB6);
    std::fill_n(c.memory.source.bytes.begin()+2*bytes,bytes,0xC7);
    auto original=c.GetFh1OwnedGeometry(0,bytes,true);assert(original);
    c.fh1_geometry_.at(bytes).depth_bounds.emplace_back();
    c.fh1_geometry_.at(bytes).terrain_bounds.emplace_back();
    c.submission_current_=2;assert(c.GetFh1OwnedGeometry(bytes,bytes,true));
    c.submission_current_=3;
    assert(!c.GetFh1OwnedGeometry(2*bytes,bytes,true)); // Every victim still in flight.
    assert(c.fh1_geometry_recycles_==0 && c.provider.device.creations==2);
    c.submission_completed_=1;
    assert(!c.GetFh1OwnedGeometry(2*bytes,bytes,true)); // Completed but used this frame.
    c.frame_current_=2;
    assert(!c.GetFh1OwnedGeometry(2*bytes,bytes,true)); // Previous frame stays resident.
    assert(c.provider.device.creations==2 && c.fh1_geometry_.size()==2);
    c.frame_current_=3;
    c.provider.device.fail=recycle; // Reuse needs no successful allocation call.
    auto barrier_start=c.barriers.size();
    auto replacement=c.GetFh1OwnedGeometry(2*bytes,bytes,true);assert(replacement);
    assert(!recycle || replacement==original);
    assert(c.provider.device.creations==(recycle?2u:3u));
    assert(c.fh1_geometry_allocations_==c.provider.device.creations);
    assert(c.fh1_geometry_recycles_==uint64_t(recycle));
    assert(c.barriers[barrier_start][0]==(recycle?6:1) && c.barriers[barrier_start][1]==1);
    assert(c.fh1_geometry_bytes_==2*bytes && c.fh1_geometry_.size()==2 && c.memory.watches.size()==2);
    assert(!c.fh1_geometry_.contains(bytes));
    auto& entry=c.fh1_geometry_.at((uint64_t(2*bytes)<<32)|bytes);
    assert(entry.depth_bounds.empty() && entry.terrain_bounds.empty());
    assert(!std::memcmp(reinterpret_cast<void*>(replacement),c.memory.source.bytes.data()+2*bytes,bytes));
    assert(!std::memcmp(entry.cpu_snapshot.data(),reinterpret_cast<void*>(replacement),bytes));
    auto watch=entry.watch;c.memory.invalidate(64,false);assert(entry.watch==watch);
    c.memory.source.bytes[2*bytes+64]=0xD8;c.memory.invalidate(2*bytes+64,false);
    assert(!entry.watch);assert(c.GetFh1OwnedGeometry(2*bytes,bytes,true)==replacement);
    assert(reinterpret_cast<uint8_t*>(replacement)[64]==0xD8);
    c.submission_completed_=3;c.ClearFh1OwnedGeometry();
    assert(c.memory.watches.empty() && c.fh1_geometry_.empty() && !c.fh1_geometry_bytes_);
  }
  {
    fh1_recycle_geometry_buffers=true;
    D3D12CommandProcessor c;c.memory.cpu=true;
    constexpr uint32_t unit=8*1024*1024;
    assert(c.GetFh1OwnedGeometry(0,unit));
    c.submission_current_=2;assert(c.GetFh1OwnedGeometry(unit,3*unit));
    c.submission_current_=3;c.submission_completed_=2;c.frame_current_=3;
    assert(c.GetFh1OwnedGeometry(4*unit,2*unit)); // Neither victim has the requested size.
    assert(c.provider.device.creations==3 && c.fh1_geometry_recycles_==0);
    assert(c.fh1_geometry_bytes_==2*unit && c.memory.watches.size()==1);
    c.ClearFh1OwnedGeometry();
  }
  {
    // Prefer the oldest exact match; preserve newer in-flight owners and budget.
    fh1_recycle_geometry_buffers=true;
    D3D12CommandProcessor c;c.memory.cpu=true;
    constexpr uint32_t unit=4*1024*1024;
    auto oldest=c.GetFh1OwnedGeometry(0,4*unit,true);assert(oldest);
    c.submission_current_=2;
    auto fitting=c.GetFh1OwnedGeometry(4*unit,2*unit,true);assert(fitting);
    auto& victim=c.fh1_geometry_.at((uint64_t(4*unit)<<32)|2*unit);
    victim.depth_bounds.emplace_back();victim.terrain_bounds.emplace_back();
    c.submission_current_=3;
    auto held=c.GetFh1OwnedGeometry(6*unit,2*unit);assert(held);
    c.submission_current_=4;c.submission_completed_=2;c.frame_current_=3;
    c.provider.device.fail=true; // Creation cannot accidentally satisfy the test.
    std::fill_n(c.memory.source.bytes.begin()+8*unit,2*unit,0xC7);
    auto replacement=c.GetFh1OwnedGeometry(8*unit,2*unit,true);
    assert(replacement==fitting && replacement!=held && replacement!=oldest);
    auto& entry=c.fh1_geometry_.at((uint64_t(8*unit)<<32)|2*unit);
    assert(entry.allocation_bytes==2*unit && entry.last_submission==4);
    assert(c.fh1_geometry_bytes_==8*unit && c.fh1_geometry_.size()==3);
    assert(entry.cpu_snapshot.size()==2*unit && entry.depth_bounds.empty() && entry.terrain_bounds.empty());
    assert(!std::memcmp(reinterpret_cast<void*>(replacement),c.memory.source.bytes.data()+8*unit,2*unit));
    assert(c.GetFh1OwnedGeometryCpuRange(8*unit,2*unit+1).empty());
    auto watch=entry.watch;
    c.memory.invalidate(4*unit+64,false); // Old owner's watch is gone.
    c.memory.invalidate(10*unit+64,false); // Beyond new logical ownership.
    assert(entry.watch==watch);
    c.memory.source.bytes[8*unit+64]=0xD8;c.memory.invalidate(8*unit+64,false);
    assert(!entry.watch && c.GetFh1OwnedGeometry(8*unit,2*unit,true)==replacement);
    assert(reinterpret_cast<uint8_t*>(replacement)[64]==0xD8);
    assert(c.fh1_geometry_bytes_==8*unit && c.provider.device.creations==3);
    c.submission_current_=5;c.submission_completed_=4;
    c.memory.cpu=false;c.memory.fail=true;
    assert(!c.GetFh1OwnedGeometry(10*unit,2*unit,true)); // Reused storage, failed import.
    auto& failed=c.fh1_geometry_.at((uint64_t(10*unit)<<32)|2*unit);
    assert(failed.buffer->GetGPUVirtualAddress()==held && !failed.watch && failed.cpu_snapshot.empty());
    c.memory.fail=false;c.memory.cpu=true;c.memory.source.bytes[10*unit]=0xE9;
    auto retry=c.GetFh1OwnedGeometry(10*unit,2*unit,true);assert(retry==held);
    assert(reinterpret_cast<uint8_t*>(retry)[0]==0xE9);
    assert(c.fh1_geometry_bytes_==8*unit && c.provider.device.creations==3);
    c.submission_completed_=5;c.ClearFh1OwnedGeometry();
    assert(c.memory.watches.empty() && c.fh1_geometry_.empty() && !c.fh1_geometry_bytes_);
  }
  fh1_recycle_geometry_buffers=false;
  {
    D3D12CommandProcessor c;c.memory.cpu=true;c.memory.source.bytes[64]=1;
    uint32_t system[8]={0,0,0,0xffffffff,0,0,0,0xffffff};
    float constants[44]{};constants[31]=1;constants[32]=1;constants[36]=100;constants[37]=10;constants[39]=9;
    uint32_t fetches[6]={128,1024,256,1024,65536,32000};
    c.GetFh1OwnedGeometry(64,4,true);
    auto bound=[&](){return c.GetFh1TerrainGeometryRanges(64,4,system,2,false,constants,fetches);};
    auto first=bound();assert(first && (*first)[0].second==36 && (*first)[1].second==8 && (*first)[2].second==32000);
    assert(terrain_scans==1 && bound()==first && terrain_scans==1);
    constants[0]=42;constants[33]=std::numeric_limits<float>::quiet_NaN();constants[32]=7;
    assert(bound()==first && terrain_scans==1); // unused constants and same optional branch
    constants[32]=0;auto inactive=bound();assert(inactive && (*inactive)[1].second==0 && terrain_scans==1 && terrain_ranges_calls==2);
    constants[32]=1;bound();auto before=terrain_ranges_calls;
    for(uint32_t component:{16u,17u,18u,20u,21u,22u,28u,29u,30u,31u,36u,37u,38u,39u}){
      float old=constants[component];constants[component]+=1;bound();assert(terrain_ranges_calls==++before && terrain_scans==1);
      bound();assert(terrain_ranges_calls==before);constants[component]=old;
    }
    for(uint32_t i=0;i<6;++i){fetches[i]^=4;bound();assert(terrain_ranges_calls==++before && terrain_scans==1);fetches[i]^=4;}
    before=terrain_scans;
    for(uint32_t i=0;i<8;++i){system[i]^=1;bound();assert(terrain_scans==++before);system[i]^=1;}
    auto varied=[&](uint32_t address,uint32_t bytes,uint32_t width,bool reset){
      auto before=terrain_scans;c.GetFh1TerrainGeometryRanges(address,bytes,system,width,reset,constants,fetches);assert(terrain_scans==before+1);
    };
    varied(66,4,2,false);varied(64,2,2,false);varied(64,4,4,false);varied(64,4,2,true);
    bound();before=terrain_scans;
    c.memory.invalidate(64,false);c.memory.source.bytes[64]=3;
    assert((*bound())[0].second==36 && terrain_scans==before);
    c.GetFh1OwnedGeometry(68,4);assert((*bound())[0].second==92 && terrain_scans==before+1);
    for(uint32_t fetch:{89u,90u,94u,95u})assert(c.vertex_buffer_states_[fetch].address==UINT32_MAX);
    for(uint32_t i=0;i<40;++i)c.GetFh1TerrainGeometryRanges(256+i*2,2,system,2,false,constants,fetches);
    assert(c.fh1_geometry_.begin()->second.terrain_bounds.size()==32);
    before=terrain_scans;bound();assert(terrain_scans==before+1);
    c.memory.cpu=false;c.memory.invalidate(64,true);c.GetFh1OwnedGeometry(64,4,true);
    assert(!bound() && c.fh1_geometry_.begin()->second.terrain_bounds.empty());
  }
  for(bool memexport_used:{false,true})for(uint64_t geometry_address:{0ull,100ull})for(uint64_t depth_index_address:{0ull,200ull}) {
    struct {int reads=0,writes=0;void UseForReading(){++reads;}void UseForWriting(){++writes;}} shared;
    auto* shared_memory_=&shared;
    /* INDEX ACCESS */
    assert(shared.writes==memexport_used);
    assert(shared.reads==(!memexport_used && (!geometry_address || !depth_index_address)));
  }
  {
    D3D12CommandProcessor c;c.memory.cpu=true;c.memory.source.bytes[64]=1;
    uint32_t system[8]={0,0,0,0xffffffff,0,0,0,0xffffff};
    c.GetFh1OwnedGeometry(64,4,true);
    auto bound=[&](){return c.GetFh1DepthGeometryRange(64,4,system,2,24,128,1024,false);};
    assert(bound()->second==36 && bound_scans==1);
    assert(bound()->second==36 && bound_scans==1);
    c.memory.invalidate(64,false);c.memory.source.bytes[64]=3;
    assert(bound()->second==36 && bound_scans==1); // still describes the bound GPU copy
    c.GetFh1OwnedGeometry(68,4); // an aliased vertex import replaces the indices
    assert(bound()->second==84 && bound_scans==2);
    for(uint32_t i=0;i<8;++i){
      system[i]^=1;auto before=bound_scans;bound();assert(bound_scans==before+1);bound();assert(bound_scans==before+1);system[i]^=1;
    }
    auto varied=[&](uint32_t address,uint32_t bytes,uint32_t width,uint32_t stride,uint32_t fetch,uint32_t size,bool reset){
      auto before=bound_scans;c.GetFh1DepthGeometryRange(address,bytes,system,width,stride,fetch,size,reset);assert(bound_scans==before+1);
    };
    varied(66,4,2,24,128,1024,false);varied(64,2,2,24,128,1024,false);
    varied(64,4,4,24,128,1024,false);varied(64,4,2,20,128,1024,false);
    varied(64,4,2,24,132,1024,false);varied(64,4,2,24,128,512,false);varied(64,4,2,24,128,1024,true);
    auto before_extent=bound_scans;
    assert(c.GetFh1DepthGeometryRange(64,4,system,2,24,128,1024,false,24)->second==96);
    assert(bound_scans==before_extent+1);
    assert(c.GetFh1DepthGeometryRange(64,4,system,2,24,128,1024,false,24)->second==96);
    assert(bound_scans==before_extent+1);
    for(uint32_t i=0;i<40;++i)c.GetFh1DepthGeometryRange(256+i*2,2,system,2,24,128,1024,false);
    auto& entry=c.fh1_geometry_.begin()->second;assert(entry.depth_bounds.size()==32);
    auto before=bound_scans;bound();assert(bound_scans==before+1); // replaced proof is recomputed
    c.memory.cpu=false;c.memory.invalidate(64,true);c.GetFh1OwnedGeometry(64,4,true);
    assert(entry.depth_bounds.empty() && !bound());
    c.memory.cpu=true;c.memory.invalidate(64,false);c.GetFh1OwnedGeometry(64,4,true);
    assert(bound()->second==84);
  }
  for(bool memexport_used:{false,true})for(uint64_t geometry_address:{0ull,100ull}) {
    struct {int reads=0,writes=0;void UseForReading(){++reads;}void UseForWriting(){++writes;}} shared;
    auto* shared_memory_=&shared;
    /* DRAW ACCESS */
    assert(shared.writes==memexport_used);
    assert(shared.reads==(!memexport_used && !geometry_address));
  }
  const bool fh1_skinned=false;
  for(uint64_t geometry_address:{0ull,100ull}) for(uint64_t control:{0ull,200ull}) {
    std::array<uint64_t,2> terrain_addresses{0,control};
    uint32_t requested=0;
    for(uint32_t vfetch_index=0;vfetch_index<96;++vfetch_index){
      /* SKIP */
      ++requested;
    }
    assert(requested==(geometry_address?(control?93u:95u):96u));
  }
  {
    D3D12CommandProcessor cpu;cpu.memory.cpu=true;cpu.memory.source.bytes[64]=91;
    auto address=cpu.GetFh1OwnedGeometry(64,64);
    assert(address && *reinterpret_cast<uint8_t*>(address)==91);
    assert(cpu.memory.requests==0 && cpu.fh1_geometry_cpu_imports_==1);
    cpu.memory.invalidate(64,false);cpu.memory.invalidate_during_copy=true;
    cpu.GetFh1OwnedGeometry(64,64);cpu.GetFh1OwnedGeometry(64,64);
    assert(cpu.fh1_geometry_cpu_imports_==3 && cpu.memory.requests==0);
    // GPU ownership rejection and upload allocation failure both use the original source.
    cpu.memory.invalidate(64,true);cpu.memory.cpu=false;cpu.memory.source.bytes[64]=92;
    assert(*reinterpret_cast<uint8_t*>(cpu.GetFh1OwnedGeometry(64,64))==92);
    assert(cpu.memory.requests==1 && cpu.fh1_geometry_cpu_imports_==3);
    cpu.memory.cpu=true;cpu.pool.fail=true;cpu.memory.invalidate(64,false);
    assert(cpu.GetFh1OwnedGeometry(64,64));assert(cpu.memory.requests==2);
    cpu.ClearFh1OwnedGeometry();assert(cpu.memory.watches.empty());
  }
  {
    D3D12CommandProcessor c;c.memory.cpu=true;
    assert(c.GetFh1OwnedGeometryCpuRange(64,4).empty());
    c.vertex_buffer_states_[95]={123,456};c.vertex_buffers_in_sync_[1]=~0ull;
    c.memory.source.bytes[64]=7;auto gpu=c.GetFh1OwnedGeometry(64,4);
    assert(c.vertex_buffer_states_[95].address==UINT32_MAX && !(c.vertex_buffers_in_sync_[1] & (1ull<<31)));
    c.vertex_buffer_states_[95]={123,456};c.vertex_buffers_in_sync_[1]=~0ull;
    c.GetFh1OwnedGeometry(64,4);
    assert(c.vertex_buffer_states_[95].address==123 && (c.vertex_buffers_in_sync_[1] & (1ull<<31)));
    assert(c.GetFh1OwnedGeometryCpuRange(64,4).empty());
    c.GetFh1OwnedGeometry(64,4,true);assert(c.memory.watches.size()==1);
    auto snapshot=c.GetFh1OwnedGeometryCpuRange(64,4);assert(snapshot.size()==4 && snapshot[0]==7);
    assert(std::memcmp(snapshot.data(),reinterpret_cast<void*>(gpu),4)==0);
    assert(c.GetFh1OwnedGeometryCpuRange(64,0).empty());
    assert(c.GetFh1OwnedGeometryCpuRange(SharedMemory::kBufferSize-2,4).empty());
    c.memory.invalidate(64,false);c.memory.source.bytes[64]=9;
    snapshot=c.GetFh1OwnedGeometryCpuRange(64,4);assert(snapshot[0]==7);
    assert(*reinterpret_cast<uint8_t*>(gpu)==7); // dirty guest data cannot change the cached import
    c.GetFh1OwnedGeometry(68,4); // aliased vertex import also refreshes the retained index snapshot
    snapshot=c.GetFh1OwnedGeometryCpuRange(64,4);assert(snapshot[0]==9);
    assert(std::memcmp(snapshot.data(),reinterpret_cast<void*>(gpu),4)==0);
    c.vertex_buffer_states_[95]={123,456};c.vertex_buffers_in_sync_[1]=~0ull;
    c.memory.cpu=false;c.memory.invalidate(64,true);c.GetFh1OwnedGeometry(64,4,true);
    assert(c.vertex_buffer_states_[95].address==123 && (c.vertex_buffers_in_sync_[1] & (1ull<<31)));
    assert(c.GetFh1OwnedGeometryCpuRange(64,4).empty()); // GPU imports cannot supply CPU bounds
    c.memory.cpu=true;c.memory.invalidate(64,false);c.memory.invalidate_during_copy=true;
    c.GetFh1OwnedGeometry(64,4,true);snapshot=c.GetFh1OwnedGeometryCpuRange(64,4);
    assert(!snapshot.empty() && std::memcmp(snapshot.data(),reinterpret_cast<void*>(gpu),4)==0);
  }
  D3D12CommandProcessor bindings;
  for(uint32_t origin:{0u,0x1000u,0x1010u,0x1010u,0u}){
    uint32_t old=bindings.current_fh1_skinned_origin_;
    bindings.cbuffer_binding_fetch_.up_to_date=true;bindings.bind_skinned(origin);
    assert(bindings.cbuffer_binding_fetch_.up_to_date==(old==origin));
  }

  bindings.bind_geometry(100);
  assert(!bindings.cbuffer_binding_fetch_.up_to_date && !(bindings.current_graphics_root_up_to_date_ & (1u<<5)));
  bindings.cbuffer_binding_fetch_.up_to_date=true;
  bindings.current_graphics_root_up_to_date_=~0u;
  bindings.bind_geometry(200);
  assert(bindings.cbuffer_binding_fetch_.up_to_date && !(bindings.current_graphics_root_up_to_date_ & (1u<<5)));
  bindings.bind_geometry(0);assert(!bindings.cbuffer_binding_fetch_.up_to_date);
  bindings.cbuffer_binding_fetch_.up_to_date=true;
  bindings.bind_geometry(0);assert(bindings.cbuffer_binding_fetch_.up_to_date);
  for(auto addresses:{std::array<uint64_t,2>{0,0},{0,200},{100,200},{100,300},{0,0}}){
    auto old=bindings.current_fh1_terrain_addresses_;
    bindings.cbuffer_binding_fetch_.up_to_date=true;bindings.current_graphics_root_up_to_date_=~0u;
    bindings.bind_terrain(addresses);
    assert(bindings.cbuffer_binding_fetch_.up_to_date==(bool(old[0])==bool(addresses[0]) && bool(old[1])==bool(addresses[1])));
    assert(bool(bindings.current_graphics_root_up_to_date_ & (1u<<6))==(old==addresses));
    assert(bool(bindings.current_graphics_root_up_to_date_ & (1u<<7))==(old==addresses));
  }
  constexpr uint32_t XE_GPU_REG_SHADER_CONSTANT_FETCH_00_0=0;
  uint32_t regs[192], output[192];
  for(uint32_t i=0;i<192;i++)regs[i]=1000+i;
  for(uint64_t geometry_address:{0ull,100ull}){
    std::memcpy(output,regs,sizeof(regs));
    auto* fetch_constants=reinterpret_cast<uint8_t*>(output);
    /* REBASE */
    for(uint32_t i=0;i<192;i++)assert(output[i]==(geometry_address && i==190 ? regs[i]&15u : regs[i]));
  }
  const bool native_skinned=false;const uint32_t skinned_origin=0;
  for(auto terrain_addresses:{std::array<uint64_t,2>{0,0},{0,200},{100,200}}){
    std::memcpy(output,regs,sizeof(regs));auto* fetch_constants=reinterpret_cast<uint8_t*>(output);
    /* TERRAIN REBASE */
    for(uint32_t i=0;i<192;++i)assert(output[i]==(((i==180 && terrain_addresses[0]) || (i==178 && terrain_addresses[1]))?regs[i]&15u:regs[i]));
  }
  for(uint32_t origin:{0x1000u,0x12340u}){
    const bool native_skinned=true;const uint32_t skinned_origin=origin;
    std::array<uint64_t,2> terrain_addresses{100,0};
    std::memcpy(output,regs,sizeof(regs));auto* fetch_constants=reinterpret_cast<uint8_t*>(output);
    /* TERRAIN REBASE */
    for(uint32_t i=0;i<192;++i)assert(output[i]==(i==188?regs[i]-origin:regs[i]));
  }
  for(bool owned:{false,true}){
    const bool fh1_skinned=true;uint64_t geometry_address=owned?100:0;
    std::array<uint64_t,2> terrain_addresses{owned?200u:0u,0};uint32_t requested=0;
    for(uint32_t vfetch_index=0;vfetch_index<96;++vfetch_index){ /* SKIP */ ++requested; }
    assert(requested==(owned?94u:96u));
  }
  D3D12CommandProcessor c;
  assert(!c.GetFh1OwnedGeometry(0,0));
  assert(!c.GetFh1OwnedGeometry(SharedMemory::kBufferSize-4,8));
  assert(!c.GetFh1OwnedGeometry(0,33*1024*1024));
  c.provider.device.fail=true;assert(!c.GetFh1OwnedGeometry(64,64));c.provider.device.fail=false;
  c.memory.source.bytes[64]=10;
  c.memory.source.bytes[68]=99;
  auto first=c.GetFh1OwnedGeometry(64,64);assert(c.fh1_geometry_.begin()->second.state==6);assert(first && *reinterpret_cast<uint8_t*>(first)==10);
  assert(c.GetFh1OwnedGeometry(64,64)==first && c.fh1_geometry_imports_==1 && c.fh1_geometry_hits_==1);
  for(bool gpu:{false,true}){
    c.memory.source.bytes[64]++;c.memory.invalidate(64,gpu);
    assert(*reinterpret_cast<uint8_t*>(c.GetFh1OwnedGeometry(64,64))==c.memory.source.bytes[64]);
  }
  assert(c.fh1_geometry_imports_==3);
  c.memory.invalidate(64,false);c.memory.invalidate_during_request=true;
  c.GetFh1OwnedGeometry(64,64);assert(c.fh1_geometry_imports_==4);
  c.GetFh1OwnedGeometry(64,64);assert(c.fh1_geometry_imports_==5); // must remain dirty during import
  c.memory.invalidate(64,false);c.memory.fail=true;
  assert(!c.GetFh1OwnedGeometry(64,64));assert(c.memory.watches.empty());
  c.memory.fail=false;assert(c.GetFh1OwnedGeometry(64,64));
  assert(c.GetFh1OwnedGeometry(64,32)==first); // same page reuses storage
  assert(c.GetFh1OwnedGeometry(68,32)==first); // aligned view, low four bits in fetch
  assert(reinterpret_cast<uint8_t*>(first)[4]==99);
  c.memory.source.bytes[65532]=33;c.memory.source.bytes[65536]=44;
  c.memory.invalidate(65532,false);
  auto crossing=c.GetFh1OwnedGeometry(65532,8);
  assert(crossing && c.fh1_geometry_.size()==2);
  assert(reinterpret_cast<uint8_t*>(crossing)[12]==33 && reinterpret_cast<uint8_t*>(crossing)[16]==44);
  assert(c.fh1_geometry_bytes_==3*65536); // crossing range owns both pages
  for(auto& item:c.fh1_geometry_)assert((item.first>>32)%65536==0);
  c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty() && c.fh1_geometry_bytes_==0);
  for(uint32_t i=0;i<512;i++)assert(c.GetFh1OwnedGeometry(i*65536,64));
  assert(c.fh1_geometry_bytes_==32*1024*1024);
  assert(!c.GetFh1OwnedGeometry(512*65536,64)); // every entry is still in flight
  c.submission_completed_=1;c.submission_current_=2;
  const auto creations=c.provider.device.creations;
  assert(!c.GetFh1OwnedGeometry(512*65536,64));
  c.frame_current_=2;
  assert(!c.GetFh1OwnedGeometry(512*65536,64));
  assert(c.provider.device.creations==creations && c.fh1_geometry_.size()==512);
  c.frame_current_=3;
  assert(c.GetFh1OwnedGeometry(512*65536,64)); // now completed entries may be evicted
  assert(c.fh1_geometry_.size()==512 && c.memory.watches.size()==512);
  assert(c.fh1_geometry_bytes_==32*1024*1024);
  c.ClearFh1OwnedGeometry();assert(c.memory.watches.empty());
}
""".replace('/* SKINNED BINDING */',skinned_binding).replace('/* MEMBERS */',members).replace('/* METHODS */',methods).replace('/* INVALIDATE */',invalidate).replace('/* DRAW ACCESS */',draw_access).replace('/* BINDING */',binding).replace('/* REBASE */',rebase).replace('/* SKIP */',skip).replace('/* TERRAIN BINDING */',terrain_binding).replace('/* TERRAIN REBASE */',terrain_rebase)
    with tempfile.TemporaryDirectory(prefix='fh1-geometry-cache-') as directory:
        cpp, executable = Path(directory)/'check.cpp', Path(directory)/'check.exe'
        cpp.write_text(harness.replace('/* INDEX ACCESS */',index_access))
        subprocess.run([args.compiler,'-std=c++20','-I'+str(root/'include'),str(cpp),'-o',str(executable)],check=True)
        subprocess.run([str(executable)],check=True)
        subprocess.run([str(executable),'contain'],check=True)
    print('Geometry cache exact/contained ownership, mutation, in-flight invalidation, failures, budget and eviction: passed')


if __name__=='__main__':
    main()
