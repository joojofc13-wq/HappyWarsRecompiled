"""Find missing local labels in all generated functions before native compilation."""
import json
import re
from analyze import ROOT

if __name__=='__main__':
    findings=[]
    total=0
    for path in (ROOT/'generated/default').glob('happywars_recomp.*.cpp'):
        source=path.read_text(encoding='utf-8')
        functions=list(re.finditer(r'^DEFINE_REX_FUNC\((\w+)\) \{',source,re.M))
        total+=len(functions)
        for i,match in enumerate(functions):
            end=functions[i+1].start() if i+1<len(functions) else len(source)
            body=source[match.end():end]
            declared=set(re.findall(r'^(loc_[0-9A-Fa-f]+):',body,re.M))
            referenced=set(re.findall(r'\bgoto (loc_[0-9A-Fa-f]+)\s*;',body))
            if referenced-declared:
                findings.append(dict(source=path.name,function=match.group(1),
                    missing=sorted(referenced-declared)))
    result=dict(functions_checked=total,functions_with_missing_labels=len(findings),findings=findings)
    (ROOT/'logs/label-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(1 if findings else 0)
