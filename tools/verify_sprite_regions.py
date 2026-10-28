"""Regression for the user's cut-off briefcase and every declared sprite region.
Screenshots are browser renders. Source artwork is never cropped or rewritten on disk.
"""
import asyncio,io,json
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/sprite-fix'
async def main():
 result={'errors':[],'http_errors':[],'gallery':{},'runtime':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1180,'height':900})
  page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_errors'].append(r.url) if r.status>=400 else None)
  await page.goto('http://localhost:8000/docs/sprite-fix/',wait_until='networkidle')
  result['gallery']=await page.evaluate('''()=>Object.fromEntries(Object.entries(DarbSprites.sheets).map(([key,s])=>{for(const [x,y,w,h] of s.regions)if(x<0||y<0||w<=0||h<=0||x+w>s.width||y+h>s.height)throw Error(key+' invalid region');return [key,s.regions.length]}))''')
  assert sum(result['gallery'].values())==102
  assert await page.locator('.sample.sprite-framed').count()==102
  for frame in await page.locator('.sample.sprite-framed').all():
   assert await frame.evaluate('''e=>{const crop=e.querySelector('.sprite-viewport>svg'),r=crop.getAttribute('viewBox').split(' ').map(Number),w=+crop.getAttribute('width'),h=+crop.getAttribute('height');return crop.getAttribute('overflow')==='hidden'&&crop.getAttribute('preserveAspectRatio')==='none'&&Math.abs(w/h-r[2]/r[3])<1e-6}''')
  for key in [*result['gallery'],'case-sizes','case-comparison']:await page.locator('#'+key).screenshot(path=str(OUT/(key+'.png')))
  def purple_pixels(data):
   im=Image.open(io.BytesIO(data)).convert('RGB');return sum(1 for r,g,b in (im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()) if b>r*1.12 and b>g*1.3 and b-g>35)
  old=purple_pixels(await page.locator('#case-before').screenshot());new=purple_pixels(await page.locator('#case-after').screenshot())
  assert old>30 and new==0,(old,new)
  result['briefcase_neighbor_purple_pixels']={'before':old,'after':new}
  await page.set_viewport_size({'width':390,'height':844});await start_game(page,eight=True)
  state=await page.evaluate('JSON.stringify(__darb.G)')
  # Reuse the real inspector for every rat-race cell, catching stale sprite identity.
  for i in range(48):
   await page.evaluate('(i)=>DarbCamera.inspect(i)',i)
   info=await page.locator('#board-inspector .ui-icon').evaluate('(e)=>({name:e.dataset.icon,key:e.dataset.spriteRegion})')
   assert info['key'],info
   expected=await page.evaluate('''name=>{if(name==='menu')name='more';return DarbSprites.extraNames.includes(name)?'extra:'+DarbSprites.extraNames.indexOf(name):'icons:'+DarbSprites.names.indexOf(name)}''',info['name'])
   assert info['key'].startswith(expected+':'),info
   await page.keyboard.press('Escape')
  assert await page.evaluate('JSON.stringify(__darb.G)')==state
  for width,height in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
   await page.set_viewport_size({'width':width,'height':height});await page.evaluate('DarbCamera.inspect(25)');await page.wait_for_timeout(350)
   assert await page.locator('#board-inspector .ui-icon').get_attribute('data-sprite-region')=='icons:8:6'
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   await page.screenshot(path=str(OUT/f'inspector-{width}.png'));await page.keyboard.press('Escape');result['runtime'].append([width,height])
  await page.locator('#sheetBtn').click();await page.wait_for_timeout(350);await page.screenshot(path=str(OUT/'financial.png'))
  assert await page.locator('#goodsCard .goods-art.sprite-framed').count()==6
  await page.goto('http://localhost:8000/brand/',wait_until='networkidle')
  assert await page.locator('.icon-grid .ui-icon.sprite-framed').count()==32
  result['brand_guide_framed_icons']=32
  assert not result['errors'] and not result['http_errors'],result
  await b.close()
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
