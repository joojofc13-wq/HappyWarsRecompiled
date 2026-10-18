"""Run pinned SDK codegen and record its real exit status; no automatic --force."""
import argparse
import datetime
import json
import os
import hashlib
import subprocess
import time
from pathlib import Path
from analyze import ROOT,xex_report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',type=Path)
    p.add_argument('--timeout',type=int,default=3600)
    p.add_argument('--tool',type=Path,help='Explicit diagnostic CLI executable; runtime still comes from --sdk')
    p.add_argument('--label',default='codegen')
    p.add_argument('--regenerate',action='store_true',help='Ignore cache stamp after changing the CLI; does not force past validation errors')
    a=p.parse_args()
    sdk=(a.sdk or Path(json.loads((ROOT/'config/local-tools.json').read_text())['sdk'])).resolve()
    xex=xex_report(ROOT/'private/game/Default.xex')
    if xex['execution']['title_id']!='0x58410ae9':
        raise SystemExit('Unexpected title ID; refusing to generate a different game')
    if not a.label.replace('-','').isalnum():
        raise SystemExit('Invalid log label')
    settings_path=ROOT/'config/local-tools.json'
    settings=json.loads(settings_path.read_text()) if settings_path.exists() else {}
    tool=a.tool.resolve() if a.tool else Path(settings.get('codegen_tool',sdk/'bin/rexglue.exe'))
    command=[str(tool),'--log-file',f'logs/{a.label}-detail.log',
             'codegen',str(ROOT/'happywars_manifest.toml')]
    if a.regenerate:
        command.append('--ignore-stamp')
    start=time.monotonic()
    result=dict(start=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=command,
                xex_sha256=xex['sha256'],tool_sha256=hashlib.sha256(tool.read_bytes()).hexdigest(),
                forced=False,cache_ignored=a.regenerate)
    env=os.environ.copy()
    env['PATH']=str(sdk/'bin')+os.pathsep+env['PATH']
    with (ROOT/'logs'/f'{a.label}.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        print(f'Codegen PID {process.pid}',flush=True)
        try:
            result['exit_code']=process.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait()
            result.update(exit_code=process.returncode,timed_out=True)
    result['elapsed_seconds']=time.monotonic()-start
    result['generated_cpp_count']=len(list((ROOT/'generated/default').glob('*.cpp')))
    (ROOT/'logs'/f'{a.label}-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('exit_code','elapsed_seconds','generated_cpp_count','forced')}))
    raise SystemExit(0 if result['exit_code']==0 else 1)
