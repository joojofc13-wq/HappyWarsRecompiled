"""Select the newest compatible local title update and verify its extracted files.

This stages private inputs. Updated PowerPC code must be recompiled separately.
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from analyze import ROOT
from extract import extract
from stage_title_update import inspect
from stfs import sha256_file


def packages(source):
    files = sorted(source.rglob('*')) if source.is_dir() else [source]
    cache = ROOT/'private/title-update-imports'
    cache.mkdir(parents=True, exist_ok=True)
    for path in files:
        if not path.is_file():
            continue
        if path.suffix.lower() == '.zip':
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > 4096:
                    raise ValueError('Too many ZIP entries')
                archive_hash = None
                for entry in entries:
                    if entry.is_dir() or entry.file_size > 512*1024*1024:
                        continue
                    # Read the signature without extracting paths from the ZIP.
                    with archive.open(entry) as stream:
                        if stream.read(4) not in (b'LIVE', b'PIRS', b'CON '):
                            continue
                    archive_hash = archive_hash or sha256_file(path)
                    key = hashlib.sha256((archive_hash+'\0'+entry.filename).encode()).hexdigest()
                    target = cache/key
                    if not target.exists():
                        temporary = cache/(key+'.part')
                        with archive.open(entry) as stream, temporary.open('wb') as output:
                            shutil.copyfileobj(stream, output)
                        temporary.rename(target)
                    # Validate cached bytes against the ZIP, including its CRC.
                    with archive.open(entry) as stream:
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    if sha256_file(target) != digest:
                        raise ValueError('Cached package differs from ZIP member')
                    yield target, path.name+' / '+entry.filename
        else:
            with path.open('rb') as stream:
                if stream.read(4) in (b'LIVE', b'PIRS', b'CON '):
                    yield path, path.name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='ZIP, extracted package, or directory')
    parser.add_argument('--base', type=Path, default=ROOT/'private/game/Default.xex')
    args = parser.parse_args()
    if not args.source.exists():
        raise SystemExit('Input does not exist')
    accepted, rejected, seen = [], [], set()
    for package, label in packages(args.source):
        digest = sha256_file(package)
        if digest in seen:
            continue
        seen.add(digest)
        try:
            report = inspect(package, args.base)
        except (ValueError, StopIteration) as error:
            rejected.append(dict(source=label, reason=str(error)))
            continue
        accepted.append((report, package, digest, label))
    if not accepted:
        raise SystemExit('No update matches the source version, Media ID and signature')
    report, package, digest, label = max(accepted,
        key=lambda item: tuple(map(int, item[0]['target_version'].split('.'))))
    destination = ROOT/'private/title-updates'/(report['target_version']+'-'+digest[:12])
    verification = extract(package, destination)
    result = dict(selected=label, target_version=report['target_version'],
        destination=str(destination.relative_to(ROOT)), package_sha256=digest,
        compatible_alternatives=[r['target_version'] for r, _, _, _ in accepted],
        rejected=rejected, extraction=verification,
        state='Verified private inputs; native rebuild still required')
    (ROOT/'logs/title-update-import.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('extraction','rejected')}, indent=2))


if __name__ == '__main__':
    main()
