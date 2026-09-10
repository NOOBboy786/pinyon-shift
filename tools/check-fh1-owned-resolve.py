"""Independent per-pixel 1x/2x depth resolve addressing against captured buffers."""
from pathlib import Path
import argparse, json
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('capture_directory',type=Path,help='Publication export containing report.json and before/after/source buffers')
root=parser.parse_args().capture_directory
report=json.loads((root/'report.json').read_text());assert 'error' not in report
results=[]
for row in report['copies']:
 eid=row['event'];v={v['name']:v['uints'][0] for b in row['constants'] for v in b['values']}
 e=v['xe_resolve_edram_info'];c=v['xe_resolve_coordinate_info'];d=v['xe_resolve_dest_info'];dc=v['xe_resolve_dest_coordinate_info']
 scale=(c>>16)&7;assert scale==((c>>19)&7) and scale in (1,2)
 assert ((e>>10)&3)==0 and e&4096 # Single-sample depth source.
 assert d&7==2 and not d&8 and not d&(1<<24) # Byte reverse, 2D, no channel swap.
 assert dc>>28==0
 width=((c>>5)&2047)*8*scale;height=row['dispatch'][1]*8
 y,x=np.indices((height,width),dtype=np.int64)
 fill=scale//2 if e&(1<<29) else 0
 sx=np.maximum(x,fill)+(c&15)*8*scale;sy=np.maximum(y,fill)+((c>>4)&1)*8*scale
 tile=(e>>13)&2047;pitch=e&1023
 # EDRAM depth samples exchange the two 40-sample half-rows.
 tw=80*scale;th=16*scale
 local_x=(sx%tw+tw//2)%tw
 address=(((tile+(sy//th)*pitch+sx//tw)%2048)*tw*th+(sy%th)*tw+local_x)
 source=np.fromfile(root/f'{eid}-source.bin',dtype='<u4')
 value=source[address].byteswap()
 px=x+((dc>>20)&15)*8*scale;py=y+((dc>>24)&15)*8*scale
 dx=(px//4//scale)*4;dy=py//scale;dest_pitch=(dc&1023)*32
 # Xbox 360 32bpp 2D tiled byte address, independently evaluated per pixel.
 macro=((dx>>5)+(dy>>5)*(dest_pitch>>5))<<9
 micro=((dx&7)+((dy&14)<<2))<<2
 offset=macro+((micro&~15)<<1)+(micro&15)+((dy&1)<<4)
 dest=(((offset&~511)<<3)+((dy&16)<<7)+((offset&448)<<2)+
       (((((dy&8)>>2)+(dx>>3))&3)<<6)+(offset&63))*scale*scale
 dest=(dest+((px//4%scale)*scale+py%scale)*16+(px%4)*4)//4
 before=np.fromfile(root/f'{eid}-before.bin',dtype='<u4');after=np.fromfile(root/f'{eid}-after.bin',dtype='<u4')
 assert dest.max()<len(before) and len(np.unique(dest))==dest.size
 expected=before.copy();expected[dest]=value
 mismatches=int(np.count_nonzero(expected!=after))
 result=dict(event=eid,pixels=dest.size,checked_bytes=after.nbytes,mismatches=mismatches)
 results.append(result);print(result)
(root/'value-check.json').write_text(json.dumps(dict(passed=all(r['mismatches']==0 for r in results),checks=results),indent=2)+'\n')
assert len(results)==4 and all(r['mismatches']==0 for r in results)
