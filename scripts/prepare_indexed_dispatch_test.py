"""Extract original indexed dispatcher for an isolated native semantics test."""
import hashlib
import json
from analyze import ROOT
from prepare_translation_test import extract_function

if __name__=='__main__':
    path,body=extract_function('DEFINE_REX_FUNC(sub_82B67950) {')
    destination=ROOT/'private/tests/translated_indexed_dispatch.cpp'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text('#include "generated/default/happywars_pch.h"\n'+body+'\n',encoding='utf-8')
    report=dict(guest_function='0x82B67950',source=str(path.relative_to(ROOT)),
        extracted_body_sha256=hashlib.sha256(body.encode()).hexdigest(),edited_instructions=False,
        scope='Original translated indexed dispatch, synthetic memory and observer destinations only; no gameplay')
    (ROOT/'logs/translated-indexed-dispatch-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
