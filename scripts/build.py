"""Configure Clang with the MSVC ABI and build the game or independent tests."""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]


def run(command, log, env):
    print(f'{log}: running',flush=True)
    with (ROOT/'logs'/log).open('w',encoding='utf-8') as output:
        output.write('Command: '+subprocess.list2cmdline([str(x) for x in command])+'\n')
        output.flush()
        process=subprocess.Popen([str(x) for x in command],cwd=ROOT,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
        for line in process.stdout:
            output.write(line); output.flush()
            if re.match(r'^\[\d+/\d+\]',line): print(line.rstrip(),flush=True)
        returncode=process.wait()
    if returncode:
        print((ROOT/'logs'/log).read_text(encoding='utf-8',errors='replace')[-8000:])
        raise SystemExit(returncode)
    print(f'{log}: OK',flush=True)


def environment(settings):
    env=os.environ.copy()
    msvc=pathlib.Path(settings['msvc'])
    vc=next((msvc/'VC/Tools/MSVC').iterdir())
    sdk=msvc/'Windows Kits/10'
    version=sorted((sdk/'Include').iterdir())[-1].name
    env['INCLUDE']=';'.join(str(p) for p in [vc/'include',sdk/'Include'/version/'ucrt',
        sdk/'Include'/version/'shared',sdk/'Include'/version/'um',sdk/'Include'/version/'winrt'])
    env['LIB']=';'.join(str(p) for p in [vc/'lib/x64',sdk/'Lib'/version/'ucrt/x64',sdk/'Lib'/version/'um/x64'])
    crt=next((msvc/'VC/Redist/MSVC').glob('*/x64/Microsoft.VC143.CRT'),None)
    env['PATH']=os.pathsep.join(([str(crt)] if crt else [])+[settings.get('linker_bin',''),str(vc/'bin/Hostx64/x64'),str(sdk/'bin'/version/'x64'),
        str(pathlib.Path(settings['clang']).parent),str(pathlib.Path(settings['ninja']).parent),
        str(pathlib.Path(settings['sdk'])/'bin'),env['PATH']])
    return env


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--settings',type=pathlib.Path,default=ROOT/'config/local-tools.json')
    p.add_argument('--game',action='store_true',help='Build actual recompiled game; default is storage tests')
    p.add_argument('--jobs',type=int,default=2)
    p.add_argument('--opt-level',choices=('0','1','2','3'),help='Optimization level for translated game code')
    p.add_argument('--translation-test',action='store_true')
    p.add_argument('--diagnostics',action='store_true',help='Validate codegen and report missing entries without compiling or launching the game')
    a=p.parse_args()
    if a.diagnostics:
        a.game=True
    settings=json.loads(a.settings.read_text())
    if a.game and not a.diagnostics:
        from prepare_fps_font import prepare
        prepare(source=settings.get('fps_font_source'))
    env=environment(settings)
    label='game' if a.game else 'translation' if a.translation_test else 'storage'
    build=ROOT/'build'/label
    # clang-<major>.exe is the real compiler, not LLVM-MinGW's target wrapper.
    flags='--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll'
    command=[settings['cmake'],'-S',ROOT,'-B',build,'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER='+settings['clang'],
        '-DCMAKE_CXX_FLAGS='+flags,'-DCMAKE_MAKE_PROGRAM='+settings['ninja'],
        '-DCMAKE_PREFIX_PATH='+settings['sdk'],
        '-DPython3_EXECUTABLE='+__import__('sys').executable,
        '-DHAPPYWARS_BUILD_GAME='+('ON' if a.game else 'OFF')]
    command.append('-DHAPPYWARS_TEST_TRANSLATION='+('ON' if a.translation_test else 'OFF'))
    if a.game and settings.get('codegen_tool'):
        command.append('-DREXGLUE_CODEGEN_EXECUTABLE='+settings['codegen_tool'])
    if a.game and a.opt_level is not None:
        command.append('-DHAPPYWARS_RECOMP_OPT_LEVEL='+a.opt_level)
    run(command,label+'-configure.log',env)
    command=[settings['cmake'],'--build',build,'--parallel',a.jobs]
    if a.diagnostics:
        command.extend(['--target','happywars_diagnostics'])
    run(command,'entry-diagnostics-build.log' if a.diagnostics else label+'-build.log',env)
    if not a.game:
        ctest=pathlib.Path(settings['cmake']).with_name('ctest.exe')
        run([ctest,'--test-dir',build,'--output-on-failure'],label+'-tests.log',env)
