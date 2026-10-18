"""Automatic extraction through pinned Extract-STFS, with independent checks."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from stfs import STFS, PackageError, safe_relative

ROOT = Path(__file__).resolve().parents[1]


def extract(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    with source.open('rb') as f:
        magic = f.read(4)
    if zipfile.is_zipfile(source):
        with tempfile.TemporaryDirectory(prefix='happywars-zip-') as scratch:
            with zipfile.ZipFile(source) as archive:
                if sum(i.file_size for i in archive.infolist()) > 10*1024**3:
                    raise PackageError('Archive exceeds 10 GiB limit')
                names = set()
                for entry in archive.infolist():
                    relative = safe_relative(entry.filename)
                    if relative.casefold() in names or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise PackageError('Duplicate ZIP path or symlink')
                    names.add(relative.casefold())
                    target = Path(scratch)/relative
                    if entry.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(entry) as a, target.open('wb') as b:
                            shutil.copyfileobj(a,b)
            candidates=[]
            for path in Path(scratch).rglob('*'):
                if path.is_file():
                    with path.open('rb') as f:
                        if f.read(4) in (b'LIVE',b'PIRS',b'CON '):
                            candidates.append(path)
            if len(candidates)!=1:
                raise PackageError(f'Expected one STFS package, found {len(candidates)}')
            return extract(candidates[0],destination)
    if magic not in (b'LIVE',b'PIRS',b'CON '):
        raise PackageError(f'Unsupported input signature {magic!r}; no extension guessing')
    # Upstream opens the input with FileShare.None. Finish preflight before
    # starting PowerShell so our read-only mmap cannot cause a sharing failure.
    with STFS(source):
        pass
    if destination.exists():
        # Repeat runs verify rather than silently mixing files from versions.
        with STFS(source) as package:
            result = package.verify_tree(destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='extract-',dir=destination.parent) as scratch:
            stage = Path(scratch)/'game'
            command = ['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                       str(ROOT/'tools/Extract-STFS.ps1'),'-Path',str(source),'-OutputDir',str(stage)]
            result_process = subprocess.run(command, capture_output=True, text=True)
            (ROOT/'logs/stfs-extract.log').write_text(result_process.stdout+result_process.stderr,encoding='utf-8')
            if result_process.returncode:
                raise PackageError('Extract-STFS failed; see logs/stfs-extract.log')
            with STFS(source) as package:
                result = package.verify_tree(stage)
            stage.rename(destination)
    result['source'] = str(source)
    result['default_xex']=[f['path'] for f in result['files'] if Path(f['path']).name.lower()=='default.xex']
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--destination',type=Path,default=ROOT/'private/game')
    args=parser.parse_args()
    try:
        result=extract(args.source,args.destination)
        (ROOT/'logs/extraction.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f"Verified {len(result['files'])} files, {result['checked_data_blocks']} blocks")
        if not result['default_xex']:
            raise PackageError('default.xex missing')
    except (OSError,ValueError,zipfile.BadZipFile) as error:
        print(f'Extraction failed: {error}',file=sys.stderr)
        sys.exit(1)
