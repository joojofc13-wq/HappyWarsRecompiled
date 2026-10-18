"""Batch-report missing metadata entries and runtime observations, keeping speculative pointers separate."""
import hashlib
import json
import re
import struct
from collections import defaultdict
from analyze import ROOT,pe_report
from audit_indirect_targets import audit

if __name__=='__main__':
    image=(ROOT/'private/loaded-image.bin').read_bytes()
    pe=pe_report(image)
    base=int(pe['image_base'],16)
    code=next(s for s in pe['sections'] if s['name']=='.text')
    low=base+code['rva']; high=low+code['virtual_size']
    registered={int(v,16) for v in re.findall(r'\{ (0x[0-9A-Fa-f]+),',
        (ROOT/'generated/default/happywars_init.cpp').read_text(encoding='utf-8'))}
    supplemental={int(v,16) for v in re.findall(r'0x[0-9A-Fa-f]+',
        (ROOT/'private/aot-callbacks/verified_blr_entries.inc').read_text())}
    declared=registered|supplemental
    pdata=next(s for s in pe['sections'] if s['name']=='.pdata')
    entries={address for address,packed in struct.iter_unpack('>II',
        image[pdata['rva']:pdata['rva']+pdata['virtual_size']]) if low<=address<high and address%4==0}
    seen=defaultdict(set)
    for log in (ROOT/'logs').glob('runtime-smoke*.log'):
        for address in re.findall(r'unregistered function at guest address (0x[0-9A-Fa-f]+)',
                                  log.read_text(encoding='utf-8',errors='replace')):
            seen[int(address,16)].add(log.name)
    audit()
    candidates=json.loads((ROOT/'logs/indirect-target-audit.json').read_text())
    report=dict(image_sha256=hashlib.sha256(image).hexdigest(),generated_registration_count=len(registered),
        original_pdata_entry_count=len(entries),
        missing_pdata_entries=[hex(a) for a in sorted(entries-registered)],
        supplemental_original_blr_count=len(supplemental),
        observed_runtime_failures=[dict(address=hex(a),generated_registration_present=a in registered,
            supplemental_original_blr_declared=a in supplemental,
            observed_in=sorted(logs)) for a,logs in sorted(seen.items())],
        observed_failures_without_declared_registration=[hex(a) for a in sorted(seen) if a not in declared],
        speculative_data_pointer_count=candidates['missing_referenced_addresses'],
        speculative_details='indirect-target-audit.json',
        limitation='Reports generated registration, not native playability. Speculative pointers include internal labels and metadata. A single execution does not explore every future indirect call.')
    (ROOT/'logs/entry-diagnostics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('generated_registration_count','original_pdata_entry_count',
        'missing_pdata_entries','observed_failures_without_declared_registration','speculative_data_pointer_count')},indent=2))
