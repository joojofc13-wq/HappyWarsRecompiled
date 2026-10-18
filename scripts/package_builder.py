"""Package the Windows builder with audited project sources, never game files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from audit_publication import audit

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    audit()
    output = ROOT/'build/builder-release'
    output.mkdir(parents=True, exist_ok=True)
    source = output/'source.zip'
    names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(filter(None,names)):
            data = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            archive.writestr(name,data)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile',
        '--windowed','--name','HappyWarsBuilder','--add-data',str(source)+';.',
        '--distpath',str(output),'--workpath',str(ROOT/'build/pyinstaller'),
        '--specpath',str(ROOT/'build'),'scripts/builder.py'],cwd=ROOT,check=True)
    executable = output/'HappyWarsBuilder.exe'
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest = {'source_revision':revision,'source_archive_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'builder_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
        'scope':'Builder and project sources only; requires owned TU46 game files and an external toolchain.'}
    (output/'builder-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(manifest['builder_sha256']+'  HappyWarsBuilder.exe\n',encoding='utf-8')
    print(executable)
