"""Read-only STFS inventory and independent integrity checks.

Layout references: Xenia stfs_xbox.h, stfs_container_device.cc (BSD-3-Clause).
Only the single hash-table, read-only format is accepted. Resilient CON
packages are rejected rather than guessing which table copy is active.
"""
import hashlib
import math
import mmap
from pathlib import Path, PurePosixPath


class PackageError(ValueError):
    pass


def safe_relative(name):
    p = PurePosixPath(name.replace('\\', '/'))
    if (not name or not p.parts or p.is_absolute() or any(x in ('..', '.') for x in p.parts)
            or any(':' in x or x.endswith((' ', '.')) for x in p.parts)):
        raise PackageError(f'Unsafe path: {name!r}')
    for part in p.parts:
        if any(c in part for c in '<>"|?*\x00') or part.split('.')[0].upper() in {
                'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)),
                *('LPT'+str(i) for i in range(1,10))}:
            raise PackageError(f'Unsafe Windows filename: {name!r}')
    return p.as_posix()


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


class STFS:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open('rb')
        try:
            self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
            if self.data[:4] not in (b'LIVE', b'PIRS', b'CON '):
                raise PackageError('Not STFS (LIVE/PIRS/CON)')
            if len(self.data) < 0xA000:
                raise PackageError('Truncated STFS header')
            self.base = (self.u32(0x340) + 4095) & ~4095
            if self.base < 0xA000 or self.base >= len(self.data):
                raise PackageError('Invalid header length')
            if self.data[0x379] != 0x24:
                raise PackageError('Unsupported volume descriptor')
            if not self.data[0x37b] & 1:
                raise PackageError('Resilient STFS needs active-table selection; unsupported')
            self.total = self.u32(0x395)
            self.checked = set()
            self.entries = self.read_entries()
        except Exception:
            self.close()
            raise

    def close(self):
        if hasattr(self, 'data'):
            self.data.close()
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def u32(self, offset):
        return int.from_bytes(self.read(offset, 4), 'big')

    def read(self, offset, size):
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise PackageError(f'Read outside package at {offset:#x}, {size:#x}')
        return self.data[offset:offset+size]

    def block_offset(self, block):
        if not 0 <= block < self.total:
            raise PackageError(f'Block outside volume: {block}')
        n, base = block, 170
        for _ in range(3):
            n += (block + base) // base
            if block < base:
                break
            base *= 170
        return self.base + n * 4096

    def hash_record(self, block):
        if block < 170:
            backing = 0
        else:
            backing = (block // 170) * 171 + (block // 28900) + 1
            if block >= 28900:
                backing += 1
        return self.read(self.base + backing * 4096 + (block % 170) * 24, 24)

    def block(self, block):
        data = self.read(self.block_offset(block), 4096)
        if block not in self.checked:
            if hashlib.sha1(data).digest() != self.hash_record(block)[:20]:
                raise PackageError(f'SHA-1 mismatch at STFS block {block}')
            self.checked.add(block)
        return data

    def chain(self, first, count, consecutive=False):
        seen = set()
        block = first
        for i in range(count):
            if block in seen:
                raise PackageError('STFS chain cycle')
            seen.add(block)
            yield block
            if i+1 < count:
                block = block+1 if consecutive else int.from_bytes(self.hash_record(block)[21:24], 'big')

    def read_entries(self):
        count = int.from_bytes(self.read(0x37c, 2), 'little')
        first = int.from_bytes(self.read(0x37e, 3), 'little')
        if count < 1 or count > self.total:
            raise PackageError('Invalid file table size')
        entries = {}
        for table_index, block in enumerate(self.chain(first, count)):
            data = self.block(block)
            for slot in range(64):
                raw = data[slot*64:slot*64+64]
                length = raw[0x28] & 0x3f
                if not length:
                    continue
                if length > 40:
                    raise PackageError('Invalid STFS filename length')
                name = raw[:length].decode('ascii')
                entries[table_index*64+slot] = dict(
                    name=name, directory=bool(raw[0x28]&128),
                    consecutive=bool(raw[0x28]&64),
                    blocks=int.from_bytes(raw[0x29:0x2c], 'little'),
                    first=int.from_bytes(raw[0x2f:0x32], 'little'),
                    parent=int.from_bytes(raw[0x32:0x34], 'big'),
                    size=int.from_bytes(raw[0x34:0x38], 'big'))
        def resolve(index, active):
            if index in active:
                raise PackageError('STFS directory cycle')
            e = entries[index]
            if e['parent'] == 0xffff:
                return safe_relative(e['name'])
            parent = entries.get(e['parent'])
            if not parent or not parent['directory']:
                raise PackageError('Invalid STFS parent')
            return safe_relative(resolve(e['parent'], active|{index})+'/'+e['name'])
        paths = set()
        for i,e in entries.items():
            e['path'] = resolve(i, set())
            key = e['path'].casefold()
            if key in paths:
                raise PackageError('Case-insensitive duplicate path')
            paths.add(key)
        return list(entries.values())

    def verify_tree(self, root):
        root = Path(root).resolve()
        files = []
        for e in self.entries:
            p = root / e['path']
            if not p.resolve().is_relative_to(root):
                raise PackageError('Extraction escaped target')
            if e['directory']:
                if not p.is_dir():
                    raise PackageError(f'Missing directory: {p}')
                continue
            if not p.is_file() or p.stat().st_size != e['size']:
                raise PackageError(f'Missing file or size mismatch: {p}')
            expected = math.ceil(e['size']/4096)
            if e['blocks'] < expected:
                raise PackageError(f'Insufficient allocation for {p}')
            digest = hashlib.sha256()
            remaining = e['size']
            for block in self.chain(e['first'], expected, e['consecutive']):
                data = self.block(block)
                digest.update(data[:min(remaining,4096)])
                remaining -= min(remaining,4096)
            actual = sha256_file(p)
            if digest.hexdigest() != actual:
                raise PackageError(f'Extracted data differs from container: {p}')
            files.append(dict(path=e['path'], size=e['size'], sha256=actual))
        return dict(package_sha256=sha256_file(self.path), files=files,
                    checked_data_blocks=len(self.checked),
                    integrity='SHA-1 for referenced data blocks; SHA-256 file bytes compared to container',
                    limitations=['RSA signature and upper hash-tree authentication are not verified'])
