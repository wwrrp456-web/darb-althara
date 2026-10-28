"""Acceptance for lightweight pre-rendered landmark/deck sprites, including upgrades and fallback."""
import asyncio,json
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
FILES=['icons-extra-sheet.png','cards-extra-sheet.png','landmarks-sheet.png','landmark-levels-sheet.png','decks-sheet.png']
async def main():
 sizes={n:(ROOT/'art/identity'/n).stat().st_size for n in FILES}
 assert all(n<=600_000 for n in sizes.values()),sizes
 assert sum(sizes.values())<=2_500_000
 assert Image.open(ROOT/'art/identity/landmarks-sheet.png').size==(2048,1024)
 for name in FILES[2:]:
  alpha=Image.open(ROOT/'art/identity'/name).convert('RGBA').getchannel('A');assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>=250,name
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c=await b.new_context(viewport={'width':390,'height':844});page=await c.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await start_game(page)
  await page.wait_for_selector('#board.landmarks-ready.decks-ready')
  assert await page.locator('.landmark-sprite').count()==6 # six normal-track + two fast-track landmarks
  assert await page.locator('.deck-sprite').count()==3
  assert await page.locator('#board .solid,.board-miniature').count()==0
  assert await page.locator('#board *').count()<477
  assert await page.locator('.pawn-layer').evaluate('(e)=>Number(getComputedStyle(e).zIndex)')>await page.locator('.landmark-stand').first.evaluate('(e)=>Number(getComputedStyle(e).zIndex)')
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.locator('.tabletop-stage').scroll_into_view_if_needed()
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   await page.locator('.tabletop-card').screenshot(path=str(ROOT/f'brand/preview-sprites-{w}.png'),style='.bar-actions,.react-fab,#toast{visibility:hidden!important}')
  # Buy with the real engine, then upgrade through its existing public hook.
  await page.evaluate('()=>{__darb.G.players[0].cash=1000000;window.__done=false;__darb.resolveTile(__darb.G.players[0],"lm_hospital").then(()=>__done=true)}')
  await page.locator('.decision-actions button').first.click();await page.wait_for_function('__done')
  await page.locator('.chip-p[data-pid="0"]').evaluate('(e)=>e.click()')
  tile=page.locator('[data-landmark=hospital]');assert await tile.get_attribute('data-level')=='0'
  assert await tile.get_attribute('data-owner-color')==await page.evaluate('__darb.G.players[0].color')
  await page.evaluate('__darb.upgradeLm(0,"hospital")');assert await tile.locator('.landmark-level-art').get_attribute('data-level')=='1'
  # The game allows levels 2-3 only after the owner's fast-track qualification.
  await page.evaluate('__darb.G.players[0].fast=true')
  await page.locator('.chip-p[data-pid="1"]').evaluate('(e)=>e.click()')
  for level in [2,3]:
   await page.evaluate('__darb.upgradeLm(0,"hospital")')
   assert await tile.locator('.landmark-level-art').get_attribute('data-level')==str(level)
  await page.locator('.chip-p[data-pid="0"]').evaluate('(e)=>e.click()')
  assert await page.locator('.landmark-sprite').count()==2
  assert set(await page.locator('[data-landmark]').evaluate_all('(a)=>a.map(e=>e.dataset.landmark)'))=={'tower','airport'}
  await c.close()
  # Eight occupants: the same small number of illustration nodes; no miniature meshes.
  c=await b.new_context(viewport={'width':1180,'height':820});page=await c.new_page();await start_game(page,eight=True)
  await page.evaluate('()=>{__darb.G.players.forEach(p=>p.pos=15);document.querySelector(".chip-p[data-pid=\\\"0\\\"]").click()}')
  assert await page.locator('.character-pawn').count()==8
  assert 'landmark-occupied' in (await page.locator('[data-landmark=hospital]').get_attribute('class'))
  assert await page.locator('#board *').count()<500
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.locator('.tabletop-stage').scroll_into_view_if_needed()
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   await page.locator('.tabletop-card').screenshot(path=str(ROOT/f'brand/preview-sprites-eight-{w}.png'),style='.bar-actions,.react-fab,#toast{visibility:hidden!important}')
  await c.close()
  # Fail the PNG deliberately: original icons must remain usable.
  c=await b.new_context(service_workers='block');page=await c.new_page();await page.route('**/landmarks-sheet.png',lambda route:route.abort())
  await start_game(page);assert await page.locator('#board').evaluate('(e)=>!e.classList.contains("landmarks-ready")')
  assert await page.locator('.tile.landmark .ui-icon').first.is_visible()
  assert not await page.locator('.landmark-stand').first.is_visible()
  assert not errors,errors
  await b.close()
 print(json.dumps({'asset_bytes':sizes,'existing_artwork_bundle_bytes':sum(sizes.values()),'all_eight_buildings':'passed','decks':3,'owner_and_three_upgrade_levels':'passed','two_and_eight_players':'passed','missing_image_fallback':'passed','javascript_errors':errors}))
asyncio.run(main())
