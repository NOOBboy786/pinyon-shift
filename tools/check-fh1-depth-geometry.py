"""Exercise depth geometry bounds from an immutable host-index snapshot."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',default='clang++');p.add_argument('--fixtures',type=Path);p.add_argument('--scene-fixtures',type=Path);args=p.parse_args()
    repo=Path(__file__).resolve().parents[1]
    code=r'''
#include "rex/graphics/d3d12/fh1_geometry.h"
#include <array>
#include <cassert>
#include <vector>
#include <fstream>
#include <iterator>
using namespace rex::graphics::d3d12;
void fixture(const char* path,std::array<uint32_t,8> sys,uint32_t width,uint32_t stride,uint32_t address,uint32_t size,bool reset,uint32_t expected,uint32_t vertex_bytes=12){
 std::ifstream file(path,std::ios::binary);assert(file);
 std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
 auto r=depth_geometry_range(sys,bytes,width,stride,address,size,reset,vertex_bytes);
 if(expected){assert(r&&r->first==(address&~3u)&&r->second==expected);}else assert(!r);
}
int main(){
 FIXTURES
 std::array<uint32_t,8> sys{0,0,0,0xffffffff,0,0,0,0xffffff};
 std::vector<uint8_t> bytes;
 auto run=[&](std::initializer_list<uint32_t> values,uint32_t width,uint32_t stride=24,uint32_t size=1024,bool reset=false){
  bytes.clear();for(auto v:values)for(uint32_t i=0;i<width;++i)bytes.push_back(uint8_t(v>>(8*i)));
  return depth_geometry_range(sys,bytes,width,stride,0x1004,(size/4)<<2,reset);
 };
 assert(!run({0xffff},2,24,1024,true));
 auto r=run({0xffff,3},2,24,1024,true);assert(r&&r->second==84);
 assert(!run({0xffff,3},2,24,1024,false));
 r=run({0xffffffff,3},4,24,1024,true);assert(r&&r->second==84);
 r=run({0,2,7},2);assert(r&&r->first==0x1004&&r->second==180);
 for(auto stride:{12u,20u,24u,28u,32u}){r=run({3},4,stride);assert(r&&r->second==3*stride+12);}
 assert(!run({43},2));assert(!run({},2));assert(!run({1},1));assert(!run({1},4,16));
 sys[4]=1;r=run({0x0700},2);assert(r&&r->second==180);
 sys[4]=2;r=run({0x07000000},4);assert(r&&r->second==180);
 sys[4]=3;r=run({0x00070000},4);assert(r&&r->second==180);
 sys[4]=4;assert(!run({0},4));sys[4]=0;
 sys[3]=0xffff;r=run({0xffff,2},2);assert(r&&r->second==60);sys[3]=0xffffffff;
 sys[5]=0xffffff;r=run({2},4);assert(r&&r->second==36);sys[5]=0;
 sys[6]=5;sys[7]=7;r=run({0,100},4);assert(r&&r->second==180);
 sys[6]=8;assert(!run({0},4));sys[6]=0;sys[7]=0x1000000;assert(!run({0},4));sys[7]=0xffffff;
 sys[0]=1;assert(!run({0},2));sys[0]=0;
 bytes={0};assert(!depth_geometry_range(sys,bytes,2,24,0x1000,1024,false));
 bytes={0,0};assert(!depth_geometry_range(sys,bytes,2,24,0x20000000,1024,false));
 assert(!depth_geometry_range(sys,bytes,2,24,0x1ffffffc,1024,false));
 assert(!depth_geometry_range(sys,bytes,2,24,0x1000,0,false));
 r=run({0xffffff},4,32,0x3fffffc);assert(!r);
 for(uint32_t stride:{12u,16u,20u}){
  bytes={1,0};auto full=depth_geometry_range(sys,bytes,2,stride,0x1000,stride*2,false,stride);
  assert(full && full->second==stride*2);
  assert(!depth_geometry_range(sys,bytes,2,stride,0x1000,stride*2-4,false,stride));
  assert(!depth_geometry_range(sys,bytes,2,stride,0x1000,1024,false,0));
  assert(!depth_geometry_range(sys,bytes,2,stride,0x1000,1024,false,stride+4));
  assert(!depth_geometry_range(sys,bytes,2,stride,0x1000,1024,false,5));
 }
 r=run({1},2,24,36);assert(r&&r->second==36);assert(!run({1},2,24,32));
}
'''
    fixtures=[]
    if args.fixtures:
        report=json.loads((args.fixtures/'report.json').read_text());assert not report.get('error')
        for d in report['draws']:
            assert d['indexed']
            path=json.dumps((args.fixtures/f"{d['event']}.bin").resolve().as_posix())
            sys='{'+','.join(str(x)+'u' for x in d['system'])+'}'
            fixtures.append(f"fixture({path},{sys},{d['index_width']}u,{d['stride']}u,{d['fetch_words'][0]}u,{d['fetch_words'][1]}u,{str(d['primitive_reset']).lower()},{d['required_bytes'] if d['fits'] else 0}u);")
        assert fixtures
    if args.scene_fixtures:
        report=json.loads((args.scene_fixtures/'report.json').read_text());assert not report.get('error')
        for d in report['draws']:
            assert d['indexed'] and d['vertex_offset']==0
            path=json.dumps((args.scene_fixtures/f"{d['event']}.bin").resolve().as_posix())
            system=','.join(str(x)+'u' for x in d['system'])
            fixtures.append(f"fixture({path},{{{system}}},{d['width']},{d['stride']},{d['fetch'][0]}u,{d['fetch'][1]}u,{str(d['primitive_reset']).lower()},{d['required'] if d['fits'] else 0}u,{d['stride']});")
    code=code.replace('FIXTURES','\n'.join(fixtures))
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'bounds.cpp';exe=Path(temp)/'bounds.exe';cpp.write_text(code)
        subprocess.run([args.compiler,'-std=c++20','-I'+str(repo/'thirdparty/shiftglue-sdk/include'),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print(f'Depth index snapshot bounds checks passed ({len(fixtures)} captured draws)')


if __name__=='__main__':main()
