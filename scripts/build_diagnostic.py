"""Build and test the patched recompiler against the pinned binary runtime."""
import argparse
import json
import pathlib
from build import ROOT,environment,run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--configure-only',action='store_true')
    a=p.parse_args()
    settings_path=ROOT/'config/local-tools.json'
    settings=json.loads(settings_path.read_text())
    env=environment(settings)
    source=pathlib.Path(settings.get('rexglue_source',ROOT/'tools/upstream/rexglue'))
    build=ROOT/'build/sdk-diagnostic'
    run([settings['cmake'],'-S',ROOT/'tools/diagnostic','-B',build,'-G','Ninja',
        '-DREXGLUE_ROOT='+str(source),'-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_CXX_COMPILER='+settings['clang'],
        '-DCMAKE_CXX_FLAGS=--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll',
        '-DCMAKE_MAKE_PROGRAM='+settings['ninja'],'-DCMAKE_PREFIX_PATH='+settings['sdk']],
        'diagnostic-wrapper-configure.log',env)
    if a.configure_only:
        raise SystemExit(0)
    run([settings['cmake'],'--build',build,'--parallel',a.jobs],'diagnostic-wrapper-build.log',env)
    run([pathlib.Path(settings['cmake']).with_name('ctest.exe'),'--test-dir',build,'--output-on-failure'],
        'diagnostic-wrapper-tests.log',env)
    settings['codegen_tool']=str(build/'cli/rexglue.exe')
    settings_path.write_text(json.dumps(settings,indent=2),encoding='utf-8')
