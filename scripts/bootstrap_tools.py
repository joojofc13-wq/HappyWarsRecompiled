"""Download pinned portable build tools into an owned output workspace."""
import hashlib
import json
import os
from pathlib import Path
import stat
import urllib.request
import urllib.parse
import uuid
import zipfile


def extract_archive(archive, destination):
    destination=Path(destination).resolve()
    with zipfile.ZipFile(archive) as source:
        if sum(entry.file_size for entry in source.infolist()) > 5*1024**3:
            raise ValueError('Tool archive exceeds the extraction limit')
        seen=set()
        for entry in source.infolist():
            relative=Path(entry.filename)
            target=(destination/relative).resolve()
            if (not target.is_relative_to(destination) or relative.is_absolute() or
                    ':' in entry.filename or '\\' in entry.filename or
                    stat.S_ISLNK(entry.external_attr >> 16) or str(relative).casefold() in seen):
                raise ValueError('Unsafe tool archive path')
            seen.add(str(relative).casefold())
        source.extractall(destination)


def download(spec, cache, emit=print):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    name=Path(urllib.parse.urlparse(spec['url']).path).name
    output=cache/name
    if output.is_file():
        with output.open('rb') as source:
            if hashlib.file_digest(source,'sha256').hexdigest()==spec['sha256']:
                return output
    partial=cache/(name+'.'+uuid.uuid4().hex+'.part')
    emit('Downloading '+name)
    request=urllib.request.Request(spec['url'],headers={'User-Agent':'HappyWarsRecompiled-Builder'})
    digest=hashlib.sha256()
    with urllib.request.urlopen(request,timeout=120) as response,partial.open('wb') as target:
        total=int(response.headers.get('Content-Length','0'));received=0;reported=-1
        while block:=response.read(1024*1024):
            digest.update(block);target.write(block);received+=len(block)
            progress=int(received*100/total) if total else 0
            if total and progress//10>reported:
                reported=progress//10;emit('Downloading '+name+': '+str(min(progress,100))+'%')
    if digest.hexdigest()!=spec['sha256']:
        raise ValueError('Tool download SHA-256 mismatch: '+name)
    partial.replace(output)
    return output


def bootstrap(port, emit=print):
    port=Path(port).resolve()
    specs=json.loads((port/'config/upstream-lock.json').read_text())['portable_tools']
    root=port/'tools/bootstrap';cache=root/'downloads'
    python=root/'python';git=root/'git';llvm=root/'llvm'
    for key,folder in [('python',python),('git',git),('llvm',llvm)]:
        archive=download(specs[key],cache,emit)
        emit('Extracting '+key)
        extract_archive(archive,folder)
    # pip runs from the embedded interpreter; no system installation is used.
    extract_archive(download(specs['pip'],cache,emit),python)
    path_file=next(python.glob('python*._pth'))
    stdlib=next(python.glob('python*.zip')).name
    path_file.write_text(stdlib+'\n.\n../../python\n../../../scripts\nimport site\n',encoding='utf-8')
    compiler=next(llvm.glob('*/bin/clang-[0-9]*.exe'),None)
    if compiler is None:raise RuntimeError('Portable LLVM compiler is missing')
    git_exe=git/'cmd/git.exe'
    if not git_exe.is_file():raise RuntimeError('Portable Git is missing')
    os.environ['PATH']=str(git_exe.parent)+os.pathsep+os.environ.get('PATH','')
    os.environ['GIT_TERMINAL_PROMPT']='0'
    os.environ['GIT_CONFIG_NOSYSTEM']='1'
    os.environ['GIT_CONFIG_GLOBAL']=os.devnull
    os.environ['GIT_CONFIG_COUNT']='1'
    os.environ['GIT_CONFIG_KEY_0']='core.longpaths'
    os.environ['GIT_CONFIG_VALUE_0']='true'
    return {'python':[str(python/'python.exe')],'llvm':compiler.parent,'git':git_exe}
