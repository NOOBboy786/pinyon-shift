"""Execute the shared lit/blended geometry loads at physical-memory boundaries."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    functions = (root/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_scene_geometry.hlsli').read_text().replace('[branch]', '')
    packed = (root/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_packed_world.vs.hlsl').read_text()
    packed_word = 'uint LoadWord' + packed.split('uint LoadWord', 1)[1].split('Vertex main', 1)[0]
    start = packed.index('  uint word=', packed.index('Vertex main'))
    normal = packed[start:packed.index(';', start) + 1]
    code = r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
using uint=uint32_t;
constexpr uint limit=1u<<29;
struct uint4{uint x,y,z,w;uint4()=default;uint4(uint a,uint b,uint c,uint d):x(a),y(b),z(c),w(d){}};
struct {uint x;} system_data[1];
struct Buffer {
 uint tag;
 uint Load(uint address){
#ifdef FH1_SCENE_OWNED_GEOMETRY
  assert(address<limit);
#endif
  assert(!(address&3));return address<limit?address^tag:0;
 }
 uint word(uint64_t address){return address<limit?Load(uint(address)):0;}
 uint4 Load4(uint address){
#ifdef FH1_SCENE_OWNED_GEOMETRY
  assert(address<=limit-16);
#endif
  return {word(address),word(uint64_t(address)+4),word(uint64_t(address)+8),word(uint64_t(address)+12)};
 }
} shared_srv{0x12345678},shared_uav{0x87654321};
uint4 fetch_data[48]{};
uint Endian(uint value,uint mode){assert(mode==0);return value;}
FUNCTIONS
PACKED_WORD
int main(){
 for(uint mode:{0u,1u})for(uint address:{0u,4u,limit-20,limit-16,limit-12,limit-8,limit-4,limit,limit+4,0xfffffff4u,0xfffffff8u,0xfffffffcu}){
  system_data[0].x=mode;uint tag=shared_srv.tag;
#ifndef FH1_SCENE_OWNED_GEOMETRY
  if(mode)tag=shared_uav.tag;
#endif
  auto value=LoadGeometry4(address);uint actual[]={value.x,value.y,value.z,value.w};
  for(uint i=0;i<4;++i){uint64_t offset=uint64_t(address)+4*i;assert(actual[i]==(offset<limit?uint(offset)^tag:0));}
  assert(LoadGeometryWord(address)==(address<limit?address^tag:0));
  PACKED_NORMAL
  uint normal_address=address+12;
  assert(word==(normal_address<limit?normal_address^tag:0));
 }
}
'''.replace('FUNCTIONS', functions).replace('PACKED_WORD', packed_word).replace('PACKED_NORMAL', normal)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'load.cpp'
        cpp.write_text(code)
        for owned in (False, True):
            exe = Path(temp)/f'load-{owned}.exe'
            defines = ['-DFH1_SCENE_OWNED_GEOMETRY=1'] if owned else []
            subprocess.run([args.compiler, '-std=c++20', *defines, str(cpp), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)
    print('Scene raw-load bounds, packed normal wrap and shared/UAV fallback checks passed')


if __name__ == '__main__':
    main()
