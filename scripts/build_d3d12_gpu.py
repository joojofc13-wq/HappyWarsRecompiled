"""Build the D3D12 GPU and presentation plugin against the pinned Windows SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from build import ROOT, environment

PATCH_NAMES = (
    'rexglue-dred-allocations.patch', 'rexglue-queue-fence-order.patch',
    'rexglue-gpu-validation.patch', 'rexglue-present-loss-diagnostics.patch',
    'rexglue-submission-lifetime.patch', 'rexglue-frame-overlap-diagnostics.patch',
    'rexglue-dred-draw-context.patch')


def build(settings, jobs=2):
    source=Path(settings['rexglue_source']).resolve()
    locked=json.loads((ROOT/'config/upstream-lock.json').read_text())['sdk']['commit']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if revision != locked:
        raise RuntimeError('The D3D12 plugin requires the pinned ReXGlue source revision: '+locked)
    patches=[ROOT/'patches'/name for name in PATCH_NAMES]
    # Reconstruct the entire patch stack before changing the checkout. This
    # accepts either pristine files or this exact stack, preserving other edits.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        prepared=Path(temporary)
        names=set()
        for patch in patches:
            names.update(line[6:] for line in patch.read_text().splitlines() if line.startswith('+++ b/'))
        originals={}
        for name in names:
            data=subprocess.check_output(['git','show',locked+':'+name],cwd=source)
            originals[name]=data
            target=prepared/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
        for patch in patches:
            subprocess.run(['git','apply',str(patch)],cwd=prepared,check=True)
        for name in names:
            actual=(source/name).read_text()
            if actual not in (originals[name].decode().replace('\r\n','\n'),(prepared/name).read_text()):
                raise RuntimeError('SDK has conflicting edits: '+name)
        for name in names:
            if (source/name).read_text() != (prepared/name).read_text():
                (source/name).write_bytes((prepared/name).read_bytes())

    # Generate a standalone project without changing the SDK's exported targets.
    project=ROOT/'private/gpu-diagnostic-source'
    project.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'tools/d3d12_gpu/CMakeLists.txt',project/'CMakeLists.txt')
    graphics=source/'src/graphics'
    manifest=(graphics/'CMakeLists.txt').read_text()
    alias='add_library(rex::gpu-xenos ALIAS rexgpu-xenos)'
    if manifest.count(alias) != 1:
        raise RuntimeError('Unexpected GPU target layout in the pinned SDK source')
    manifest=manifest.replace(alias,'')
    manifest=re.sub(r'^(\s+)([\w./-]+\.cpp)\s*$',
        lambda match:match[1]+'"'+(graphics/match[2]).as_posix()+'"',manifest,flags=re.MULTILINE)
    (project/'gpu-target.cmake').write_text(manifest,encoding='utf-8',newline='\n')

    output=ROOT/'build/gpu-diagnostic'
    flags='--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll'
    configure=[settings['cmake'],'-S',str(project),'-B',str(output),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER='+settings['clang'],
        '-DCMAKE_CXX_COMPILER='+settings['clang'],'-DCMAKE_C_FLAGS='+flags,
        '-DCMAKE_CXX_FLAGS='+flags,'-DCMAKE_MAKE_PROGRAM='+settings['ninja'],
        '-DCMAKE_PREFIX_PATH='+settings['sdk'],'-DREXGLUE_ROOT='+str(source)]
    env=environment(settings)
    (ROOT/'logs').mkdir(exist_ok=True)
    for command,name in [(configure,'gpu-diagnostic-configure.log'),
                         ([settings['cmake'],'--build',str(output),'--parallel',str(jobs)],'gpu-diagnostic-build.log')]:
        with (ROOT/'logs'/name).open('w',encoding='utf-8') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError((ROOT/'logs'/name).read_text(errors='replace')[-8000:])
    binary=output/'rexgpu-xenos.dll'
    (output/'d3d12-build-info.json').write_text(json.dumps(dict(
        source_revision=revision,backend='d3d12',
        patches={patch.name:hashlib.sha256(patch.read_bytes()).hexdigest() for patch in patches},
        plugin_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),indent=2)+'\n')
    return binary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,default=ROOT/'config/local-tools.json')
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    if args.jobs < 1:parser.error('--jobs must be positive')
    print(build(json.loads(args.settings.read_text()),args.jobs))
