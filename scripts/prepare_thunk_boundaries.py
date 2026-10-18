"""Declare referenced short AOT entries using exact original instruction patterns."""
import json
import re
import struct
import tomllib
from bisect import bisect_right
from analyze import ROOT,pe_report
from audit_indirect_targets import audit

def virtual_registers(image,offset):
    if offset<0 or offset+16>len(image):
        return None
    first,second,third,fourth=struct.unpack_from('>4I',image,offset)
    table=(first>>21)&31
    target=(second>>21)&31
    if table not in (10,11,12) or target not in (10,11,12):
        return None
    if first&0xfc1fffff!=0x80030000 or second&0xfc1f0000!=0x80000000|(table<<16):
        return None
    if third!=(0x7c0903a6|(target<<21)) or fourth!=0x4e800420:
        return None
    return table,target

def prepare():
    audit()
    candidates=json.loads((ROOT/'logs/indirect-target-audit.json').read_text())['entries']
    image=(ROOT/'private/loaded-image.bin').read_bytes()
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    registered={int(v,16) for v in re.findall(r'\{ (0x[0-9A-Fa-f]+),',
        (ROOT/'generated/default/happywars_init.cpp').read_text(encoding='utf-8'))}
    explicit=tomllib.loads((ROOT/'config/function-boundaries.toml').read_text(encoding='utf-8'))['functions']
    ranges=[(int(a,0),int(a,0)+v['size']) for a,v in explicit.items()]
    pdata=next(s for s in pe['sections'] if s['name']=='.pdata')
    for address,packed in struct.iter_unpack('>II',image[pdata['rva']:pdata['rva']+pdata['virtual_size']]):
        length=((packed>>8)&0x3fffff)*4
        if length:
            ranges.append((address,address+length))
    # Original unwind metadata and manually reviewed complete functions take
    # precedence. Do not turn their internal tail-call blocks into new entries.
    merged=[]
    for lo,hi in sorted(ranges):
        if merged and lo<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
        else:
            merged.append((lo,hi))
    starts=[lo for lo,hi in merged]
    output=ROOT/'config/verified-thunks.toml'
    prior=[int(v,16) for v in re.findall(r'^(0x[0-9A-Fa-f]+) =',output.read_text() if output.exists() else '',re.M)]
    # Retain previously verified declarations on subsequent runs after codegen
    # has registered them. Recheck their original bytes and destinations.
    candidates.extend(dict(address=hex(a),references=[dict(adjacent_code_pointers=1)]) for a in prior)
    # MSVC emits these complete four-instruction vcall thunks even when their
    # addresses are materialized in code instead of appearing in .rdata.
    section=next(s for s in pe['sections'] if s['name']=='.text')
    start=section['rva']; end=start+section['virtual_size']
    for prefix in ((0x80030000|(r<<21)).to_bytes(4,'big') for r in (10,11,12)):
        offset=image.find(prefix,start,end)
        while offset>=0:
            address=base+offset
            if offset%4==0 and offset+16<=end and address not in registered and \
               virtual_registers(image,offset) is not None:
                candidates.append(dict(address=hex(address),references=[],exact_vcall_pattern=True))
            offset=image.find(prefix,offset+4,end)
    entries={}
    for candidate in candidates:
        if not candidate.get('exact_vcall_pattern') and not any(r['adjacent_code_pointers'] for r in candidate['references']):
            continue
        address=int(candidate['address'],16)
        containing=bisect_right(starts,address)-1
        if containing>=0 and address<merged[containing][1]:
            continue
        offset=address-base
        first=int.from_bytes(image[offset:offset+4],'big')
        # Exact four-instruction virtual-dispatch entry. Preserve the guest
        # context; the SDK translates the loads and indirect tail call normally.
        registers=virtual_registers(image,offset)
        if registers is not None:
            previous=int.from_bytes(image[offset-4:offset],'big')
            if previous not in (0,0x4e800020,0x4e800420) and previous&0xfc000001!=0x48000000:
                # A tail-call block preceded by argument preparation or a
                # conditional branch belongs to the containing function.
                continue
            entries[address]=dict(address=hex(address),size=16,target='ctr (virtual dispatch)',
                kind='lwz; lwz; mtctr; bctr',table_register=registers[0],target_register=registers[1],
                original_bytes=image[offset:offset+16].hex())
            continue
        # Constant-argument adapters (li rN,imm; b) are complete functions too.
        # Require a preceding terminator, data-pointer evidence and a known
        # destination, excluding internal blocks covered by unwind metadata.
        constant_argument=(first&0xfc1f0000==0x38000000 and 3<=((first>>21)&31)<=12)
        if constant_argument:
            previous=int.from_bytes(image[offset-4:offset],'big')
            if previous not in (0,0x4e800020,0x4e800420) and previous&0xfc000003!=0x48000000:
                continue
        size=8 if first&0xffff0000==0x38630000 or constant_argument else 4
        branch_address=address+size-4
        branch=int.from_bytes(image[branch_address-base:branch_address-base+4],'big')
        # Relative, non-linking, unconditional b only; no bc, bctr or bctrl.
        if branch&0xfc000003!=0x48000000:
            continue
        displacement=branch&0x03fffffc
        if displacement&0x02000000:
            displacement-=0x04000000
        target=(branch_address+displacement)&0xffffffff
        if target not in registered or target==address:
            continue
        entries[address]=dict(address=hex(address),size=size,target=hex(target),
            kind='li rN,imm; b' if constant_argument else 'addi r3,r3,imm; b' if size==8 else 'b',
            original_bytes=image[offset:offset+size].hex())
    lines=['# Verified real short tail-call entries; generated from local game data.','[functions]']
    lines.extend(f'0x{a:08X} = {{ size = {e["size"]}, share_registers = true }} # {e["kind"]} -> {e["target"]}'
        for a,e in sorted(entries.items()))
    content='\n'.join(lines)+'\n'
    if not output.exists() or output.read_text(encoding='utf-8')!=content:
        output.write_text(content,encoding='utf-8')
    report=dict(count=len(entries),entries=[e for a,e in sorted(entries.items())],
        scope='Explicit AOT entry boundaries; SDK translates original instructions unchanged')
    (ROOT/'logs/verified-thunk-boundaries.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Prepared {len(entries)} verified real tail-call entries; current target included: {0x830697e8 in entries}')

if __name__=='__main__':
    prepare()
