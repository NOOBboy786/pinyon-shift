"""Compile production shadow and standalone vertex admission gates."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default='clang++')
a=p.parse_args()
s=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
assert 'const bool fh1_skinned_geometry = false &&' in s, 'ownership must stay disabled until its performance gate passes'
i=s.index('  return',s.index('bool PipelineCache::IsFh1NativeShadowPipeline'))
gate=s[i:s.index(';',i)+1].replace('  return','  const bool fh1_shadow_mask_pixel =',1)
j=s.index("  return",s.index("bool PipelineCache::IsFh1NativeShadowVertex"))
vertex_gate=s[j:s.index(";",j)+1]
j=s.index("  return",s.index("bool PipelineCache::IsFh1NativeStandaloneVertex"))
standalone_gate=s[j:s.index(";",j)+1].replace('IsFh1NativeShadowVertex(hash, modification)', 'admits_vertex(hash, modification, bindless_resources_used_)')
j=s.index("  return",s.index("bool PipelineCache::IsFh1NativePositionPipeline"))
position_gate=s[j:s.index(";",j)+1].replace('IsFh1NativeStandaloneVertex(description.vertex_shader_hash, description.vertex_shader_modification)', 'standalone(description.vertex_shader_hash, description.vertex_shader_modification, bindless_resources_used_)')
code=r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
struct RenderTargetCache{enum class Path{kHostRenderTargets,kPixelShaderInterlock};Path path=Path::kHostRenderTargets;int x=2,y=2;Path GetPath(){return path;}int draw_resolution_scale_x(){return x;}int draw_resolution_scale_y(){return y;}} render_target_cache_;
struct Description{uint64_t vertex_shader_hash=0xA3B9ED5D5C87230Eull,vertex_shader_modification=1,pixel_shader_hash=0x93626E75D17576C5ull,pixel_shader_modification=0x0000400300000001ull;};
bool admits_vertex(uint64_t hash,uint64_t modification,bool bindless_resources_used_=true){VERTEX_GATE}
bool standalone(uint64_t hash,uint64_t modification,bool bindless_resources_used_=true){STANDALONE_GATE}
bool position(Description description,bool bindless_resources_used_=true){POSITION_GATE}
bool admits(Description description,bool bindless_resources_used_=true){auto IsFh1NativeShadowVertex = [&](uint64_t hash,uint64_t modification){return admits_vertex(hash,modification,bindless_resources_used_);}; GATE return fh1_shadow_mask_pixel;}
int main(){
 for(int x=1;x<=4;++x)for(int y=1;y<=4;++y)for(uint64_t mod:{0ull,1ull,0x1Full,0x3Full,~0ull}){
  render_target_cache_={};render_target_cache_.x=x;render_target_cache_.y=y;
  assert(standalone(0xB8489164D5A86043ull,mod)==(mod==0x1F&&x==2&&y==2));
  assert(!standalone(0xB8489164D5A86043ull,mod,false));
  render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;
  assert(!standalone(0xB8489164D5A86043ull,mod));
 }
 render_target_cache_={};
 for(int bit=0;bit<64;++bit){
  assert(!standalone(0xB8489164D5A86043ull^(uint64_t(1)<<bit),0x1F));
  assert(!standalone(0xB8489164D5A86043ull,0x1Full^(uint64_t(1)<<bit)));
 }
 for(uint64_t mod:{0x0000400000000001ull,0x0000400000010001ull}){
  render_target_cache_={};Description d;d.vertex_shader_hash=0x1E6883FCCDE1F688ull;d.pixel_shader_hash=0xA4A965C189287B99ull;d.pixel_shader_modification=mod;
  assert(position(d));assert(!position(d,false));
  for(int i=0;i<64;++i){auto v=d;v.vertex_shader_hash^=uint64_t(1)<<i;assert(!position(v));v=d;v.vertex_shader_modification^=uint64_t(1)<<i;assert(!position(v));v=d;v.pixel_shader_hash^=uint64_t(1)<<i;assert(!position(v));v=d;v.pixel_shader_modification^=uint64_t(1)<<i;assert(position(v)==(i==16));}
  for(int x=1;x<=4;++x)for(int y=1;y<=4;++y){render_target_cache_.x=x;render_target_cache_.y=y;assert(position(d)==((x==1||x==2)&&x==y));}
  render_target_cache_={};render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;assert(!position(d));
 }

 for(int x=1;x<=4;++x)for(int y=1;y<=4;++y)for(uint64_t mod:{0ull,1ull,2ull,~0ull}){
  render_target_cache_={};render_target_cache_.x=x;render_target_cache_.y=y;
  assert(standalone(0x1E6883FCCDE1F688ull,mod)==(mod<=1&&(x==1||x==2)&&x==y));
  assert(!standalone(0x1E6883FCCDE1F688ull,mod,false));
  render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;
  assert(!standalone(0x1E6883FCCDE1F688ull,mod));
 }
 render_target_cache_={};
 for(int bit=0;bit<64;++bit)assert(!standalone(0x1E6883FCCDE1F688ull^(uint64_t(1)<<bit),1));
 for(uint64_t pixel:{0x93626E75D17576C5ull,0x26EB620936001876ull,0x22DA22B5639EBAE4ull,0x8418C40F121D7EA7ull,0x11824C2EC1B156C6ull,0x26C4FD34AECBE4DEull,0xFCDF9BE8C57F7D01ull}){render_target_cache_={};Description d;d.pixel_shader_hash=pixel;assert(admits(d));assert(!admits(d,false));
 assert(admits_vertex(d.vertex_shader_hash,d.vertex_shader_modification));assert(!admits_vertex(d.vertex_shader_hash,d.vertex_shader_modification,false));
 for(uint64_t ps:{0ull,~0ull}){auto v=d;v.pixel_shader_hash=ps;assert(!admits(v));assert(admits_vertex(v.vertex_shader_hash,v.vertex_shader_modification));}
 for(int i=0;i<64;++i){auto v=d;v.vertex_shader_hash^=uint64_t(1)<<i;assert(!admits(v));v=d;v.vertex_shader_modification^=uint64_t(1)<<i;assert(!admits(v));v=d;v.pixel_shader_hash^=uint64_t(1)<<i;assert(!admits(v));v=d;v.pixel_shader_modification^=uint64_t(1)<<i;assert(!admits(v));}
 for(int x=1;x<=4;++x)for(int y=1;y<=4;++y){render_target_cache_.x=x;render_target_cache_.y=y;assert(admits(d)==((x==1||x==2)&&x==y));}
 render_target_cache_.x=render_target_cache_.y=2;render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;assert(!admits(d));
}}
'''.replace('POSITION_GATE',position_gate).replace('STANDALONE_GATE',standalone_gate).replace('VERTEX_GATE',vertex_gate).replace('GATE',gate)
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check.exe';cpp.write_text(code)
 subprocess.run([a.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Shadow and standalone vertex admission checks passed')
