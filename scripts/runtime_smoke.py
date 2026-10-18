"""Bounded offline bring-up of the actual native executable; no gameplay claims."""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import time
from analyze import ROOT

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds',type=int,default=20)
    p.add_argument('--visible',action='store_true',help='Run the normal interactive window during the bounded test')
    p.add_argument('--keyboard',action='store_true',help='Enable SDK keyboard controller: Enter=start, Space=A, WASD=left stick')
    p.add_argument('--log-level',choices=('info','debug','trace'),default='info')
    a=p.parse_args()
    settings=json.loads((ROOT/'config/local-tools.json').read_text())
    exe=ROOT/'build/game/HappyWars.exe'
    if not exe.exists():
        raise SystemExit('Native game executable is not built')
    command=[str(exe),'--headless','--log_file='+str(ROOT/'logs/runtime-smoke.log'),
        '--game_data_root='+str(ROOT/'private/game'),'--user_data_root='+str(ROOT/'private/smoke-user'),
        '--cache_root='+str(ROOT/'private/smoke-cache'),'--window_width=1280','--window_height=720',
        '--log_level='+a.log_level]
    if a.visible:
        command.remove('--headless')
    if a.keyboard:
        command.append('--mnk_mode=true')
    env=os.environ.copy()
    env['PATH']=str(__import__('pathlib').Path(settings['sdk'])/'bin')+os.pathsep+env['PATH']
    started=time.monotonic()
    previous_log=ROOT/'logs/runtime-smoke.log'
    if previous_log.exists():
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
        previous_log.rename(ROOT/'logs'/f'runtime-smoke-prior-{stamp}.log')
    result=dict(command=command,started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        network_mode='Guest socket/connect/send and HTTP entry points overridden to explicit offline errors',
        menu_confirmed=False,skirmish_confirmed=False)
    with (ROOT/'logs/runtime-smoke-stdout.log').open('w',encoding='utf-8') as output:
        process=subprocess.Popen(command,cwd=exe.parent,env=env,stdout=output,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        result['pid']=process.pid
        try:
            result['exit_code']=process.wait(timeout=a.seconds)
            result['terminated_after_timeout']=False
        except subprocess.TimeoutExpired:
            process.terminate()
            result['exit_code']=process.wait()
            result['terminated_after_timeout']=True
    result['elapsed_seconds']=time.monotonic()-started
    text=previous_log.read_text(encoding='utf-8',errors='replace') if previous_log.exists() else ''
    targets=re.findall(r'unregistered function at guest address (0x[0-9A-Fa-f]+)',text)
    result['unregistered_targets']=list(dict.fromkeys(targets))
    result['fatal_log_lines']=[line for line in text.splitlines() if '[FATAL]' in line][-10:]
    result['runtime_milestones_logged']=dict(
        function_table='Function table initialized' in text,
        input='SDL input driver initialized successfully' in text,
        d3d12='Direct3D 12 device and OS features' in text,
        audio_endpoint='audio endpoint' in text)
    (ROOT/'logs/runtime-smoke-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('exe_sha256','exit_code','terminated_after_timeout','elapsed_seconds',
        'unregistered_targets','runtime_milestones_logged','menu_confirmed','skirmish_confirmed')},indent=2))
    if not result['terminated_after_timeout'] and result['exit_code']!=0:
        raise SystemExit(1)
