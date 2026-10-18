"""Verify actual 3D geometry, physical-size controls, picking, preview rotation and zoom focus."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
async def verify():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  c=await b.new_context(viewport={'width':1180,'height':1000});page=await c.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await start_game(page)
  assert await page.locator('.tile .board-miniature').count()==48
  assert await page.locator('.character-pawn .toy-person').count()==2
  assert await page.locator('.pawn-art').first.evaluate('(e)=>getComputedStyle(e).display')=='none'
  assert await page.locator('.tile .face').count()>500
  # Distinct normals and a nonzero Z extent prove these are solid surfaces, not billboard icons.
  matrices=await page.locator('.tile.landmark .solid').first.evaluate('''e=>[...e.querySelectorAll('.face')].map(f=>{const m=new DOMMatrix(getComputedStyle(f).transform);return [m.m31,m.m32,m.m33,m.m43]})''')
  assert len(set(tuple(m) for m in matrices))>=4,matrices
  assert max(m[3] for m in matrices)>0,matrices
  before=await page.evaluate('JSON.stringify(__darb.G)')
  async def size(n):
   await page.locator('[data-model-size]').evaluate('(e,n)=>{e.value=n;e.dispatchEvent(new Event("input",{bubbles:true}))}',n)
  await size(100)
  w1=(await page.locator('.tile.landmark .face.top').first.bounding_box())['width']
  pawn1=(await page.locator('.character-pawn .character-head .top').first.bounding_box())['width']
  await size(180)
  w2=(await page.locator('.tile.landmark .face.top').first.bounding_box())['width']
  pawn2=(await page.locator('.character-pawn .character-head .top').first.bounding_box())['width']
  assert 1.75<w2/w1<1.85,(w1,w2)
  assert 1.75<pawn2/pawn1<1.85,(pawn1,pawn2)
  await size(135)
  tile=page.locator('.tile.landmark').first
  await tile.focus();await page.keyboard.press('Enter')
  inspector=page.locator('#board-inspector');assert await inspector.is_visible()
  assert await inspector.locator('h2').inner_text()=='مقهى الحي'
  assert 'الدفعة الأولى' in await inspector.locator('dl').inner_text()
  assert await inspector.locator('.inspect-model-world .face').count()>0
  transform=await inspector.locator('.inspect-model-world').get_attribute('style')
  await inspector.locator('.inspect-model-rotate').click()
  assert await inspector.locator('.inspect-model-world').get_attribute('style')!=transform
  preview=await inspector.locator('.board-info-symbol').bounding_box()
  transform=await inspector.locator('.inspect-model-world').get_attribute('style')
  await page.mouse.move(preview['x']+30,preview['y']+45);await page.mouse.down()
  await page.mouse.move(preview['x']+75,preview['y']+45,steps=5);await page.mouse.up()
  assert await inspector.locator('.inspect-model-world').get_attribute('style')!=transform
  await page.screenshot(path=str(ROOT/'brand/preview-model-inspector.png'))
  await inspector.locator('.inspect-model-focus').click()
  assert not await inspector.is_visible()
  assert await page.locator('.tabletop-stage').get_attribute('data-zoom')=='240'
  assert await page.locator('.tabletop-stage').get_attribute('data-follow')=='false'
  centered=await tile.bounding_box();viewport=await page.locator('.tabletop-stage').bounding_box()
  assert abs(centered['x']+centered['width']/2-viewport['x']-viewport['width']/2)<viewport['width']*.2
  await page.locator('.tabletop-stage').screenshot(path=str(ROOT/'brand/preview-model-closeup.png'))
  # A native click on a projected solid face must resolve to its owning tile.
  await tile.locator('.face.top').first.click()
  assert await inspector.locator('h2').inner_text()=='مقهى الحي'
  await page.keyboard.press('Escape')
  # The moving player miniature also exposes current profession and financial data.
  await page.locator('.character-pawn[data-player="0"]').focus();await page.keyboard.press('Enter')
  assert await inspector.locator('h2').inner_text()=='محسن'
  assert 'المهنة' in await inspector.locator('dl').inner_text()
  assert 'الراتب الشهري' in await inspector.locator('dl').inner_text()
  await inspector.locator('.inspect-model-focus').click()
  assert await page.locator('.character-pawn[data-player="0"]').evaluate('(e)=>e===document.activeElement')
  assert await page.evaluate('JSON.stringify(__darb.G)')==before,'Inspection or size controls mutated game rules'
  await page.locator('[data-camera=reset]').click()
  await page.locator('.character-pawn[data-player="0"] .minifig-face').click()
  assert await inspector.locator('h2').inner_text()=='محسن'
  await page.keyboard.press('Escape')
  assert await page.evaluate('JSON.stringify(__darb.G)')==before
  for w,h in [(320,740),(390,844),(768,1024),(1180,1000)]:
   await page.set_viewport_size({'width':w,'height':h})
   await page.locator('.tabletop-stage').scroll_into_view_if_needed()
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
   assert await page.locator('[data-model-size]').is_visible()
   if w==390:await page.screenshot(path=str(ROOT/'brand/preview-models-mobile.png'))
   if w==1180:await page.locator('.tabletop-card').screenshot(path=str(ROOT/'brand/preview-models.png'))
  await size(180);await page.reload(wait_until='networkidle')
  assert await page.locator('[data-model-size]').input_value()=='180'
  assert await page.locator('.tile .board-miniature').count()==48
  assert not errors,errors
  print(json.dumps({'solid_3d_tiles':48,'volumetric_characters':2,'model_scale_range':'100–180%','mouse_and_keyboard_inspection':'passed','preview_drag_and_rotation':'passed','focus_zoom':'240%','unchanged_game_state':'passed','responsive_sizes':4,'saved_size_preference':'passed','javascript_errors':errors}))
  await b.close()
asyncio.run(verify())
