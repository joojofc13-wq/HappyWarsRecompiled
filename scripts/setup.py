"""Install pinned SDK/build tools locally; use a supplied LLVM and MSVC SDK.

Example: py scripts/setup.py --llvm-bin C:/llvm/bin --msvc C:/portable-msvc
The MSVC path must contain VC/Tools/MSVC and Windows Kits/10.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]


def pinned_clone(repository,commit,destination):
    if not destination.exists():
        subprocess.run(['git','clone','--no-checkout',repository,str(destination)],check=True)
    current=subprocess.check_output(['git','-C',str(destination),'rev-parse','HEAD'],text=True).strip()
    if current!=commit:
        subprocess.run(['git','-C',str(destination),'fetch','origin',commit],check=True)
        subprocess.run(['git','-C',str(destination),'checkout','--detach',commit],check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--llvm-bin',type=pathlib.Path,required=True)
    p.add_argument('--msvc',type=pathlib.Path,required=True)
    p.add_argument('--diagnostic-source',action='store_true')
    a=p.parse_args()
    lock=json.loads((ROOT/'config/upstream-lock.json').read_text())
    tools=ROOT/'tools'
    tools.mkdir(exist_ok=True)
    archive=tools/'sdk.zip'
    sdk=tools/'sdk'
    if not archive.exists():
        urllib.request.urlretrieve(lock['sdk']['url'],archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=lock['sdk']['sha256']:
        raise SystemExit('SDK archive SHA-256 mismatch')
    if not (sdk/'win-amd64/bin/rexglue.exe').exists():
        with zipfile.ZipFile(archive) as z:
            z.extractall(sdk)
    pytools=tools/'python'
    subprocess.run([sys.executable,'-m','pip','install','--target',str(pytools),
        *[f'{name}=={version}' for name,version in lock['python_packages'].items()]],check=True)
    compiler=sorted(a.llvm_bin.glob('clang-[0-9]*.exe'))
    if not compiler:
        raise SystemExit('Real clang-<major>.exe not found in --llvm-bin')
    link_bin=tools/'native-bin'
    link_bin.mkdir(exist_ok=True)
    if (a.llvm_bin/'lld-link.exe').exists():
        linker=a.llvm_bin
    elif (a.llvm_bin/'ld.lld.exe').exists():
        shutil.copy2(a.llvm_bin/'ld.lld.exe',link_bin/'lld-link.exe')
        linker=link_bin
    else:
        raise SystemExit('LLVM linker missing')
    if not (a.msvc/'VC/Tools/MSVC').is_dir() or not (a.msvc/'Windows Kits/10/Include').is_dir():
        raise SystemExit('Incomplete MSVC/Windows SDK layout')
    settings=dict(clang=str(compiler[-1].resolve()),msvc=str(a.msvc.resolve()),
        cmake=str(pytools/'cmake/data/bin/cmake.exe'),
        ninja=str(next(pytools.rglob('ninja.exe'))),sdk=str((sdk/'win-amd64').resolve()),
        linker_bin=str(linker.resolve()))
    if a.diagnostic_source:
        source=tools/'upstream/rexglue'
        pinned_clone(lock['sources']['rexglue']['repository'],lock['sources']['rexglue']['commit'],source)
        subprocess.run(['git','-C',str(source),'submodule','update','--init','--depth','1',
            'thirdparty/cli11','thirdparty/inja','thirdparty/tomlplusplus','thirdparty/simde','thirdparty/xxHash'],check=True)
        for name in ('rexglue-gap-cleanup.patch','rexglue-indirect-tail-branches.patch'):
            patch=ROOT/'patches'/name
            applied=subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],capture_output=True).returncode==0
            if not applied:
                subprocess.run(['git','-C',str(source),'apply',str(patch)],check=True)
        settings['rexglue_source']=str(source.resolve())
    (ROOT/'config/local-tools.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
    print('Local build settings written. Run py scripts/build.py')
