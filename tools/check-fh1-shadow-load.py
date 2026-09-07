"""Execute the production shadow Load3 at physical-memory boundaries."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', default='clang++')
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
source = (root/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_shadow_mask.vs.hlsl').read_text()
functions = source[source.index('uint Swap8In16'):source.index('float Fh1Mul')].replace('[branch]', '')
code = r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
using uint=uint32_t;
constexpr uint limit=1u<<29;
struct uint3{uint x,y,z;uint3(uint a,uint b,uint c):x(a),y(b),z(c){};uint3()=default;};
struct {uint x;} xe_system[1];
struct Buffer {
 uint tag;
 uint Load(uint address){
#ifdef FH1_SCENE_OWNED_GEOMETRY
  assert(address<limit);
#endif
  assert(!(address&3));return address<limit?address^tag:0;
 }
 uint word(uint64_t address){return address<limit?Load(uint(address)):0;}
 uint3 Load3(uint address){
#ifdef FH1_SCENE_OWNED_GEOMETRY
  assert(address<=limit-12);
#endif
  return {word(address),word(uint64_t(address)+4),word(uint64_t(address)+8)};
 }
} xe_shared_memory_srv{0x12345678},xe_shared_memory_uav{0x87654321};
FUNCTIONS
int main(){
 for(uint mode:{0u,1u})for(uint endian:{0u,1u,2u,3u})
 for(uint address:{0u,4u,limit-16,limit-12,limit-8,limit-4,limit,limit+4,0xfffffff8u,0xfffffffcu}){
  xe_system[0].x=mode;uint tag=xe_shared_memory_srv.tag;
#ifndef FH1_SCENE_OWNED_GEOMETRY
  if(mode)tag=xe_shared_memory_uav.tag;
#endif
  auto v=Load3(address,endian);uint actual[]={v.x,v.y,v.z};
  for(uint i=0;i<3;++i){uint64_t offset=uint64_t(address)+4*i;uint expected=offset<limit?uint(offset)^tag:0;
   if(endian==1||endian==2)expected=((expected&0x00FF00FF)<<8)|((expected>>8)&0x00FF00FF);
   if(endian==2||endian==3)expected=(expected<<16)|(expected>>16);
   assert(actual[i]==expected);
  }
 }
}
'''.replace('FUNCTIONS', functions)
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'check.cpp';cpp.write_text(code)
    for owned in (False,True):
        exe=Path(tmp)/f'check-{owned}.exe'
        defines=['-DFH1_SCENE_OWNED_GEOMETRY=1'] if owned else []
        subprocess.run([a.compiler,'-std=c++20',*defines,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('Shadow Load3 physical bounds, endian and shared/UAV checks passed')
