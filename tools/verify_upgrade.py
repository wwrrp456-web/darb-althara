"""PWA upgrade regression check using a disposable HTTP fixture and real Chromium.
Requires Python Playwright, /usr/bin/chromium, and the previous commit in Git history.
"""
import asyncio,shutil,json,subprocess,tarfile,io,tempfile,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.async_api import async_playwright
async def main(root,dest,base_url):
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  c=await b.new_context();page=await c.new_page()
  await page.goto(base_url+'/',wait_until='networkidle')
  if await page.locator('#hClose').is_visible():await page.locator('#hClose').click()
  await page.locator('#wNew').click();await page.locator('#sStart').click()
  await page.get_by_role('button',name='ابدأ المباراة 🎲',exact=True).click()
  for _ in range(15):
   await page.wait_for_timeout(200)
   if await page.locator('#roll').is_enabled():break
   buttons=page.locator('#modal.on #sheet button')
   if await buttons.count():await buttons.last.click()
  await page.wait_for_function('!document.querySelector("#roll").disabled')
  await page.evaluate('navigator.serviceWorker.ready.then(()=>true)')
  await page.wait_for_function('navigator.serviceWorker.controller !== null')
  assert 'darb-illustrated-cards-v7' in await page.evaluate('caches.keys()')
  saved=await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6")).players.map(p=>({name:p.name,pk:p.pk,cash:p.cash}))')
  for f in root.rglob('*'):
   if f.is_file() and '.git' not in f.relative_to(root).parts:
    to=dest/f.relative_to(root);to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,to)
  await page.evaluate('navigator.serviceWorker.getRegistration().then(r=>r.update())')
  await page.wait_for_function('''async () => (await caches.keys()).includes('darb-solid-miniatures-v8') && !(await caches.keys()).includes('darb-illustrated-cards-v7')''',timeout=30000)
  await page.reload(wait_until='networkidle')
  assert await page.locator('.character-pawn').count()==2
  after=await page.evaluate('__darb.G.players.map(p=>({name:p.name,pk:p.pk,cash:p.cash}))')
  assert saved==after,(saved,after)
  await page.wait_for_function('''async () => (await (await caches.match('./index.html')).text()).includes('scripts/models.js')''')
  await c.set_offline(True);await page.reload(wait_until='domcontentloaded')
  await page.wait_for_function('window.__darb && __darb.G')
  assert await page.locator('.character-pawn').count()==2
  assert await page.locator('.tile .board-miniature').count()==48
  assert await page.locator('.pawn-figure .toy-person').count()==2
  print(json.dumps({'upgrade_v7_to_v8':'passed','previous_game_players_professions_cash':'preserved','upgraded_offline_game':'passed'}))
  await b.close()
if __name__ == '__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Verify old PWA upgrade preserves an actual saved game.')
 parser.add_argument('--previous-ref',default='00ebc40')
 args=parser.parse_args()
 root=Path(__file__).resolve().parents[1]
 class QuietHandler(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 with tempfile.TemporaryDirectory(prefix='darb-upgrade-') as directory:
  dest=Path(directory)
  archived=subprocess.run(['git','archive',args.previous_ref,'index.html','sw.js','manifest.webmanifest','icons','fonts','styles','scripts','art/identity'],cwd=root,check=True,stdout=subprocess.PIPE).stdout
  with tarfile.open(fileobj=io.BytesIO(archived)) as tar:tar.extractall(dest,filter='data')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(dest)))
  threading.Thread(target=server.serve_forever,daemon=True).start()
  try:asyncio.run(asyncio.wait_for(main(root,dest,f'http://localhost:{server.server_port}'),timeout=80))
  finally:server.shutdown();server.server_close()

