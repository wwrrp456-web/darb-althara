"""Local city choice, staged previews and live play; no match/protocol edits."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
OUT=Path(__file__).resolve().parents[1]/'docs/cities'
async def main():
 result={'errors':[],'matrix':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=await browser.new_context(viewport={'width':390,'height':844});page=await context.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)))
  await page.goto('http://localhost:8000/');await page.locator('#wNew').click();await page.locator('#sStart').click()
  await page.locator('#sEnding').select_option('rounds');await page.locator('#sLimit').fill('9')
  await page.locator('#choose-city-setup').click();assert await page.locator('#city-list button').count()==10
  for i in range(10):
   await page.locator(f'[data-city-index="{i}"]').click();assert await page.locator('#city-preview-title').inner_text()
   assert await page.locator('#city-apply').is_enabled()==(i==0)
  await page.locator('[data-city-index="0"]').click();await page.locator('#city-apply').click()
  assert await page.locator('#sLimit').input_value()=='9'
  await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click();assert 'مدينة المعمار' in await page.locator('#sheet').inner_text()
  await start_game(page,eight=True);baseline=await page.evaluate('JSON.stringify(__darb.G)')
  for w,h in [(360,640),(390,844),(430,932),(768,1024),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.locator('[data-camera=reset]').click()
   await page.wait_for_timeout(100)
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert await page.locator('#board').get_attribute('data-route')=='rat'
   await page.screenshot(path=str(OUT/f'play-{w}.png'))
   await page.locator('#camera-help').click();await page.locator('#choose-city-play').click()
   await page.screenshot(path=str(OUT/f'chooser-{w}.png'))
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   await page.keyboard.press('Escape');assert not await page.locator('#city-picker').is_visible()
   result['matrix'].append([w,h])
  await page.locator('#camera-help').click();await page.locator('#choose-city-play').click();await page.locator('#city-classic').click()
  assert await page.evaluate('document.documentElement.dataset.city')=='classic'
  assert await page.evaluate('JSON.stringify(__darb.G)')==baseline
  await page.reload(wait_until='networkidle');assert await page.evaluate('document.documentElement.dataset.city')=='classic'
  # Random draws exclusively from genuinely available production cities.
  await page.locator('#camera-help').click();await page.locator('#choose-city-play').click();await page.locator('#city-random').click()
  assert await page.evaluate('document.documentElement.dataset.city')=='architecture'
  # Missing local preference / unknown value safely chooses the shipped city.
  await page.evaluate("localStorage.setItem('darb-city-view','unknown')");await page.reload(wait_until='networkidle')
  assert await page.evaluate('document.documentElement.dataset.city')=='architecture'
  await page.locator('[data-camera=reset]').click()
  frozen=await page.evaluate('JSON.stringify(__darb.G)')
  hospital=page.locator('[data-city-project=hospital]');await hospital.focus();await page.keyboard.press('Enter')
  assert await page.locator('#board-info-title').inner_text()=='مستشفى خاص';await page.keyboard.press('Escape')
  await hospital.click();assert await page.locator('#board-info-title').inner_text()=='مستشفى خاص';await page.keyboard.press('Escape')
  assert await page.evaluate('JSON.stringify(__darb.G)')==frozen
  # No state, financial or player changes from city selection; independent new device uses its own preference.
  other=await browser.new_context();tab=await other.new_page();await tab.goto('http://localhost:8000/');assert await tab.evaluate('document.documentElement.dataset.city')=='architecture';await other.close()
  await context.set_offline(True);await page.reload(wait_until='domcontentloaded');await page.wait_for_selector('.center')
  assert await page.locator('#board').get_attribute('data-route')=='rat'
  result['offline_asset_bytes']=await page.evaluate("async()=>{const out={};for(const name of ['architecture-models','fast-models','concepts']){const r=await fetch('art/cities/'+name+'.webp');if(!r.ok)throw Error(name+' offline missing');out[name]=(await r.blob()).size;}return out;}")
  assert result['offline_asset_bytes']=={'architecture-models':420616,'fast-models':243960,'concepts':454778}
  assert not result['errors'],result;await browser.close()
 result.update(cities=10,playable_new_cities=1,remaining_cities='honest previews, not selectable as finished artwork',classic_fallback='passed',random_available_only='passed',local_preference_reload='passed',offline='passed',setup_values_preserved='passed',match_unchanged='passed')
 (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();OUT=args.output;OUT.mkdir(parents=True,exist_ok=True);asyncio.run(main())
