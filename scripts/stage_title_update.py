"""Validate a title update against its exact source XEX and extract privately."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from analyze import ROOT, xex_report, version
from extract import extract
from stfs import STFS, PackageError


def inspect(package, base):
    source = xex_report(base)
    data = Path(base).read_bytes()
    security = struct.unpack_from('>I', data, 16)[0]
    signature = hashlib.sha1(data[security+8:security+264]).hexdigest()
    with STFS(package) as container:
        entry = next((e for e in container.entries if e['path'].lower() == 'default.xexp'), None)
        if entry is None:
            raise PackageError('Default.xexp missing')
        patch = b''.join(container.block(n) for n in container.chain(
            entry['first'], math.ceil(entry['size']/4096), entry['consecutive']))[:entry['size']]
        if patch[:4] != b'XEX2':
            raise PackageError('Invalid XEX patch')
        count = struct.unpack_from('>I', patch, 20)[0]
        if count > 4096:
            raise PackageError('Invalid optional-header count')
        headers = dict(struct.unpack_from('>II', patch, 24+i*8) for i in range(count))
        descriptor = headers.get(0x5ff)
        if descriptor is None:
            raise PackageError('Delta descriptor missing')
        target, required = struct.unpack_from('>II', patch, descriptor+4)
        digest = patch[descriptor+12:descriptor+32].hex()
        execution = source['execution']
        checks = {
            'title': container.u32(0x360) == int(execution['title_id'], 16),
            'media': container.u32(0x354) == int(execution['media_id'], 16),
            'source_version': version(required) == execution['version'],
            'source_signature': digest == signature,
            'content_type': container.u32(0x344) == 0xB0000,
        }
        report = dict(package=Path(package).name, base_sha256=source['sha256'],
                      required_source_version=version(required), target_version=version(target),
                      media_id=f'{container.u32(0x354):08x}', checks=checks)
        if not all(checks.values()):
            raise PackageError('Incompatible update: '+', '.join(k for k,v in checks.items() if not v))
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--base', type=Path, default=ROOT/'private/game/Default.xex')
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not destination.is_relative_to((ROOT/'private').resolve()):
        raise SystemExit('Update staging must remain inside private/')
    report = inspect(args.package, args.base)
    report['extraction'] = extract(args.package, destination)
    report['state'] = 'Extracted and verified; executable delta has not been applied'
    (ROOT/'logs/title-update-staging.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'extraction'}, indent=2))
