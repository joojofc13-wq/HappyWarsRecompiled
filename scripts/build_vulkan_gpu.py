"""Build the Vulkan GPU and presentation plugin against the pinned Windows SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from build import ROOT, environment


def build(settings, jobs=2):
    source=Path(settings['rexglue_source']).resolve()
    locked=json.loads((ROOT/'config/upstream-lock.json').read_text())['sdk']['commit']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if revision != locked:
        raise RuntimeError('The Vulkan plugin requires the pinned ReXGlue source revision: '+locked)
    patches=[ROOT/'patches'/name for name in (
        'rexglue-vulkan-rendering-attachments.patch',
        'rexglue-vulkan-render-diagnostics.patch')]
    for patch in patches:
        # Preserve existing SDK edits. Recognize an applied patch before trying
        # to apply it, and reject conflicting changes without resetting files.
        command=['git','apply','--check']
        if subprocess.run([*command,'--reverse',str(patch)],cwd=source,
                          capture_output=True).returncode == 0:
            continue
        result=subprocess.run([*command,str(patch)],cwd=source,
                              capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError('Cannot apply '+patch.name+': '+result.stderr.strip())
        subprocess.run(['git','apply',str(patch)],cwd=source,check=True)
    dependencies=('vulkan-headers','vulkan-memory-allocator','spirv-headers','spirv-tools','glslang')
    missing=[name for name in dependencies if not (source/'thirdparty'/name/'CMakeLists.txt').is_file()]
    if missing:
        subprocess.run(['git','submodule','update','--init','--depth','1','--jobs',str(jobs),'--',
                        *('thirdparty/'+name for name in missing)],cwd=source,check=True)
    for name in dependencies:
        relative='thirdparty/'+name
        expected=subprocess.check_output(['git','rev-parse','HEAD:'+relative],cwd=source,text=True).strip()
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source/relative,text=True).strip()
        if actual != expected:
            raise RuntimeError('Unexpected Vulkan dependency revision: '+relative)

    # Generate a standalone project without changing the SDK's exported targets.
    project=ROOT/'private/vulkan-plugin-source'
    project.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'tools/vulkan_gpu/CMakeLists.txt',project/'CMakeLists.txt')
    graphics=source/'src/graphics'
    manifest=(graphics/'CMakeLists.txt').read_text()
    alias='add_library(rex::gpu-xenos ALIAS rexgpu-xenos)'
    if manifest.count(alias) != 1:
        raise RuntimeError('Unexpected GPU target layout in the pinned SDK source')
    manifest=manifest.replace(alias,'')
    manifest=re.sub(r'^(\s+)([\w./-]+\.cpp)\s*$',
        lambda match:match[1]+'"'+(graphics/match[2]).as_posix()+'"',manifest,flags=re.MULTILINE)
    (project/'gpu-target.cmake').write_text(manifest,encoding='utf-8',newline='\n')

    output=ROOT/'build/gpu-vulkan'
    flags='--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll'
    configure=[settings['cmake'],'-S',str(project),'-B',str(output),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER='+settings['clang'],
        '-DCMAKE_CXX_COMPILER='+settings['clang'],'-DCMAKE_C_FLAGS='+flags,
        '-DCMAKE_CXX_FLAGS='+flags,'-DCMAKE_MAKE_PROGRAM='+settings['ninja'],
        '-DCMAKE_PREFIX_PATH='+settings['sdk'],'-DREXGLUE_ROOT='+str(source)]
    env=environment(settings)
    (ROOT/'logs').mkdir(exist_ok=True)
    for command,name in [(configure,'gpu-vulkan-configure.log'),
                         ([settings['cmake'],'--build',str(output),'--parallel',str(jobs)],'gpu-vulkan-build.log')]:
        with (ROOT/'logs'/name).open('w',encoding='utf-8') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError((ROOT/'logs'/name).read_text(errors='replace')[-8000:])
    binary=output/'rexgpu-xenos.dll'
    (output/'vulkan-build-info.json').write_text(json.dumps(dict(
        source_revision=revision,backend='vulkan',
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
