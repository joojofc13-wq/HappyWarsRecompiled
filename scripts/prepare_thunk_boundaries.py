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

def member_virtual_register(image,offset):
    """Recognize a complete member-object virtual-call adapter, not an inner block."""
    if offset<0 or offset+24>len(image):
        return None
    load,adjust,table,target,mtctr,bctr=struct.unpack_from('>6I',image,offset)
    register=(load>>21)&31
    if register not in (10,11,12) or load&0xffff0000!=(0x80030000|(register<<21)):
        return None
    if adjust&0xffff0000!=(0x38600000|(register<<16)):
        return None
    if table!=(0x80000000|(register<<21)|(register<<16)|(adjust&0xffff)):
        return None
    if target&0xffff0000!=(0x80000000|(register<<21)|(register<<16)):
        return None
    if mtctr!=(0x7c0903a6|(register<<21)) or bctr!=0x4e800420:
        return None
    return register

def constant_tail(image,offset,address):
    if offset<0 or offset+8>len(image):
        return None
    first,branch=struct.unpack_from('>II',image,offset)
    register=(first>>21)&31
    if first&0xfc1f0000!=0x38000000 or not 3<=register<=12 or branch&0xfc000003!=0x48000000:
        return None
    displacement=branch&0x03fffffc
    if displacement&0x02000000:
        displacement-=0x04000000
    return register,(address+4+displacement)&0xffffffff

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
    # Adjacent argument specializations may have their addresses constructed
    # in code rather than stored in a vtable. Require a registered first entry,
    # identical argument register and destination, and complete non-linking tails.
    for anchor in registered:
        offset=anchor-base
        if not start<=offset<end:
            continue
        signature=constant_tail(image,offset,anchor)
        if signature is None or signature[1] not in registered:
            continue
        previous=int.from_bytes(image[offset-4:offset],'big')
        if previous not in (0,0x4e800020,0x4e800420) and previous&0xfc000003!=0x48000000:
            continue
        siblings=[]
        for delta in range(8,128,8):
            address=anchor+delta
            if offset+delta+8>end or constant_tail(image,offset+delta,address)!=signature:
                break
            if address not in registered:
                siblings.append(address)
        if siblings:
            candidates.extend(dict(address=hex(a),references=[],exact_argument_family=True) for a in siblings)
    for prefix in ((0x80030000|(r<<21)).to_bytes(4,'big') for r in (10,11,12)):
        offset=image.find(prefix,start,end)
        while offset>=0:
            address=base+offset
            if offset%4==0 and offset+16<=end and address not in registered and \
               virtual_registers(image,offset) is not None:
                candidates.append(dict(address=hex(address),references=[],exact_vcall_pattern=True))
            offset=image.find(prefix,offset+4,end)
    # Member adapters first adjust this to a nested object's vtable field.
    # Match every register dependency and the final non-linking tail dispatch.
    for prefix in ((0x80030000|(r<<21)).to_bytes(4,'big')[:2] for r in (10,11,12)):
        offset=image.find(prefix,start,end)
        while offset>=0:
            address=base+offset
            if offset%4==0 and offset+24<=end and address not in registered and \
               member_virtual_register(image,offset) is not None:
                candidates.append(dict(address=hex(address),references=[],exact_vcall_pattern=True))
            offset=image.find(prefix,offset+2,end)
    entries={}
    for candidate in candidates:
        if not candidate.get('exact_vcall_pattern') and not candidate.get('exact_argument_family') and not any(r['adjacent_code_pointers'] for r in candidate['references']):
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
        member_register=member_virtual_register(image,offset)
        if registers is not None or member_register is not None:
            previous=int.from_bytes(image[offset-4:offset],'big')
            if previous not in (0,0x4e800020,0x4e800420) and previous&0xfc000001!=0x48000000:
                # A tail-call block preceded by argument preparation or a
                # conditional branch belongs to the containing function.
                continue
            size=24 if member_register is not None else 16
            entries[address]=dict(address=hex(address),size=size,target='ctr (virtual dispatch)',
                kind='lwz; addi; lwz; lwz; mtctr; bctr' if size==24 else 'lwz; lwz; mtctr; bctr',
                table_register=member_register if size==24 else registers[0],
                target_register=member_register if size==24 else registers[1],
                original_bytes=image[offset:offset+size].hex())
            continue
        # Constant-argument adapters (li rN,imm; b) are complete functions too.
        # Require a preceding terminator, data-pointer evidence and a known
        # destination, excluding internal blocks covered by unwind metadata.
        constant_argument=(first&0xfc1f0000==0x38000000 and 3<=((first>>21)&31)<=12)
        load_argument=first&0xffff0000==0x80630000
        if constant_argument or load_argument:
            previous=int.from_bytes(image[offset-4:offset],'big')
            if previous not in (0,0x4e800020,0x4e800420) and previous&0xfc000003!=0x48000000:
                continue
        size=8 if first&0xffff0000==0x38630000 or constant_argument or load_argument else 4
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
            kind='li rN,imm; b' if constant_argument else 'lwz r3,imm(r3); b' if load_argument else 'addi r3,r3,imm; b' if size==8 else 'b',
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
