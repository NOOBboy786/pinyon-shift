"""Compile the production packed-world admission and creation-fallback gates."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    source = (Path(__file__).resolve().parents[1] / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
    start = source.index('  const bool fh1_packed_world_vertex =')
    admission = source[start:source.index(';', start) + 1]
    start = source.index('  const bool fh1_packed_world_geometry =')
    geometry = source[start:source.index(';', start) + 1]
    start = source.index('if (FAILED(create_result) && (fh1_standalone_vertex || fh1_shadow_mask_pixel || fh1_packed_world_vertex')
    fallback = source[start:source.index('{', start)]
    start = source.index('    if (fh1_packed_world_vertex && bindless_resources_used_ &&')
    selection = source[start:source.index('    if (fh1_native_scene && !fh1_packed_world_vertex && !fh1_shadow_mask_pixel)', start)]
    start = source.index("std::span<const uint32_t> PipelineCache::GetFh1PackedWorldTextureFetches")
    fetches = source[start:source.index("bool PipelineCache::IsFh1NativeShadowVertex", start)].replace("PipelineCache::", "")
    start = source.index("bool PipelineCache::PrepareFh1SceneBindings")
    bindings = source[start:source.index("bool PipelineCache::ConfigurePipeline", start)].replace("PipelineCache::", "")
    start = source.index('    if (fh1_native_scene && !fh1_packed_world_vertex && !fh1_shadow_mask_pixel)')
    scene_override = source[start:source.index('\n  } else {', start)]
    harness = r"""
#include <cassert>
#include <span>
#include <cstdint>
FETCHES
#include <cstdint>
#include <cstddef>
#include <initializer_list>
#include <array>
#include <vector>
namespace xenos {
enum class FetchOpDimension:uint32_t{k2D=1};
enum class TextureFilter:uint32_t{kPoint=0,kUseFetchConst=3};
enum class AnisoFilter:uint32_t{kDisabled=0,kUseFetchConst=7};
}
struct D3D12Shader {
 struct TextureBinding{uint32_t index,fetch;xenos::FetchOpDimension dim;bool sign;};
 struct SamplerBinding{uint32_t index,fetch;xenos::TextureFilter mag,min,mip;xenos::AnisoFilter aniso;};
 uint64_t hash;std::vector<TextureBinding> textures;std::vector<SamplerBinding> samplers;uint32_t mask=0;
 uint64_t ucode_data_hash(){return hash;}
 bool LoadPrecompiledBindings(std::span<const TextureBinding> t,std::span<const SamplerBinding> s,uint32_t m){textures.assign(t.begin(),t.end());samplers.assign(s.begin(),s.end());mask=m;return true;}
};
void SetupShaderBindingLayouts(D3D12Shader&){}
BINDINGS
struct RenderTargetCache { enum class Path{kHostRenderTargets,kPixelShaderInterlock};
  Path path=Path::kHostRenderTargets;Path GetPath(){return path;} } render_target_cache_;
struct Description { uint64_t vertex_shader_hash=0x6934E161812AB10Bull,vertex_shader_modification=0x7Full; };
bool native(Description description) { ADMISSION return fh1_packed_world_vertex; }
bool owns(bool fh1_packed_world_vertex,bool bindless_resources_used_,bool v,bool present,bool p){
  struct Shader{bool writes;unsigned memexport_eM_written(){return writes?1:0;}} vertex{v},pixel{p};
  struct Translation{Shader* s;Shader& shader(){return *s;}} vt{&vertex},pt{&pixel};
  struct{Translation* vertex_shader;Translation* pixel_shader;}runtime_description{&vt,present?&pt:nullptr};
  GEOMETRY return fh1_packed_world_geometry;
}
#define FAILED(x) ((x)<0)
bool fallback(int create_result,bool fh1_packed_world_vertex,bool fh1_native_scene=false) {
  bool fh1_standalone_vertex=false,fh1_shadow_mask_pixel=false;
  bool fh1_world_lit_vertex=false,fh1_world_lit_uv2_vertex=false,fh1_depth_mesh_vertex=false;
  FALLBACK return true;return false;
}
namespace shaders {
const unsigned char guest[]={0};
const unsigned char fh1_layered_scene_vs[]={10},fh1_layered_lit_ps[]={11},fh1_lit_scene_owned_vs[]={12},fh1_lit_scene_fixed_ps[]={13},fh1_blended_scene_owned_vs[]={14},fh1_blended_lit_fixed_ps[]={15};
const unsigned char fh1_packed_world_ps[]={1};
const unsigned char fh1_packed_world_blend_ps[]={2};
const unsigned char fh1_world_material_b985_ps[]={3};
const unsigned char fh1_world_material_c0e2_ps[]={4};
const unsigned char fh1_world_material_d96c_ps[]={5};
const unsigned char fh1_world_material_b1f8_ps[]={6};
const unsigned char fh1_world_material_e163_ps[]={7};
const unsigned char fh1_world_material_ef18_ps[]={8};
const unsigned char fh1_packed_world_blend_y_ps[]={9};
}
struct D3D12_SHADER_BYTECODE{const unsigned char* data;size_t size;};
const unsigned char* selected(bool fh1_packed_world_vertex,bool bindless_resources_used_,uint64_t hash,uint64_t mod){
  struct{uint64_t pixel_shader_hash,pixel_shader_modification;}description{hash,mod};
  struct{D3D12_SHADER_BYTECODE PS{shaders::guest,sizeof(shaders::guest)};}state_desc;
  SELECTION return state_desc.PS.data;
}
bool scene_unchanged(uint64_t fh1_vertex_shader_hash){
 bool fh1_native_scene=true,fh1_packed_world_vertex=false,fh1_shadow_mask_pixel=false;
 struct{D3D12_SHADER_BYTECODE VS{shaders::guest,1},PS{shaders::guest,1};}state_desc;
 SCENE_OVERRIDE
 return state_desc.VS.data==shaders::guest&&state_desc.PS.data==shaders::guest;
}
int main(){

 assert(scene_unchanged(0x1E6883FCCDE1F688ull));assert(scene_unchanged(0));
 assert(!scene_unchanged(0x3BC346726C1C2535ull));assert(!scene_unchanged(0xAD2C355A6BE1EE87ull));assert(!scene_unchanged(0x8D8A197476841A9Aull));

 {D3D12Shader v{0x1E6883FCCDE1F688ull},p{0xA4A965C189287B99ull};assert(PrepareFh1SceneBindings(v,&p));assert(v.textures.empty()&&v.samplers.empty()&&v.mask==0);assert(p.textures.empty()&&p.samplers.empty()&&p.mask==0);p.hash=1;assert(!PrepareFh1SceneBindings(v,&p));}

  for(uint64_t shadow_hash:{0x93626E75D17576C5ull,0x26EB620936001876ull,0x22DA22B5639EBAE4ull,0x8418C40F121D7EA7ull,0x11824C2EC1B156C6ull,0x26C4FD34AECBE4DEull,0xFCDF9BE8C57F7D01ull}){
  D3D12Shader shadow_v{0xA3B9ED5D5C87230Eull},shadow_p{shadow_hash};
  assert(PrepareFh1SceneBindings(shadow_v,&shadow_p));
  assert(shadow_v.textures.empty() && shadow_v.samplers.empty() && shadow_v.mask==0);
  assert(shadow_p.textures.size()==4 && shadow_p.samplers.size()==2 && shadow_p.mask==3);
  for(unsigned i=0;i<2;++i){
    for(unsigned j=0;j<2;++j){auto t=shadow_p.textures[2*i+j];assert(t.index==2+3*i+j && t.fetch==i && uint32_t(t.dim)==1 && t.sign==bool(j));}
    auto t=shadow_p.samplers[i];assert(t.index==1+3*i && t.fetch==i && uint32_t(t.mag)==3*i && uint32_t(t.min)==3*i && uint32_t(t.mip)==3*i && uint32_t(t.aniso)==0);
  }
  shadow_p.hash=0;assert(!PrepareFh1SceneBindings(shadow_v,&shadow_p));
  }
  constexpr uint64_t mod=0x00004000005B007Full;
  struct Entry{uint64_t hash;const unsigned char* data;};
  const Entry known[]={
    {0xA2C1F872E049AD8Bull,shaders::fh1_packed_world_ps},
    {0xFF096DC71B188012ull,shaders::fh1_packed_world_blend_ps},
    {0xB98566FB7CE14699ull,shaders::fh1_world_material_b985_ps},
    {0xC0E286228970074Dull,shaders::fh1_world_material_c0e2_ps},
    {0xD96CCDCC3F783790ull,shaders::fh1_world_material_d96c_ps},
    {0xB1F8F94927415BEDull,shaders::fh1_world_material_b1f8_ps},
    {0xE163D0BE1C2F9775ull,shaders::fh1_world_material_e163_ps},
    {0xEF18394497BDC2A6ull,shaders::fh1_world_material_ef18_ps},
    {0x6B97D48A7336AB24ull,shaders::fh1_packed_world_blend_y_ps},
  };
  const uint32_t expected[][7]={{6,7,13,2,5,1,0},{5,7,13,1,0,2},{6,13,2,5,1,0},{2,0,13},{13,0},{0,13},{5,13,1,0,2},{5,13,1,0,2},{5,7,13,1,0,2}};
  const size_t counts[]={7,6,6,3,2,2,5,5,6};
  for(size_t i=0;i<9;++i){auto f=GetFh1PackedWorldTextureFetches(known[i].hash);
    assert(f.size()==counts[i]);for(size_t j=0;j<f.size();++j)assert(f[j]==expected[i][j]);}
  assert(GetFh1PackedWorldTextureFetches(0).empty());
  for(auto entry:known){
    D3D12Shader v{0x6934E161812AB10Bull},p{entry.hash};
    assert(PrepareFh1SceneBindings(v,&p));
    auto f=GetFh1PackedWorldTextureFetches(entry.hash);uint32_t mask=0;
    assert(v.textures.empty() && v.samplers.empty() && v.mask==0);
    assert(p.textures.size()==2*f.size() && p.samplers.size()==f.size());
    for(size_t i=0;i<f.size();++i){mask|=1u<<f[i];
      for(size_t j=0;j<2;++j){auto t=p.textures[2*i+j];
        assert(t.index==2+3*i+j && t.fetch==f[i] && uint32_t(t.dim)==1 && t.sign==bool(j));}
      auto t=p.samplers[i];assert(t.index==1+3*i && t.fetch==f[i]);
      assert(uint32_t(t.mag)==3 && uint32_t(t.min)==3 && uint32_t(t.mip)==3 && uint32_t(t.aniso)==7);
    }assert(p.mask==mask);
    assert(selected(true,true,entry.hash,mod)==entry.data);
    assert(selected(false,true,entry.hash,mod)==shaders::guest);
    assert(selected(true,false,entry.hash,mod)==shaders::guest);
    for(unsigned i=0;i<64;++i){
      assert(selected(true,true,entry.hash^(uint64_t(1)<<i),mod)==shaders::guest);
      assert(selected(true,true,entry.hash,mod^(uint64_t(1)<<i))==shaders::guest);
    }
  }
  for(bool native:{false,true})for(bool bindless:{false,true})for(bool v:{false,true})
   for(bool present:{false,true})for(bool p:{false,true})
    assert(owns(native,bindless,v,present,p)==(native && bindless && !v && (!present || !p)));
  Description good;assert(native(good));
  for(unsigned i=0;i<64;++i){auto d=good;d.vertex_shader_hash^=uint64_t(1)<<i;assert(!native(d));
    d=good;d.vertex_shader_modification^=uint64_t(1)<<i;assert(!native(d));}
  render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;assert(!native(good));
  assert(fallback(-1,false,true));assert(!fallback(0,false,true));
  assert(fallback(-1,true));assert(!fallback(0,true));assert(!fallback(-1,false));
}
""".replace('BINDINGS', bindings).replace('SCENE_OVERRIDE', scene_override).replace('FETCHES', fetches).replace('SELECTION', selection).replace('ADMISSION', admission).replace('GEOMETRY', geometry).replace('FALLBACK', fallback)
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'check.cpp';exe=Path(temp)/'check.exe';cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print('Packed-world admission and fallback checks passed')


if __name__ == '__main__':
    main()
