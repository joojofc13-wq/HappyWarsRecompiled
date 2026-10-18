"""Copy the exact SDK translation of a real this-adjusting thunk for a native regression test."""
import hashlib
import json
from analyze import ROOT
from prepare_translation_test import extract_function

if __name__=='__main__':
    path,body=extract_function('DEFINE_REX_FUNC(sub_830697E8) {')
    output=ROOT/'private/tests/translated_thunk.cpp'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('#include "generated/default/happywars_pch.h"\nREX_EXTERN(sub_83069388);\n'+body+'\n',encoding='utf-8')
    constant_path,constant_body=extract_function('DEFINE_REX_FUNC(sub_82D1D0A0) {')
    with output.open('a',encoding='utf-8') as stream:
        stream.write('REX_EXTERN(sub_82D1B380);\n'+constant_body+'\n')
    report=dict(guest_function='0x830697E8',source=str(path.relative_to(ROOT)),
        extracted_body_sha256=hashlib.sha256(body.encode()).hexdigest(),edited_instructions=False,
        scope='Native instruction-semantics test; destination is a fixture observer, not gameplay')
    (ROOT/'logs/translated-thunk-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    path,body=extract_function('DEFINE_REX_FUNC(sub_82C3DD30) {')
    (ROOT/'private/tests/translated_vcall4.cpp').write_text(
        '#include "generated/default/happywars_pch.h"\n'+body+'\n',encoding='utf-8')
    report=dict(guest_function='0x82C3DD30',source=str(path.relative_to(ROOT)),
        extracted_body_sha256=hashlib.sha256(body.encode()).hexdigest(),edited_instructions=False,
        scope='Original four-instruction virtual thunk; synthetic test memory and observer only')
    (ROOT/'logs/translated-vcall4-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    path,body=extract_function('DEFINE_REX_FUNC(sub_8327D108) {')
    (ROOT/'private/tests/translated_virtual_adapter.cpp').write_text(
        '#include "generated/default/happywars_pch.h"\n'+body+'\n',encoding='utf-8')
    report=dict(guest_function='0x8327D108',source=str(path.relative_to(ROOT)),
        extracted_body_sha256=hashlib.sha256(body.encode()).hexdigest(),edited_instructions=False,
        scope='Native virtual-tail-call instruction test using sparse fixture memory and observer destination; no gameplay')
    (ROOT/'logs/translated-virtual-adapter-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
