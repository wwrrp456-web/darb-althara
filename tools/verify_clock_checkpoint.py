"""Expired-time recovery fixture: preserve the safe turn, not a partial later round."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_sessions import setup,drive
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page()
  await setup(page,ending='time',limit=1)
  await page.evaluate("""()=>{__darb.G.round=2;__darb.G.clock.elapsedMs=60001;__darb.G.clock.endingRound=2;dispatchEvent(new PageTransitionEvent('pagehide'));}""")
  saved=await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6"))')
  assert saved['round']==1 and saved['clock']['endingRound']==1
  assert await page.evaluate('__darb.G.clock.endingRound')==2
  await page.reload(wait_until='networkidle');await drive(page)
  assert await page.evaluate('__darb.G.round')==1
  assert await page.evaluate('__darb.G.summary.reason')=='time'
  assert await page.evaluate('__darb.G.players.map(p=>p.turns)')==[1,1]
  await b.close()
 result={'fixture':'deadline in a later uncommitted round','safe_turn_and_elapsed_time':'preserved','no_extra_round_on_expired_reload':'passed','completed_safe_round_with_equal_turns':'passed'}
 (Path(__file__).resolve().parents[1]/'docs/phase-e/clock-checkpoint-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':asyncio.run(main())
