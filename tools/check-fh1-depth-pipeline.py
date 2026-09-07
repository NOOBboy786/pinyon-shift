"""Compile native binding and fallback code with absent/present pixel stages."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def block(source, marker):
    start=source.index(marker);depth=0
    opening=source.index(') {',start)+2 if marker.startswith('for (') else source.index('{',start)
    for end in range(opening,len(source)):
        depth+=(source[end]=='{')-(source[end]=='}')
        if not depth:return source[start:end+1]
    raise AssertionError('Unterminated block')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default='clang++')
    args=parser.parse_args()
    source=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/d3d12/pipeline_cache.cpp').read_text()
    prepare=block(source,'bool PipelineCache::PrepareFh1SceneBindings(')
    admission=block(source,'bool PipelineCache::IsFh1NativeScenePipeline(')
    preload=block(source[source.index('// Native velocity'):], 'if (bindless_resources_used_ &&')
    fallback=block(source,'for (auto* translation : {runtime_description.vertex_shader, runtime_description.pixel_shader})')
    harness=r'''
#include <cassert>
#include <span>
#include <cstdint>
namespace xenos {
enum class FetchOpDimension{k2D};enum class TextureFilter{kUseFetchConst};enum class AnisoFilter{kUseFetchConst};
}
struct D3D12Shader {
  struct TextureBinding {int index,fetch;xenos::FetchOpDimension dim;bool sign;};
  struct SamplerBinding {int index,fetch;xenos::TextureFilter a,b,c;xenos::AnisoFilter d;};
  bool fail=false;int loads=0,layouts=0;size_t textures=0,samplers=0;
  bool LoadPrecompiledBindings(std::span<const TextureBinding> t,std::span<const SamplerBinding> s,int){++loads;textures=t.size();samplers=s.size();return !fail;}
};
struct Translation {bool translated=false,valid=true,fail=false;bool is_translated(){return translated;}bool is_valid(){return valid;}};
struct PipelineDescription {uint64_t vertex_shader_hash=0,pixel_shader_hash=0,test_hash=0;};
uint64_t XXH3_64bits(const void* p,size_t){return static_cast<const PipelineDescription*>(p)->test_hash;}
struct RenderTargetCache {enum class Path{kHostRenderTargets,kPixelShaderInterlock};Path path=Path::kHostRenderTargets;Path GetPath()const{return path;}};
struct PipelineCache {
  bool bindless_resources_used_=true;RenderTargetCache render_target_cache_;
  bool IsFh1NativeScenePipeline(const PipelineDescription&)const;
  bool preload(uint64_t shader_hash){for(int i=0;i<1;++i){PREFILTER return true;}return false;}
  bool PrepareFh1SceneBindings(D3D12Shader&,D3D12Shader*);
  void SetupShaderBindingLayouts(D3D12Shader& s){++s.layouts;}
  struct {Translation* vertex_shader;Translation* pixel_shader;} runtime_description;
  int dxbc_converter_=0,dxc_utils_=0,dxc_compiler_=0,translations=0;
  bool TranslateAnalyzedShader(void*,Translation& t,int,int,int){++translations;if(t.fail)return false;t.translated=true;return true;}
  void* fallback(){FALLBACK return this;}
};
PREPARE
ADMISSION
int main(){
  PipelineCache p;D3D12Shader v,ps;
  assert(!p.preload(0xC8C39E5AE1B08DE6ull));assert(p.preload(123));
  p.bindless_resources_used_=false;assert(p.preload(0xC8C39E5AE1B08DE6ull));p.bindless_resources_used_=true;
  for(PipelineDescription d : {
    PipelineDescription{0xC8C39E5AE1B08DE6ull,0,0x53BA06CDA0AF43C1ull},
    {0xC8C39E5AE1B08DE6ull,0,0x864862F2FDCC2307ull},
    {0x9BF2991815B941B9ull,0,0x9CE112156F9A2FE7ull},
    {0x9BF2991815B941B9ull,0,0x0D0C6B5516E60BB8ull},
    {0xB646F85EF69A57E0ull,0,0x4FAB5D009EDC7575ull},
    {0xB646F85EF69A57E0ull,0,0xB11F709480BB88C7ull},
    {0xB646F85EF69A57E0ull,0,0x0462A10067F56C6Cull},
    {0xD0C40C04F166092Eull,0,0xDAA16CBF4502F6F6ull},
    {0xD0C40C04F166092Eull,0,0xEEA552E1610954A1ull},
    {0x5A28C7FAFD86F112ull,0,0x034B44F468DEC548ull},
    {0x5A28C7FAFD86F112ull,0,0x2370BFB73FCCFD27ull},
    {0xCA293E0A1CB4B416ull,0,0x6C161CE29479E1BFull},
    {0x4E1DA281CC3D7EDBull,0,0xD7F8863A6EEF08ABull},
    {0xB6C9863F710683ECull,0,0xFB9F7AF89FA5E129ull},
    {0xB6C9863F710683ECull,0,0xE09E8BD845D68BDDull},
    {0xB6C9863F710683ECull,0,0x38DC022591899969ull},
    {0xB6C9863F710683ECull,0,0x544EA3FFE46CB7B3ull}}){
    const uint64_t hash=d.test_hash;
    assert(!p.preload(d.vertex_shader_hash));assert(p.IsFh1NativeScenePipeline(d));
    d.test_hash^=1;assert(!p.IsFh1NativeScenePipeline(d));d.test_hash=hash;
    d.pixel_shader_hash=1;assert(!p.IsFh1NativeScenePipeline(d));d.pixel_shader_hash=0;
    p.bindless_resources_used_=false;assert(!p.IsFh1NativeScenePipeline(d));p.bindless_resources_used_=true;
    p.render_target_cache_.path=RenderTargetCache::Path::kPixelShaderInterlock;assert(!p.IsFh1NativeScenePipeline(d));p.render_target_cache_.path=RenderTargetCache::Path::kHostRenderTargets;
  }
  assert(p.PrepareFh1SceneBindings(v,nullptr));assert(v.loads==1&&v.layouts==1&&!v.textures&&!v.samplers);
  assert(p.PrepareFh1SceneBindings(v,&ps));assert(ps.textures==2&&ps.samplers==1&&ps.layouts==1);
  ps.fail=true;assert(!p.PrepareFh1SceneBindings(v,&ps));v.fail=true;assert(!p.PrepareFh1SceneBindings(v,nullptr));
  Translation vs; p.runtime_description={&vs,nullptr};assert(p.fallback()&&p.translations==1);
  assert(p.fallback()&&p.translations==1);
  Translation pixel; p.runtime_description.pixel_shader=&pixel;assert(p.fallback()&&p.translations==2);
  pixel.valid=false;assert(!p.fallback());p.runtime_description.pixel_shader=nullptr;
  vs.translated=false;vs.fail=true;assert(!p.fallback());
}
'''.replace('PREPARE',prepare).replace('FALLBACK',fallback).replace('ADMISSION',admission).replace('PREFILTER',preload)
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'depth.cpp';exe=Path(temp)/'depth.exe';cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print('Native depth binding and nullable fallback checks passed')


if __name__=='__main__':main()
