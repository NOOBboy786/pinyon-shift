"""Execute the depth shader's raw loads at the shared-memory boundary.

Reference: https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/ld-raw--sm5---asm-
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    shader = (repo/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_depth_mesh.vs.hlsl').read_text()
    functions = shader[shader.index('uint Swap8In16('):shader.index('float Fh1Mul(')].replace('[branch]', '')
    code = r'''
#include <cassert>
#include <algorithm>
#include <cstring>
#include <cstdint>
#include <initializer_list>
#define FH1_DEPTH_OWNED_GEOMETRY 1
using uint=uint32_t;
struct uint3 {uint x,y,z;uint3(uint a,uint b,uint c):x(a),y(b),z(c){}};
constexpr uint limit=1u<<29;
struct Buffer {
 uint Load(uint address){assert(address<limit && !(address&3));return address^0x12345678;}
 uint3 Load3(uint address){assert(address<=limit-12);return {Load(address),Load(address+4),Load(address+8)};}
} xe_shared_memory_srv;
FUNCTIONS
int main(){
 for(uint address:{0u,4u,limit-16,limit-12,limit-8,limit-4,limit,limit+4,0xfffffffcu})
  for(uint endian=0;endian<4;++endian){
   auto value=Load3(address,endian);uint actual[]={value.x,value.y,value.z};
   for(uint i=0;i<3;++i){uint64_t offset=uint64_t(address)+i*4;
    uint expected=0;
    if(offset<limit){
     uint word=uint(offset)^0x12345678;uint8_t bytes[4];std::memcpy(bytes,&word,4);
     if(endian==1 || endian==2){std::swap(bytes[0],bytes[1]);std::swap(bytes[2],bytes[3]);}
     if(endian==2 || endian==3){std::swap(bytes[0],bytes[2]);std::swap(bytes[1],bytes[3]);}
     std::memcpy(&expected,bytes,4);
    }
    assert(actual[i]==expected);
   }
  }
}
'''.replace('FUNCTIONS', functions)
    with tempfile.TemporaryDirectory() as temp:
        cpp = Path(temp)/'load.cpp'; exe = Path(temp)/'load.exe'; cpp.write_text(code)
        subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Depth raw-load boundary and endian checks passed')


if __name__ == '__main__':
    main()
