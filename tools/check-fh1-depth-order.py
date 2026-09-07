"""Check the production depth shader's distinct model/projection sum orders."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1] /
                        'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_depth_mesh.vs.hlsl')
    args = parser.parse_args()
    source = args.source.read_text()
    methods = '\n'.join(re.search(r'float '+name+r'\([^}]+\}', source).group() for name in ('Fh1Mul', 'Fh1Dot4'))
    projection = source[source.index('float4 position = float4('):source.index('  if (!(xe_system[0].x & 8))')]
    harness = r'''
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <iostream>
using std::min;using std::abs;
struct float4 {
  float x,y,z,w;
  float4(float a,float b,float c,float d):x(a),y(b),z(c),w(d){}
  float4 zxwy()const{return {z,x,w,y};}
};
METHODS
int main() try {
  float4 a(1e20f,1,-1e20f,1),b(1,1,1,1);
  if(Fh1Dot4(a,b)!=2)throw std::runtime_error("model order changed");
  float4 c[]={a,a,a,a,a,a,a,a,a,a};float4 view_position=b;
  PROJECTION
  if(position.x!=1 || position.y!=1 || position.z!=1 || position.w!=1)
    throw std::runtime_error("projection must accumulate w,z,x,y");
} catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
'''.replace('METHODS', methods.replace('precise ', '')).replace('PROJECTION', projection.replace('.zxwy', '.zxwy()'))
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'order.cpp';exe=Path(temp)/'order.exe'
        cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20','-ffp-contract=off',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    assert 'precise float4 position = float4(' in source, 'Final viewport arithmetic must stay precise'
    print('Depth model/projection order and precise output checks passed')


if __name__=='__main__':main()
