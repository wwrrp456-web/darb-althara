import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright,Page
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/phase-d'; result={'screens':[],'errors':[],'http_errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c=await b.new_context();page=await c.new_page();page.set_default_timeout(15000)
  page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_errors'].append(r.url) if r.status>=400 else None)
  await page.goto('http://localhost:8000/',wait_until='networkidle')
  if await page.locator('#hClose').is_visible():await page.locator('#hClose').click()
  for w,h in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(100)
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   await page.screenshot(path=str(OUT/f'home-{w}.png'),full_page=True)
  await c.close()
  for count in (2,8):
   c=await b.new_context();page=await c.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
   await start_game(page,eight=count==8)
   for w,h in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
    await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(200)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    row=await page.evaluate('''()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return {stage:r('.tabletop-stage').height,dockBottom:r('.bar-actions').bottom,small:[...document.querySelectorAll('button,select')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden').filter(e=>{const b=e.getBoundingClientRect();return b.width<47.9||b.height<47.9}).map(e=>e.id||e.textContent)}}''')
    assert row['stage']>=180 and row['dockBottom']<=h+.5 and not row['small'],row
    result['screens'].append(dict(players=count,width=w,height=h,**row));await page.screenshot(path=str(OUT/f'play-{count}p-{w}.png'))
   if count==2:
    await page.set_viewport_size({'width':390,'height':844})
    await page.evaluate("()=>{__darb.G.players[0].cash=300000;window.__offerDone=false;__darb.resolveTile(__darb.G.players[0],'lm_cafe').then(()=>window.__offerDone=true);}")
    await page.wait_for_selector('#sheet.decision-card')
    cash=await page.evaluate('__darb.G.players[0].cash');down=await page.evaluate('__darb.G.prompt.data.down')
    await page.wait_for_timeout(350)
    await page.screenshot(path=str(OUT/'investment-decision.png'))
    await page.locator('#sheet .decision-actions button').first.click()
    await page.wait_for_function('window.__offerDone')
    # Direct rule fixture bypasses the turn loop's final render; use its existing view action.
    await page.locator('#chips [data-pid="0"]').evaluate('(e)=>e.click()')
    assert await page.evaluate('__darb.G.players[0].cash')==cash-down
    before=await page.evaluate('JSON.stringify(__darb.G)')
    await page.locator('#mini').click()
    assert await page.locator('.financial-recap').count()==1
    values=await page.locator('.financial-recap').inner_text()
    assert 'النقد' in values and 'الدخل التلقائي' in values,values
    assert await page.evaluate('JSON.stringify(__darb.G)')==before
    await page.wait_for_timeout(350)
    await page.screenshot(path=str(OUT/'actual-financial-change.png'))
    await page.locator('#tabs [data-t=play]').click()
    result['actual_purchase_and_readonly_recap']='passed'
   # Exercise presentation guidance without adding prompts or touching G.
   await page.set_viewport_size({'width':390,'height':844})
   before=await page.evaluate('JSON.stringify(__darb.G)')
   await page.evaluate('''()=>{const s=document.createElement('section');s.id='guide-test';s.innerHTML='<h2>قرار إرشادي</h2><p>المحتوى المالي</p><div class="row"><button>تابع</button></div>';document.body.append(s);DarbIdentity.decorateCard(s,{kind:'guidance-fixture'});}''')
   assert await page.locator('#guide-test details').evaluate('(e)=>e.open')
   await page.locator('#guide-test summary').click();assert not await page.locator('#guide-test details').evaluate('(e)=>e.open')
   assert await page.evaluate('JSON.stringify(__darb.G)')==before
   await page.evaluate('document.querySelector("#guide-test").remove()')
   await c.close()
  assert not result['errors'] and not result['http_errors'],result
  await b.close()
 (OUT/'identity-layout-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('passed: 5 home + 10 play views, accessible reversible guidance')
asyncio.run(main())
