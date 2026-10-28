"""Contrast evidence from actual computed styles and rendered glyph backgrounds.
Not a full WCAG audit: projection, text size, vision and screen readers need separate checks.
"""
import asyncio,io,json,re,argparse
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
def rgba(value):
 nums=[float(v) for v in re.findall(r'[\d.]+',value)];return tuple(nums[:3]),nums[3] if len(nums)>3 else 1

def lum(rgb):
 c=[x/255 for x in rgb];return sum((x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4)*w for x,w in zip(c,[.2126,.7152,.0722]))
def contrast(fg,bg):
 lo,hi=sorted([lum(fg),lum(bg)]);return (hi+.05)/(lo+.05)
async def main(args):
 args.output.mkdir(parents=True,exist_ok=True)
 result={'scope':'computed opaque colors, conservative alpha background bound, and background under solid text pixels','palette':[],'glyph_samples':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1180,'height':820});page.on('pageerror',lambda e:result['errors'].append(str(e)))
  await start_game(page,eight=True)
  # Includes all eight pawn colors even when grouped visually.
  selectors=['.pawn-number','.pawn-cluster','.has-deck-art>b','.tabletop-hud .mut','[data-camera=out]','[data-close-crowd]']
  for selector in selectors:
   for i,el in enumerate(await page.locator(selector).all()):
    css=await el.evaluate('(e)=>{const s=getComputedStyle(e);return {foreground:s.color,background:s.backgroundColor,opacity:s.opacity}}')
    fg,fa=rgba(css['foreground']);bg,ba=rgba(css['background'])
    # All sampled backgrounds are light and foregrounds dark, or both fully opaque.
    # For translucent light backgrounds, compositing over black is a conservative lower bound.
    worst=tuple(v*ba for v in bg)
    ratio=contrast(fg,worst)
    row=dict(selector=selector,index=i,**css,background_over_black=list(worst),contrast=round(ratio,3),threshold=4.5)
    assert fa==1 and float(css['opacity'])==1, row
    assert ratio>=4.5,row
    result['palette'].append(row)
  for w,h in [(390,844),(1180,820)]:
   await page.set_viewport_size({'width':w,'height':h})
   for view in ['top','perspective']:
    if w<768:await page.locator('#table-view-select').select_option(view)
    else:await page.locator(f'[data-table-view={view}]').click()
    for name in ['محسن','عبدالرحمن سالم']:
     # Valid-length name fixture; invokes the existing view render, not any financial action.
     await page.evaluate('(name)=>__darb.G.players[0].name=name',name)
     await page.locator('#chips [data-pid="0"]').evaluate('(e)=>e.click()')
     await page.locator('[data-camera=reset]').click()
     await page.locator('.tabletop-stage').focus()
     for _ in range(5):await page.keyboard.press('+')
     await page.wait_for_timeout(350)
     el=page.locator('.tabletop-hud .big');title_selector='.tabletop-hud .big'
     if not await el.is_visible():el=page.locator('#turn-readout b');title_selector='#turn-readout b'
     rect=await el.bounding_box();fg,_=rgba(await el.evaluate('(e)=>getComputedStyle(e).color'))
     # Exclude the light shadow so evidence does not rely on it for contrast.
     await el.evaluate('(e)=>e.style.setProperty("text-shadow","none","important")')
     visible=Image.open(io.BytesIO(await page.screenshot())).convert('RGB')
     await el.evaluate('(e)=>e.style.setProperty("visibility","hidden","important")')
     background=Image.open(io.BytesIO(await page.screenshot())).convert('RGB')
     ratios=[]
     for y in range(max(0,int(rect['y'])),min(h,int(rect['y']+rect['height']+1))):
      for x in range(max(0,int(rect['x'])),min(w,int(rect['x']+rect['width']+1))):
       v=visible.getpixel((x,y));bg=background.getpixel((x,y))
       if max(abs(a-c) for a,c in zip(v,fg))<12 and sum(abs(a-c) for a,c in zip(v,bg))>30:ratios.append(contrast(fg,bg))
     row={'title_selector':title_selector,'viewport':[w,h],'view':view,'name':name,'glyph_pixels':len(ratios),'min_contrast':round(min(ratios),3) if ratios else None,'text_shadow_used':False}
     result['glyph_samples'].append(row)
     await el.evaluate('(e)=>{e.style.removeProperty("visibility");e.style.removeProperty("text-shadow");}')
     await page.locator('.tabletop-stage').evaluate('(e)=>e.blur()')
     await page.screenshot(path=str(args.output/f'{w}-{view}-{len(name)}.png'))
     assert len(ratios)>0 and min(ratios)>=4.5,row
  assert not result['errors'],result['errors'];await b.close()
 (args.output/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/contrast');asyncio.run(main(parser.parse_args()))
