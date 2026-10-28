"""PWA upgrade regression check using a disposable HTTP fixture and real Chromium.
Requires Python Playwright, /usr/bin/chromium, and the previous commit in Git history.
"""
import asyncio,shutil,json,subprocess,tarfile,io,tempfile,threading,re
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from verify_tabletop import complete_setup
from playwright.async_api import async_playwright
async def main(root,dest,base_url,stop_server):
 old_version=re.search(r'const VER = "([^"]+)"', (dest/"sw.js").read_text()).group(1)
 new_version=re.search(r'const VER = "([^"]+)"', (root/"sw.js").read_text()).group(1)
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  c=await b.new_context();page=await c.new_page();errors=[];pending=set()
  page.on("request",lambda r:pending.add(r.url))
  page.on("requestfinished",lambda r:pending.discard(r.url))
  page.on("requestfailed",lambda r:pending.discard(r.url))
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(base_url+'/',wait_until='networkidle')
  if await page.locator('#hClose').is_visible():await page.locator('#hClose').click()
  await page.locator('#wNew').click();await complete_setup(page)
  await page.get_by_role('button',name='ابدأ المباراة 🎲',exact=True).click()
  for _ in range(15):
   await page.wait_for_timeout(200)
   if await page.locator('#roll').is_enabled():break
   buttons=page.locator('#modal.on #sheet button')
   if await buttons.count():await buttons.last.click()
  await page.wait_for_function('!document.querySelector("#roll").disabled')
  await page.evaluate('navigator.serviceWorker.ready.then(()=>true)')
  await page.wait_for_function('navigator.serviceWorker.controller !== null')
  assert old_version in await page.evaluate('caches.keys()')
  old_nodes=await page.locator('#board *').count()
  saved=await page.evaluate('JSON.parse(localStorage.getItem("darb-althara-v6")).players.map(p=>({name:p.name,pk:p.pk,cash:p.cash}))')
  for f in root.rglob('*'):
   if f.is_file() and '.git' not in f.relative_to(root).parts:
    to=dest/f.relative_to(root);to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,to)
  await page.evaluate('navigator.serviceWorker.getRegistration().then(r=>r.update())')
  await page.wait_for_function('''async v => (await caches.keys()).includes(v.next) && !(await caches.keys()).includes(v.old)''',arg={'next':new_version,'old':old_version},timeout=30000)
  await page.wait_for_function('''async () => {const r=await navigator.serviceWorker.getRegistration();return r?.active?.state==='activated'&&navigator.serviceWorker.controller===r.active}''')
  await page.reload(wait_until='networkidle')
  assert await page.locator('.character-pawn').count()==2, {'errors':errors,'state':await page.evaluate('({engine:!!window.__darb,tabletop:!!window.DarbTabletop,game:!!window.__darb?.G})')}
  after=await page.evaluate('__darb.G.players.map(p=>({name:p.name,pk:p.pk,cash:p.cash}))')
  assert saved==after,(saved,after)
  await page.wait_for_function('''async () => (await (await caches.match('./index.html')).text()).includes('scripts/identity.js')''')
  # Cut the origin itself: this verifies cache-only reload without a CDP offline-toggle race.
  await asyncio.to_thread(stop_server)
  try:await page.reload(wait_until='domcontentloaded',timeout=10000)
  except Exception:
   print({'offline_pending_requests':sorted(pending),'workers':[await w.evaluate('typeof VER!=="undefined"?VER:"unknown"') for w in c.service_workers]},flush=True)
   raise
  await page.wait_for_function('window.__darb && __darb.G')
  assert await page.locator('.character-pawn').count()==2, {'errors':errors,'state':await page.evaluate('({engine:!!window.__darb,tabletop:!!window.DarbTabletop,game:!!window.__darb?.G})')}
  new_nodes=await page.locator('#board *').count()
  assert new_nodes<=old_nodes+180,(old_nodes,new_nodes)
  assert await page.locator('#board .solid, #board .board-miniature').count()==0
  assert await page.locator('.pawn-art').first.is_visible()
  await page.wait_for_selector('#board.landmarks-ready.decks-ready')
  assert await page.locator('.landmark-sprite').count()==6
  assert await page.locator('.deck-sprite').count()==3
  assert not errors,errors
  print(json.dumps({'board_nodes_before_after':[old_nodes,new_nodes],'upgrade_from':old_version,'upgrade_to':new_version,'upgrade':'passed','previous_game_players_professions_cash':'preserved','upgraded_offline_game':'passed'}))
  await b.close()
if __name__ == '__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Verify old PWA upgrade preserves an actual saved game.')
 parser.add_argument('--previous-ref',default='be053fc')
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
  def stop_server():
   server.shutdown();server.server_close()
  try:asyncio.run(asyncio.wait_for(main(root,dest,f'http://localhost:{server.server_port}',stop_server),timeout=80))
  finally:stop_server();server.server_close()

