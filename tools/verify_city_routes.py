"""Verify logical rule indices, real road positions, live projects and movement."""
import asyncio,json,math
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/city-routes'
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def main():
 result={'matrix':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:result['errors'].append(str(e)))
  await start_game(page,eight=True)
  # Exact mission order is retained; alternate route cells are real descriptions.
  for track,count,other in [('rat',48,20),('fast',20,48)]:
   if track=='fast':
    await page.evaluate('()=>{__darb.G.players.forEach(p=>{p.fast=true;p.pos=0});document.querySelector("#chips [data-pid=\\\"0\\\"]").click();}')
   state=await page.evaluate('JSON.stringify(__darb.G)')
   assert await page.locator('#board').get_attribute('data-route')==track
   assert await page.locator('[data-tile]').count()==count
   assert await page.locator('.city-route-hint').count()==other
   assert await page.locator('.city-model').count()==8
   positions=await page.locator('[data-tile]').evaluate_all('(es)=>es.map(e=>({id:+e.dataset.tile,x:+e.dataset.routeX,y:+e.dataset.routeY,cx:e.offsetLeft+e.offsetWidth/2,cy:e.offsetTop+e.offsetHeight/2}))')
   positions.sort(key=lambda row:row['id'])
   assert sorted(r['id'] for r in positions)==list(range(count))
   assert len({(round(r['x'],4),round(r['y'],4)) for r in positions})==count
   assert all(abs(r['x']-r['cx'])<1 and abs(r['y']-r['cy'])<1 for r in positions)
   # The closure edge is an ordinary road step, not a jump across the city.
   edges=[math.hypot(positions[(i+1)%count]['x']-r['x'],positions[(i+1)%count]['y']-r['y']) for i,r in enumerate(positions)]
   assert min(edges)>25 and max(edges)<60,edges
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h});await page.locator('[data-camera=reset]').click();await page.wait_for_timeout(100)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    covered=await page.evaluate("""()=>{const tiles=[...document.querySelectorAll('[data-tile],.city-route-hint')].map(e=>({title:e.title,r:e.getBoundingClientRect()}));return [...document.querySelectorAll('.city-model>svg')].flatMap(e=>{const r=e.getBoundingClientRect();return tiles.filter(({r:t})=>t.left+t.width/2>r.left&&t.left+t.width/2<r.right&&t.top+t.height/2>r.top&&t.top+t.height/2<r.bottom).map(t=>({model:e.parentElement.dataset.cityProject,tile:t.title}));});}""")
    assert not covered,covered
    await page.screenshot(path=str(OUT/f'{track}-{w}.png'))
    result['matrix'].append({'track':track,'viewport':[w,h],'active_cells':count,'other_cells':other,'max_step':round(max(edges),2)})
   await page.locator('.city-route-hint').first.focus();await page.keyboard.press('Enter');assert await page.locator('#board-inspector').is_visible();await page.keyboard.press('Escape')
   assert await page.evaluate('JSON.stringify(__darb.G)')==state
   # Every pawn must use the active road's tile coordinates, including wraparound.
   for position in range(count):
    await page.evaluate('(i)=>{__darb.G.players[0].pos=i;document.querySelector("#chips [data-pid=\\\"0\\\"]").click();}',position)
    coords=await page.evaluate('''()=>{const pawn=document.querySelector('.character-pawn[data-player="0"]'),tile=document.querySelector('[data-tile="'+__darb.G.players[0].pos+'"]'),m=new DOMMatrix(pawn.style.transform);return {x:m.m41,y:m.m42,tx:tile.offsetLeft+tile.offsetWidth/2,ty:tile.offsetTop+tile.offsetHeight*.65}}''')
    # At shared start the cluster leader is fanned within the tile; singleton centres exactly.
    assert abs(coords['x']-coords['tx'])<24 and abs(coords['y']-coords['ty'])<20,(position,coords)
   result[track+'_all_positions_follow_road']=count
  # Both roads retain their players, including same logical index on different roads.
  await page.evaluate('()=>{__darb.G.players.forEach((p,i)=>{p.fast=i>=4;p.pos=0});document.getElementById("chips").querySelector(".chip-p").click();}')
  assert await page.locator('.character-pawn').count()==8
  assert await page.locator('.pawn-cluster').count()==2
  await page.evaluate("DarbCamera.inspect('group:fast:0')")
  assert await page.locator('#crowd-list button').count()==4;await page.keyboard.press('Escape')
  await page.screenshot(path=str(OUT/'mixed-tracks.png'));result['mixed_tracks']='8 players, two separate clusters on the two physical roads'
  # Real model -> live inspector -> purchase/development remains the engine's job.
  await page.evaluate("localStorage.removeItem('darb-althara-v6')")
  await start_game(page)
  await page.locator('[data-city-project=hospital]').focus();await page.keyboard.press('Enter');assert await page.locator('#board-info-title').inner_text()=='مستشفى خاص';await page.keyboard.press('Escape')
  frozen=await page.evaluate('JSON.stringify(__darb.G)')
  await page.locator('#camera-help').click();await page.locator('#choose-city-play').click();await page.locator('#city-classic').click();assert await page.locator('.city-route-board').count()==0
  assert await page.evaluate('JSON.stringify(__darb.G)')==frozen
  await page.locator('#camera-help').click();await page.locator('#choose-city-play').click();await page.locator('#city-apply').click();assert await page.locator('.city-route-board').count()==1
  assert await page.evaluate('JSON.stringify(__darb.G)')==frozen
  await page.locator('[data-camera=in]').click();await page.locator('[data-camera=in]').click();await page.locator('[data-camera=in]').click();await page.screenshot(path=str(OUT/'close-view.png'))
  fallback_context=await b.new_context(service_workers='block')
  fallback_page=await fallback_context.new_page();await fallback_page.route('**/architecture-models.webp',lambda route:route.abort())
  await start_game(fallback_page);await fallback_page.wait_for_timeout(250)
  assert await fallback_page.locator('.city-model-placeholder').count()==6
  await fallback_page.locator('[data-city-project=hospital]').focus();await fallback_page.keyboard.press('Enter')
  assert await fallback_page.locator('#board-info-title').inner_text()=='مستشفى خاص'
  await fallback_context.close();result['missing_model_images']='fallback symbols, projects still inspectable'
  # Actual dice movement still advances one logical index at a time on the mapped road.
  await page.evaluate("localStorage.removeItem('darb-althara-v6')")
  await start_game(page)
  await page.evaluate('()=>{__darb.G.players[0].pos=47;document.querySelector("#chips [data-pid=\\\"0\\\"]").click();window.__roadSteps=[];const pawn=document.querySelector(".character-pawn[data-player=\\\"0\\\"]");new MutationObserver(()=>__roadSteps.push(+pawn.dataset.position)).observe(pawn,{attributes:true,attributeFilter:["data-position"]});}')
  await page.locator('#roll').click();await page.wait_for_function('!__darb.G.rolling&&__darb.G.players[0].last&&__darb.G.players[0].pos===(47+__darb.G.players[0].last)%48',timeout=20000)
  steps=await page.evaluate('__roadSteps');unique=[]
  for step in steps:
   if not unique or unique[-1]!=step:unique.append(step)
  if unique and unique[0]==47:unique.pop(0)
  rolled=await page.evaluate('__darb.G.players[0].last');assert unique==list(range(rolled)),(unique,rolled)
  result['actual_dice_steps']=unique;result['rolled_sum']=rolled
  assert not result['errors'],result;await b.close()
 result.update(stable_rule_indices='unchanged, exhaustive positions checked',classic_switch='no match mutation',alternate_route='actual mission descriptions, read-only')
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
