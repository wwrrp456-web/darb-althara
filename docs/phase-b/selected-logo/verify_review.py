"""Export review sizes and validate only the selected-logo design prototype.
Requires repository HTTP server on 8010 and /workspace HTTP server on 8011.
"""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parent
BASE='http://localhost:8010/docs/phase-b/'
async def render(page,url,w,h,path):
 await page.set_viewport_size({'width':w,'height':h})
 await page.set_content(f'<style>html,body{{margin:0;background:transparent}}img{{display:block;width:{w}px;height:{h}px}}</style><img src="{url}">')
 await page.locator('img').evaluate('(e)=>e.decode()')
 await page.screenshot(path=str(path),omit_background=True)
async def main():
 result={'scope':'selected logo and design prototype, not production game','matrix':[],'errors':[],'http_errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page()
  page.on('pageerror',lambda e:result['errors'].append(str(e)))
  page.on('response',lambda r:result['http_errors'].append({'status':r.status,'url':r.url}) if r.status>=400 else None)
  for size in [32,64,192,512]:
   await render(page,BASE+'selected-logo/compact-source.png',size,size,OUT/f'icon-{size}.png')
  for name,w,h in [('horizontal',1200,360),('vertical',840,916),('horizontal-dark',1200,360)]:
   await render(page,BASE+f'selected-logo/{name}.svg',w,h,OUT/f'{name}.png')
  for count in [2,8]:
   await page.goto(BASE+f'?logo=cartoon1&screen=play&players={count}',wait_until='networkidle')
   assert (await page.evaluate('prototypeSnapshot()'))['logo']=='cartoon1'
   assert await page.locator('.brand-lockup').get_attribute('src')=='selected-logo/horizontal.svg'
   for w,h in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
    await page.set_viewport_size({'width':w,'height':h})
    await page.wait_for_timeout(80)
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert await page.locator('.brand-lockup').evaluate('(e)=>e.complete&&e.naturalWidth>0')
    boxes=await page.evaluate('''() => {const s=document.querySelector('#board-stage').getBoundingClientRect(),d=document.querySelector('.action-dock').getBoundingClientRect();return {stageBottom:s.bottom,dockTop:d.y}}''')
    assert boxes['stageBottom']<=boxes['dockTop']
    result['matrix'].append({'players':count,'width':w,'height':h,'overflow':False,**boxes})
    if count==8 and w in [390,1180]:
     await page.locator('#roll-demo').evaluate('(e)=>e.blur()')
     await page.screenshot(path=str(OUT/f'play-{w}.png'))
   await page.locator('#crowd-button').click()
   assert await page.locator('#crowd-list button').count()==count
   await page.keyboard.press('Escape')
  await page.goto(BASE+'?logo=cartoon1',wait_until='networkidle')
  await page.set_viewport_size({'width':1180,'height':820})
  await page.locator('#home-title').evaluate('(e)=>e.blur()')
  await page.screenshot(path=str(OUT/'home-1180.png'))
  await page.set_viewport_size({'width':390,'height':844})
  await page.screenshot(path=str(OUT/'home-390.png'))
  await page.locator('.review-link').click()
  assert await page.locator('.hero>img').get_attribute('src')=='horizontal.svg'
  await page.set_viewport_size({'width':1440,'height':1460})
  await page.screenshot(path=str(OUT/'applications.png'),full_page=True)
  requests=[];page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
  await page.goto('http://localhost:8011/darb-althara-selected-review.html',wait_until='networkidle')
  assert (await page.evaluate('prototypeSnapshot()'))['logo']=='cartoon1'
  await page.locator('.brand-lockup').evaluate('(e)=>e.decode()')
  await page.locator('.review-link').click()
  assert await page.locator('#info-dialog').is_visible()
  await page.keyboard.press('Escape')
  await page.locator('#home [data-go=players]').click()
  await page.locator('#players [data-go=session]').click()
  await page.locator('#review-settings').click()
  await page.locator('#start-demo').click()
  await page.locator('#roll-demo').click()
  await page.wait_for_selector('#decision-dialog[open]')
  await page.locator('#decline-demo').click()
  assert (await page.evaluate('prototypeSnapshot()'))['chosen']==False
  assert requests==['http://localhost:8011/darb-althara-selected-review.html'],requests
  result.update(standalone_http='passed',standalone_external_asset_requests=0,selected_brand_and_setup_decision='passed',png_exports=[32,64,192,512])
  assert not result['errors'] and not result['http_errors'],result
  await b.close()
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'matrix_cases':len(result['matrix']),'standalone_http':result['standalone_http'],'errors':result['errors'],'http_errors':result['http_errors']},ensure_ascii=False))
asyncio.run(asyncio.wait_for(main(),timeout=120))
