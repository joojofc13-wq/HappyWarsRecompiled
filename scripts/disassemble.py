"""Disassemble a range of the SDK-loaded PowerPC image, using optional Capstone."""
import argparse
import json
import sys
from pathlib import Path
from analyze import ROOT,pe_report,word

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--address',type=lambda x:int(x,0),required=True)
    p.add_argument('--size',type=lambda x:int(x,0),default=128)
    p.add_argument('--python-path',type=Path,default=ROOT/'tools/python')
    p.add_argument('--image',type=Path,default=ROOT/'private/loaded-image.bin')
    a=p.parse_args()
    sys.path.insert(0,str(a.python_path.resolve()))
    from capstone import Cs,CS_ARCH_PPC,CS_MODE_32,CS_MODE_BIG_ENDIAN
    image=a.image.read_bytes()
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    offset=a.address-base
    if offset<0 or a.size<4 or offset+a.size>len(image) or a.address%4:
        raise SystemExit('Invalid image range')
    decoder=Cs(CS_ARCH_PPC,CS_MODE_32|CS_MODE_BIG_ENDIAN)
    decoder.skipdata=True
    for instruction in decoder.disasm(image[offset:offset+a.size],a.address):
        print(f'{instruction.address:08X} {instruction.bytes.hex():8s} {instruction.mnemonic:10s} {instruction.op_str}')
