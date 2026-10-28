"""Locate each project using native UI without changing game state."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/project-location'
async def main():
 OUT.mkdir(exist_ok=True);result={'cases':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await b.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)))
  await start_game(page,eight=True)
  for track in ['rat','fast']:
   if track=='fast':
    await page.evaluate('__darb.G.players.forEach(p=>{p.fast=true;p.pos=0})');await page.locator('#chips [data-pid="0"]').evaluate('(e)=>e.click()')
   baseline=await page.evaluate('JSON.stringify(__darb.G)')
   for width,height in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
    await page.set_viewport_size({'width':width,'height':height});await page.locator('[data-camera=reset]').click()
    keys=await page.locator('[data-landmark]').evaluate_all('(es)=>es.map(e=>e.dataset.landmark)')
    for key in keys:
     await page.locator('#board-projects-open').click();await page.locator(f'#project-list [data-project={key}]').click()
     locate=page.locator('#locate-project');assert await locate.is_visible()
     # Keyboard activation, including stable focus on the scene after dialog close.
     await locate.focus();await page.keyboard.press('Enter');await page.wait_for_timeout(60)
     assert not await page.locator('#board-inspector').is_visible()
     selected=page.locator('.project-located');assert await selected.count()==1
     rect=await selected.bounding_box();scene=await page.locator('.tabletop-stage').bounding_box()
     assert abs(rect['x']+rect['width']/2-scene['x']-scene['width']/2)<2,(key,rect,scene)
     assert abs(rect['y']+rect['height']/2-scene['y']-scene['height']/2)<2,(key,rect,scene)
     assert await selected.get_attribute('data-landmark')==key
     assert await page.evaluate('document.activeElement.matches(".tabletop-stage")')
     assert await page.locator('.tabletop-stage').get_attribute('data-follow')=='false'
     assert await page.evaluate('JSON.stringify(__darb.G)')==baseline
     result['cases'].append({'track':track,'viewport':[width,height],'project':key,'centered':True,'state_unchanged':True})
    if width==390:await page.screenshot(path=str(OUT/f'{track}-located.png'))
    await page.locator('[data-camera=reset]').click();assert await page.locator('.project-located').count()==0
    assert await page.locator('.tabletop-stage').get_attribute('data-zoom')=='100'
   await page.locator('#board-deck-rack [data-deck=quiz]').click();assert not await page.locator('#locate-project').is_visible();await page.keyboard.press('Escape')
  # A pending decision must block programmatic camera inspection too.
  await page.evaluate("()=>{__darb.resolveTile(__darb.G.players[0],'quiz');}")
  await page.evaluate("DarbCamera.inspect('lm_tower')");assert not await page.locator('#board-inspector').is_visible()
  assert not result['errors'],result
  await b.close()
 result.update(keyboard_focus='scene after locating',reset='selection cleared, overview restored',decks='locate action hidden',decision_priority='preserved')
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'cases':len(result['cases']),'errors':result['errors']}))
if __name__=='__main__':asyncio.run(main())
