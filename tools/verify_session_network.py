"""Two isolated Chromium contexts connected through real local WebRTC data channels.
This does not prove internet/STUN/TURN behavior between physical devices.
"""
import asyncio,json,base64,argparse
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[1]/'docs/phase-e'
async def main(simulated=False,ending="rounds"):
 result={'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  hc=await b.new_context();gc=await b.new_context();host=await hc.new_page();guest=await gc.new_page()
  for page in [host,guest]:page.set_default_timeout(20000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
  for page in [host,guest]:await page.add_init_script("""window.__wireLog=[];const originalSend=RTCDataChannel.prototype.send;RTCDataChannel.prototype.send=function(message){try{const o=JSON.parse(message);__wireLog.push({type:o.t,protocol:o.protocol});}catch(e){}return originalSend.call(this,message);};""")
  await host.goto('http://localhost:8000/?speed=80',wait_until='networkidle');await host.locator('#wNew').click()
  await host.locator('[data-i="1"] [data-k="ctrl"]').select_option('remote');await host.locator('#sStart').click()
  await host.locator('#sSession').select_option('extended' if ending=='time' else 'family');await host.locator('#sEnding').select_option(ending);await host.locator('#sLimit').fill('1')
  await host.get_by_role('button',name='مراجعة الإعدادات',exact=True).click();await host.locator('#sLaunch').click()
  await host.locator('#iMake').click();await host.locator('#iCode').wait_for();offer=await host.locator('#iCode').input_value()
  await guest.goto('http://localhost:8000/?speed=80',wait_until='networkidle');await guest.locator('#wJoin').click()
  # Old invitation explicitly fails before RTC creation.
  old='DARB1R'+base64.urlsafe_b64encode(json.dumps({'t':'offer','sdp':'v=0\r\n','protocol':1}).encode()).decode().rstrip('=')
  await guest.locator('#jCode').fill(old);await guest.locator('#jMake').click()
  await guest.wait_for_function('document.querySelector("#jMsg").textContent.includes("غير متوافق")')
  result['old_protocol_invitation_rejected']='passed'
  await guest.locator('#jCode').fill(offer);await guest.locator('#jMake').click();await guest.locator('#jAns').wait_for()
  answer=await guest.locator('#jAns').input_value();await host.locator('#iAns').fill(answer);await host.locator('#iGo').click()
  await host.wait_for_timeout(500)
  initial=[]
  for page in [host,guest]:initial.append(await page.evaluate("({role:__darb.Net.role,signaling:__darb.Net.pc?.signalingState,localType:__darb.Net.pc?.localDescription?.type,remoteType:__darb.Net.pc?.remoteDescription?.type,candidates:(__darb.Net.pc?.localDescription?.sdp.match(/a=candidate/g)||[]).length,message:document.querySelector('#iMsg,#jMsg')?.textContent})"))
  print(initial,flush=True)
  if simulated:
   # Explicit transport fixture only: keep the app's actual message parsing, handshake,
   # authority checks and game engine; replace only UDP delivery blocked by policy.
   async def to_guest(raw):await guest.evaluate('(raw)=>__darb.Net.dc.onmessage({data:raw})',raw)
   async def to_host(raw):await host.evaluate('(raw)=>__darb.Net.dc.onmessage({data:raw})',raw)
   await host.expose_function('__deliverGuest',to_guest);await guest.expose_function('__deliverHost',to_host)
   await host.evaluate("""()=>{const original=__darb.Net.dc;__darb.Net.dc={readyState:'open',send:raw=>__deliverGuest(raw),close(){},onmessage:original.onmessage};original.onopen();}""")
   await guest.evaluate("""()=>{const channel={readyState:'open',send:raw=>__deliverHost(raw),close(){}};__darb.Net.pc.ondatachannel({channel});channel.onopen();}""")
  try:
   await host.wait_for_function('window.__darb?.Net.open&&__darb.Net.role==="host"');await guest.wait_for_function('window.__darb?.G&&__darb.Net.role==="guest"')
  except Exception:
   diagnostics=[]
   for page in [host,guest]:diagnostics.append(await page.evaluate("({role:__darb.Net.role,open:__darb.Net.open,connection:__darb.Net.pc?.connectionState,ice:__darb.Net.pc?.iceConnectionState,channel:__darb.Net.dc?.readyState,message:document.querySelector('#iMsg,#jMsg')?.textContent,errors:window.__wireLog})"))
   (OUT/'network-diagnostic.json').write_text(json.dumps({'initial':initial,'after_timeout':diagnostics,'environment_policy':'/etc/chromium/policies/managed/misc.json: WebRtcIPHandling=disable_non_proxied_udp'},ensure_ascii=False,indent=2));print(diagnostics,flush=True);raise
  assert await guest.evaluate('__darb.G.session.ending')==ending
  assert await guest.evaluate('document.documentElement.dataset.session')==('extended' if ending=='time' else 'family')
  if ending=='time':
   await host.evaluate('__darb.G.clock.elapsedMs=60001')
  else:
   snapshot=await host.evaluate('JSON.stringify(__darb.G)')
   await host.evaluate('''()=>{__darb.Net.dc.onmessage({data:JSON.stringify({protocol:1,t:'roll'})});__darb.Net.dc.onmessage({data:JSON.stringify({protocol:2,t:'clock',clock:{elapsedMs:1e12},round:999})});}''')
   assert await host.evaluate('JSON.stringify(__darb.G)')==snapshot
   result['guest_cannot_override_clock_or_use_wrong_protocol']='passed'
  for _ in range(1500):
   if await host.evaluate('__darb.G.phase==="over"'):break
   for page in [host,guest]:
    buttons=page.locator('#modal.on #sheet button')
    if await buttons.count():
     try:await buttons.last.click(timeout=600)
     except Exception:pass
    elif await page.locator('#roll').is_enabled():await page.locator('#roll').click()
   await host.wait_for_timeout(25)
  else:raise AssertionError('Network game did not finish')
  await guest.wait_for_function('__darb.G.phase==="over"')
  a=await host.evaluate('JSON.stringify(__darb.G.summary)');z=await guest.evaluate('JSON.stringify(__darb.G.summary)');assert a==z
  assert await guest.evaluate('__darb.G.players.map(p=>p.turns)')==[1,1]
  assert await guest.evaluate('__darb.G.summary.reason')==ending
  result.update(transport='simulated application transport' if simulated else 'real WebRTC',host_round_limit_and_settlement='passed',identical_result='passed')
  assert not result['errors'],result['errors'];await b.close()
 (OUT/('network-simulated-'+ending+'-check.json' if simulated else 'network-check.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--simulated-transport',action='store_true');parser.add_argument('--ending',choices=['rounds','time'],default='rounds');args=parser.parse_args();asyncio.run(main(args.simulated_transport,args.ending))
