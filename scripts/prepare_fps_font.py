"""Convert the original game's DefineFont3 outlines to a private FPS font."""
import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from resources import ROOT, decode_zres

class Bits:
    def __init__(self,data):
        self.data=data
        self.position=0
    def read(self,n):
        if self.position+n>len(self.data)*8:
            raise ValueError('Truncated glyph')
        value=0
        for _ in range(n):
            value=(value<<1)|((self.data[self.position//8]>>(7-self.position%8))&1)
            self.position+=1
        return value
    def signed(self,n):
        v=self.read(n)
        return v-(1<<n) if n and v&(1<<(n-1)) else v

def glyph_shape(data):
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    bits=Bits(data)
    fills,lines=bits.read(4),bits.read(4)
    pen=TTGlyphPen(None)
    x=y=0
    opened=False
    def point(x,y):
        return round(x/20),round(-y/20)
    while True:
        edge=bits.read(1)
        if not edge:
            flags=bits.read(5)
            if not flags:
                break
            if flags&16:
                raise ValueError('Unexpected new styles in font glyph')
            if flags&1:
                if opened:
                    pen.closePath()
                n=bits.read(5)
                x,y=bits.signed(n),bits.signed(n)
                pen.moveTo(point(x,y))
                opened=True
            if flags&2:
                bits.read(fills)
            if flags&4:
                bits.read(fills)
            if flags&8:
                bits.read(lines)
            continue
        if not opened:
            pen.moveTo(point(x,y))
            opened=True
        straight=bits.read(1)
        n=bits.read(4)+2
        if straight:
            if bits.read(1):
                x+=bits.signed(n)
                y+=bits.signed(n)
            elif bits.read(1):
                y+=bits.signed(n)
            else:
                x+=bits.signed(n)
            pen.lineTo(point(x,y))
        else:
            cx,cy=x+bits.signed(n),y+bits.signed(n)
            x,y=cx+bits.signed(n),cy+bits.signed(n)
            pen.qCurveTo(point(cx,cy),point(x,y))
    if opened:
        pen.closePath()
    return pen.glyph()

def font_tags(resource):
    start=resource.index(b'CFX')
    header=resource[start:start+8]
    expected=struct.unpack_from('<I',header,4)[0]
    if expected>32*1024*1024:
        raise ValueError('Font movie exceeds size limit')
    movie=header+zlib.decompress(resource[start+8:])
    if len(movie)!=expected:
        raise ValueError('Font movie size mismatch')
    rect_bits=movie[8]>>3
    p=8+(5+4*rect_bits+7)//8+4
    while p+2<=len(movie):
        record=struct.unpack_from('<H',movie,p)[0]
        p+=2
        kind,length=record>>6,record&63
        if length==63:
            length=struct.unpack_from('<I',movie,p)[0]
            p+=4
        if p+length>len(movie):
            raise ValueError('Truncated font tag')
        if kind==75:
            yield movie[p:p+length]
        p+=length
        if not kind:
            break

def prepare(python_path=None,source=None):
    if python_path:
        sys.path.insert(0,str(python_path))
    else:
        for p in (ROOT/'tools/python',ROOT.parent.parent/'work/python-tools'):
            if p.exists():
                sys.path.insert(0,str(p))
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    source=Path(source) if source else ROOT/'private/game/media/scaleform/Font_en.bres'
    if not source.is_file() and source == ROOT/'private/game/media/scaleform/Font_en.bres':
        print('Optional Scaleform font is absent; FPS overlay will be disabled.')
        return None
    source_bytes=source.read_bytes()
    output=ROOT/'private/ui/happywars-fps.ttf'
    report_file=ROOT/'logs/fps-font.json'
    source_hash=hashlib.sha256(source_bytes).hexdigest()
    script_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if output.exists() and report_file.exists():
        prior=json.loads(report_file.read_text())
        if prior.get('source_sha256')==source_hash and prior.get('script_sha256')==script_hash:
            return output
    resource=decode_zres(source_bytes) or source_bytes
    for tag in font_tags(resource):
        name=tag[5:5+tag[4]].rstrip(b'\0').decode('utf-8')
        if 'Rowdy' not in name:
            continue
        flags=tag[2]
        if flags&0x8c!=0x8c:
            raise ValueError('Expected font layout, wide offsets and wide codes')
        p=5+tag[4]
        count=struct.unpack_from('<H',tag,p)[0]
        origin=p+2
        offsets=struct.unpack_from('<'+str(count+1)+'I',tag,origin)
        codes=struct.unpack_from('<'+str(count)+'H',tag,origin+offsets[-1])
        layout=origin+offsets[-1]+count*2
        ascent,descent,leading=struct.unpack_from('<hhh',tag,layout)
        advances=struct.unpack_from('<'+str(count)+'h',tag,layout+6)
        required=set(map(ord,'0123456789FPS .'))
        if not required.issubset(codes):
            raise ValueError('Game font is missing FPS glyphs')
        glyphs={'.notdef':TTGlyphPen(None).glyph()}
        metrics={'.notdef':(512,0)}
        cmap={}
        for i,code in enumerate(codes):
            if code not in required:
                continue
            glyph=glyph_shape(tag[origin+offsets[i]:origin+offsets[i+1]])
            glyph.recalcBounds(None)
            key='uni'+format(code,'04X')
            glyphs[key]=glyph
            metrics[key]=(round(advances[i]/20),getattr(glyph,'xMin',0))
            cmap[code]=key
        builder=FontBuilder(1024,isTTF=True)
        builder.setupGlyphOrder(list(glyphs))
        builder.setupCharacterMap(cmap)
        builder.setupGlyf(glyphs)
        builder.setupHorizontalMetrics(metrics)
        asc,desc=round(ascent/20),-abs(round(descent/20))
        builder.setupHorizontalHeader(ascent=asc,descent=desc,lineGap=round(leading/20))
        builder.setupNameTable(dict(familyName=name,styleName='Regular',
            uniqueFontIdentifier='HappyWarsLocalFPS',fullName=name+' FPS subset',
            psName='HappyWarsLocalFPS'))
        builder.setupOS2(sTypoAscender=asc,sTypoDescender=desc,
            usWinAscent=max(0,asc),usWinDescent=abs(desc))
        builder.setupPost()
        output.parent.mkdir(parents=True,exist_ok=True)
        builder.save(output)
        with TTFont(output) as check:
            if set(check.getBestCmap())!=required:
                raise ValueError('Converted font cmap mismatch')
        report_file.write_text(json.dumps(dict(source_font=name,glyphs=len(cmap),
            source_sha256=source_hash,script_sha256=script_hash,
            output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
            scope='Original outlines converted locally; font file is not redistributed'),indent=2))
        print('Prepared private FPS subset from '+name)
        return output
    raise ValueError('Original Rowdy font was not found')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-path',type=Path)
    parser.add_argument('--source',type=Path,help='Original Scaleform font resource from an owned copy')
    args=parser.parse_args()
    prepare(args.python_path,args.source)
