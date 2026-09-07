"""Execute owned depth bounds checks, including aliased index-cache refreshes."""
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
    start = source.index('  // Bounds must describe the cached indices actually bound below.')
    block = source[start:source.index('  // Ensure vertex buffers are resident.', start)]
    pipeline = (repo/'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
    first = pipeline.index('  const bool fh1_native_depth =')
    admission = pipeline[first:pipeline.index('  // Root signature.', first)]
    first = pipeline.index('  HRESULT create_result =') + len('  HRESULT create_result =')
    missing = pipeline[first:pipeline.index('? E_FAIL', first)]
    code = r'''
#include <cassert>
#include <vector>
#include <rex/graphics/d3d12/fh1_geometry.h>
using namespace rex::graphics::d3d12;
namespace xenos {enum class IndexFormat {kInt16,kInt32};}
uint32_t reads=0,imports=0,fail_read=0,initial_index=0,later_index=0;
bool import_ok=true,cache_hit=false;uint64_t fh1_geometry_imports_=0;
std::optional<std::pair<uint32_t,uint32_t>> GetFh1DepthGeometryRange(
 uint32_t address,uint32_t size,std::span<const uint32_t,8> system,uint32_t width,
 uint32_t stride,uint32_t fetch,uint32_t fetch_size,bool reset){
 assert(address==64 && size==2);++reads;
 if(reads==fail_read)return {};
 static uint16_t index;index=reads==1?initial_index:later_index;
 return depth_geometry_range(system,{reinterpret_cast<const uint8_t*>(&index),2},width,stride,fetch,fetch_size,reset);
}
uint64_t GetFh1OwnedGeometry(uint32_t address,uint32_t size){
 ++imports;if(!cache_hit)++fh1_geometry_imports_;assert(address==128 && size==initial_index*24+12);return import_ok?1234:0;
}
uint64_t run(bool owned_index=true,bool native_root=true){
 uint64_t depth_index_address=owned_index?5678:0,geometry_address=0;
 int root_signature_fh1_depth_=1,root_signature=native_root?1:2;
 struct {xenos::IndexFormat host_index_format=xenos::IndexFormat::kInt16;
  uint32_t host_draw_vertex_count=1,guest_index_base=64;
  bool host_primitive_reset_enabled=false;} primitive_processing_result;
 uint32_t system_constants_[8]={0,0,0,0xffffffff,0,0,0,0xffffff};
 uint32_t regs[192]={};regs[190]=128;regs[191]=128;
 const uint32_t fh1_depth_stride=24,XE_GPU_REG_SHADER_CONSTANT_FETCH_00_0=0;
 BLOCK
 return geometry_address;
}
bool admitted(uint64_t fh1_vertex_shader_hash,bool fh1_native_scene,bool pixel){
 struct {bool pixel_shader;} runtime_description{pixel};
 ADMISSION
 return fh1_native_depth;
}
bool missing_root(bool fh1_native_scene,uint64_t fh1_vertex_shader_hash,bool fh1_native_depth,bool layered,bool depth){
 struct {bool layered,depth;bool GetFh1LayeredRootSignature(){return layered;}bool GetFh1DepthRootSignature(){return depth;}} command_processor_{layered,depth};
 return MISSING;
}
void reset(){reads=imports=fail_read=initial_index=later_index=0;import_ok=true;cache_hit=false;fh1_geometry_imports_=0;}
int main(){
 for(uint64_t hash:{0x9BF2991815B941B9ull,0xC8C39E5AE1B08DE6ull,0xB646F85EF69A57E0ull,0xD0C40C04F166092Eull}){
  assert(admitted(hash,true,false));assert(!admitted(hash,false,false));assert(!admitted(hash,true,true));assert(!admitted(hash^1,true,false));
  assert(missing_root(true,hash,true,true,false));assert(!missing_root(true,hash,true,true,true));
 }
 assert(missing_root(true,0x3BC346726C1C2535ull,false,false,true));
 assert(!missing_root(false,0,false,false,false));
 reset();assert(run()==1234 && reads==2 && imports==1);
 reset();cache_hit=true;assert(run()==1234 && reads==1 && imports==1);
 reset();later_index=4;assert(run()==0 && reads==2 && imports==1);
 reset();initial_index=4;assert(run()==1234 && reads==2 && imports==1);
 reset();initial_index=6;assert(run()==0 && reads==1 && imports==0);
 reset();fail_read=1;assert(run()==0 && reads==1 && imports==0);
 reset();fail_read=2;assert(run()==0 && reads==2 && imports==1);
 reset();import_ok=false;assert(run()==0 && reads==1 && imports==1);
 reset();assert(run(false)==0 && reads==0 && imports==0);
 reset();assert(run(true,false)==0 && reads==0 && imports==0);
}
'''.replace('BLOCK', block).replace('ADMISSION', admission).replace('MISSING', missing)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'vertices.cpp'; exe = Path(temp)/'vertices.exe'
        cpp.write_text(code)
        subprocess.run([args.compiler, '-std=c++20', '-I'+str(repo/'thirdparty/shiftglue-sdk/include'), str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Depth vertex bounds, aliased imports and fallback checks passed')


if __name__ == '__main__':
    main()
