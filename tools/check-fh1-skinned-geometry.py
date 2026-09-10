"""Check B848 transform bounds and unsigned address rebasing, with optional capture evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default='clang++')
p.add_argument('--fixtures',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
source=(root/'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
start=source.index('  const bool fh1_skinned =')
ownership=source[start:source.index('  if (fh1_terrain_depth &&',start)]
code=r'''
#include <rex/graphics/d3d12/fh1_geometry.h>
#include <cassert>
#include <cfenv>
using namespace rex::graphics::d3d12;
void check(float offset,uint32_t address,uint32_t size){
 auto range=skinned_transform_range(offset,address,size);assert(range);
 const uint32_t origin=range->first & ~15u;
 const uint32_t rebased=address-origin;
 for(uint32_t byte=0;byte<256;++byte){
  volatile float sum=offset+float(byte);
  uint32_t index=uint32_t(std::floor(sum));
  for(uint32_t component=0;component<3;++component){
   uint64_t guest=uint64_t(address & ~3u)+uint64_t(index)*12+component*4;
   assert(guest>=range->first && guest+4<=uint64_t(range->first)+range->second);
   uint32_t local=(rebased & ~3u)+index*12+component*4;
   assert(uint64_t(origin)+local==guest);
  }
 }
}
using D3D12_GPU_VIRTUAL_ADDRESS=uint64_t;
namespace xenos {enum class IndexFormat{kInt16,kInt32};}
bool snapshot_valid,change_snapshot,import_ok,cache_hit;int snapshot_reads;
uint64_t fh1_geometry_imports_;
template<class... T> auto GetFh1DepthGeometryRange(T&&...){
 ++snapshot_reads;
 return snapshot_valid ? std::optional(std::pair(64u,change_snapshot&&snapshot_reads>1?128u:64u)) : std::nullopt;
}
uint64_t GetFh1OwnedGeometry(uint32_t address,uint32_t size){assert(address==0x1000&&size==3072);if(import_ok&&!cache_hit)++fh1_geometry_imports_;return import_ok?333:0;}
void ownership_check(bool valid,bool palette_valid,bool available,bool changed,bool hit){
 snapshot_valid=valid;change_snapshot=changed;import_ok=available;snapshot_reads=0;
 cache_hit=hit;fh1_geometry_imports_=0;
 uint32_t regs[2048]{};constexpr uint32_t XE_GPU_REG_SHADER_CONSTANT_000_X=0,XE_GPU_REG_SHADER_CONSTANT_FETCH_00_0=1024;
 regs[1024+188]=0x1003;regs[1024+189]=palette_valid?4096:0;
 uint32_t system_constants_[8]{};
 struct {xenos::IndexFormat host_index_format=xenos::IndexFormat::kInt16;uint32_t host_draw_vertex_count=2,guest_index_base=64;bool host_primitive_reset_enabled=false;} primitive_processing_result;
 uint64_t geometry_address=111,depth_index_address=222;std::array<uint64_t,2> terrain_addresses{};
 int root_signature_fh1_skinned_=1,root_signature=1;
 OWNERSHIP
 const bool success=valid&&palette_valid&&available&&(!changed||hit);
 assert(bool(geometry_address)==success&&bool(depth_index_address)==success&&bool(terrain_addresses[0])==success);
 assert(snapshot_reads==(valid&&palette_valid&&available&&!hit?2:1));
}
int main(){
 for(bool valid:{false,true})for(bool palette:{false,true})for(bool available:{false,true})for(bool changed:{false,true})for(bool hit:{false,true})ownership_check(valid,palette,available,changed,hit);

 constexpr uint32_t address=0x1003,size=0x100000;
 auto run=[&](float o){return skinned_transform_range(o,address,size);};
 assert(run(0)==std::pair(0x1000u,3072u));
 assert(run(66234)->second==3072);
 for(float o:{0.0f,0.25f,100.0f,66234.0f,123120.0f})check(o,address,0x400000);
 assert(!run(-1));assert(!run(std::numeric_limits<float>::infinity()));
 assert(!run(std::numeric_limits<float>::quiet_NaN()));assert(!run(2147483648.0f));
 assert(!skinned_transform_range(0,address,3068));
 assert(skinned_transform_range(0,address,3072));
 assert(!skinned_transform_range(0,0x1ffffffcu,3072));
 assert(!skinned_transform_range(0,address,0));
 for(int mode:{FE_TONEAREST,FE_UPWARD,FE_DOWNWARD,FE_TOWARDZERO}){
  assert(std::fesetround(mode)==0);
  for(float offset:{0.0f,0.99999994f,1023.99994f,123120.25f})check(offset,address,0x400000);
 }
 std::fesetround(FE_TONEAREST);
 FIXTURES
}
'''
fixtures=[]
if a.fixtures:
 report=json.loads(a.fixtures.read_text());assert 'error' not in report and report['draws']
 for d in report['draws']:
  assert d['primary_fits'] and d['transform_fits']
  address,size=d['transform_fetch'];offset=d['offset']
  fixtures.append(f'check({offset}f,{address}u,{size}u);')
code=code.replace('OWNERSHIP',ownership)
code=code.replace('FIXTURES','\n'.join(fixtures))
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check.exe';cpp.write_text(code)
 subprocess.run([a.compiler,'-std=c++20','-I'+str(root/'thirdparty/shiftglue-sdk/include'),str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print(f'Skinned transform range checks passed ({len(fixtures)} captured draws)')
