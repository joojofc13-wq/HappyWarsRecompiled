"""Conservative PPC lis/addi or lis/ori string references and direct import calls.

These are static leads, not semantic proof. No patches are generated.
"""
import bisect
import collections
import json
import re
import struct
from pathlib import Path
from analyze import ROOT,pe_report,word


def signed16(v):
    return (v&32767)-(v&32768)


if __name__=='__main__':
    image=(ROOT/'private/loaded-image.bin').read_bytes()
    xex=json.loads((ROOT/'logs/xex-analysis.json').read_text())
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    pdata=next(s for s in pe['sections'] if s['name']=='.pdata')
    functions=[]
    for o in range(pdata['rva'],pdata['rva']+pdata['virtual_size'],8):
        start,packed=struct.unpack_from('>II',image,o)
        functions.append((start,start+max(4,((packed>>8)&0x3fffff)*4)))
    functions.sort()
    starts=[x[0] for x in functions]
    def owner(address):
        i=bisect.bisect_right(starts,address)-1
        return hex(functions[i][0]) if i>=0 and address<functions[i][1] else None
    keywords=re.compile(rb'skirmish|happy.?card|offline|inventory|reward|unlock|game.?mode|save.?data',re.I)
    strings={base+m.start():m.group().decode('ascii') for m in re.finditer(rb'[ -~]{5,500}',image)
             if keywords.search(m.group())}
    imported={int(i['thunk'],16):i for i in xex['function_imports']}
    refs=[]
    calls=[]
    for section in pe['sections']:
        if not int(section['flags'],16)&0x20000000:
            continue
        start=section['rva']
        words=list(struct.unpack('>'+str(section['virtual_size']//4)+'I',
                                image[start:start+(section['virtual_size']//4)*4]))
        for i,insn in enumerate(words):
            address=base+start+i*4
            op=insn>>26
            if op==18:
                displacement=insn&0x03fffffc
                if displacement&0x02000000:
                    displacement-=0x04000000
                target=(displacement if insn&2 else address+displacement)&0xffffffff
                if target in imported:
                    calls.append(dict(address=hex(address),function=owner(address),target=imported[target]['name']))
            if op!=15 or (insn>>16)&31:
                continue
            register=(insn>>21)&31
            high=(signed16(insn)<<16)&0xffffffff
            for j in range(i+1,min(i+7,len(words))):
                nxt=words[j]
                nextop=nxt>>26
                value=None
                if nextop==14 and (nxt>>16)&31==register:
                    value=(high+signed16(nxt))&0xffffffff
                elif nextop==24 and (nxt>>21)&31==register:
                    value=high|(nxt&65535)
                if value in strings:
                    refs.append(dict(address=hex(address),function=owner(address),string_address=hex(value),text=strings[value]))
                # Stop on a branch or definite overwrite of the source GPR.
                if nextop in (16,18,19):
                    break
                if nextop in (14,15,32,34,40,42) and (nxt>>21)&31==register:
                    break
    result=dict(pdata_entries=len(functions),candidate_string_refs=refs,direct_import_calls=calls,
        limitations=['Only short lis/addi and lis/ori patterns; no data flow proof',
                     'Indirect calls, r2-based loads, and strings inside resource archives are not covered'])
    (ROOT/'logs/xrefs.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'{len(functions)} PDATA entries; {len(refs)} candidate string references; {len(calls)} direct import calls')
