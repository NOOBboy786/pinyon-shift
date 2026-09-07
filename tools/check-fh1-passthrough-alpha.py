"""Execute the passthrough shader's alpha test against comparison semantics."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default='clang++')
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_passthrough_color.ps.hlsl')
    args=parser.parse_args();source=args.source.read_text()
    alpha=re.search(r'bool AlphaTest\([^}]+\}',source).group()
    harness=r'''
#include <cassert>
#include <bit>
#include <cstdint>
#include <limits>
#include <initializer_list>
using uint=uint32_t;
struct {uint x,y,z,w;} xe_system[30];
float asfloat(uint x){return std::bit_cast<float>(x);}
ALPHA
int main(){
 float nan=std::numeric_limits<float>::quiet_NaN();
 for(uint compare=0;compare<8;++compare){
  xe_system[0].x=compare<<7;
  for(float reference:{-1.0f,0.0f,1.0f,nan}){
   xe_system[14].x=std::bit_cast<uint>(reference);
   for(float alpha:{-1.0f,0.0f,1.0f,nan}){
    bool expected;
    switch(compare){case 0:expected=false;break;case 1:expected=alpha<reference;break;
     case 2:expected=alpha==reference;break;case 3:expected=alpha<=reference;break;
     case 4:expected=alpha>reference;break;case 5:expected=alpha!=reference;break;
     case 6:expected=alpha>=reference;break;default:expected=true;}
    assert(AlphaTest(alpha)==expected);
   }
  }
 }
}
'''.replace('ALPHA',alpha)
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'alpha.cpp';exe=Path(temp)/'alpha.exe';cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print('Passthrough alpha comparison checks passed')


if __name__=='__main__':main()
