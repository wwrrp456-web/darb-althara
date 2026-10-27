"""Phase A observations, not acceptance tests. Requires local server on port 8000.
Run from repository root: python3 docs/phase-a/diagnose.py
Writes only docs/phase-a artifacts. Uses disposable browser contexts.
"""
import asyncio
import json
import sys
from pathlib import Path
from importlib.metadata import version
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_tabletop import start_game
OUT = Path(__file__).resolve().parent
SIZES = [(360, 640), (390, 844), (430, 932), (768, 1024), (1180, 820)]
MEASURE = """() => {
 const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}};
 const stage=document.querySelector('.tabletop-stage'), bar=document.querySelector('.bar-actions');
 const a=box(stage),b=box(bar);
 const controls=[...document.querySelectorAll('#game button,.bar-actions button')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden');
 const small=controls.filter(e=>{const r=e.getBoundingClientRect();return r.width<48||r.height<48}).map(e=>({text:e.textContent.trim(),label:e.getAttribute('aria-label'),...box(e),font:parseFloat(getComputedStyle(e).fontSize)}));
 const tiles=[...document.querySelectorAll('#board .tile')];
 const hits=[...document.querySelectorAll('.character-pawn .miniature-hit')];
 const pairs=[];
 for(let i=0;i<hits.length;i++)for(let j=i+1;j<hits.length;j++){
  const r=hits[i].getBoundingClientRect(),s=hits[j].getBoundingClientRect();
  const area=Math.max(0,Math.min(r.right,s.right)-Math.max(r.left,s.left))*Math.max(0,Math.min(r.bottom,s.bottom)-Math.max(r.top,s.top));
  if(area>0)pairs.push({i,j,area});
 }
 return {viewport:{width:innerWidth,height:innerHeight},scrollY,scrollHeight:document.documentElement.scrollHeight,
 horizontalOverflow:document.documentElement.scrollWidth>innerWidth,stage:a,bar:b,
 stageBarOverlap:Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)),
 tile:tiles[0]?box(tiles[0]):null,visibleTileNames:tiles.filter(e=>getComputedStyle(e.querySelector('.tile-name')).display!=='none').length,
 pawnCount:document.querySelectorAll('.character-pawn').length,hitOverlaps:pairs,
 tilesIntersectBar:tiles.filter(e=>{const r=e.getBoundingClientRect();return r.bottom>b.y&&r.top<b.bottom&&r.right>b.x&&r.left<b.x+b.w}).map(e=>e.dataset.tile),
 tileCentersOutsideStage:tiles.filter(e=>{const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return x<a.x||x>a.x+a.w||y<a.y||y>a.bottom}).map(e=>e.dataset.tile),
 controlsUnder48:small,bodyFont:parseFloat(getComputedStyle(document.body).fontSize)};
}"""
async def main():
 result={'schema':1,'base_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
         'playwright':version('playwright'),'matrix':[],'errors':[],'http_errors':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  result['browser']=browser.version
  for count in (2,8):
   ctx=await browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
   page=await ctx.new_page()
   page.on('pageerror',lambda e:result['errors'].append(str(e)))
   page.on('response',lambda r:result['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   await start_game(page,eight=count==8)
   await page.wait_for_selector('#board.landmarks-ready.decks-ready')
   # All pieces initially occupy tile 0; no game-state edits in the matrix.
   for w,h in SIZES:
    await page.set_viewport_size({'width':w,'height':h})
    await page.locator('[data-camera=reset]').evaluate('(e)=>e.click()')
    await page.evaluate('window.scrollTo(0,0)')
    await page.wait_for_timeout(500)
    row=await page.evaluate(MEASURE)
    row['players']=count
    row['screenshot']=f'{count}p-{w}x{h}.png'
    await page.screenshot(path=str(OUT/row['screenshot']))
    result['matrix'].append(row)
   await page.set_viewport_size({'width':390,'height':844})
   await page.evaluate('window.scrollTo(0,0)')
   if count==2:
    await page.locator('#sheetBtn').focus()
    await page.keyboard.press('Enter')
    result['financial_modal']=await page.evaluate("""() => ({open:document.querySelector('#modal').classList.contains('on'),focus:document.activeElement.id,
     focusInside:document.querySelector('#sheet').contains(document.activeElement),role:document.querySelector('#modal').getAttribute('role'),ariaModal:document.querySelector('#modal').getAttribute('aria-modal')})""")
    await page.keyboard.press('Tab')
    result['financial_modal']['focusAfterTab']=await page.evaluate('document.activeElement.id')
    result['financial_modal']['insideAfterTab']=await page.evaluate("document.querySelector('#sheet').contains(document.activeElement)")
    await page.wait_for_timeout(350)
    await page.screenshot(path=str(OUT/'financial-modal.png'))
   else:
    # Fixture only, in disposable memory: inspect fast-track layout with eight pieces.
    await page.evaluate("__darb.G.players.forEach(p=>{p.fast=true;p.pos=0});document.querySelector('.chip-p[data-pid=\"0\"]').click()")
    await page.locator('[data-camera=reset]').evaluate('(e)=>e.click()')
    await page.evaluate('window.scrollTo(0,0)')
    await page.wait_for_timeout(500)
    result['fast_fixture']=await page.evaluate(MEASURE)
    await page.screenshot(path=str(OUT/'8p-fast-390x844.png'))
   await ctx.close()
  await browser.close()
 (OUT/'observations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'matrix_cases':len(result['matrix']),'errors':result['errors'],'http_errors':result['http_errors'],'financial_modal':result['financial_modal']},ensure_ascii=False))
asyncio.run(main())
