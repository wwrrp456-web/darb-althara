"""Package the prototype into one downloadable HTML; no application files modified.
Run: python3 docs/phase-b/make_review.py --output /workspace/darb-althara-review.html
The output embeds original, unmodified local assets, SVGs, CSS, JS and fonts.
"""
import argparse
import base64
import json
import mimetypes
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def data(path):
 path=path.resolve()
 mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
 return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

def build(output):
 html=(ROOT/'index.html').read_text()
 css=(ROOT/'prototype.css').read_text()
 css=re.sub(r"url\(['\"]?([^)'\"]+)['\"]?\)",lambda m:'url("'+data(ROOT/m[1])+'")',css)
 html=html.replace('<link rel="stylesheet" href="prototype.css">','<style>'+css+'</style>')
 html=re.sub(r'(<img\b[^>]*?\bsrc=)"([^"\n]+)"',lambda m:m[1]+'"'+data(ROOT/m[2])+'"',html)
 assets={str(p.relative_to(ROOT)):data(p) for p in sorted((ROOT/'marks').glob('*.svg'))}
 js='window.REVIEW_ASSETS='+json.dumps(assets)+';\n'+(ROOT/'prototype.js').read_text()
 html=html.replace('<script src="prototype.js"></script>','<script>'+js+'</script>')
 assert 'window.REVIEW_ASSETS=' in html
 assert '<script src=' not in html
 assert '<link rel="stylesheet"' not in html
 output.write_text(html)
 print(f'Wrote standalone review: {output} ({output.stat().st_size:,} bytes)')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('/tmp/darb-althara-review.html'))
 build(parser.parse_args().output)
