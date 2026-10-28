"""Diagnostic only: real input + rAF sampling and CDP CPU metrics under 4x throttling."""
import argparse,asyncio,json,statistics
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1]
async def run(output,ending="dreams"):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  results=[]
  for width,height in [(390,844),(1180,820)]:
   context=await browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
   page=await context.new_page()
   if ending=='time':
    from verify_sessions import setup
    await setup(page,ending='time',limit=30)
   else:await start_game(page)
   await page.locator('.tabletop-stage').scroll_into_view_if_needed()
   await page.evaluate('Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))')
   cdp=await context.new_cdp_session(page)
   await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});await cdp.send('Performance.enable')
   rect=await page.locator('.tabletop-stage').bounding_box();x=rect['x']+rect['width']*.5;y=rect['y']+rect['height']*.5
   before={m['name']:m['value'] for m in (await cdp.send('Performance.getMetrics'))['metrics']}
   await page.evaluate('''()=>{window.__sample={start:performance.now(),times:[],done:false};function frame(t){__sample.times.push(t);if(t-__sample.start<3000)requestAnimationFrame(frame);else __sample.done=true}requestAnimationFrame(frame)}''')
   await page.mouse.move(x,y);await page.mouse.down()
   for _ in range(3):
    await page.mouse.move(x+35,y+25,steps=18);await page.mouse.move(x-30,y-15,steps=18)
   await page.mouse.up();await page.mouse.wheel(0,-60);await page.mouse.wheel(0,60)
   await page.wait_for_function('__sample.done')
   sample=await page.evaluate('__sample')
   after={m['name']:m['value'] for m in (await cdp.send('Performance.getMetrics'))['metrics']}
   t=sample['times'];intervals=[b-a for a,b in zip(t,t[1:])];elapsed=(t[-1]-t[0])/1000
   row={'viewport':[width,height],'cpu_throttle':4,'session_ending':ending,'fps':round((len(t)-1)/elapsed,2),'median_frame_ms':round(statistics.median(intervals),2),'p95_frame_ms':round(sorted(intervals)[int(len(intervals)*.95)],2),'main_thread_task_ms':round((after['TaskDuration']-before['TaskDuration'])*1000,2),'script_ms':round((after['ScriptDuration']-before['ScriptDuration'])*1000,2),'board_nodes':await page.locator('#board *').count()}
   results.append(row);await context.close()
  Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results));await browser.close()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',default='/tmp/darb-performance.json');parser.add_argument('--session-ending',choices=['dreams','time'],default='dreams');args=parser.parse_args();asyncio.run(run(args.output,args.session_ending))
