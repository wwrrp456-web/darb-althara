"""Exercise real financial card decisions, UI icon coverage and responsive card layouts."""
import asyncio,json,re,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
def numeric_rules(source):
 arrays=[]
 for name in ['SMALL','BIG','BIZ','DOODADS','EVENTS','QUIZ','FAMILY','LIFE']:
  arrays.append(re.search(r'const '+name+r'=(\[.*?\n\]);',source,re.S).group(1))
 data=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify(['+','.join(arrays)+']))'],text=True))
 def numbers(v,path=''):
  out={}
  if isinstance(v,(int,float,bool)):out[path]=v
  elif isinstance(v,list):
   for i,x in enumerate(v):out.update(numbers(x,path+'/'+str(i)))
  elif isinstance(v,dict):
   for k,x in v.items():out.update(numbers(x,path+'/'+k))
  return out
 return numbers(data)
async def verify():
 previous=subprocess.check_output(['git','show','c26fb3b:index.html'],cwd=ROOT,text=True)
 assert numeric_rules(previous)==numeric_rules((ROOT/'index.html').read_text()),'Authored numeric rules changed'

 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  context=await browser.new_context(viewport={'width':390,'height':844})
  page=await context.new_page();errors=[];missing=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
  await start_game(page)
  await page.evaluate('__darb.G.players[0].cash=300000')
  async def trigger(tile):
   await page.evaluate('''tile=>{window.__cardDone=false;window.__cardTask=__darb.resolveTile(__darb.G.players[0],tile).then(()=>window.__cardDone=true)}''',tile)
   await page.wait_for_selector('#sheet.decision-card')
  async def choice(i):
   await page.locator('#sheet .decision-actions button').nth(i).click()
  async def done():await page.wait_for_function('window.__cardDone')
  async def money():return await page.evaluate('__darb.G.players[0].cash')
  async def layout():
   for w,h in [(320,640),(390,844),(768,1024),(1180,820)]:
    await page.set_viewport_size({'width':w,'height':h})
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
    assert await page.locator('#sheet').evaluate('(e)=>e.scrollWidth<=e.clientWidth'),w
    for button in await page.locator('#sheet .decision-actions button').all():
     await button.scroll_into_view_if_needed();assert await button.is_visible()
     assert await button.evaluate('(e)=>{let r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}'),w
   await page.set_viewport_size({'width':390,'height':844})
   await page.locator('#sheet').evaluate('(e)=>e.scrollTop=0')
  # A landmark offer has deterministic values; the display must preserve the transaction.
  await trigger('lm_cafe');assert await page.evaluate('__darb.G.prompt.kind')=='offer'
  down=await page.evaluate('__darb.G.prompt.data.down');before=await money()
  assert await page.locator('#sheet .decision-content .lrow').count()>=2
  await layout();await page.screenshot(path=str(ROOT/'brand/preview-cards-mobile.png'))
  await choice(0);await done();assert await money()==before-down
  assert await page.evaluate('__darb.G.players[0].assets.some(a=>a.lm==="cafe")')
  # Declining a new investment must not change cash or portfolio.
  before=await money();assets=await page.evaluate('__darb.G.players[0].assets.length')
  await trigger('deal');await choice(0)
  await page.wait_for_function('__darb.G.prompt?.kind==="offer"')
  await choice(1);await done();assert await money()==before
  assert await page.evaluate('__darb.G.players[0].assets.length')==assets
  # Insurance and learning retain their costs, durations and trade-offs.
  await trigger('insure');c=await page.evaluate('__darb.G.prompt.data.c');before=await money()
  await choice(0);await done();assert await money()==before-c
  assert await page.evaluate('__darb.G.players[0].ins===__darb.G.round+6')
  await trigger('learn');c=await page.evaluate('__darb.G.prompt.data.c');before=await money()
  salary,hap=await page.evaluate('[__darb.G.players[0].salary,__darb.G.players[0].hap]')
  await choice(0);await done();assert await money()==before-c
  assert await page.evaluate('__darb.G.players[0].salary')==int(salary*1.08+0.5)
  assert await page.evaluate('__darb.G.players[0].hap')==hap-6
  assert await page.evaluate('__darb.G.players[0].learn===1&&__darb.G.players[0].skip===1')
  # Family acknowledgement gains and player choices both use the illustrated family card.
  await page.evaluate('__darb.setFamilyDeck([0])');before=await money()
  await trigger('family');assert await page.locator('.card-kicker').inner_text()=='بطاقات العائلة'
  await choice(0);await done();assert await money()>before
  await page.evaluate('__darb.setFamilyDeck([7])');before=await money()
  await trigger('family');await layout()
  await page.screenshot(path=str(ROOT/'brand/preview-family-mobile.png'))
  await choice(2);await done();assert await money()==before
  # Answer a shuffled quiz correctly using the authored answer, never a fixed index.
  source=(ROOT/'index.html').read_text();q=re.search(r'const QUIZ=(\[.*?\n\]);',source,re.S).group(1)
  questions=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify('+q+'))'],text=True))
  await trigger('quiz');text=await page.locator('.decision-content').inner_text()
  authored=next(row for row in questions if row[0] in text)
  options=await page.evaluate('__darb.G.prompt.opts');correct=options.index(authored[1][authored[2]])
  before=await money();await choice(correct)
  await page.wait_for_function('__darb.G.prompt?.kind==="ack"')
  assert await money()>before;assert await page.evaluate('__darb.G.players[0].st.quizOk')==1
  await choice(0);await done()
  # Visible UI text uses illustrated icons, including menus, reactions, logs and selects.
  await page.locator('.react-fab').click()
  leaks=await page.evaluate('''()=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),out=[];while(w.nextNode()){const n=w.currentNode;if(n.parentElement.closest('script,style,svg,.illustrated-icon'))continue;if(/\\p{Extended_Pictographic}/u.test(n.nodeValue))out.push(n.nodeValue)}return out}''')
  assert not leaks,leaks
  assert await page.locator('.identity-extra').count()>0
  semantic=await page.evaluate("""()=>{const box=document.createElement('div');box.textContent='⬆️ ⬇️ ↔️ 😟 😵 🔇';document.body.append(box);DarbIdentity.hydrate(box);const result={directions:[...box.querySelectorAll('.identity-direction')].map(e=>e.textContent),extras:box.querySelectorAll('.identity-extra').length};box.remove();return result}""")
  assert semantic=={'directions':['↑','↓','↔'],'extras':3},semantic
  assert await page.locator('#board .ui-icon').first.evaluate('(e)=>getComputedStyle(e).backgroundImage.includes("icons-sheet.png")')
  await page.locator('#menuBtn').click()
  assert 'decision-card' not in (await page.locator('#sheet').get_attribute('class'))
  assert not errors,errors;assert not missing,missing
  print(json.dumps({'real_investment_purchase_and_decline':'passed','insurance_and_learning_effects':'passed','family_cards':'passed','shuffled_quiz_correct_answer':'passed','card_viewports':4,'unreplaced_emoji':leaks,'javascript_errors':errors}))
  await browser.close()
asyncio.run(verify())
