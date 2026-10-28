"""Table composition: stable deck names, contained project markers and readable close view.
Project state is inspected through real controls; all financial values stay in the engine.
"""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/table-finish'
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def main():
 OUT.mkdir(exist_ok=True);result={'matrix':[],'errors':[],'http_errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for count in [2,8]:
   c=await b.new_context();page=await c.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_errors'].append(r.url) if r.status>=400 else None)
   await start_game(page,eight=count==8);await page.wait_for_selector('#board.landmarks-ready.decks-ready')
   baseline=await page.evaluate('JSON.stringify(__darb.G)')
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h});await page.locator('[data-camera=reset]').click();await page.wait_for_timeout(250)
    row=await page.evaluate('''()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return {overflow:document.documentElement.scrollWidth>innerWidth,stageHeight:r('.tabletop-stage').height,rackBottom:r('#board-deck-rack').bottom,stageTop:r('.tabletop-stage').top,dockBottom:r('.bar-actions').bottom,deckLabels:[...document.querySelectorAll('#board-deck-rack b')].map(e=>({text:e.textContent,clipped:e.scrollWidth>e.clientWidth||e.scrollHeight>e.clientHeight})),oversizedMarkers:[...document.querySelectorAll('.landmark-stand')].filter(e=>e.offsetWidth>e.parentElement.clientWidth||e.offsetHeight>e.parentElement.clientHeight).length};}''')
    assert not row['overflow'] and row['stageHeight']>=180 and row['dockBottom']<=h+.5,row
    assert row['rackBottom']<=row['stageTop']+.5 and not any(x['clipped'] for x in row['deckLabels']),row
    assert not row['oversizedMarkers'],row
    assert await page.locator('.landmark-stand .miniature-hit').count()==0
    result['matrix'].append(dict(players=count,width=w,height=h,**row));await page.screenshot(path=str(OUT/f'{count}p-{w}.png'))
   for kind in ['deal','family','quiz']:
    await page.locator(f'#board-deck-rack [data-deck={kind}]').click();assert await page.locator('#board-inspector').is_visible();await page.keyboard.press('Escape')
   assert await page.evaluate('JSON.stringify(__darb.G)')==baseline
   await page.locator('#board-projects-open').click();assert await page.locator('#project-list button').count()==6
   await page.locator('#project-list [data-project=hospital]').click();assert await page.locator('#board-info-title').inner_text()=='مستشفى خاص';await page.keyboard.press('Escape')
   assert await page.evaluate('document.activeElement.id')=='board-projects-open'
   assert await page.evaluate('JSON.stringify(__darb.G)')==baseline
   await page.set_viewport_size({'width':390,'height':844});await page.locator('#board-projects-open').click();await page.wait_for_timeout(350);await page.screenshot(path=str(OUT/f'projects-{count}p.png'));await page.keyboard.press('Escape')
   # Inspect close-up local layout on every tile, not only the visible camera portion.
   await page.locator('[data-camera=reset]').click()
   for _ in range(9):await page.locator('[data-camera=in]').click()
   close=await page.evaluate('''()=>({readable:document.querySelector('#board').classList.contains('camera-readable'),bad:[...document.querySelectorAll('.tile-name')].filter(e=>{const t=e.parentElement;return e.scrollWidth>e.clientWidth+1||e.offsetTop+e.offsetHeight>t.clientHeight+1}).map(e=>({text:e.textContent,w:e.clientWidth,scroll:e.scrollWidth,top:e.offsetTop,h:e.offsetHeight,tile:e.parentElement.clientHeight}))})''')
   assert close['readable'] and not close['bad'],close
   # Pan the same project edge the owner highlighted into the centre using the camera gesture.
   tile=page.locator('[data-landmark=uni]');r=await tile.bounding_box();scene=await page.locator('.tabletop-stage').bounding_box();x=scene['x']+scene['width']/2;y=scene['y']+scene['height']/2
   dx=x-(r['x']+r['width']/2);dy=y-(r['y']+r['height']/2)
   await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+dx,y+dy,steps=20);await page.mouse.up();await page.wait_for_timeout(300);await page.screenshot(path=str(OUT/f'close-{count}p.png'))
   assert await page.evaluate('JSON.stringify(__darb.G)')==baseline
   if count==8:
    await page.evaluate('__darb.G.players.forEach(p=>{p.fast=true;p.pos=0})');await page.locator('#chips [data-pid="0"]').evaluate('(e)=>e.click()');fast=await page.evaluate('JSON.stringify(__darb.G)')
    await page.locator('#board-projects-open').click();assert await page.locator('#project-list button').count()==2;await page.keyboard.press('Escape');assert await page.evaluate('JSON.stringify(__darb.G)')==fast
    await page.locator('[data-camera=reset]').click();await page.screenshot(path=str(OUT/'fast-8p.png'))
   await c.close()
  assert not result['errors'] and not result['http_errors'],result;await b.close()
 result.update(deck_and_project_inspection='read-only',fast_track_catalog='2 projects',close_labels='no ellipsis or overflow at readable zoom',project_markers='contained, no oversized independent hit planes')
 (OUT/'composition-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
