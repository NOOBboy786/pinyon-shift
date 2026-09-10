"""Compile the qualified video-pixel admission predicate and alpha comparisons."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default='clang++')
a=p.parse_args()
s=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
start=s.index('  const bool fh1_video_pixel =')
gate=s[start:s.index(';',start)+1]
assert 'false &&' not in gate
assert 'FAILED(create_result) && (fh1_video_pixel ||' in s
gate=gate.replace('false &&','').replace('const bool fh1_video_pixel =','return')
shader=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_video_color.ps.hlsl').read_text()
alpha=shader[shader.index('bool AlphaTest'):shader.index('uint AlphaCoverage')]
alpha=alpha.replace('xe_system[0].x','flags').replace('xe_system[14].x','reference_bits')
code=r'''
#include <cassert>
#include <cstdint>
#include <bit>
#include <cmath>
#include <limits>
using uint=uint32_t;
uint flags,reference_bits;
float asfloat(uint bits){return std::bit_cast<float>(bits);}
ALPHA
struct RenderTargetCache {
 enum class Path {kHostRenderTargets,kOther}; Path path=Path::kHostRenderTargets;
 int x=2,y=2;Path GetPath(){return path;}
 int draw_resolution_scale_x(){return x;}int draw_resolution_scale_y(){return y;}
};
struct Description {
 uint64_t vertex_shader_hash=0x7156CE05C6365E51ull,pixel_shader_hash=0x31511D87CC0C94B9ull;
 uint64_t vertex_shader_modification=1,pixel_shader_modification=1;
};
bool admits(Description description={},RenderTargetCache render_target_cache_={},bool bindless_resources_used_=true){GATE}
int main(){
 assert(admits());assert(!admits({},{},false));
 for(unsigned bit=0;bit<64;++bit){
  Description d;d.vertex_shader_hash^=1ull<<bit;assert(!admits(d));
  d={};d.pixel_shader_hash^=1ull<<bit;assert(!admits(d));
  d={};d.vertex_shader_modification^=1ull<<bit;assert(!admits(d));
  d={};d.pixel_shader_modification^=1ull<<bit;assert(!admits(d));
 }
 for(int x=1;x<=3;++x)for(int y=1;y<=3;++y){RenderTargetCache t;t.x=x;t.y=y;assert(admits({},t)==((x==1||x==2)&&y==x));}
 RenderTargetCache t;t.path=RenderTargetCache::Path::kOther;assert(!admits({},t));
 float values[]={-INFINITY,-1.0f,-0.0f,0.0f,0.5f,1.0f,INFINITY,std::numeric_limits<float>::quiet_NaN()};
 for(float a:values)for(float b:values)for(uint compare=0;compare<8;++compare){
  flags=compare<<7;reference_bits=std::bit_cast<uint>(b);
  bool expected[]={false,a<b,a==b,a<=b,a>b,a!=b,a>=b,true};
  assert(AlphaTest(a)==expected[compare]);
 }
}
'''.replace('GATE',gate).replace('ALPHA',alpha)
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check.exe';cpp.write_text(code)
    subprocess.run([a.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Video pixel admission exclusions, alpha comparisons and fallback guard passed')
