"""Execute mesh/scene draw ownership and post-import range revalidation."""
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
    block = source[start:source.index('  std::array<D3D12_GPU_VIRTUAL_ADDRESS, 2> terrain_addresses{};', start)]
    start = source.index('  if (fh1_vertex_hash == 0x3BC346726C1C2535ull &&')
    layered = source[start + 6:source.index(') {', start)]
    code = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include <optional>
#include <span>
#include <utility>
namespace xenos {enum class IndexFormat{kInt16,kInt32};}
constexpr uint32_t XE_GPU_REG_SHADER_CONSTANT_FETCH_00_0=0;
struct Harness {
 uint64_t fh1_geometry_imports_=0;
 uint32_t regs[192]{},system_constants_[8]{},expected_stride=0,expected_extent=0;
 bool proof_ok=true,import_ok=true,refresh=true;
 int proofs=0,imports=0,changed=0;
 std::optional<std::pair<uint32_t,uint32_t>> GetFh1DepthGeometryRange(
     uint32_t address,uint32_t bytes,std::span<const uint32_t,8> system,
     uint32_t width,uint32_t stride,uint32_t fetch_address,uint32_t fetch_size,
     bool reset,uint32_t extent){
  assert(address==64 && bytes==4 && width==2 && reset);
  assert(stride==expected_stride && extent==expected_extent);
  assert(fetch_address==128 && fetch_size==1024 && std::memcmp(system.data(),system_constants_,32)==0);
  ++proofs;if(!proof_ok || (proofs>1 && changed==1))return {};
  return std::pair{proofs>1 && changed==2?132u:128u,
      proofs>1 && changed==3?68u:proofs>1 && changed==4?32u:64u};
 }
 uint64_t GetFh1OwnedGeometry(uint32_t address,uint32_t bytes){
  assert(address==128 && bytes==64);++imports;if(refresh)++fh1_geometry_imports_;
  return import_ok?4224:0;
 }
 bool run(uint32_t fh1_scene_stride,uint32_t fh1_depth_stride=24,bool qualified=true){
  expected_stride=fh1_scene_stride?fh1_scene_stride:fh1_depth_stride;
  expected_extent=fh1_scene_stride?fh1_scene_stride:12;
  regs[190]=128;regs[191]=1024;
  uint64_t depth_index_address=4096,geometry_address=0;
  int fh1_mesh_root=fh1_scene_stride==16 || fh1_scene_stride==20?3:1,root_signature=qualified?fh1_mesh_root:4;
  struct {xenos::IndexFormat host_index_format=xenos::IndexFormat::kInt16;
   uint32_t host_draw_vertex_count=2,guest_index_base=64;bool host_primitive_reset_enabled=true;} primitive_processing_result;
  BLOCK
  assert(depth_index_address==(fh1_scene_stride && !geometry_address?0u:4096u));
  assert(!geometry_address || geometry_address==4224);return geometry_address!=0;
 }
};
struct PrimitiveProcessor {enum class ProcessedIndexBufferType{kNone,kGuestDMA};};
bool layered_proof(uint64_t fh1_vertex_hash,int root_signature,PrimitiveProcessor::ProcessedIndexBufferType type){
 int root_signature_fh1_layered_=3;struct {PrimitiveProcessor::ProcessedIndexBufferType index_buffer_type;} primitive_processing_result{type};
 return LAYERED;
}
int main(){
 for(uint64_t hash:{0x3BC346726C1C2535ull,0xAD2C355A6BE1EE87ull,0x8D8A197476841A9Aull,0x6934E161812AB10Bull})
  for(int root:{3,4})for(auto type:{PrimitiveProcessor::ProcessedIndexBufferType::kNone,PrimitiveProcessor::ProcessedIndexBufferType::kGuestDMA})
   assert(layered_proof(hash,root,type)==(hash==0x3BC346726C1C2535ull && root==3 && type==PrimitiveProcessor::ProcessedIndexBufferType::kNone));
 for(uint32_t scene:{0u,12u,16u,20u,28u}){
  for(bool refresh:{false,true}){Harness h;h.refresh=refresh;assert(h.run(scene));assert(h.proofs==(refresh?2:1));}
  {Harness h;h.proof_ok=false;assert(!h.run(scene) && !h.imports);}
  {Harness h;h.import_ok=false;assert(!h.run(scene) && h.proofs==1);}
  for(int changed=1;changed<=3;++changed){Harness h;h.changed=changed;assert(!h.run(scene) && h.proofs==2);}
  {Harness h;h.changed=4;assert(h.run(scene) && h.proofs==2);}
  {Harness h;assert(!h.run(scene,24,false) && !h.proofs && !h.imports);}
 }
 for(uint32_t stride:{20u,24u,28u,32u}){Harness h;assert(h.run(0,stride));}
}
'''.replace('BLOCK', block).replace('LAYERED', layered)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'mesh.cpp'
        exe = Path(temp)/'mesh.exe'
        cpp.write_text(code)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Mesh/scene read extents, import revalidation and fallback checks passed')


if __name__ == '__main__':
    main()
