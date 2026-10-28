"""New board transactions, real wraparound rolls, invalid saves and artwork fallback."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/ten-city-boards'
async def main():
 result={};errors=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  c=await b.new_context();await c.add_init_script("if(!localStorage.getItem('darb-city-view'))localStorage.setItem('darb-city-view','ivory')")
  page=await c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));await start_game(page)
  frozen=await page.evaluate('JSON.stringify(__darb.G)');await page.locator('[data-city-project=hospital]').focus();await page.keyboard.press('Enter');assert await page.locator('#board-info-title').inner_text()=='مستشفى خاص';await page.keyboard.press('Escape');assert await page.evaluate('JSON.stringify(__darb.G)')==frozen
  await page.evaluate('()=>{__darb.G.players[0].cash=1000000;window.__done=false;__darb.resolveTile(__darb.G.players[0],"lm_hospital").then(()=>__done=true)}')
  await page.locator('.decision-actions button').first.click();await page.wait_for_function('__done')
  for level in [1,2,3]:
   if level==2:await page.evaluate('__darb.G.players[0].fast=true')
   await page.evaluate('__darb.upgradeLm(0,"hospital")');await page.locator('.chip-p').nth(1).click()
   model=page.locator('[data-city-project=hospital]');assert 'city-model-owned' in await model.get_attribute('class');assert await model.locator('.city-model-level').inner_text()==str(level)
   assert await page.evaluate('__darb.G.players[0].assets.find(a=>a.lm==="hospital").inc')>1200
  result['read_only_model_and_real_purchase_levels_1_to_3']='passed';await c.close()
  for fast in [False,True]:
   c=await b.new_context();await c.add_init_script("localStorage.setItem('darb-city-view','rings')");page=await c.new_page();await start_game(page)
   await page.evaluate('''fast=>{const p=__darb.G.players[0];p.fast=fast;p.pos=(fast?__darb.G.board.fast:__darb.G.board.rat).length-1;document.querySelector('.chip-p').click();window.__steps=[];new MutationObserver(()=>__steps.push(+document.querySelector('.character-pawn[data-player="0"]').dataset.position)).observe(document.querySelector('.character-pawn[data-player="0"]'),{attributes:true,attributeFilter:['data-position']});}''',fast)
   await page.locator('#roll').click();await page.wait_for_function('''()=>{const p=__darb.G.players[0],n=(p.fast?__darb.G.board.fast:__darb.G.board.rat).length;return !__darb.G.rolling&&p.last&&p.pos===(n-1+p.last)%n}''',timeout=20000)
   roll=await page.evaluate('__darb.G.players[0].last');steps=await page.evaluate('__steps');unique=[]
   for step in steps:
    if not unique or unique[-1]!=step:unique.append(step)
   n=await page.evaluate('( __darb.G.players[0].fast?__darb.G.board.fast:__darb.G.board.rat).length')
   if unique and unique[0]==n-1:unique.pop(0)
   assert unique==[i%n for i in range(roll)],(fast,roll,unique)
   result['fast_roll' if fast else 'rat_roll']={'sum':roll,'visited':unique,'length':n};await c.close()
  c=await b.new_context(service_workers='block');page=await c.new_page();await page.route('**/playable-cities.webp',lambda r:r.abort());await start_game(page);await page.wait_for_timeout(200)
  assert await page.locator('.city-reference-board').count()==0 and await page.locator('[data-tile]').count()>0
  assert await page.locator('#dice').count()==1;result['missing_art_fallback']='live grid, original missions and dice retained';await c.close()
  c=await b.new_context();page=await c.new_page();await start_game(page)
  await page.evaluate("()=>{const g=JSON.parse(localStorage.getItem('darb-althara-v6'));g.board.id='invalid-city';localStorage.setItem('darb-althara-v6',JSON.stringify(g))}")
  await page.reload(wait_until='networkidle');assert await page.evaluate('!__darb.G');assert await page.evaluate("JSON.parse(localStorage.getItem('darb-althara-v6')).board.id")=='invalid-city'
  result['invalid_save']='rejected without deleting stored data';await c.close();await b.close()
 assert not errors,errors
 result['errors']=errors;(OUT/'match-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':asyncio.run(main())
