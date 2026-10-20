"""Package the Windows builder with audited project sources, never game files."""
import hashlib
import argparse
import json
import shutil
from pathlib import Path
import subprocess
import sys
import zipfile
from audit_publication import audit

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    audit()
    import PyInstaller
    required=json.loads((ROOT/'config/upstream-lock.json').read_text())['builder_packages']['pyinstaller']
    if PyInstaller.__version__ != required:
        raise SystemExit('Install the pinned PyInstaller version: '+required)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='0.1')
    parser.add_argument('--gpu-payload', type=Path, help='Verified patched D3D12 plugin folder')
    parser.add_argument('--output', type=Path, default=ROOT/'build/builder-release')
    args = parser.parse_args()
    output = args.output.resolve()
    payload = args.gpu_payload.resolve() if args.gpu_payload else None
    if payload:
        from runtime_distribution import apply_gpu_override
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary)
            (staged/'build/game').mkdir(parents=True)
            shutil.copytree(ROOT/'patches', staged/'patches')
            shutil.copytree(ROOT/'config', staged/'config')
            apply_gpu_override(staged, payload)
    if not output.is_relative_to((ROOT/'build').resolve()):
        raise SystemExit('Release staging must remain inside build/')
    output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source = output/'source.zip'
    names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(filter(None,names)):
            data = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            archive.writestr(name,data)
        archive.writestr('builder-source.json',json.dumps({'source_revision':revision,'version':args.version}))
    command = [sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile',
        '--windowed','--name','HappyWarsBuilder','--add-data',str(source)+';.',
        '--distpath',str(output),'--workpath',str(ROOT/'build/pyinstaller'),
        '--specpath',str(ROOT/'build'),'scripts/builder.py']
    if payload:
        command.extend(['--add-data', str(payload)+';runtime-overrides'])
    subprocess.run(command,cwd=ROOT,check=True)
    executable = output/'HappyWarsBuilder.exe'
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest = {'version':args.version,'source_revision':revision,'source_archive_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'builder_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
        'scope':'Builder and project sources only; requires owned TU46 game files; portable tools are prepared automatically.'}
    if payload:
        manifest['gpu_runtime'] = json.loads((payload/'gpu-build-info.json').read_text())
    (output/'builder-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(manifest['builder_sha256']+'  HappyWarsBuilder.exe\n',encoding='utf-8')
    print(executable)
