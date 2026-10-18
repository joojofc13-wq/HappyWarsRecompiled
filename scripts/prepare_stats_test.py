"""Extract the original stats consumers and register save/restore helpers."""
import hashlib
import json
from analyze import ROOT
from prepare_translation_test import extract_function

def prepare():
    bodies=[]
    report=[]
    for name in ('__savegprlr_29','__restgprlr_29','sub_82AAA650','sub_82AAA518'):
        source,body=extract_function('DEFINE_REX_FUNC('+name+') {')
        bodies.append(body)
        report.append(dict(function=name,source=str(source.relative_to(ROOT)),
                           sha256=hashlib.sha256(body.encode()).hexdigest()))
    (ROOT/'private/tests/translated_stats.cpp').write_text(
        '#include "generated/default/happywars_pch.h"\n'+'\n'.join(bodies)+'\n',encoding='utf-8')
    (ROOT/'logs/translated-stats-source.json').write_text(
        json.dumps(dict(edited_instructions=False,functions=report),indent=2))
    print('Prepared exact original stats consumers and register helpers')

if __name__=='__main__':
    prepare()
