"""Create a source-only handoff; never include game data, tools or saves."""
import hashlib
import json
import zipfile
from pathlib import Path
from analyze import ROOT

def package():
    files=[]
    for name in ('README.md','STATUS.md','CMakeLists.txt','CMakePresets.json','happywars_manifest.toml','.gitignore'):
        files.append(ROOT/name)
    for folder in ('scripts','src','include','runtime','tests','docs','patches'):
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend([ROOT/'config/upstream-lock.json',ROOT/'config/function-boundaries.toml',ROOT/'config/verified-thunks.toml',
                  ROOT/'generated/rexglue.cmake',ROOT/'tools/Extract-STFS.ps1',
                  ROOT/'tools/Extract-STFS.LICENSE',ROOT/'tools/ReXGlue.LICENSE'])
    files.extend(p for p in (ROOT/'tools/diagnostic').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    evidence=('tool-tests.log','translation-tests.log','sdk-diagnostic-tests.log',
              'corrected-codegen-result.json','codegen-audit.json','translated-leaf-source.json',
              'build-observation.json','pdata-codegen-result.json','label-audit.json',
              'native-artifact.json','runtime-smoke-result.json','boot-target-codegen-result.json',
              'gpu-boot-codegen-result.json','verified-blr-callbacks.json','runtime-smoke.log',
              'registration-equivalence.json','verified-thunk-boundaries.json','translated-thunk-source.json',
              'tail-thunks-result.json','main-boot-result.json','virtual-adapters-result.json',
              'virtual-adapters-disassembly.log','virtual-thunks-result.json',
              'four-instruction-adapters-disassembly.log','translated-virtual-adapter-source.json',
              'translated-indexed-dispatch-source.json','indexed-dispatch-disassembly.log',
              'translated-vcall4-source.json','translation-validation.json','bounded-vcalls-result.json')
    files.extend(ROOT/'logs'/name for name in evidence if (ROOT/'logs'/name).is_file())
    archive=ROOT.parent/'HappyWarsRecompiled-fontes.zip'
    manifest=[]
    forbidden={'.exe','.dll','.xex','.xexp','.lib','.obj','.pdb','.sqlite','.bin'}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as output:
        for file in sorted(set(files)):
            relative=file.relative_to(ROOT)
            if relative.parts[0] in ('private','saves','build') or file.suffix.lower() in forbidden or file.name=='local-tools.json':
                raise ValueError(f'Forbidden source-package member: {file}')
            data=file.read_bytes()
            output.writestr('HappyWarsRecompiled/'+relative.as_posix(),data)
            manifest.append(dict(path=relative.as_posix(),size=len(data),sha256=hashlib.sha256(data).hexdigest()))
        output.writestr('HappyWarsRecompiled/SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive) as verification:
        if verification.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
    report=dict(path=archive.name,size=archive.stat().st_size,files=len(manifest),
                sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                contains_proprietary_assets=False,contains_game_binaries=False)
    (ROOT.parent/'HappyWarsRecompiled-fontes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    package()
