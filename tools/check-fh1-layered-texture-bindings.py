"""Compile the production layered root-binding branches with descriptor-heap mocks.

Run in the release build environment; covers fixed slots, dirty tracking and
return to the guest root. Live RenderDoc checks cover GPU resources and pixels.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def block(source, start):
    depth = 0
    for end in range(source.index('{', start), len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[start:end + 1]
    raise AssertionError('Unterminated block')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    source = (Path(__file__).resolve().parents[1] / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
    start = source.rfind('  if (bindless_resources_used_) {', 0, source.index('cbuffer_binding_descriptor_indices_pixel_.address);'))
    bindings = block(source, start)
    dirty = block(source, source.index('  if (native_layered) {', source.index('// Texture dirtiness need not')))
    pixel_invalid = block(source, source.index('      if (!native_layered) {', source.index('      cbuffer_binding_descriptor_indices_pixel_.up_to_date = true;')))
    uploads = []
    for stage in ('vertex', 'pixel'):
        begin = source.index('      uint32_t* descriptor_indices = nullptr;', source.index('    if (!cbuffer_binding_descriptor_indices_' + stage + '_.up_to_date)'))
        end = source.index('      for (size_t i = 0; i < texture_count_', begin)
        uploads.append('bool upload_' + stage + '(){' + source[begin:end] + 'cbuffer_binding_descriptor_indices_' + stage + '_.up_to_date=true;return true;}')
    restore = block(source, source.index('    if (!native_layered) {', source.index('// Native fixed bindings')))
    pipeline = (Path(__file__).resolve().parents[1] / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
    fallback = pipeline[pipeline.index('  HRESULT create_result ='):pipeline.index('  if (FAILED(create_result)', pipeline.index('  HRESULT create_result ='))]
    harness = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <map>
#include <vector>
#define assert_true(x) assert(x)
enum { kRootParameter_Bindless_DescriptorIndicesPixel=3,
       kRootParameter_Bindless_DescriptorIndicesVertex=4,
       kRootParameter_Bindless_SamplerHeap=8, kRootParameter_Bindless_ViewHeap=9 };
struct Provider {
  uint64_t OffsetViewDescriptor(uint64_t base, uint32_t i) { return base + i * 32; }
  uint64_t OffsetSamplerDescriptor(uint64_t base, uint32_t i) { return base + i * 16; }
};
struct Cache { uint32_t GetActiveTextureBindlessSRVIndex(uint32_t i) { return i; } };
struct Commands {
  std::map<int,uint64_t> tables, cbvs;
  void D3DSetGraphicsRootDescriptorTable(int i, uint64_t a) { tables[i]=a; }
  void D3DSetGraphicsRootConstantBufferView(int i, uint64_t a) { cbvs[i]=a; }
  void D3DSetGraphicsRootShaderResourceView(int i, uint64_t a) { cbvs[i]=a; }
};
struct Test {
  bool bindless_resources_used_=true,native_terrain=false;
  uint64_t terrain_addresses[2]={};
  struct Memory {uint64_t GetGPUAddress(){return 60000;}} memory;Memory* shared_memory_=&memory;
  int root_signature_fh1_layered_=1, current_graphics_root_signature_=1;
  uint32_t current_graphics_root_up_to_date_=0;
  std::array<uint32_t,3> fh1_fixed_descriptor_indices_{};
  uint64_t sampler_bindless_heap_gpu_start_=10000, view_bindless_heap_gpu_start_=20000;
  size_t texture_count_pixel=2, sampler_count_pixel=1;
  std::vector<uint32_t> indices{57,211}, current_sampler_bindless_indices_pixel_{13};
  std::vector<uint32_t>* textures_pixel=&indices;
  struct Binding { uint64_t address; } cbuffer_binding_descriptor_indices_pixel_{30000},
      cbuffer_binding_descriptor_indices_vertex_{40000};
  Cache cache; Cache* texture_cache_=&cache;
  Provider provider; Commands deferred_command_list_;
  void invalidate_pixel() {
    const bool native_layered=current_graphics_root_signature_==root_signature_fh1_layered_;
    PIXEL_INVALID
  }
  void bind() { const bool native_layered=current_graphics_root_signature_==root_signature_fh1_layered_; DIRTY BINDINGS }
};
using HRESULT = int;
constexpr int E_FAIL = -1;
#define IID_PPV_ARGS(x) x
struct Fallback {
  bool fh1_packed_world_vertex=false,fh1_packed_world_geometry=false;
  bool fh1_native_scene=true,fh1_native_depth=false,fh1_native_terrain=false,fh1_native_scene_geometry=false;
  uint64_t fh1_vertex_shader_hash=0x3BC346726C1C2535ull;
  struct Processor { int root=0; int GetFh1LayeredRootSignature() { return root; } int GetFh1DepthRootSignature(){return root;} int GetFh1TerrainRootSignature(){return root;} } command_processor_;
  struct Device { int calls=0; int CreateGraphicsPipelineState(int*,int*) { ++calls; return 0; } } gpu;
  int run() { auto* device=&gpu; int state_desc=0,state=0; FALLBACK return create_result; }
};
struct IndexUploads {
  bool native_layered=true;uint64_t frame_current_=1;
  size_t texture_count_vertex=0,sampler_count_vertex=0,texture_count_pixel=2,sampler_count_pixel=1;
  static constexpr uint32_t D3D12_CONSTANT_BUFFER_DATA_PLACEMENT_ALIGNMENT=256;
  struct Binding {uint64_t address=900;bool up_to_date=false;};
  Binding cbuffer_binding_descriptor_indices_vertex_,cbuffer_binding_descriptor_indices_pixel_;
  struct Pool {int calls=0;bool fail=false;uint32_t data[8];
    uint8_t* Request(uint64_t,size_t,uint32_t,void*,void*,uint64_t* address){
      ++calls;if(fail)return nullptr;*address=1000+calls;return reinterpret_cast<uint8_t*>(data);
    }
  } pool;Pool* constant_buffer_pool_=&pool;
  UPLOADS
  void restore(){RESTORE}
};
int main() {
  IndexUploads u;
  assert(u.upload_vertex() && u.upload_pixel() && u.pool.calls==0);
  assert(!u.cbuffer_binding_descriptor_indices_vertex_.address && !u.cbuffer_binding_descriptor_indices_pixel_.address);
  u.restore();assert(u.cbuffer_binding_descriptor_indices_pixel_.up_to_date);
  u.native_layered=false;u.restore();
  assert(!u.cbuffer_binding_descriptor_indices_vertex_.up_to_date && !u.cbuffer_binding_descriptor_indices_pixel_.up_to_date);
  u.pool.fail=true;assert(!u.upload_pixel());u.pool.fail=false;
  assert(u.upload_vertex() && u.upload_pixel() && u.pool.calls==3);
  u.restore();assert(u.cbuffer_binding_descriptor_indices_vertex_.up_to_date && u.cbuffer_binding_descriptor_indices_pixel_.up_to_date);

  Fallback f;
  assert(f.run()==E_FAIL && !f.gpu.calls);
  f.command_processor_.root=1; assert(f.run()==0 && f.gpu.calls==1);
  f.command_processor_.root=0; f.fh1_vertex_shader_hash=0;
  assert(f.run()==0 && f.gpu.calls==2);
  f.fh1_vertex_shader_hash=0x3BC346726C1C2535ull; f.fh1_native_scene=false;
  assert(f.run()==0 && f.gpu.calls==3);
  f.fh1_native_scene_geometry=true;
  assert(f.run()==E_FAIL && f.gpu.calls==3);
  f.command_processor_.root=1;assert(f.run()==0 && f.gpu.calls==4);
  f.fh1_native_scene_geometry=false;f.fh1_packed_world_geometry=true;f.command_processor_.root=0;
  assert(f.run()==E_FAIL && f.gpu.calls==4);
  Test zero;zero.indices={0,0};zero.current_sampler_bindless_indices_pixel_[0]=0;zero.bind();
  assert(zero.deferred_command_list_.tables.size()==3);
  assert(zero.deferred_command_list_.tables.at(3)==20000 && zero.deferred_command_list_.tables.at(8)==10000);
  Test t;
  t.bind();
  assert(t.deferred_command_list_.tables.at(9)==20000+57*32);
  assert(t.deferred_command_list_.tables.at(3)==20000+211*32);
  assert(t.deferred_command_list_.tables.at(8)==10000+13*16);
  assert(!t.deferred_command_list_.cbvs.count(3) && !t.deferred_command_list_.cbvs.count(4));
  t.deferred_command_list_.tables.clear(); t.bind();
  assert(t.deferred_command_list_.tables.empty());
  t.indices={211,57}; t.current_sampler_bindless_indices_pixel_[0]=19;
  t.invalidate_pixel(); t.bind();
  assert(t.deferred_command_list_.tables.at(9)==20000+211*32);
  assert(t.deferred_command_list_.tables.at(3)==20000+57*32);
  assert(t.deferred_command_list_.tables.at(8)==10000+19*16);
  t.deferred_command_list_.tables.clear();
  t.invalidate_pixel();t.bind();assert(t.deferred_command_list_.tables.empty());
  t.indices[0]=212;t.invalidate_pixel();t.bind();
  assert(t.deferred_command_list_.tables.size()==1 && t.deferred_command_list_.tables.at(9)==20000+212*32);
  t.deferred_command_list_.tables.clear();t.indices[1]=58;t.invalidate_pixel();t.bind();
  assert(t.deferred_command_list_.tables.size()==1 && t.deferred_command_list_.tables.at(3)==20000+58*32);
  t.deferred_command_list_.tables.clear();t.current_sampler_bindless_indices_pixel_[0]=20;t.invalidate_pixel();t.bind();
  assert(t.deferred_command_list_.tables.size()==1 && t.deferred_command_list_.tables.at(8)==10000+20*16);
  // A new heap must rebind even if the resolved index is unchanged.
  t.deferred_command_list_.tables.clear();t.sampler_bindless_heap_gpu_start_=40000;
  t.current_graphics_root_up_to_date_ &= ~(1u << kRootParameter_Bindless_SamplerHeap);
  t.bind();assert(t.deferred_command_list_.tables.size()==1 && t.deferred_command_list_.tables.at(8)==40000+20*16);
  // Sampler heap rollover must use the new heap base and resolved sampler index.
  t.sampler_bindless_heap_gpu_start_=50000;
  t.current_sampler_bindless_indices_pixel_[0]=2;
  t.invalidate_pixel(); t.bind();
  assert(t.deferred_command_list_.tables.at(8)==50000+2*16);
  // Root switches invalidate all slots; guest bindings use whole heaps and b4.
  t.current_graphics_root_signature_=2; t.current_graphics_root_up_to_date_=0;
  t.deferred_command_list_.tables.clear(); t.bind();
  assert(t.deferred_command_list_.tables.at(9)==20000);
  assert(t.deferred_command_list_.tables.at(8)==50000);
  assert(!t.deferred_command_list_.tables.count(3));
  assert(t.deferred_command_list_.cbvs.at(3)==30000);
  t.current_graphics_root_signature_=1; t.current_graphics_root_up_to_date_=0;
  t.bind(); assert(t.deferred_command_list_.tables.at(3)==20000+58*32);
}
""".replace('DIRTY', dirty).replace('PIXEL_INVALID', pixel_invalid).replace('BINDINGS', bindings).replace('FALLBACK', fallback).replace('UPLOADS', '\n'.join(uploads)).replace('RESTORE', restore)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp) / 'bindings.cpp'
        exe = Path(temp) / 'bindings.exe'
        cpp.write_text(harness)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Layered texture binding checks passed')


if __name__ == '__main__':
    main()
