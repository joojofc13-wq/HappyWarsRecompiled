"""Copy one exact generated leaf function for an isolated native translation test.

Test-only synthetic memory inputs are passed to real translated game code.
This is not a game executable or a gameplay simulation.
"""
import hashlib
import json
from pathlib import Path
from analyze import ROOT

def extract_function(marker):
    matches=[]
    for path in (ROOT/'generated/default').glob('happywars_recomp.*.cpp'):
        source=path.read_text(encoding='utf-8')
        if marker not in source:
            continue
        start=source.index(marker)
        begin=source.index('{',start)
        depth=1
        cursor=begin+1
        while depth:
            depth+=(source[cursor]=='{')-(source[cursor]=='}')
            cursor+=1
        body=source[start:cursor]
        matches.append((path,body))
    if len(matches)!=1:
        raise ValueError(f'Expected exactly one generated leaf, found {len(matches)}')
    return matches[0]

def prepare():
    path,body=extract_function('DEFINE_REX_FUNC(sub_82E0AE08) {')
    output=ROOT/'private/tests/translated_leaf.cpp'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('#include "generated/default/happywars_pch.h"\n'+body+'\n',encoding='utf-8')
    report=dict(guest_function='0x82E0AE08',source=str(path.relative_to(ROOT)),
        extracted_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        edited_instructions=False,scope='Isolated native translation test; no gameplay')
    (ROOT/'logs/translated-leaf-source.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    prepare()
