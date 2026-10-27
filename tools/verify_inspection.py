"""Read-only live inspector: real purchases/upgrades, deck counters, touch targets and input arbitration."""
import asyncio,json,re
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
def integer(text):return int(re.sub(r'[^0-9]','',text))
async def verify():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c=await b.new_context(viewport={'width':390,'height':844});page=await c.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
  await start_game(page);await page.wait_for_selector('#board.landmarks-ready.decks-ready')
  inspector=page.locator('#board-inspector')
  async def snapshot():return await page.evaluate('JSON.stringify({game:__darb.G,decks:__darb.deckCounts})')
  async def details():return await inspector.locator('dl').evaluate('(e)=>Object.fromEntries([...e.querySelectorAll("dt")].map(t=>[t.textContent,t.nextElementSibling.textContent]))')
  async def inspect(selector):
   state=await snapshot();await page.locator(selector).focus();await page.keyboard.press('Enter');assert await inspector.is_visible();assert await snapshot()==state;return await details()
  async def close():await page.keyboard.press('Escape')
  # Invisible target padding measures >=48 CSS pixels even with the board zoomed out.
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await page.locator('.tabletop-stage').scroll_into_view_if_needed()
   await page.locator('[data-camera=out]').click()
   for hit in await page.locator('.landmark-stand .miniature-hit,.has-deck-art>.miniature-hit,.pawn-stand>.miniature-hit').all():
    box=await hit.bounding_box();assert box['width']>=48 and box['height']>=48,(w,box)
   await page.locator('[data-camera=reset]').click()
  await page.set_viewport_size({'width':390,'height':844})
  d=await inspect('[data-landmark=hospital]');assert d['المالك']=='متاح للشراء';assert integer(d['سعر الشراء الأساسي'])==110000;assert integer(d['الدخل الأساسي'])==1200
  initial_down=integer(d['الدفعة الأولى']);await close()
  # Native pointer on the actual miniature, not just its tile, opens the same inspector.
  state=await snapshot();await page.locator('[data-landmark=hospital] .landmark-stand').click();assert await inspector.locator('h2').inner_text()=='مستشفى خاص';assert await snapshot()==state;await close()
  # A real engine purchase followed by each allowed upgrade changes live data and badges.
  await page.evaluate('()=>{__darb.G.players[0].cash=1000000;window.__done=false;__darb.resolveTile(__darb.G.players[0],"lm_hospital").then(()=>__done=true)}')
  assert await page.evaluate('__darb.G.prompt.data.down')==initial_down
  await page.locator('.decision-actions button').first.click();await page.wait_for_function('__done');await page.locator('.chip-p[data-pid="0"]').evaluate('(e)=>e.click()')
  await page.evaluate('__darb.upgradeLm(0,"hospital")')
  d=await inspect('[data-landmark=hospital]')
  assert 'محسن' in d['المالك'];assert await inspector.locator('dd .identity-avatar').count()==1;assert integer(d['مستوى التطوير'])==1;assert integer(d['تكلفة التطوير التالي'])==17000
  assert integer(d['الدخل الشهري الحالي'])==await page.evaluate('__darb.G.players[0].assets.find(a=>a.lm==="hospital").inc')
  assert integer(d['الإيجار قبل سقف قدرة الزائر'])==2250
  await close();await page.evaluate('__darb.G.players[0].fast=true');await page.locator('.chip-p[data-pid="1"]').evaluate('(e)=>e.click()')
  await inspect('[data-landmark=hospital]')
  for level in [2,3]:
   await page.evaluate('__darb.upgradeLm(0,"hospital")');assert await inspector.is_visible();d=await details()
   assert integer(d['مستوى التطوير'])==level
   assert integer(d['الدخل الشهري الحالي'])==await page.evaluate('__darb.G.players[0].assets.find(a=>a.lm==="hospital").inc')
   assert integer(d['الإيجار قبل سقف قدرة الزائر'])==await page.evaluate('__darb.lmRent("hospital")')
   if level==3:assert d['تكلفة التطوير التالي']=='اكتملت المستويات الثلاثة'
  await close()
  # A snapshot of the counters is frozen and cannot mutate the deck.
  await page.evaluate('__darb.setFamilyDeck([0,1,2])')
  assert await page.evaluate('Object.isFrozen(__darb.deckCounts)&&Object.isFrozen(__darb.deckCounts.family)')
  d=await inspect('[data-deck=family]');assert integer(d['المتبقي في الخلطة الحالية'])==3;assert integer(d['المستخدم في الخلطة الحالية'])==12;await close()
  d=await inspect('[data-deck=quiz]');assert integer(d['عدد البطاقات'])==29;assert integer(d['المتبقي في الخلطة الحالية'])==0;await close()
  # Draw a real quiz once, while checking that inspection cannot steal a pending decision.
  await page.evaluate('()=>{window.__done=false;__darb.resolveTile(__darb.G.players[0],"quiz").then(()=>__done=true)}')
  prompt=await page.evaluate('__darb.G.prompt.id');await page.locator('[data-deck=quiz]').focus();await page.keyboard.press('Enter')
  assert not await inspector.is_visible();assert await page.evaluate('__darb.G.prompt.id')==prompt
  await page.locator('.decision-actions button').first.click();await page.wait_for_function('__darb.G.prompt?.kind==="ack"');await page.locator('.decision-actions button').first.click();await page.wait_for_function('__done')
  d=await inspect('[data-deck=quiz]');assert integer(d['المتبقي في الخلطة الحالية'])==28;assert integer(d['المستخدم في الخلطة الحالية'])==1;await close()
  # Pawn details are the current financial data; the portrait keeps the approved identity.
  d=await inspect('.character-pawn[data-player="1"]');assert d['المهنة']=='مبرمجة';assert d['حالة السجن']=='خارج السجن';assert await inspector.locator('.inspector-character').count()==1;await close()
  # Capture the actual live upgraded property inspector at both target sizes.
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h});await inspect('[data-landmark=hospital]')
   await page.screenshot(path=str(ROOT/f'brand/preview-live-inspector-{w}.png'));assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth');await close()
  assert not errors,errors;await b.close()
 print(json.dumps({'live_purchase_and_levels_0_to_3':'passed','base_current_income_and_rent':'passed','next_upgrade_cost':'passed','owner_avatar':'passed','deck_counts_and_frozen_getter':'passed','no_inspection_state_mutation':'passed','pending_decision_priority':'passed','min_touch_target_px':48,'pawn_data':'passed','console_errors':errors}))
asyncio.run(verify())
