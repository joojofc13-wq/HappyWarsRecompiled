"""Require identical ordered entries in the SDK mapping and registration outputs."""
import hashlib
import json
import re
from analyze import ROOT

def verify():
    folder=ROOT/'generated/default'
    calls=(folder/'happywars_register.cpp').read_text(encoding='utf-8')
    mappings=(folder/'happywars_init.cpp').read_text(encoding='utf-8')
    left=re.findall(r'registrar->SetFunction\((0x[0-9A-Fa-f]+), (\w+)\);',calls)
    right=re.findall(r'\{ (0x[0-9A-Fa-f]+), (\w+) \}',mappings)
    if not left or left!=right or calls.count('registrar->SetFunction(')!=len(left):
        raise ValueError('Generated ordered registration and mapping lists differ')
    if mappings.count('{ 0, nullptr }')!=1 or not mappings.rstrip().endswith('{ 0, nullptr }\n};'):
        raise ValueError('Mapping sentinel is missing or not final')
    report=dict(entries=len(left),ordered_lists_equal=True,
        ordered_pairs_sha256=hashlib.sha256(json.dumps(left).encode()).hexdigest(),
        behavior='Iterate the original mapping array, excluding its terminal sentinel')
    (ROOT/'logs/registration-equivalence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Verified {len(left)} identical ordered function registrations')

if __name__=='__main__':
    verify()
