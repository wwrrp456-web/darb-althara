"""Verify added card artwork, answer order and unchanged state while decorating."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
async def main():
 assert (ROOT/'art/identity/cards-extra-sheet.png').stat().st_size<=600_000
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':390,'height':844});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await start_game(page)
  await page.evaluate('__darb.G.players[0].cash=100000')
  state=await page.evaluate('JSON.stringify(__darb.G)')
  results=await page.evaluate('''()=>['market','audit','jail','bankrupt','family','quiz'].map(kind=>{const s=document.createElement('div');s.innerHTML='<h2>عنوان البطاقة</h2><p>نص القرار 1200</p><div class="row"><button>الأول</button><button>الثاني</button></div>';DarbIdentity.decorateCard(s,{kind});return {kind,extra:s.querySelector('.card-illustration').classList.contains('card-art-extra'),opts:[...s.querySelectorAll('button')].map(e=>e.textContent),x:s.querySelector('.card-illustration').style.getPropertyValue('--cx'),y:s.querySelector('.card-illustration').style.getPropertyValue('--cy')}})''')
  for row in results:
   assert row['extra']==(row['kind'] in ['market','audit','jail','bankrupt'])
   assert row['opts']==['الأول','الثاني']
  assert [(r['x'],r['y']) for r in results[:4]]==[('0%','0%'),('100%','0%'),('0%','100%'),('100%','100%')]
  assert await page.evaluate('JSON.stringify(__darb.G)')==state
  # Drive a real audit card and select the normal pay path. Preserve original tax and indices.
  await page.evaluate('()=>{window.__done=false;window.__task=__darb.resolveTile(__darb.G.players[0],"audit").then(()=>__done=true)}')
  await page.wait_for_selector('.card-art-extra');tax=await page.evaluate('__darb.G.prompt.data.tax');cash=await page.evaluate('__darb.G.players[0].cash')
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.screenshot(path=str(ROOT/f'brand/preview-extra-card-{w}.png'))
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  await page.locator('.decision-actions button').nth(0).click();await page.wait_for_function('__done')
  assert await page.evaluate('__darb.G.players[0].cash')==cash-tax
  assert not errors,errors;await b.close()
 print(json.dumps({'four_new_card_categories':'passed','old_categories_preserved':'passed','answer_order':'passed','read_only_decoration':'passed','actual_audit_card':'passed'}))
asyncio.run(main())
