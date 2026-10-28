"""Phase C: real app layout, read-only group selection, focus and camera recovery.
Serve repository on localhost:8000. Writes artifacts only to docs/phase-c.
"""
import argparse,asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,default=Path(__file__).resolve().parents[1]/'docs/phase-c');OUT=parser.parse_args().artifacts
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 result={'matrix':[],'errors':[],'http_errors':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  result['browser']=browser.version
  for count in (2,8):
   context=await browser.new_context(viewport={'width':390,'height':844})
   page=await context.new_page()
   page.on('pageerror',lambda e:result['errors'].append(str(e)))
   page.on('response',lambda r:result['http_errors'].append(r.url) if r.status>=400 else None)
   await start_game(page,eight=count==8)
   await page.wait_for_selector('#board.landmarks-ready.decks-ready')
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h})
    await page.wait_for_timeout(180)
    row=await page.evaluate('''() => {
      const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}};
      const controls=[...document.querySelectorAll('button,select')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden');
      return {overflow:document.documentElement.scrollWidth>innerWidth,stage:box('.tabletop-stage'),dock:box('.bar-actions'),toast:box('#toast'),
       smallControls:controls.filter(e=>{const r=e.getBoundingClientRect();return r.width<47.9||r.height<47.9}).map(e=>e.id||e.textContent),
       hitBar:[...document.querySelectorAll('#board .tile')].filter(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('.bar-actions')}).length};}''')
    row.update(width=w,height=h,players=count)
    assert not row['overflow'] and not row['smallControls'],row
    assert row['stage']['h']>=180,row
    assert row['stage']['bottom']<=row['toast']['y']<=row['dock']['y'],row
    assert row['dock']['bottom']<=h+.5,row
    assert row['hitBar']==0,row
    result['matrix'].append(row)
    await page.locator('#roll').evaluate('(e)=>e.blur()')
    await page.screenshot(path=str(OUT/f'{count}p-{w}x{h}.png'))
   await page.set_viewport_size({'width':390,'height':844})
   before=await page.evaluate('JSON.stringify(__darb.G)')
   for i in range(count):
    await page.locator('#board-players').click()
    assert await page.locator('#crowd-list button').count()==count
    await page.locator(f'#crowd-list [data-player="{i}"]').click()
    assert await page.locator('#board-inspector').is_visible()
    for _ in range(5):
     await page.keyboard.press('Tab')
     assert await page.evaluate('document.querySelector("#board-inspector").contains(document.activeElement)')
    await page.keyboard.press('Escape')
   assert await page.evaluate('JSON.stringify(__darb.G)')==before
   for selected in [1,0]:
    await page.locator('#board-players').click()
    await page.locator(f'#crowd-list [data-player="{selected}"]').click()
    await page.locator('#view-player-board').click()
    expected='مريم' if selected else 'محسن'
    assert expected in await page.locator('#current-location').get_attribute('aria-label')
   assert await page.evaluate('JSON.stringify(__darb.G)')==before
   if count==8:
    await page.locator('#board-players').click()
    await page.screenshot(path=str(OUT/'eight-player-picker.png'))
    await page.keyboard.press('Escape')
   await page.locator('#sheetBtn').focus();await page.keyboard.press('Enter')
   await page.wait_for_function('document.querySelector("#sheet").contains(document.activeElement)')
   assert await page.locator('.wrap').evaluate('(e)=>e.inert')
   assert await page.locator('#modal').get_attribute('role')=='dialog'
   for _ in range(10):
    await page.keyboard.press('Tab')
    assert await page.evaluate('document.querySelector("#sheet").contains(document.activeElement)')
   await page.wait_for_timeout(350)
   await page.screenshot(path=str(OUT/f'financial-{count}p.png'))
   await page.keyboard.press('Escape')
   await page.wait_for_function('document.activeElement.id==="sheetBtn"')
   assert not await page.locator('.wrap').evaluate('(e)=>e.inert')
   assert await page.evaluate('JSON.stringify(__darb.G)')==before
   # A real required game choice cannot be dismissed by Escape or background clicks.
   await page.evaluate('()=>{window.__layoutQuizDone=false;__darb.resolveTile(__darb.G.players[0],"quiz").then(()=>__layoutQuizDone=true)}')
   await page.wait_for_selector('#modal.on')
   prompt=await page.evaluate('__darb.G.prompt.id')
   await page.keyboard.press('Escape')
   assert await page.locator('#modal.on').is_visible()
   assert await page.evaluate('__darb.G.prompt.id')==prompt
   await page.locator('#sheet .row button').first.click()
   await page.wait_for_function('__darb.G.prompt?.kind==="ack"')
   # Two events on one stale confirmation must not answer a later prompt.
   await page.locator('#sheet .row button').first.evaluate('(e)=>{e.click();e.click()}')
   await page.wait_for_function('__layoutQuizDone')
   # Measured fit and manual/automatic camera recovery, using a deterministic view fixture.
   for _ in range(5):await page.locator('[data-camera=in]').click()
   stage=page.locator('.tabletop-stage');rect=await stage.bounding_box()
   await page.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']/2)
   await page.mouse.down();await page.mouse.move(rect['x']+rect['width']/2+45,rect['y']+rect['height']/2+30,steps=5);await page.mouse.up()
   assert await stage.get_attribute('data-follow')=='false'
   await page.locator('[data-camera=follow]').click()
   await page.wait_for_timeout(900)
   previous=await page.locator('.tabletop-camera-world').get_attribute('style')
   await page.evaluate('()=>{__darb.G.players[0].pos=12;document.querySelector(".chip-p[data-pid=\\"0\\"]").click()}')
   await page.wait_for_timeout(550)
   current=await page.locator('.tabletop-camera-world').get_attribute('style')
   assert current!=previous,(previous,current)
   assert await stage.get_attribute('data-follow')=='true'
   # Camera and viewport changes must never change the rest of game state.
   for w,h in [(1180,820),(768,1024),(390,844)]:
    await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(100)
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
   if count==8:
    await page.evaluate('()=>{__darb.G.players.forEach(p=>{p.fast=true;p.pos=0});document.querySelector(".chip-p[data-pid=\\"0\\"]").click()}')
    assert await page.locator('#board .tile').count()==20
    for w,h in [(390,844),(1180,820)]:
     await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(180)
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
     await page.screenshot(path=str(OUT/f'fast-eight-{w}.png'))
   await context.close()
  assert not result['errors'] and not result['http_errors'],result
  result.update(read_only_all_players='passed; including board selection',financial_focus_trap_restore_and_background_inert='passed',mandatory_choice_escape_and_duplicate_confirmation='passed',zoomed_follow_after_manual_recovery='passed (position fixture)',rotations='passed (viewport simulation)')
  await browser.close()
 (OUT/'layout-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'matrix_cases':len(result['matrix']),**{k:v for k,v in result.items() if k not in ('matrix',)}},ensure_ascii=False,indent=2))
asyncio.run(asyncio.wait_for(main(),timeout=180))
