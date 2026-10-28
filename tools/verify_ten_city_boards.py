"""Exercise each city as a distinct saved match board, across five viewport sizes."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/ten-city-boards'
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def main():
 result={'cities':[],'errors':[],'http_errors':[]};tasks={}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for index,key in enumerate(['architecture','cartoon','ivory','harbor','rings','paper','strategy','districts','night','crystal']):
   c=await b.new_context(viewport={'width':1180,'height':820})
   await c.add_init_script("if(!localStorage.getItem('darb-city-view'))localStorage.setItem('darb-city-view',"+json.dumps(key)+");")
   page=await c.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_errors'].append(r.url) if r.status>=400 else None)
   await start_game(page,eight=True)
   d=await page.evaluate('DarbCityScenes.defs.find(d=>d.id===__darb.G.board.id)');board=await page.evaluate('__darb.G.board')
   assert d['id']==key and await page.evaluate('__darb.G.v')==11
   assert board['rat'].count('payday')==2 and board['fast'].count('payday')==2 and board['fast'].count('dream')==3
   assert len(board['rat'])==len(d['slots']) and len(board['fast'])==len(d['fastSlots'])
   assert len(set(map(tuple,d['slots'])))==len(d['slots'])
   assert await page.locator('#choose-city-play').is_disabled()
   assert await page.locator('.city-scene-art image').get_attribute('href')=='art/cities/playable-cities.webp'
   assert await page.locator('.city-roads').count()==0
   assert await page.locator('.city-model').count()==sum(k.startswith('lm_') for k in board['rat'])
   row={'id':key,'rat':len(board['rat']),'fast':len(board['fast']),'sizes':[]};tasks[key]={}
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h});await page.locator('[data-camera=reset]').click();await page.wait_for_timeout(50)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert await page.locator('.city-dice #dice').is_visible()
    box=await page.locator('.bar-actions').bounding_box();assert box['y']+box['height']<=h+1
    if w in [390,1180]:await page.screenshot(path=str(OUT/f'{index+1:02d}-{w}.png'))
    row['sizes'].append([w,h])
   for fast,track in [(False,'rat'),(True,'fast')]:
    await page.evaluate('(fast)=>{__darb.G.players.forEach(p=>{p.fast=fast;p.pos=0});document.querySelector(".chip-p").click();}',fast)
    assert await page.locator('[data-tile]').count()==len(board[track])
    tasks[key][track]=await page.locator('[data-tile]').evaluate_all('(els)=>els.sort((a,b)=>+a.dataset.tile-b.dataset.tile).map(e=>({title:e.title}))')
    for pos in range(len(board[track])):
     await page.evaluate('(i)=>{__darb.G.players[0].pos=i;document.querySelector(".chip-p").click();}',pos)
     point=await page.evaluate("""()=>{const p=document.querySelector('.character-pawn[data-player="0"]'),t=document.querySelector('[data-tile="'+__darb.G.players[0].pos+'"]'),m=new DOMMatrix(p.style.transform);return {x:m.m41,y:m.m42,tx:t.offsetLeft+t.offsetWidth/2,ty:t.offsetTop+t.offsetHeight*.65}}""")
     assert abs(point['x']-point['tx'])<24 and abs(point['y']-point['ty'])<20,(key,pos,point)
   await page.evaluate('()=>{__darb.G.players.forEach((p,i)=>{p.fast=i>=4;p.pos=0});document.querySelector(".chip-p").click();}')
   assert await page.locator('.pawn-cluster').count()==(1 if d['sharedRoad'] else 2)
   # The saved board snapshot, not a changed local preference, survives reopening.
   await page.evaluate("localStorage.setItem('darb-city-view','night')")
   await page.reload(wait_until='networkidle')
   assert await page.evaluate('__darb.G.board')==board
   assert await page.locator('#board').get_attribute('data-scene')==key
   await page.evaluate('navigator.serviceWorker.ready.then(()=>true)');await c.set_offline(True);await page.reload(wait_until='domcontentloaded');await page.wait_for_selector('.city-scene-art')
   assert await page.evaluate("async()=>(await(await fetch('art/cities/playable-cities.webp')).blob()).size")==448734
   row['save_reload_offline']='passed';result['cities'].append(row);print(key,row['rat'],row['fast'],flush=True);await c.close()
  await b.close()
 assert not result['errors'] and not result['http_errors'],result
 result['positions_checked']=sum(r['rat']+r['fast'] for r in result['cities'])
 (OUT/'tasks.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':asyncio.run(main())
