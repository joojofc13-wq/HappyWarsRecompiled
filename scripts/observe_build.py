"""Write an honest file-based build snapshot without inferring gameplay success."""
import datetime
import json
from analyze import ROOT

if __name__=='__main__':
    folder=ROOT/'build/game'
    exe=folder/'HappyWars.exe'
    log=ROOT/'logs/game-build.log'
    text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
    objects=list((folder/'CMakeFiles/happywars_recomp.dir/generated/default').glob('*.obj'))
    result=dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        generated_cpp_files=len(list((ROOT/'generated/default').glob('*.cpp'))),
        generated_cpp_objects_present=len(objects),happywars_exe_present=exe.exists(),
        compile_failure_marker='FAILED:' in text,tail=text.splitlines()[-5:],
        runtime_tested=False,menu_tested=False,skirmish_tested=False,
        limitation='File observation only; object existence does not certify a completed build or runtime behavior')
    (ROOT/'logs/build-observation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
