"""Phase E: real app wizard, bounded endings, pause/reload and compatibility.
Clock-expiry and old-save scenarios use explicit fixtures; turn completion uses the real engine.
"""
import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/phase-e'
async def setup(page,ending='rounds',limit=1,mode='family',eight=False):
 await page.goto('http://localhost:8000/?speed=80',wait_until='networkidle')
 await page.locator('#wNew').click()
 await page.locator('[data-i="1"] [data-k="ctrl"]').select_option('local')
 for i in [0,1]:
  await page.locator(f'[data-i="{i}"] [data-k="profbtn"]').click();await page.locator(f'.pcard[data-p="{i}"]').click()
 if eight:
  for _ in range(6):await page.locator('#sAdd').click()
 await page.locator('#sStart').click()
 await page.locator('#sSession').select_option(mode);await page.locator('#sEnding').select_option(ending)
 if ending!='dreams':await page.locator('#sLimit').fill(str(limit))
 await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click()
 assert await page.locator('#sLaunch').is_visible()
 await page.locator('#sLaunch').click()
 await page.get_by_role('button',name='ابدأ المباراة 🎲',exact=True).click()
 for _ in range(100):
  await page.wait_for_timeout(30)
  if await page.locator('#roll').is_enabled():return
  if await page.locator('#modal.on #sheet button').count():await page.locator('#modal.on #sheet button').last.click()
 raise AssertionError('No first roll')
async def drive(page):
 for _ in range(1200):
  state=await page.evaluate('({phase:__darb.G.phase,prompt:__darb.G.prompt?.id})')
  if state['phase']=='over':return
  buttons=page.locator('#modal.on #sheet .decision-actions button')
  if await buttons.count():
   try:await buttons.last.click(timeout=1000)
   except Exception:pass
  elif await page.locator('#roll').is_enabled():await page.locator('#roll').click()
  await page.wait_for_timeout(25)
 raise AssertionError('Game did not end')
async def main():
 OUT.mkdir(exist_ok=True);result={'scenarios':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for mode,eight in [('family',False),('extended',True)]:
   c=await b.new_context(viewport={'width':390,'height':844});page=await c.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
   await setup(page,mode=mode,eight=eight)
   assert await page.evaluate('__darb.G.v')==10
   assert await page.evaluate('__darb.G.session.mode')==mode
   await drive(page)
   summary=await page.evaluate('({round:__darb.G.round,reason:__darb.G.summary.reason,turns:__darb.G.players.map(p=>p.turns),count:__darb.G.players.length})')
   assert summary['round']==1 and summary['reason']=='rounds',summary
   assert all(t==1 for t in summary['turns']),summary
   result['scenarios'].append(dict(mode=mode,**summary));await page.wait_for_timeout(300);await page.screenshot(path=str(OUT/f'end-rounds-{summary["count"]}p.png'))
   profiles=await page.evaluate('__darb.G.players.map(p=>p.pk)');settings=await page.evaluate('__darb.G.session')
   await page.get_by_role('button',name='🔁 إعادة المباراة',exact=True).click()
   assert await page.evaluate('__darb.G.session')==settings
   assert await page.evaluate('__darb.G.players.map(p=>p.pk)')==profiles
   assert await page.evaluate('__darb.G.players.every(p=>p.dp===0&&p.turns===0)')
   result['rematch_same_settings_and_professions']='passed'
   await c.close()
  c=await b.new_context(viewport={'width':390,'height':844});page=await c.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)));page.set_default_timeout(15000)
  await setup(page,ending='time',limit=1)
  await page.locator('#menuBtn').click();await page.get_by_role('button',name='⏸ إيقاف مؤقت',exact=True).click()
  await page.evaluate("__darb.G.lm.cafe=0;__darb.G.players[0].cash=100000")
  paused=await page.evaluate('JSON.stringify(__darb.G)');await page.evaluate("__darb.upgradeLm(0,'cafe')")
  assert await page.evaluate('JSON.stringify(__darb.G)')==paused
  result['paused_financial_mutation_rejected']='passed'
  frozen=await page.evaluate('__darb.G.clock.elapsedMs');await page.wait_for_timeout(1200)
  assert await page.evaluate('__darb.G.clock.elapsedMs')==frozen
  await page.reload(wait_until='networkidle')
  assert await page.evaluate('__darb.G.clock.paused')
  assert not await page.locator('#roll').is_enabled()
  await page.locator('#menuBtn').click();await page.get_by_role('button',name='▶ استئناف المباراة',exact=True).click()
  await page.wait_for_function('!document.querySelector("#roll").disabled')
  # Time expires while a mandatory real quiz is open. It cannot end mid-decision.
  await page.evaluate("()=>{window.__quizDone=false;__darb.resolveTile(__darb.G.players[0],'quiz').then(()=>window.__quizDone=true);}")
  await page.wait_for_selector('#sheet.decision-card');prompt=await page.evaluate('__darb.G.prompt.id')
  await page.evaluate('__darb.G.clock.elapsedMs=60001');await page.wait_for_timeout(1100)
  assert await page.evaluate('__darb.G.prompt.id')==prompt
  assert await page.evaluate('__darb.G.phase')!='over'
  await page.locator('#sheet .decision-actions button').last.click()
  await page.wait_for_function('__darb.G.prompt?.kind==="ack"')
  await page.locator('#sheet .decision-actions button').last.click();await page.wait_for_function('window.__quizDone')
  await drive(page)
  assert await page.evaluate('__darb.G.summary.reason')=='time'
  assert await page.evaluate('__darb.G.players.map(p=>p.turns)')==[1,1]
  result['timed_expiry_in_required_decision_then_equal_round']='passed';result['pause_reload_resume']='passed'
  await page.wait_for_timeout(300);await page.screenshot(path=str(OUT/'end-time.png'));await c.close()
  # Historic save fixture: no new ending settings can be added to an old game.
  c=await b.new_context();page=await c.new_page();await setup(page,ending='dreams')
  old=await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6"))');old['v']=9;old.pop('session',None);old.pop('clock',None)
  await page.evaluate('(g)=>localStorage.setItem("darb-althara-v6",JSON.stringify(g))',old);await page.reload(wait_until='networkidle')
  assert await page.evaluate('__darb.G.v')==10 and await page.evaluate('__darb.G.session') is None
  assert await page.evaluate('__darb.G.players.map(p=>p.cash)')==[p['cash'] for p in old['players']]
  result['v9_migrates_with_original_dream_ending']='passed'
  assert await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6-v9-backup")).v')==9
  # Funded fast-track fixture exercises the original dream transaction and finish.
  await page.wait_for_function('!document.querySelector("#roll").disabled')
  await page.evaluate("()=>{const p=__darb.G.players[0];p.fast=true;p.pos=2;p.cash=1e9;p.hap=80;window.__dreamDone=false;__darb.resolveTile(p,'dream').then(()=>window.__dreamDone=true);}")
  await page.wait_for_function('__darb.G.prompt?.kind==="dream"')
  await page.locator('#sheet .decision-actions button').first.click();await page.wait_for_function('window.__dreamDone')
  assert await page.evaluate('__darb.G.phase')=='over' and await page.evaluate('__darb.G.summary.reason')=='dreams'
  result['original_dream_ending']='passed'
  future={**old,'v':999};await page.evaluate('(g)=>localStorage.setItem("darb-althara-v6",JSON.stringify(g))',future);await page.reload(wait_until='networkidle')
  assert not await page.evaluate('!!__darb.G')
  assert await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6")).v')==999
  result['unsupported_future_save_preserved']='passed';await c.close()
  assert not result['errors'],result['errors'];await b.close()
 (OUT/'session-integration-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
