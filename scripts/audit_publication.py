"""Check the exact Git index before publishing project-owned sources."""
import json
import hashlib
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={'.exe','.dll','.xex','.xexp','.lib','.obj','.pdb','.bin','.sqlite','.zip','.bres','.pres','.wmv'}
COVER_SHA256='ebd225170505e71bc627cbf2c499cf80e13af30ed70af4864b5598e58f7a86dc'

def audit():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    checked=0
    for name in filter(None,names):
        path=Path(name)
        if path.parts[0] in ('private','saves','build','logs') or \
           name.startswith('generated/default/') or path.suffix.lower() in FORBIDDEN or \
           path.name=='local-tools.json':
            raise ValueError(f'Private or generated artifact in index: {name}')
        data=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
        cover=name=='assets/happy-wars-cover.png'
        if cover and (not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest()!=COVER_SHA256):
            raise ValueError('README cover does not match the supplied image')
        if (len(data)>1024*1024 and not cover) or data.startswith((b'MZ',b'PK\x03\x04')):
            raise ValueError(f'Unexpected binary or oversized file: {name}')
        if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',data):
            raise ValueError(f'Credential-like content in file: {name}')
        if re.search(rb'C:[\\/]Users[\\/]',data,re.I):
            raise ValueError(f'Local user path in public file: {name}')
        checked+=1
    if not checked:
        raise ValueError('No tracked sources to publish')
    print(json.dumps(dict(tracked_files_checked=checked,private_artifacts_found=0,
        scope='Exact staged sources; excludes proprietary assets, translated game code and local logs')))

if __name__=='__main__':
    audit()
