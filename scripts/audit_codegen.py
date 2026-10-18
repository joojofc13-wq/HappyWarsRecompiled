"""Count generated files and explicit fatal/unimplemented placeholders."""
import collections
import json
import re
from analyze import ROOT

if __name__=='__main__':
    cpp=list((ROOT/'generated/default').glob('*.cpp'))
    counters=collections.Counter()
    findings=[]
    for path in cpp:
        source=path.read_text(encoding='utf-8')
        counters['function_definitions']+=len(re.findall(r'^DEFINE_REX_FUNC\(',source,re.M))
        for number,line in enumerate(source.splitlines(),1):
            if re.search(r'REX_FATAL\(|REX_UNIMPLEMENTED|PPC_UNIMPLEMENTED|ERROR:.*(?:branch|instruction)',line,re.I):
                findings.append(dict(path=path.name,line=number,text=line.strip()[:240]))
    report=dict(cpp_files=len(cpp),cpp_bytes=sum(p.stat().st_size for p in cpp),
        **counters,explicit_placeholders=findings,
        limitations=['A zero placeholder count is not proof of correct translation or gameplay'])
    (ROOT/'logs/codegen-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='explicit_placeholders'},indent=2))
    print(f'Explicit placeholders: {len(findings)}')
    raise SystemExit(1 if findings else 0)
