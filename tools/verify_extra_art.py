"""Additional art: semantic icons, unchanged avatars, local-file support and cache delivery."""
import asyncio,json,re
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright, Error
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
async def verify():
 image=Image.open(ROOT/'art/identity/icons-extra-sheet.png');assert image.size==(1250,750)
 assert (ROOT/'art/identity/icons-extra-sheet.png').stat().st_size<=600_000
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  file_result="not run"
  for origin in ['http://localhost:8000/',(ROOT/'index.html').as_uri()]:
   c=await b.new_context(viewport={'width':390,'height':844});page=await c.new_page();errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   try:await page.goto(origin,wait_until='networkidle')
   except Error as error:
    if origin.startswith('file:') and 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(error):
     file_result='blocked by managed Chromium policy (ERR_BLOCKED_BY_ADMINISTRATOR)';await c.close();continue
    raise
   result=await page.evaluate('''()=>{const box=document.createElement('div');box.textContent='💹 🕵️ 🚔 🏗️ 🐀 🚀 😄 🙂 😐 😟 😵 ☰';document.body.append(box);DarbIdentity.hydrate(box);const a=[...box.querySelectorAll('.illustrated-icon')].map(e=>e.dataset.icon);box.remove();return a}''')
   assert result==['investor','audit','jail','upgrade','rat-race','fast-track','mood-great','mood-good','mood-neutral','mood-worried','mood-exhausted','more'],result
   assert await page.evaluate('''()=>{const e=document.createElement('span');e.className='identity-avatar-value';e.textContent='🚀';document.body.append(e);DarbIdentity.hydrate(e);const ok=!!e.querySelector('.identity-avatar');e.remove();return ok}''')
   assert await page.locator('#wNew').is_visible()
   if origin.startswith('http'):
    await start_game(page)
    assert await page.locator('[data-icon=investor]').count()>0
    assert await page.locator('#roll [data-icon=two-dice]').count()==1
    assert await page.locator('.identity-additional[data-icon=rat-race]').count()>0
    await page.screenshot(path=str(ROOT/'brand/preview-extra-icons-mobile.png'))
    await page.set_viewport_size({'width':1180,'height':820});await page.screenshot(path=str(ROOT/'brand/preview-extra-icons-desktop.png'))
   else:
    await page.locator('#wNew').click();await page.locator('[data-i="0"] [data-k="profbtn"]').click()
    assert await page.locator('.pcard img').count()==14
    file_result='passed'
   assert not errors,(origin,errors)
   await c.close()
  await b.close()
 print(json.dumps({'semantic_icons':12,'rocket_avatar_preserved':True,'http':'passed','file':file_result,'icon_png_bytes':(ROOT/'art/identity/icons-extra-sheet.png').stat().st_size}))
asyncio.run(verify())
