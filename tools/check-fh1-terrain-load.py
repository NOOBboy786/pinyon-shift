"""Execute terrain's production raw loads across physical bounds and bindings."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    shader = (repo/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_terrain_depth.vs.hlsl').read_text()
    functions = shader[shader.index('uint Swap8In16('):shader.index('int SignExtend(')].replace('[branch]', '')
    code = r'''
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <initializer_list>
using uint=uint32_t;
struct uint2 {uint x,y; uint2(uint a,uint b):x(a),y(b){}};
struct uint4 {uint x,y,z,w; uint4(uint a,uint b,uint c,uint d):x(a),y(b),z(c),w(d){}};
constexpr uint limit=1u<<29;
struct Buffer {
 uint tag;
 uint Load(uint address) {assert(address<limit && !(address&3));return address^tag;}
 uint word(uint64_t address) {return address<limit ? Load(uint(address)) : 0;}
 uint2 Load2(uint address) {
#ifdef FH1_TERRAIN_OWNED_GEOMETRY
  assert(address<=limit-8);
#endif
  return {word(address),word(uint64_t(address)+4)};
 }
 uint4 Load4(uint address) {
#ifdef FH1_TERRAIN_OWNED_GEOMETRY
  assert(address<=limit-16);
#endif
  return {word(address),word(uint64_t(address)+4),word(uint64_t(address)+8),word(uint64_t(address)+12)};
 }
};
#ifdef FH1_TERRAIN_OWNED_GEOMETRY
Buffer xe_shared_memory_srv{0x12345678},terrain_direction_srv{0x87654321},terrain_control_srv{0xabcdef01};
#else
// Descriptor-based shared loads return zero out of bounds.
struct SharedBuffer:Buffer {uint Load(uint address){return address<limit ? Buffer::Load(address) : 0;}};
SharedBuffer xe_shared_memory_srv{{0x12345678}},xe_shared_memory_uav{{0x87654321}};
struct {uint x;} xe_system[1];
#endif
FUNCTIONS
uint expected(uint64_t address,uint tag,uint endian) {
 if(address>=limit)return 0;
 uint word=uint(address)^tag;uint8_t bytes[4];std::memcpy(bytes,&word,4);
 if(endian==1 || endian==2){std::swap(bytes[0],bytes[1]);std::swap(bytes[2],bytes[3]);}
 if(endian==2 || endian==3){std::swap(bytes[0],bytes[2]);std::swap(bytes[1],bytes[3]);}
 std::memcpy(&word,bytes,4);return word;
}
int main(){
 for(uint uav=0;uav<2;++uav)
  for(uint address:{0u,4u,limit-20,limit-16,limit-12,limit-8,limit-4,limit,limit+4,0xfffffffcu})
   for(uint endian=0;endian<4;++endian){
#ifdef FH1_TERRAIN_OWNED_GEOMETRY
    uint vertex_tag=xe_shared_memory_srv.tag,direction_tag=terrain_direction_srv.tag,control_tag=terrain_control_srv.tag;
#else
    xe_system[0].x=uav;
    uint vertex_tag=uav?xe_shared_memory_uav.tag:xe_shared_memory_srv.tag;
    uint direction_tag=vertex_tag,control_tag=vertex_tag;
#endif
    auto vertex=LoadVertex(address,endian);auto control=Load4(address,endian);
    assert(vertex.x==expected(address,vertex_tag,endian));
    assert(vertex.y==expected(uint64_t(address)+4,vertex_tag,endian));
    assert(LoadWord(address,endian)==expected(address,direction_tag,endian));
    uint actual[]={control.x,control.y,control.z,control.w};
    for(uint i=0;i<4;++i)assert(actual[i]==expected(uint64_t(address)+4*i,control_tag,endian));
   }
}
'''.replace('FUNCTIONS', functions)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'load.cpp'
        cpp.write_text(code)
        for owned in (False, True):
            exe = Path(temp)/f'load-{owned}.exe'
            defines = ['-DFH1_TERRAIN_OWNED_GEOMETRY=1'] if owned else []
            subprocess.run([args.compiler, '-std=c++20', *defines, str(cpp), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)
    print('Terrain raw-load resource, boundary, endian and shared/UAV checks passed')


if __name__ == '__main__':
    main()
