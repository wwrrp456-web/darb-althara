"""Render identity exports using a server at http://localhost:8000 and system Chromium."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
r=Path(__file__).resolve().parents[1]
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  context=await browser.new_context(device_scale_factor=1)
  page=await context.new_page()
  mark=(r/'icons/brand-mark.svg').read_text()
  for size,name in [(64,'favicon-64.png'),(180,'apple-touch-icon.png'),(192,'icon-192.png'),(512,'icon-512.png'),(512,'maskable-512.png')]:
   await page.set_viewport_size({'width':size,'height':size})
   svg=mark
   if name.startswith('maskable'):
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" fill="#124c40"/><g transform="translate(12.8 12.8) scale(.8)">'+mark.split('>',1)[1].rsplit('</svg>',1)[0]+'</g></svg>'
   await page.set_content('<style>html,body{margin:0;background:transparent}svg{width:100vw;height:100vh;display:block}</style>'+svg)
   await page.screenshot(path=str(r/'icons'/name),omit_background=True)
  for size,name in [({'width':1200,'height':630},'social-card.png'),({'width':1080,'height':1080},'social-square.png')]:
   await page.set_viewport_size(size)
   await page.goto('http://localhost:8000/brand/social.html',wait_until='networkidle')
   await page.evaluate('document.fonts.ready')
   await page.screenshot(path=str(r/'brand'/name))
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.goto('http://localhost:8000/',wait_until='networkidle')
  if await page.locator('#hClose').is_visible():await page.locator('#hClose').click()
  await page.screenshot(path=str(r/'brand/preview-home.png'),full_page=True)
  await page.set_viewport_size({'width':390,'height':844})
  await page.wait_for_timeout(250)
  await page.screenshot(path=str(r/'brand/preview-mobile.png'),full_page=True)
  await page.goto('http://localhost:8000/brand/',wait_until='networkidle')
  await page.pdf(path=str(r/'brand/brand-guide.pdf'),format='A4',print_background=True,margin={'top':'14mm','bottom':'14mm','left':'12mm','right':'12mm'})
  await browser.close()
asyncio.run(main())
