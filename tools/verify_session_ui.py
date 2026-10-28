import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_sessions import setup
OUT=Path(__file__).resolve().parents[1]/'docs/phase-e'
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def main():
 result={'checks':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)))
  await page.goto('http://localhost:8000/',wait_until='networkidle');await page.locator('#wNew').click()
  async def matrix(stage):
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(300)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert await page.locator('#sheet').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
    for button in await page.locator('#sheet button,#sheet select,#sheet input:not([type=hidden])').all():
     if not await button.is_visible():continue
     assert await button.evaluate('(e)=>{const r=e.getBoundingClientRect();return r.width>=47.9&&r.height>=47.9}')
    for _ in range(8):
     await page.keyboard.press('Tab');assert await page.locator('#sheet').evaluate('(e)=>e.contains(document.activeElement)')
    await page.locator('#sheet').evaluate('(e)=>e.scrollTop=0')
    await page.screenshot(path=str(OUT/f'setup-{stage}-{w}.png'));result['checks'].append([stage,w,h])
  await matrix('players');await page.locator('#sStart').click();await page.locator('#sEnding').select_option('time')
  await matrix('session')
  # Invalid fractional/empty/bounds values cannot reach the review or start a game.
  for bad in ['', '0','1.5','241']:
   await page.locator('#sEnding').select_option('time');await page.locator('#sLimit').fill(bad);await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click()
   assert await page.locator('#sSessionError').inner_text()
   assert not await page.evaluate('!!__darb.G')
  await page.locator('#sEnding').select_option('rounds');await page.locator('#sLimit').fill('2');await page.locator('#sSession').select_option('extended');await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click()
  await matrix('review');await page.get_by_role('button',name='تعديل الجلسة',exact=True).click()
  assert await page.locator('#sSession').input_value()=='extended'
  assert await page.locator('#sEnding').input_value()=='rounds' and await page.locator('#sLimit').input_value()=='2'
  await page.set_viewport_size({'width':390,'height':844});await setup(page,ending='time',limit=30)
  await page.wait_for_timeout(350);assert 'متبقٍ' in await page.locator('#turn-readout').inner_text()
  await page.screenshot(path=str(OUT/'timed-play.png'))
  await page.locator('#menuBtn').click();await page.get_by_role('button',name='⏸ إيقاف مؤقت',exact=True).click();await page.wait_for_timeout(350)
  assert not await page.locator('#roll').is_enabled();await page.screenshot(path=str(OUT/'paused-play.png'))
  result['timer_and_pause_views']='passed'
  assert not result['errors'],result['errors'];await b.close()
 (OUT/'setup-ui-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('passed: 15 setup layouts, focus trap, bounds and back navigation')
if __name__=='__main__':asyncio.run(main())
