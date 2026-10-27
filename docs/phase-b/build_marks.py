"""Rebuild draft vector marks and outlined Arabic wordmarks only in docs/phase-b/marks.
Optional authoring dependencies: fontTools and uharfbuzz==0.55.0.
Uses the repository's OFL-licensed Tajawal Bold. Does not generate a modified font.
"""
from pathlib import Path
import sys
if Path('/tmp/darb-phase-b-tools').exists():
    sys.path.insert(0,'/tmp/darb-phase-b-tools')
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'marks'
FONT=ROOT/'fonts/Tajawal-Bold.ttf'
f=TTFont(FONT); glyphs=f.getGlyphSet(); order=f.getGlyphOrder()
face=hb.Face(FONT.read_bytes()); font=hb.Font(face)
blue='#335f73';sage='#688574';gold='#d7a448'
SYMBOLS={
'a':f'<path d="M24 96V57a38 38 0 0 1 76 0v39" fill="none" stroke="{blue}" stroke-width="13" stroke-linecap="round"/><path d="M35 116c46-3 59-20 30-30-27-10-16-21 3-31" fill="none" stroke="{gold}" stroke-width="13" stroke-linecap="round"/><path d="m72 29 5 11 12 2-9 8 2 12-10-6-11 6 2-12-9-8 12-2Z" fill="{gold}"/><path d="M16 115q9-18 27-18l-8 19Z" fill="{sage}"/>',
'b':f'<path d="M62 111c-21-8-13-26 5-43 8-8 9-19 5-28" fill="none" stroke="{gold}" stroke-width="11" stroke-linecap="round"/><path d="M64 72C24 72 13 45 16 17c32 0 56 14 48 55Z" fill="{sage}"/><path d="M76 66c-4-36 12-52 40-55 3 28-6 51-40 55Z" fill="{blue}"/><path d="m30 34 28 27m28-6 17-28" fill="none" stroke="#f8f5ed" stroke-width="4" stroke-linecap="round"/><path d="M68 87c-18 7-24 20-12 30 20 2 30-9 12-30Z" fill="{gold}"/>',
'c':f'<path d="M20 82h76L82 97H35Z" fill="{blue}"/><path d="M59 15v60l40-4Z" fill="{gold}"/><path d="M51 34 23 75l28-4Z" fill="{blue}"/><path d="M9 107q18-10 36 0t36 0t36 0" fill="none" stroke="{blue}" stroke-width="7" stroke-linecap="round"/><path d="M26 121q18-8 36 0t36 0" fill="none" stroke="{sage}" stroke-width="5" stroke-linecap="round"/><path d="M94 54a14 14 0 0 1 28 0" fill="{gold}"/>'
}
def outlines(text):
    buf=hb.Buffer();buf.add_str(text);buf.guess_segment_properties();hb.shape(font,buf,{'kern':True})
    parts=[];x=0
    minx=miny=10**8;maxx=maxy=-10**8
    for info,pos in zip(buf.glyph_infos,buf.glyph_positions):
        name=order[info.codepoint];tr=(1,0,0,-1,x+pos.x_offset,-pos.y_offset)
        pen=SVGPathPen(glyphs);glyphs[name].draw(TransformPen(pen,tr));parts.append(pen.getCommands())
        bp=BoundsPen(glyphs);glyphs[name].draw(TransformPen(bp,tr))
        if bp.bounds:
            a,b,c,d=bp.bounds;minx=min(minx,a);miny=min(miny,b);maxx=max(maxx,c);maxy=max(maxy,d)
        x+=pos.x_advance
    scale=min(240/(maxx-minx),58/(maxy-miny))
    tx=(260-(maxx-minx)*scale)/2-minx*scale
    ty=(80-(maxy-miny)*scale)/2-miny*scale
    return f'<g transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f})"><path d="{" ".join(parts)}"/></g>'
def svg(vb,body,label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{label}"><title>{label}</title>{body}</svg>\n'
OUT.mkdir(exist_ok=True)
for key,text in [('a','درب الثـراء'),('b','درب الـثراء'),('c','درب الثراء')]:
    symbol=SYMBOLS[key]
    word=outlines(text)
    if key=='b':
        word=f'<g transform="translate(108 -7) scale(.5)">{outlines("درب")}</g><g transform="translate(18 24) scale(.78)">{outlines("الثـراء")}</g>'
    (OUT/f'{key}-mark.svg').write_text(svg('0 0 128 128',symbol,'رمز مقترح '+key))
    (OUT/f'{key}-wordmark.svg').write_text(svg('0 0 260 80',f'<g fill="{blue}">{word}</g>','درب الثراء — صياغة أولية '+key))
    for suffix,color in [('lockup',blue),('light','#f8f5ed')]:
        display_symbol=symbol if suffix=='lockup' else symbol.replace(blue,'#dce8eb').replace(sage,'#a7bc9f')
        body=f'<g transform="translate(274 2) scale(.72)">{display_symbol}</g><g transform="translate(0 8)" fill="{color}">{word}</g>'
        (OUT/f'{key}-{suffix}.svg').write_text(svg('0 0 370 96',body,'درب الثراء — مقترح '+key))
print('Built 12 draft SVG assets; Arabic names are outlined paths, no generated text.')
