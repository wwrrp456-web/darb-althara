"""Design-prototype checks only; never assert readiness of the production game.
Serve repository on port 8010, then run: python3 docs/phase-b/verify_prototype.py
Writes snapshots and review-checks.json only in docs/phase-b.
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
BASE='http://localhost:8010/docs/phase-b/'
OUT=Path(__file__).resolve().parent
SIZES=[(360,640),(390,844),(430,932),(768,1024),(1180,820)]
async def bounds(page):
 return await page.evaluate('''() => {
 const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}};
 const stage=box('#board-stage'),dock=box('.action-dock');
 const controls=[...document.querySelectorAll('button,input:not([type=radio]),select')].filter(e=>e.getClientRects().length);
 return {overflow:document.documentElement.scrollWidth>innerWidth,stage,dock,
  smallControls:controls.filter(e=>{const r=e.getBoundingClientRect();return r.width<47.9||r.height<47.9}).map(e=>e.id||e.textContent),
  visibleImagesBroken:[...document.images].filter(e=>e.getClientRects().length&&e.loading!=='lazy'&&(!e.complete||!e.naturalWidth)).map(e=>e.src)};
 }''')
async def main():
 result={'scope':'phase B design prototype, not production game','matrix':[],'functional':{},'errors':[],'http_errors':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  result['browser']=browser.version
  context=await browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
  page=await context.new_page()
  page.on('pageerror',lambda e:result['errors'].append(str(e)))
  page.on('response',lambda r:result['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  for count in (2,8):
   await page.goto(BASE+f'?screen=play&players={count}',wait_until='networkidle')
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h})
    await page.wait_for_timeout(100)
    row=await bounds(page)
    assert not row['overflow'],row
    assert not row['smallControls'],row
    assert not row['visibleImagesBroken'],row
    assert row['stage']['h']>190,row
    assert row['stage']['bottom']<=row['dock']['y'],row
    assert row['dock']['bottom']<=h+.5,row
    row.update(players=count,width=w,height=h)
    await page.locator('#roll-demo').evaluate('(e)=>e.blur()')
    await page.screenshot(path=str(OUT/f'snapshots/play-{count}p-{w}x{h}.png'))
    result['matrix'].append(row)
  # Read-only inspection for all eight people from the crowd picker.
  await page.set_viewport_size({'width':390,'height':844})
  before=await page.evaluate('prototypeSnapshot()')
  for i in range(8):
   await page.locator('#crowd-button').click()
   assert await page.locator('#crowd-list button').count()==8
   await page.locator(f'#crowd-list [data-person="{i}"]').click()
   assert await page.locator('#info-dialog').is_visible()
   assert await page.evaluate('document.querySelector("#info-dialog").contains(document.activeElement)')
   for _ in range(5):
    await page.keyboard.press('Tab')
    assert await page.evaluate('document.querySelector("#info-dialog").contains(document.activeElement)')
   await page.keyboard.press('Escape')
   assert await page.evaluate('document.activeElement.id')=='crowd-button'
  assert await page.evaluate('prototypeSnapshot()')==before
  result['functional']['eight_person_picker_and_read_only_inspection']='passed'
  await page.locator('#crowd-button').click()
  await page.screenshot(path=str(OUT/'snapshots/eight-person-picker.png'))
  await page.keyboard.press('Escape')
  await page.locator('#current-tile').click()
  assert await page.locator('#info-title').inner_text()=='مقهى الحي'
  await page.keyboard.press('Escape')
  assert await page.evaluate('document.activeElement.id')=='current-tile'
  # Camera is a presentation-only mock. These are not production camera tests.
  await page.locator('#zoom-in').click();await page.locator('#board-stage').focus();await page.keyboard.press('ArrowLeft')
  assert 'translate(20px' in await page.locator('#board-world').get_attribute('style')
  await page.keyboard.press('0')
  assert 'scale(1)' in await page.locator('#board-world').get_attribute('style')
  result['functional']['mock_camera_buttons_and_keyboard']='passed'
  # Walk the actual setup UI for all ending choices, with editable names.
  for ending in ('dreams','rounds','time'):
   await page.goto(BASE,wait_until='networkidle')
   await page.locator('#home [data-go=players]').click()
   await page.locator('#player-count').select_option('8')
   await page.locator('[data-player-name="0"]').fill('علي')
   await page.locator('#players [data-go=session]').click()
   await page.locator('input[name=mode][value=extended]').check()
   await page.locator(f'input[name=ending][value={ending}]').check()
   if ending!='dreams':await page.locator('#ending-limit').fill('10')
   await page.locator('#review-settings').click()
   assert 'علي' in await page.locator('#review-players').inner_text()
   assert 'موسع' in await page.locator('#settings-summary').inner_text()
   await page.locator('#start-demo').click()
   assert (await page.evaluate('prototypeSnapshot()'))['ending']==ending
   assert 'علي' in await page.locator('.turn-person b').inner_text()
   await page.locator('#more-button').click();await page.locator('#show-end').click()
   assert await page.locator('#end').is_visible()
   await page.locator('#replay').click()
   assert (await page.evaluate('prototypeSnapshot()'))['count']==8
   assert (await page.evaluate('prototypeSnapshot()'))['ending']==ending
  result['functional']['three_step_setup_endings_and_replay']='passed (mock outcomes; no timers or settlement engine)'
  # Both choices in the mandatory financial decision, including Escape and repeat clicks.
  for accepted in (True,False):
   await page.goto(BASE+'?screen=play',wait_until='networkidle')
   await page.locator('#roll-demo').dblclick()
   await page.wait_for_selector('#decision-dialog[open]')
   await page.keyboard.press('Escape')
   assert await page.locator('#decision-dialog').is_visible()
   assert await page.evaluate('document.querySelector("#decision-dialog").contains(document.activeElement)')
   await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab')
   assert await page.evaluate('document.querySelector("#decision-dialog").contains(document.activeElement)')
   if accepted:await page.screenshot(path=str(OUT/'snapshots/decision-mobile.png'))
   await page.locator('#accept-demo' if accepted else '#decline-demo').click()
   await page.wait_for_selector('#info-dialog[open]')
   assert (await page.evaluate('prototypeSnapshot()'))['chosen']==accepted
   assert ('٣٬٠٠٠' if accepted else '١٥٬٠٠٠') in await page.locator('#info-body').inner_text()
   if accepted:await page.screenshot(path=str(OUT/'snapshots/outcome-mobile.png'))
   await page.locator('#outcome-end').click()
   if accepted:await page.screenshot(path=str(OUT/'snapshots/end-mobile.png'))
  result['functional']['mandatory_decision_accept_decline_escape_and_repeat_input']='passed (fixture amounts)'
  # Compare every direction on the actual home layout and header.
  for concept in ('a','b','c'):
   await page.goto(BASE+f'?logo={concept}',wait_until='networkidle')
   await page.set_viewport_size({'width':1180,'height':820})
   await page.locator('#home-title').evaluate('(e)=>e.blur()')
   await page.screenshot(path=str(OUT/f'snapshots/home-{concept}-1180x820.png'))
   await page.locator('.app-header [data-go=concepts]').click()
   assert await page.locator(f'[data-concept={concept}]').get_attribute('aria-pressed')=='true'
   for size in (32,192):
    mark=await context.new_page()
    await mark.set_viewport_size({'width':size,'height':size})
    await mark.goto(BASE+f'marks/{concept}-mark.svg',wait_until='load')
    await mark.screenshot(path=str(OUT/f'marks/{concept}-{size}.png'),omit_background=True)
    await mark.close()
  result['functional']['three_logo_applications_and_32px_exports']='passed (human recognition review pending)'
  await page.goto(BASE+'?screen=concepts',wait_until='networkidle')
  await page.set_viewport_size({'width':1440,'height':1400})
  await page.locator('#concepts-title').evaluate('(e)=>e.blur()')
  await page.screenshot(path=str(OUT/'snapshots/logo-directions.png'))
  for screen in ('home','players','session','summary','end'):
   for w,h in SIZES:
    await page.goto(BASE+f'?screen={screen}',wait_until='networkidle')
    await page.set_viewport_size({'width':w,'height':h})
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth'),(screen,w,h)
    assert not (await bounds(page))['smallControls'],(screen,w,h,await bounds(page))
   if screen in ('home','summary'):
    await page.set_viewport_size({'width':390,'height':844})
    await page.screenshot(path=str(OUT/f'snapshots/{screen}-mobile.png'))
  result['functional']['other_screens_five_viewports']='passed (25 cases)'
  assert not await page.evaluate('localStorage.length'), 'Prototype must not write localStorage'
  assert not await page.evaluate('navigator.serviceWorker.getRegistrations().then(r=>r.length)'), 'Prototype must not register a worker'
  result['functional']['isolated_from_saved_games_and_service_workers']='passed'
  assert not result['errors'],result['errors']
  assert not result['http_errors'],result['http_errors']
  await browser.close()
 (OUT/'review-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'matrix_cases':len(result['matrix']),**result['functional'],'errors':result['errors'],'http_errors':result['http_errors']},ensure_ascii=False,indent=2))
asyncio.run(asyncio.wait_for(main(),timeout=240))
