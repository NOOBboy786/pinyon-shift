"""Compile clear rectangle qualification, optionally against captured vertex audits."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', default='clang++')
p.add_argument('--audit', type=Path, action='append', default=[])
p.add_argument('--inputs', type=Path, action='append', default=[])
a = p.parse_args()
fixtures = []
for path in a.audit:
    audit = json.loads(path.read_text())
    assert 'error' not in audit and audit['draws']
    for draw in audit['draws']:
        vp, sc = draw['viewports'][0], draw['scissors'][0]
        vertices = draw['vertices']
        assert len(vertices) % 3 == 0
        for i in range(0, len(vertices), 3):
            v = [row[:4] for row in vertices[i:i+3]]
            xy = [(vp['x'] + (q[0]+1)*vp['width']/2,
                   vp['y'] + (1-q[1])*vp['height']/2) for q in v]
            assert all(x.is_integer() and y.is_integer() for x, y in xy)
            bounds = [max(min(x for x, y in xy), sc['x']),
                      max(min(y for x, y in xy), sc['y']),
                      min(max(x for x, y in xy), sc['x']+sc['width']),
                      min(max(y for x, y in xy), sc['y']+sc['height'])]
            if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                bounds = [0]*4
            depth = max(0, min(1, v[0][2]*(vp['maxDepth']-vp['minDepth'])+vp['minDepth']))
            floats = lambda row: '{' + ','.join(float(x).hex()+'f' for x in row) + '}'
            ints = lambda row: '{' + ','.join(str(int(x)) for x in row) + '}'
            fixtures.append('check({{' + ','.join(floats(q) for q in v) + '}},' +
                            ints([vp[k] for k in ('x','y','width','height')]) + ',' +
                            floats([vp['minDepth'],vp['maxDepth']]) + ',' +
                            ints([sc[k] for k in ('x','y','width','height')]) + ',' +
                            ints(bounds) + ',' + float(depth).hex()+'f);')
input_count = 0
for path in a.inputs:
    capture = json.loads(path.read_text())
    assert 'error' not in capture and capture['draws']
    for draw in capture['draws']:
        assert not draw['indexed']
        output = bytes.fromhex(draw['post_vs'])
        assert len(output) == len(draw['rows'])*draw['stride']
        for index, row in enumerate(draw['rows']):
            raw = bytes.fromhex(row['raw'])
            expected = output[index*draw['stride']:(index+1)*draw['stride']]
            ints = lambda values: '{' + ','.join(str(x)+'u' for x in values) + '}'
            fixtures.append('vertex_check(' + ints(raw) + ',' + str(draw['fetch'][1]&3) + ',' + ints(draw['system']) + ',' + ints(expected) + ');')
            input_count += 1
code = r'''
#include "rex/graphics/d3d12/fh1_clear.h"
#include <cassert>
using namespace rex::graphics::d3d12;
using V = std::array<std::array<float,4>,3>;
void check(V v,std::array<uint32_t,4> vp,std::array<float,2> z,
           std::array<uint32_t,4> sc,std::array<int32_t,4> bounds,float depth){
 auto r=fh1_clear_rectangle(v,vp,z,sc);assert(r&&r->bounds==bounds&&r->depth==depth);
}
void vertex_check(std::array<uint8_t,28> bytes,uint32_t endian,std::array<uint32_t,120> system,std::initializer_list<uint8_t> expected){
 auto r=fh1_clear_vertex(bytes,endian,system,expected.size()==32);assert(r&&std::memcmp(r->data(),expected.begin(),expected.size())==0);
 assert(!fh1_clear_vertex(bytes,4,system,true));
}
int main(){
 V v{{{-1,1,0,1},{1,1,0,1},{1,-1,0,1}}};
 check(v,{0,0,128,64},{0,1},{2,3,5,7},{2,3,7,10},0);
 check(v,{0,0,128,64},{0,1},{200,0,1,1},{0,0,0,0},0);
 check(v,{0,0,128,64},{0,1},{0xffffffff,0,0xffffffff,1},{0,0,0,0},0);
 for(auto& q:v)q[2]=-0.000001f;
 check(v,{0,0,128,64},{0,.5},{0,0,128,64},{0,0,128,64},0);
 auto valid=v;
 auto reject=[&](){assert(!fh1_clear_rectangle(v,{0,0,128,64},{0,1},{0,0,128,64}));};
 v[1]=v[0];reject();v=valid;v[1][0]=0;reject();v=valid;
 v[1][3]=2;reject();v=valid;v[1][2]=1;reject();v=valid;
 v[1][0]=.1f;reject();v=valid;
 for(float bad:{std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::denorm_min()}){v[0][0]=bad;reject();v=valid;}
 assert(!fh1_clear_rectangle(v,{0,0,128,64},{1,0},{0,0,128,64}));
 FIXTURES
}
'''.replace('FIXTURES', '\n'.join(fixtures))
with tempfile.TemporaryDirectory() as tmp:
    cpp, exe = Path(tmp)/'check.cpp', Path(tmp)/'check.exe'
    cpp.write_text(code)
    include = Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/include'
    subprocess.run([a.compiler, '-std=c++20', '-I'+str(include), str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print(f'Clear rectangle checks passed; {len(fixtures)-input_count} captured rectangles, {input_count} captured vertices')
