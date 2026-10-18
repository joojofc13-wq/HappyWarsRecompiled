"""Integration checks against real game entries previously omitted by GapFill."""
import json
import re
import sys
import tomllib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze import ROOT

registered={int(a,16) for a in re.findall(r'\{ (0x[0-9A-Fa-f]+),',
    (ROOT/'generated/default/happywars_init.cpp').read_text(encoding='utf-8'))}
declared=set()
for name in ('function-boundaries.toml','verified-thunks.toml'):
    declared.update(int(a,0) for a in tomllib.loads((ROOT/'config'/name).read_text())['functions'])
image=(ROOT/'private/loaded-image.bin').read_bytes()
# Complete adjacent file-wrapper methods, each ending in a real bctr. These
# entries must come from discovery, not the manually supplied configuration.
for address,size in ((0x82C92A60,0x20),(0x82C92A80,0x20),(0x82C92AA0,0x24),
                     (0x82C92AC8,0x20),(0x82C92AE8,0x20)):
    assert address not in declared, f'{address:#x} was manually declared'
    assert address in registered, f'Automatic discovery omitted {address:#x}'
    assert image[address-0x82000000+size-4:address-0x82000000+size]==bytes.fromhex('4e800420')
assert not json.loads((ROOT/'logs/codegen-audit.json').read_text())['explicit_placeholders']
assert not json.loads((ROOT/'logs/label-audit.json').read_text())['findings']
report=dict(automatic_entries_verified=5,manual_declarations_for_these_entries=0,
    translation_audits_clean=True,scope='Real game discovery and source checks; not gameplay')
(ROOT/'logs/discovery-regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
