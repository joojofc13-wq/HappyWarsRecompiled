"""Local MSVC/Windows SDK extraction through pinned msvc-wine and Microsoft manifests."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from setup import ROOT,pinned_clone

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,default=ROOT/'tools/msvc')
    p.add_argument('--accept-license',action='store_true',help='Accept the Microsoft license presented by vsdownload')
    p.add_argument('--plan',action='store_true',help='Print command without installing')
    a=p.parse_args()
    lock=json.loads((ROOT/'config/upstream-lock.json').read_text())
    source=ROOT/'tools/upstream/msvc-wine'
    command=[sys.executable,str(source/'vsdownload.py'),'--major','17',
        '--dest',str(a.destination.resolve()),'--cache',str(ROOT/'tools/msvc-cache'),
        '--manifest',lock['msvc_manifest']['url'],
        '--with-workload','no','--with-msvc','yes','--with-sdk','yes','--with-asan','no',
        '--with-atl','no','--with-dia','no','--with-msbuild','no','--with-devcmd','no',
        '--architecture','x64','--host-arch','x64']
    if a.accept_license:
        command.append('--accept-license')
    print(subprocess.list2cmdline(command),flush=True)
    if a.plan:
        raise SystemExit(0)
    pinned_clone(lock['sources']['msvc-wine']['repository'],lock['sources']['msvc-wine']['commit'],source)
    patch=ROOT/'patches/msvc-wine-required-sdk-only.patch'
    applied=subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],capture_output=True).returncode==0
    if not applied:
        subprocess.run(['git','-C',str(source),'apply',str(patch)],check=True)
    import urllib.request
    manifest=urllib.request.urlopen(lock['msvc_manifest']['url']).read()
    if hashlib.sha256(manifest).hexdigest()!=lock['msvc_manifest']['sha256']:
        raise SystemExit('Microsoft manifest differs from pinned SHA-256')
    with (ROOT/'logs/msvc-install.log').open('w',encoding='utf-8') as log:
        result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    raise SystemExit(result.returncode)
