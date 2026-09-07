"""Compile native terrain shaders and verify exclusive SRV/UAV fetches."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',required=True,help='Path to fxc.exe')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/shaders'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    for variant in ['lit','depth_standard','depth_offset','depth_standard_owned','depth_offset_owned']:
        source=root/('fh1_terrain_lit.vs.hlsl' if variant=='lit' else 'fh1_terrain_depth.vs.hlsl')
        raw=tmp/(variant+'.dxbc');asm=tmp/(variant+'.txt')
        args=[a.compiler,'/nologo','/T','vs_5_1','/E','main','/O3','/Fo',str(raw),'/Fc',str(asm)]
        if 'standard' in variant:args+=['/D','FH1_TERRAIN_DEPTH_STANDARD_TRANSFORM=1']
        if variant.endswith('owned'):args+=['/D','FH1_TERRAIN_OWNED_GEOMETRY=1']
        subprocess.run(args+[str(source)],check=True,stdout=subprocess.DEVNULL)
        header=(root/'bytecode/d3d12_5_1'/('fh1_terrain_'+variant+'_vs.h')).read_text()
        array=header[header.index('const BYTE'):];array=array[array.index('{')+1:array.index('}')]
        assert raw.read_bytes()==bytes(map(int,re.findall(r'\d+',array))),variant+' generated header differs'
        disassembly=asm.read_text()
        for line in disassembly.splitlines():
            assert not (line.strip().startswith('div ') and re.search(r'\b(?:32767|65535|127|1023|511)\.000000',line)),variant+': packed normalization must multiply by reciprocal'
        if variant.endswith('owned'):continue
        stack=[];loads=[]
        for line in asm.read_text().splitlines():
            line=line.strip()
            if line.startswith(('if_nz ','if_z ')):stack.append([line,False])
            elif line=='else':stack[-1][1]=True
            elif line=='endif':stack.pop()
            elif line.startswith('ld_raw'):
                assert stack,variant+': unconditional raw fetch'
                loads.append((line,tuple((a,b) for a,b in stack)))
        assert loads and len(loads)%2==0,variant
        for i in range(0,len(loads),2):
            first,fb=loads[i];second,sb=loads[i+1]
            assert 'U0[0]' in first and 'T0[0]' in second,variant
            assert fb[:-1]==sb[:-1] and fb[-1][0]==sb[-1][0],variant
            assert not fb[-1][1] and sb[-1][1],variant
print('Five terrain bytecodes match source; packed normalization uses reciprocals and shared fetches select one resource')
