"""Execute production depth index cache and residency fallback branches."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    source = (repo/'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
    begin = source.index('  const uint32_t fh1_depth_stride =')
    admission = source[begin:source.index('  const bool fh1_native_velocity_candidate', begin)]
    start = source.index('  D3D12_GPU_VIRTUAL_ADDRESS depth_index_address = 0;')
    snapshot = source[start:source.index('  D3D12_GPU_VIRTUAL_ADDRESS geometry_address', start)]
    start = source.index('        if (depth_index_address)', start)
    fallback = source[start:source.index('        if (memexport_used)', start)]
    primitive = (repo/'thirdparty/shiftglue-sdk/src/graphics/primitive_processor.cpp').read_text()
    start = primitive.index('  if ((cacheable.index_buffer_type ==')
    predicate = primitive[start+6:primitive.index(') {', start)]
    code = r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
using D3D12_GPU_VIRTUAL_ADDRESS = uint64_t;
namespace xenos {enum class IndexFormat {kInt16,kInt32};}
struct PrimitiveProcessor {enum class ProcessedIndexBufferType {kNone,kGuestDMA,kHostBuiltinForDMA,kHostConverted};};
using ProcessedIndexBufferType=PrimitiveProcessor::ProcessedIndexBufferType;
struct Result {ProcessedIndexBufferType index_buffer_type=ProcessedIndexBufferType::kGuestDMA;
 xenos::IndexFormat host_index_format=xenos::IndexFormat::kInt16;
 uint32_t host_draw_vertex_count=2,guest_index_base=64;};
struct SharedMemory {static constexpr uint32_t kBufferSize=1u<<29;
 bool resident=true;int requests=0;
 bool RequestRange(uint32_t,uint32_t size){++requests;assert(size==4);return resident;}
};
bool cache_ok=true;int cache_calls=0;
uint64_t GetFh1OwnedGeometry(uint32_t address,uint32_t size,bool keep_snapshot){++cache_calls;assert(address>=64 && size==4);return cache_ok?4096:0;}
struct RenderTargetCache {enum class Path{kHostRenderTargets,kPixelShaderInterlock};};
bool admitted(uint64_t fh1_vertex_hash,bool pixel,bool memexport_used,bool host,uint64_t fh1_pixel_hash=0){
 void* pixel_shader=pixel?reinterpret_cast<void*>(1):nullptr;
 struct Cache{bool host;RenderTargetCache::Path GetPath(){return host?RenderTargetCache::Path::kHostRenderTargets:RenderTargetCache::Path::kPixelShaderInterlock;}} cache{host};
 auto* render_target_cache_=&cache;
 ADMISSION
 return fh1_depth_indices;
}
bool run(bool eligible,Result primitive_processing_result,SharedMemory& memory,bool terrain=false,bool qualified=true,bool scene=false,bool packed=false){
 auto* shared_memory_=&memory;const bool fh1_depth_indices=eligible;
 int root_signature_fh1_depth_=1,root_signature_fh1_terrain_=2,root_signature_fh1_layered_=3,root_signature=qualified?(terrain?2:scene&&!packed?3:1):4;
 uint32_t fh1_depth_stride=(terrain || scene)?0:24,fh1_scene_stride=scene?(packed?28:20):0;
 SNAPSHOT
 struct {uint64_t BufferLocation=0;uint32_t SizeInBytes=4;} index_buffer_view;
 auto finish_draw=[](bool result){return result;};
 do {
 FALLBACK
 index_buffer_view.BufferLocation=999;
 } while(false);
 return index_buffer_view.BufferLocation==4096+(primitive_processing_result.guest_index_base & 15);
}
bool needs_residency(Result cacheable,bool defer_guest_dma_residency){return PREDICATE;}
int main(){
 {SharedMemory m;assert(run(true,Result{},m,false,true,true,true));
  assert(!run(true,Result{},m,false,false,true,true));}

 for(uint64_t hash:{0x9BF2991815B941B9ull,0xC8C39E5AE1B08DE6ull,0xB646F85EF69A57E0ull,0xD0C40C04F166092Eull,0x5A28C7FAFD86F112ull,0xCA293E0A1CB4B416ull,0x4E1DA281CC3D7EDBull})
  for(bool pixel:{false,true})for(bool memexport:{false,true})for(bool host:{false,true})assert(admitted(hash,pixel,memexport,host)==(!pixel && !memexport && host));
 for(bool pixel:{false,true})for(bool memexport:{false,true})for(bool host:{false,true})
  assert(admitted(0x6934E161812AB10Bull,pixel,memexport,host)==(!memexport && host));
 for(bool pixel:{false,true})for(bool memexport:{false,true})for(bool host:{false,true})
  assert(admitted(0xA3B9ED5D5C87230Eull,pixel,memexport,host)==(!memexport && host));
 assert(!admitted(0,false,false,true));
 for(bool memexport:{false,true})for(bool host:{false,true}){
  assert(admitted(0xAD2C355A6BE1EE87ull,true,memexport,host,0x2F2137BF953DA7AFull)==(!memexport && host));
  assert(admitted(0x8D8A197476841A9Aull,true,memexport,host,0xBA6A2871A980A4E8ull)==(!memexport && host));
 }
 assert(!admitted(0xAD2C355A6BE1EE87ull,true,false,true,0xBA6A2871A980A4E8ull));
 assert(!admitted(0x8D8A197476841A9Aull,true,false,true,0x2F2137BF953DA7AFull));
 {Result r;SharedMemory m;cache_ok=true;cache_calls=0;assert(run(true,r,m,true,true) && cache_calls==1 && !m.requests);}
 {Result r;SharedMemory m;cache_ok=true;cache_calls=0;assert(!run(true,r,m,true,false) && !cache_calls && m.requests==1);}
 {Result r;SharedMemory m;cache_ok=true;cache_calls=0;assert(run(true,r,m,false,true,true) && cache_calls==1 && !m.requests);}
 {Result r;SharedMemory m;cache_ok=true;cache_calls=0;assert(!run(true,r,m,false,false,true) && !cache_calls && m.requests==1);}
 for(auto type:{ProcessedIndexBufferType::kNone,ProcessedIndexBufferType::kGuestDMA,ProcessedIndexBufferType::kHostBuiltinForDMA,ProcessedIndexBufferType::kHostConverted}){
  Result r;r.index_buffer_type=type;
  assert(needs_residency(r,false)==(type==ProcessedIndexBufferType::kGuestDMA || type==ProcessedIndexBufferType::kHostBuiltinForDMA));
  assert(needs_residency(r,true)==(type==ProcessedIndexBufferType::kHostBuiltinForDMA));
 }
 for(bool available:{false,true})for(uint32_t low=0;low<16;low+=2){
  Result r;r.guest_index_base+=low;SharedMemory m;cache_ok=available;cache_calls=0;
  assert(run(true,r,m)==available);assert(m.requests==!available);assert(cache_calls==1);
 }
 Result r;SharedMemory m;cache_ok=true;cache_calls=0;
 assert(!run(false,r,m));assert(!m.requests && !cache_calls);
 r.host_index_format=xenos::IndexFormat::kInt32;r.host_draw_vertex_count=1;
 assert(run(true,r,m));assert(!m.requests);
 cache_ok=false;m.resident=false;assert(!run(true,r,m));assert(m.requests==1);
 r.host_draw_vertex_count=0;cache_calls=0;assert(!run(true,r,m));assert(!cache_calls);
 r.host_draw_vertex_count=0xffffffff;assert(!run(true,r,m));assert(!cache_calls);
}
'''.replace('SNAPSHOT', snapshot).replace('FALLBACK', fallback).replace('PREDICATE', predicate).replace('ADMISSION', admission)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'indices.cpp'; exe = Path(temp)/'indices.exe'
        cpp.write_text(code)
        subprocess.run([args.compiler, '-std=c++20', '-I'+str(repo/'thirdparty/shiftglue-sdk/include'), str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Depth index ownership and residency fallback checks passed')


if __name__ == '__main__':
    main()
