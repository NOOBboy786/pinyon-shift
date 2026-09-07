"""Execute terrain's actual draw admission, constant packing and import fallback."""
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
    start = source.index('  std::array<D3D12_GPU_VIRTUAL_ADDRESS, 2> terrain_addresses{};')
    block = source[start:source.index('  // Ensure vertex buffers are resident.', start)]
    code = r'''
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <optional>
#include <span>
#include <utility>
using D3D12_GPU_VIRTUAL_ADDRESS=uint64_t;
namespace xenos {enum class IndexFormat{kInt16,kInt32};}
namespace rex {bool bit_scan_forward(uint64_t bits,uint32_t* index){if(!bits)return false;*index=std::countr_zero(bits);return true;}}
constexpr uint32_t XE_GPU_REG_SHADER_CONSTANT_000_X=0,XE_GPU_REG_SHADER_CONSTANT_FETCH_00_0=1024;
struct Map {uint64_t float_bitmap[4]{};uint32_t float_count=11;bool float_dynamic_addressing=false;};
struct Shader {Map map;const Map& constant_register_map(){return map;}};
using Ranges=std::array<std::pair<uint32_t,uint32_t>,3>;
struct Harness {
 Shader shader;Shader* vertex_shader=&shader;
 uint32_t regs[1216]{},system_constants_[8]{};
 float expected[44]{};
 uint64_t fh1_geometry_imports_=0;
 bool proof_ok=true,refresh=true,stale=false,inactive=false;
 int fail_import=0,proofs=0,imports=0,changed_range=0;
 std::optional<Ranges> GetFh1TerrainGeometryRanges(uint32_t address,uint32_t size,
     std::span<const uint32_t,8> system,uint32_t width,bool reset,
     std::span<const float,44> constants,std::span<const uint32_t,6> fetches){
  assert(address==64 && size==4 && width==2 && reset);
  assert(std::memcmp(system.data(),system_constants_,32)==0);
  assert(std::memcmp(constants.data(),expected,shader.map.float_count*16)==0);
  if(shader.map.float_count==10)for(int i=40;i<44;++i)assert(constants[i]==0);
  for(int i=0;i<6;++i)assert(fetches[i]==uint32_t(100+i));
  ++proofs;if(!proof_ok || (stale && proofs>1))return {};
  Ranges result{{{128,64},{256,inactive?0u:32u},{512,128}}};
  if(proofs>1 && changed_range){
   auto& range=result[(changed_range-1)/2];
   if(changed_range%2)range.first+=4;else range.second+=4;
  }
  return result;
 }
 uint64_t GetFh1OwnedGeometry(uint32_t address,uint32_t size){
  assert(size);++imports;if(refresh)++fh1_geometry_imports_;
  return imports==fail_import?0:address+4096;
 }
 Harness(uint32_t count=11){
  shader.map.float_count=count;
  const uint32_t slots[]={3,7,64,90,128,130,190,192,253,254,255};
  for(uint32_t i=0;i<count;++i){
   shader.map.float_bitmap[slots[i]/64]|=uint64_t(1)<<(slots[i]%64);
   for(uint32_t j=0;j<4;++j)expected[i*4+j]=float(i*4+j)+0.5f;
   std::memcpy(regs+slots[i]*4,expected+i*4,16);
  }
  const uint32_t streams[]={95,90,89};
  for(uint32_t i=0;i<3;++i)for(uint32_t j=0;j<2;++j)regs[1024+streams[i]*2+j]=100+i*2+j;
 }
 bool run(){
  bool fh1_terrain_depth=true;
  uint64_t geometry_address=0,depth_index_address=4096;
  int root_signature_fh1_terrain_=2,root_signature=2;
  struct {xenos::IndexFormat host_index_format=xenos::IndexFormat::kInt16;
   uint32_t host_draw_vertex_count=2,guest_index_base=64;bool host_primitive_reset_enabled=true;} primitive_processing_result;
  BLOCK
  if(!geometry_address){assert(depth_index_address==0 && terrain_addresses[0]==0 && terrain_addresses[1]==0);return false;}
  assert(geometry_address==4224 && depth_index_address==4096 && terrain_addresses[1]==4608);
  assert(terrain_addresses[0]==(inactive?0:4352));return true;
 }
};
int main(){
 for(uint32_t count:{10u,11u})for(bool refresh:{false,true})for(bool inactive:{false,true}){
  Harness h(count);h.refresh=refresh;h.inactive=inactive;assert(h.run());
  assert(h.proofs==(refresh?2:1) && h.imports==(inactive?2:3));
 }
 for(int fail=1;fail<=3;++fail){Harness h;h.fail_import=fail;assert(!h.run() && h.imports==fail && h.proofs==1);}
 {Harness h;h.proof_ok=false;assert(!h.run() && h.imports==0);}
 {Harness h;h.stale=true;assert(!h.run() && h.proofs==2);}
 for(int changed=1;changed<=6;++changed){Harness h;h.changed_range=changed;assert(!h.run() && h.proofs==2);}
 {Harness h;h.shader.map.float_dynamic_addressing=true;assert(!h.run() && h.proofs==0);}
 {Harness h;h.shader.map.float_count=9;assert(!h.run() && h.proofs==0);}
 {Harness h;h.shader.map.float_count=12;assert(!h.run() && h.proofs==0);}
 {Harness h;h.shader.map.float_bitmap[0]|=1;assert(!h.run() && h.proofs==0);}
 {Harness h;h.shader.map.float_bitmap[0]&=~(uint64_t(1)<<3);assert(!h.run() && h.proofs==0);}
}
'''.replace('BLOCK', block)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'terrain.cpp'
        exe = Path(temp)/'terrain.exe'
        cpp.write_text(code)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Terrain constant packing, complete ownership and import fallback checks passed')


if __name__ == '__main__':
    main()
