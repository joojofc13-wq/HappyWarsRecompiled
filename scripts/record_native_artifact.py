"""Record the real native PE artifact; never infer playability from its presence."""
import hashlib
import json
import struct
from analyze import ROOT

if __name__=='__main__':
    path=ROOT/'build/game/HappyWars.exe'
    data=path.read_bytes()
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0':
        raise SystemExit('Not a valid PE artifact')
    machine=struct.unpack_from('<H',data,pe+4)[0]
    if machine!=0x8664:
        raise SystemExit(f'Expected AMD64, got {machine:#x}')
    report=dict(path=str(path.relative_to(ROOT)),size=len(data),sha256=hashlib.sha256(data).hexdigest(),
        machine=hex(machine),architecture='Windows x64 AMD64 native PE',
        playability='Not demonstrated; consult runtime-smoke-result.json and STATUS.md')
    (ROOT/'logs/native-artifact.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
