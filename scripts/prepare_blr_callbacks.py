"""Find referenced, unregistered functions whose original body is exactly blr.

Produces an AOT address list. The native body is a compiled return; it does not
invent return values or provide a fallback for arbitrary missing functions.
"""
import json
import re
import struct
from analyze import ROOT,pe_report

if __name__=='__main__':
    image=(ROOT/'private/loaded-image.bin').read_bytes()
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    code=next(s for s in pe['sections'] if s['name']=='.text')
    start=code['rva']; end=start+code['virtual_size']
    returns={base+o for o in range(start,end,4) if image[o:o+4]==b'\x4e\x80\x00\x20'}
    registered={int(x,16) for x in re.findall(r'\{ (0x[0-9A-Fa-f]+),',
                (ROOT/'generated/default/happywars_init.cpp').read_text(encoding='utf-8'))}
    references={}
    for section in pe['sections']:
        if section['name'] not in ('.rdata','.data'):
            continue
        data=image[section['rva']:section['rva']+section['virtual_size']]
        for i,(value,) in enumerate(struct.iter_unpack('>I',data[:len(data)//4*4])):
            if value in returns and value not in registered:
                references.setdefault(value,[]).append(base+section['rva']+i*4)
    folder=ROOT/'private/aot-callbacks'
    folder.mkdir(parents=True,exist_ok=True)
    include=folder/'verified_blr_entries.inc'
    content=''.join(f'0x{address:08X}u,\n' for address in sorted(references))
    if not include.exists() or include.read_text(encoding='ascii')!=content:
        include.write_text(content,encoding='ascii')
    report=dict(count=len(references),source_instruction='4e800020 (blr)',
        entries=[dict(address=hex(a),references=[hex(r) for r in refs[:8]]) for a,refs in sorted(references.items())],
        native_behavior='Return without changing PPC registers; no fabricated success status',
        generation='Build-time only; no CPU interpreter or JIT')
    (ROOT/'logs/verified-blr-callbacks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Prepared {len(references)} referenced original blr callbacks; includes current target: {0x83353380 in references}")
