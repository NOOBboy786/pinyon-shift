"""Compile the qualified RMS downsample admission predicate."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='clang++')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
source = (repo / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
start = source.index('  const bool fh1_rms_downsample =')
gate = source[start:source.index(';', start) + 1]
assert 'false &&' not in gate
assert 'FAILED(create_result) && (fh1_video_pixel || fh1_postprocess_center || fh1_rms_downsample ||' in source
gate = gate.replace('false &&', '').replace('const bool fh1_rms_downsample =', 'return')
harness = r'''
#include <cassert>
#include <cstdint>
struct RenderTargetCache {
 enum class Path {kHostRenderTargets,kOther}; Path path=Path::kHostRenderTargets;
 int x=2,y=2; Path GetPath(){return path;}
 int draw_resolution_scale_x(){return x;} int draw_resolution_scale_y(){return y;}
};
struct Description {
 uint64_t vertex_shader_hash=0x2C53E1A563484076ull,pixel_shader_hash=0xE17BECBE8BE65806ull;
 uint64_t vertex_shader_modification=1,pixel_shader_modification=0x0000400000000001ull;
};
bool admits(Description description={},RenderTargetCache render_target_cache_={},bool bindless_resources_used_=true){GATE}
int main(){
 assert(admits()); assert(!admits({},{},false));
 for(unsigned bit=0;bit<64;++bit){
  Description d; d.vertex_shader_hash^=1ull<<bit; assert(!admits(d));
  d={};d.pixel_shader_hash^=1ull<<bit; assert(!admits(d));
  d={};d.vertex_shader_modification^=1ull<<bit; assert(!admits(d));
  d={};d.pixel_shader_modification^=1ull<<bit; assert(!admits(d));
 }
 for(int x=1;x<=3;++x)for(int y=1;y<=3;++y){
  RenderTargetCache t;t.x=x;t.y=y;assert(admits({},t)==((x==1||x==2)&&y==x));
 }
 RenderTargetCache t;t.path=RenderTargetCache::Path::kOther;assert(!admits({},t));
}
'''.replace('GATE', gate)
with tempfile.TemporaryDirectory(prefix='fh1-rms-') as temp:
    cpp, exe = Path(temp) / 'check.cpp', Path(temp) / 'check.exe'
    cpp.write_text(harness)
    subprocess.run([args.compiler, '-std=c++20', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('RMS admission exclusions and fallback checks pass')
