"""Exercise the production linear video upload with failing ownership/layout/allocation."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',default='clang++');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
s=(root/'thirdparty/shiftglue-sdk/src/graphics/d3d12/texture_cache.cpp').read_text()
body=s[s.index('  // BEGIN FH1 LINEAR VIDEO UPLOAD'):s.index('  // END FH1 LINEAR VIDEO UPLOAD')]
cp=(root/'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
admission=cp.split('const bool fh1_video_textures = ',1)[1].split(';',1)[0]
code=r'''
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <span>
#include <vector>
using UINT64=uint64_t;
namespace xenos {enum class DataDimension{k2DOrStacked,k3D};enum class TextureFormat{k_8,kOther};enum class Endian{kNone,kOther};}
constexpr int D3D12_TEXTURE_DATA_PLACEMENT_ALIGNMENT=512,D3D12_RESOURCE_STATE_COPY_DEST=1,D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT=2,D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX=3;
struct D3D12_PLACED_SUBRESOURCE_FOOTPRINT{uint64_t Offset=0;struct{uint32_t RowPitch=1280;}Footprint;};
struct ID3D12Resource{int GetDesc(){return 0;}}resource,upload;
struct D3D12_TEXTURE_COPY_LOCATION{ID3D12Resource* pResource=nullptr;int Type=0;D3D12_PLACED_SUBRESOURCE_FOOTPRINT PlacedFootprint;};
struct TextureKey{bool mip_max_level=false,scaled_resolve=false,tiled=false;uint32_t base_page=1,depth=1;xenos::DataDimension dimension=xenos::DataDimension::k2DOrStacked;xenos::TextureFormat format=xenos::TextureFormat::k_8;xenos::Endian endianness=xenos::Endian::kNone;uint32_t GetDepthOrArraySize() const{return depth;}};
uint32_t host_pitch=1280;uint64_t host_size=1280*720,host_offset=0;bool allocation_ok=true,cpu_owned=true;int copies=0,marks=0,barriers=0,reads=0;
struct Texture{TextureKey k;bool forced=false;struct{struct{uint32_t row_pitch_bytes=1280,level_data_extent_bytes=1280*720;}base;}layout;auto key(){return k;}bool force_load_3d_tiling(){return forced;}auto& guest_layout(){return layout;}};
struct D3D12Texture:Texture{ID3D12Resource* resource(){return &::resource;}void MarkAsUsed(){++marks;}int SetResourceState(int){return 0;}};
struct Device{void GetCopyableFootprints(const int*,int,int,int,D3D12_PLACED_SUBRESOURCE_FOOTPRINT* f,void*,void*,uint64_t* size){f->Footprint.RowPitch=host_pitch;f->Offset=host_offset;*size=host_size;}}device;
struct Processor{
 auto& GetD3D12Provider(){return *this;}auto* GetDevice(){return &device;}auto& GetConstantBufferPool(){return *this;}int GetCurrentFrame(){return 0;}
 uint8_t* Request(int,uint64_t size,int alignment,ID3D12Resource** r,size_t* offset,void*){assert(alignment==512);static std::vector<uint8_t> data(2<<20);assert(size<=data.size());*r=&upload;*offset=512;return allocation_ok?data.data():nullptr;}
 void PushTransitionBarrier(ID3D12Resource*,int,int){++barriers;}void SubmitBarriers(){}auto& GetDeferredCommandList(){return *this;}
 void D3DCopyTextureRegion(D3D12_TEXTURE_COPY_LOCATION* d,int,int,int,D3D12_TEXTURE_COPY_LOCATION* s,void*){assert(d->pResource==&resource&&s->pResource==&upload);assert(s->PlacedFootprint.Offset==512&&s->PlacedFootprint.Footprint.RowPitch==host_pitch);++copies;}
}command_processor_;
struct Memory{bool CopyCpuRange(uint32_t address,std::span<uint8_t> data){++reads;assert(address==4096&&!data.empty());return cpu_owned;}}memory;
auto& shared_memory(){return memory;}
bool run(Texture& texture,bool load_base=true,bool load_mips=false){bool request_fh1_video_=true;BODY return false;}
struct Shader {uint64_t hash;uint64_t ucode_data_hash(){return hash;}};
struct Scale {int x=2,y=2;int draw_resolution_scale_x(){return x;}int draw_resolution_scale_y(){return y;}};
bool admit(Shader* vertex_shader,Shader* pixel_shader,Scale* texture_cache_){return ADMISSION;}
int main(){
 Shader vs{0x7156CE05C6365E51ull},ps{0x31511D87CC0C94B9ull};Scale scale;
 assert(admit(&vs,&ps,&scale));assert(!admit(&vs,nullptr,&scale));
 for(int x=1;x<=3;++x)for(int y=1;y<=3;++y){scale={x,y};assert(admit(&vs,&ps,&scale)==((x==1||x==2)&&y==x));}
 scale={2,2};
 for(int bit=0;bit<64;++bit){vs.hash^=uint64_t(1)<<bit;assert(!admit(&vs,&ps,&scale));vs.hash^=uint64_t(1)<<bit;ps.hash^=uint64_t(1)<<bit;assert(!admit(&vs,&ps,&scale));ps.hash^=uint64_t(1)<<bit;}

 for(int failure=0;failure<=15;++failure){
  D3D12Texture t;host_pitch=1280;host_size=1280*720;host_offset=0;allocation_ok=cpu_owned=true;copies=marks=barriers=reads=0;
  switch(failure){case 1:t.k.tiled=true;break;case 2:t.k.scaled_resolve=true;break;case 3:t.k.mip_max_level=true;break;case 4:t.k.base_page=0;break;case 5:t.k.depth=2;break;case 6:t.k.dimension=xenos::DataDimension::k3D;break;case 7:t.k.format=xenos::TextureFormat::kOther;break;case 8:t.k.endianness=xenos::Endian::kOther;break;case 9:t.forced=true;break;case 10:host_pitch=1536;break;case 11:host_size=1;break;case 12:host_offset=512;break;case 13:allocation_ok=false;break;case 14:cpu_owned=false;break;case 15:t.layout.base.level_data_extent_bytes=0;break;}
  bool ok=run(t);assert(ok==(failure==0));assert(copies==int(ok)&&marks==int(ok)&&barriers==int(ok));
 }
 D3D12Texture t;assert(!run(t,false));assert(!run(t,true,true));
 host_pitch=768;host_size=768*359+640;t.layout.base={768,uint32_t(host_size)};cpu_owned=allocation_ok=true;assert(run(t));
}
'''.replace('BODY',body).replace('ADMISSION',admission)
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check.exe';cpp.write_text(code)
    subprocess.run([a.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Video upload: matching layouts, rejection and ownership/allocation fallback passed')
