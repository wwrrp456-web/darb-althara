"""Automated WCAG A/AA audit using a locally supplied axe-core 4.10.3.
No audit library is added to app runtime. Run with --axe /path/axe.min.js.
"""
import argparse,asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
async def main(args):
 result={'axe_version':'4.10.3','scope':'Chromium automated WCAG 2.0/2.1 A/AA; not a screen-reader certification','screens':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:result['errors'].append(str(e)))
  async def audit(name):
   await page.wait_for_timeout(350)
   await page.add_script_tag(path=str(args.axe))
   data=await page.evaluate("""async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,help:v.help,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))})),passes:r.passes.length};}""")
   result['screens'].append(dict(name=name,**data));print(name,[(v['id'],len(v['nodes'])) for v in data['violations']],flush=True)
  await page.goto('http://localhost:8000/',wait_until='networkidle');await audit('home')
  await page.locator('#wNew').click();await audit('players')
  for _ in range(6):await page.locator('#sAdd').click()
  for number in range(1,9):
   assert await page.get_by_role('combobox',name=f'طريقة تحكم اللاعب {number}',exact=True).count()==1
   assert await page.get_by_role('textbox',name=f'اسم اللاعب {number}',exact=True).count()==1
   if number>1:assert await page.get_by_role('button',name=f'حذف اللاعب {number}',exact=True).count()==1
  await audit('eight-players')
  await page.locator('#sStart').click();await page.locator('#sEnding').select_option('time');await audit('session')
  await page.locator('#choose-city-setup').click();await audit('city-ready');await page.locator('[data-city-index="1"]').click();await audit('city-preview');await page.keyboard.press('Escape')
  await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click();await audit('review')
  await start_game(page);await audit('play')
  await page.locator('#sheetBtn').click();await audit('financial')
  await page.get_by_role('button',name='إغلاق',exact=True).click();await page.locator('#board-players').click();await audit('player-picker')
  await page.keyboard.press('Escape');await page.locator('#board-projects-open').click();await audit('projects');await page.keyboard.press('Escape');await page.evaluate("()=>{__darb.resolveTile(__darb.G.players[0],'quiz');}");await page.wait_for_selector('#sheet.decision-card');await audit('quiz')
  await page.goto('http://localhost:8000/',wait_until='networkidle')
  # Fresh context avoids restoring the active fixture for the join screen.
  await page.evaluate('localStorage.removeItem("darb-althara-v6")');await page.reload(wait_until='networkidle');await page.locator('#wJoin').click();await audit('join')
  await page.locator('#jCancel').click();await page.locator('#wNew').click()
  await page.locator('[data-i="1"] [data-k="ctrl"]').select_option('remote')
  await page.locator('#sStart').click();await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click();await page.locator('#sLaunch').click()
  await audit('invite');await page.locator('#iMake').click();await page.locator('#iCode').wait_for();await audit('invite-code')
  assert not result['errors'],result['errors'];await b.close()
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if args.require_clean:assert not any(x['violations'] for x in result['screens']),'Accessibility violations remain'
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--axe',type=Path,required=True);parser.add_argument('--output',type=Path,default=Path('docs/accessibility/after.json'));parser.add_argument('--require-clean',action='store_true');asyncio.run(main(parser.parse_args()))
