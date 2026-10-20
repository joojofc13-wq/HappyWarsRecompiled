"""Install runtime files while preserving game content and local profiles."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

REQUIRED = ('HappyWars.exe', 'rexruntime.dll', 'rexgpu-xenos.dll')
HELPERS = ('ResetSaves.cmd', 'reset_saves.ps1')


def reject_links(path):
    """Reject symlinks and Windows junctions, including parent directories."""
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
            raise ValueError('Linked installation paths are not supported: '+str(parent))


def validate_destination(destination, update=False):
    destination = Path(destination).absolute()
    reject_links(destination)
    if destination.exists() and not destination.is_dir():
        raise ValueError('Output must be a folder.')
    if update:
        for name in (*REQUIRED, 'game/Default.xex'):
            path = destination/name
            reject_links(path)
            if not path.is_file():
                raise ValueError('Select an existing standalone build folder; missing '+name)
    elif destination.exists() and any(destination.iterdir()):
        raise ValueError('Choose an empty output folder or select Update existing build.')
    return destination.resolve()


@contextmanager
def installation_lock(destination):
    """Keep concurrent builders from publishing into the same output."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = destination.parent/('.'+destination.name+'.builder.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError('Another builder owns this output. If it crashed, remove '+str(lock)) from None
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def check_replaceable(paths):
    """Detect a running executable or a locked DLL before replacing any file."""
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handles = []
    try:
        for path in paths:
            if not path.exists():
                continue
            handle = kernel.CreateFileW(str(path), 0x80000000 | 0x40000000, 0,
                                        None, 3, 0x80, None)
            if handle == ctypes.c_void_p(-1).value:
                raise RuntimeError('Close the game and applications using '+str(path))
            handles.append(handle)
    finally:
        for handle in handles:
            kernel.CloseHandle(handle)


def apply_gpu_override(port, payload):
    """Verify the bundled, patched SDK plugin before staging a public build."""
    port, payload = Path(port), Path(payload)
    manifest_path = payload/'gpu-build-info.json'
    plugin = payload/'rexgpu-xenos.dll'
    if not manifest_path.is_file() or not plugin.is_file():
        raise RuntimeError('Incomplete GPU runtime payload')
    info = json.loads(manifest_path.read_text())
    locked = json.loads((port/'config/upstream-lock.json').read_text())['sdk']['commit']
    if info.get('source_revision') != locked or info.get('backend') != 'd3d12':
        raise RuntimeError('GPU plugin does not match the pinned D3D12 SDK')
    if hashlib.sha256(plugin.read_bytes()).hexdigest() != info.get('plugin_sha256'):
        raise RuntimeError('GPU plugin checksum mismatch')
    from build_d3d12_gpu import PATCH_NAMES
    if set(info.get('patches', {})) != set(PATCH_NAMES):
        raise RuntimeError('GPU plugin patch set is incomplete')
    for name, digest in info['patches'].items():
        if hashlib.sha256((port/'patches'/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('GPU plugin source patch mismatch: '+name)
    native = port/'build/game'
    if not native.is_dir():
        raise RuntimeError('Build the native executable before applying its GPU plugin')
    shutil.copy2(plugin, native/'rexgpu-xenos.dll')
    shutil.copy2(manifest_path, native/'gpu-build-info.json')
    if (payload/'licenses').is_dir():
        shutil.copytree(payload/'licenses', native/'licenses', dirs_exist_ok=True)
    return info


def install_runtime(port, destination, update=False):
    """Stage first, back up old runtime files, and roll back replacement failures."""
    port = Path(port)
    native = port/'build/game'
    for name in REQUIRED:
        if not (native/name).is_file():
            raise RuntimeError('Missing runtime file: '+name)
    destination = validate_destination(destination, update)
    with installation_lock(destination):
        destination = validate_destination(destination, update)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.happywars-stage-', dir=destination.parent) as temporary:
            stage = Path(temporary)
            for source in native.iterdir():
                if source.is_file() and (source.suffix.lower() == '.dll' or
                                        source.name in ('HappyWars.exe', *HELPERS)):
                    shutil.copy2(source, stage/source.name)
            if (native/'licenses').is_dir():
                shutil.copytree(native/'licenses', stage/'licenses')
            if (native/'fonts').is_dir():
                shutil.copytree(native/'fonts', stage/'fonts')
            if not update:
                shutil.copytree(port/'private/game', stage/'game')
            metadata = port/'builder-source.json'
            provenance = json.loads(metadata.read_text()) if metadata.is_file() else {}
            managed = sorted(p.relative_to(stage).as_posix() for p in stage.rglob('*')
                             if p.is_file() and 'game' not in p.relative_to(stage).parts[:1])
            manifest = dict(format_version=1, source_revision=provenance.get('source_revision'),
                files={name:hashlib.sha256((stage/name).read_bytes()).hexdigest() for name in managed})
            if (native/'gpu-build-info.json').is_file():
                manifest['gpu_runtime'] = json.loads((native/'gpu-build-info.json').read_text())
            (stage/'build-info.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
            files = sorted(p.relative_to(stage) for p in stage.rglob('*') if p.is_file())
            for relative in files:
                target = destination/relative
                reject_links(target)
                if target.exists() and not target.is_file():
                    raise ValueError('A folder occupies a runtime file path: '+str(target))
            check_replaceable([destination/name for name in files])
            destination.mkdir(parents=True, exist_ok=True)
            backup = destination/'.update-backups'/uuid.uuid4().hex if update else None
            if backup:
                reject_links(backup)
                backup.mkdir(parents=True)
            replaced = []
            try:
                for relative in files:
                    target = destination/relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    previous = backup/relative if backup and target.exists() else None
                    if previous:
                        previous.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(target, previous)
                    # Record only after successful replacement. An interrupted copy
                    # never changes the executable currently installed.
                    os.replace(stage/relative, target)
                    replaced.append((target, previous))
            except Exception as error:
                failures = []
                for target, previous in reversed(replaced):
                    try:
                        if previous:
                            shutil.copy2(previous, target)
                        else:
                            target.unlink()
                    except OSError as restore_error:
                        failures.append(str(restore_error))
                if failures:
                    raise RuntimeError('Update rollback needs recovery from '+str(backup)+': '+
                                       '; '.join(failures)) from error
                raise
    return destination/'HappyWars.exe'
