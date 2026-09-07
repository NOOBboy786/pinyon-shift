"""Execute production layered raw loads at the physical-memory boundary."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    shader = (repo/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_layered_scene.vs.hlsl').read_text()
    functions = shader[shader.index('uint Endian('):shader.index('struct Vertex')].replace('[branch]', '')
    code = r'''
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <initializer_list>
using uint=uint32_t;
constexpr uint limit=1u<<29;
struct {uint w;} fetch_data[48];
struct {uint Load(uint address){assert(address<limit && !(address&3));return address^0x12345678;}} shared_srv;
FUNCTIONS
int main(){
 for(uint address:{0u,4u,limit-8,limit-4,limit,limit+4,0xfffffffcu})
  for(uint mode=0;mode<4;++mode){
   fetch_data[47].w=mode;uint expected=0;
   if(address<limit){
    uint word=address^0x12345678;uint8_t bytes[4];std::memcpy(bytes,&word,4);
    if(mode==1 || mode==2){std::swap(bytes[0],bytes[1]);std::swap(bytes[2],bytes[3]);}
    if(mode==2 || mode==3){std::swap(bytes[0],bytes[2]);std::swap(bytes[1],bytes[3]);}
    std::memcpy(&expected,bytes,4);
   }
   assert(LoadWord(address)==expected);
  }
}
'''.replace('FUNCTIONS', functions)
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'load.cpp'; exe=Path(temp)/'load.exe'; cpp.write_text(code)
        subprocess.run([args.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print('Layered raw-load bounds and endian checks passed')


if __name__ == '__main__':
    main()
