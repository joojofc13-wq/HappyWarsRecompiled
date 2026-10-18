"""Launch a playtest with a separate log and group observed failures by address."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
FATAL = re.compile(r'Call to invalid or unregistered function at guest address (0x[0-9a-fA-F]+)')


def summarize(root=ROOT):
    directory = root/'logs/playtests'
    sessions = []
    failures = defaultdict(list)
    for manifest in sorted(directory.glob('*.json')):
        session = json.loads(manifest.read_text(encoding='utf-8'))
        log = root/session['log']
        content = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        addresses = sorted({f'0x{int(a,16):08X}' for a in FATAL.findall(content)})
        session['missing_functions'] = addresses
        session['critical_lines'] = [line for line in content.splitlines() if '[critical]' in line][-8:]
        session['gpu_errors'] = [line for line in content.splitlines() if 'D3D12 device removed:' in line][-4:]
        for address in addresses:
            failures[address].append(session['log'])
        sessions.append(session)
    report = {'sessions': sessions, 'missing_functions': [
        {'address': address, 'occurrences': len(logs), 'logs': logs}
        for address, logs in sorted(failures.items())]}
    directory.parent.mkdir(parents=True, exist_ok=True)
    pending = directory.parent/f'playtest-summary-{uuid.uuid4().hex}.tmp'
    pending.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    pending.replace(directory.parent/'playtest-summary.json')
    return report


def launch(label='', root=ROOT):
    executable = root/'build/game/HappyWars.exe'
    game = root/'private/game'
    if not executable.is_file() or not (game/'Default.xex').is_file():
        raise RuntimeError('Build the native executable and import your game files first.')
    directory = root/'logs/playtests'
    directory.mkdir(parents=True, exist_ok=True)
    identity = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    log = directory/f'{identity}.log'
    manifest = directory/f'{identity}.json'
    command = [str(executable), f'--game_data_root={game}',
        f'--user_data_root={root / "private/smoke-user"}',
        f'--cache_root={root / "private/smoke-cache"}', f'--log_file={log}',
        '--window_width=1280', '--window_height=720', '--mnk_mode=true']
    with executable.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    session = {'id': identity, 'label': label, 'log': log.relative_to(root).as_posix(),
        'executable_sha256': digest,
        'state': 'starting'}
    def save():
        pending = manifest.with_suffix('.tmp')
        pending.write_text(json.dumps(session, indent=2)+'\n', encoding='utf-8')
        pending.replace(manifest)
    save()
    try:
        gpu_path = root/'private/gpu-settings.json'
        if gpu_path.exists():
            gpu = json.loads(gpu_path.read_text(encoding='utf-8'))
            selected = {}
            for key in ('d3d12_bindless', 'd3d12_debug', 'd3d12_tiled_shared_memory'):
                if key not in gpu:
                    continue
                if type(gpu[key]) is not bool:
                    raise ValueError(f'{key} must be a boolean')
                command.append(f'--{key}={str(gpu[key]).lower()}')
                selected[key] = gpu[key]
            session['gpu_settings'] = selected
        session['profile'] = 'private/smoke-user'
        # Keep launcher output in this session, including failures before runtime logging starts.
        with (directory/f'{identity}.launcher.txt').open('wb') as output:
            process = subprocess.Popen(command, cwd=executable.parent,
                stdout=output, stderr=subprocess.STDOUT)
            session.update(pid=process.pid, state='running')
            save()
            session.update(exit_code=process.wait(), state='exited')
    except (OSError, ValueError, RuntimeError) as error:
        session.update(state='launch_failed', error=str(error))
    finally:
        save()
        summarize(root)
    return session


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='', help='Optional map, difficulty or action being tested')
    parser.add_argument('--summarize', action='store_true', help='Update the grouped report without launching')
    args = parser.parse_args()
    if args.summarize:
        report = summarize()
        print(f'{len(report["sessions"])} sessions; {len(report["missing_functions"])} distinct missing functions')
    else:
        launch(args.label)
