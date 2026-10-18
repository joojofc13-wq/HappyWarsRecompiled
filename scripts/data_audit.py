"""Inventory real exported JSON tables without inventing reward probabilities."""
import collections
import hashlib
import json
import re
from pathlib import Path
from analyze import ROOT


def read_json_export(path):
    raw=Path(path).read_bytes()
    try:
        text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text=raw.decode('cp932')
    # Protect quoted strings, remove only comments outside them.
    tokens=re.compile(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*.*?\*/',re.S)
    text=tokens.sub(lambda m:m.group() if m.group().startswith('"') else '',text)
    return json.loads(text)


if __name__=='__main__':
    root=ROOT/'private/decoded/media/json'
    tables=[]
    failures=[]
    parsed={}
    for path in sorted(root.rglob('*.json')):
        relative=path.relative_to(root).as_posix()
        try:
            data=read_json_export(path)
            parsed[relative]=data
            for name,container in data.items():
                tables.append(dict(path=relative,root=name,
                    sections={k:len(v) if isinstance(v,(list,dict)) else None for k,v in container.items()}
                        if isinstance(container,dict) else {'array_length':len(container)}))
        except (ValueError,UnicodeError) as error:
            failures.append(dict(path=relative,error=str(error)))
    item_tables={}
    for name in ('item/ItemSeedParam.json','item/ItemSeedParamDLC.json'):
        if name in parsed:
            for container in parsed[name].values():
                for section,rows in container.items():
                    if section=='itemSeedParam_':
                        item_tables.update({k:v for k,v in rows.items() if not k.startswith('_')})
    spinner=parsed.get('item/ItemSpinner.json',{})
    summary=dict(parsed_files=len(parsed),tables=tables,failures=failures,
        item_definition_count=len(item_tables),
        item_fields=sorted({key for item in item_tables.values() for key in item}),
        item_classes={job:sum(bool(row.get(job+'Equip')) for row in item_tables.values())
                      for job in ('Warrior','Mage','Cleric')},
        spinner_sections={k:len(v) for top in spinner.values() for k,v in top.items()},
        limitations=['Tables establish available data, not the behavior of the original server',
            'No local reward draws, unlock patches or game inventory objects are produced'])
    (ROOT/'logs/data-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('tables','item_fields')},indent=2))
