"""Compile the production clear pipeline gate and exercise state rejection."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default='clang++')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk'
source=(root/'src/graphics/d3d12/pipeline_cache.cpp').read_text()
header=(root/'include/rex/graphics/d3d12/pipeline_cache.h').read_text()
types=header[header.index('  enum class PipelineStripCutIndex'):header.index('  REXPACKEDSTRUCT(PipelineStoredDescription')]
methods=[]
for name in ('IsFh1NativeShadowVertex','IsFh1NativeStandaloneVertex','IsFh1NativePositionPipeline','IsFh1ClearPipeline'):
    start=source.index('bool PipelineCache::'+name+'(')
    methods.append(source[start:source.index('\n}\n',start)+3])
code=r'''
#include <cassert>
#include <initializer_list>
#include <cstdint>
namespace xenos {
constexpr int kMaxColorRenderTargets=4;
enum class ColorRenderTargetFormat:uint32_t{k_8_8_8_8=0,k_2_10_10_10_FLOAT=3,k_16_16_16_16_FLOAT=7};
enum class DepthRenderTargetFormat:uint32_t{kD24S8,kD24FS8};
enum class CompareFunction:uint32_t{kNever,kLess,kEqual,kLessEqual,kGreater,kNotEqual,kGreaterEqual,kAlways};
enum class StencilOp:uint32_t{kKeep,kZero,kReplace};
enum class BlendOp:uint32_t{kAdd,kSubtract};
enum class MsaaSamples:uint32_t{k1X,k2X,k4X};
}
struct RenderTargetCache {
 enum class Path{kHostRenderTargets,kPixelShaderInterlock};
 Path path=Path::kHostRenderTargets;bool native2=true;int x=2,y=2;
 Path GetPath()const{return path;}int draw_resolution_scale_x()const{return x;}int draw_resolution_scale_y()const{return y;}bool msaa_2x_supported()const{return native2;}
};
#define REXPACKEDSTRUCT(name,...) struct name __VA_ARGS__
struct PipelineCache {
 TYPES
 struct Runtime{PipelineDescription description;};struct Pipeline{Runtime description;};
 bool bindless_resources_used_=true;RenderTargetCache render_target_cache_;
 bool IsFh1NativeShadowVertex(uint64_t,uint64_t)const;
 bool IsFh1NativeStandaloneVertex(uint64_t,uint64_t)const;
 bool IsFh1NativePositionPipeline(const PipelineDescription&)const;
 bool IsFh1ClearPipeline(void*)const;
};
METHODS
int main(){
 using C=PipelineCache;C c;C::Pipeline p{};auto& d=p.description.description;
 d.vertex_shader_hash=0x1E6883FCCDE1F688ull;d.geometry_shader=C::PipelineGeometryShader::kRectangleList;d.depth_func=xenos::CompareFunction::kAlways;
 assert(c.IsFh1ClearPipeline(&p));assert(!c.IsFh1ClearPipeline(nullptr));
 auto base=d;

 #define REJECT(field,value) d=base;d.field=value;assert(!c.IsFh1ClearPipeline(&p))
 REJECT(depth_bias,1);REJECT(depth_bias_slope_scaled,1);REJECT(depth_clip,1);REJECT(fill_mode_wireframe,1);
 REJECT(cull_mode,C::PipelineCullMode::kBack);REJECT(geometry_shader,C::PipelineGeometryShader::kQuadList);
 REJECT(depth_func,xenos::CompareFunction::kLess);REJECT(vertex_shader_hash,1);REJECT(vertex_shader_hash,0xC34795A841E7DEFFull);
 REJECT(vertex_shader_modification,1);REJECT(stencil_enable,1);
 d=base;d.stencil_enable=1;d.stencil_write_mask=255;
 d.stencil_front_func=d.stencil_back_func=xenos::CompareFunction::kAlways;
 d.stencil_front_pass_op=d.stencil_back_pass_op=xenos::StencilOp::kReplace;
 assert(c.IsFh1ClearPipeline(&p));d.stencil_write_mask=127;assert(!c.IsFh1ClearPipeline(&p));
 d=base;d.host_msaa_samples=xenos::MsaaSamples::k2X;c.render_target_cache_.native2=false;assert(!c.IsFh1ClearPipeline(&p));c.render_target_cache_.native2=true;assert(c.IsFh1ClearPipeline(&p));
 d=base;d.vertex_shader_modification=1;d.pixel_shader_hash=0xA4A965C189287B99ull;d.pixel_shader_modification=0x400000000001ull;
 auto& t=d.render_targets[0];t.used=1;t.write_mask=15;t.src_blend=t.src_blend_alpha=C::PipelineBlendFactor::kOne;
 assert(c.IsFh1ClearPipeline(&p));d.pixel_shader_modification|=0x10000;assert(c.IsFh1ClearPipeline(&p));
 t.format=xenos::ColorRenderTargetFormat::k_2_10_10_10_FLOAT;
 for(auto samples:{xenos::MsaaSamples::k1X,xenos::MsaaSamples::k2X,xenos::MsaaSamples::k4X}){d.host_msaa_samples=samples;assert(c.IsFh1ClearPipeline(&p));}
 t.format=static_cast<xenos::ColorRenderTargetFormat>(2);assert(!c.IsFh1ClearPipeline(&p));
 t.format=xenos::ColorRenderTargetFormat::k_8_8_8_8;
 t.dest_blend=C::PipelineBlendFactor::kOne;assert(!c.IsFh1ClearPipeline(&p));t.dest_blend=C::PipelineBlendFactor::kZero;
 t.write_mask=7;assert(!c.IsFh1ClearPipeline(&p));t.write_mask=15;
 d.render_targets[1]=t;assert(!c.IsFh1ClearPipeline(&p));d.render_targets[1]={};
 c.bindless_resources_used_=false;assert(!c.IsFh1ClearPipeline(&p));
}
'''.replace('TYPES',types).replace('METHODS','\n'.join(methods))
with tempfile.TemporaryDirectory() as tmp:
    cpp,exe=Path(tmp)/'check.cpp',Path(tmp)/'check.exe'
    cpp.write_text(code)
    subprocess.run([a.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Clear pipeline shader, raster, depth/stencil, blend and MSAA gates passed')
