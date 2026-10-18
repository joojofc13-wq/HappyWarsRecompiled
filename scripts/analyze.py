"""Parse real XEX2 metadata and an optional SDK-loaded PE memory snapshot."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def word(data, offset, size=4, endian='big'):
    if offset<0 or offset+size>len(data):
        raise ValueError(f'Out-of-range field at {offset:#x}')
    return int.from_bytes(data[offset:offset+size],endian)


def version(v):
    return f'{v>>28}.{(v>>24)&15}.{(v>>8)&65535}.{v&255}'


def xex_report(path):
    data=Path(path).read_bytes()
    if data[:4]!=b'XEX2':
        raise ValueError('Expected XEX2')
    u=lambda o:word(data,o)
    count=u(20)
    if count>4096:
        raise ValueError('Implausible optional-header count')
    headers={u(24+i*8):u(28+i*8) for i in range(count)}
    security=u(16)
    report=dict(sha256=hashlib.sha256(data).hexdigest(),size=len(data),
        magic='XEX2',module_flags=hex(u(4)),header_size=u(8),security_offset=security,
        image_size=u(security+4),load_address=hex(u(security+0x110)),
        entry_point=hex(headers.get(0x10100,0)),export_table=hex(u(security+0x160)),
        optional_headers={hex(k):hex(v) for k,v in headers.items()},
        limitations=['XEX header analysis does not decrypt the PE image or validate its RSA signature'])
    if 0x3ff in headers:
        o=headers[0x3ff]
        report['file_format']=dict(size=u(o),encryption=word(data,o+4,2),compression=word(data,o+6,2))
    if 0x40006 in headers:
        o=headers[0x40006]
        report['execution']=dict(media_id=hex(u(o)),version=version(u(o+4)),
                                 base_version=version(u(o+8)),title_id=hex(u(o+12)))
    if 0x20104 in headers:
        o=headers[0x20104]
        report['tls']=dict(zip(('slots','raw_address','data_size','raw_size'),struct.unpack_from('>4I',data,o)))
    report['default_stack_size']=headers.get(0x20200)
    if 0x200ff in headers:
        o=headers[0x200ff]
        report['static_libraries']=[]
        for pos in range(o+4,o+u(o),16):
            report['static_libraries'].append(dict(name=data[pos:pos+8].rstrip(b'\0').decode('ascii'),
                major=word(data,pos+8,2),minor=word(data,pos+10,2),build=word(data,pos+12,2)))
    libraries=[]
    if 0x103ff in headers:
        o=headers[0x103ff]
        strings_size=u(o+4)
        library_count=u(o+8)
        strings=[]
        pos=o+12
        end=pos+strings_size
        while pos<end:
            z=data.find(b'\0',pos,end)
            if z<0:
                raise ValueError('Unterminated import library name')
            strings.append(data[pos:z].decode('ascii'))
            pos=(z+4)&~3
        pos=end
        for _ in range(library_count):
            name_index=word(data,pos+0x24,2)
            n=word(data,pos+0x26,2)
            if name_index>=len(strings) or u(pos)<40+n*4:
                raise ValueError('Invalid import library bounds')
            libraries.append(dict(name=strings[name_index],version=version(u(pos+28)),
                min_version=version(u(pos+32)),record_count=n,
                record_addresses=[u(pos+40+i*4) for i in range(n)]))
            pos+=u(pos)
    report['import_libraries']=libraries
    return report


def pe_report(data):
    u=lambda o,n=4:word(data,o,n,'little')
    if data[:2]!=b'MZ':
        raise ValueError('Memory snapshot does not start with MZ')
    pe=u(0x3c)
    if data[pe:pe+4]!=b'PE\0\0':
        raise ValueError('PE signature missing')
    optional=pe+24
    if u(optional,2)!=0x10b:
        raise ValueError('Expected PE32 guest image')
    sections=[]
    section_table=optional+u(pe+20,2)
    for i in range(u(pe+6,2)):
        p=section_table+i*40
        sections.append(dict(name=data[p:p+8].rstrip(b'\0').decode('ascii'),
            virtual_size=u(p+8),rva=u(p+12),raw_size=u(p+16),raw_offset=u(p+20),flags=hex(u(p+36))))
    directories=[]
    for i in range(min(u(optional+92),16)):
        directories.append(dict(index=i,rva=u(optional+96+i*8),size=u(optional+100+i*8)))
    return dict(machine=hex(u(pe+4,2)),machine_expected='0x1f2 = PowerPC big-endian',
        image_base=hex(u(optional+28)),entry_rva=hex(u(optional+16)),image_size=u(optional+56),
        sections=sections,data_directories=directories,
        note='Mapped image obtained from ReXGlue after load; variable imports may have been patched')


def import_report(xex, image, table_root):
    base=int(xex['load_address'],16)
    result=[]
    for library in xex['import_libraries']:
        module=library['name'].split('.')[0]
        names={}
        table=Path(table_root)/module/(module+'_table.inc')
        if table.exists():
            for ordinal,name in re.findall(r'XE_EXPORT\([^,]+,\s*(0x[0-9A-Fa-f]+),\s*(\w+)',table.read_text()):
                names[int(ordinal,16)]=name
        for address in library['record_addresses']:
            value=word(image,address-base)
            record_type=value>>24
            # Only type-1 thunk records remain authoritative after SDK load.
            if record_type==1:
                ordinal=value&65535
                result.append(dict(library=library['name'],ordinal=ordinal,
                    name=names.get(ordinal,f'ordinal_{ordinal:04X}'),thunk=hex(address)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--xex',type=Path,default=ROOT/'private/game/Default.xex')
    p.add_argument('--image',type=Path)
    p.add_argument('--xenia-kernel',type=Path)
    a=p.parse_args()
    report=xex_report(a.xex)
    if a.image:
        image=a.image.read_bytes()
        report['mapped_pe']=pe_report(image)
        if a.xenia_kernel:
            report['function_imports']=import_report(report,image,a.xenia_kernel)
    (ROOT/'logs/xex-analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('optional_headers','function_imports','import_libraries')},indent=2))
