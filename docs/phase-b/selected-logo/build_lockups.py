"""Compose the selected raster symbol with outlined Arabic lettering.
SVG compositions embed PNG; they are not pure vector artwork.
Writes only in docs/phase-b/selected-logo; uses an existing outlined wordmark.
"""
import base64
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parent
NS='{http://www.w3.org/2000/svg}'

def word(color):
    original=ET.fromstring((ROOT.parent/'marks/a-wordmark.svg').read_text())
    group=list(original)[1] if list(original)[0].tag==NS+'title' else list(original)[0]
    # Original holds shaped, outlined Arabic; retain connected forms and proportions.
    group.attrib['fill']=color
    for path in group.iter(NS+'path'):
        path.set('stroke','#5b3d29');path.set('stroke-width','24');path.set('stroke-linejoin','round');path.set('paint-order','stroke fill')
    return ET.tostring(group,encoding='unicode')

def png(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
def svg(view,body,label):return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+view+'" role="img" aria-label="'+label+'"><title>'+label+'</title>'+body+'</svg>\n'

def main():
    art=png(ROOT/'symbol.png')
    for name,color in [('horizontal','#e2ac3b'),('horizontal-dark','#f6e1b2')]:
        body=f'<image href="{art}" x="410" y="0" width="180" height="180"/><g transform="translate(4 38) scale(1.55)">{word(color)}</g>'
        (ROOT/(name+'.svg')).write_text(svg('0 0 600 180',body,'درب الثراء — خطوة إلى الحلم'))
    body=f'<image href="{art}" x="40" y="0" width="340" height="340"/><g transform="translate(15 328) scale(1.5)">{word("#e2ac3b")}</g>'
    (ROOT/'vertical.svg').write_text(svg('0 0 420 458',body,'درب الثراء — الشعار الرأسي'))
    (ROOT/'wordmark.svg').write_text(svg('0 0 260 80',word('#e2ac3b'),'درب الثراء — كتابة متجهية'))
    print('Composed horizontal, dark, vertical and vector wordmark assets.')

if __name__=='__main__':main()
