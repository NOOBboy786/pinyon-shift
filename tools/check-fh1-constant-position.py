"""Verify the constant-position shader preserves viewport mul/mad in compiled DXBC."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fxc',default='C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/fxc.exe')
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'thirdparty/shiftglue-sdk/src/graphics/shaders/fh1_constant_position.vs.hlsl')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        assembly=Path(temp)/'constant.txt'
        subprocess.run([args.fxc,'/nologo','/T','vs_5_1','/E','main','/O3','/Fc',str(assembly),'/Fo',str(Path(temp)/'constant.dxbc'),str(args.source)],check=True,capture_output=True)
        text=assembly.read_text()
    # Zero * viewport scale must survive for IEEE exceptional values; the
    # offset must use the same fused mad as the translated reference.
    multiply=re.search(r'^mul \[precise\(xyz\)\] (r\d+)\.xyz, CB0\[0\]\[8\]\.xyzx, l\(0\.000000, 0\.000000, 0\.000000, 0\.000000\)',text,re.M)
    assert multiply,'Missing precise zero-times-scale instruction'
    assert re.search(r'^mad \[precise\(xyz\)\] o0\.xyz, CB0\[0\]\[9\]\.xyzx, l\(1\.000000, 1\.000000, 1\.000000, 0\.000000\), '+multiply[1]+r'\.xyzx',text,re.M),'Viewport offset must remain fused'
    assert 'mov o0.w, l(1.000000)' in text
    assert not re.search(r'^\s*(ld_|sample|store)',text,re.M),'Constant shader must not fetch vertex resources'
    print('Compiled constant-position viewport checks passed')


if __name__=='__main__':main()
