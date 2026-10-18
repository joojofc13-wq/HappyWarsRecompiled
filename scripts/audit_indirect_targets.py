"""Report code pointers absent from the AOT function table; never assume every pointer is a function."""
import bisect
import json
import re
import struct
from analyze import ROOT, pe_report

def audit():
    image=(ROOT/'private/loaded-image.bin').read_bytes()
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    code=next(s for s in pe['sections'] if s['name']=='.text')
    low=base+code['rva']; high=low+code['virtual_size']
    registered={int(v,16) for v in re.findall(r'\{ (0x[0-9A-Fa-f]+),',
        (ROOT/'generated/default/happywars_init.cpp').read_text(encoding='utf-8'))}
    functions=sorted(registered)
    references={}
    for section in pe['sections']:
        if section['name'] not in ('.rdata','.data'):
            continue
        offset=section['rva']; length=section['virtual_size']//4*4
        words=[v for v, in struct.iter_unpack('>I',image[offset:offset+length])]
        for i,value in enumerate(words):
            if low<=value<high and value%4==0 and value not in registered:
                neighbors=sum(low<=words[j]<high and words[j]%4==0
                    for j in (i-1,i+1) if 0<=j<len(words))
                references.setdefault(value,[]).append(dict(address=hex(base+offset+i*4),
                    adjacent_code_pointers=neighbors))
    entries=[]
    for value,refs in sorted(references.items()):
        index=bisect.bisect_right(functions,value)
        entries.append(dict(address=hex(value),opcode=image[value-base:value-base+4].hex(),
            previous_registered=hex(functions[index-1]) if index else None,
            next_registered=hex(functions[index]) if index<len(functions) else None,
            references=refs))
    report=dict(missing_referenced_addresses=len(entries),entries=entries,
        limitation='Candidates only: references can target internal labels or data; inspect original control flow before registration')
    (ROOT/'logs/indirect-target-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(missing_referenced_addresses=len(entries),
        with_neighboring_code_pointers=sum(any(r['adjacent_code_pointers'] for r in e['references']) for e in entries))))

if __name__=='__main__':
    audit()
