"""Decode observed ZRES/zlib assets into private/decoded; never edit originals."""
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def decode_zres(data):
    if data[:4]!=b'ZRES':
        return None
    if len(data)<8:
        raise ValueError('Truncated ZRES')
    size=struct.unpack_from('<I',data,4)[0]
    if size>512*1024**2:
        raise ValueError('ZRES exceeds decompression limit')
    decoder=zlib.decompressobj()
    decoded=decoder.decompress(data[8:],size+1)
    if len(decoded)!=size or not decoder.eof or decoder.unused_data:
        raise ValueError('ZRES declared length or stream boundary mismatch')
    return decoded


def scan():
    game=ROOT/'private/game'
    inventory=[]
    hits=[]
    failures=[]
    keywords=re.compile(r'skirmish|happy.?card|inventory|match.?mak|server|reward|unlock|game.?mode|offline',re.I)
    for file in sorted(game.rglob('*')):
        if not file.is_file():
            continue
        relative=file.relative_to(game)
        data=file.read_bytes()
        try:
            decoded=decode_zres(data)
            if decoded is None:
                continue
            output=ROOT/'private/decoded'/relative
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(decoded)
            inventory.append(dict(path=relative.as_posix(),size=len(decoded),sha256=hashlib.sha256(decoded).hexdigest()))
            if file.suffix in ('.json','.nut'):
                text=decoded.decode('utf-8-sig',errors='replace')
                for number,line in enumerate(text.splitlines(),1):
                    if keywords.search(line):
                        hits.append(dict(path=relative.as_posix(),line=number,text=line[:240]))
        except ValueError as error:
            failures.append(dict(path=relative.as_posix(),error=str(error)))
    report=dict(decoded=inventory,keyword_hits=hits,failures=failures,
        limitations=['Keywords are investigation leads, not proven code paths or protocol definitions'])
    (ROOT/'logs/resource-analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Decoded {len(inventory)} assets; {len(hits)} keyword hits; {len(failures)} failures')


if __name__=='__main__':
    scan()
