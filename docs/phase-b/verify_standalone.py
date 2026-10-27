"""Verify the self-contained review artifact, not the production game.
Build /workspace/darb-althara-review.html with make_review.py first.
Serve /workspace using port 8011, then run this script from repository root.
"""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright,Error
async def main():
 result={'artifact_sha256':__import__('hashlib').sha256(Path('/workspace/darb-althara-review.html').read_bytes()).hexdigest()}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  context=await b.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
  page=await context.new_page();requests=[];errors=[]
  page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:','file:')) else None)
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto('http://localhost:8011/darb-althara-review.html',wait_until='networkidle')
  await page.locator('.app-header [data-go=concepts]').click()
  for c in ('b','c','a'):
   await page.locator(f'[data-concept={c}]').click()
   assert (await page.evaluate('prototypeSnapshot()'))['logo']==c
   await page.locator('.brand-lockup').evaluate('(e)=>e.decode()')
   assert await page.locator('.brand-lockup').evaluate('(e)=>e.complete&&e.naturalWidth>0&&e.src.startsWith("data:")')
  await page.locator('#concepts [data-go=home]').click()
  await page.locator('#home [data-go=players]').click()
  await page.locator('#player-count').select_option('8')
  await page.locator('#players [data-go=session]').click()
  await page.locator('input[name=ending][value=time]').check()
  await page.locator('#ending-limit').fill('30')
  await page.locator('#review-settings').click()
  await page.locator('#start-demo').click()
  await page.locator('#crowd-button').click()
  assert await page.locator('#crowd-list button').count()==8
  await page.keyboard.press('Escape')
  await page.locator('#roll-demo').click()
  await page.wait_for_selector('#decision-dialog[open]')
  await page.locator('#accept-demo').click()
  await page.wait_for_selector('#info-dialog[open]')
  assert (await page.evaluate('prototypeSnapshot()'))['chosen']==True
  assert not errors,errors
  assert requests==['http://localhost:8011/darb-althara-review.html'],requests
  result.update(standalone_http='passed',external_asset_requests=0,requests=requests,javascript_errors=errors,logo_switch_setup_and_decision='passed')
  filepage=await context.new_page()
  try:
   await filepage.goto('file:///workspace/darb-althara-review.html',wait_until='networkidle')
   assert await filepage.locator('#home-title').is_visible()
   result['file_protocol']='passed: home loaded; complete file workflow not exercised'
  except Error as e:
   result['file_protocol']='blocked by browser policy' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(e) else str(e).splitlines()[0]
  await b.close()
 Path('docs/phase-b/standalone-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
asyncio.run(main())
