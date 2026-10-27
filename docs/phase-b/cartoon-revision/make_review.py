"""Embed the cartoon comparison assets in one review HTML; never edits game files."""
from pathlib import Path
import argparse, base64, mimetypes, re
ROOT=Path(__file__).resolve().parent

def main(output):
 text=(ROOT/'index.html').read_text()
 def inline(match):
  path=(ROOT/match[1]).resolve()
  return 'url("data:'+mimetypes.guess_type(path.name)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()+'")'
 text=re.sub(r"url\('([^']+)'\)",inline,text)
 output.write_text(text)
 print(f'Exported {output} ({output.stat().st_size:,} bytes)')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('/tmp/darb-althara-cartoon-logos.html'))
 main(parser.parse_args().output)
