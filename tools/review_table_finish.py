"""Capture the same 320% project edge from the previous release and current app.
Uses an isolated archive/server; never checks out over user work or edits artwork.
"""
import asyncio,io,json,math,subprocess,tarfile,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.async_api import async_playwright
from verify_tabletop import start_game
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/table-finish'
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
async def capture(base,name):
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':390,'height':844});await start_game(page,base_url=base)
  state=await page.evaluate('JSON.stringify(__darb.G)');stage=page.locator('.tabletop-stage');scene=await stage.bounding_box();x=scene['x']+scene['width']/2;y=scene['y']+scene['height']/2
  for delta in [-200,-200,-(math.log(3.2)-.8)/.002]:await stage.dispatch_event('wheel',{'deltaY':delta,'clientX':x,'clientY':y,'deltaMode':0})
  assert await stage.get_attribute('data-zoom')=='320'
  boxes=[await page.locator(f'[data-landmark={key}]').bounding_box() for key in ['uni','hotel']]
  mx=sum(r['x']+r['width']/2 for r in boxes)/2;my=sum(r['y']+r['height']/2 for r in boxes)/2
  await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+x-mx,y+y-my,steps=24);await page.mouse.up();await page.wait_for_timeout(350)
  assert await page.evaluate('JSON.stringify(__darb.G)')==state
  await page.screenshot(path=str(OUT/name));await b.close()
async def main(base):
 await capture(base,'before-320.png');await capture('http://localhost:8000','after-320.png')
 (OUT/'comparison-check.json').write_text(json.dumps({'previous_ref':'58b8237dccf213448cbde793900097464d0abd7f','viewport':[390,844],'both_zoom_percent':320,'fixture':'same professions, university/hotel edge centred through the ordinary camera gesture','game_state_after_camera':'unchanged'},indent=2)+'\n')
if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='darb-table-before-') as directory:
  data=subprocess.check_output(['git','archive','58b8237','index.html','sw.js','manifest.webmanifest','icons','fonts','styles','scripts','art/identity'],cwd=ROOT)
  with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall(directory,filter='data')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=directory));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:asyncio.run(main(f'http://localhost:{server.server_port}'))
  finally:server.shutdown();server.server_close()
