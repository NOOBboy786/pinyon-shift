"""Check terrain depth transform order, interpolation saturation and guest zero multiply."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default='clang++')
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_terrain_depth.vs.hlsl')
    args=parser.parse_args();source=args.source.read_text()
    multiply=re.search(r'float Fh1Mul\([^}]+\}',source).group().replace('precise ','')
    transform=source.split('#ifdef FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM',1)[1].split('#else',1)[0]
    for component in 'xyz':transform=transform.replace('.'+component*4,'.'+component)
    offset=source.split('#ifdef FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM',1)[1].split('#else',1)[1].split('#endif',1)[0].replace('precise ','')
    for swizzle in ('zzzz','yyyy','xxxx','xwzy','xywz','xwyz'):offset=offset.replace('.'+swizzle,'.'+swizzle+'()')
    height=re.search(r'precise float height = [^;]+;',source).group().replace('precise ','')
    harness=r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>
using std::abs;using std::min;
float saturate(float x){return std::clamp(x,0.0f,1.0f);}
MULTIPLY
struct float4 {
 float x,y,z,w;
 float4 operator+(float4 b)const{return {x+b.x,y+b.y,z+b.z,w+b.w};}
 float4 xxxx()const{return {x,x,x,x};} float4 yyyy()const{return {y,y,y,y};}
 float4 zzzz()const{return {z,z,z,z};}
 float4 xwzy()const{return {x,w,z,y};} float4 xywz()const{return {x,y,w,z};}
 float4 xwyz()const{return {x,w,y,z};}
};
float4 operator*(float a,float4 b){return {a*b.x,a*b.y,a*b.z,a*b.w};}
float4 Fh1Mul(float4 a,float4 b){return {Fh1Mul(a.x,b.x),Fh1Mul(a.y,b.y),Fh1Mul(a.z,b.z),Fh1Mul(a.w,b.w)};}
float rcp(float x){return 1.0f/x;}
float4 offset_transform(float4 position,float4* c){float4 output;OFFSET return output;}
int main(){
 float4 matrix[11]={{1,2,3,4},{5,6,7,8},{9,10,11,12},{13,14,15,16}};
 float4 transformed=offset_transform({2,3,5,1},matrix);
 assert(transformed.x==75 && transformed.z==97 && transformed.w==108);
 assert(transformed.y==Fh1Mul(Fh1Mul(86,rcp(108)),108));
 assert(Fh1Mul(0,std::numeric_limits<float>::infinity())==0);
 assert(Fh1Mul(2,3)==6);
 struct {float x,y,z;} position{1,1,1};
 float c[]{1,1,-1e20f,1e20f};float output;
 TRANSFORM
 assert(output==2);
 for(float input:{-2.0f,2.0f}){
  struct {float x,y;} y_lerp{input,input};struct {float z;} fraction{0.5f};
  HEIGHT
  assert(height==(input<0?0:1));
 }
}
'''.replace('MULTIPLY',multiply).replace('TRANSFORM',transform).replace('HEIGHT',height).replace('OFFSET',offset)
    assert 'precise float4 output;' in source
    assert 'output.xyz = mad(asfloat(xe_system[9].xyz), output.w, scaled_position);' in source
    assert 'output.w = 1.0 / output.w;' in source
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'terrain.cpp';exe=Path(temp)/'terrain.exe';cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20','-ffp-contract=off',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print('Terrain depth arithmetic checks passed')


if __name__=='__main__':main()
