"""Export approved logo sizes, safe-area icons and share art using Chromium.
Serve the repository on localhost:8000 first. No game state is involved.
"""
import asyncio,base64
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page()
  await page.set_viewport_size({'width':512,'height':512})
  await page.set_content('<style>body{margin:0;background:transparent}img{display:block;width:512px;height:512px}</style><img src="http://localhost:8000/docs/phase-b/selected-logo/symbol.png">')
  await page.locator('img').evaluate('(e)=>e.decode()')
  await page.screenshot(path=str(ROOT/'icons/logo-symbol.png'),omit_background=True)
  encoded=base64.b64encode((ROOT/'icons/logo-symbol.png').read_bytes()).decode()
  import re,shutil
  for name in ['horizontal','horizontal-dark','vertical']:
   source=(ROOT/'docs/phase-b/selected-logo'/f'{name}.svg').read_text()
   source=re.sub(r'data:image/png;base64,[^"]+', 'data:image/png;base64,'+encoded,source)
   (ROOT/'icons'/f'logo-{name}.svg').write_text(source)
   shutil.copyfile(ROOT/'docs/phase-b/selected-logo'/f'{name}.png',ROOT/'icons'/f'logo-{name}.png')
  shutil.copyfile(ROOT/'icons/logo-horizontal.svg',ROOT/'icons/brand-lockup.svg')
  for name,size,pad,bg in [('maskable-512.png',512,110,'#f8f5ed'),('apple-touch-icon.png',180,25,'#f8f5ed')]:
   await page.set_viewport_size({'width':size,'height':size})
   await page.set_content(f'<style>body{{margin:0;background:{bg};padding:{pad}px;box-sizing:border-box}}img{{display:block;width:100%}}</style><img src="http://localhost:8000/icons/icon-512.png">')
   await page.locator('img').evaluate('(e)=>e.decode()');await page.screenshot(path=str(ROOT/'icons'/name))
  for name,w,h in [('social-card.png',1200,630),('social-square.png',1080,1080)]:
   await page.set_viewport_size({'width':w,'height':h});await page.goto('http://localhost:8000/brand/social.html',wait_until='networkidle');await page.evaluate('document.fonts.ready');await page.screenshot(path=str(ROOT/'brand'/name))
  await page.goto('http://localhost:8000/brand/',wait_until='networkidle');await page.evaluate('document.fonts.ready');await page.pdf(path=str(ROOT/'brand/brand-guide.pdf'),format='A4',print_background=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
