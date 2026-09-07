"""Check terrain's three input ranges, optionally using captured index fixtures."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default='clang++')
    parser.add_argument('--fixtures',type=Path)
    args=parser.parse_args();repo=Path(__file__).resolve().parents[1]
    code=r'''
#include <rex/graphics/d3d12/fh1_geometry.h>
#include <bit>
#include <cassert>
#include <fstream>
#include <iterator>
#include <random>
#include <vector>
using namespace rex::graphics::d3d12;
void fixture(const char* path,std::array<uint32_t,8> system,uint32_t width,bool reset,
 std::array<uint32_t,44> bits,std::array<uint32_t,6> fetches,uint32_t expected_max){
 std::ifstream file(path,std::ios::binary);assert(file);
 std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
 auto maximum=geometry_index_maximum(system,bytes,width,reset);assert(maximum && *maximum==expected_max);
 std::array<float,44> constants;for(uint32_t i=0;i<44;++i)constants[i]=std::bit_cast<float>(bits[i]);
 auto ranges=terrain_geometry_ranges(*maximum,constants,fetches);assert(ranges);
 assert((*ranges)[0]==std::pair(fetches[0]&~3u,expected_max*28+8));
 assert((*ranges)[1]==(constants[32]==0?std::pair(0u,0u):std::pair(fetches[2]&~3u,expected_max*4+4)));
 assert((*ranges)[2]==std::pair(fetches[4]&~3u,32000u));
}
float mul(float a,float b){volatile float result=a*b;return std::min(std::abs(a),std::abs(b))==0?0:result;}
float add(float a,float b){volatile float result=a+b;return result;}
int main(){
 FIXTURES
 std::array<float,44> c{};c[20]=c[21]=c[22]=c[31]=c[32]=1;
 c[36]=100;c[37]=10;c[39]=9;
 std::array<uint32_t,6> f{0x1003,92,0x2000,16,0x3000,32000};
 auto run=[&](){return terrain_geometry_ranges(3,c,f);};
 assert(run() && (*run())[0]==std::pair(0x1000u,92u));
 f[1]=88;assert(!run());f[1]=92;f[5]=31996;assert(!run());f[5]=32000;
 f[3]=12;assert(!run());c[32]=0;assert(run() && (*run())[1]==std::pair(0u,0u));
 f[2]=0xffffffff;f[3]=0;assert(run());c[32]=1;assert(!run());f[2]=0x2000;f[3]=16;
 assert(!terrain_geometry_ranges(0x1000000,c,f));
 f[0]=0x1ffffffc;assert(!run());f[0]=0x1003;
 for(uint32_t i:{16u,17u,18u,20u,21u,22u,28u,29u,30u,31u,36u,37u,38u,39u}){
  float old=c[i];c[i]=std::numeric_limits<float>::quiet_NaN();assert(!run());c[i]=old;
 }
 c[33]=std::numeric_limits<float>::quiet_NaN();assert(run()); // unused component
 c[36]=-1;assert(!run());c[36]=100;c[38]=-1;assert(!run());c[38]=10;assert(!run());c[38]=0;
 c[20]=std::numeric_limits<float>::max();assert(!run());c[20]=1;
 c[28]=std::numeric_limits<float>::max();c[16]=-c[28];assert(!run());c[28]=c[16]=0;
 c[36]=2;c[37]=3;c[39]=1;assert((*run())[2].second==224);
 c[36]=c[37]=c[39]=0;assert((*run())[2].second==32);
 c[36]=1;c[39]=2147483648.0f;assert(!run());c[39]=1;
 c[31]=std::numeric_limits<float>::denorm_min();assert(run());c[31]=1;
 // Independent float-operation samples exercise the interval, including
 // separate rounding before adds; decoded vertex components lie in [-1,1].
 std::mt19937 rng(123);std::uniform_real_distribution<float> coord(-10000,10000),unit(-1,1);
 f[5]=65536;
 for(uint32_t trial=0;trial<1000;++trial){
  for(uint32_t i:{16u,17u,18u,20u,21u,22u,28u,29u,30u,31u})c[i]=coord(rng);
  c[36]=float(rng()%101);c[37]=float(rng()%101);c[38]=0;c[39]=float(rng()%10);
  auto ranges=run();assert(ranges);
  for(uint32_t vertex=0;vertex<32;++vertex){
   float cell[3];float scale=mul(unit(rng),c[31]);
   for(uint32_t i=0;i<3;++i){
    float delta=add(c[28+i],-c[16+i]);
    float grid=mul(mul(c[20+i],c[37]),add(delta,mul(scale,unit(rng))));
    assert(std::isfinite(grid));cell[i]=std::clamp(std::floor(grid),c[38],c[39]);
   }
   float index=add(add(mul(cell[1],c[36]),mul(cell[0],c[37])),cell[2]);
   assert(std::isfinite(index) && index>=0);
   assert((uint64_t(std::floor(index))+1)*32<=(*ranges)[2].second);
  }
 }
}
'''
    fixtures=[]
    if args.fixtures:
        report=json.loads((args.fixtures/'report.json').read_text());assert not report.get('error')
        def array(values):return '{'+','.join(str(int(x))+'u' for x in values)+'}'
        for draw in report['draws']:
            path=json.dumps((args.fixtures/f"{draw['event']}.bin").resolve().as_posix())
            fetches=sum((draw['fetches'][str(i)] for i in (95,90,89)),[])
            fixtures.append(f"fixture({path},{array(draw['system'])},{int(draw['width'])}u,{str(draw['primitive_reset']).lower()},{array(draw['float_bits'])},{array(fetches)},{int(draw['maximum'])}u);")
        assert fixtures
    code=code.replace('FIXTURES','\n'.join(fixtures))
    with tempfile.TemporaryDirectory() as temp:
        cpp=Path(temp)/'terrain.cpp';exe=Path(temp)/'terrain.exe';cpp.write_text(code)
        subprocess.run([args.compiler,'-std=c++20','-I'+str(repo/'thirdparty/shiftglue-sdk/include'),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print(f'Terrain geometry checks passed ({len(fixtures)} captured draws, 32000 interval samples)')


if __name__=='__main__':main()
