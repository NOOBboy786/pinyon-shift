"""Execute the production no-output predicate and exercise each fallback guard."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',default='clang++');args=p.parse_args()
    source=(Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
    start=source.index('  const bool fh1_constant_no_output =');end=source.index('  if (!BeginSubmission(true))',start)
    predicate=source[start:end]
    draw=source[source.index('bool D3D12CommandProcessor::IssueDraw('):]
    assert draw.index('IssueCopy()')<draw.index('fh1_constant_no_output')<draw.index('BeginSubmission(true)')
    harness=r'''
#include <cassert>
#include <cstdint>
struct Shader {uint64_t hash;uint64_t ucode_data_hash(){return hash;}int writes_color_targets(){return 1;}};
struct Regs{bool z_enable=false,stencil_enable=false;uint32_t mask=0;};
int depth_checks=0;
namespace draw_util {Regs GetNormalizedDepthControl(Regs r){++depth_checks;return r;}uint32_t GetNormalizedColorMask(Regs r,int){return r.mask;}}
bool skip(Shader* vertex_shader,Shader* pixel_shader,Regs regs,bool memexport_used,bool query){
 struct {bool valid;} active_occlusion_query_{query};
 const auto finish_draw=[](bool x){return x;};
 PREDICATE
 return false;
}
int main(){
 Shader v{0xB6C9863F710683ECull},p{0xA4A965C189287B99ull};Regs r;
 assert(skip(&v,&p,r,false,false));assert(depth_checks==1);depth_checks=0;
 assert(!skip(&v,nullptr,r,false,false));assert(depth_checks==0);
 assert(!skip(&v,&p,r,true,false));assert(!skip(&v,&p,r,false,true));assert(depth_checks==0);
 r.z_enable=true;assert(!skip(&v,&p,r,false,false));r.z_enable=false;
 r.stencil_enable=true;assert(!skip(&v,&p,r,false,false));r.stencil_enable=false;
 for(uint32_t bit=1;bit<65536;bit<<=1){r.mask=bit;assert(!skip(&v,&p,r,false,false));}r.mask=0;
 depth_checks=0;v.hash^=1;assert(!skip(&v,&p,r,false,false));assert(depth_checks==0);v.hash^=1;
 p.hash^=1;assert(!skip(&v,&p,r,false,false));assert(depth_checks==0);
}
'''.replace('PREDICATE',predicate)
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'skip.cpp';exe=Path(temp)/'skip.exe';cpp.write_text(harness)
        subprocess.run([args.compiler,'-std=c++20',str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
    print('Constant no-output draw guard checks passed')


if __name__=='__main__':main()
