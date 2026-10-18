"""Compare actual imported thunks to declarations in the pinned SDK source."""
import argparse
import collections
import json
import re
from pathlib import Path
from analyze import ROOT

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    a=p.parse_args()
    xex=json.loads((ROOT/'logs/xex-analysis.json').read_text())
    source='\n'.join(p.read_text(encoding='utf-8',errors='replace') for p in (a.source/'src/kernel').rglob('*.cpp'))
    stubs=set(re.findall(r'REX_EXPORT_STUB\(\s*__imp__(\w+)',source))
    actual=set(re.findall(r'REX_EXPORT\(\s*__imp__(\w+)',source))
    rows=[dict(i,sdk_declaration='stub' if i['name'] in stubs else 'implementation'
               if i['name'] in actual else 'not_found_by_macro_scan') for i in xex['function_imports']]
    (ROOT/'logs/import-coverage.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(collections.Counter(i['sdk_declaration'] for i in rows))
