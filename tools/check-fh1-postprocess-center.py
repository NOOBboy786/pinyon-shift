"""Compile the disabled post-process admission predicate."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default='clang++')
a=p.parse_args()
s=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
start=s.index('  const bool fh1_postprocess_center =')
gate=s[start:s.index(';',start)+1]
assert 'false &&' in gate
assert 'FAILED(create_result) && (fh1_video_pixel || fh1_postprocess_center ||' in s
gate=gate.replace('false &&','').replace('const bool fh1_postprocess_center =','return')
code=r'''
#include <cassert>
#include <cstdint>
#include <bit>
#include <cmath>
#include <limits>
using uint=uint32_t;
uint flags,reference_bits;
float asfloat(uint bits){return std::bit_cast<float>(bits);}
struct RenderTargetCache {
 enum class Path {kHostRenderTargets,kOther}; Path path=Path::kHostRenderTargets;
 int x=2,y=2;Path GetPath(){return path;}
 int draw_resolution_scale_x(){return x;}int draw_resolution_scale_y(){return y;}
};
struct Description {
 uint64_t vertex_shader_hash=0x20A41D46F34D238Eull,pixel_shader_hash=0x614588022744BF6Bull;
 uint64_t vertex_shader_modification=7,pixel_shader_modification=0x0000400000000007ull;
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
 for(int x=1;x<=3;++x)for(int y=1;y<=3;++y){RenderTargetCache t;t.x=x;t.y=y;assert(admits({},t)==(x==2&&y==2));}
 RenderTargetCache t;t.path=RenderTargetCache::Path::kOther;assert(!admits({},t));

}
'''.replace('GATE',gate)
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check.exe';cpp.write_text(code)
    subprocess.run([a.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Post-process disabled admission, exclusions and creation fallback checks passed')
